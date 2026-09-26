"""Tests for Cycle 43 / CP-0047: 0.19 bootstrap plan (docs/design DRAFT).

Markers: bootstrap_plan_cycle43
Aim: ≥10 tests — planning docs, designs, NO_HELD, version held, tags untouched, no GIA.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from neural_mesh import __version__
from neural_mesh.packaging import RELEASE_VERSION

pytestmark = [pytest.mark.bootstrap_plan_cycle43]

REPO = Path(__file__).resolve().parents[1]

NO_HELD = (
    "Raft,N>2,multi-primary,ML,R2,R3,plaintext,Vault-ACME-req,GIA,"
    "SLO_chase,tag_schema,EVERY_fsync"
)


def test_package_version_held_0180():
    init = (REPO / "src" / "neural_mesh" / "__init__.py").read_text(encoding="utf-8")
    pyproject = (REPO / "pyproject.toml").read_text(encoding="utf-8")
    assert 'version = "0.18.0"' in pyproject
    assert '__version__ = "0.18.0"' in init
    assert __version__ == "0.18.0"
    assert RELEASE_VERSION == "0.16.3"


def test_bootstrap_plan_doc_present():
    path = REPO / "docs" / "planning" / "0.19_BOOTSTRAP.md"
    assert path.is_file()
    text = path.read_text(encoding="utf-8")
    assert "0.18.0" in text
    assert "DRAFT" in text or "PLAN" in text
    assert "not opened" in text.lower() or "HELD" in text or "held" in text
    assert "CP-0047" in text or "Cycle 43" in text
    assert "NO_HELD" in text or "no Raft" in text.lower()


def test_scope_draft_themes_abcd():
    path = REPO / "docs" / "planning" / "0.19_SCOPE_DRAFT.md"
    assert path.is_file()
    text = path.read_text(encoding="utf-8")
    assert "DRAFT" in text
    assert "FROZEN" in text  # mentions freeze deferred
    assert "L_judge" in text or "L_JUDGE" in text or "MIX" in text
    assert "durable" in text.lower() or "goal" in text.lower()
    assert "agent-shell" in text.lower() or "agent_shell" in text.lower() or "shell" in text.lower()
    assert "M1" in text and "M2" in text and "M3" in text
    assert "NO_HELD" in text
    # must not claim frozen status as current
    # DRAFT may later be SUPERSEDED by freeze (CP-0048+)
    assert (
        "**Status:** DRAFT" in text
        or "Status:** DRAFT" in text
        or "SUPERSEDED" in text
    )


def test_scope_not_frozen_file_absent_or_not_claimed():
    """CP-0047 shipped DRAFT-only; CP-0048+ may add FROZEN with DRAFT SUPERSEDED."""
    frozen = REPO / "docs" / "planning" / "0.19_SCOPE_FROZEN.md"
    draft = REPO / "docs" / "planning" / "0.19_SCOPE_DRAFT.md"
    assert draft.is_file()
    if frozen.is_file():
        assert "SUPERSEDED" in draft.read_text(encoding="utf-8")
        assert "FROZEN" in frozen.read_text(encoding="utf-8")


def test_non_goals_no_held():
    path = REPO / "docs" / "planning" / "0.19_NON_GOALS.md"
    assert path.is_file()
    text = path.read_text(encoding="utf-8")
    assert "NO_HELD" in text
    for item in NO_HELD.split(","):
        assert item in text, item
    assert "DO_NOT_TRAIN_70B_NOW" in text or "train" in text.lower()
    assert "SaaS" in text or "SAAS" in text
    assert "GIA" in text


def test_l_judge_mix_design_doc():
    path = REPO / "docs" / "design" / "L_JUDGE_MIX_DESIGN.md"
    assert path.is_file()
    text = path.read_text(encoding="utf-8")
    assert "JudgeRequest" in text
    assert "JudgeResponse" in text
    assert "JudgeReceipt" in text
    assert "dry_run" in text
    assert "I2" in text and "I6" in text
    assert "DO_NOT_TRAIN_70B_NOW" in text or "DO_NOT_TRAIN" in text
    assert "NO_HELD" in text
    assert "amnesia" in text.lower() or "ephemeral" in text.lower()
    low = text.lower()
    assert "we are gia" not in low
    assert "agi achieved" not in low


def test_durable_goals_continuity_design_doc():
    path = REPO / "docs" / "design" / "DURABLE_GOALS_CONTINUITY_DESIGN.md"
    assert path.is_file()
    text = path.read_text(encoding="utf-8")
    assert "GoalRecord" in text
    assert "EvidenceEntry" in text or "ledger" in text.lower()
    assert "ContinuityState" in text or "continuity" in text.lower()
    assert "substrate" in text.lower()
    assert "NOT" in text and "consciousness" in text.lower()
    assert "NO_HELD" in text
    assert "amnesia" in text.lower() or "session" in text.lower()


def test_capability_019_bootstrap_plan_doc():
    path = REPO / "docs" / "capabilities" / "MESH_0.19_BOOTSTRAP_PLAN.md"
    assert path.is_file()
    text = path.read_text(encoding="utf-8")
    assert "0.18.0" in text
    assert "CP-0047" in text
    assert "NO_HELD" in text
    assert "DRAFT" in text or "draft" in text
    assert "GIA" in text
    low = text.lower()
    assert "do not open package 0.19" in low or "not opened" in low or "held" in low


def test_council_scope_019_draft():
    path = REPO / "council" / "SCOPE_0.19_DRAFT.md"
    assert path.is_file()
    text = path.read_text(encoding="utf-8")
    assert "STATUS: DRAFT" in text
    assert "VER_PACKAGE: 0.18.0_HELD" in text or "0.18.0" in text
    assert "A_L_judge" in text or "L_judge" in text
    assert "NO_HELD" in text
    for token in ("Raft", "N>2", "GIA"):
        assert token in text


def test_hyperbrain_astra_agreement_locked():
    path = REPO / "council" / "COUNCIL_AGREEMENT_HYPERBRAIN_ASTRA.md"
    assert path.is_file()
    text = path.read_text(encoding="utf-8")
    assert "LOCKED" in text
    assert "0.19_bootstrap_plan" in text
    assert "substrate memory" in text.lower() or "Durable goal" in text
    assert "DO_NOT_TRAIN_70B_NOW" in text or "train-70B" in text.lower()


def test_prior_018_release_and_tags_untouched():
    assert (REPO / "dist" / "releases" / "0.18.0").is_dir()
    assert (REPO / "dist" / "releases" / "0.17.0").is_dir()
    assert (REPO / "dist" / "releases" / "0.16.3").is_dir()
    for tag in ("v0.18.0", "v0.17.0", "v0.16.3"):
        r = subprocess.run(
            ["git", "rev-parse", "--verify", tag],
            cwd=str(REPO),
            capture_output=True,
            text=True,
            check=False,
        )
        assert r.returncode == 0, f"missing tag {tag}: {r.stderr}"
    show = subprocess.run(
        ["git", "show", "v0.18.0:src/neural_mesh/__init__.py"],
        cwd=str(REPO),
        capture_output=True,
        text=True,
        check=False,
    )
    assert show.returncode == 0
    assert '__version__ = "0.18.0"' in show.stdout


def test_no_gia_claims_in_019_planning():
    for rel in (
        "docs/planning/0.19_BOOTSTRAP.md",
        "docs/planning/0.19_SCOPE_DRAFT.md",
        "docs/planning/0.19_NON_GOALS.md",
        "docs/capabilities/MESH_0.19_BOOTSTRAP_PLAN.md",
        "docs/design/L_JUDGE_MIX_DESIGN.md",
        "docs/design/DURABLE_GOALS_CONTINUITY_DESIGN.md",
    ):
        text = (REPO / rel).read_text(encoding="utf-8").lower()
        assert "we are gia" not in text
        assert "agi achieved" not in text
        assert "consciousness proven" not in text
        if "hyperbrain achieved" in text:
            assert (
                "not claim" in text
                or "do not claim" in text
                or "no gia" in text
                or "non-goal" in text
                or "forbidden" in text
            )
        if "gia" in text:
            assert (
                "no gia" in text
                or "gia," in text
                or "gia/" in text
                or "held" in text
                or "non-goal" in text
                or "no_held" in text
                or "l_gia" in text
            )


def test_council_agreement_cycle43_present():
    path = REPO / "council" / "COUNCIL_AGREEMENT_CYCLE43.md"
    assert path.is_file()
    text = path.read_text(encoding="utf-8")
    assert "CP-0047" in text
    assert "0.19" in text
    assert "DRAFT" in text
    assert "PREFERRED_NEXT=`0.19_scope_freeze`" in text or "0.19_scope_freeze" in text
