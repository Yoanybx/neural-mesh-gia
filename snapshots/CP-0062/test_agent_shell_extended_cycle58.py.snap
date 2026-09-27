"""Tests for Cycle 58 / CP-0062: agent_shell_extended_scenarios.

Markers: agent_shell_extended_cycle58
Mock-only; live=DISABLED; no N>2 runtime; no Raft; no live LLM; no settlement.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

import pytest

from neural_mesh import __version__
from neural_mesh.packaging.agent_shell_extended import (
    ABORT_CODES,
    ALLOWED_TOOLS,
    CYCLE,
    LIVE_API_ENABLED,
    N_CAP,
    PACKAGE_HELD,
    PREFERRED_NEXT_DEFAULT,
    PRIOR_CP,
    PROBE_NAMES,
    SCHEMA_SHELL_EXT,
    SEAL_CP,
    MockAgentShellAdapter,
    ShellMembershipBridge,
    run_multi_turn,
    run_probe_matrix,
    sample_workload,
    verify_receipt_chain,
)
from neural_mesh.packaging.m2_membership_rejoin import (
    MemberState,
    MembershipError,
    TrustTierName,
)

pytestmark = [pytest.mark.agent_shell_extended_cycle58]

REPO = Path(__file__).resolve().parents[1]
DESIGN = REPO / "docs" / "design" / "AGENT_SHELL_EXTENDED_SCENARIOS.md"
CAP = REPO / "docs" / "capabilities" / "MESH_AGENT_SHELL_EXTENDED.md"
AGREEMENT = REPO / "council" / "COUNCIL_AGREEMENT_CYCLE58.md"
PASTE = REPO / "council" / "PASTE_CYCLE58_M2M.md"
PKG = REPO / "src" / "neural_mesh" / "packaging" / "agent_shell_extended.py"


def test_version_and_constants():
    assert __version__ == "0.18.0"
    assert PACKAGE_HELD == "0.18.0"
    assert SEAL_CP == "CP-0062"
    assert PRIOR_CP == "CP-0061"
    assert CYCLE == 58
    assert PREFERRED_NEXT_DEFAULT == "0.19_design_set_signoff_v2"
    assert SCHEMA_SHELL_EXT == "mesh.shell.extended_bridge/v0"
    assert N_CAP == 2
    assert LIVE_API_ENABLED is False
    assert "echo" in ALLOWED_TOOLS
    assert "SCHEMA_INVALID" in ABORT_CODES
    assert "SHELL_MEMBER_DRAINING" in ABORT_CODES
    assert "schema" in PROBE_NAMES


def test_design_note_and_capability():
    assert DESIGN.is_file()
    text = DESIGN.read_text(encoding="utf-8")
    assert "CP-0062" in text
    assert "multi-turn" in text.lower() or "Multi-turn" in text
    assert "probe" in text.lower()
    assert "churn" in text.lower() or "DRAINING" in text
    assert "T-shell-a" in text and "T-shell-b" in text and "T-shell-c" in text
    assert "live=DISABLED" in text or "LIVE_API_ENABLED" in text
    assert "hash-chain" in text.lower() or "hash-chained" in text.lower() or "Receipt" in text
    assert "NO_HELD" in text
    assert "settlement" in text.lower()
    assert CAP.is_file()
    ctext = CAP.read_text(encoding="utf-8")
    assert "CP-0062" in ctext
    assert "NO_HELD" in ctext
    assert "MESH_AGENT_SHELL_EXTENDED" in ctext or "Agent-Shell Extended" in ctext


def test_happy_multi_turn_pipeline():
    ad = MockAgentShellAdapter()
    wl = sample_workload()
    report = run_multi_turn(ad, wl, turns=3, use_judge=True)
    assert report["verdict"] == "ACCEPT"
    assert report["receipt_id"].startswith("rcpt:")
    assert any(e["type"] == "final" for e in report["normalized_events"])
    # step_start + 3*(call+result) + final = at least 8 events
    assert len(report["normalized_events"]) >= 8
    assert all(p["ok"] for p in report["probe_results"])
    assert report["receipt"]["live_api"] is False


def test_multi_turn_with_membership_and_judge():
    b = ShellMembershipBridge()
    b.bring_active("n1", tier=TrustTierName.T2)
    wl = sample_workload(workload_id="wl:00000000-0000-4000-8000-000000000010")
    sub = b.submit("n1", wl)
    assert sub["verdict"] == "ACCEPT"
    for i in range(2):
        ack = b.ingest_event(
            "n1",
            {
                "schema": "mesh.shell.event/v0",
                "event_id": f"sev:m{i}",
                "workload_id": wl["workload_id"],
                "type": "tool_call",
                "tool": {"name": "hash_probe", "side_effect": False},
                "payload_digest": "sha256:" + ("d" * 64),
                "ts_hlc": f"mock-hlc-m{i}",
            },
        )
        assert ack["ok"] is True
    report = b.finalize("n1", wl["workload_id"], use_judge=True)
    assert report["verdict"] == "ACCEPT"
    assert report["receipt"]["judge_receipt_id"] is not None
    assert report["receipt"]["judge_receipt_id"].startswith("rcpt:")
    assert verify_receipt_chain(b.shell.receipts)


def test_probe_matrix():
    result = run_probe_matrix()
    assert len(result.cases) >= 7
    assert result.all_aborted_or_ok, result.cases
    names = {c["name"] for c in result.cases}
    assert "schema" in names
    assert "dual_primary" in names
    assert "audit" in names
    assert "tool_allowlist" in names
    assert "forbid_side_effects" in names
    assert "max_steps" in names
    assert "no_dry_run" in names


def test_receipt_chain_under_churn():
    b = ShellMembershipBridge()
    b.bring_active("n1")
    # happy finalize → first receipt
    wl1 = sample_workload(workload_id="wl:00000000-0000-4000-8000-000000000021")
    assert b.submit("n1", wl1)["verdict"] == "ACCEPT"
    r1 = b.finalize("n1", wl1["workload_id"])
    assert r1["verdict"] == "ACCEPT"

    # start second workload then drain mid-flight
    wl2 = sample_workload(
        workload_id="wl:00000000-0000-4000-8000-000000000022",
        idempotency_key="shell-ext-fam-2",
    )
    assert b.submit("n1", wl2)["verdict"] == "ACCEPT"
    b.ingest_event(
        "n1",
        {
            "schema": "mesh.shell.event/v0",
            "event_id": "sev:mid",
            "workload_id": wl2["workload_id"],
            "type": "tool_call",
            "tool": {"name": "echo", "side_effect": False},
            "payload_digest": "sha256:" + ("e" * 64),
            "ts_hlc": "mock-hlc-mid",
        },
    )
    b.drain("n1")
    assert b.sm.records["n1"].state == MemberState.DRAINING
    # cancelled
    assert wl2["workload_id"] in b.shell.cancelled
    mid = b.shell.finalize(wl2["workload_id"])
    assert mid["verdict"] == "ABORT"
    assert mid["abort"]["code"] == "SHELL_INFLIGHT_CANCELLED"

    # new submit while draining refused
    wl3 = sample_workload(
        workload_id="wl:00000000-0000-4000-8000-000000000023",
        idempotency_key="shell-ext-fam-3",
    )
    refused = b.submit("n1", wl3)
    assert refused["verdict"] == "ABORT"
    assert refused["abort"]["code"] == "SHELL_MEMBER_DRAINING"

    assert verify_receipt_chain(b.shell.receipts)
    assert len(b.shell.receipts) >= 3


def test_t_shell_a_not_active_states():
    """T-shell-a: shell while JOINING / LEFT / REJOIN / ATTESTING → NOT_ACTIVE."""
    b = ShellMembershipBridge()
    b.join("n1")
    assert b.sm.records["n1"].state == MemberState.JOINING
    bad = b.submit("n1", sample_workload())
    assert bad["verdict"] == "ABORT"
    assert bad["abort"]["code"] == "SHELL_MEMBER_NOT_ACTIVE"

    b.begin_attest("n1")
    assert b.sm.records["n1"].state == MemberState.ATTESTING
    bad2 = b.submit("n1", sample_workload(workload_id="wl:00000000-0000-4000-8000-000000000031"))
    assert bad2["abort"]["code"] == "SHELL_MEMBER_NOT_ACTIVE"

    b.attest_ok("n1")
    b.drain("n1")
    b.drain_complete("n1")
    assert b.sm.records["n1"].state == MemberState.LEFT
    bad3 = b.submit("n1", sample_workload(workload_id="wl:00000000-0000-4000-8000-000000000032"))
    assert bad3["abort"]["code"] == "SHELL_MEMBER_NOT_ACTIVE"

    b.rejoin_intent("n1")
    assert b.sm.records["n1"].state == MemberState.REJOIN
    bad4 = b.submit("n1", sample_workload(workload_id="wl:00000000-0000-4000-8000-000000000033"))
    assert bad4["abort"]["code"] == "SHELL_MEMBER_NOT_ACTIVE"


def test_t_shell_b_draining_and_cancel():
    """T-shell-b: DRAINING refuses new; mid-workload cancel."""
    b = ShellMembershipBridge()
    b.bring_active("n1", tier=TrustTierName.T3)
    wl = sample_workload(workload_id="wl:00000000-0000-4000-8000-000000000041")
    assert b.submit("n1", wl)["verdict"] == "ACCEPT"
    b.drain("n1")
    assert wl["workload_id"] in b.shell.cancelled
    ack = b.shell.ingest_event(
        {
            "schema": "mesh.shell.event/v0",
            "event_id": "sev:after-drain",
            "workload_id": wl["workload_id"],
            "type": "tool_call",
            "tool": {"name": "echo", "side_effect": False},
            "payload_digest": "sha256:" + ("f" * 64),
            "ts_hlc": "mock-hlc-ad",
        }
    )
    assert ack["ok"] is False
    assert ack["abort"]["code"] == "SHELL_INFLIGHT_CANCELLED"
    refused = b.submit(
        "n1",
        sample_workload(workload_id="wl:00000000-0000-4000-8000-000000000042"),
    )
    assert refused["abort"]["code"] == "SHELL_MEMBER_DRAINING"


def test_t_shell_c_probe_matrix_and_n_gt2():
    """T-shell-c: probe matrix ABORTs + N>2 refuse."""
    result = run_probe_matrix()
    assert result.all_aborted_or_ok
    b = ShellMembershipBridge()
    b.bring_active("n1")
    b.bring_active("n2")
    with pytest.raises(MembershipError) as ei:
        b.join("n3")
    assert "N>" in str(ei.value) or getattr(ei.value, "code", "") == "MEMBER_N_GT2_REFUSED" or "N>" in repr(ei.value)
    # MembershipError should carry MEMBER_N_GT2_REFUSED
    code = getattr(ei.value, "code", None)
    if code:
        assert code == "MEMBER_N_GT2_REFUSED"


def test_left_rejoin_inflight_cancel():
    b = ShellMembershipBridge()
    b.bring_active("n1")
    wl = sample_workload(workload_id="wl:00000000-0000-4000-8000-000000000051")
    assert b.submit("n1", wl)["verdict"] == "ACCEPT"
    b.drain("n1")
    b.drain_complete("n1")
    # already cancelled on drain; rejoin also cancels (idempotent)
    b.rejoin_intent("n1")
    assert wl["workload_id"] in b.shell.cancelled
    assert verify_receipt_chain(b.shell.receipts)


def test_live_api_stays_disabled():
    ad = MockAgentShellAdapter(live_api_enabled=True)
    r = ad.submit(sample_workload())
    assert r["verdict"] == "ABORT"
    assert r["abort"]["code"] == "SHELL_LIVE_DISABLED"
    assert LIVE_API_ENABLED is False


def test_agreement_and_paste():
    assert AGREEMENT.is_file()
    atext = AGREEMENT.read_text(encoding="utf-8")
    assert "CP-0062" in atext
    assert "agent_shell_extended" in atext
    assert PASTE.is_file()
    ptext = PASTE.read_text(encoding="utf-8")
    assert "CYCLE: 58" in ptext
    assert "CP-0062" in ptext
    assert "LAST_SEALED:" in ptext
    assert "CP-0061" in ptext
    assert "de228b0" in ptext
    assert "PREFERRED_NEXT" in ptext
    assert "0.19_design_set_signoff_v2" in ptext
    assert "live=DISABLED" in ptext or "DISABLED" in ptext


def test_packaging_file_and_no_settlement_unlock():
    assert PKG.is_file()
    text = PKG.read_text(encoding="utf-8")
    assert "LIVE_API_ENABLED = False" in text
    assert "settlement" not in text.lower() or "no settlement" in text.lower()
    for rel in (
        "docs/design/AGENT_SHELL_EXTENDED_SCENARIOS.md",
        "docs/capabilities/MESH_AGENT_SHELL_EXTENDED.md",
    ):
        t = (REPO / rel).read_text(encoding="utf-8").lower()
        assert "we are gia" not in t
        assert "agi achieved" not in t
        assert "settlement live" not in t


def test_tags_untouched():
    assert (
        subprocess.run(
            ["git", "rev-parse", "--verify", "v0.18.0"],
            cwd=str(REPO),
            capture_output=True,
        ).returncode
        == 0
    )


def test_no_src_shell_runtime_codec():
    src = REPO / "src" / "neural_mesh"
    for name in ("shell_adapter.py", "agent_shell.py", "shell_spike.py"):
        assert not (src / name).is_file(), name
