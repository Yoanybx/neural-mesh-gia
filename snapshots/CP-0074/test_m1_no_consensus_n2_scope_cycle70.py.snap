"""Tests for Cycle 70 / CP-0074: M1 permanent NO_CONSENSUS_YET under N=2 scope.

Markers: m1_no_consensus_n2_scope_cycle70
Design-only operator Path C + HOLD. Numeric ≥80 ≠ ratified.
No Raft default; no N>2 unlock; D3 ACK-gated OFF; live=DISABLED;
MESH_PERF_EXPERIMENTAL=OFF; pkg0190 NOT_OPENED; no GIA/train/SaaS.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from neural_mesh import __version__
from neural_mesh.packaging.m1_no_consensus_n2_scope import (
    CANDIDATE_TOTALS,
    CAPABILITY_DOC,
    CLOSEST_CANDIDATE,
    CLOSEST_SCORE,
    COMPOSED_CPS,
    CYCLE,
    DESIGN_DOC,
    FENCE_PROBE_STATUS,
    MUST_STAY_FALSE,
    PACKAGE_HELD,
    PLANNING_DOC,
    POSTURE,
    POSTURE_NOTE,
    PREFERRED_NEXT_DEFAULT,
    PRIOR_CP,
    RATIFY_THRESHOLD,
    REMAINING_UNLOCK_GAPS,
    SCHEMA_DOC,
    SCHEMA_ID,
    SEAL_CP,
    STRUCTURAL_CIRCULARITY,
    VERDICT,
    default_posture_gate,
    numeric_met_does_not_ratify,
    rejects_raft_default,
    run_m1_n2_scope_posture_gates,
)

pytestmark = [pytest.mark.m1_no_consensus_n2_scope_cycle70]

REPO = Path(__file__).resolve().parents[1]


def test_constants():
    assert __version__ == "0.18.0"
    assert PACKAGE_HELD == "0.18.0"
    assert SEAL_CP == "CP-0074"
    assert PRIOR_CP == "CP-0073"
    assert CYCLE == 70
    assert PREFERRED_NEXT_DEFAULT == "await_deepseek"
    assert SCHEMA_ID == "mesh.membership.m1_n2_scope_posture/v0"
    assert RATIFY_THRESHOLD == 80
    assert VERDICT == "NO_CONSENSUS_YET"
    assert POSTURE == "PERMANENT_UNDER_N2_SCOPE"
    assert CLOSEST_CANDIDATE == "C5"
    assert CLOSEST_SCORE == 80
    assert FENCE_PROBE_STATUS == "DESIGN_DRAFTED"
    assert COMPOSED_CPS == ("CP-0050", "CP-0054", "CP-0071", "CP-0072", "CP-0073")
    assert "raft_is_default" in MUST_STAY_FALSE
    assert "d3_started_without_ack" in MUST_STAY_FALSE
    assert "numeric_80_means_ratified" in MUST_STAY_FALSE
    assert "pending_reresearch_under_n2" in MUST_STAY_FALSE
    assert len(REMAINING_UNLOCK_GAPS) >= 3
    assert "n_gt2_safety" in STRUCTURAL_CIRCULARITY


def test_candidate_totals_unchanged():
    expected = {"C0": 85, "C1": 54, "C2": 53, "C3": 60, "C4": 73, "C5": 80}
    assert CANDIDATE_TOTALS == expected
    assert RATIFY_THRESHOLD == 80  # not lowered


def test_numeric_met_does_not_ratify():
    assert numeric_met_does_not_ratify(numeric_met=True, unlocked=False)
    assert not numeric_met_does_not_ratify(numeric_met=True, unlocked=True)
    assert numeric_met_does_not_ratify(numeric_met=False, unlocked=False)


def test_raft_not_default():
    assert rejects_raft_default(None)
    assert rejects_raft_default("NO_CONSENSUS_YET")
    assert rejects_raft_default("C0")
    assert not rejects_raft_default("C1")


def test_default_gate():
    gate = default_posture_gate()
    assert gate["live_enabled"] is False
    assert gate["m1_status"] == "NO_CONSENSUS_YET"
    assert gate["posture"] == "PERMANENT_UNDER_N2_SCOPE"
    assert gate["pending_reresearch"] is False
    assert gate["unlocked"] is False
    assert gate["raft_is_default"] is False
    assert gate["n_gt2_status"] == "NO_HELD"
    assert gate["mesh_perf_experimental"] == "OFF"
    assert gate["d3_acked"] is False
    assert gate["hold_active"] is True
    assert gate["closest_score"] == 80
    assert gate["c5_numeric_threshold_met"] is True
    assert gate["fence_probe_status"] == "DESIGN_DRAFTED"
    assert all(v is False for v in gate["must_stay_false"].values())


def test_posture_note_and_planning_substance():
    note = (REPO / POSTURE_NOTE).read_text(encoding="utf-8")
    text = (REPO / PLANNING_DOC).read_text(encoding="utf-8")
    for blob in (note, text):
        assert "CP-0074" in blob
        assert "NO_CONSENSUS_YET" in blob
        assert "N=2" in blob or "N2" in blob
        assert "HOLD" in blob or "Hold" in blob
    assert "permanent" in note.lower() or "PERMANENT" in note
    assert "structural" in text.lower() or "circular" in text.lower()
    assert "n_gt2_safety" in text or "N>2 safety" in text
    assert "≠ ratified" in text or "not ratified" in text.lower() or "Numeric ≥80" in text
    assert "Raft" in text
    assert "live=DISABLED" in text or "live=DISABLED" in note or "DISABLED" in note
    assert "ACK-gated" in text or "ACK-gated" in note
    assert "does **not**" in text.lower() or "Does not" in text or "does not" in text.lower()


def test_design_capability_schema():
    design = (REPO / DESIGN_DOC).read_text(encoding="utf-8")
    cap = (REPO / CAPABILITY_DOC).read_text(encoding="utf-8")
    sch = (REPO / SCHEMA_DOC).read_text(encoding="utf-8")
    assert "NO_CONSENSUS_YET" in design and "permanent" in design.lower()
    assert "CP-0074" in cap
    assert "await_deepseek" in cap
    assert SCHEMA_ID in sch
    assert "PERMANENT_UNDER_N2_SCOPE" in sch
    assert "hold_active" in sch


def test_composed_cps_verified():
    for cp in COMPOSED_CPS:
        data = json.loads(
            (REPO / "snapshots" / cp / "CHECKPOINT.json").read_text(encoding="utf-8")
        )
        assert str(data.get("status", "")).upper() == "VERIFIED", cp


def test_gates_pass(tmp_path: Path):
    out = tmp_path / "releases" / "m1-no-consensus-n2-scope"
    result = run_m1_n2_scope_posture_gates(
        REPO,
        out_dir=out,
        tip="c50074",
        timestamp="2026-09-27T03:40:00Z",
        pytest_count=1200,
        write_project_state=False,
    )
    assert result.ok, result.errors
    assert result.cp == SEAL_CP
    assert result.prior_cp == PRIOR_CP
    assert result.version == "0.18.0"
    path = Path(result.summary_path)
    assert path.is_file()
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["ok"] is True
    assert data["live"] == "DISABLED"
    assert data["m1_status"] == "NO_CONSENSUS_YET"
    assert data["posture"] == "PERMANENT_UNDER_N2_SCOPE"
    assert data["unlocked"] is False
    assert data["closest_score"] == 80
    assert data["fence_probe_status"] == "DESIGN_DRAFTED"
    assert data["raft_is_default"] is False
    assert data["n_gt2_status"] == "NO_HELD"
    assert data["mesh_perf_experimental"] == "OFF"
    assert data["d3_acked"] is False
    assert data["hold_active"] is True
    assert data["pending_reresearch"] is False


@pytest.mark.parametrize(
    "force_fail",
    [
        "posture_note_present",
        "planning_doc_present",
        "permanent_no_consensus",
        "numeric_not_ratify",
        "no_raft_default",
        "n_gt2_no_held",
        "live_disabled",
        "d3_not_acked",
        "mesh_perf_experimental_off",
        "pkg0190_not_opened",
        "structural_circularity_documented",
        "hold_active",
        "remaining_gaps",
        "prior_m1_cps",
        "no_gia_claim",
        "version_held",
    ],
)
def test_gates_force_fail(tmp_path: Path, force_fail: str):
    result = run_m1_n2_scope_posture_gates(
        REPO,
        out_dir=tmp_path / force_fail,
        tip="bad",
        pytest_count=10,
        force_fail=force_fail,
        write_project_state=False,
    )
    assert not result.ok
    assert any(g.name == force_fail and not g.ok for g in result.gates)


def test_agreement_and_paste_cycle70():
    agree = (REPO / "council" / "COUNCIL_AGREEMENT_CYCLE70.md").read_text(encoding="utf-8")
    paste = (REPO / "council" / "PASTE_CYCLE70_M2M.md").read_text(encoding="utf-8")
    assert "CP-0074" in agree
    assert "NO_CONSENSUS_YET" in agree
    assert "live=DISABLED" in agree
    assert "PERMANENT" in agree.upper() or "permanent" in agree.lower()
    assert "LAST_SEALED:" in paste
    assert "CP-0073" in paste
    assert "PREFERRED_NEXT: await_deepseek" in paste
    assert "a6f53fb" in paste or "CP-0073" in paste
    assert "NO_CONSENSUS_YET" in paste
    assert "HOLD" in paste or "hold" in paste.lower()


def test_tags_untouched_no_v019():
    assert (
        subprocess.run(
            ["git", "rev-parse", "--verify", "v0.18.0"],
            cwd=str(REPO),
            capture_output=True,
        ).returncode
        == 0
    )
    assert (
        subprocess.run(
            ["git", "rev-parse", "--verify", "v0.19.0"],
            cwd=str(REPO),
            capture_output=True,
        ).returncode
        != 0
    )


def test_no_gia_claims():
    for rel in (PLANNING_DOC, CAPABILITY_DOC, DESIGN_DOC, POSTURE_NOTE):
        t = (REPO / rel).read_text(encoding="utf-8").lower()
        assert "we are gia" not in t
        assert "agi achieved" not in t
        assert "gia unlocked" not in t


def test_m1_reresearch_points_to_permanent():
    text = (REPO / "docs/design/fabric/M1_CONSENSUS_RERESEARCH.md").read_text(encoding="utf-8")
    assert "CP-0074" in text
    assert "permanent" in text.lower()
    assert "NO_CONSENSUS_YET" in text
