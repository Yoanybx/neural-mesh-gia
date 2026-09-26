"""Tests for Cycle 46 / CP-0050: M1 consensus choice design + M2/M3 pointers.

Markers: m1_design_cycle46
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from neural_mesh import __version__

pytestmark = [pytest.mark.m1_design_cycle46]

REPO = Path(__file__).resolve().parents[1]


def test_version_held():
    assert __version__ == "0.18.0"


def test_m1_scorecard_no_raft_default():
    path = REPO / "docs" / "design" / "fabric" / "M1_CONSENSUS_CHOICE_DESIGN.md"
    assert path.is_file()
    text = path.read_text(encoding="utf-8")
    assert "80" in text
    assert "no default" in text.lower() or "no default = Raft" in text or "not default" in text.lower()
    assert "Raft" in text
    assert "NO_HELD" in text
    assert "Scorecard" in text or "scorecard" in text
    assert "C0" in text and "C1" in text


def test_m2_pointer():
    path = REPO / "docs" / "design" / "fabric" / "M2_MEMBERSHIP_REJOIN_POINTER.md"
    assert path.is_file()
    text = path.read_text(encoding="utf-8")
    assert "JOINING" in text and "REJOIN" in text
    assert "NO_HELD" in text


def test_m3_pointer_hlc():
    path = REPO / "docs" / "design" / "fabric" / "M3_WAN_PARTITION_HLC_POINTER.md"
    assert path.is_file()
    text = path.read_text(encoding="utf-8")
    assert "HLC" in text
    assert "NO_HELD" in text


def test_capability():
    text = (REPO / "docs" / "capabilities" / "MESH_M1_CONSENSUS_CHOICE_DESIGN.md").read_text(encoding="utf-8")
    assert "CP-0050" in text
    assert "L_judge_schema_stubs" in text
    assert "NO_HELD" in text


def test_agreement():
    text = (REPO / "council" / "COUNCIL_AGREEMENT_CYCLE46.md").read_text(encoding="utf-8")
    assert "CP-0050" in text
    assert "M1" in text


def test_frozen_theme_d():
    text = (REPO / "docs" / "planning" / "0.19_SCOPE_FROZEN.md").read_text(encoding="utf-8")
    assert "M1" in text and "M3" in text


def test_no_runtime_claim():
    text = (REPO / "docs" / "design" / "fabric" / "M1_CONSENSUS_CHOICE_DESIGN.md").read_text(encoding="utf-8").lower()
    assert "no runtime" in text or "not implement" in text or "design" in text
    assert "we unlocked raft" not in text
    assert "n>2 is live" not in text


def test_tags_untouched():
    assert subprocess.run(["git", "rev-parse", "--verify", "v0.18.0"], cwd=str(REPO), capture_output=True).returncode == 0


def test_no_gia():
    text = (REPO / "docs" / "design" / "fabric" / "M1_CONSENSUS_CHOICE_DESIGN.md").read_text(encoding="utf-8").lower()
    assert "we are gia" not in text
    assert "agi achieved" not in text
