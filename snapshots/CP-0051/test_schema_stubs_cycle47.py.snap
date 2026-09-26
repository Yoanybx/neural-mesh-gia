"""Tests for Cycle 47 / CP-0051: L_judge + goal/continuity/shell schema stubs.

Markers: schema_stubs_cycle47
"""

from __future__ import annotations

from pathlib import Path

import pytest

from neural_mesh import __version__

pytestmark = [pytest.mark.schema_stubs_cycle47]

REPO = Path(__file__).resolve().parents[1]


def test_version_held():
    assert __version__ == "0.18.0"


def test_judge_schema_stub():
    text = (REPO / "docs" / "schema" / "judge" / "v0.md").read_text(encoding="utf-8")
    assert "mesh.judge.request/v0" in text
    assert "mesh.judge.response/v0" in text
    assert "mesh.judge.receipt/v0" in text
    assert "STUB" in text
    assert "NO_HELD" in text


def test_goal_schema_stub():
    text = (REPO / "docs" / "schema" / "goal" / "v0.md").read_text(encoding="utf-8")
    assert "mesh.goal/v0" in text
    assert "goal_id" in text
    assert "consciousness" in text.lower() or "NOT consciousness" in text


def test_continuity_schema_stub():
    text = (REPO / "docs" / "schema" / "continuity" / "v0.md").read_text(encoding="utf-8")
    assert "mesh.continuity/v0" in text
    assert "mesh.evidence/v0" in text
    assert "RUNNING" in text and "ABORTED" in text


def test_shell_schema_stub():
    text = (REPO / "docs" / "schema" / "shell" / "v0.md").read_text(encoding="utf-8")
    assert "mesh.shell.workload/v0" in text
    assert "settlement" in text.lower() or "economy" in text.lower()


def test_capability():
    text = (REPO / "docs" / "capabilities" / "MESH_L_JUDGE_SCHEMA_STUBS.md").read_text(encoding="utf-8")
    assert "CP-0051" in text
    assert "no runtime" in text.lower() or "no src" in text.lower()


def test_no_runtime_codec_modules():
    src = REPO / "src" / "neural_mesh"
    for name in ("judge_mix.py", "goal_registry.py", "shell_adapter.py"):
        assert not (src / name).is_file(), name


def test_designs_still_present():
    assert (REPO / "docs" / "design" / "L_JUDGE_MIX_DESIGN.md").is_file()
    assert (REPO / "docs" / "design" / "DURABLE_GOALS_CONTINUITY_DESIGN.md").is_file()


def test_agreement_cycle47():
    text = (REPO / "council" / "COUNCIL_AGREEMENT_CYCLE47.md").read_text(encoding="utf-8")
    assert "CP-0051" in text


def test_no_gia_claims():
    for rel in (
        "docs/schema/judge/v0.md",
        "docs/schema/goal/v0.md",
        "docs/capabilities/MESH_L_JUDGE_SCHEMA_STUBS.md",
    ):
        text = (REPO / rel).read_text(encoding="utf-8").lower()
        assert "we are gia" not in text
        assert "agi achieved" not in text
