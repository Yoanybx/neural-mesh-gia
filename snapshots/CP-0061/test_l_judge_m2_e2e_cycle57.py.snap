"""Tests for Cycle 57 / CP-0061: L_judge mock e2e with M2 membership SM.

Markers: l_judge_m2_e2e_cycle57
Mock-only; live=DISABLED; no N>2 runtime; no Raft; no live LLM; no pkg0190.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

import pytest

from neural_mesh import __version__
from neural_mesh.packaging.l_judge_m2_e2e import (
    ABORT_CODES,
    CYCLE,
    LIVE_API_ENABLED,
    N_CAP,
    PACKAGE_HELD,
    PREFERRED_NEXT_DEFAULT,
    PRIOR_CP,
    SCHEMA_BRIDGE,
    SEAL_CP,
    BridgeError,
    JudgeMembershipBridge,
    sample_judge_request,
)
from neural_mesh.packaging.m2_membership_rejoin import (
    MemberState,
    MembershipError,
    TrustTierName,
)

pytestmark = [pytest.mark.l_judge_m2_e2e_cycle57]

REPO = Path(__file__).resolve().parents[1]
DESIGN = REPO / "docs" / "design" / "L_JUDGE_M2_E2E_SPIKE.md"
CAP = REPO / "docs" / "capabilities" / "MESH_L_JUDGE_M2_E2E.md"
AGREEMENT = REPO / "council" / "COUNCIL_AGREEMENT_CYCLE57.md"
PASTE = REPO / "council" / "PASTE_CYCLE57_M2M.md"
PKG = REPO / "src" / "neural_mesh" / "packaging" / "l_judge_m2_e2e.py"


def test_version_and_constants():
    assert __version__ == "0.18.0"
    assert PACKAGE_HELD == "0.18.0"
    assert SEAL_CP == "CP-0061"
    assert PRIOR_CP == "CP-0060"
    assert CYCLE == 57
    assert PREFERRED_NEXT_DEFAULT == "await_deepseek"
    assert SCHEMA_BRIDGE == "mesh.judge.m2_bridge/v0"
    assert N_CAP == 2
    assert LIVE_API_ENABLED is False


def test_design_note_and_capability():
    assert DESIGN.is_file()
    text = DESIGN.read_text(encoding="utf-8")
    assert "CP-0061" in text
    assert "JOINING" in text and "ATTESTING" in text and "ACTIVE" in text
    assert "DRAINING" in text and "REJOIN" in text
    assert "T-M2-judge-a" in text
    assert "T-M2-judge-b" in text
    assert "T-M2-judge-c" in text
    assert "live=DISABLED" in text or "LIVE_API_ENABLED" in text
    assert "hash-chain" in text.lower() or "hash-chained" in text.lower()
    assert "NO_HELD" in text
    assert "no live" in text.lower() or "Mock" in text
    assert CAP.is_file()
    ctext = CAP.read_text(encoding="utf-8")
    assert "CP-0061" in ctext
    assert "NO_HELD" in ctext


def test_happy_path_joining_to_active_with_judgments():
    """JOINING→ATTESTING→ACTIVE(T2) + dry_run + mock live_advisory submit."""
    b = JudgeMembershipBridge()
    b.join("n1", fingerprint="fp1")
    assert b.sm.records["n1"].state == MemberState.JOINING
    # JOINING: judge refused
    bad = b.judge_dry_run("n1", sample_judge_request())
    assert bad["verdict"] == "ABORT"
    assert bad["abort"]["code"] == "JUDGE_MEMBER_NOT_ACTIVE"
    assert bad["receipt_id"]  # audit receipt still emitted

    b.begin_attest("n1")
    assert b.sm.records["n1"].state == MemberState.ATTESTING
    # ATTESTING: dry_run OK
    dry = b.judge_dry_run(
        "n1",
        sample_judge_request(
            request_id="00000000-0000-4000-8000-000000000010",
            idempotency_key="fam-attest",
        ),
    )
    assert dry["verdict"] == "ACCEPT"
    assert dry["receipt_id"].startswith("rcpt:")
    assert dry["engine_meta"]["live_api"] is False

    b.attest_ok("n1", tier=TrustTierName.T2)
    assert b.sm.records["n1"].state == MemberState.ACTIVE
    assert b.sm.records["n1"].tier == TrustTierName.T2

    dry2 = b.judge_dry_run(
        "n1",
        sample_judge_request(
            request_id="00000000-0000-4000-8000-000000000011",
            idempotency_key="fam-active",
        ),
    )
    assert dry2["verdict"] == "ACCEPT"
    sub = b.judge_submit(
        "n1",
        sample_judge_request(
            request_id="00000000-0000-4000-8000-000000000012",
            idempotency_key="fam-active",
            mode="live_advisory",
        ),
    )
    assert sub["verdict"] == "ACCEPT"
    assert sub["engine_meta"]["live_api"] is False
    # hash chain advanced
    assert b.judge.prev_receipt_hash is not None
    assert b.judge.prev_receipt_hash.startswith("sha256:")
    assert len(b.judge.receipts) >= 3


def test_happy_path_t3_and_receipt_chain_order():
    b = JudgeMembershipBridge()
    b.join("n1", fingerprint="fp-t3")
    b.begin_attest("n1")
    b.attest_ok("n1", tier=TrustTierName.T3)
    r1 = b.judge_dry_run(
        "n1",
        sample_judge_request(
            request_id="00000000-0000-4000-8000-000000000021",
            idempotency_key="fam-t3a",
        ),
    )
    r2 = b.judge_dry_run(
        "n1",
        sample_judge_request(
            request_id="00000000-0000-4000-8000-000000000022",
            idempotency_key="fam-t3b",
        ),
    )
    assert r1["receipt_id"] != r2["receipt_id"]
    # second receipt links to first via prev on port
    assert b.judge.receipts[-1]["prev_receipt_hash"] is not None
    assert b.judge.receipts[-1]["dual_primary"] == 0


def test_t_m2_judge_a_not_active_states():
    """T-M2-judge-a: judge while JOINING / LEFT / REJOIN → JUDGE_MEMBER_NOT_ACTIVE."""
    b = JudgeMembershipBridge()
    b.join("n1", fingerprint="fp1")
    r = b.judge_dry_run("n1", sample_judge_request())
    assert r["abort"]["code"] == "JUDGE_MEMBER_NOT_ACTIVE"

    b.begin_attest("n1")
    b.attest_ok("n1", tier=TrustTierName.T2)
    b.drain("n1")
    b.drain_complete("n1")
    assert b.sm.records["n1"].state == MemberState.LEFT
    r2 = b.judge_submit(
        "n1",
        sample_judge_request(
            request_id="00000000-0000-4000-8000-000000000031",
            mode="live_advisory",
        ),
    )
    assert r2["abort"]["code"] == "JUDGE_MEMBER_NOT_ACTIVE"

    b.rejoin_intent("n1")
    assert b.sm.records["n1"].state == MemberState.REJOIN
    r3 = b.judge_dry_run(
        "n1",
        sample_judge_request(request_id="00000000-0000-4000-8000-000000000032"),
    )
    assert r3["abort"]["code"] == "JUDGE_MEMBER_NOT_ACTIVE"


def test_t_m2_judge_b_draining_mid_judgment():
    """T-M2-judge-b: DRAINING cancels in-flight; new judge ABORT."""
    b = JudgeMembershipBridge()
    b.join("n1", fingerprint="fp1")
    b.begin_attest("n1")
    b.attest_ok("n1", tier=TrustTierName.T2)

    # Simulate in-flight PENDING then drain.
    req_id = "00000000-0000-4000-8000-000000000041"
    # Manually park a PENDING flight, then drain (cancel), then try judge.
    from neural_mesh.packaging.l_judge_m2_e2e import InFlightJudge

    b.inflight[req_id] = InFlightJudge(
        request_id=req_id, node_id="n1", mode="dry_run", family="fam-mid"
    )
    assert len(b.pending_for("n1")) == 1
    b.drain("n1")
    assert b.sm.records["n1"].state == MemberState.DRAINING
    assert b.inflight[req_id].status == "CANCELLED"
    assert b.pending_for("n1") == []

    refused = b.judge_dry_run(
        "n1",
        sample_judge_request(request_id="00000000-0000-4000-8000-000000000042"),
    )
    assert refused["verdict"] == "ABORT"
    assert refused["abort"]["code"] == "JUDGE_MEMBER_DRAINING"

    cancelled = b.cancel_inflight(req_id, reason="explicit")
    assert cancelled["abort"]["code"] == "JUDGE_INFLIGHT_CANCELLED"


def test_t_m2_judge_c_attesting_submit_n_gt2_shortcut():
    """T-M2-judge-c: ATTESTING submit ABORT; N>2 refuse; LEFT→ACTIVE forbidden."""
    b = JudgeMembershipBridge()
    b.join("n1", fingerprint="fp1")
    b.begin_attest("n1")
    # dry_run OK in ATTESTING
    ok = b.judge_dry_run(
        "n1",
        sample_judge_request(
            request_id="00000000-0000-4000-8000-000000000051",
            idempotency_key="fam-att",
        ),
    )
    assert ok["verdict"] == "ACCEPT"
    # submit forbidden
    bad = b.judge_submit(
        "n1",
        sample_judge_request(
            request_id="00000000-0000-4000-8000-000000000052",
            idempotency_key="fam-att",
            mode="live_advisory",
        ),
    )
    assert bad["abort"]["code"] == "JUDGE_MEMBER_ATTESTING_SUBMIT"

    b.attest_ok("n1", tier=TrustTierName.T2)
    # second node to fill cap, then third refused
    b.join("n2", fingerprint="fp2")
    b.begin_attest("n2")
    b.attest_ok("n2", tier=TrustTierName.T3)
    assert b.sm.active_count == 2
    with pytest.raises(MembershipError) as ei:
        b.join("n3", fingerprint="fp3")
    assert ei.value.code == "MEMBER_N_GT2_REFUSED"

    # LEFT→ACTIVE shortcut still forbidden
    b.drain("n1")
    b.drain_complete("n1")
    with pytest.raises(MembershipError) as ei2:
        b.sm.force_active_shortcut_from_left("n1")
    assert ei2.value.code == "MEMBER_INVALID_TRANSITION"


def test_left_rejoin_with_inflight_then_reattest():
    """LEFT/REJOIN with in-flight judge request; re-attest restores judging."""
    b = JudgeMembershipBridge()
    b.join("n1", fingerprint="fp1")
    b.begin_attest("n1")
    b.attest_ok("n1", tier=TrustTierName.T2)
    from neural_mesh.packaging.l_judge_m2_e2e import InFlightJudge

    rid = "00000000-0000-4000-8000-000000000061"
    b.inflight[rid] = InFlightJudge(
        request_id=rid, node_id="n1", mode="live_advisory", family="fam-rejoin"
    )
    b.drain("n1")
    b.drain_complete("n1")
    b.rejoin_intent("n1")
    assert b.inflight[rid].status == "CANCELLED"
    assert b.sm.records["n1"].state == MemberState.REJOIN
    refused = b.judge_dry_run(
        "n1", sample_judge_request(request_id="00000000-0000-4000-8000-000000000062")
    )
    assert refused["abort"]["code"] == "JUDGE_MEMBER_NOT_ACTIVE"

    b.enter_joining_from_rejoin("n1")
    b.begin_attest("n1")
    b.attest_ok("n1", tier=TrustTierName.T3)
    ok = b.judge_dry_run(
        "n1",
        sample_judge_request(
            request_id="00000000-0000-4000-8000-000000000063",
            idempotency_key="fam-rejoin-ok",
        ),
    )
    assert ok["verdict"] == "ACCEPT"


def test_fence_dual_primary_abort():
    b = JudgeMembershipBridge()
    b.join("n1", fingerprint="fp1")
    b.begin_attest("n1")
    b.attest_ok("n1", tier=TrustTierName.T2)
    req = sample_judge_request(request_id="00000000-0000-4000-8000-000000000071")
    req["injection"]["fence"]["dual_primary"] = 1
    resp = b.judge_dry_run("n1", req)
    assert resp["verdict"] == "ABORT"
    assert resp["abort"]["code"] == "FENCE"


def test_live_api_disabled_invariant():
    assert LIVE_API_ENABLED is False
    b = JudgeMembershipBridge()
    assert b.live_api_enabled is False
    b.join("n1", fingerprint="fp1")
    b.begin_attest("n1")
    b.attest_ok("n1", tier=TrustTierName.T2)
    with pytest.raises(BridgeError) as ei:
        b.judge_dry_run(
            "n1",
            sample_judge_request(
                request_id="00000000-0000-4000-8000-000000000081",
                engine={"provider": "openai", "model_hint": "x"},
            ),
        )
    assert ei.value.code == "JUDGE_LIVE_DISABLED"


def test_no_audit_abort():
    b = JudgeMembershipBridge()
    b.judge.audit_sink = False
    b.join("n1", fingerprint="fp1")
    b.begin_attest("n1")
    b.attest_ok("n1", tier=TrustTierName.T2)
    resp = b.judge_dry_run(
        "n1", sample_judge_request(request_id="00000000-0000-4000-8000-000000000091")
    )
    assert resp["abort"]["code"] == "NO_AUDIT"


def test_abort_codes_documented():
    text = DESIGN.read_text(encoding="utf-8") + CAP.read_text(encoding="utf-8")
    for code in (
        "JUDGE_MEMBER_NOT_ACTIVE",
        "JUDGE_MEMBER_DRAINING",
        "JUDGE_INFLIGHT_CANCELLED",
        "JUDGE_MEMBER_ATTESTING_SUBMIT",
    ):
        assert code in text, code
    assert set(ABORT_CODES)  # non-empty


def test_no_runtime_judge_codec():
    src = REPO / "src" / "neural_mesh"
    for name in ("judge_mix.py", "l_judge.py", "judge_port.py", "judge_integration.py"):
        assert not (src / name).is_file(), name
    assert PKG.is_file()


def test_no_gia_raft_live_claims():
    text = DESIGN.read_text(encoding="utf-8")
    low = text.lower()
    assert "we unlocked raft" not in low
    assert "agi achieved" not in low
    assert "n>2 is live" not in low
    assert "live=disabled" in low
    # Must not claim live is on
    assert "live is enabled" not in low
    assert "live_api_enabled = true" not in low
    assert "live_api_enabled=true" not in low


def test_no_live_secrets_in_docs():
    for path in (DESIGN, CAP, PKG):
        text = path.read_text(encoding="utf-8")
        assert not re.search(r"sk-[A-Za-z0-9]{10,}", text), path.name


def test_council_paste_last_sealed():
    assert AGREEMENT.is_file()
    assert PASTE.is_file()
    ptext = PASTE.read_text(encoding="utf-8")
    assert "CYCLE: 57" in ptext
    assert "CP-0061" in ptext
    assert "LAST_SEALED:" in ptext
    assert "CP-0060" in ptext
    assert "L_judge_mock_e2e" in ptext or "L_JUDGE_M2" in ptext or "M2_SM" in ptext
    assert "PREFERRED_NEXT" in ptext
    assert "live=DISABLED" in ptext or "live=DISABLED" in ptext.lower() or "DISABLED" in ptext


def test_tags_untouched():
    assert (
        subprocess.run(
            ["git", "rev-parse", "--verify", "v0.18.0"],
            cwd=str(REPO),
            capture_output=True,
        ).returncode
        == 0
    )
