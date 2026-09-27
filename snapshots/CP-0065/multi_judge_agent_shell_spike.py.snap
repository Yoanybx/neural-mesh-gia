"""Multi-judge + agent_shell spike (CP-0065 / Cycle 61).

Composes CP-0064 OrchestratorRouter with two mock judgment engines and
CP-0062 agent_shell under M2 churn (DRAINING→LEFT→REJOIN). Exercises
DUAL_ADVISORY, FALLBACK, ABORT_MISMATCH. Verifies receipt hash-chain,
no double-invoke, attribution. Mock-only; live=DISABLED; M1=NO_CONSENSUS_YET
(dual advisory ≠ consensus). No N>2, no Raft, no train, no GIA, no SaaS.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import Any

from neural_mesh.packaging.agent_shell_extended import (
    MockAgentShellAdapter,
    sample_workload,
)
from neural_mesh.packaging.m2_membership_rejoin import (
    MemberState,
    MembershipSM,
    TrustTierName,
)
from neural_mesh.packaging.m3_wan_model import LatencyBand
from neural_mesh.packaging.orchestrator_judge_routing import (
    ActionClass,
    JudgeCapabilitiesRegistry,
    JudgeCapability,
    OrchestratorRouter,
    OversightGate,
    RoutingDecision,
    RoutingEnvelope,
    RoutingPolicy,
    RoutingReceipt,
    RoutingTarget,
    WorkloadClass,
    sample_envelope,
    verify_receipt_chain as verify_routing_receipt_chain,
)

__all__ = [
    "PACKAGE_HELD",
    "CYCLE",
    "SEAL_CP",
    "PRIOR_CP",
    "PREFERRED_NEXT_DEFAULT",
    "LIVE_API_ENABLED",
    "SCHEMA_SPIKE",
    "SCHEMA_SPIKE_RECEIPT",
    "N_CAP",
    "M1_STATUS",
    "ABORT_CODES",
    "CHURN_SEQUENCE",
    "MockJudgmentEngine",
    "SpikeReceipt",
    "SpikeReport",
    "MultiJudgeAgentShellSpike",
    "two_judge_registry",
    "sample_spike_envelope",
    "verify_spike_receipt_chain",
    "verify_no_double_invoke",
    "verify_attribution",
]

PACKAGE_HELD = "0.18.0"
CYCLE = 61
SEAL_CP = "CP-0065"
PRIOR_CP = "CP-0064"
PREFERRED_NEXT_DEFAULT = "await_deepseek"
LIVE_API_ENABLED = False  # must stay False (live=DISABLED)
SCHEMA_SPIKE = "mesh.orchestrator.multi_judge_shell_spike/v0"
SCHEMA_SPIKE_RECEIPT = "mesh.orchestrator.spike_receipt/v0"
N_CAP = 2
M1_STATUS = "NO_CONSENSUS_YET"  # dual advisory ≠ M1 consensus

ABORT_CODES: tuple[str, ...] = (
    "SPIKE_LIVE_DISABLED",
    "SPIKE_MEMBER_NOT_ACTIVE",
    "SPIKE_MEMBER_DRAINING",
    "SPIKE_DOUBLE_INVOKE",
    "SPIKE_MISSING_ATTRIBUTION",
    "SPIKE_N_GT2_REFUSED",
    "SPIKE_FENCE",
    "SPIKE_SCHEMA_INVALID",
    "ROUTE_JUDGE_MISMATCH",
    "ROUTE_DUAL_UNDERPROVISIONED",
    "ROUTE_FALLBACK_EXHAUSTED",
    "ROUTE_NO_CAPABLE_ENGINE",
    "ROUTE_MEMBER_DRAINING",
    "ROUTE_MEMBER_NOT_ACTIVE",
    "ROUTE_N_GT2_REFUSED",
    "ROUTE_LIVE_DISABLED",
    "FENCE",
)

# Canonical churn path exercised by this spike
CHURN_SEQUENCE: tuple[MemberState, ...] = (
    MemberState.DRAINING,
    MemberState.LEFT,
    MemberState.REJOIN,
)


def _digest16(payload: dict[str, Any]) -> str:
    blob = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(blob).hexdigest()[:16]


def _sha256(text: str) -> str:
    return "sha256:" + hashlib.sha256(text.encode()).hexdigest()


@dataclass
class MockJudgmentEngine:
    """In-process mock judgment engine (not a live LLM)."""

    engine_id: str
    model_hint: str = "mock-judge"
    invoke_count: int = 0
    last_prompt_hash: str | None = None
    last_response_digest: str | None = None
    # Optional override for ABORT_MISMATCH tests
    forced_digest: str | None = None
    live: bool = False

    def invoke(self, *, prompt_body: str, request_id: str) -> dict[str, Any]:
        if self.live or LIVE_API_ENABLED:
            raise RuntimeError("SPIKE_LIVE_DISABLED")
        self.invoke_count += 1
        prompt_hash = _sha256(prompt_body)
        self.last_prompt_hash = prompt_hash
        digest = self.forced_digest or _sha256(
            f"adv:{self.engine_id}:{prompt_body}:agree"
        )
        self.last_response_digest = digest
        return {
            "engine_id": self.engine_id,
            "model_hint": self.model_hint,
            "request_id": request_id,
            "prompt_hash": prompt_hash,
            "response_digest": digest,
            "invoke_ordinal": self.invoke_count,
            "live": False,
            "advisory_only": True,
            "m1_consensus": False,  # dual advisory ≠ consensus
        }


@dataclass
class SpikeReceipt:
    receipt_id: str
    phase: str
    decision: str
    policy: str | None
    target: str | None
    engine_ids: list[str]
    attributions: list[dict[str, Any]]
    invoke_counts: dict[str, int]
    member_state: str
    latency_band: str | None
    abort_code: str | None
    abort_reason: str | None
    goal_id: str | None
    continuity_id: str | None
    routing_receipt_id: str | None
    shell_workload_id: str | None
    advisory_only: bool = True
    m1_status: str = M1_STATUS
    dual_primary: int = 0
    live_api: bool = False
    prev_receipt_hash: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": SCHEMA_SPIKE_RECEIPT,
            "receipt_id": self.receipt_id,
            "phase": self.phase,
            "decision": self.decision,
            "policy": self.policy,
            "target": self.target,
            "engine_ids": list(self.engine_ids),
            "attributions": list(self.attributions),
            "invoke_counts": dict(self.invoke_counts),
            "member_state": self.member_state,
            "latency_band": self.latency_band,
            "abort": {"code": self.abort_code, "reason": self.abort_reason},
            "goal_id": self.goal_id,
            "continuity_id": self.continuity_id,
            "routing_receipt_id": self.routing_receipt_id,
            "shell_workload_id": self.shell_workload_id,
            "advisory_only": self.advisory_only,
            "m1_status": self.m1_status,
            "dual_primary": 0,
            "live_api": False,
            "prev_receipt_hash": self.prev_receipt_hash,
        }

    def content_hash(self) -> str:
        d = self.to_dict()
        d.pop("prev_receipt_hash", None)
        return "sha256:" + hashlib.sha256(
            json.dumps(d, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()


@dataclass
class SpikeReport:
    ok: bool
    phase: str
    decision: str
    abort_code: str | None
    receipt: SpikeReceipt
    routing: RoutingDecision | None = None
    shell_report: dict[str, Any] | None = None
    attributions: list[dict[str, Any]] = field(default_factory=list)
    double_invoke: bool = False


def two_judge_registry() -> JudgeCapabilitiesRegistry:
    """Exactly two mock judges — dual advisory provisioned; N_CAP=2 held."""
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
            max_latency_band=LatencyBand.RTT_x,  # enables FALLBACK under RTT_x
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
    return reg


def sample_spike_envelope(**kwargs: Any) -> RoutingEnvelope:
    return sample_envelope(**kwargs)


@dataclass
class MultiJudgeAgentShellSpike:
    """Spike harness: orchestrator routing × two mock judges × agent_shell × M2 churn."""

    membership: MembershipSM = field(default_factory=MembershipSM)
    router: OrchestratorRouter = field(default_factory=lambda: OrchestratorRouter(
        registry=two_judge_registry()
    ))
    shell: MockAgentShellAdapter = field(default_factory=MockAgentShellAdapter)
    engines: dict[str, MockJudgmentEngine] = field(default_factory=dict)
    spike_receipts: list[SpikeReceipt] = field(default_factory=list)
    # Per-request invoke ledger to detect double-invoke within a single route
    _request_invokes: dict[str, set[str]] = field(default_factory=dict)
    _req_seq: int = 0
    node_id: str = "n1"

    def __post_init__(self) -> None:
        if not self.engines:
            self.engines = {
                "judge:mock-a": MockJudgmentEngine(
                    engine_id="judge:mock-a", model_hint="mock-judge-a"
                ),
                "judge:mock-b": MockJudgmentEngine(
                    engine_id="judge:mock-b", model_hint="mock-judge-b"
                ),
            }
        # Keep router dual digests in sync with engines by default
        if not self.router.dual_response_digests:
            # Digests filled at invoke time; leave empty so router uses agree default
            pass

    def _next_request_id(self, prefix: str = "req") -> str:
        self._req_seq += 1
        return f"{prefix}:{self._req_seq:04d}"

    def bring_active(
        self, node_id: str | None = None, *, tier: TrustTierName = TrustTierName.T2
    ) -> None:
        nid = node_id or self.node_id
        self.membership.join_intent(nid, fingerprint=f"fp-{nid}")
        self.membership.begin_attest(nid)
        self.membership.attest_ok(nid, tier=tier)

    def member_state(self, node_id: str | None = None) -> MemberState:
        nid = node_id or self.node_id
        rec = self.membership.records.get(nid)
        if rec is None:
            return MemberState.LEFT
        return rec.state

    def trust_tier(self, node_id: str | None = None) -> TrustTierName:
        nid = node_id or self.node_id
        rec = self.membership.records.get(nid)
        if rec is None:
            return TrustTierName.T0
        return rec.tier

    def apply_churn_step(self, target: MemberState, node_id: str | None = None) -> MemberState:
        """Advance membership toward DRAINING→LEFT→REJOIN (fail-closed at each gate)."""
        nid = node_id or self.node_id
        cur = self.member_state(nid)
        if target == MemberState.DRAINING:
            if cur == MemberState.ACTIVE:
                self.membership.drain(nid)
            return self.member_state(nid)
        if target == MemberState.LEFT:
            if cur == MemberState.ACTIVE:
                self.membership.drain(nid)
                cur = self.member_state(nid)
            if cur == MemberState.DRAINING:
                self.membership.drain_complete(nid)
            return self.member_state(nid)
        if target == MemberState.REJOIN:
            if cur == MemberState.ACTIVE:
                self.membership.drain(nid)
                cur = self.member_state(nid)
            if cur == MemberState.DRAINING:
                self.membership.drain_complete(nid)
                cur = self.member_state(nid)
            if cur == MemberState.LEFT:
                self.membership.rejoin_intent(nid)
            return self.member_state(nid)
        raise ValueError(f"unsupported churn target {target}")

    def run_churn_sequence(self, node_id: str | None = None) -> list[MemberState]:
        nid = node_id or self.node_id
        seen: list[MemberState] = []
        for st in CHURN_SEQUENCE:
            seen.append(self.apply_churn_step(st, nid))
        return seen

    def _prev_hash(self) -> str | None:
        if not self.spike_receipts:
            return None
        return self.spike_receipts[-1].content_hash()

    def _emit(
        self,
        *,
        phase: str,
        decision: str,
        policy: str | None,
        target: str | None,
        engine_ids: list[str],
        attributions: list[dict[str, Any]],
        member_state: str,
        latency_band: str | None,
        abort_code: str | None = None,
        abort_reason: str | None = None,
        goal_id: str | None = None,
        continuity_id: str | None = None,
        routing_receipt_id: str | None = None,
        shell_workload_id: str | None = None,
    ) -> SpikeReceipt:
        counts = {eid: self.engines[eid].invoke_count for eid in self.engines}
        body = {
            "phase": phase,
            "decision": decision,
            "engines": engine_ids,
            "member": member_state,
            "abort": abort_code,
        }
        rid = "spike:" + _digest16(body)
        rcpt = SpikeReceipt(
            receipt_id=rid,
            phase=phase,
            decision=decision,
            policy=policy,
            target=target,
            engine_ids=list(engine_ids),
            attributions=list(attributions),
            invoke_counts=counts,
            member_state=member_state,
            latency_band=latency_band,
            abort_code=abort_code,
            abort_reason=abort_reason,
            goal_id=goal_id,
            continuity_id=continuity_id,
            routing_receipt_id=routing_receipt_id,
            shell_workload_id=shell_workload_id,
            advisory_only=True,
            m1_status=M1_STATUS,
            prev_receipt_hash=self._prev_hash(),
        )
        self.spike_receipts.append(rcpt)
        return rcpt

    def _envelope_from_member(
        self,
        *,
        workload_class: WorkloadClass,
        latency_band: LatencyBand = LatencyBand.RTT_lo,
        action_class: ActionClass = ActionClass.A1,
        prefer_dual: bool = False,
        n_members: int = N_CAP,
        live_api_enabled: bool = False,
        dual_primary: int = 0,
        prompt_body: str = "spike-prompt",
        node_id: str | None = None,
        request_id: str | None = None,
        **extra: Any,
    ) -> RoutingEnvelope:
        nid = node_id or self.node_id
        rid = request_id or self._next_request_id()
        return sample_envelope(
            request_id=rid,
            workload_class=workload_class,
            action_class=action_class,
            member_state=self.member_state(nid),
            trust_tier=self.trust_tier(nid),
            latency_band=latency_band,
            prefer_dual=prefer_dual,
            n_members=n_members,
            live_api_enabled=live_api_enabled,
            dual_primary=dual_primary,
            prompt_body=prompt_body,
            **extra,
        )

    def _invoke_selected(
        self, decision: RoutingDecision, env: RoutingEnvelope
    ) -> tuple[list[dict[str, Any]], bool, str | None]:
        """Invoke each selected engine exactly once. Returns (attrs, double, abort)."""
        attributions: list[dict[str, Any]] = []
        req = env.request_id
        seen = self._request_invokes.setdefault(req, set())
        for eid in decision.engine_ids:
            if eid in seen:
                return attributions, True, "SPIKE_DOUBLE_INVOKE"
            eng = self.engines.get(eid)
            if eng is None:
                return attributions, False, "SPIKE_MISSING_ATTRIBUTION"
            result = eng.invoke(prompt_body=env.prompt_body, request_id=req)
            seen.add(eid)
            attributions.append(
                {
                    "engine_id": eid,
                    "invoke_ordinal": result["invoke_ordinal"],
                    "response_digest": result["response_digest"],
                    "prompt_hash": result["prompt_hash"],
                    "advisory_only": True,
                    "m1_consensus": False,
                }
            )
        # Attribution completeness: every engine_id must appear
        attributed_ids = {a["engine_id"] for a in attributions}
        if set(decision.engine_ids) != attributed_ids:
            return attributions, False, "SPIKE_MISSING_ATTRIBUTION"
        return attributions, False, None

    def execute_route(
        self,
        env: RoutingEnvelope,
        *,
        phase: str = "route",
        also_shell: bool = False,
    ) -> SpikeReport:
        if LIVE_API_ENABLED or env.live_api_enabled:
            rcpt = self._emit(
                phase=phase,
                decision="ABORT",
                policy=None,
                target=None,
                engine_ids=[],
                attributions=[],
                member_state=env.member_state.value,
                latency_band=env.latency_band.value,
                abort_code="SPIKE_LIVE_DISABLED",
                abort_reason="live path forbidden",
                goal_id=env.goal_id,
                continuity_id=env.continuity_id,
            )
            return SpikeReport(
                ok=False,
                phase=phase,
                decision="ABORT",
                abort_code="SPIKE_LIVE_DISABLED",
                receipt=rcpt,
            )

        decision = self.router.route(env)
        routing_rid = decision.receipt.receipt_id if decision.receipt else None

        if not decision.allow:
            # Map membership aborts into spike-visible codes while preserving route code
            code = decision.abort_code
            rcpt = self._emit(
                phase=phase,
                decision="ABORT",
                policy=decision.policy.value if decision.policy else None,
                target=decision.target.value if decision.target else None,
                engine_ids=list(decision.engine_ids),
                attributions=[],
                member_state=env.member_state.value,
                latency_band=env.latency_band.value,
                abort_code=code,
                abort_reason=decision.reason,
                goal_id=env.goal_id,
                continuity_id=env.continuity_id,
                routing_receipt_id=routing_rid,
            )
            return SpikeReport(
                ok=False,
                phase=phase,
                decision="ABORT",
                abort_code=code,
                receipt=rcpt,
                routing=decision,
            )

        attributions: list[dict[str, Any]] = []
        double = False
        inv_abort: str | None = None
        shell_report: dict[str, Any] | None = None
        shell_wid: str | None = None

        if decision.target == RoutingTarget.L_JUDGE and decision.engine_ids:
            attributions, double, inv_abort = self._invoke_selected(decision, env)
            if double or inv_abort:
                code = inv_abort or "SPIKE_DOUBLE_INVOKE"
                rcpt = self._emit(
                    phase=phase,
                    decision="ABORT",
                    policy=decision.policy.value,
                    target=decision.target.value,
                    engine_ids=list(decision.engine_ids),
                    attributions=attributions,
                    member_state=env.member_state.value,
                    latency_band=env.latency_band.value,
                    abort_code=code,
                    abort_reason="invoke guard failed",
                    goal_id=env.goal_id,
                    continuity_id=env.continuity_id,
                    routing_receipt_id=routing_rid,
                )
                return SpikeReport(
                    ok=False,
                    phase=phase,
                    decision="ABORT",
                    abort_code=code,
                    receipt=rcpt,
                    routing=decision,
                    attributions=attributions,
                    double_invoke=double,
                )

        if decision.target == RoutingTarget.AGENT_SHELL or also_shell:
            wl = sample_workload(
                workload_id="wl:spike-" + _digest16({"g": env.goal_id, "p": phase})
            )
            shell_report = self.shell.submit(wl)
            shell_wid = wl["workload_id"]
            if shell_report.get("verdict") == "ACCEPT":
                # Bounded single-shot finalize without judge (keep live=DISABLED)
                shell_report = self.shell.finalize(
                    wl["workload_id"], require_prior_dry_run=False
                )

        rcpt = self._emit(
            phase=phase,
            decision="ALLOW",
            policy=decision.policy.value,
            target=decision.target.value,
            engine_ids=list(decision.engine_ids),
            attributions=attributions,
            member_state=env.member_state.value,
            latency_band=env.latency_band.value,
            goal_id=env.goal_id,
            continuity_id=env.continuity_id,
            routing_receipt_id=routing_rid,
            shell_workload_id=shell_wid,
        )
        return SpikeReport(
            ok=True,
            phase=phase,
            decision="ALLOW",
            abort_code=None,
            receipt=rcpt,
            routing=decision,
            shell_report=shell_report,
            attributions=attributions,
        )

    def run_dual_advisory(
        self,
        *,
        mismatch: bool = False,
        latency_band: LatencyBand = LatencyBand.RTT_lo,
        node_id: str | None = None,
        phase: str = "dual_advisory",
    ) -> SpikeReport:
        """Exercise DUAL_JUDGE_ADVISORY (advisory_only; ≠ M1 consensus)."""
        if mismatch:
            # Force router mismatch via dual_response_digests
            self.router.dual_response_digests = {
                "judge:mock-a": "sha256:" + "a" * 64,
                "judge:mock-b": "sha256:" + "b" * 64,
            }
        else:
            self.router.dual_response_digests = {}
        env = self._envelope_from_member(
            workload_class=WorkloadClass.JUDGE_CRITIQUE,
            latency_band=latency_band,
            prefer_dual=True,
            node_id=node_id,
            prompt_body="dual-advisory-spike",
        )
        return self.execute_route(env, phase=phase)

    def run_fallback(
        self,
        *,
        latency_band: LatencyBand = LatencyBand.RTT_x,
        node_id: str | None = None,
        phase: str = "fallback",
    ) -> SpikeReport:
        env = self._envelope_from_member(
            workload_class=WorkloadClass.JUDGE_ADVISORY,
            latency_band=latency_band,
            node_id=node_id,
            prompt_body="fallback-spike",
        )
        return self.execute_route(env, phase=phase)

    def run_shell(
        self,
        *,
        multi_turn: bool = False,
        node_id: str | None = None,
        phase: str = "shell",
    ) -> SpikeReport:
        wc = (
            WorkloadClass.SHELL_MULTI_TURN
            if multi_turn
            else WorkloadClass.SHELL_BOUNDED
        )
        env = self._envelope_from_member(
            workload_class=wc,
            latency_band=LatencyBand.RTT_lo,
            node_id=node_id,
            prompt_body="shell-spike",
        )
        return self.execute_route(env, phase=phase, also_shell=True)

    def run_under_churn(
        self,
        *,
        policy_kind: str = "dual",
        node_id: str | None = None,
    ) -> list[SpikeReport]:
        """Route under each churn state; expect ABORT at DRAINING/LEFT/REJOIN."""
        nid = node_id or self.node_id
        reports: list[SpikeReport] = []
        # Ensure we start ACTIVE then walk churn
        if self.member_state(nid) != MemberState.ACTIVE:
            # Reset membership for clean churn walk
            self.membership = MembershipSM()
            self.bring_active(nid)
        for st in CHURN_SEQUENCE:
            # Reset SM path from ACTIVE each time for isolated state tests
            self.membership = MembershipSM()
            self.bring_active(nid)
            self.apply_churn_step(st, nid)
            if policy_kind == "dual":
                reports.append(
                    self.run_dual_advisory(
                        node_id=nid, phase=f"churn_{st.value}_dual"
                    )
                )
            elif policy_kind == "fallback":
                reports.append(
                    self.run_fallback(
                        node_id=nid, phase=f"churn_{st.value}_fallback"
                    )
                )
            else:
                reports.append(
                    self.run_shell(node_id=nid, phase=f"churn_{st.value}_shell")
                )
        return reports

    def force_double_invoke_attempt(
        self, env: RoutingEnvelope | None = None
    ) -> SpikeReport:
        """Negative helper: simulate a second invoke of the same engine for a request."""
        env = env or self._envelope_from_member(
            workload_class=WorkloadClass.JUDGE_ADVISORY,
            latency_band=LatencyBand.RTT_lo,
            prompt_body="double-invoke-probe",
        )
        decision = self.router.route(env)
        if not decision.allow or not decision.engine_ids:
            # Still emit abort path
            return self.execute_route(env, phase="double_invoke_probe")
        # First legitimate invoke
        attrs, double, abort = self._invoke_selected(decision, env)
        assert not double and abort is None
        # Second illicit invoke of same engine_ids
        attrs2, double2, abort2 = self._invoke_selected(decision, env)
        code = abort2 or ("SPIKE_DOUBLE_INVOKE" if double2 else None)
        rcpt = self._emit(
            phase="double_invoke_probe",
            decision="ABORT",
            policy=decision.policy.value,
            target=decision.target.value,
            engine_ids=list(decision.engine_ids),
            attributions=attrs + attrs2,
            member_state=env.member_state.value,
            latency_band=env.latency_band.value,
            abort_code=code,
            abort_reason="double-invoke detected",
            goal_id=env.goal_id,
            continuity_id=env.continuity_id,
            routing_receipt_id=decision.receipt.receipt_id if decision.receipt else None,
        )
        return SpikeReport(
            ok=False,
            phase="double_invoke_probe",
            decision="ABORT",
            abort_code=code,
            receipt=rcpt,
            routing=decision,
            attributions=attrs + attrs2,
            double_invoke=bool(double2),
        )


def verify_spike_receipt_chain(receipts: list[SpikeReceipt]) -> bool:
    prev: str | None = None
    for r in receipts:
        if r.prev_receipt_hash != prev:
            return False
        if r.dual_primary != 0 or r.live_api is not False:
            return False
        if r.m1_status != M1_STATUS:
            return False
        if not r.advisory_only:
            return False
        prev = r.content_hash()
    return True


def verify_no_double_invoke(spike: MultiJudgeAgentShellSpike) -> bool:
    """True iff no request invoked the same engine twice."""
    for req, engines in spike._request_invokes.items():
        # set semantics already unique; also check engine counters vs ledger size
        _ = req
        if len(engines) != len(set(engines)):
            return False
    # Cross-check: for any single request, ordinals must be unique per engine
    # Engine invoke_count is global; double-invoke within a request is the guard.
    for r in spike.spike_receipts:
        if r.abort_code == "SPIKE_DOUBLE_INVOKE":
            # Presence of the abort means the guard fired — ok for neg tests,
            # but "verify_no_double_invoke" on a clean happy path should be True
            # only when no such abort exists in ALLOW receipts.
            pass
        seen: set[str] = set()
        for a in r.attributions:
            eid = a["engine_id"]
            if eid in seen and r.decision == "ALLOW":
                return False
            seen.add(eid)
    return True


def verify_attribution(report: SpikeReport) -> bool:
    """Every engine_id in the routing decision has an attribution entry."""
    if report.routing is None:
        return report.abort_code is not None  # abort without engines is fine
    if not report.ok:
        # Abort before invoke may lack attributions
        if not report.routing.engine_ids:
            return True
        if report.abort_code in (
            "ROUTE_JUDGE_MISMATCH",
            "ROUTE_DUAL_UNDERPROVISIONED",
            "ROUTE_FALLBACK_EXHAUSTED",
            "ROUTE_NO_CAPABLE_ENGINE",
            "ROUTE_MEMBER_DRAINING",
            "ROUTE_MEMBER_NOT_ACTIVE",
            "ROUTE_N_GT2_REFUSED",
            "ROUTE_LIVE_DISABLED",
            "FENCE",
            "SPIKE_LIVE_DISABLED",
            "SPIKE_MEMBER_DRAINING",
            "SPIKE_MEMBER_NOT_ACTIVE",
            "SPIKE_N_GT2_REFUSED",
            "SPIKE_FENCE",
        ):
            return True
    attributed = {a["engine_id"] for a in report.attributions}
    return set(report.routing.engine_ids) == attributed
