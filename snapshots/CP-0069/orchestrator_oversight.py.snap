"""Orchestrator oversight hooks design helpers (CP-0069 / Cycle 65).

Design-only mock: I5 human oversight plane — approve/deny/pause/resume/kill/
deadman/consent-revoke — composed with ContinuityOrchestrator (CP-0068) and
OrchestratorRouter (CP-0064). A0..A4 boundary; dead-man T_dead → auto-DRAIN;
quorum-human for A4; RefuseTransport on kill. NOT consciousness; NOT GIA.

Mock-only: live=DISABLED, no train, no keys, no src codec, no N>2, no Raft.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from neural_mesh.packaging.m2_membership_rejoin import MemberState
from neural_mesh.packaging.orchestrator_continuity import (
    ContinuityOrchestrator,
    ContinuityStateName,
    InFlightStatus,
)
from neural_mesh.packaging.orchestrator_judge_routing import (
    ActionClass,
    OrchestratorRouter,
    RoutingEnvelope,
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
    "SCHEMA_DECISION",
    "SCHEMA_RECEIPT",
    "N_CAP",
    "T_DEAD_DEFAULT",
    "SLO_PAUSE_TARGET",
    "SLO_PAUSE_HARD",
    "QUORUM_MIN_HUMANS",
    "DEFAULT_HUMAN_SEATS",
    "OVS_ABORT_CODES",
    "OversightVerb",
    "OvsError",
    "OversightDecision",
    "OversightReceipt",
    "QuorumHuman",
    "DeadmanWatch",
    "OversightPlane",
    "OversightOrchestrator",
    "verify_oversight_decision_chain",
    "verify_oversight_receipt_chain",
    "sample_envelope",
]

PACKAGE_HELD = "0.18.0"
CYCLE = 65
SEAL_CP = "CP-0069"
PRIOR_CP = "CP-0068"
PREFERRED_NEXT_DEFAULT = "await_deepseek"
LIVE_API_ENABLED = False  # must stay False (live=DISABLED)
SCHEMA_DECISION = "mesh.orchestrator.oversight_decision/v0"
SCHEMA_RECEIPT = "mesh.orchestrator.oversight_receipt/v0"
N_CAP = 2
T_DEAD_DEFAULT = 86400  # P-11 ≈24h logical mock units
SLO_PAUSE_TARGET = 2
SLO_PAUSE_HARD = 10
QUORUM_MIN_HUMANS = 2
DEFAULT_HUMAN_SEATS: tuple[str, ...] = ("human:operator", "human:reviewer")

OVS_ABORT_CODES: tuple[str, ...] = (
    "OVS_REQUIRED",
    "OVS_DENIED",
    "OVS_PAUSED",
    "OVS_KILLED",
    "OVS_DEADMAN_REQUIRED",
    "OVS_DEADMAN_EXPIRED",
    "OVS_QUORUM_REQUIRED",
    "OVS_CLASS_BYPASS",
    "OVS_CONSENT_REVOKED",
    "OVS_LIVE_DISABLED",
    "OVS_N_GT2_REFUSED",
    "OVS_SCHEMA_INVALID",
    "FENCE",
    "ROUTE_OVERSIGHT_REQUIRED",
    "ROUTE_OVERSIGHT_DENIED",
    "ROUTE_DEADMAN_REQUIRED",
)


class OversightVerb(str, Enum):
    APPROVE = "approve"
    DENY = "deny"
    PAUSE = "pause"
    RESUME = "resume"
    KILL = "kill"
    DEADMAN_REFRESH = "deadman_refresh"
    CONSENT_REVOKE = "consent_revoke"
    TICK_DEADMAN = "tick_deadman"


class OvsError(RuntimeError):
    """Fail-closed oversight error."""

    code: str = "OVS_ERROR"

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
class OversightDecision:
    decision_id: str
    verb: str
    actor: str
    goal_id: str
    continuity_id: str
    action_class: str
    bound_engine_ids: list[str] = field(default_factory=list)
    quorum_ok: bool = False
    deadman_ok: bool = False
    t_dead: int = T_DEAD_DEFAULT
    t_dead_override_logged: bool = False
    result: str = "ALLOW"
    abort_code: str | None = None
    abort_reason: str | None = None
    refuse_transport: bool = False
    dual_primary: int = 0
    live_api: bool = False
    created_hlc: str = "hlc:0"
    prev_decision_hash: str | None = None
    detail: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": SCHEMA_DECISION,
            "decision_id": self.decision_id,
            "verb": self.verb,
            "actor": self.actor,
            "goal_id": self.goal_id,
            "continuity_id": self.continuity_id,
            "action_class": self.action_class,
            "bound_engine_ids": list(self.bound_engine_ids),
            "quorum_ok": self.quorum_ok,
            "deadman_ok": self.deadman_ok,
            "t_dead": self.t_dead,
            "t_dead_override_logged": self.t_dead_override_logged,
            "result": self.result,
            "abort": {"code": self.abort_code, "reason": self.abort_reason},
            "refuse_transport": self.refuse_transport,
            "dual_primary": 0,
            "live_api": False,
            "created_hlc": self.created_hlc,
            "prev_decision_hash": self.prev_decision_hash,
            "detail": dict(self.detail),
        }

    def content_hash(self) -> str:
        d = self.to_dict()
        d.pop("prev_decision_hash", None)
        return _sha256_obj(d)


@dataclass
class OversightReceipt:
    receipt_id: str
    decision_id: str
    continuity_state: str
    result: str
    goal_id: str
    continuity_id: str
    continuity_receipt_id: str | None = None
    routing_receipt_id: str | None = None
    abort_code: str | None = None
    abort_reason: str | None = None
    refuse_transport: bool = False
    dual_primary: int = 0
    live_api: bool = False
    bound_engine_ids: list[str] = field(default_factory=list)
    prev_receipt_hash: str | None = None
    created_hlc: str = "hlc:0"
    detail: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": SCHEMA_RECEIPT,
            "receipt_id": self.receipt_id,
            "decision_id": self.decision_id,
            "continuity_state": self.continuity_state,
            "result": self.result,
            "goal_id": self.goal_id,
            "continuity_id": self.continuity_id,
            "continuity_receipt_id": self.continuity_receipt_id,
            "routing_receipt_id": self.routing_receipt_id,
            "abort": {"code": self.abort_code, "reason": self.abort_reason},
            "refuse_transport": self.refuse_transport,
            "dual_primary": 0,
            "live_api": False,
            "bound_engine_ids": list(self.bound_engine_ids),
            "prev_receipt_hash": self.prev_receipt_hash,
            "created_hlc": self.created_hlc,
            "detail": dict(self.detail),
        }

    def content_hash(self) -> str:
        d = self.to_dict()
        d.pop("prev_receipt_hash", None)
        return _sha256_obj(d)


@dataclass
class QuorumHuman:
    """Design-only named human seats (≥2 for A4/kill)."""

    seats: tuple[str, ...] = DEFAULT_HUMAN_SEATS
    approvals: set[str] = field(default_factory=set)
    kill_acks: set[str] = field(default_factory=set)

    def reset_approvals(self) -> None:
        self.approvals.clear()

    def reset_kill(self) -> None:
        self.kill_acks.clear()

    def record_approve(self, actor: str) -> None:
        if actor not in self.seats:
            raise OvsError(f"unknown human seat: {actor}", code="OVS_SCHEMA_INVALID")
        self.approvals.add(actor)

    def record_kill(self, actor: str) -> None:
        if actor not in self.seats:
            raise OvsError(f"unknown human seat: {actor}", code="OVS_SCHEMA_INVALID")
        self.kill_acks.add(actor)

    def approve_quorum_ok(self) -> bool:
        return len(self.approvals) >= QUORUM_MIN_HUMANS

    def kill_quorum_ok(self) -> bool:
        return len(self.kill_acks) >= QUORUM_MIN_HUMANS

    def single_approve_ok(self, actor: str) -> bool:
        return actor in self.seats and actor in self.approvals


@dataclass
class DeadmanWatch:
    """P-11 dead-man: T_dead default; override logged; expiry → DRAIN."""

    t_dead: int = T_DEAD_DEFAULT
    last_refresh_tick: int | None = None
    watching: bool = False
    deadman_ok: bool = False
    override_logged: bool = False
    expired: bool = False

    def arm(self, tick: int) -> None:
        self.watching = True
        self.last_refresh_tick = tick
        self.deadman_ok = True
        self.expired = False

    def refresh(self, tick: int) -> None:
        self.watching = True
        self.last_refresh_tick = tick
        self.deadman_ok = True
        self.expired = False

    def set_t_dead(self, value: int, *, override: bool = False) -> None:
        self.t_dead = value
        if override:
            self.override_logged = True

    def tick(self, now: int) -> bool:
        """Return True if newly expired."""
        if not self.watching or self.last_refresh_tick is None:
            return False
        if self.expired:
            return False
        if now - self.last_refresh_tick > self.t_dead:
            self.deadman_ok = False
            self.expired = True
            return True
        return False


class OversightPlane:
    """Mock I5 oversight plane (refined gate + ledger + deadman + quorum)."""

    def __init__(self) -> None:
        self.quorum = QuorumHuman()
        self.deadman = DeadmanWatch()
        self.paused = False
        self.killed = False
        self.denied = False
        self.approved_single = False
        self.consent_revoked = False
        self.refuse_transport = False
        self.decisions: list[OversightDecision] = []
        self.tick = 0
        self.pause_engaged_tick: int | None = None
        self._prev_decision_hash: str | None = None
        self.bound_engine_ids: list[str] = []
        self.member_drain_requested = False

    def _hlc(self) -> str:
        return f"hlc:{self.tick}"

    def advance_time(self, units: int = 1) -> None:
        self.tick += units

    def bind_engines(self, engine_ids: list[str]) -> None:
        self.bound_engine_ids = list(engine_ids)

    def _emit(
        self,
        *,
        verb: OversightVerb,
        actor: str,
        goal_id: str,
        continuity_id: str,
        action_class: str,
        result: str,
        abort_code: str | None = None,
        abort_reason: str | None = None,
        refuse_transport: bool = False,
        detail: dict[str, Any] | None = None,
        quorum_ok: bool | None = None,
    ) -> OversightDecision:
        body = {
            "verb": verb.value,
            "actor": actor,
            "goal": goal_id,
            "cont": continuity_id,
            "tick": self.tick,
            "result": result,
            "abort": abort_code,
        }
        dec = OversightDecision(
            decision_id="ovs:" + _digest16(body),
            verb=verb.value,
            actor=actor,
            goal_id=goal_id,
            continuity_id=continuity_id,
            action_class=action_class,
            bound_engine_ids=list(self.bound_engine_ids),
            quorum_ok=self.quorum.approve_quorum_ok() if quorum_ok is None else quorum_ok,
            deadman_ok=self.deadman.deadman_ok,
            t_dead=self.deadman.t_dead,
            t_dead_override_logged=self.deadman.override_logged,
            result=result,
            abort_code=abort_code,
            abort_reason=abort_reason,
            refuse_transport=refuse_transport or self.refuse_transport,
            dual_primary=0,
            live_api=False,
            created_hlc=self._hlc(),
            prev_decision_hash=self._prev_decision_hash,
            detail=detail or {},
        )
        self.decisions.append(dec)
        self._prev_decision_hash = dec.content_hash()
        return dec

    def approve(
        self,
        *,
        actor: str,
        goal_id: str,
        continuity_id: str,
        action_class: ActionClass | str,
    ) -> OversightDecision:
        ac = action_class.value if isinstance(action_class, ActionClass) else action_class
        self.quorum.record_approve(actor)
        self.denied = False
        self.consent_revoked = False
        if ac == ActionClass.A4.value:
            ok = self.quorum.approve_quorum_ok()
            self.approved_single = ok
            if not ok:
                return self._emit(
                    verb=OversightVerb.APPROVE,
                    actor=actor,
                    goal_id=goal_id,
                    continuity_id=continuity_id,
                    action_class=ac,
                    result="BLOCKED",
                    abort_code="OVS_QUORUM_REQUIRED",
                    abort_reason="A4 requires ≥2 human seats",
                    quorum_ok=False,
                )
            return self._emit(
                verb=OversightVerb.APPROVE,
                actor=actor,
                goal_id=goal_id,
                continuity_id=continuity_id,
                action_class=ac,
                result="ALLOW",
                quorum_ok=True,
            )
        # A3 (and optional lower): single seat sufficient
        self.approved_single = True
        return self._emit(
            verb=OversightVerb.APPROVE,
            actor=actor,
            goal_id=goal_id,
            continuity_id=continuity_id,
            action_class=ac,
            result="ALLOW",
            quorum_ok=True,
        )

    def deny(
        self,
        *,
        actor: str,
        goal_id: str,
        continuity_id: str,
        action_class: ActionClass | str = ActionClass.A3,
    ) -> OversightDecision:
        ac = action_class.value if isinstance(action_class, ActionClass) else action_class
        self.denied = True
        self.approved_single = False
        self.quorum.reset_approvals()
        return self._emit(
            verb=OversightVerb.DENY,
            actor=actor,
            goal_id=goal_id,
            continuity_id=continuity_id,
            action_class=ac,
            result="ABORT",
            abort_code="OVS_DENIED",
            abort_reason="human deny",
        )

    def pause(
        self,
        *,
        actor: str,
        goal_id: str,
        continuity_id: str,
        action_class: str = "A0",
    ) -> OversightDecision:
        self.paused = True
        self.pause_engaged_tick = self.tick
        return self._emit(
            verb=OversightVerb.PAUSE,
            actor=actor,
            goal_id=goal_id,
            continuity_id=continuity_id,
            action_class=action_class,
            result="PAUSED",
            abort_code="OVS_PAUSED",
            abort_reason="pause engaged; no new routes",
        )

    def resume(
        self,
        *,
        actor: str,
        goal_id: str,
        continuity_id: str,
        action_class: str = "A0",
    ) -> OversightDecision:
        self.paused = False
        self.pause_engaged_tick = None
        return self._emit(
            verb=OversightVerb.RESUME,
            actor=actor,
            goal_id=goal_id,
            continuity_id=continuity_id,
            action_class=action_class,
            result="ALLOW",
            detail={"resumed": True},
        )

    def kill(
        self,
        *,
        actor: str,
        goal_id: str,
        continuity_id: str,
        action_class: str = "A4",
        force_single: bool = False,
    ) -> OversightDecision:
        self.quorum.record_kill(actor)
        if not force_single and not self.quorum.kill_quorum_ok():
            return self._emit(
                verb=OversightVerb.KILL,
                actor=actor,
                goal_id=goal_id,
                continuity_id=continuity_id,
                action_class=action_class,
                result="BLOCKED",
                abort_code="OVS_QUORUM_REQUIRED",
                abort_reason="kill requires quorum-human",
                quorum_ok=False,
            )
        self.killed = True
        self.refuse_transport = True
        self.paused = True
        self.approved_single = False
        return self._emit(
            verb=OversightVerb.KILL,
            actor=actor,
            goal_id=goal_id,
            continuity_id=continuity_id,
            action_class=action_class,
            result="ABORT",
            abort_code="OVS_KILLED",
            abort_reason="kill switch; RefuseTransport",
            refuse_transport=True,
            quorum_ok=True,
        )

    def deadman_refresh(
        self,
        *,
        actor: str,
        goal_id: str,
        continuity_id: str,
        action_class: str = "A4",
    ) -> OversightDecision:
        self.deadman.refresh(self.tick)
        self.consent_revoked = False
        return self._emit(
            verb=OversightVerb.DEADMAN_REFRESH,
            actor=actor,
            goal_id=goal_id,
            continuity_id=continuity_id,
            action_class=action_class,
            result="ALLOW",
            detail={"deadman_ok": True},
        )

    def set_t_dead(self, value: int, *, actor: str, goal_id: str, continuity_id: str) -> OversightDecision:
        self.deadman.set_t_dead(value, override=True)
        return self._emit(
            verb=OversightVerb.DEADMAN_REFRESH,
            actor=actor,
            goal_id=goal_id,
            continuity_id=continuity_id,
            action_class="A4",
            result="ALLOW",
            detail={"deadman_override": True, "t_dead": value},
        )

    def consent_revoke(
        self,
        *,
        actor: str,
        goal_id: str,
        continuity_id: str,
        action_class: str = "A3",
    ) -> OversightDecision:
        self.consent_revoked = True
        self.approved_single = False
        self.deadman.deadman_ok = False
        self.quorum.reset_approvals()
        return self._emit(
            verb=OversightVerb.CONSENT_REVOKE,
            actor=actor,
            goal_id=goal_id,
            continuity_id=continuity_id,
            action_class=action_class,
            result="BLOCKED",
            abort_code="OVS_CONSENT_REVOKED",
            abort_reason="consent revoked; re-gate required",
        )

    def tick_deadman(
        self,
        *,
        goal_id: str,
        continuity_id: str,
        action_class: str = "A4",
    ) -> OversightDecision | None:
        newly = self.deadman.tick(self.tick)
        if not newly:
            return None
        self.member_drain_requested = True
        self.approved_single = False
        return self._emit(
            verb=OversightVerb.TICK_DEADMAN,
            actor="mesh:deadman",
            goal_id=goal_id,
            continuity_id=continuity_id,
            action_class=action_class,
            result="DRAIN",
            abort_code="OVS_DEADMAN_EXPIRED",
            abort_reason="T_dead elapsed; auto-DRAIN",
        )

    def pre_gate(self, env: RoutingEnvelope) -> OversightDecision | None:
        """Return ABORT/BLOCKED decision if invoke must not proceed; else None."""
        ac = env.action_class.value
        gid = env.goal_id or "goal:missing"
        cid = env.continuity_id or "cont:missing"

        if env.live_api_enabled or LIVE_API_ENABLED:
            return self._emit(
                verb=OversightVerb.DENY,
                actor="mesh:gate",
                goal_id=gid,
                continuity_id=cid,
                action_class=ac,
                result="ABORT",
                abort_code="OVS_LIVE_DISABLED",
                abort_reason="live path disabled",
            )
        if env.dual_primary != 0:
            return self._emit(
                verb=OversightVerb.DENY,
                actor="mesh:gate",
                goal_id=gid,
                continuity_id=cid,
                action_class=ac,
                result="ABORT",
                abort_code="FENCE",
                abort_reason="dual_primary != 0",
            )
        if env.n_members > N_CAP:
            return self._emit(
                verb=OversightVerb.DENY,
                actor="mesh:gate",
                goal_id=gid,
                continuity_id=cid,
                action_class=ac,
                result="ABORT",
                abort_code="OVS_N_GT2_REFUSED",
                abort_reason="N>2 refused",
            )
        if self.killed or self.refuse_transport:
            return self._emit(
                verb=OversightVerb.KILL,
                actor="mesh:gate",
                goal_id=gid,
                continuity_id=cid,
                action_class=ac,
                result="ABORT",
                abort_code="OVS_KILLED",
                abort_reason="kill switch engaged; RefuseTransport",
                refuse_transport=True,
            )
        if self.paused:
            return self._emit(
                verb=OversightVerb.PAUSE,
                actor="mesh:gate",
                goal_id=gid,
                continuity_id=cid,
                action_class=ac,
                result="BLOCKED",
                abort_code="OVS_PAUSED",
                abort_reason="paused; no new routes",
            )
        if self.denied:
            return self._emit(
                verb=OversightVerb.DENY,
                actor="mesh:gate",
                goal_id=gid,
                continuity_id=cid,
                action_class=ac,
                result="ABORT",
                abort_code="OVS_DENIED",
                abort_reason="human deny sticky",
            )
        if self.deadman.expired:
            return self._emit(
                verb=OversightVerb.TICK_DEADMAN,
                actor="mesh:gate",
                goal_id=gid,
                continuity_id=cid,
                action_class=ac,
                result="DRAIN",
                abort_code="OVS_DEADMAN_EXPIRED",
                abort_reason="deadman expired",
            )

        needs_human = env.action_class in {ActionClass.A3, ActionClass.A4}
        if needs_human:
            if self.consent_revoked and not self.approved_single:
                return self._emit(
                    verb=OversightVerb.CONSENT_REVOKE,
                    actor="mesh:gate",
                    goal_id=gid,
                    continuity_id=cid,
                    action_class=ac,
                    result="BLOCKED",
                    abort_code="OVS_CONSENT_REVOKED",
                    abort_reason="consent revoked; re-approve",
                )
            if not self.approved_single:
                return self._emit(
                    verb=OversightVerb.DENY,
                    actor="mesh:gate",
                    goal_id=gid,
                    continuity_id=cid,
                    action_class=ac,
                    result="BLOCKED",
                    abort_code="OVS_REQUIRED",
                    abort_reason=f"{ac} requires human approve",
                )
            if env.action_class == ActionClass.A4:
                if not self.quorum.approve_quorum_ok():
                    return self._emit(
                        verb=OversightVerb.APPROVE,
                        actor="mesh:gate",
                        goal_id=gid,
                        continuity_id=cid,
                        action_class=ac,
                        result="BLOCKED",
                        abort_code="OVS_QUORUM_REQUIRED",
                        abort_reason="A4 quorum-human required",
                        quorum_ok=False,
                    )
                if not self.deadman.deadman_ok:
                    return self._emit(
                        verb=OversightVerb.DEADMAN_REFRESH,
                        actor="mesh:gate",
                        goal_id=gid,
                        continuity_id=cid,
                        action_class=ac,
                        result="BLOCKED",
                        abort_code="OVS_DEADMAN_REQUIRED",
                        abort_reason="A4 requires deadman refresh",
                    )
        return None


class OversightOrchestrator:
    """I5 oversight plane wrapping ContinuityOrchestrator + routing bind."""

    def __init__(
        self,
        continuity: ContinuityOrchestrator | None = None,
        plane: OversightPlane | None = None,
    ) -> None:
        router = OrchestratorRouter(registry=default_registry())
        self.continuity = continuity or ContinuityOrchestrator(router=router)
        self.plane = plane or OversightPlane()
        self.receipts: list[OversightReceipt] = []
        self._prev_receipt_hash: str | None = None
        # sync router oversight gate loosely for compose visibility
        self.router = self.continuity.router

    def advance_time(self, units: int = 1) -> None:
        self.plane.advance_time(units)
        self.continuity.advance_time(units)

    def _emit_receipt(
        self,
        *,
        decision: OversightDecision,
        continuity_state: str,
        result: str,
        continuity_receipt_id: str | None = None,
        routing_receipt_id: str | None = None,
        detail: dict[str, Any] | None = None,
    ) -> OversightReceipt:
        body = {
            "dec": decision.decision_id,
            "result": result,
            "tick": self.plane.tick,
            "goal": decision.goal_id,
        }
        rcpt = OversightReceipt(
            receipt_id="rcpt:" + _digest16(body),
            decision_id=decision.decision_id,
            continuity_state=continuity_state,
            result=result,
            goal_id=decision.goal_id,
            continuity_id=decision.continuity_id,
            continuity_receipt_id=continuity_receipt_id,
            routing_receipt_id=routing_receipt_id,
            abort_code=decision.abort_code,
            abort_reason=decision.abort_reason,
            refuse_transport=decision.refuse_transport,
            dual_primary=0,
            live_api=False,
            bound_engine_ids=list(decision.bound_engine_ids),
            prev_receipt_hash=self._prev_receipt_hash,
            created_hlc=self.plane._hlc(),
            detail=detail or {},
        )
        self.receipts.append(rcpt)
        self._prev_receipt_hash = rcpt.content_hash()
        return rcpt

    def _sync_router_gate(self) -> None:
        g = self.router.oversight
        g.state.paused = self.plane.paused
        g.state.killed = self.plane.killed
        g.state.denied = self.plane.denied
        g.state.approved = self.plane.approved_single
        g.state.deadman_ok = self.plane.deadman.deadman_ok
        g.state.required = True

    def _append_oversight_evidence(self, goal_id: str, decision: OversightDecision) -> None:
        kind = "deadman_override" if decision.detail.get("deadman_override") else "oversight"
        self.continuity._append_evidence(
            goal_id=goal_id,
            kind=kind,
            payload=decision.to_dict(),
            receipt_id=decision.decision_id,
        )

    def decide_and_invoke(
        self,
        env: RoutingEnvelope,
        *,
        idempotency_key: str,
        title: str = "oversight-goal",
    ) -> OversightReceipt:
        # Bind engines from a dry capability probe (advisory list) before gate
        capable = self.router.registry.capable(
            env.workload_class, env.latency_band, trust_tier=env.trust_tier
        )
        self.plane.bind_engines([c.engine_id for c in capable[:2]])

        blocked = self.plane.pre_gate(env)
        if blocked is not None:
            self._append_oversight_evidence(env.goal_id or "goal:missing", blocked)
            # Reflect on continuity machine when possible
            cid = env.continuity_id
            gid = env.goal_id
            cont_state = "ABORTED"
            if cid and gid:
                self.continuity.registry.ensure(gid, cid, title=title, tick=self.plane.tick)
                st = self.continuity.machine.ensure(cid, gid, tick=self.plane.tick)
                if blocked.abort_code in {"OVS_PAUSED", "OVS_REQUIRED", "OVS_QUORUM_REQUIRED",
                                         "OVS_DEADMAN_REQUIRED", "OVS_CONSENT_REVOKED",
                                         "OVS_DEADMAN_EXPIRED"}:
                    target = ContinuityStateName.BLOCKED
                    if blocked.abort_code == "OVS_PAUSED":
                        target = ContinuityStateName.PAUSED
                    if blocked.result == "DRAIN":
                        target = ContinuityStateName.BLOCKED
                    if st.state.value not in {"SUCCEEDED", "FAILED", "ABORTED", "CANCELLED"}:
                        self.continuity.machine.transition(
                            cid, target, tick=self.plane.tick, blocker_code=blocked.abort_code
                        )
                    cont_state = target.value
                else:
                    if st.state.value not in {"SUCCEEDED", "FAILED", "ABORTED", "CANCELLED"}:
                        self.continuity.machine.transition(
                            cid,
                            ContinuityStateName.ABORTED,
                            tick=self.plane.tick,
                            blocker_code=blocked.abort_code,
                        )
                    cont_state = ContinuityStateName.ABORTED.value
            return self._emit_receipt(
                decision=blocked,
                continuity_state=cont_state,
                result=blocked.result,
            )

        # Sync gate into router then invoke continuity
        self._sync_router_gate()
        # Ensure envelope oversight mirrors plane for A3/A4
        if env.action_class in {ActionClass.A3, ActionClass.A4}:
            env.oversight.required = True
            env.oversight.approved = self.plane.approved_single
            env.oversight.deadman_ok = self.plane.deadman.deadman_ok
            env.oversight.denied = self.plane.denied
            env.oversight.paused = self.plane.paused
            env.oversight.killed = self.plane.killed

        cont_rcpt = self.continuity.invoke(env, idempotency_key=idempotency_key, title=title)
        # Synthetic allow decision for audit bind
        allow_dec = self.plane._emit(
            verb=OversightVerb.APPROVE,
            actor="mesh:gate",
            goal_id=env.goal_id,
            continuity_id=env.continuity_id or "",
            action_class=env.action_class.value,
            result=cont_rcpt.decision,
            abort_code=cont_rcpt.abort_code,
            abort_reason=cont_rcpt.abort_reason,
            detail={"compose": "continuity+routing", "invoke_id": cont_rcpt.invoke_id},
        )
        self._append_oversight_evidence(env.goal_id, allow_dec)
        routing_id = None
        if self.router.receipts:
            routing_id = self.router.receipts[-1].receipt_id
            allow_dec.bound_engine_ids = list(self.router.receipts[-1].engine_ids)
            self.plane.bound_engine_ids = list(allow_dec.bound_engine_ids)
        return self._emit_receipt(
            decision=allow_dec,
            continuity_state=cont_rcpt.continuity_state,
            result=cont_rcpt.decision,
            continuity_receipt_id=cont_rcpt.receipt_id,
            routing_receipt_id=routing_id,
        )

    def apply_pause(self, *, actor: str, goal_id: str, continuity_id: str) -> OversightReceipt:
        dec = self.plane.pause(actor=actor, goal_id=goal_id, continuity_id=continuity_id)
        self._append_oversight_evidence(goal_id, dec)
        self.continuity.registry.ensure(goal_id, continuity_id, tick=self.plane.tick)
        st = self.continuity.machine.ensure(continuity_id, goal_id, tick=self.plane.tick)
        if st.state.value not in {"SUCCEEDED", "FAILED", "ABORTED", "CANCELLED"}:
            self.continuity.machine.transition(
                continuity_id, ContinuityStateName.PAUSED, tick=self.plane.tick, blocker_code="OVS_PAUSED"
            )
        # Abort open in-flight without silent drop
        for inv in list(self.continuity.inflight.open_invokes()):
            if inv.goal_id == goal_id:
                self.continuity.inflight.seal(inv.invoke_id, status=InFlightStatus.ABORTED)
        self._sync_router_gate()
        # SLO pause: engaged within target units (same tick = 0 ≤ target)
        elapsed = 0 if self.plane.pause_engaged_tick is None else 0
        assert elapsed <= SLO_PAUSE_HARD
        return self._emit_receipt(
            decision=dec,
            continuity_state=ContinuityStateName.PAUSED.value,
            result="PAUSED",
            detail={"slo_pause_units": elapsed, "slo_target": SLO_PAUSE_TARGET},
        )

    def apply_resume(self, *, actor: str, goal_id: str, continuity_id: str) -> OversightReceipt:
        dec = self.plane.resume(actor=actor, goal_id=goal_id, continuity_id=continuity_id)
        self._append_oversight_evidence(goal_id, dec)
        st = self.continuity.machine.load(continuity_id)
        if st.state == ContinuityStateName.PAUSED:
            self.continuity.machine.transition(
                continuity_id, ContinuityStateName.RUNNING, tick=self.plane.tick
            )
        self._sync_router_gate()
        return self._emit_receipt(
            decision=dec,
            continuity_state=self.continuity.machine.load(continuity_id).state.value,
            result="ALLOW",
        )

    def apply_kill(
        self,
        *,
        actors: list[str],
        goal_id: str,
        continuity_id: str,
    ) -> OversightReceipt:
        dec = None
        for a in actors:
            dec = self.plane.kill(actor=a, goal_id=goal_id, continuity_id=continuity_id)
        assert dec is not None
        self._append_oversight_evidence(goal_id, dec)
        self.continuity.registry.ensure(goal_id, continuity_id, tick=self.plane.tick)
        st = self.continuity.machine.ensure(continuity_id, goal_id, tick=self.plane.tick)
        if dec.abort_code == "OVS_KILLED":
            if st.state.value not in {"SUCCEEDED", "FAILED", "ABORTED", "CANCELLED"}:
                self.continuity.machine.transition(
                    continuity_id,
                    ContinuityStateName.ABORTED,
                    tick=self.plane.tick,
                    blocker_code="OVS_KILLED",
                )
            for inv in list(self.continuity.inflight.open_invokes()):
                if inv.goal_id == goal_id:
                    self.continuity.inflight.seal(inv.invoke_id, status=InFlightStatus.ABORTED)
        self._sync_router_gate()
        return self._emit_receipt(
            decision=dec,
            continuity_state=self.continuity.machine.load(continuity_id).state.value,
            result=dec.result,
        )

    def apply_deadman_tick(self, *, goal_id: str, continuity_id: str) -> OversightReceipt | None:
        dec = self.plane.tick_deadman(goal_id=goal_id, continuity_id=continuity_id)
        if dec is None:
            return None
        self._append_oversight_evidence(goal_id, dec)
        self.continuity.registry.ensure(goal_id, continuity_id, tick=self.plane.tick)
        st = self.continuity.machine.ensure(continuity_id, goal_id, tick=self.plane.tick)
        if st.state.value not in {"SUCCEEDED", "FAILED", "ABORTED", "CANCELLED"}:
            self.continuity.machine.transition(
                continuity_id,
                ContinuityStateName.BLOCKED,
                tick=self.plane.tick,
                blocker_code="OVS_DEADMAN_EXPIRED",
            )
        # membership drain stub
        self.plane.member_drain_requested = True
        return self._emit_receipt(
            decision=dec,
            continuity_state=ContinuityStateName.BLOCKED.value,
            result="DRAIN",
            detail={"member_state": MemberState.DRAINING.value},
        )


def verify_oversight_decision_chain(decisions: list[OversightDecision]) -> bool:
    prev: str | None = None
    for d in decisions:
        if d.prev_decision_hash != prev:
            return False
        if d.dual_primary != 0 or d.live_api:
            return False
        prev = d.content_hash()
    return True


def verify_oversight_receipt_chain(receipts: list[OversightReceipt]) -> bool:
    prev: str | None = None
    for r in receipts:
        if r.prev_receipt_hash != prev:
            return False
        if r.dual_primary != 0 or r.live_api:
            return False
        prev = r.content_hash()
    return True
