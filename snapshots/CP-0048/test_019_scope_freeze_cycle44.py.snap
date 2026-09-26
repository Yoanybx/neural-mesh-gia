"""Tests for Cycle 44 / CP-0048: 0.19 scope freeze (A–D).

Markers: scope_freeze_cycle44
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from neural_mesh import __version__

pytestmark = [pytest.mark.scope_freeze_cycle44]

REPO = Path(__file__).resolve().parents[1]

NO_HELD = (
    "Raft,N>2,multi-primary,ML,R2,R3,plaintext,Vault-ACME-req,GIA,"
    "SLO_chase,tag_schema,EVERY_fsync"
)


def test_version_still_0180():
    assert __version__ == "0.18.0"
    assert 'version = "0.18.0"' in (REPO / "pyproject.toml").read_text(encoding="utf-8")


def test_scope_frozen_abcd():
    path = REPO / "docs" / "planning" / "0.19_SCOPE_FROZEN.md"
    assert path.is_file()
    text = path.read_text(encoding="utf-8")
    assert "**Status:** FROZEN" in text or "Status:** FROZEN" in text
    assert "L_judge" in text or "MIX" in text
    assert "Durable goal" in text or "durable" in text.lower()
    assert "Agent-shell" in text or "agent-shell" in text.lower()
    assert "M1" in text and "M2" in text and "M3" in text
    assert "NO_HELD" in text
    assert "agent_shell_adapter_spike_plan" in text


def test_draft_superseded():
    text = (REPO / "docs" / "planning" / "0.19_SCOPE_DRAFT.md").read_text(encoding="utf-8")
    assert "SUPERSEDED" in text
    assert "0.19_SCOPE_FROZEN" in text


def test_council_frozen():
    path = REPO / "council" / "SCOPE_0.19_FROZEN.md"
    assert path.is_file()
    text = path.read_text(encoding="utf-8")
    assert "STATUS: FROZEN" in text
    assert "A_L_judge" in text
    assert "C_agent_shell" in text
    assert "NO_HELD" in text
    for item in ("Raft", "N>2", "GIA"):
        assert item in text


def test_non_goals_still_hold():
    text = (REPO / "docs" / "planning" / "0.19_NON_GOALS.md").read_text(encoding="utf-8")
    for item in NO_HELD.split(","):
        assert item in text, item


def test_designs_ab_present():
    assert (REPO / "docs" / "design" / "L_JUDGE_MIX_DESIGN.md").is_file()
    assert (REPO / "docs" / "design" / "DURABLE_GOALS_CONTINUITY_DESIGN.md").is_file()


def test_capability_freeze_doc():
    path = REPO / "docs" / "capabilities" / "MESH_0.19_SCOPE_FREEZE.md"
    assert path.is_file()
    text = path.read_text(encoding="utf-8")
    assert "CP-0048" in text
    assert "agent_shell_adapter_spike_plan" in text
    assert "NO_HELD" in text


def test_agreement_cycle44():
    text = (REPO / "council" / "COUNCIL_AGREEMENT_CYCLE44.md").read_text(encoding="utf-8")
    assert "CP-0048" in text
    assert "0.19_scope_freeze" in text
    assert "agent_shell_adapter_spike_plan" in text


def test_tags_untouched():
    for tag in ("v0.18.0", "v0.17.0", "v0.16.3"):
        r = subprocess.run(
            ["git", "rev-parse", "--verify", tag],
            cwd=str(REPO),
            capture_output=True,
            text=True,
            check=False,
        )
        assert r.returncode == 0, tag


def test_no_gia_claims():
    for rel in (
        "docs/planning/0.19_SCOPE_FROZEN.md",
        "docs/capabilities/MESH_0.19_SCOPE_FREEZE.md",
        "council/SCOPE_0.19_FROZEN.md",
    ):
        text = (REPO / rel).read_text(encoding="utf-8").lower()
        assert "we are gia" not in text
        assert "agi achieved" not in text
