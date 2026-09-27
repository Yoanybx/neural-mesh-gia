"""Orchestrator continuity design helpers (CP-0068 / Cycle 64).

Design-only mock: durable GoalRegistry + EvidenceLedger + ContinuityMachine,
in-flight tracker with orphan policy across LEFT/REJOIN, invocation
idempotency, resume-after-restart, timeout bounds, ABORT propagation.
Composes OrchestratorRouter (CP-0064). Substrate memory — NOT consciousness.

Mock-only: live=DISABLED, no train, no keys, no src codec, no N>2, no Raft.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from neural_mesh.packaging.m2_membership_rejoin import MemberState, TrustTierName
from neural_mesh.packaging.m3_wan_model import LatencyBand
from neural_mesh.packaging.orchestrator_judge_routing import (
    ActionClass,
    OrchestratorRouter,
    RoutingEnvelope,
    RoutingReceipt,
    WorkloadClass,
    default_registry,
    sample_envelope,
)

__all__ = [
    "PACKAGE_HELD",
    "CYCLE",
    "SEAL_CP",
    "PRIOR_CP",
    "PREFERRED_NEXT_DEFAULT",
    "LIVE_API_ENABLED",
    "SCHEMA_INFLIGHT",
    "SCHEMA_CONT_RECEIPT",
    "SCHEMA_GOAL",
    "SCHEMA_EVIDENCE",
    "SCHEMA_CONTINUITY",
    "N_CAP",
    "SOFT_TIMEOUT_UNITS",
    "HARD_TIMEOUT_UNITS",
    "ORPHAN_GRACE_UNITS",
    "TERMINAL_STATES",
    "CONT_ABORT_CODES",
    "ContinuityStateName",
    "InFlightStatus",
    "ContError",
    "GoalRecord",
    "EvidenceEntry",
    "ContinuityState",
    "InFlightRecord",
    "ContinuityReceipt",
    "GoalRegistry",
    "EvidenceLedger",
    "ContinuityMachine",
    "InFlightTracker",
    "ContinuityOrchestrator",
    "verify_evidence_chain",
    "verify_continuity_receipt_chain",
]

PACKAGE_HELD = "0.18.0"
CYCLE = 64
SEAL_CP = "CP-0068"
PRIOR_CP = "CP-0067"
PREFERRED_NEXT_DEFAULT = "await_deepseek"
LIVE_API_ENABLED = False  # must stay False (live=DISABLED)
SCHEMA_INFLIGHT = "mesh.orchestrator.inflight/v0"
SCHEMA_CONT_RECEIPT = "mesh.orchestrator.continuity_receipt/v0"
SCHEMA_GOAL = "mesh.goal/v0"
SCHEMA_EVIDENCE = "mesh.evidence/v0"
SCHEMA_CONTINUITY = "mesh.continuity/v0"
N_CAP = 2
SOFT_TIMEOUT_UNITS = 30
HARD_TIMEOUT_UNITS = 120
ORPHAN_GRACE_UNITS = 5

TERMINAL_STATES = frozenset({"SUCCEEDED", "FAILED", "ABORTED", "CANCELLED"})

CONT_ABORT_CODES: tuple[str, ...] = (
    "CONT_ORPHAN_LEFT",
    "CONT_ORPHAN_REJOIN_PENDING",
    "CONT_ORPHAN_DRAIN",
    "CONT_ORPHAN_DROP_FORBIDDEN",
    "CONT_IDEMPOTENCY_CONFLICT",
    "CONT_TIMEOUT_SOFT",
    "CONT_TIMEOUT_HARD",
    "CONT_LIVE_DISABLED",
    "CONT_N_GT2_REFUSED",
    "CONT_SCHEMA_INVALID",
    "CONT_RESUME_FORBIDDEN_TERMINAL",
    "FENCE",
)


class ContinuityStateName(str, Enum):
    PENDING = "PENDING"
    READY = "READY"
    RUNNING = "RUNNING"
    BLOCKED = "BLOCKED"
    PAUSED = "PAUSED"
    RESUMING = "RESUMING"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    ABORTED = "ABORTED"
    CANCELLED = "CANCELLED"


class InFlightStatus(str, Enum):
    OPEN = "OPEN"
    SEALED = "SEALED"
    ORPHANED = "ORPHANED"
    TIMED_OUT = "TIMED_OUT"
    ABORTED = "ABORTED"


class ContError(RuntimeError):
    """Fail-closed continuity error."""

    code: str = "CONT_ERROR"

    def __init__(self, message: str, *, code: str | None = None):
        super().__init__(message)
        if code:
            self.code = code


def _digest16(payload: dict[str, Any]) -> str:
    blob = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(blob).hexdigest()[:16]


def _sha256_obj(payload: dict[str, Any]) -> str:
    blob = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return "sha256:" + hashlib.sha256(blob).hexdigest()


@dataclass
class GoalRecord:
    goal_id: str
    version: int = 1
    content_digest: str = ""
    title: str = ""
    assignee: str = "mesh:orchestrator"
    priority: int = 0
    created_hlc: str = "hlc:0"
    updated_hlc: str = "hlc:0"
    parent_goal_id: str | None = None
    tags: list[str] = field(default_factory=list)
    terminal: bool = False
    continuity_id: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": SCHEMA_GOAL,
            "goal_id": self.goal_id,
            "version": self.version,
            "content_digest": self.content_digest,
            "title": self.title,
            "assignee": self.assignee,
            "priority": self.priority,
            "created_hlc": self.created_hlc,
            "updated_hlc": self.updated_hlc,
            "parent_goal_id": self.parent_goal_id,
            "tags": list(self.tags),
            "terminal": self.terminal,
            "continuity_id": self.continuity_id,
        }


@dataclass
class EvidenceEntry:
    entry_id: str
    goal_id: str
    kind: str
    payload_digest: str
    receipt_id: str | None = None
    prev_entry_hash: str | None = None
    created_hlc: str = "hlc:0"
    node_id: str = "node:mock"
    dual_primary: int = 0
    detail: dict[str, Any] = field(default_factory=dict)

    def content_hash(self) -> str:
        return _sha256_obj(self.to_dict_for_hash())

    def to_dict_for_hash(self) -> dict[str, Any]:
        return {
            "schema": SCHEMA_EVIDENCE,
            "entry_id": self.entry_id,
            "goal_id": self.goal_id,
            "kind": self.kind,
            "payload_digest": self.payload_digest,
            "receipt_id": self.receipt_id,
            "prev_entry_hash": self.prev_entry_hash,
            "created_hlc": self.created_hlc,
            "node_id": self.node_id,
            "dual_primary": self.dual_primary,
            "detail": self.detail,
        }


@dataclass
class ContinuityState:
    continuity_id: str
    goal_id: str
    state: ContinuityStateName = ContinuityStateName.PENDING
    step_id: str = "step:0"
    steps_done: list[str] = field(default_factory=list)
    blocker_code: str | None = None
    resume_token: str | None = None
    last_receipt_id: str | None = None
    updated_hlc: str = "hlc:0"
    last_policy: str | None = None
    last_engine_ids: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": SCHEMA_CONTINUITY,
            "continuity_id": self.continuity_id,
            "goal_id": self.goal_id,
            "state": self.state.value,
            "step_id": self.step_id,
            "steps_done": list(self.steps_done),
            "blocker": {"code": self.blocker_code, "detail_digest": None},
            "resume_token": self.resume_token,
            "last_receipt_id": self.last_receipt_id,
            "updated_hlc": self.updated_hlc,
            "last_policy": self.last_policy,
            "last_engine_ids": list(self.last_engine_ids),
        }


@dataclass
class InFlightRecord:
    invoke_id: str
    idempotency_key: str
    goal_id: str
    continuity_id: str
    request_id: str
    payload_digest: str
    engine_ids: list[str] = field(default_factory=list)
    member_state_at_start: str = "ACTIVE"
    status: InFlightStatus = InFlightStatus.OPEN
    opened_tick: int = 0
    deadline_tick: int = HARD_TIMEOUT_UNITS
    last_routing_receipt_id: str | None = None
    prev_entry_hash: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": SCHEMA_INFLIGHT,
            "invoke_id": self.invoke_id,
            "idempotency_key": self.idempotency_key,
            "goal_id": self.goal_id,
            "continuity_id": self.continuity_id,
            "request_id": self.request_id,
            "engine_ids": list(self.engine_ids),
            "member_state_at_start": self.member_state_at_start,
            "status": self.status.value,
            "opened_hlc": f"hlc:{self.opened_tick}",
            "deadline_hlc": f"hlc:{self.deadline_tick}",
            "last_routing_receipt_id": self.last_routing_receipt_id,
            "payload_digest": self.payload_digest,
            "prev_entry_hash": self.prev_entry_hash,
        }


@dataclass
class ContinuityReceipt:
    receipt_id: str
    decision: str
    continuity_state: str
    goal_id: str
    continuity_id: str
    idempotency_key: str
    invoke_id: str | None = None
    orphan_code: str | None = None
    abort_code: str | None = None
    abort_reason: str | None = None
    routing_receipt_id: str | None = None
    dual_primary: int = 0
    live_api: bool = False
    prev_receipt_hash: str | None = None
    created_hlc: str = "hlc:0"
    detail: dict[str, Any] = field(default_factory=dict)

    def content_hash(self) -> str:
        return _sha256_obj(self.to_dict())

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": SCHEMA_CONT_RECEIPT,
            "receipt_id": self.receipt_id,
            "decision": self.decision,
            "continuity_state": self.continuity_state,
            "goal_id": self.goal_id,
            "continuity_id": self.continuity_id,
            "invoke_id": self.invoke_id,
            "idempotency_key": self.idempotency_key,
            "orphan_code": self.orphan_code,
            "abort": {"code": self.abort_code, "reason": self.abort_reason}
            if self.abort_code
            else None,
            "routing_receipt_id": self.routing_receipt_id,
            "dual_primary": self.dual_primary,
            "live_api": self.live_api,
            "prev_receipt_hash": self.prev_receipt_hash,
            "created_hlc": self.created_hlc,
            "detail": self.detail,
        }


class GoalRegistry:
    def __init__(self) -> None:
        self._goals: dict[str, GoalRecord] = {}

    def put(self, goal: GoalRecord) -> GoalRecord:
        self._goals[goal.goal_id] = goal
        return goal

    def get(self, goal_id: str) -> GoalRecord:
        if goal_id not in self._goals:
            raise ContError(f"unknown goal {goal_id}", code="CONT_SCHEMA_INVALID")
        return self._goals[goal_id]

    def list_open(self) -> list[GoalRecord]:
        return [g for g in self._goals.values() if not g.terminal]

    def ensure(
        self,
        goal_id: str,
        continuity_id: str,
        title: str = "orchestrator-goal",
        tick: int = 0,
    ) -> GoalRecord:
        if goal_id in self._goals:
            return self._goals[goal_id]
        digest = _sha256_obj({"goal_id": goal_id, "title": title, "v": 1})
        g = GoalRecord(
            goal_id=goal_id,
            content_digest=digest,
            title=title,
            created_hlc=f"hlc:{tick}",
            updated_hlc=f"hlc:{tick}",
            continuity_id=continuity_id,
        )
        return self.put(g)


class EvidenceLedger:
    def __init__(self) -> None:
        self._by_goal: dict[str, list[EvidenceEntry]] = {}

    def append(self, entry: EvidenceEntry) -> EvidenceEntry:
        chain = self._by_goal.setdefault(entry.goal_id, [])
        if chain:
            entry.prev_entry_hash = chain[-1].content_hash()
        else:
            entry.prev_entry_hash = None
        if entry.dual_primary != 0:
            raise ContError("dual_primary must be 0", code="FENCE")
        chain.append(entry)
        return entry

    def chain(self, goal_id: str) -> list[EvidenceEntry]:
        return list(self._by_goal.get(goal_id, []))

    def verify(self, goal_id: str) -> bool:
        return verify_evidence_chain(self.chain(goal_id))


def verify_evidence_chain(entries: list[EvidenceEntry]) -> bool:
    prev: str | None = None
    for e in entries:
        if e.prev_entry_hash != prev:
            return False
        if e.dual_primary != 0:
            return False
        prev = e.content_hash()
    return True


class ContinuityMachine:
    def __init__(self) -> None:
        self._states: dict[str, ContinuityState] = {}

    def ensure(self, continuity_id: str, goal_id: str, tick: int = 0) -> ContinuityState:
        if continuity_id in self._states:
            return self._states[continuity_id]
        st = ContinuityState(
            continuity_id=continuity_id,
            goal_id=goal_id,
            state=ContinuityStateName.READY,
            updated_hlc=f"hlc:{tick}",
            resume_token=f"rt:{_digest16({'c': continuity_id})}",
        )
        self._states[continuity_id] = st
        return st

    def load(self, continuity_id: str) -> ContinuityState:
        if continuity_id not in self._states:
            raise ContError(f"unknown continuity {continuity_id}", code="CONT_SCHEMA_INVALID")
        return self._states[continuity_id]

    def transition(
        self,
        continuity_id: str,
        new_state: ContinuityStateName,
        *,
        tick: int = 0,
        blocker_code: str | None = None,
        receipt_id: str | None = None,
        policy: str | None = None,
        engine_ids: list[str] | None = None,
        step: str | None = None,
    ) -> ContinuityState:
        st = self.load(continuity_id)
        if st.state.value in TERMINAL_STATES and new_state.value not in TERMINAL_STATES:
            # immutable terminal except audited supersede (not modeled as silent flip)
            raise ContError(
                "terminal continuity immutable",
                code="CONT_RESUME_FORBIDDEN_TERMINAL",
            )
        if st.state.value in TERMINAL_STATES and new_state != st.state:
            raise ContError(
                "terminal continuity immutable",
                code="CONT_RESUME_FORBIDDEN_TERMINAL",
            )
        st.state = new_state
        st.updated_hlc = f"hlc:{tick}"
        st.blocker_code = blocker_code
        if receipt_id:
            st.last_receipt_id = receipt_id
        if policy:
            st.last_policy = policy
        if engine_ids is not None:
            st.last_engine_ids = list(engine_ids)
        if step:
            if step not in st.steps_done:
                st.steps_done.append(step)
            st.step_id = step
        return st


class InFlightTracker:
    def __init__(self) -> None:
        self._by_key: dict[str, InFlightRecord] = {}
        self._by_id: dict[str, InFlightRecord] = {}

    def open(
        self,
        *,
        idempotency_key: str,
        goal_id: str,
        continuity_id: str,
        request_id: str,
        payload_digest: str,
        member_state: str,
        tick: int,
        hard_timeout: int = HARD_TIMEOUT_UNITS,
    ) -> tuple[InFlightRecord, bool]:
        """Return (record, is_replay). is_replay True => caller must not re-invoke."""
        existing = self._by_key.get(idempotency_key)
        if existing is not None:
            if existing.payload_digest != payload_digest:
                raise ContError(
                    "idempotency key conflict",
                    code="CONT_IDEMPOTENCY_CONFLICT",
                )
            return existing, True
        invoke_id = "inv:" + _digest16(
            {
                "key": idempotency_key,
                "goal": goal_id,
                "req": request_id,
                "tick": tick,
            }
        )
        rec = InFlightRecord(
            invoke_id=invoke_id,
            idempotency_key=idempotency_key,
            goal_id=goal_id,
            continuity_id=continuity_id,
            request_id=request_id,
            payload_digest=payload_digest,
            member_state_at_start=member_state,
            status=InFlightStatus.OPEN,
            opened_tick=tick,
            deadline_tick=tick + hard_timeout,
        )
        self._by_key[idempotency_key] = rec
        self._by_id[invoke_id] = rec
        return rec, False

    def get(self, invoke_id: str) -> InFlightRecord:
        if invoke_id not in self._by_id:
            raise ContError(f"unknown invoke {invoke_id}", code="CONT_SCHEMA_INVALID")
        return self._by_id[invoke_id]

    def get_by_key(self, key: str) -> InFlightRecord | None:
        return self._by_key.get(key)

    def seal(self, invoke_id: str, *, status: InFlightStatus, routing_receipt_id: str | None = None) -> InFlightRecord:
        rec = self.get(invoke_id)
        rec.status = status
        if routing_receipt_id:
            rec.last_routing_receipt_id = routing_receipt_id
        return rec

    def open_invokes(self) -> list[InFlightRecord]:
        return [r for r in self._by_id.values() if r.status == InFlightStatus.OPEN]


class ContinuityOrchestrator:
    """Mesh continuity plane wrapping OrchestratorRouter."""

    def __init__(
        self,
        router: OrchestratorRouter | None = None,
        *,
        soft_timeout: int = SOFT_TIMEOUT_UNITS,
        hard_timeout: int = HARD_TIMEOUT_UNITS,
        orphan_grace: int = ORPHAN_GRACE_UNITS,
    ) -> None:
        self.router = router or OrchestratorRouter(registry=default_registry())
        self.registry = GoalRegistry()
        self.ledger = EvidenceLedger()
        self.machine = ContinuityMachine()
        self.inflight = InFlightTracker()
        self.soft_timeout = soft_timeout
        self.hard_timeout = hard_timeout
        self.orphan_grace = orphan_grace
        self.tick = 0
        self.receipts: list[ContinuityReceipt] = []
        self._prev_receipt_hash: str | None = None
        self.invoke_count = 0  # counts real router delegations (not replays)

    def _hlc(self) -> str:
        return f"hlc:{self.tick}"

    def advance_time(self, units: int = 1) -> None:
        self.tick += units

    def _append_evidence(
        self,
        *,
        goal_id: str,
        kind: str,
        payload: dict[str, Any],
        receipt_id: str | None = None,
    ) -> EvidenceEntry:
        entry_id = "ev:" + _digest16({"g": goal_id, "k": kind, "t": self.tick, "p": payload})
        entry = EvidenceEntry(
            entry_id=entry_id,
            goal_id=goal_id,
            kind=kind,
            payload_digest=_sha256_obj(payload),
            receipt_id=receipt_id,
            created_hlc=self._hlc(),
            dual_primary=0,
            detail=payload,
        )
        return self.ledger.append(entry)

    def _emit_receipt(
        self,
        *,
        decision: str,
        state: ContinuityState,
        idempotency_key: str,
        invoke_id: str | None = None,
        orphan_code: str | None = None,
        abort_code: str | None = None,
        abort_reason: str | None = None,
        routing_receipt_id: str | None = None,
        detail: dict[str, Any] | None = None,
    ) -> ContinuityReceipt:
        body = {
            "decision": decision,
            "state": state.state.value,
            "goal": state.goal_id,
            "cont": state.continuity_id,
            "key": idempotency_key,
            "tick": self.tick,
            "orphan": orphan_code,
            "abort": abort_code,
        }
        rcpt = ContinuityReceipt(
            receipt_id="rcpt:" + _digest16(body),
            decision=decision,
            continuity_state=state.state.value,
            goal_id=state.goal_id,
            continuity_id=state.continuity_id,
            idempotency_key=idempotency_key,
            invoke_id=invoke_id,
            orphan_code=orphan_code,
            abort_code=abort_code,
            abort_reason=abort_reason,
            routing_receipt_id=routing_receipt_id,
            dual_primary=0,
            live_api=False,
            prev_receipt_hash=self._prev_receipt_hash,
            created_hlc=self._hlc(),
            detail=detail or {},
        )
        self.receipts.append(rcpt)
        self._prev_receipt_hash = rcpt.content_hash()
        return rcpt

    def _payload_digest(self, env: RoutingEnvelope, idempotency_key: str) -> str:
        return _sha256_obj(
            {
                "key": idempotency_key,
                "goal_id": env.goal_id,
                "continuity_id": env.continuity_id,
                "workload_class": env.workload_class.value,
                "action_class": env.action_class.value,
                "prompt_body": env.prompt_body,
                "request_id": env.request_id,
            }
        )

    def invoke(
        self,
        env: RoutingEnvelope,
        *,
        idempotency_key: str,
        title: str = "orchestrator-goal",
    ) -> ContinuityReceipt:
        # Hard safety gates (continuity plane)
        if env.live_api_enabled or LIVE_API_ENABLED:
            return self._fail_schema(
                env,
                idempotency_key,
                "CONT_LIVE_DISABLED",
                "live path disabled",
            )
        if env.dual_primary != 0:
            return self._fail_schema(env, idempotency_key, "FENCE", "dual_primary != 0")
        if env.n_members > N_CAP:
            return self._fail_schema(
                env,
                idempotency_key,
                "CONT_N_GT2_REFUSED",
                "N>2 refused",
            )
        if not env.goal_id or not env.continuity_id or not idempotency_key:
            return self._fail_schema(
                env,
                idempotency_key or "idem:missing",
                "CONT_SCHEMA_INVALID",
                "goal_id, continuity_id, idempotency_key required",
            )

        self.registry.ensure(env.goal_id, env.continuity_id, title=title, tick=self.tick)
        st = self.machine.ensure(env.continuity_id, env.goal_id, tick=self.tick)
        if st.state.value in TERMINAL_STATES:
            return self._emit_receipt(
                decision="ABORT",
                state=st,
                idempotency_key=idempotency_key,
                abort_code="CONT_RESUME_FORBIDDEN_TERMINAL",
                abort_reason="invoke on terminal continuity",
            )

        # Member must be ACTIVE for new work (orphan path handled separately)
        if env.member_state != MemberState.ACTIVE:
            return self._member_gate_abort(env, idempotency_key, st)

        payload_digest = self._payload_digest(env, idempotency_key)
        try:
            rec, is_replay = self.inflight.open(
                idempotency_key=idempotency_key,
                goal_id=env.goal_id,
                continuity_id=env.continuity_id,
                request_id=env.request_id,
                payload_digest=payload_digest,
                member_state=env.member_state.value,
                tick=self.tick,
                hard_timeout=self.hard_timeout,
            )
        except ContError as e:
            self.machine.transition(
                env.continuity_id,
                ContinuityStateName.ABORTED,
                tick=self.tick,
                blocker_code=e.code,
            )
            st = self.machine.load(env.continuity_id)
            self._append_evidence(
                goal_id=env.goal_id,
                kind="abort",
                payload={"code": e.code, "msg": str(e)},
            )
            return self._emit_receipt(
                decision="ABORT",
                state=st,
                idempotency_key=idempotency_key,
                abort_code=e.code,
                abort_reason=str(e),
            )

        if is_replay:
            # No double-invoke: return prior continuity receipt if any, else synthesize from sealed
            for prev in reversed(self.receipts):
                if prev.idempotency_key == idempotency_key and prev.invoke_id == rec.invoke_id:
                    return prev
            # Still open replay — return BLOCKED-style replay marker without re-route
            return self._emit_receipt(
                decision="ALLOW" if rec.status == InFlightStatus.SEALED else "BLOCKED",
                state=st,
                idempotency_key=idempotency_key,
                invoke_id=rec.invoke_id,
                routing_receipt_id=rec.last_routing_receipt_id,
                detail={"replay": True, "inflight_status": rec.status.value},
            )

        self._append_evidence(
            goal_id=env.goal_id,
            kind="invoke_start",
            payload=rec.to_dict(),
        )
        self.machine.transition(
            env.continuity_id,
            ContinuityStateName.RUNNING,
            tick=self.tick,
            step=f"step:invoke:{rec.invoke_id[-8:]}",
        )
        st = self.machine.load(env.continuity_id)

        # Delegate to routing
        self.invoke_count += 1
        decision = self.router.route(env)
        routing_rcpt: RoutingReceipt | None = decision.receipt
        routing_id = routing_rcpt.receipt_id if routing_rcpt else None

        if decision.allow:
            self.inflight.seal(
                rec.invoke_id,
                status=InFlightStatus.SEALED,
                routing_receipt_id=routing_id,
            )
            self._append_evidence(
                goal_id=env.goal_id,
                kind="routing_receipt",
                payload=routing_rcpt.to_dict() if routing_rcpt else {"allow": True},
                receipt_id=routing_id,
            )
            self._append_evidence(
                goal_id=env.goal_id,
                kind="invoke_end",
                payload={"invoke_id": rec.invoke_id, "status": "SEALED"},
                receipt_id=routing_id,
            )
            self.machine.transition(
                env.continuity_id,
                ContinuityStateName.RUNNING,
                tick=self.tick,
                receipt_id=routing_id,
                policy=decision.policy.value if decision.policy else None,
                engine_ids=list(decision.engine_ids),
            )
            st = self.machine.load(env.continuity_id)
            return self._emit_receipt(
                decision="ALLOW",
                state=st,
                idempotency_key=idempotency_key,
                invoke_id=rec.invoke_id,
                routing_receipt_id=routing_id,
            )

        # Routing ABORT
        code = decision.abort_code or (routing_rcpt.abort_code if routing_rcpt else None) or "ROUTE_ABORT"
        reason = decision.reason or (routing_rcpt.abort_reason if routing_rcpt else "") or "routing abort"
        # Map member/drain style to continuity states
        if code in {"ROUTE_MEMBER_DRAINING"}:
            new_state = ContinuityStateName.BLOCKED
            inflight_status = InFlightStatus.ORPHANED
        elif code in {"ROUTE_LIVE_DISABLED", "FENCE", "ROUTE_N_GT2_REFUSED"}:
            new_state = ContinuityStateName.ABORTED
            inflight_status = InFlightStatus.ABORTED
        else:
            new_state = ContinuityStateName.BLOCKED
            inflight_status = InFlightStatus.ABORTED

        self.inflight.seal(rec.invoke_id, status=inflight_status, routing_receipt_id=routing_id)
        self._append_evidence(
            goal_id=env.goal_id,
            kind="abort",
            payload={"code": code, "reason": reason},
            receipt_id=routing_id,
        )
        self.machine.transition(
            env.continuity_id,
            new_state,
            tick=self.tick,
            blocker_code=code,
            receipt_id=routing_id,
        )
        st = self.machine.load(env.continuity_id)
        return self._emit_receipt(
            decision="ABORT" if new_state == ContinuityStateName.ABORTED else "BLOCKED",
            state=st,
            idempotency_key=idempotency_key,
            invoke_id=rec.invoke_id,
            abort_code=code,
            abort_reason=reason,
            routing_receipt_id=routing_id,
        )

    def _fail_schema(
        self,
        env: RoutingEnvelope,
        idempotency_key: str,
        code: str,
        reason: str,
    ) -> ContinuityReceipt:
        # Ensure minimal state for receipt emission
        cid = env.continuity_id or "cont:0000000000000000"
        gid = env.goal_id or "goal:0000000000000000"
        try:
            st = self.machine.load(cid)
        except ContError:
            self.registry.ensure(gid, cid, tick=self.tick)
            st = self.machine.ensure(cid, gid, tick=self.tick)
        if st.state.value not in TERMINAL_STATES:
            self.machine.transition(
                cid,
                ContinuityStateName.ABORTED,
                tick=self.tick,
                blocker_code=code,
            )
            st = self.machine.load(cid)
        self._append_evidence(
            goal_id=gid,
            kind="abort",
            payload={"code": code, "reason": reason},
        )
        return self._emit_receipt(
            decision="ABORT",
            state=st,
            idempotency_key=idempotency_key,
            abort_code=code,
            abort_reason=reason,
        )

    def _member_gate_abort(
        self,
        env: RoutingEnvelope,
        idempotency_key: str,
        st: ContinuityState,
    ) -> ContinuityReceipt:
        ms = env.member_state
        if ms == MemberState.DRAINING:
            code = "CONT_ORPHAN_DRAIN"
            new_state = ContinuityStateName.BLOCKED
            decision = "BLOCKED"
        elif ms == MemberState.LEFT:
            code = "CONT_ORPHAN_LEFT"
            new_state = ContinuityStateName.ABORTED
            decision = "ABORT"
        elif ms in {MemberState.REJOIN, MemberState.JOINING, MemberState.ATTESTING}:
            code = "CONT_ORPHAN_REJOIN_PENDING"
            new_state = ContinuityStateName.BLOCKED
            decision = "BLOCKED"
        else:
            code = "ROUTE_MEMBER_NOT_ACTIVE"
            new_state = ContinuityStateName.BLOCKED
            decision = "BLOCKED"
        self.machine.transition(
            env.continuity_id,
            new_state,
            tick=self.tick,
            blocker_code=code,
        )
        st = self.machine.load(env.continuity_id)
        self._append_evidence(
            goal_id=env.goal_id,
            kind="orphan",
            payload={"code": code, "member_state": ms.value},
        )
        return self._emit_receipt(
            decision=decision,
            state=st,
            idempotency_key=idempotency_key,
            orphan_code=code,
            abort_code=code if decision == "ABORT" else None,
            abort_reason=f"member_state={ms.value}",
        )

    def begin_invoke(
        self,
        env: RoutingEnvelope,
        *,
        idempotency_key: str,
        title: str = "orchestrator-goal",
    ) -> InFlightRecord:
        """Open an in-flight invoke without routing (for mid-flight orphan tests)."""
        if env.live_api_enabled or LIVE_API_ENABLED:
            raise ContError("live path disabled", code="CONT_LIVE_DISABLED")
        if env.dual_primary != 0:
            raise ContError("dual_primary != 0", code="FENCE")
        if env.n_members > N_CAP:
            raise ContError("N>2 refused", code="CONT_N_GT2_REFUSED")
        if not env.goal_id or not env.continuity_id or not idempotency_key:
            raise ContError("schema invalid", code="CONT_SCHEMA_INVALID")
        if env.member_state != MemberState.ACTIVE:
            raise ContError(
                f"member not active: {env.member_state.value}",
                code="ROUTE_MEMBER_NOT_ACTIVE",
            )
        self.registry.ensure(env.goal_id, env.continuity_id, title=title, tick=self.tick)
        st = self.machine.ensure(env.continuity_id, env.goal_id, tick=self.tick)
        if st.state.value in TERMINAL_STATES:
            raise ContError("terminal", code="CONT_RESUME_FORBIDDEN_TERMINAL")
        payload_digest = self._payload_digest(env, idempotency_key)
        rec, is_replay = self.inflight.open(
            idempotency_key=idempotency_key,
            goal_id=env.goal_id,
            continuity_id=env.continuity_id,
            request_id=env.request_id,
            payload_digest=payload_digest,
            member_state=env.member_state.value,
            tick=self.tick,
            hard_timeout=self.hard_timeout,
        )
        if is_replay and rec.status == InFlightStatus.OPEN:
            return rec
        if is_replay:
            raise ContError("idempotency key already sealed", code="CONT_IDEMPOTENCY_CONFLICT")
        self._append_evidence(goal_id=env.goal_id, kind="invoke_start", payload=rec.to_dict())
        self.machine.transition(
            env.continuity_id,
            ContinuityStateName.RUNNING,
            tick=self.tick,
            step=f"step:begin:{rec.invoke_id[-8:]}",
        )
        return rec

    def notify_member_churn(

        self,
        *,
        goal_id: str,
        continuity_id: str,
        new_state: MemberState,
        allow_silent_drop: bool = False,
    ) -> list[ContinuityReceipt]:
        """Apply orphan policy to all OPEN in-flights for goal/continuity."""
        if allow_silent_drop:
            # Forbidden — always audit
            st = self.machine.ensure(continuity_id, goal_id, tick=self.tick)
            self._append_evidence(
                goal_id=goal_id,
                kind="abort",
                payload={"code": "CONT_ORPHAN_DROP_FORBIDDEN"},
            )
            rcpt = self._emit_receipt(
                decision="ABORT",
                state=st,
                idempotency_key="idem:drop-forbidden",
                orphan_code="CONT_ORPHAN_DROP_FORBIDDEN",
                abort_code="CONT_ORPHAN_DROP_FORBIDDEN",
                abort_reason="silent drop forbidden",
            )
            return [rcpt]

        out: list[ContinuityReceipt] = []
        for rec in list(self.inflight.open_invokes()):
            if rec.goal_id != goal_id or rec.continuity_id != continuity_id:
                continue
            if new_state == MemberState.DRAINING:
                code = "CONT_ORPHAN_DRAIN"
                cont_state = ContinuityStateName.BLOCKED
                decision = "BLOCKED"
                inflight_status = InFlightStatus.ORPHANED
            elif new_state == MemberState.LEFT:
                code = "CONT_ORPHAN_LEFT"
                cont_state = ContinuityStateName.ABORTED
                decision = "ABORT"
                inflight_status = InFlightStatus.ORPHANED
            elif new_state in {MemberState.REJOIN, MemberState.JOINING, MemberState.ATTESTING}:
                code = "CONT_ORPHAN_REJOIN_PENDING"
                cont_state = ContinuityStateName.BLOCKED
                decision = "BLOCKED"
                inflight_status = InFlightStatus.ORPHANED
            else:
                continue
            self.inflight.seal(rec.invoke_id, status=inflight_status)
            self.machine.transition(
                continuity_id,
                cont_state,
                tick=self.tick,
                blocker_code=code,
            )
            st = self.machine.load(continuity_id)
            self._append_evidence(
                goal_id=goal_id,
                kind="orphan",
                payload={
                    "code": code,
                    "invoke_id": rec.invoke_id,
                    "member_state": new_state.value,
                },
            )
            out.append(
                self._emit_receipt(
                    decision=decision,
                    state=st,
                    idempotency_key=rec.idempotency_key,
                    invoke_id=rec.invoke_id,
                    orphan_code=code,
                    abort_code=code if decision == "ABORT" else None,
                    abort_reason=f"churn:{new_state.value}",
                )
            )
        return out

    def check_timeouts(self, *, goal_id: str, continuity_id: str) -> list[ContinuityReceipt]:
        out: list[ContinuityReceipt] = []
        for rec in list(self.inflight.open_invokes()):
            if rec.goal_id != goal_id or rec.continuity_id != continuity_id:
                continue
            age = self.tick - rec.opened_tick
            if age >= self.hard_timeout or self.tick >= rec.deadline_tick:
                self.inflight.seal(rec.invoke_id, status=InFlightStatus.TIMED_OUT)
                self.machine.transition(
                    continuity_id,
                    ContinuityStateName.FAILED,
                    tick=self.tick,
                    blocker_code="CONT_TIMEOUT_HARD",
                )
                st = self.machine.load(continuity_id)
                self._append_evidence(
                    goal_id=goal_id,
                    kind="timeout",
                    payload={"code": "CONT_TIMEOUT_HARD", "invoke_id": rec.invoke_id},
                )
                out.append(
                    self._emit_receipt(
                        decision="ABORT",
                        state=st,
                        idempotency_key=rec.idempotency_key,
                        invoke_id=rec.invoke_id,
                        abort_code="CONT_TIMEOUT_HARD",
                        abort_reason="hard timeout",
                    )
                )
            elif age >= self.soft_timeout:
                self.machine.transition(
                    continuity_id,
                    ContinuityStateName.BLOCKED,
                    tick=self.tick,
                    blocker_code="CONT_TIMEOUT_SOFT",
                )
                st = self.machine.load(continuity_id)
                self._append_evidence(
                    goal_id=goal_id,
                    kind="timeout",
                    payload={"code": "CONT_TIMEOUT_SOFT", "invoke_id": rec.invoke_id},
                )
                out.append(
                    self._emit_receipt(
                        decision="BLOCKED",
                        state=st,
                        idempotency_key=rec.idempotency_key,
                        invoke_id=rec.invoke_id,
                        abort_code="CONT_TIMEOUT_SOFT",
                        abort_reason="soft timeout",
                    )
                )
        return out

    def resume_after_restart(
        self,
        continuity_id: str,
        *,
        member_state: MemberState = MemberState.ACTIVE,
        trust_tier: TrustTierName = TrustTierName.T2,
        latency_band: LatencyBand = LatencyBand.RTT_mid,
        dual_primary: int = 0,
        n_members: int = 2,
        live_api_enabled: bool = False,
        idempotency_key: str = "idem:resume",
    ) -> ContinuityReceipt:
        st = self.machine.load(continuity_id)
        goal = self.registry.get(st.goal_id)
        # Never from engine chat — ledger must verify
        if not self.ledger.verify(goal.goal_id):
            raise ContError("ledger chain broken", code="CONT_SCHEMA_INVALID")

        if st.state.value in TERMINAL_STATES:
            return self._emit_receipt(
                decision="ABORT",
                state=st,
                idempotency_key=idempotency_key,
                abort_code="CONT_RESUME_FORBIDDEN_TERMINAL",
                abort_reason="cannot resume terminal",
            )
        if live_api_enabled or LIVE_API_ENABLED:
            return self._emit_receipt(
                decision="ABORT",
                state=st,
                idempotency_key=idempotency_key,
                abort_code="CONT_LIVE_DISABLED",
                abort_reason="live disabled",
            )
        if dual_primary != 0:
            return self._emit_receipt(
                decision="ABORT",
                state=st,
                idempotency_key=idempotency_key,
                abort_code="FENCE",
                abort_reason="dual_primary",
            )
        if n_members > N_CAP:
            return self._emit_receipt(
                decision="ABORT",
                state=st,
                idempotency_key=idempotency_key,
                abort_code="CONT_N_GT2_REFUSED",
                abort_reason="N>2",
            )
        if member_state != MemberState.ACTIVE or trust_tier not in {
            TrustTierName.T2,
            TrustTierName.T3,
        }:
            self.machine.transition(
                continuity_id,
                ContinuityStateName.BLOCKED,
                tick=self.tick,
                blocker_code="CONT_ORPHAN_REJOIN_PENDING",
            )
            st = self.machine.load(continuity_id)
            self._append_evidence(
                goal_id=goal.goal_id,
                kind="resume",
                payload={"blocked": True, "member_state": member_state.value},
            )
            return self._emit_receipt(
                decision="BLOCKED",
                state=st,
                idempotency_key=idempotency_key,
                orphan_code="CONT_ORPHAN_REJOIN_PENDING",
                detail={"resume": True},
            )

        self.machine.transition(
            continuity_id,
            ContinuityStateName.RESUMING,
            tick=self.tick,
        )
        env = sample_envelope(
            workload_class=WorkloadClass.CONTINUITY_RESUME,
            action_class=ActionClass.A1,
            member_state=member_state,
            trust_tier=trust_tier,
            latency_band=latency_band,
            goal_id=goal.goal_id,
            continuity_id=continuity_id,
            dual_primary=dual_primary,
            n_members=n_members,
            live_api_enabled=False,
            prior_engine_ids=tuple(st.last_engine_ids),
        )
        # Fresh idempotency for resume route (distinct from prior invoke keys)
        rcpt = self.invoke(env, idempotency_key=idempotency_key, title=goal.title)
        self._append_evidence(
            goal_id=goal.goal_id,
            kind="resume",
            payload={
                "continuity_id": continuity_id,
                "decision": rcpt.decision,
                "state": rcpt.continuity_state,
            },
            receipt_id=rcpt.receipt_id,
        )
        return rcpt


def verify_continuity_receipt_chain(receipts: list[ContinuityReceipt]) -> bool:
    prev: str | None = None
    for r in receipts:
        if r.prev_receipt_hash != prev:
            return False
        if r.dual_primary != 0 or r.live_api is not False:
            return False
        prev = r.content_hash()
    return True
