"""Tests for Cycle 69 / CP-0073: C5 FQ-ED refinement.

Markers: c5_fq_ed_refinement_cycle69
Design-only honest +2 (fence_compat +1, adversary +1) → C5=80 numeric.
M1=NO_CONSENSUS_YET (fence DESIGN_DRAFTED ≠ green; GOV.2 open).
No Raft default; live=DISABLED; pkg0190 NOT_OPENED; D3 not ACKed;
MESH_PERF_EXPERIMENTAL=OFF; threshold ≥80 held; no GIA/Raft/N>2/train/SaaS.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from neural_mesh import __version__
from neural_mesh.packaging.c5_fq_ed_refinement import (
    AXIS_WEIGHTS,
    CANDIDATE_TOTALS,
    CAPABILITY_DOC,
    CLOSEST_CANDIDATE,
    CLOSEST_SCORE,
    COMPOSED_CPS,
    CORRELATION_CLASSES,
    CYCLE,
    DESIGN_DOC,
    EVIDENCE_KINDS,
    FENCE_PROBE_IDS,
    FENCE_PROBE_STATUS,
    MUST_STAY_FALSE,
    PACKAGE_HELD,
    PLANNING_DOC,
    PREFERRED_NEXT_DEFAULT,
    PRIOR_CLOSEST_SCORE,
    PRIOR_CP,
    PROVISIONAL_SCORES,
    RATIFY_THRESHOLD,
    REMAINING_UNLOCK_GAPS,
    SCHEMA_DOC,
    SCHEMA_ID,
    SEAL_CP,
    UNLOCK_CANDIDATES,
    VERDICT,
    axis_weight_sum,
    default_refinement_gate,
    evaluate_candidate,
    rejects_raft_default,
    run_c5_fq_ed_refinement_gates,
    total_score,
    unlock_verdict,
)

pytestmark = [pytest.mark.c5_fq_ed_refinement_cycle69]

REPO = Path(__file__).resolve().parents[1]


def test_constants():
    assert __version__ == "0.18.0"
    assert PACKAGE_HELD == "0.18.0"
    assert SEAL_CP == "CP-0073"
    assert PRIOR_CP == "CP-0072"
    assert CYCLE == 69
    assert PREFERRED_NEXT_DEFAULT == "await_deepseek"
    assert SCHEMA_ID == "mesh.membership.m1_c5_refinement/v0"
    assert RATIFY_THRESHOLD == 80
    assert VERDICT == "NO_CONSENSUS_YET"
    assert CLOSEST_CANDIDATE == "C5"
    assert CLOSEST_SCORE == 80
    assert PRIOR_CLOSEST_SCORE == 78
    assert FENCE_PROBE_STATUS == "DESIGN_DRAFTED"
    assert COMPOSED_CPS == ("CP-0050", "CP-0054", "CP-0071", "CP-0072")
    assert "raft_is_default" in MUST_STAY_FALSE
    assert "d3_started_without_ack" in MUST_STAY_FALSE
    assert len(REMAINING_UNLOCK_GAPS) >= 3


def test_axis_weights_unchanged():
    assert axis_weight_sum() == 100
    assert AXIS_WEIGHTS["safety"] == 30
    assert RATIFY_THRESHOLD == 80  # not lowered


def test_provisional_totals_and_honest_delta():
    expected = {"C0": 85, "C1": 54, "C2": 53, "C3": 60, "C4": 73, "C5": 80}
    assert CANDIDATE_TOTALS == expected
    assert PROVISIONAL_SCORES["C5"]["fence_compat"] == 13
    assert PROVISIONAL_SCORES["C5"]["adversary_resistance"] == 9
    assert PROVISIONAL_SCORES["C5"]["safety"] == 23  # no fudge
    assert CLOSEST_SCORE - PRIOR_CLOSEST_SCORE == 2


def test_c5_numeric_met_but_not_ratifiable():
    results = {
        cid: evaluate_candidate(cid, scores) for cid, scores in PROVISIONAL_SCORES.items()
    }
    assert results["C5"].numeric_threshold_met
    assert not results["C5"].ratifiable  # fence not DESIGN_REVIEW_GREEN
    for cid in UNLOCK_CANDIDATES - {"C5"}:
        assert results[cid].total < RATIFY_THRESHOLD
    assert unlock_verdict(results) == "NO_CONSENSUS_YET"


def test_raft_not_default():
    assert PROVISIONAL_SCORES["C1"]["no_raft"] == 0
    assert rejects_raft_default(None)
    assert rejects_raft_default("NO_CONSENSUS_YET")
    assert not rejects_raft_default("C1")


def test_validate_rejects_overshoot():
    bad = dict(PROVISIONAL_SCORES["C5"])
    bad["safety"] = 99
    with pytest.raises(ValueError):
        total_score(bad)


def test_default_gate():
    gate = default_refinement_gate()
    assert gate["live_enabled"] is False
    assert gate["m1_status"] == "NO_CONSENSUS_YET"
    assert gate["raft_is_default"] is False
    assert gate["mesh_perf_experimental"] == "OFF"
    assert gate["closest_score"] == 80
    assert gate["prior_closest_score"] == 78
    assert gate["fence_probe_status"] == "DESIGN_DRAFTED"
    assert gate["c5_numeric_threshold_met"] is True
    assert all(v is False for v in gate["must_stay_false"].values())


def test_planning_doc_substance():
    text = (REPO / PLANNING_DOC).read_text(encoding="utf-8")
    assert "CP-0073" in text
    assert "NO_CONSENSUS_YET" in text
    assert "FQ-ED" in text
    assert "live=DISABLED" in text or "**live=DISABLED**" in text
    assert "12→13" in text or "12->13" in text
    assert "8→9" in text or "8->9" in text
    assert "without fudge" in text.lower() or "no fudge" in text.lower() or "Honest" in text
    assert "DESIGN_DRAFTED" in text
    assert "GOV.2" in text
    assert "NOT ACK" in text or "not ACKed" in text or "ACK-gated" in text
    assert "does **not** enable live" in text or "does not enable live" in text.lower()
    for pid in ("FP-H3-a", "FP-H6-a", "FP-H7-a", "FP-ED-a", "FP-ADV-a", "FP-ABORT-a"):
        assert pid in text
    assert "routing_receipt" in text
    assert "≥2" in text or ">=2" in text


def test_design_capability_schema():
    design = (REPO / DESIGN_DOC).read_text(encoding="utf-8")
    cap = (REPO / CAPABILITY_DOC).read_text(encoding="utf-8")
    sch = (REPO / SCHEMA_DOC).read_text(encoding="utf-8")
    assert "NO_CONSENSUS_YET" in design and "80" in design
    assert "CP-0073" in cap
    assert "await_deepseek" in cap
    assert SCHEMA_ID in sch
    assert "DESIGN_DRAFTED" in sch


def test_fence_probe_and_ed_constants():
    assert len(FENCE_PROBE_IDS) >= 12
    assert "FP-H3-a" in FENCE_PROBE_IDS
    assert "routing_receipt" in EVIDENCE_KINDS
    assert "same_provider" in CORRELATION_CLASSES


def test_composed_cps_verified():
    for cp in COMPOSED_CPS:
        data = json.loads(
            (REPO / "snapshots" / cp / "CHECKPOINT.json").read_text(encoding="utf-8")
        )
        assert str(data.get("status", "")).upper() == "VERIFIED", cp


def test_gates_pass(tmp_path: Path):
    out = tmp_path / "releases" / "c5-fq-ed-refinement"
    result = run_c5_fq_ed_refinement_gates(
        REPO,
        out_dir=out,
        tip="c50073",
        timestamp="2026-09-27T03:30:00Z",
        pytest_count=1160,
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
    assert data["closest_score"] == 80
    assert data["prior_closest_score"] == 78
    assert data["fence_probe_status"] == "DESIGN_DRAFTED"
    assert data["raft_is_default"] is False
    assert data["mesh_perf_experimental"] == "OFF"
    assert data["d3_acked"] is False


@pytest.mark.parametrize(
    "force_fail",
    [
        "planning_doc_present",
        "hold_note_present",
        "axes_threshold_held",
        "scores_filled",
        "honest_delta_documented",
        "fence_probe_matrix",
        "evidence_diversity_criteria",
        "no_consensus_yet",
        "remaining_gaps",
        "no_raft_default",
        "live_disabled",
        "mesh_perf_experimental_off",
        "pkg0190_not_opened",
        "prior_m1_cps",
        "d3_not_acked",
        "no_gia_claim",
        "version_held",
    ],
)
def test_gates_force_fail(tmp_path: Path, force_fail: str):
    result = run_c5_fq_ed_refinement_gates(
        REPO,
        out_dir=tmp_path / force_fail,
        tip="bad",
        pytest_count=10,
        force_fail=force_fail,
        write_project_state=False,
    )
    assert not result.ok
    assert any(g.name == force_fail and not g.ok for g in result.gates)


def test_agreement_and_paste_cycle69():
    agree = (REPO / "council" / "COUNCIL_AGREEMENT_CYCLE69.md").read_text(encoding="utf-8")
    paste = (REPO / "council" / "PASTE_CYCLE69_M2M.md").read_text(encoding="utf-8")
    assert "CP-0073" in agree
    assert "NO_CONSENSUS_YET" in agree
    assert "live=DISABLED" in agree
    assert "LAST_SEALED:" in paste
    assert "CP-0072" in paste
    assert "PREFERRED_NEXT: await_deepseek" in paste
    assert "1e028d2" in paste or "CP-0072" in paste
    assert "NO_CONSENSUS_YET" in paste
    assert "80" in paste


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
    for rel in (PLANNING_DOC, CAPABILITY_DOC, DESIGN_DOC):
        t = (REPO / rel).read_text(encoding="utf-8").lower()
        assert "we are gia" not in t
        assert "agi achieved" not in t
        assert "gia unlocked" not in t
