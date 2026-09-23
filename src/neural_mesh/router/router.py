"""Cognitive Router R0/R1 — Round-Robin + Capability-aware (Cycle 10)."""

from __future__ import annotations

import hashlib
import time
import uuid
from pathlib import Path
from typing import Any, Iterable, Sequence

from .audit import AuditTrail
from .errors import CramPersistError, UnknownPolicy
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
from .capabilities import CapabilityRegistry
from .strategy import CapabilityAwareStrategy, RoundRobinStrategy, RoutingStrategy
from .trace import build_replay_envelope, ensure_trace_id


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

    C-RAM audit (Cycle 9 harden)
    ----------------------------
    Every decision persisted with ``op_id + epoch + trace_id``. Same ``op_id``
    is idempotent (replay returns the stored decision; RR cursor unchanged).

    **P1 Guard:** when a DecisionStore is configured, ``RouteDecision`` is
    emitted only after a durable persist ACK. Persist failure ⇒ typed
    ``CramPersistError`` (no phantom decision, RR cursor unchanged).
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
        audit_trail: AuditTrail | None = None,
        strategy: RoutingStrategy | None = None,
        capability_registry: CapabilityRegistry | None = None,
        epoch: int = 0,
        queue_bound: int = DEFAULT_QUEUE_BOUND,
    ):
        ordered = sorted(list(candidates), key=lambda c: c.node_id)
        self._candidates: list[RouteCandidate] = ordered
        self.seed = int(seed)
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

        self.capability_registry = (
            capability_registry
            if capability_registry is not None
            else CapabilityRegistry()
        )

        # Strategy first so we can fold routing_strategy into policy_hash (C10).
        if strategy is None:
            self.strategy: RoutingStrategy = RoundRobinStrategy(index=int(seed))
        else:
            self.strategy = strategy
        self._rr_index = int(getattr(self.strategy, "index", seed))

        try:
            hash_policy = dict(raw_policy)
            sname = getattr(self.strategy, "name", "ROUND_ROBIN")
            if sname in ("CAPABILITY_AWARE", "capability"):
                hash_policy["routing_strategy"] = "capability"
            # RR keeps R0 hash (no routing_strategy key) for Cycle 8/9 back-compat.
            self._policy = normalize_policy(hash_policy)
            self._policy_hash = policy_hash(hash_policy)
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

        self.audit = audit_trail if audit_trail is not None else AuditTrail()

        self._cand_fp = candidates_fingerprint(self._candidates)
        self._cap_fp = self.capability_registry.fingerprint(fresh_only=True)

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
        """Compute a RouteDecision for ``task`` (no side-effect execution).

        Raises ``CramPersistError`` when a store is configured and persist ack
        fails — never returns a phantom decision in that case.
        """
        t0 = time.perf_counter()
        considered = [c.node_id for c in self._candidates]
        rr_before = int(getattr(self.strategy, "index", self._rr_index))

        # Fail-closed: unknown policy — never route under it.
        if self._policy_error is not None or self._policy is None:
            op_id = task.op_id or f"unknown-policy-{task.task_id}-{uuid.uuid4().hex[:8]}"
            trace_id = ensure_trace_id(task, op_id)
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
                rr_before=rr_before,
            )
            return self._commit(decision, task=task, advance_rr=False, rr_before=rr_before)

        p_hash = self._policy_hash
        op_id = _default_op_id(task, self.seed, p_hash)
        trace_id = ensure_trace_id(task, op_id)

        # Idempotency: same op_id → one decision (no RR advance).
        if self.store is not None:
            try:
                prior = self.store.get_by_op_id(op_id)
            except CramPersistError:
                raise
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
                rr_before=rr_before,
            )
            return self._commit(decision, task=task, advance_rr=False, rr_before=rr_before)

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
                rr_before=rr_before,
            )
            return self._commit(decision, task=task, advance_rr=False, rr_before=rr_before)

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
                rr_before=rr_before,
            )
            return self._commit(decision, task=task, advance_rr=False, rr_before=rr_before)

        chosen, pick_idx = self.strategy.select(task, eligible)
        # R1: CapabilityAware may return (None, None) ⇒ typed no-match (never silent RR).
        if chosen is None or pick_idx is None:
            reason = getattr(self.strategy, "last_reason", None) or "CAPABILITY_NO_MATCH"
            if reason not in (
                "CAPABILITY_NO_MATCH",
                "NO_CAPABLE_NODE",
                "STALE_CAPABILITY",
            ):
                # Empty eligible already handled; treat as no-match fail-closed.
                reason = "CAPABILITY_NO_MATCH" if isinstance(
                    self.strategy, CapabilityAwareStrategy
                ) else "NO_CAPABLE_NODE"
            decision = self._make_decision(
                task=task,
                status=DecisionStatus.REJECTED,
                reason=reason,
                selected=None,
                considered=considered,
                eligible=eligible_ids,
                excluded=excluded
                + [{"node_id": "*", "reason": reason}],
                t0=t0,
                op_id=op_id,
                trace_id=trace_id,
                rr_pick=None,
                rr_before=rr_before,
            )
            return self._commit(decision, task=task, advance_rr=False, rr_before=rr_before)

        sname = getattr(self.strategy, "name", "ROUND_ROBIN")
        reason = "CAPABILITY_AWARE" if sname == "CAPABILITY_AWARE" else "ROUND_ROBIN"

        decision = self._make_decision(
            task=task,
            status=DecisionStatus.ACCEPTED,
            reason=reason,
            selected=chosen.node_id,
            considered=considered,
            eligible=eligible_ids,
            excluded=excluded,
            t0=t0,
            op_id=op_id,
            trace_id=trace_id,
            rr_pick=pick_idx,
            rr_before=rr_before,
        )
        return self._commit(decision, task=task, advance_rr=True, rr_before=rr_before)

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
        rr_before: int,
    ) -> RouteDecision:
        latency_ms = (time.perf_counter() - t0) * 1000.0
        sname = getattr(self.strategy, "name", "ROUND_ROBIN")
        # Refresh cap fingerprint from registry (deterministic over fresh set).
        self._cap_fp = self.capability_registry.fingerprint(fresh_only=True)
        if hasattr(self.strategy, "last_cap_state_fp") and getattr(
            self.strategy, "last_cap_state_fp", ""
        ):
            self._cap_fp = str(self.strategy.last_cap_state_fp)

        score = getattr(self.strategy, "last_score", None)
        factors = list(getattr(self.strategy, "last_factors", []) or [])
        score_table = dict(getattr(self.strategy, "last_scores", {}) or {})

        metrics: dict[str, Any] = {
            "router_version": "R1" if sname == "CAPABILITY_AWARE" else self.VERSION,
            "decision_latency_ms": latency_ms,
            "queue_time_ms": 0.0,  # R0/R1 in-process: no async queue wait
            "eligible_count": len(eligible),
            "rr_index_before": rr_before,
            "rr_pick": rr_pick,
            "selected_node_id": selected,
            "seed": self.seed,
            "candidate_count": len(self._candidates),
            "inflight": self._inflight,
            "queue_bound": self.queue_bound,
            "strategy": sname,
            "score": score,
            "factors": factors,
            "score_table": score_table,
            "cap_state_fp": self._cap_fp,
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
            cap_state_fp=self._cap_fp,
        )

    def _commit(
        self,
        decision: RouteDecision,
        *,
        task: TaskSpec,
        advance_rr: bool,
        rr_before: int,
    ) -> RouteDecision:
        """Persist-ack guard then mutate RR / log / audit (Cycle 9 P1).

        Order:
        1. Build replay envelope
        2. If store configured → put() must ACK (else raise, no side effects)
        3. Advance RR / inflight only after ACK
        4. Append decision log + audit trail
        5. Return decision
        """
        replay = build_replay_envelope(
            task=task,
            candidates=self._candidates,
            policy=self._policy,
            seed=self.seed,
            epoch=self.epoch,
            rr_index_before=rr_before,
            decision=decision,
            strategy_name=getattr(self.strategy, "name", "ROUND_ROBIN"),
            capabilities=self.capability_registry.list_all(),
        )

        if self.store is not None:
            try:
                ack = self.store.put(decision, replay=replay)
            except CramPersistError:
                # Fail-closed: do NOT advance RR, do NOT log as committed decision.
                raise
            except Exception as exc:  # noqa: BLE001
                raise CramPersistError(
                    "C-RAM persist ack failed",
                    op_id=decision.op_id,
                    trace_id=decision.trace_id,
                    cause=str(exc),
                ) from exc
            if not ack:
                raise CramPersistError(
                    "C-RAM persist returned empty ack",
                    op_id=decision.op_id,
                    trace_id=decision.trace_id,
                )

        if advance_rr and decision.status == DecisionStatus.ACCEPTED:
            # Only RoundRobin advances a cursor; CapabilityAware is stateless.
            if hasattr(self.strategy, "advance"):
                self.strategy.advance()  # type: ignore[attr-defined]
                self._rr_index = int(getattr(self.strategy, "index", self._rr_index))
            self._inflight += 1

        self.log.append(decision)
        self.audit.record(decision)
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
    """JSON shape for `mesh router explain` (Cycle 7 + Cycle 10 factors)."""
    metrics = dict(decision.metrics or {})
    strategy_name = metrics.get("strategy") or "ROUND_ROBIN"
    # CLI-friendly alias: capability | rr (from live strategy, not reject reason)
    if strategy_name == "CAPABILITY_AWARE":
        strategy_alias = "capability"
    elif strategy_name == "ROUND_ROBIN":
        strategy_alias = "rr"
    else:
        strategy_alias = str(strategy_name)
    # Back-compat: historical explain used decision.reason as "strategy"
    # (ROUND_ROBIN on accept; SAFETY_POLICY_* / NO_CAPABLE_NODE on reject).
    status_val = (
        decision.status.value
        if hasattr(decision.status, "value")
        else str(decision.status)
    )
    if status_val == "ACCEPTED":
        strategy_display = (
            strategy_name if strategy_name in ("ROUND_ROBIN", "CAPABILITY_AWARE")
            else decision.reason
        )
    else:
        strategy_display = decision.reason
    score = metrics.get("score")
    factors = list(metrics.get("factors") or [])
    return {
        "task_id": decision.task_id,
        "decision": decision.selected_node_id,
        "selected": decision.selected_node_id,
        "status": status_val,
        "strategy": strategy_display,
        "strategy_alias": strategy_alias,
        "score": score,
        "factors": factors,
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
        "candidates_fingerprint": decision.candidates_fingerprint,
        "cap_state_fp": getattr(decision, "cap_state_fp", "") or "",
        "metrics": metrics,
    }


def replay_from_store(
    store: DecisionStore,
    trace_id: str,
) -> tuple[RouteDecision, RouteDecision]:
    """Recompute RouteDecision from stored replay envelope; return (stored, recomputed).

    Recomputed decision is produced without a store (pure function of envelope)
    so idempotent lookup does not short-circuit the recompute path. Canonical
    bytes exclude timestamp/latency and must match the stored decision.
    """
    env = store.get_envelope_by_trace_id(trace_id)
    if env is None:
        raise KeyError(f"no decision for trace_id={trace_id}")
    stored = RouteDecision.from_dict(env["decision"])
    replay = env.get("replay") or {}
    if not replay:
        return stored, stored

    task = TaskSpec.from_dict(replay["task"])
    cands = [RouteCandidate.from_dict(c) for c in replay.get("candidates", [])]
    policy = replay.get("policy")
    seed = int(replay.get("seed", stored.seed))
    epoch = int(replay.get("epoch", stored.epoch))
    rr_before = int(replay.get("rr_index_before", seed))

    strategy_name = str(replay.get("strategy") or stored.metrics.get("strategy") or "ROUND_ROBIN")
    registry = CapabilityRegistry()
    for cap_raw in replay.get("capabilities") or []:
        from .capabilities import NodeCapability

        cap = NodeCapability.from_dict(cap_raw)
        registry.upsert(
            cap,
            op_id=f"replay-cap-{cap.node_id}-{stored.op_id}",
            epoch=epoch,
            trace_id=stored.trace_id,
        )

    if strategy_name == "CAPABILITY_AWARE":
        strategy: RoutingStrategy = CapabilityAwareStrategy(registry)
    else:
        strategy = RoundRobinStrategy(index=rr_before)

    router = CognitiveRouterR0(
        cands,
        seed=seed,
        policy=policy,
        epoch=epoch,
        strategy=strategy,
        capability_registry=registry,
        decision_store=None,
    )
    # Restore inflight + rr cursor snapshot so metrics match the original commit.
    router._inflight = int(stored.metrics.get("inflight", 0))
    router._rr_index = rr_before
    if hasattr(router.strategy, "index"):
        router.strategy.index = rr_before  # type: ignore[attr-defined]
    recompute_task = TaskSpec(
        task_id=task.task_id,
        required_capabilities=task.required_capabilities,
        requires_network=task.requires_network,
        requires_physical=task.requires_physical,
        payload_hint=task.payload_hint,
        objective=task.objective,
        priority=task.priority,
        resource_requirements=dict(task.resource_requirements),
        safety_level=task.safety_level,
        state_refs=task.state_refs,
        op_id=stored.op_id,
        trace_id=stored.trace_id,
    )
    recomputed = router.route(recompute_task)
    return stored, recomputed


__all__ = [
    "CognitiveRouterR0",
    "candidates_from_topology",
    "explain_decision",
    "replay_from_store",
]
