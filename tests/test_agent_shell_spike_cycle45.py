"""Tests for Cycle 45 / CP-0049: agent-shell adapter spike plan.

Markers: shell_spike_cycle45
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from neural_mesh import __version__

pytestmark = [pytest.mark.shell_spike_cycle45]

REPO = Path(__file__).resolve().parents[1]


def test_version_held():
    assert __version__ == "0.18.0"


def test_spike_doc_shapes_and_boundary():
    path = REPO / "docs" / "design" / "AGENT_SHELL_ADAPTER_SPIKE.md"
    assert path.is_file()
    text = path.read_text(encoding="utf-8")
    assert "ShellWorkload" in text
    assert "NormalizedEvent" in text
    assert "ShellReceipt" in text
    assert "ShellReport" in text
    assert "safety probes" in text.lower() or "Safety probes" in text
    assert "Mesh" in text and "policy" in text.lower()
    assert "second policy" in text.lower() or "not a second" in text.lower()
    assert "NO_HELD" in text
    assert "settlement" in text.lower() or "economy" in text.lower()


def test_capability_doc():
    path = REPO / "docs" / "capabilities" / "MESH_AGENT_SHELL_SPIKE_PLAN.md"
    assert path.is_file()
    text = path.read_text(encoding="utf-8")
    assert "CP-0049" in text
    assert "M1_consensus_choice_design" in text
    assert "NO_HELD" in text


def test_agreement_cycle45():
    text = (REPO / "council" / "COUNCIL_AGREEMENT_CYCLE45.md").read_text(encoding="utf-8")
    assert "CP-0049" in text
    assert "agent_shell" in text.lower() or "agent-shell" in text.lower()


def test_frozen_scope_lists_theme_c():
    text = (REPO / "docs" / "planning" / "0.19_SCOPE_FROZEN.md").read_text(encoding="utf-8")
    assert "Agent-shell" in text or "agent-shell" in text.lower()
    assert "FROZEN" in text


def test_no_economy_rails_claimed():
    text = (REPO / "docs" / "design" / "AGENT_SHELL_ADAPTER_SPIKE.md").read_text(encoding="utf-8").lower()
    assert "settlement" in text
    assert "parked" in text or "non-goal" in text or "out of spike" in text


def test_links_l_judge_and_goals():
    text = (REPO / "docs" / "design" / "AGENT_SHELL_ADAPTER_SPIKE.md").read_text(encoding="utf-8")
    assert "L_JUDGE_MIX_DESIGN" in text
    assert "DURABLE_GOALS_CONTINUITY_DESIGN" in text


def test_tags_untouched():
    r = subprocess.run(
        ["git", "rev-parse", "--verify", "v0.18.0"],
        cwd=str(REPO), capture_output=True, text=True, check=False,
    )
    assert r.returncode == 0


def test_no_gia_claims():
    text = (REPO / "docs" / "design" / "AGENT_SHELL_ADAPTER_SPIKE.md").read_text(encoding="utf-8").lower()
    assert "we are gia" not in text
    assert "agi achieved" not in text


def test_hyperbrain_ranked_shell():
    text = (REPO / "council" / "COUNCIL_AGREEMENT_HYPERBRAIN_ASTRA.md").read_text(encoding="utf-8")
    assert "agent-shell" in text.lower()
