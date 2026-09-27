"""Tests for Cycle 51 / CP-0055: 0.19 design-set signoff (A–D).

Markers: design_set_signoff_cycle51
Design-track closeout only — package stays 0.18.0; no v0.19.0; no Raft/N>2/GIA.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from neural_mesh import __version__
from neural_mesh.packaging.design_set_signoff_019 import (
    CYCLE_019D,
    DESIGN_CHANNEL,
    PACKAGE_HELD,
    PREFERRED_NEXT_DEFAULT,
    PRIOR_CP_019D,
    SEAL_CP_019D,
    THEME_CPS,
    THEME_DOCS,
    THEME_LABELS,
    run_019_design_set_signoff,
)

pytestmark = [pytest.mark.design_set_signoff_cycle51]

REPO = Path(__file__).resolve().parents[1]


def test_constants_019_design_channel():
    assert PACKAGE_HELD == "0.18.0"
    assert DESIGN_CHANNEL == "0.19.x-design"
    assert SEAL_CP_019D == "CP-0055"
    assert PRIOR_CP_019D == "CP-0054"
    assert CYCLE_019D == 51
    assert PREFERRED_NEXT_DEFAULT == "await_deepseek_design_signoff"
    assert set(THEME_LABELS) == {"A", "B", "C", "D"}
    assert "CP-0048" in THEME_CPS and "CP-0054" in THEME_CPS
    assert len(THEME_DOCS) >= 8


def test_version_held():
    assert __version__ == "0.18.0"


def test_theme_docs_exist():
    for name, rel in THEME_DOCS:
        assert (REPO / rel).is_file(), f"missing {name}: {rel}"


def test_theme_cps_sealed():
    for cp in THEME_CPS:
        snap = REPO / "snapshots" / cp
        assert snap.is_dir(), cp
        data = json.loads((snap / "CHECKPOINT.json").read_text(encoding="utf-8"))
        assert str(data.get("status", "")).upper() == "VERIFIED", cp


def test_signoff_pass(tmp_path: Path):
    out = tmp_path / "releases" / "0.19.x-design"
    result = run_019_design_set_signoff(
        REPO,
        out_dir=out,
        tip="sg019d",
        timestamp="2026-09-26T20:20:00Z",
        pytest_count=830,
        skip_pytest=True,
        write_project_state=False,
    )
    assert result.ok, result.errors
    assert result.version == "0.18.0"
    assert result.channel == DESIGN_CHANNEL
    assert result.cp == SEAL_CP_019D
    assert result.prior_cp == PRIOR_CP_019D
    assert result.dual_primary == 0
    path = Path(result.signoff_path)
    assert path.is_file()
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["ok"] is True
    assert data["package_held"] == "0.18.0"
    assert data["package_open_0190"] is False
    assert data["themes"]["status"] == "CLOSED"
    assert data["line_status"] == "CLOSED_FROZEN_DESIGN_SET"
    assert data["m1_unlock"] == "NO_CONSENSUS_YET"
    assert data["preferred_next"] == PREFERRED_NEXT_DEFAULT
    assert (out / "CHECKLIST.json").is_file()


def test_signoff_force_fail_themes(tmp_path: Path):
    result = run_019_design_set_signoff(
        REPO,
        out_dir=tmp_path / "bad",
        tip="bad",
        pytest_count=10,
        skip_pytest=True,
        force_fail="themes_a_d_present",
        write_project_state=False,
    )
    assert not result.ok
    assert any(g.name == "themes_a_d_present" and not g.ok for g in result.gates)


def test_signoff_force_fail_version(tmp_path: Path):
    result = run_019_design_set_signoff(
        REPO,
        out_dir=tmp_path / "badver",
        tip="badver",
        pytest_count=10,
        skip_pytest=True,
        force_fail="version_held",
        write_project_state=False,
    )
    assert not result.ok
    assert any(g.name == "version_held" and not g.ok for g in result.gates)


def test_signoff_force_fail_gia(tmp_path: Path):
    result = run_019_design_set_signoff(
        REPO,
        out_dir=tmp_path / "badgia",
        tip="badgia",
        pytest_count=10,
        skip_pytest=True,
        force_fail="no_gia_claim",
        write_project_state=False,
    )
    assert not result.ok
    assert any(g.name == "no_gia_claim" and not g.ok for g in result.gates)


def test_signoff_force_fail_m1(tmp_path: Path):
    result = run_019_design_set_signoff(
        REPO,
        out_dir=tmp_path / "badm1",
        tip="badm1",
        pytest_count=10,
        skip_pytest=True,
        force_fail="m1_no_consensus",
        write_project_state=False,
    )
    assert not result.ok
    assert any(g.name == "m1_no_consensus" and not g.ok for g in result.gates)


def test_capability_doc():
    text = (REPO / "docs" / "capabilities" / "MESH_0.19_DESIGN_SET_SIGNOFF.md").read_text(
        encoding="utf-8"
    )
    assert "CP-0055" in text
    assert "CLOSED" in text
    assert "0.18.0" in text
    assert "NO_HELD" in text
    assert "await_deepseek_design_signoff" in text


def test_planning_doc():
    text = (REPO / "docs" / "planning" / "0.19_DESIGN_SET_SIGNOFF.md").read_text(encoding="utf-8")
    assert "A" in text and "D" in text
    assert "NO_CONSENSUS_YET" in text
    assert "package" in text.lower()


def test_agreement():
    text = (REPO / "council" / "COUNCIL_AGREEMENT_CYCLE51.md").read_text(encoding="utf-8")
    assert "CP-0055" in text
    assert "design" in text.lower()


def test_tags_untouched():
    assert (
        subprocess.run(
            ["git", "rev-parse", "--verify", "v0.18.0"],
            cwd=str(REPO),
            capture_output=True,
        ).returncode
        == 0
    )
    # must NOT require v0.19.0
    rc = subprocess.run(
        ["git", "rev-parse", "--verify", "v0.19.0"],
        cwd=str(REPO),
        capture_output=True,
    ).returncode
    assert rc != 0


def test_no_gia_in_signoff_docs():
    for rel in (
        "docs/planning/0.19_DESIGN_SET_SIGNOFF.md",
        "docs/capabilities/MESH_0.19_DESIGN_SET_SIGNOFF.md",
    ):
        t = (REPO / rel).read_text(encoding="utf-8").lower()
        assert "we are gia" not in t
        assert "agi achieved" not in t
