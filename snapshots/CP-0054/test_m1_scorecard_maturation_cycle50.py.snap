"""Tests for Cycle 50 / CP-0054: M1 scorecard maturation.

Design-only helpers: axis weights, candidate totals, ≥80 ratification,
no-default-Raft, NO_CONSENSUS_YET when no unlock candidate clears the bar.
Markers: m1_scorecard_maturation_cycle50
"""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping

import pytest

from neural_mesh import __version__

pytestmark = [pytest.mark.m1_scorecard_maturation_cycle50]

REPO = Path(__file__).resolve().parents[1]

# --- Scorecard helpers (design-only; no consensus runtime) ---

AXIS_WEIGHTS: dict[str, int] = {
    "safety": 20,
    "fence": 15,
    "liveness_n2": 10,
    "liveness_ngt2": 10,
    "ops": 10,
    "audit_obs": 10,
    "wan_hlc": 10,
    "unlock_evidence": 10,
    "reversibility": 5,
}

RATIFY_THRESHOLD = 80
UNLOCK_CANDIDATES = frozenset({"C1", "C2", "C3", "C4", "C5"})

# Provisional design scores from M1_SCORECARD_MATURATION.md (CP-0054)
PROVISIONAL_SCORES: dict[str, dict[str, int]] = {
    "C0": {
        "safety": 20,
        "fence": 15,
        "liveness_n2": 10,
        "liveness_ngt2": 0,
        "ops": 10,
        "audit_obs": 10,
        "wan_hlc": 5,
        "unlock_evidence": 10,
        "reversibility": 5,
    },
    "C1": {  # Raft — not default
        "safety": 16,
        "fence": 8,
        "liveness_n2": 7,
        "liveness_ngt2": 9,
        "ops": 6,
        "audit_obs": 7,
        "wan_hlc": 6,
        "unlock_evidence": 5,
        "reversibility": 4,
    },
    "C2": {
        "safety": 15,
        "fence": 7,
        "liveness_n2": 6,
        "liveness_ngt2": 8,
        "ops": 4,
        "audit_obs": 7,
        "wan_hlc": 5,
        "unlock_evidence": 4,
        "reversibility": 3,
    },
    "C3": {
        "safety": 14,
        "fence": 7,
        "liveness_n2": 6,
        "liveness_ngt2": 9,
        "ops": 5,
        "audit_obs": 6,
        "wan_hlc": 8,
        "unlock_evidence": 4,
        "reversibility": 3,
    },
    "C4": {
        "safety": 17,
        "fence": 12,
        "liveness_n2": 9,
        "liveness_ngt2": 7,
        "ops": 6,
        "audit_obs": 8,
        "wan_hlc": 7,
        "unlock_evidence": 5,
        "reversibility": 4,
    },
}


@dataclass(frozen=True)
class ScorecardResult:
    candidate_id: str
    total: int
    axis_scores: Mapping[str, int]
    unlock_eligible: bool
    ratifiable: bool


def axis_weight_sum() -> int:
    return sum(AXIS_WEIGHTS.values())


def validate_axis_scores(scores: Mapping[str, int]) -> None:
    if set(scores) != set(AXIS_WEIGHTS):
        missing = set(AXIS_WEIGHTS) - set(scores)
        extra = set(scores) - set(AXIS_WEIGHTS)
        raise ValueError(f"axis mismatch missing={missing} extra={extra}")
    for axis, pts in scores.items():
        cap = AXIS_WEIGHTS[axis]
        if not isinstance(pts, int) or pts < 0 or pts > cap:
            raise ValueError(f"axis {axis} score {pts} out of range 0..{cap}")


def total_score(scores: Mapping[str, int]) -> int:
    validate_axis_scores(scores)
    return sum(scores.values())


def evaluate_candidate(candidate_id: str, scores: Mapping[str, int]) -> ScorecardResult:
    total = total_score(scores)
    unlock_eligible = candidate_id in UNLOCK_CANDIDATES
    # C0 is baseline-only; never an N>2 unlock ratification
    ratifiable = unlock_eligible and total >= RATIFY_THRESHOLD
    return ScorecardResult(
        candidate_id=candidate_id,
        total=total,
        axis_scores=dict(scores),
        unlock_eligible=unlock_eligible,
        ratifiable=ratifiable,
    )



def rejects_raft_default(policy_default: str | None) -> bool:
    """Hard rule: no default = Raft. Default must be None or C0 (stay)."""
    return policy_default in (None, "C0", "NO_CONSENSUS_YET")


def unlock_verdict(results: Mapping[str, ScorecardResult]) -> str:
    """Return chosen unlock id, or NO_CONSENSUS_YET if none ratifiable."""
    winners = [r.candidate_id for r in results.values() if r.ratifiable]
    if not winners:
        return "NO_CONSENSUS_YET"
    # Still never auto-pick Raft among ties without GOV — design helper only lists
    non_raft = [w for w in winners if w != "C1"]
    if len(winners) == 1:
        return winners[0]
    if non_raft:
        return "NO_CONSENSUS_YET"  # ambiguous; require GOV, not vibe-pick
    return "NO_CONSENSUS_YET"


# --- Doc / capability gates ---


def test_version_held():
    assert __version__ == "0.18.0"


def test_axis_weights_sum_100():
    assert axis_weight_sum() == 100


def test_provisional_totals_match_design():
    expected = {"C0": 85, "C1": 68, "C2": 59, "C3": 62, "C4": 75}
    for cid, scores in PROVISIONAL_SCORES.items():
        r = evaluate_candidate(cid, scores)
        assert r.total == expected[cid], (cid, r.total, expected[cid])


def test_no_unlock_candidate_reaches_80():
    results = {
        cid: evaluate_candidate(cid, scores) for cid, scores in PROVISIONAL_SCORES.items()
    }
    for cid, r in results.items():
        if cid in UNLOCK_CANDIDATES:
            assert r.total < RATIFY_THRESHOLD
            assert not r.ratifiable
    assert unlock_verdict(results) == "NO_CONSENSUS_YET"


def test_c0_baseline_not_unlock_ratifiable():
    r = evaluate_candidate("C0", PROVISIONAL_SCORES["C0"])
    assert r.total >= RATIFY_THRESHOLD  # viable baseline
    assert not r.unlock_eligible
    assert not r.ratifiable  # cannot unlock N>2 via C0 alone


def test_raft_not_default_policy():
    assert rejects_raft_default(None)
    assert rejects_raft_default("C0")
    assert rejects_raft_default("NO_CONSENSUS_YET")
    assert not rejects_raft_default("C1")
    # helper must not treat C1 as silent default winner
    results = {
        cid: evaluate_candidate(cid, scores) for cid, scores in PROVISIONAL_SCORES.items()
    }
    assert unlock_verdict(results) != "C1"


def test_validate_rejects_overshoot():
    bad = dict(PROVISIONAL_SCORES["C1"])
    bad["safety"] = 99
    with pytest.raises(ValueError):
        total_score(bad)


def test_maturation_doc():
    path = REPO / "docs" / "design" / "fabric" / "M1_SCORECARD_MATURATION.md"
    assert path.is_file()
    text = path.read_text(encoding="utf-8")
    assert "NO_CONSENSUS_YET" in text
    assert "80" in text
    assert "no default" in text.lower() or "not default" in text.lower()
    assert "Raft" in text
    assert "NO_HELD" in text
    assert "CP-0054" in text
    assert "C1" in text and "C4" in text


def test_base_design_updated():
    path = REPO / "docs" / "design" / "fabric" / "M1_CONSENSUS_CHOICE_DESIGN.md"
    text = path.read_text(encoding="utf-8")
    assert "NO_CONSENSUS_YET" in text
    assert "CP-0054" in text
    assert "68" in text  # C1 provisional
    assert "no default" in text.lower() or "not default" in text.lower()


def test_capability():
    text = (
        REPO / "docs" / "capabilities" / "MESH_M1_SCORECARD_MATURATION.md"
    ).read_text(encoding="utf-8")
    assert "CP-0054" in text
    assert "NO_CONSENSUS_YET" in text
    assert "0.19_design_set_signoff" in text
    assert "NO_HELD" in text


def test_agreement():
    text = (REPO / "council" / "COUNCIL_AGREEMENT_CYCLE50.md").read_text(encoding="utf-8")
    assert "CP-0054" in text
    assert "M1" in text
    assert "NO_CONSENSUS_YET" in text


def test_no_runtime_claim():
    text = (
        REPO / "docs" / "design" / "fabric" / "M1_SCORECARD_MATURATION.md"
    ).read_text(encoding="utf-8").lower()
    assert "no runtime" in text or "not implement" in text
    assert "we unlocked raft" not in text
    assert "n>2 is live" not in text


def test_tags_untouched():
    assert (
        subprocess.run(
            ["git", "rev-parse", "--verify", "v0.18.0"],
            cwd=str(REPO),
            capture_output=True,
        ).returncode
        == 0
    )


def test_no_gia():
    text = (
        REPO / "docs" / "design" / "fabric" / "M1_SCORECARD_MATURATION.md"
    ).read_text(encoding="utf-8").lower()
    assert "we are gia" not in text
    assert "agi achieved" not in text
