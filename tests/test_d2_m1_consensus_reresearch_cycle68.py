"""Tests for Cycle 68 / CP-0072: D2 M1 consensus candidate re-research.

Markers: d2_m1_consensus_reresearch_cycle68
Design-only C67 re-weighted scorecard + C5 FQ-ED sketch.
M1=NO_CONSENSUS_YET; no Raft default; live=DISABLED; pkg0190 NOT_OPENED;
MESH_PERF_EXPERIMENTAL=OFF; no GIA/Raft/N>2/train/SaaS.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from neural_mesh import __version__
from neural_mesh.packaging.d2_m1_consensus_reresearch import (
    AXIS_WEIGHTS,
    CANDIDATE_TOTALS,
    CAPABILITY_DOC,
    CLOSEST_CANDIDATE,
    CLOSEST_SCORE,
    COMPOSED_CPS,
    CYCLE,
    D4_FINDINGS_DOC,
    DESIGN_DOC,
    MUST_STAY_FALSE,
    PACKAGE_HELD,
    PLANNING_DOC,
    PREFERRED_NEXT_DEFAULT,
    PRIOR_CP,
    PROVISIONAL_SCORES,
    RATIFY_THRESHOLD,
    SCHEMA_DOC,
    SCHEMA_ID,
    SEAL_CP,
    UNLOCK_CANDIDATES,
    VERDICT,
    axis_weight_sum,
    default_reresearch_gate,
    evaluate_candidate,
    rejects_raft_default,
    run_d2_m1_reresearch_gates,
    total_score,
    unlock_verdict,
)

pytestmark = [pytest.mark.d2_m1_consensus_reresearch_cycle68]

REPO = Path(__file__).resolve().parents[1]


def test_constants():
    assert __version__ == "0.18.0"
    assert PACKAGE_HELD == "0.18.0"
    assert SEAL_CP == "CP-0072"
    assert PRIOR_CP == "CP-0071"
    assert CYCLE == 68
    assert PREFERRED_NEXT_DEFAULT == "await_deepseek"
    assert SCHEMA_ID == "mesh.membership.m1_reresearch/v0"
    assert RATIFY_THRESHOLD == 80
    assert VERDICT == "NO_CONSENSUS_YET"
    assert CLOSEST_CANDIDATE == "C5"
    assert CLOSEST_SCORE == 78
    assert COMPOSED_CPS == ("CP-0050", "CP-0054", "CP-0071")
    assert "raft_is_default" in MUST_STAY_FALSE
    assert "m1_consensus_default_selected" in MUST_STAY_FALSE


def test_axis_weights_c67():
    assert axis_weight_sum() == 100
    assert AXIS_WEIGHTS == {
        "safety": 30,
        "liveness": 15,
        "fence_compat": 15,
        "no_raft": 10,
        "wan_tolerance": 15,
        "adversary_resistance": 10,
        "complexity": 5,
    }


def test_provisional_totals():
    expected = {"C0": 85, "C1": 54, "C2": 53, "C3": 60, "C4": 73, "C5": 78}
    assert CANDIDATE_TOTALS == expected
    for cid, scores in PROVISIONAL_SCORES.items():
        r = evaluate_candidate(cid, scores)
        assert r.total == expected[cid], (cid, r.total)


def test_no_unlock_candidate_reaches_80():
    results = {
        cid: evaluate_candidate(cid, scores) for cid, scores in PROVISIONAL_SCORES.items()
    }
    for cid, r in results.items():
        if cid in UNLOCK_CANDIDATES:
            assert r.total < RATIFY_THRESHOLD
            assert not r.ratifiable
    assert unlock_verdict(results) == "NO_CONSENSUS_YET"


def test_c0_baseline_not_unlock():
    r = evaluate_candidate("C0", PROVISIONAL_SCORES["C0"])
    assert r.total >= RATIFY_THRESHOLD
    assert not r.unlock_eligible
    assert not r.ratifiable


def test_raft_not_default_and_no_raft_axis_zero():
    assert PROVISIONAL_SCORES["C1"]["no_raft"] == 0
    assert rejects_raft_default(None)
    assert rejects_raft_default("C0")
    assert rejects_raft_default("NO_CONSENSUS_YET")
    assert not rejects_raft_default("C1")
    results = {
        cid: evaluate_candidate(cid, scores) for cid, scores in PROVISIONAL_SCORES.items()
    }
    assert unlock_verdict(results) != "C1"


def test_validate_rejects_overshoot():
    bad = dict(PROVISIONAL_SCORES["C5"])
    bad["safety"] = 99
    with pytest.raises(ValueError):
        total_score(bad)


def test_default_gate():
    gate = default_reresearch_gate()
    assert gate["live_enabled"] is False
    assert gate["m1_status"] == "NO_CONSENSUS_YET"
    assert gate["raft_is_default"] is False
    assert gate["mesh_perf_experimental"] == "OFF"
    assert gate["closest_candidate"] == "C5"
    assert gate["closest_score"] == 78
    assert gate["d1_exit_seal"] == "PASS"
    assert gate["d1_exit_live_discussion"] == "NOT_PASS"
    assert all(v is False for v in gate["must_stay_false"].values())


def test_planning_doc_substance():
    text = (REPO / PLANNING_DOC).read_text(encoding="utf-8")
    assert "CP-0072" in text
    assert "NO_CONSENSUS_YET" in text
    assert "FQ-ED" in text
    assert "live=DISABLED" in text or "**live=DISABLED**" in text
    assert "D4_CHATGPT_FINDINGS" in text or "D4_CHATGPT_FINDINGS.md" in text
    assert "D1 seal exit" in text
    assert "PASS" in text
    assert "adversary" in text.lower() or "Adversary" in text
    assert "independence" in text.lower() or "Independence" in text
    assert "no-Raft" in text or "No-Raft" in text
    assert "78" in text
    assert "C5" in text
    assert "does **not** enable live" in text or "does not enable live" in text.lower()
    for cid in ("C0", "C1", "C2", "C3", "C4", "C5"):
        assert cid in text


def test_design_capability_schema():
    design = (REPO / DESIGN_DOC).read_text(encoding="utf-8")
    cap = (REPO / CAPABILITY_DOC).read_text(encoding="utf-8")
    sch = (REPO / SCHEMA_DOC).read_text(encoding="utf-8")
    assert "NO_CONSENSUS_YET" in design and "78" in design
    assert "CP-0072" in cap
    assert "await_deepseek" in cap
    assert SCHEMA_ID in sch
    assert "must be false" in sch.lower() or "**must be false**" in sch


def test_f2_and_d1_docs_present():
    assert (REPO / D4_FINDINGS_DOC).is_file()
    assert (REPO / "docs/planning/D1_L_JUDGE_SAFETY_CASE_MATURATION.md").is_file()
    assert (REPO / "council/COUNCIL_AGREEMENT_D4.md").is_file()


def test_composed_cps_verified():
    for cp in COMPOSED_CPS:
        data = json.loads(
            (REPO / "snapshots" / cp / "CHECKPOINT.json").read_text(encoding="utf-8")
        )
        assert str(data.get("status", "")).upper() == "VERIFIED", cp


def test_gates_pass(tmp_path: Path):
    out = tmp_path / "releases" / "d2-m1-reresearch"
    result = run_d2_m1_reresearch_gates(
        REPO,
        out_dir=out,
        tip="d20072",
        timestamp="2026-09-27T03:20:00Z",
        pytest_count=1120,
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
    assert data["verdict"] == "NO_CONSENSUS_YET"
    assert data["closest_candidate"] == "C5"
    assert data["closest_score"] == 78
    assert data["raft_is_default"] is False
    assert data["mesh_perf_experimental"] == "OFF"
    assert data["package_open_0190"] is False


@pytest.mark.parametrize(
    "force_fail",
    [
        "planning_doc_present",
        "f2_d4_findings_present",
        "d1_exit_noted",
        "axes_c67_weights",
        "scores_filled",
        "c5_sketch",
        "no_consensus_yet",
        "no_raft_default",
        "composes_d1",
        "live_disabled",
        "mesh_perf_experimental_off",
        "pkg0190_not_opened",
        "prior_m1_cps",
        "no_gia_claim",
        "version_held",
    ],
)
def test_gates_force_fail(tmp_path: Path, force_fail: str):
    result = run_d2_m1_reresearch_gates(
        REPO,
        out_dir=tmp_path / force_fail,
        tip="bad",
        pytest_count=10,
        force_fail=force_fail,
        write_project_state=False,
    )
    assert not result.ok
    assert any(g.name == force_fail and not g.ok for g in result.gates)


def test_agreement_cycle68():
    text = (REPO / "council" / "COUNCIL_AGREEMENT_CYCLE68.md").read_text(encoding="utf-8")
    assert "CP-0072" in text
    assert "NO_CONSENSUS_YET" in text
    assert "live=DISABLED" in text
    assert "FQ-ED" in text or "C5" in text


def test_paste_has_last_sealed():
    text = (REPO / "council" / "PASTE_CYCLE68_M2M.md").read_text(encoding="utf-8")
    assert "LAST_SEALED:" in text
    assert "CP-0071" in text
    assert "PREFERRED_NEXT: await_deepseek" in text
    assert "CP-0072" in text
    assert "c6e824a" in text
    assert "NO_CONSENSUS_YET" in text


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
