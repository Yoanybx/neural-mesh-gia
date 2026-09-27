"""Tests for Cycle 61 / CP-0065: multi_judge_agent_shell_spike.

Markers: multi_judge_agent_shell_spike_cycle61
Mock-only; live=DISABLED; no N>2; no Raft; no live LLM; M1=NO_CONSENSUS_YET.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

import pytest

from neural_mesh import __version__
from neural_mesh.packaging.m2_membership_rejoin import MemberState, TrustTierName
from neural_mesh.packaging.m3_wan_model import LatencyBand
from neural_mesh.packaging.multi_judge_agent_shell_spike import (
    ABORT_CODES,
    CHURN_SEQUENCE,
    CYCLE,
    LIVE_API_ENABLED,
    M1_STATUS,
    N_CAP,
    PACKAGE_HELD,
    PREFERRED_NEXT_DEFAULT,
    PRIOR_CP,
    SCHEMA_SPIKE,
    SCHEMA_SPIKE_RECEIPT,
    SEAL_CP,
    MultiJudgeAgentShellSpike,
    sample_spike_envelope,
    two_judge_registry,
    verify_attribution,
    verify_no_double_invoke,
    verify_spike_receipt_chain,
)
from neural_mesh.packaging.orchestrator_judge_routing import (
    JudgeCapabilitiesRegistry,
    JudgeCapability,
    OrchestratorRouter,
    RoutingPolicy,
    RoutingTarget,
    WorkloadClass,
)

pytestmark = [pytest.mark.multi_judge_agent_shell_spike_cycle61]

REPO = Path(__file__).resolve().parents[1]
DESIGN = REPO / "docs" / "design" / "MULTI_JUDGE_AGENT_SHELL_SPIKE.md"
CAP = REPO / "docs" / "capabilities" / "MESH_MULTI_JUDGE_AGENT_SHELL_SPIKE.md"
AGREEMENT = REPO / "council" / "COUNCIL_AGREEMENT_CYCLE61.md"
PASTE = REPO / "council" / "PASTE_CYCLE61_M2M.md"
PKG = REPO / "src" / "neural_mesh" / "packaging" / "multi_judge_agent_shell_spike.py"


def test_version_and_constants():
    assert __version__ == "0.18.0"
    assert PACKAGE_HELD == "0.18.0"
    assert SEAL_CP == "CP-0065"
    assert PRIOR_CP == "CP-0064"
    assert CYCLE == 61
    assert PREFERRED_NEXT_DEFAULT == "await_deepseek"
    assert SCHEMA_SPIKE == "mesh.orchestrator.multi_judge_shell_spike/v0"
    assert SCHEMA_SPIKE_RECEIPT == "mesh.orchestrator.spike_receipt/v0"
    assert N_CAP == 2
    assert LIVE_API_ENABLED is False
    assert M1_STATUS == "NO_CONSENSUS_YET"
    assert CHURN_SEQUENCE == (
        MemberState.DRAINING,
        MemberState.LEFT,
        MemberState.REJOIN,
    )
    assert "SPIKE_DOUBLE_INVOKE" in ABORT_CODES
    assert "ROUTE_JUDGE_MISMATCH" in ABORT_CODES


def test_design_and_capability():
    assert DESIGN.is_file()
    text = DESIGN.read_text(encoding="utf-8")
    assert "CP-0065" in text
    assert "multi_judge" in text.lower() or "Multi-Judge" in text
    assert "DUAL" in text and "FALLBACK" in text
    assert "ABORT" in text
    assert "DRAINING" in text and "LEFT" in text and "REJOIN" in text
    assert "T-route-spike-a" in text and "T-route-spike-b" in text and "T-route-spike-c" in text
    assert "NO_CONSENSUS_YET" in text
    assert "live=DISABLED" in text or "LIVE_API_ENABLED" in text
    assert "hash-chain" in text.lower() or "hash-chained" in text.lower()
    assert "double-invoke" in text.lower() or "double_invoke" in text.lower()
    assert "attribution" in text.lower()
    assert "NO_HELD" in text
    assert CAP.is_file()
    ctext = CAP.read_text(encoding="utf-8")
    assert "CP-0065" in ctext
    assert "MESH_MULTI_JUDGE_AGENT_SHELL_SPIKE" in ctext
    assert "NO_CONSENSUS_YET" in ctext


def test_happy_dual_advisory_attribution():
    s = MultiJudgeAgentShellSpike()
    s.bring_active()
    r = s.run_dual_advisory()
    assert r.ok is True
    assert r.routing is not None
    assert r.routing.policy == RoutingPolicy.DUAL_JUDGE_ADVISORY
    assert r.routing.target == RoutingTarget.L_JUDGE
    assert set(r.routing.engine_ids) == {"judge:mock-a", "judge:mock-b"}
    assert verify_attribution(r)
    assert len(r.attributions) == 2
    assert all(a["advisory_only"] and a["m1_consensus"] is False for a in r.attributions)
    assert r.receipt.m1_status == M1_STATUS
    assert r.receipt.advisory_only is True
    assert r.receipt.live_api is False
    assert r.receipt.dual_primary == 0


def test_happy_fallback_and_shell():
    s = MultiJudgeAgentShellSpike()
    s.bring_active()
    fb = s.run_fallback()
    assert fb.ok is True
    assert fb.routing.policy == RoutingPolicy.FALLBACK_CHAIN
    assert fb.routing.engine_ids == ["judge:mock-a"]
    assert verify_attribution(fb)
    sh = s.run_shell()
    assert sh.ok is True
    assert sh.routing.target == RoutingTarget.AGENT_SHELL
    assert sh.shell_report is not None
    assert sh.shell_report["verdict"] == "ACCEPT"
    assert sh.shell_report["receipt"]["live_api"] is False
    assert verify_spike_receipt_chain(s.spike_receipts)
    assert verify_no_double_invoke(s)


def test_t_route_spike_a_churn_gates():
    """T-route-spike-a: dual under DRAINING/LEFT/REJOIN → membership ABORT."""
    s = MultiJudgeAgentShellSpike()
    reports = s.run_under_churn(policy_kind="dual")
    assert len(reports) == 3
    assert reports[0].abort_code == "ROUTE_MEMBER_DRAINING"
    assert reports[1].abort_code == "ROUTE_MEMBER_NOT_ACTIVE"
    assert reports[2].abort_code == "ROUTE_MEMBER_NOT_ACTIVE"
    for r in reports:
        assert r.ok is False
        assert r.receipt.m1_status == M1_STATUS
    # shell under churn likewise
    s2 = MultiJudgeAgentShellSpike()
    shell_reports = s2.run_under_churn(policy_kind="shell")
    assert all(not r.ok for r in shell_reports)
    assert shell_reports[0].abort_code == "ROUTE_MEMBER_DRAINING"
    assert verify_spike_receipt_chain(s.spike_receipts)
    assert verify_spike_receipt_chain(s2.spike_receipts)


def test_t_route_spike_b_mismatch_double_invoke():
    """T-route-spike-b: mismatch + double-invoke guards."""
    s = MultiJudgeAgentShellSpike()
    s.bring_active()
    mis = s.run_dual_advisory(mismatch=True)
    assert mis.ok is False
    assert mis.abort_code == "ROUTE_JUDGE_MISMATCH"
    # no attributions on mismatch (aborted before invoke)
    assert mis.attributions == []

    s2 = MultiJudgeAgentShellSpike()
    s2.bring_active()
    dbl = s2.force_double_invoke_attempt()
    assert dbl.ok is False
    assert dbl.abort_code == "SPIKE_DOUBLE_INVOKE"
    assert dbl.double_invoke is True


def test_t_route_spike_c_n_live_fence_fallback_exhaust():
    """T-route-spike-c: N>2, live, fence, fallback exhaust."""
    s = MultiJudgeAgentShellSpike()
    s.bring_active()
    env_n = s._envelope_from_member(
        workload_class=WorkloadClass.JUDGE_ADVISORY, n_members=3
    )
    rn = s.execute_route(env_n, phase="n_gt2")
    assert rn.abort_code == "ROUTE_N_GT2_REFUSED"

    env_live = s._envelope_from_member(
        workload_class=WorkloadClass.JUDGE_ADVISORY, live_api_enabled=True
    )
    rl = s.execute_route(env_live, phase="live")
    assert rl.abort_code in ("SPIKE_LIVE_DISABLED", "ROUTE_LIVE_DISABLED")

    env_fence = s._envelope_from_member(
        workload_class=WorkloadClass.JUDGE_ADVISORY, dual_primary=1
    )
    rf = s.execute_route(env_fence, phase="fence")
    assert rf.abort_code == "FENCE"

    empty = MultiJudgeAgentShellSpike()
    empty.router = OrchestratorRouter(registry=JudgeCapabilitiesRegistry())
    empty.bring_active()
    # RTT_x → FALLBACK; empty registry → exhaust
    ex = empty.run_fallback()
    assert ex.abort_code == "ROUTE_FALLBACK_EXHAUSTED"


def test_receipt_chain_post_churn_and_invariants():
    s = MultiJudgeAgentShellSpike()
    s.bring_active()
    s.run_dual_advisory()
    s.run_fallback()
    s.run_shell()
    s.run_under_churn(policy_kind="dual")
    assert verify_spike_receipt_chain(s.spike_receipts)
    assert len(s.spike_receipts) >= 6
    for rcpt in s.spike_receipts:
        d = rcpt.to_dict()
        assert d["schema"] == SCHEMA_SPIKE_RECEIPT
        assert d["dual_primary"] == 0
        assert d["live_api"] is False
        assert d["advisory_only"] is True
        assert d["m1_status"] == M1_STATUS


def test_two_judge_registry_no_live():
    reg = two_judge_registry()
    assert len(reg.engines) == 2
    assert all(e.live is False for e in reg.engines)
    with pytest.raises(Exception) as ei:
        reg.register(JudgeCapability(engine_id="judge:live", live=True))
    assert getattr(ei.value, "code", "") == "ROUTE_LIVE_DISABLED"


def test_abort_codes_documented():
    text = DESIGN.read_text(encoding="utf-8")
    for code in (
        "SPIKE_DOUBLE_INVOKE",
        "SPIKE_MISSING_ATTRIBUTION",
        "ROUTE_JUDGE_MISMATCH",
        "ROUTE_MEMBER_DRAINING",
        "ROUTE_N_GT2_REFUSED",
    ):
        assert code in text or code in ABORT_CODES


def test_no_gia_raft_train_consensus_collapse():
    text = DESIGN.read_text(encoding="utf-8")
    low = text.lower()
    assert "we unlocked raft" not in low
    assert "n>2 is live" not in low
    assert "agi achieved" not in low
    assert "no_consensus_yet" in low or "NO_CONSENSUS_YET" in text
    assert "≠ consensus" in text or "!= consensus" in low or "not consensus" in low
    assert "spike" in low


def test_no_live_secrets_in_docs():
    for path in (DESIGN, CAP, PKG):
        text = path.read_text(encoding="utf-8")
        assert not re.search(r"sk-[A-Za-z0-9]{10,}", text), path.name
        assert "BEGIN PRIVATE KEY" not in text


def test_council_paste_last_sealed():
    assert AGREEMENT.is_file()
    assert PASTE.is_file()
    ptext = PASTE.read_text(encoding="utf-8")
    assert "CP-0065" in ptext
    assert "LAST_SEALED" in ptext
    assert "CP-0064" in ptext
    assert "PREFERRED_NEXT" in ptext
    assert "await_deepseek" in ptext or "MESH_PERF" in ptext
    assert "NO_CONSENSUS_YET" in ptext or "m1=NO_CONSENSUS_YET" in ptext.lower()
    assert "live=DISABLED" in ptext or "LIVE" in ptext
    atext = AGREEMENT.read_text(encoding="utf-8")
    assert "CP-0065" in atext
    assert "NO_HELD" in atext


def test_tags_untouched():
    assert subprocess.run(
        ["git", "rev-parse", "--verify", "v0.18.0"],
        cwd=str(REPO),
        capture_output=True,
    ).returncode == 0


def test_sample_envelope_helper():
    env = sample_spike_envelope(
        workload_class=WorkloadClass.JUDGE_ADVISORY,
        member_state=MemberState.ACTIVE,
        trust_tier=TrustTierName.T2,
        latency_band=LatencyBand.RTT_lo,
    )
    assert env.member_state == MemberState.ACTIVE
