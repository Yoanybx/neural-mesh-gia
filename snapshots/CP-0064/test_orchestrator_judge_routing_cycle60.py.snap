"""Tests for Cycle 60 / CP-0064: Orchestrator_judge_routing_DESIGN.

Markers: orchestrator_judge_routing_cycle60
Design-only mock; live=DISABLED; no N>2; no Raft; no train; no live LLM.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

import pytest

from neural_mesh import __version__
from neural_mesh.packaging.m2_membership_rejoin import MemberState, TrustTierName
from neural_mesh.packaging.m3_wan_model import LatencyBand
from neural_mesh.packaging.orchestrator_judge_routing import (
    ABORT_CODES,
    CYCLE,
    LIVE_API_ENABLED,
    N_CAP,
    PACKAGE_HELD,
    PREFERRED_NEXT_DEFAULT,
    PRIOR_CP,
    SCHEMA_CAPABILITY,
    SCHEMA_ENVELOPE,
    SCHEMA_RECEIPT,
    SEAL_CP,
    ActionClass,
    JudgeCapability,
    JudgeCapabilitiesRegistry,
    OrchestratorRouter,
    OversightGate,
    RoutingPolicy,
    RoutingTarget,
    WorkloadClass,
    default_registry,
    sample_envelope,
    verify_receipt_chain,
)

pytestmark = [pytest.mark.orchestrator_judge_routing_cycle60]

REPO = Path(__file__).resolve().parents[1]
DESIGN = REPO / "docs" / "design" / "ORCHESTRATOR_JUDGE_ROUTING_DESIGN.md"
CAP = REPO / "docs" / "capabilities" / "MESH_ORCHESTRATOR_JUDGE_ROUTING.md"
SCHEMA = REPO / "docs" / "schema" / "judge" / "routing_v0.md"
AGREEMENT = REPO / "council" / "COUNCIL_AGREEMENT_CYCLE60.md"
PASTE = REPO / "council" / "PASTE_CYCLE60_M2M.md"
PKG = REPO / "src" / "neural_mesh" / "packaging" / "orchestrator_judge_routing.py"


def test_version_and_constants():
    assert __version__ == "0.18.0"
    assert PACKAGE_HELD == "0.18.0"
    assert SEAL_CP == "CP-0064"
    assert PRIOR_CP == "CP-0063"
    assert CYCLE == 60
    assert PREFERRED_NEXT_DEFAULT == "await_deepseek"
    assert SCHEMA_ENVELOPE == "mesh.orchestrator.routing_envelope/v0"
    assert SCHEMA_RECEIPT == "mesh.orchestrator.routing_receipt/v0"
    assert SCHEMA_CAPABILITY == "mesh.judge.capability/v0"
    assert N_CAP == 2
    assert LIVE_API_ENABLED is False


def test_design_doc_covers_routing_surface():
    assert DESIGN.is_file()
    text = DESIGN.read_text(encoding="utf-8")
    assert "CP-0064" in text
    assert "DESIGN" in text
    assert "Orchestrator" in text or "orchestrator" in text
    assert "L_judge" in text or "L_JUDGE" in text
    assert "agent_shell" in text
    assert "SINGLE_JUDGE" in text
    assert "DUAL_JUDGE_ADVISORY" in text
    assert "FALLBACK" in text
    assert "ABORT" in text
    assert "ABORT_ON_MISMATCH" in text or "ROUTE_JUDGE_MISMATCH" in text
    assert "A3" in text and "A4" in text
    assert "oversight" in text.lower() or "I5" in text
    assert "continuity" in text.lower() or "durable" in text.lower()
    assert "M2" in text and "M3" in text
    assert "NO_CONSENSUS_YET" in text or "advisory" in text.lower()
    assert "live=DISABLED" in text or "LIVE_API_ENABLED" in text
    assert "NO_HELD" in text
    assert "T-route-a" in text and "T-route-b" in text and "T-route-c" in text
    assert "not a frontier" in text.lower() or "not** a frontier" in text.lower() or "≠ frontier" in text
    assert "train" in text.lower()
    # no consciousness leak as claim
    assert "we are conscious" not in text.lower()


def test_schema_and_capability():
    assert SCHEMA.is_file()
    stext = SCHEMA.read_text(encoding="utf-8")
    assert "mesh.orchestrator.routing_envelope/v0" in stext
    assert "mesh.orchestrator.routing_receipt/v0" in stext
    assert "mesh.judge.capability/v0" in stext
    for code in (
        "ROUTE_LIVE_DISABLED",
        "ROUTE_MEMBER_NOT_ACTIVE",
        "ROUTE_JUDGE_MISMATCH",
        "ROUTE_OVERSIGHT_REQUIRED",
    ):
        assert code in stext
    assert CAP.is_file()
    ctext = CAP.read_text(encoding="utf-8")
    assert "CP-0064" in ctext
    assert "NO_HELD" in ctext
    assert "orchestrator" in ctext.lower()


def test_happy_single_judge_advisory():
    r = OrchestratorRouter()
    env = sample_envelope(
        workload_class=WorkloadClass.JUDGE_ADVISORY,
        action_class=ActionClass.A1,
        member_state=MemberState.ACTIVE,
        trust_tier=TrustTierName.T2,
        latency_band=LatencyBand.RTT_mid,
    )
    d = r.route(env)
    assert d.allow is True
    assert d.target == RoutingTarget.L_JUDGE
    assert d.policy == RoutingPolicy.SINGLE_JUDGE
    assert len(d.engine_ids) == 1
    assert d.receipt is not None
    assert d.receipt.decision == "ALLOW"
    assert d.receipt.live_api is False
    assert d.receipt.dual_primary == 0
    assert d.receipt.goal_id.startswith("goal:")
    assert d.receipt.prompt_hash and d.receipt.prompt_hash.startswith("sha256:")
    assert d.receipt.response_hash and d.receipt.response_hash.startswith("sha256:")
    assert d.receipt.continuity_state == "RUNNING"


def test_happy_dual_advisory_critique():
    r = OrchestratorRouter()
    env = sample_envelope(
        workload_class=WorkloadClass.JUDGE_CRITIQUE,
        action_class=ActionClass.A1,
        latency_band=LatencyBand.RTT_lo,
    )
    d = r.route(env)
    assert d.allow is True
    assert d.policy == RoutingPolicy.DUAL_JUDGE_ADVISORY
    assert len(d.engine_ids) == 2
    assert d.abort_on_mismatch is True
    assert d.receipt is not None
    assert d.receipt.advisory_only is True
    # Must not claim consensus
    assert "consensus" not in d.receipt.reason.lower() or "≠" in d.reason or "advisory" in d.reason.lower()


def test_happy_agent_shell_and_safety_probe():
    r = OrchestratorRouter()
    shell = r.route(
        sample_envelope(
            workload_class=WorkloadClass.SHELL_MULTI_TURN,
            action_class=ActionClass.A1,
        )
    )
    assert shell.allow is True
    assert shell.target == RoutingTarget.AGENT_SHELL
    probe = r.route(
        sample_envelope(
            workload_class=WorkloadClass.SAFETY_PROBE,
            action_class=ActionClass.A0,
        )
    )
    assert probe.allow is True
    assert probe.target == RoutingTarget.MESH_LOCAL
    assert verify_receipt_chain(r.receipts)


def test_fallback_on_rtt_x():
    r = OrchestratorRouter()
    # mock-a tolerates RTT_hi only — RTT_x capable list may be empty for advisory
    # Prefer_dual with RTT_x selects FALLBACK; if no engine tolerates x → exhaust
    env = sample_envelope(
        workload_class=WorkloadClass.JUDGE_ADVISORY,
        latency_band=LatencyBand.RTT_x,
    )
    d = r.route(env)
    assert d.allow is False
    assert d.abort_code == "ROUTE_FALLBACK_EXHAUSTED"


def test_continuity_resume_hooks():
    r = OrchestratorRouter()
    first = r.route(sample_envelope(workload_class=WorkloadClass.JUDGE_ADVISORY))
    assert first.allow
    env = sample_envelope(
        workload_class=WorkloadClass.CONTINUITY_RESUME,
        continuity_id="cont:cafebabecafebabe",
        prior_policy=RoutingPolicy.SINGLE_JUDGE,
        prior_engine_ids=tuple(first.engine_ids),
    )
    d = r.route(env)
    assert d.allow is True
    assert d.target == RoutingTarget.L_JUDGE
    assert d.receipt is not None
    assert d.receipt.continuity_id == "cont:cafebabecafebabe"
    assert d.receipt.evidence_kind == "routing_receipt"


def test_t_route_a_member_gates():
    r = OrchestratorRouter()
    for st in (
        MemberState.JOINING,
        MemberState.ATTESTING,
        MemberState.LEFT,
        MemberState.REJOIN,
    ):
        d = r.route(sample_envelope(member_state=st))
        assert d.allow is False
        assert d.abort_code == "ROUTE_MEMBER_NOT_ACTIVE"
    d_drain = r.route(sample_envelope(member_state=MemberState.DRAINING))
    assert d_drain.abort_code == "ROUTE_MEMBER_DRAINING"
    d_tier = r.route(
        sample_envelope(member_state=MemberState.ACTIVE, trust_tier=TrustTierName.T1)
    )
    assert d_tier.abort_code == "ROUTE_MEMBER_NOT_ACTIVE"


def test_t_route_b_oversight_a3_a4():
    r = OrchestratorRouter()
    d3 = r.route(sample_envelope(action_class=ActionClass.A3))
    assert d3.abort_code == "ROUTE_OVERSIGHT_REQUIRED"
    gate = OversightGate()
    gate.approve()
    r2 = OrchestratorRouter(oversight=gate)
    env = sample_envelope(action_class=ActionClass.A3)
    env.oversight.approved = True
    ok = r2.route(env)
    assert ok.allow is True

    d4 = r.route(sample_envelope(action_class=ActionClass.A4))
    assert d4.abort_code == "ROUTE_OVERSIGHT_REQUIRED"
    env4 = sample_envelope(action_class=ActionClass.A4)
    env4.oversight.approved = True
    env4.oversight.deadman_ok = False
    d4b = OrchestratorRouter().route(env4)
    assert d4b.abort_code == "ROUTE_DEADMAN_REQUIRED"
    env4.oversight.deadman_ok = True
    ok4 = OrchestratorRouter().route(env4)
    assert ok4.allow is True

    deny_gate = OversightGate()
    deny_gate.deny()
    d_deny = OrchestratorRouter(oversight=deny_gate).route(
        sample_envelope(action_class=ActionClass.A1)
    )
    assert d_deny.abort_code == "ROUTE_OVERSIGHT_DENIED"


def test_t_route_c_mismatch_n_live_fence_nocapable():
    r = OrchestratorRouter()
    # dual mismatch
    r.dual_response_digests = {
        "judge:mock-a": "sha256:" + "a" * 64,
        "judge:mock-b": "sha256:" + "b" * 64,
    }
    d_mis = r.route(
        sample_envelope(
            workload_class=WorkloadClass.JUDGE_CRITIQUE,
            latency_band=LatencyBand.RTT_lo,
        )
    )
    assert d_mis.abort_code == "ROUTE_JUDGE_MISMATCH"

    d_n = OrchestratorRouter().route(sample_envelope(n_members=3))
    assert d_n.abort_code == "ROUTE_N_GT2_REFUSED"

    d_live = OrchestratorRouter().route(sample_envelope(live_api_enabled=True))
    assert d_live.abort_code == "ROUTE_LIVE_DISABLED"

    d_fence = OrchestratorRouter().route(sample_envelope(dual_primary=1))
    assert d_fence.abort_code == "FENCE"

    empty = OrchestratorRouter(registry=JudgeCapabilitiesRegistry())
    d_empty = empty.route(sample_envelope(workload_class=WorkloadClass.JUDGE_ADVISORY))
    assert d_empty.abort_code == "ROUTE_NO_CAPABLE_ENGINE"

    # dual underprovisioned: only one critique-capable engine
    reg = JudgeCapabilitiesRegistry()
    reg.register(
        JudgeCapability(
            engine_id="judge:only",
            supports=(WorkloadClass.JUDGE_CRITIQUE.value,),
            max_latency_band=LatencyBand.RTT_hi,
        )
    )
    d_dual = OrchestratorRouter(registry=reg).route(
        sample_envelope(workload_class=WorkloadClass.JUDGE_CRITIQUE)
    )
    assert d_dual.abort_code == "ROUTE_DUAL_UNDERPROVISIONED"


def test_receipt_chain_and_invariants():
    r = OrchestratorRouter()
    r.route(sample_envelope(workload_class=WorkloadClass.JUDGE_ADVISORY))
    r.route(sample_envelope(workload_class=WorkloadClass.SHELL_BOUNDED))
    r.route(sample_envelope(member_state=MemberState.JOINING))  # abort
    assert verify_receipt_chain(r.receipts)
    for rcpt in r.receipts:
        d = rcpt.to_dict()
        assert d["dual_primary"] == 0
        assert d["live_api"] is False
        assert d["schema"] == SCHEMA_RECEIPT


def test_abort_codes_documented():
    text = DESIGN.read_text(encoding="utf-8") + SCHEMA.read_text(encoding="utf-8")
    for code in ABORT_CODES:
        assert code in text, code


def test_registry_rejects_live_engine():
    reg = default_registry()
    with pytest.raises(Exception) as ei:
        reg.register(
            JudgeCapability(engine_id="judge:live", live=True)
        )
    assert getattr(ei.value, "code", "") == "ROUTE_LIVE_DISABLED"


def test_no_gia_raft_train_claims():
    text = DESIGN.read_text(encoding="utf-8")
    low = text.lower()
    assert "we unlocked raft" not in low
    assert "n>2 is live" not in low
    assert "agi achieved" not in low
    assert "train-70b" in low or "do_not_train" in low or "no train" in low
    assert "design only" in low or "DESIGN ONLY" in text


def test_no_live_secrets_in_docs():
    for path in (DESIGN, SCHEMA, CAP, PKG):
        text = path.read_text(encoding="utf-8")
        assert not re.search(r"sk-[A-Za-z0-9]{10,}", text), path.name
        assert "BEGIN PRIVATE KEY" not in text


def test_council_paste_operator_intent():
    assert AGREEMENT.is_file()
    assert PASTE.is_file()
    ptext = PASTE.read_text(encoding="utf-8")
    assert "CP-0064" in ptext
    assert "LAST_SEALED" in ptext
    assert "operator_intent" in ptext.lower() or "OPERATOR_INTENT" in ptext or "orchestrator" in ptext.lower()
    assert "PREFERRED_NEXT" in ptext
    assert "await_deepseek" in ptext
    assert "live=DISABLED" in ptext or "LIVE" in ptext
    atext = AGREEMENT.read_text(encoding="utf-8")
    assert "CP-0064" in atext
    assert "NO_HELD" in atext


def test_tags_untouched():
    assert subprocess.run(
        ["git", "rev-parse", "--verify", "v0.18.0"],
        cwd=str(REPO),
        capture_output=True,
    ).returncode == 0


def test_latency_band_filters_engines():
    r = OrchestratorRouter()
    # RTT_hi: mock-b max is mid → excluded; mock-a max hi → included
    d = r.route(
        sample_envelope(
            workload_class=WorkloadClass.JUDGE_ADVISORY,
            latency_band=LatencyBand.RTT_hi,
        )
    )
    assert d.allow is True
    assert d.engine_ids == ["judge:mock-a"]
