"""Cognitive Router R0 — deterministic Round-Robin with capability/safety filters."""

from __future__ import annotations

import hashlib
import time
import uuid
from pathlib import Path
from typing import Any, Iterable, Sequence

from .errors import UnknownPolicy
from .log import DecisionLog
from .models import (
    DecisionStatus,
    NodeAvailability,
    RouteCandidate,
    RouteDecision,
    TaskSpec,
    candidates_fingerprint,
)
from .persist import DecisionStore
from .policy import (
    normalize_policy,
    policy_hash,
    resolve_policy,
    safety_block_reason,
)


def _has_capabilities(
    candidate: RouteCandidate, required: Sequence[str]
) -> bool:
    have = set(candidate.capabilities)
    return all(cap in have for cap in required)


def _default_op_id(task: TaskSpec, seed: int, p_hash: str) -> str:
    """Deterministic op_id when caller omits one (still unique per task+seed+policy)."""
    if task.op_id:
        return task.op_id
    material = f"{task.task_id}|{seed}|{p_hash}|{','.join(task.required_capabilities)}"
    return hashlib.sha256(material.encode("utf-8")).hexdigest()[:32]


def _default_trace_id(task: TaskSpec, op_id: str) -> str:
    if task.trace_id:
        return task.trace_id
    return op_id


class CognitiveRouterR0:
    """Phase 3 R0: Task → filters → deterministic Round-Robin → RouteDecision.

    Determinism (DeepSeek C8)
    -------------------------
    ``RouteDecision_canonical = f(policy_hash, seed, TaskSpec, candidates_fp)``.
    Volatile fields excluded via ``RouteDecision.canonical_bytes()``.

    Safety — fail-closed
    --------------------
    Unknown policy / no capable node / safety block / saturation ⇒ REJECTED
    with typed reason. Never silent fallback. Never executes network/physical.

    C-RAM audit
    -----------
    Every decision persisted with ``op_id + epoch + trace_id``. Same ``op_id``
    is idempotent (replay returns the stored decision; RR cursor unchanged).
    """

    VERSION = "R0"
    DEFAULT_QUEUE_BOUND = 1000

    def __init__(
        self,
        candidates: Iterable[RouteCandidate],
        *,
        seed: int = 0,
        policy: dict[str, Any] | None = None,
        policy_root: str | Path | None = None,
        decision_log: DecisionLog | None = None,
        decision_log_path: str | Path | None = None,
        decision_store: DecisionStore | None = None,
        decision_store_root: str | Path | None = None,
        epoch: int = 0,
        queue_bound: int = DEFAULT_QUEUE_BOUND,
    ):
        ordered = sorted(list(candidates), key=lambda c: c.node_id)
        self._candidates: list[RouteCandidate] = ordered
        self.seed = int(seed)
        self._rr_index = int(seed)
        self.epoch = int(epoch)
        self.queue_bound = int(queue_bound)
        self._inflight = 0  # accepted not yet completed

        raw_policy = resolve_policy(
            policy, root=Path(policy_root) if policy_root else None
        )
        self._policy_raw = raw_policy
        self._policy_error: str | None = None
        self._policy: dict[str, Any] | None = None
        self._policy_hash: str = ""
        try:
            self._policy = normalize_policy(raw_policy)
            self._policy_hash = policy_hash(raw_policy)
        except UnknownPolicy as exc:
            self._policy_error = str(exc.detail or exc)
            self._policy_hash = ""

        if decision_log is not None:
            self.log = decision_log
        else:
            self.log = DecisionLog(decision_log_path)

        if decision_store is not None:
            self.store = decision_store
        elif decision_store_root is not None:
            self.store = DecisionStore(decision_store_root)
        else:
            self.store = None

        self._cand_fp = candidates_fingerprint(self._candidates)

    @property
    def policy_hash(self) -> str:
        return self._policy_hash

    @property
    def candidates(self) -> list[RouteCandidate]:
        return list(self._candidates)

    def update_candidates(self, candidates: Iterable[RouteCandidate]) -> None:
        self._candidates = sorted(list(candidates), key=lambda c: c.node_id)
        self._cand_fp = candidates_fingerprint(self._candidates)

    def set_node_status(self, node_id: str, status: NodeAvailability) -> None:
        updated: list[RouteCandidate] = []
        for c in self._candidates:
            if c.node_id == node_id:
                updated.append(
                    RouteCandidate(
                        node_id=c.node_id,
                        capabilities=c.capabilities,
                        status=status,
                        cpu=c.cpu,
                        memory=c.memory,
                    )
                )
            else:
                updated.append(c)
        self._candidates = sorted(updated, key=lambda c: c.node_id)
        self._cand_fp = candidates_fingerprint(self._candidates)

    def complete(self, op_id: str) -> None:
        """Mark an accepted decision complete (frees saturation slot)."""
        if self._inflight > 0:
            self._inflight -= 1

    def route(self, task: TaskSpec) -> RouteDecision:
        """Compute a RouteDecision for ``task`` (no side-effect execution)."""
        t0 = time.perf_counter()
        considered = [c.node_id for c in self._candidates]

        # Fail-closed: unknown policy — never route under it.
        if self._policy_error is not None or self._policy is None:
            op_id = task.op_id or f"unknown-policy-{task.task_id}-{uuid.uuid4().hex[:8]}"
            trace_id = _default_trace_id(task, op_id)
            decision = self._make_decision(
                task=task,
                status=DecisionStatus.REJECTED,
                reason="UNKNOWN_POLICY",
                selected=None,
                considered=considered,
                eligible=[],
                excluded=[{"node_id": "*", "reason": "UNKNOWN_POLICY"}],
                t0=t0,
                op_id=op_id,
                trace_id=trace_id,
                rr_pick=None,
            )
            return self._commit(decision, advance_rr=False)

        p_hash = self._policy_hash
        op_id = _default_op_id(task, self.seed, p_hash)
        trace_id = _default_trace_id(task, op_id)

        # Idempotency: same op_id → one decision (no RR advance).
        if self.store is not None:
            prior = self.store.get_by_op_id(op_id)
            if prior is not None:
                return prior

        # SAFETY_POLICY blocks (network/physical).
        block = safety_block_reason(task, self._policy)
        if block is not None:
            decision = self._make_decision(
                task=task,
                status=DecisionStatus.REJECTED,
                reason=block,
                selected=None,
                considered=considered,
                eligible=[],
                excluded=[{"node_id": "*", "reason": block}],
                t0=t0,
                op_id=op_id,
                trace_id=trace_id,
                rr_pick=None,
            )
            return self._commit(decision, advance_rr=False)

        eligible: list[RouteCandidate] = []
        excluded: list[dict[str, str]] = []
        for c in self._candidates:
            if c.status != NodeAvailability.AVAILABLE:
                excluded.append({"node_id": c.node_id, "reason": "UNAVAILABLE"})
                continue
            if not _has_capabilities(c, task.required_capabilities):
                excluded.append(
                    {"node_id": c.node_id, "reason": "MISSING_CAPABILITY"}
                )
                continue
            eligible.append(c)

        eligible_ids = [c.node_id for c in eligible]
        if not eligible:
            decision = self._make_decision(
                task=task,
                status=DecisionStatus.REJECTED,
                reason="NO_CAPABLE_NODE",
                selected=None,
                considered=considered,
                eligible=[],
                excluded=excluded,
                t0=t0,
                op_id=op_id,
                trace_id=trace_id,
                rr_pick=None,
            )
            return self._commit(decision, advance_rr=False)

        # Saturation: reject when inflight would exceed bound (no silent drop).
        if self._inflight >= self.queue_bound:
            decision = self._make_decision(
                task=task,
                status=DecisionStatus.REJECTED,
                reason="SATURATION_QUEUE_FULL",
                selected=None,
                considered=considered,
                eligible=eligible_ids,
                excluded=excluded
                + [
                    {
                        "node_id": "*",
                        "reason": f"SATURATION_QUEUE_FULL:{self._inflight}>={self.queue_bound}",
                    }
                ],
                t0=t0,
                op_id=op_id,
                trace_id=trace_id,
                rr_pick=None,
            )
            return self._commit(decision, advance_rr=False)

        pick_idx = self._rr_index % len(eligible)
        chosen = eligible[pick_idx]

        decision = self._make_decision(
            task=task,
            status=DecisionStatus.ACCEPTED,
            reason="ROUND_ROBIN",
            selected=chosen.node_id,
            considered=considered,
            eligible=eligible_ids,
            excluded=excluded,
            t0=t0,
            op_id=op_id,
            trace_id=trace_id,
            rr_pick=pick_idx,
        )
        return self._commit(decision, advance_rr=True)

    def route_many(self, tasks: Sequence[TaskSpec]) -> list[RouteDecision]:
        return [self.route(t) for t in tasks]

    def _make_decision(
        self,
        *,
        task: TaskSpec,
        status: DecisionStatus,
        reason: str,
        selected: str | None,
        considered: list[str],
        eligible: list[str],
        excluded: list[dict[str, str]],
        t0: float,
        op_id: str,
        trace_id: str,
        rr_pick: int | None,
    ) -> RouteDecision:
        latency_ms = (time.perf_counter() - t0) * 1000.0
        metrics: dict[str, Any] = {
            "router_version": self.VERSION,
            "decision_latency_ms": latency_ms,
            "eligible_count": len(eligible),
            "rr_index_before": (
                self._rr_index if rr_pick is not None else self._rr_index
            ),
            "rr_pick": rr_pick,
            "selected_node_id": selected,
            "seed": self.seed,
            "candidate_count": len(self._candidates),
            "inflight": self._inflight,
            "queue_bound": self.queue_bound,
        }
        return RouteDecision(
            task_id=task.task_id,
            status=status,
            reason=reason,
            selected_node_id=selected,
            candidates_considered=considered,
            eligible=eligible,
            excluded=excluded,
            metrics=metrics,
            seed=self.seed,
            policy_hash=self._policy_hash,
            op_id=op_id,
            epoch=self.epoch,
            trace_id=trace_id,
            candidates_fingerprint=self._cand_fp,
        )

    def _commit(self, decision: RouteDecision, *, advance_rr: bool) -> RouteDecision:
        if advance_rr and decision.status == DecisionStatus.ACCEPTED:
            self._rr_index += 1
            self._inflight += 1
        self.log.append(decision)
        if self.store is not None:
            self.store.put(decision)
        return decision


def candidates_from_topology(
    topology: Any,
    *,
    unavailable: Iterable[str] | None = None,
) -> list[RouteCandidate]:
    """Build RouteCandidates from Twin Topology / DigitalTwin-like object."""
    lost = set(unavailable or [])
    nodes_raw: list[Any]
    if hasattr(topology, "nodes") and not callable(topology.nodes):
        nodes = topology.nodes
        if isinstance(nodes, dict):
            out: list[RouteCandidate] = []
            for nid, n in sorted(nodes.items(), key=lambda kv: str(kv[0])):
                caps = getattr(n, "capabilities", ("compute",))
                if isinstance(caps, str):
                    caps_t = (caps,)
                else:
                    caps_t = tuple(caps)
                status = (
                    NodeAvailability.UNAVAILABLE
                    if str(nid) in lost
                    else NodeAvailability.AVAILABLE
                )
                out.append(
                    RouteCandidate(
                        node_id=str(nid),
                        capabilities=caps_t,
                        status=status,
                        cpu=int(getattr(n, "cpu_cores", getattr(n, "cpu", 0))),
                        memory=int(
                            getattr(
                                n,
                                "memory",
                                int(float(getattr(n, "memory_gb", 0)) * 1000),
                            )
                        ),
                    )
                )
            return out
        nodes_raw = list(nodes)
    elif isinstance(topology, dict) and "nodes" in topology:
        nodes_raw = list(topology["nodes"])
    else:
        raise TypeError(f"unsupported topology for candidates: {type(topology)!r}")

    out2: list[RouteCandidate] = []
    for n in nodes_raw:
        if hasattr(n, "id"):
            nid = str(n.id)
            caps = tuple(getattr(n, "capabilities", ["compute"]))
            cpu = int(getattr(n, "cpu", 0))
            memory = int(getattr(n, "memory", 0))
        elif hasattr(n, "node_id"):
            nid = str(n.node_id)
            caps = tuple(getattr(n, "capabilities", ["compute"]))
            cpu = int(getattr(n, "cpu_cores", 0))
            memory = int(float(getattr(n, "memory_gb", 0)) * 1000)
        elif isinstance(n, dict):
            nid = str(n.get("id") or n.get("node_id"))
            caps = tuple(n.get("capabilities", ["compute"]))
            cpu = int(n.get("cpu", n.get("cpu_cores", 0)))
            memory = int(n.get("memory", 0))
        else:
            raise TypeError(f"unsupported node type: {type(n)!r}")
        status = (
            NodeAvailability.UNAVAILABLE
            if nid in lost
            else NodeAvailability.AVAILABLE
        )
        out2.append(
            RouteCandidate(
                node_id=nid,
                capabilities=caps,
                status=status,
                cpu=cpu,
                memory=memory,
            )
        )
    return sorted(out2, key=lambda c: c.node_id)


def explain_decision(decision: RouteDecision) -> dict[str, Any]:
    """JSON shape for `mesh router explain` (Cycle 7 ChatGPT P3)."""
    return {
        "task_id": decision.task_id,
        "decision": decision.selected_node_id,
        "status": decision.status.value
        if hasattr(decision.status, "value")
        else str(decision.status),
        "strategy": decision.reason,
        "reason": decision.reason,
        "excluded_nodes": [
            {"node": e.get("node_id", e.get("node")), "reason": e.get("reason")}
            for e in decision.excluded
        ],
        "eligible": list(decision.eligible),
        "seed": decision.seed,
        "policy_hash": decision.policy_hash,
        "op_id": decision.op_id,
        "epoch": decision.epoch,
        "trace_id": decision.trace_id,
        "metrics": dict(decision.metrics),
    }


__all__ = [
    "CognitiveRouterR0",
    "candidates_from_topology",
    "explain_decision",
]
