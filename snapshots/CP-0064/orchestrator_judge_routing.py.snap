"""Orchestrator judge/shell routing design helpers (CP-0064 / Cycle 60).

Design-only mock: select L_judge MIX vs agent_shell under policy, M2 member
state, M3 latency band, judge capability registry, A3/A4 oversight, dual
advisory (≠ M1 consensus), fallback chain, ABORT-on-mismatch, durable goal
continuity hooks.

Mock-only: live=DISABLED, no train, no keys, no src codec, no N>2, no Raft.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from neural_mesh.packaging.m2_membership_rejoin import (
    ACTIVE_TIERS,
    MemberState,
    TrustTierName,
)
from neural_mesh.packaging.m3_wan_model import LatencyBand

__all__ = [
    "PACKAGE_HELD",
    "CYCLE",
    "SEAL_CP",
    "PRIOR_CP",
    "PREFERRED_NEXT_DEFAULT",
    "LIVE_API_ENABLED",
    "SCHEMA_ENVELOPE",
    "SCHEMA_RECEIPT",
    "SCHEMA_CAPABILITY",
    "N_CAP",
    "WorkloadClass",
    "ActionClass",
    "RoutingPolicy",
    "RoutingTarget",
    "ABORT_CODES",
    "BAND_ORDER",
    "RouteError",
    "JudgeCapability",
    "OversightState",
    "RoutingEnvelope",
    "RoutingReceipt",
    "RoutingDecision",
    "JudgeCapabilitiesRegistry",
    "OversightGate",
    "OrchestratorRouter",
    "sample_envelope",
    "default_registry",
    "verify_receipt_chain",
]

PACKAGE_HELD = "0.18.0"
CYCLE = 60
SEAL_CP = "CP-0064"
PRIOR_CP = "CP-0063"
PREFERRED_NEXT_DEFAULT = "await_deepseek"
LIVE_API_ENABLED = False  # must stay False (live=DISABLED)
SCHEMA_ENVELOPE = "mesh.orchestrator.routing_envelope/v0"
SCHEMA_RECEIPT = "mesh.orchestrator.routing_receipt/v0"
SCHEMA_CAPABILITY = "mesh.judge.capability/v0"
N_CAP = 2


class WorkloadClass(str, Enum):
    JUDGE_ADVISORY = "JUDGE_ADVISORY"
    JUDGE_CRITIQUE = "JUDGE_CRITIQUE"
    SHELL_BOUNDED = "SHELL_BOUNDED"
    SHELL_MULTI_TURN = "SHELL_MULTI_TURN"
    SAFETY_PROBE = "SAFETY_PROBE"
    CONTINUITY_RESUME = "CONTINUITY_RESUME"


class ActionClass(str, Enum):
    A0 = "A0"
    A1 = "A1"
    A2 = "A2"
    A3 = "A3"
    A4 = "A4"


class RoutingPolicy(str, Enum):
    SINGLE_JUDGE = "SINGLE_JUDGE"
    DUAL_JUDGE_ADVISORY = "DUAL_JUDGE_ADVISORY"
    FALLBACK_CHAIN = "FALLBACK_CHAIN"
    MESH_LOCAL = "MESH_LOCAL"


class RoutingTarget(str, Enum):
    L_JUDGE = "L_JUDGE"
    AGENT_SHELL = "AGENT_SHELL"
    MESH_LOCAL = "MESH_LOCAL"
    NONE = "NONE"


BAND_ORDER: tuple[LatencyBand, ...] = (
    LatencyBand.RTT_lo,
    LatencyBand.RTT_mid,
    LatencyBand.RTT_hi,
    LatencyBand.RTT_x,
)

ABORT_CODES: tuple[str, ...] = (
    "ROUTE_LIVE_DISABLED",
    "ROUTE_MEMBER_NOT_ACTIVE",
    "ROUTE_MEMBER_DRAINING",
    "ROUTE_OVERSIGHT_REQUIRED",
    "ROUTE_OVERSIGHT_DENIED",
    "ROUTE_DEADMAN_REQUIRED",
    "ROUTE_NO_CAPABLE_ENGINE",
    "ROUTE_DUAL_UNDERPROVISIONED",
    "ROUTE_JUDGE_MISMATCH",
    "ROUTE_FALLBACK_EXHAUSTED",
    "ROUTE_N_GT2_REFUSED",
    "ROUTE_POLICY_UNKNOWN",
    "ROUTE_SCHEMA_INVALID",
    "FENCE",
)


class RouteError(RuntimeError):
    """Fail-closed orchestrator routing error."""

    code: str = "ROUTE_ERROR"

    def __init__(self, message: str, *, code: str | None = None):
        super().__init__(message)
        if code:
            self.code = code


def _band_rank(band: LatencyBand | str) -> int:
    b = LatencyBand(band) if not isinstance(band, LatencyBand) else band
    return BAND_ORDER.index(b)


def _digest16(payload: dict[str, Any]) -> str:
    blob = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(blob).hexdigest()[:16]


def _sha256(text: str) -> str:
    return "sha256:" + hashlib.sha256(text.encode()).hexdigest()


@dataclass
class JudgeCapability:
    engine_id: str
    provider: str = "mock"
    model_hint: str = "mock-judge"
    supports: tuple[str, ...] = (WorkloadClass.JUDGE_ADVISORY.value,)
    max_latency_band: LatencyBand = LatencyBand.RTT_mid
    trust_floor: TrustTierName = TrustTierName.T2
    live: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": SCHEMA_CAPABILITY,
            "engine_id": self.engine_id,
            "provider": self.provider,
            "model_hint": self.model_hint,
            "supports": list(self.supports),
            "max_latency_band": self.max_latency_band.value,
            "trust_floor": self.trust_floor.value,
            "live": False,
        }

    def supports_class(self, wc: WorkloadClass) -> bool:
        return wc.value in self.supports

    def tolerates_band(self, band: LatencyBand) -> bool:
        return _band_rank(band) <= _band_rank(self.max_latency_band)


@dataclass
class OversightState:
    required: bool = False
    approved: bool | None = None
    denied: bool = False
    deadman_ok: bool | None = None
    paused: bool = False
    killed: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "required": self.required,
            "approved": self.approved,
            "denied": self.denied,
            "deadman_ok": self.deadman_ok,
            "paused": self.paused,
            "killed": self.killed,
        }


@dataclass
class RoutingEnvelope:
    request_id: str = "req:0001"
    goal_id: str = "goal:deadbeefdeadbeef"
    continuity_id: str | None = "cont:cafebabecafebabe"
    workload_class: WorkloadClass = WorkloadClass.JUDGE_ADVISORY
    action_class: ActionClass = ActionClass.A1
    member_state: MemberState = MemberState.ACTIVE
    trust_tier: TrustTierName = TrustTierName.T2
    latency_band: LatencyBand = LatencyBand.RTT_mid
    prefer_dual: bool = False
    oversight: OversightState = field(default_factory=OversightState)
    dual_primary: int = 0
    n_members: int = N_CAP
    live_api_enabled: bool = False
    prompt_body: str = "advisory-prompt"
    # For dual advisory mismatch tests / resume
    prior_policy: RoutingPolicy | None = None
    prior_target: RoutingTarget | None = None
    prior_engine_ids: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": SCHEMA_ENVELOPE,
            "request_id": self.request_id,
            "goal_id": self.goal_id,
            "continuity_id": self.continuity_id,
            "workload_class": self.workload_class.value,
            "action_class": self.action_class.value,
            "member_state": self.member_state.value,
            "trust_tier": self.trust_tier.value,
            "latency_band": self.latency_band.value,
            "prefer_dual": self.prefer_dual,
            "oversight": self.oversight.to_dict(),
            "dual_primary": self.dual_primary,
            "n_members": self.n_members,
            "live_api_enabled": self.live_api_enabled,
        }


@dataclass
class RoutingReceipt:
    receipt_id: str
    decision: str
    policy: str
    target: str
    workload_class: str
    action_class: str
    engine_ids: list[str]
    reason: str
    prompt_hash: str | None
    response_hash: str | None
    goal_id: str
    continuity_id: str | None
    member_state: str
    latency_band: str
    oversight: dict[str, Any]
    abort_code: str | None = None
    abort_reason: str | None = None
    dual_primary: int = 0
    live_api: bool = False
    advisory_only: bool = True
    prev_receipt_hash: str | None = None
    evidence_kind: str = "routing_receipt"
    continuity_state: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": SCHEMA_RECEIPT,
            "receipt_id": self.receipt_id,
            "decision": self.decision,
            "policy": self.policy,
            "target": self.target,
            "workload_class": self.workload_class,
            "action_class": self.action_class,
            "engine_ids": list(self.engine_ids),
            "reason": self.reason,
            "prompt_hash": self.prompt_hash,
            "response_hash": self.response_hash,
            "goal_id": self.goal_id,
            "continuity_id": self.continuity_id,
            "member_state": self.member_state,
            "latency_band": self.latency_band,
            "oversight": dict(self.oversight),
            "abort": {"code": self.abort_code, "reason": self.abort_reason},
            "dual_primary": 0,
            "live_api": False,
            "advisory_only": self.advisory_only,
            "prev_receipt_hash": self.prev_receipt_hash,
            "evidence_kind": self.evidence_kind,
            "continuity_state": self.continuity_state,
        }

    def content_hash(self) -> str:
        d = self.to_dict()
        d.pop("prev_receipt_hash", None)
        return "sha256:" + hashlib.sha256(
            json.dumps(d, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()


@dataclass
class RoutingDecision:
    allow: bool
    policy: RoutingPolicy
    target: RoutingTarget
    engine_ids: list[str]
    reason: str
    abort_code: str | None = None
    abort_on_mismatch: bool = False
    receipt: RoutingReceipt | None = None


@dataclass
class JudgeCapabilitiesRegistry:
    engines: list[JudgeCapability] = field(default_factory=list)

    def register(self, cap: JudgeCapability) -> None:
        if cap.live:
            raise RouteError(
                "live engines forbidden while live=DISABLED",
                code="ROUTE_LIVE_DISABLED",
            )
        self.engines.append(cap)

    def capable(
        self,
        workload_class: WorkloadClass,
        band: LatencyBand,
        *,
        trust_tier: TrustTierName,
    ) -> list[JudgeCapability]:
        out: list[JudgeCapability] = []
        for e in self.engines:
            if e.live:
                continue
            if not e.supports_class(workload_class):
                continue
            if not e.tolerates_band(band):
                continue
            floor = e.trust_floor
            # trust_tier must meet or exceed floor (T3 > T2 > T1 > T0)
            order = [TrustTierName.T0, TrustTierName.T1, TrustTierName.T2, TrustTierName.T3]
            if order.index(trust_tier) < order.index(floor):
                continue
            out.append(e)
        return out


@dataclass
class OversightGate:
    """Mock I5 approve/deny/pause/kill/deadman."""

    state: OversightState = field(default_factory=OversightState)

    def approve(self) -> None:
        self.state.approved = True
        self.state.denied = False

    def deny(self) -> None:
        self.state.denied = True
        self.state.approved = False

    def pause(self) -> None:
        self.state.paused = True

    def kill(self) -> None:
        self.state.killed = True

    def refresh_deadman(self) -> None:
        self.state.deadman_ok = True

    def consent_revoke(self) -> None:
        self.state.approved = False
        self.state.deadman_ok = False


def default_registry() -> JudgeCapabilitiesRegistry:
    reg = JudgeCapabilitiesRegistry()
    reg.register(
        JudgeCapability(
            engine_id="judge:mock-a",
            model_hint="mock-judge-a",
            supports=(
                WorkloadClass.JUDGE_ADVISORY.value,
                WorkloadClass.JUDGE_CRITIQUE.value,
                WorkloadClass.CONTINUITY_RESUME.value,
            ),
            max_latency_band=LatencyBand.RTT_hi,
        )
    )
    reg.register(
        JudgeCapability(
            engine_id="judge:mock-b",
            model_hint="mock-judge-b",
            supports=(
                WorkloadClass.JUDGE_ADVISORY.value,
                WorkloadClass.JUDGE_CRITIQUE.value,
                WorkloadClass.CONTINUITY_RESUME.value,
            ),
            max_latency_band=LatencyBand.RTT_mid,
        )
    )
    reg.register(
        JudgeCapability(
            engine_id="judge:mock-lo",
            model_hint="mock-judge-lo",
            supports=(WorkloadClass.JUDGE_ADVISORY.value,),
            max_latency_band=LatencyBand.RTT_lo,
        )
    )
    return reg


def sample_envelope(**kwargs: Any) -> RoutingEnvelope:
    env = RoutingEnvelope()
    for k, v in kwargs.items():
        if not hasattr(env, k):
            raise RouteError(f"unknown envelope field: {k}", code="ROUTE_SCHEMA_INVALID")
        setattr(env, k, v)
    return env


@dataclass
class OrchestratorRouter:
    """In-memory mock orchestrator. Not a live multi-engine service."""

    registry: JudgeCapabilitiesRegistry = field(default_factory=default_registry)
    oversight: OversightGate = field(default_factory=OversightGate)
    receipts: list[RoutingReceipt] = field(default_factory=list)
    # Simulated dual responses for mismatch tests: engine_id -> verdict digest
    dual_response_digests: dict[str, str] = field(default_factory=dict)

    def _prev_hash(self) -> str | None:
        if not self.receipts:
            return None
        return self.receipts[-1].content_hash()

    def _emit(
        self,
        *,
        decision: str,
        policy: RoutingPolicy,
        target: RoutingTarget,
        env: RoutingEnvelope,
        engine_ids: list[str],
        reason: str,
        abort_code: str | None = None,
        abort_reason: str | None = None,
        prompt_hash: str | None = None,
        response_hash: str | None = None,
        continuity_state: str | None = None,
        advisory_only: bool = True,
    ) -> RoutingReceipt:
        body = {
            "decision": decision,
            "policy": policy.value,
            "target": target.value,
            "engines": engine_ids,
            "goal": env.goal_id,
            "req": env.request_id,
        }
        rid = "rcpt:" + _digest16(body)
        ov = env.oversight.to_dict()
        # Merge gate state for audit
        ov.update(self.oversight.state.to_dict())
        rcpt = RoutingReceipt(
            receipt_id=rid,
            decision=decision,
            policy=policy.value,
            target=target.value,
            workload_class=env.workload_class.value,
            action_class=env.action_class.value,
            engine_ids=list(engine_ids),
            reason=reason,
            prompt_hash=prompt_hash,
            response_hash=response_hash,
            goal_id=env.goal_id,
            continuity_id=env.continuity_id,
            member_state=env.member_state.value,
            latency_band=env.latency_band.value,
            oversight=ov,
            abort_code=abort_code,
            abort_reason=abort_reason,
            dual_primary=0,
            live_api=False,
            advisory_only=advisory_only,
            prev_receipt_hash=self._prev_hash(),
            continuity_state=continuity_state,
        )
        self.receipts.append(rcpt)
        return rcpt

    def _abort(self, env: RoutingEnvelope, code: str, reason: str) -> RoutingDecision:
        cont = "ABORTED" if code in ("ROUTE_OVERSIGHT_DENIED",) or self.oversight.state.killed else "BLOCKED"
        if self.oversight.state.killed:
            cont = "ABORTED"
        rcpt = self._emit(
            decision="ABORT",
            policy=RoutingPolicy.MESH_LOCAL,
            target=RoutingTarget.NONE,
            env=env,
            engine_ids=[],
            reason=reason,
            abort_code=code,
            abort_reason=reason,
            continuity_state=cont,
        )
        return RoutingDecision(
            allow=False,
            policy=RoutingPolicy.MESH_LOCAL,
            target=RoutingTarget.NONE,
            engine_ids=[],
            reason=reason,
            abort_code=code,
            receipt=rcpt,
        )

    def select_policy(self, env: RoutingEnvelope) -> RoutingPolicy:
        wc = env.workload_class
        if wc in (WorkloadClass.SAFETY_PROBE,):
            return RoutingPolicy.MESH_LOCAL
        if wc in (WorkloadClass.SHELL_BOUNDED, WorkloadClass.SHELL_MULTI_TURN):
            return RoutingPolicy.SINGLE_JUDGE  # shell path; policy label SINGLE
        if wc == WorkloadClass.CONTINUITY_RESUME and env.prior_policy is not None:
            return env.prior_policy
        if wc == WorkloadClass.JUDGE_CRITIQUE or env.prefer_dual:
            if env.latency_band == LatencyBand.RTT_x:
                return RoutingPolicy.FALLBACK_CHAIN
            return RoutingPolicy.DUAL_JUDGE_ADVISORY
        if env.latency_band == LatencyBand.RTT_x:
            return RoutingPolicy.FALLBACK_CHAIN
        return RoutingPolicy.SINGLE_JUDGE

    def route(self, env: RoutingEnvelope) -> RoutingDecision:
        if LIVE_API_ENABLED or env.live_api_enabled:
            return self._abort(env, "ROUTE_LIVE_DISABLED", "live path forbidden")
        if env.dual_primary != 0:
            return self._abort(env, "FENCE", "dual_primary must be 0")
        if env.n_members > N_CAP:
            return self._abort(env, "ROUTE_N_GT2_REFUSED", "N>2 refused (NO_HELD)")
        if self.oversight.state.killed:
            return self._abort(env, "ROUTE_OVERSIGHT_DENIED", "kill switch engaged")
        if self.oversight.state.paused:
            return self._abort(env, "ROUTE_OVERSIGHT_REQUIRED", "paused; no new routes")
        if self.oversight.state.denied:
            return self._abort(env, "ROUTE_OVERSIGHT_DENIED", "human deny")

        # Membership gates
        if env.member_state == MemberState.DRAINING:
            return self._abort(env, "ROUTE_MEMBER_DRAINING", "member draining")
        if env.member_state != MemberState.ACTIVE or env.trust_tier not in ACTIVE_TIERS:
            return self._abort(
                env,
                "ROUTE_MEMBER_NOT_ACTIVE",
                f"member {env.member_state.value}/{env.trust_tier.value} not ACTIVE T2|T3",
            )

        # I5 oversight for A3/A4
        if env.action_class in (ActionClass.A3, ActionClass.A4):
            env.oversight.required = True
            approved = env.oversight.approved or self.oversight.state.approved
            if not approved:
                return self._abort(
                    env,
                    "ROUTE_OVERSIGHT_REQUIRED",
                    f"{env.action_class.value} requires human approve",
                )
            if env.action_class == ActionClass.A4:
                deadman = (
                    env.oversight.deadman_ok
                    if env.oversight.deadman_ok is not None
                    else self.oversight.state.deadman_ok
                )
                if not deadman:
                    return self._abort(
                        env,
                        "ROUTE_DEADMAN_REQUIRED",
                        "A4 requires deadman refresh",
                    )

        if env.workload_class == WorkloadClass.CONTINUITY_RESUME and not env.continuity_id:
            return self._abort(env, "ROUTE_SCHEMA_INVALID", "CONTINUITY_RESUME needs continuity_id")

        policy = self.select_policy(env)
        prompt_hash = _sha256(env.prompt_body)

        # Shell / local paths
        if env.workload_class in (
            WorkloadClass.SHELL_BOUNDED,
            WorkloadClass.SHELL_MULTI_TURN,
        ):
            rcpt = self._emit(
                decision="ALLOW",
                policy=RoutingPolicy.SINGLE_JUDGE,
                target=RoutingTarget.AGENT_SHELL,
                env=env,
                engine_ids=[],
                reason=f"shell path; member=ACTIVE; band={env.latency_band.value}",
                prompt_hash=prompt_hash,
                response_hash=None,
                continuity_state="RUNNING",
                advisory_only=True,
            )
            return RoutingDecision(
                allow=True,
                policy=RoutingPolicy.SINGLE_JUDGE,
                target=RoutingTarget.AGENT_SHELL,
                engine_ids=[],
                reason=rcpt.reason,
                receipt=rcpt,
            )

        if env.workload_class == WorkloadClass.SAFETY_PROBE or policy == RoutingPolicy.MESH_LOCAL:
            rcpt = self._emit(
                decision="ALLOW",
                policy=RoutingPolicy.MESH_LOCAL,
                target=RoutingTarget.MESH_LOCAL,
                env=env,
                engine_ids=[],
                reason="mesh-local safety probe",
                prompt_hash=prompt_hash,
                continuity_state="RUNNING",
            )
            return RoutingDecision(
                allow=True,
                policy=RoutingPolicy.MESH_LOCAL,
                target=RoutingTarget.MESH_LOCAL,
                engine_ids=[],
                reason=rcpt.reason,
                receipt=rcpt,
            )

        # Continuity resume: restore prior engines if still capable
        wc_for_cap = env.workload_class
        if env.workload_class == WorkloadClass.CONTINUITY_RESUME:
            wc_for_cap = WorkloadClass.JUDGE_ADVISORY

        engines = self.registry.capable(
            wc_for_cap if wc_for_cap != WorkloadClass.JUDGE_CRITIQUE else WorkloadClass.JUDGE_CRITIQUE,
            env.latency_band,
            trust_tier=env.trust_tier,
        )
        # For critique, capable() already filters JUDGE_CRITIQUE supporters

        if policy == RoutingPolicy.SINGLE_JUDGE:
            if env.workload_class == WorkloadClass.CONTINUITY_RESUME and env.prior_engine_ids:
                ids = [e for e in env.prior_engine_ids if any(x.engine_id == e for x in engines)]
                if not ids and engines:
                    ids = [engines[0].engine_id]
                if not ids:
                    return self._abort(env, "ROUTE_NO_CAPABLE_ENGINE", "resume: no capable engine")
                engine_ids = ids[:1]
            else:
                if not engines:
                    return self._abort(env, "ROUTE_NO_CAPABLE_ENGINE", "no capable engine")
                engine_ids = [engines[0].engine_id]
            resp = _sha256(f"resp:{engine_ids[0]}:{env.prompt_body}")
            rcpt = self._emit(
                decision="ALLOW",
                policy=policy,
                target=RoutingTarget.L_JUDGE,
                env=env,
                engine_ids=engine_ids,
                reason=f"SINGLE_JUDGE; capable+ACTIVE+{env.latency_band.value}",
                prompt_hash=prompt_hash,
                response_hash=resp,
                continuity_state="RUNNING",
            )
            return RoutingDecision(
                allow=True,
                policy=policy,
                target=RoutingTarget.L_JUDGE,
                engine_ids=engine_ids,
                reason=rcpt.reason,
                receipt=rcpt,
            )

        if policy == RoutingPolicy.DUAL_JUDGE_ADVISORY:
            if len(engines) < 2:
                return self._abort(
                    env,
                    "ROUTE_DUAL_UNDERPROVISIONED",
                    "dual advisory needs ≥2 capable engines",
                )
            engine_ids = [engines[0].engine_id, engines[1].engine_id]
            # Advisory digests — default agree; tests may inject mismatch
            d0 = self.dual_response_digests.get(
                engine_ids[0], _sha256(f"adv:{env.prompt_body}:agree")
            )
            d1 = self.dual_response_digests.get(
                engine_ids[1], _sha256(f"adv:{env.prompt_body}:agree")
            )
            if d0 != d1:
                return self._abort(
                    env,
                    "ROUTE_JUDGE_MISMATCH",
                    "dual advisory digest mismatch (fail closed)",
                )
            rcpt = self._emit(
                decision="ALLOW",
                policy=policy,
                target=RoutingTarget.L_JUDGE,
                env=env,
                engine_ids=engine_ids,
                reason="DUAL_JUDGE_ADVISORY; advisory_only≠M1_consensus",
                prompt_hash=prompt_hash,
                response_hash=d0,
                continuity_state="RUNNING",
                advisory_only=True,
            )
            return RoutingDecision(
                allow=True,
                policy=policy,
                target=RoutingTarget.L_JUDGE,
                engine_ids=engine_ids,
                reason=rcpt.reason,
                abort_on_mismatch=True,
                receipt=rcpt,
            )

        if policy == RoutingPolicy.FALLBACK_CHAIN:
            if not engines:
                # Try any advisory engine ignoring band as fallback exhaust check
                return self._abort(
                    env,
                    "ROUTE_FALLBACK_EXHAUSTED",
                    "fallback chain empty for band",
                )
            engine_ids = [e.engine_id for e in engines]
            chosen = engine_ids[0]
            resp = _sha256(f"fb:{chosen}:{env.prompt_body}")
            rcpt = self._emit(
                decision="ALLOW",
                policy=policy,
                target=RoutingTarget.L_JUDGE,
                env=env,
                engine_ids=[chosen],
                reason=f"FALLBACK_CHAIN; try_order={engine_ids}",
                prompt_hash=prompt_hash,
                response_hash=resp,
                continuity_state="RUNNING",
            )
            return RoutingDecision(
                allow=True,
                policy=policy,
                target=RoutingTarget.L_JUDGE,
                engine_ids=[chosen],
                reason=rcpt.reason,
                receipt=rcpt,
            )

        return self._abort(env, "ROUTE_POLICY_UNKNOWN", f"unknown policy {policy}")


def verify_receipt_chain(receipts: list[RoutingReceipt]) -> bool:
    prev: str | None = None
    for r in receipts:
        if r.prev_receipt_hash != prev:
            return False
        if r.dual_primary != 0 or r.live_api is not False:
            return False
        prev = r.content_hash()
    return True
