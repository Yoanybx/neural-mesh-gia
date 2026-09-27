"""Tests for Cycle 59 / CP-0063: 0.19 design-set signoff v2 (post-C51 amendment).

Markers: design_set_signoff_v2_cycle59
Amends C51 A–D closeout with M2/M3/live-adapter/safety/L_judge×M2/agent_shell
extended. Package stays 0.18.0; no v0.19.0; no Raft/N>2/GIA/live/train/SaaS.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from neural_mesh import __version__
from neural_mesh.packaging.design_set_signoff_019_v2 import (
    BASELINE_CP_019D,
    CYCLE_019D_V2,
    DESIGN_CHANNEL,
    EXTENSION_CPS,
    EXTENSION_DOCS,
    PACKAGE_HELD,
    PREFERRED_NEXT_DEFAULT,
    PRIOR_CP_019D_V2,
    SEAL_CP_019D_V2,
    THEME_CPS_V2,
    THEME_DOCS_V2,
    THEME_LABELS_V2,
    run_019_design_set_signoff_v2,
)

pytestmark = [pytest.mark.design_set_signoff_v2_cycle59]

REPO = Path(__file__).resolve().parents[1]


def test_constants_019_design_v2():
    assert PACKAGE_HELD == "0.18.0"
    assert DESIGN_CHANNEL == "0.19.x-design"
    assert SEAL_CP_019D_V2 == "CP-0063"
    assert PRIOR_CP_019D_V2 == "CP-0062"
    assert BASELINE_CP_019D == "CP-0055"
    assert CYCLE_019D_V2 == 59
    assert PREFERRED_NEXT_DEFAULT == "await_deepseek"
    assert set(THEME_LABELS_V2) == {"A", "B", "C", "D", "E", "F", "G"}
    assert "CP-0055" in THEME_CPS_V2
    assert "CP-0062" in THEME_CPS_V2
    assert EXTENSION_CPS == (
        "CP-0057",
        "CP-0058",
        "CP-0059",
        "CP-0060",
        "CP-0061",
        "CP-0062",
    )
    assert len(THEME_DOCS_V2) >= 14
    assert len(EXTENSION_DOCS) >= 6


def test_version_held():
    assert __version__ == "0.18.0"


def test_theme_docs_v2_exist():
    for name, rel in THEME_DOCS_V2:
        assert (REPO / rel).is_file(), f"missing {name}: {rel}"


def test_extension_docs_exist():
    for name, rel in EXTENSION_DOCS:
        assert (REPO / rel).is_file(), f"missing ext {name}: {rel}"


def test_theme_cps_v2_sealed():
    for cp in THEME_CPS_V2:
        snap = REPO / "snapshots" / cp
        assert snap.is_dir(), cp
        data = json.loads((snap / "CHECKPOINT.json").read_text(encoding="utf-8"))
        assert str(data.get("status", "")).upper() == "VERIFIED", cp


def test_extension_cps_sealed():
    for cp in EXTENSION_CPS:
        data = json.loads(
            (REPO / "snapshots" / cp / "CHECKPOINT.json").read_text(encoding="utf-8")
        )
        assert str(data.get("status", "")).upper() == "VERIFIED", cp


def test_signoff_v2_pass(tmp_path: Path):
    out = tmp_path / "releases" / "0.19.x-design"
    result = run_019_design_set_signoff_v2(
        REPO,
        out_dir=out,
        tip="sg019v2",
        timestamp="2026-09-26T20:56:00Z",
        pytest_count=958,
        skip_pytest=True,
        write_project_state=False,
    )
    assert result.ok, result.errors
    assert result.version == "0.18.0"
    assert result.channel == DESIGN_CHANNEL
    assert result.cp == SEAL_CP_019D_V2
    assert result.prior_cp == PRIOR_CP_019D_V2
    assert result.baseline_cp == BASELINE_CP_019D
    assert result.dual_primary == 0
    path = Path(result.signoff_path)
    assert path.is_file()
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["ok"] is True
    assert data["schema"] == "mesh.release.design_set_signoff/v2"
    assert data["amendment"] == "v2"
    assert data["package_held"] == "0.18.0"
    assert data["package_open_0190"] is False
    assert data["themes"]["status"] == "CLOSED_V2"
    assert data["themes"]["baseline_status"] == "CLOSED"
    assert data["line_status"] == "CLOSED_FROZEN_DESIGN_SET_V2"
    assert data["m1_unlock"] == "NO_CONSENSUS_YET"
    assert data["preferred_next"] == PREFERRED_NEXT_DEFAULT
    assert data["live"] == "DISABLED"
    assert "CP-0062" in data["extension_cps"]
    assert (out / "CHECKLIST_V2.json").is_file()


def test_signoff_v2_force_fail_themes(tmp_path: Path):
    result = run_019_design_set_signoff_v2(
        REPO,
        out_dir=tmp_path / "bad",
        tip="bad",
        pytest_count=10,
        skip_pytest=True,
        force_fail="themes_a_g_present",
        write_project_state=False,
    )
    assert not result.ok
    assert any(g.name == "themes_a_g_present" and not g.ok for g in result.gates)


def test_signoff_v2_force_fail_version(tmp_path: Path):
    result = run_019_design_set_signoff_v2(
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


def test_signoff_v2_force_fail_gia(tmp_path: Path):
    result = run_019_design_set_signoff_v2(
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


def test_signoff_v2_force_fail_live(tmp_path: Path):
    result = run_019_design_set_signoff_v2(
        REPO,
        out_dir=tmp_path / "badlive",
        tip="badlive",
        pytest_count=10,
        skip_pytest=True,
        force_fail="live_disabled",
        write_project_state=False,
    )
    assert not result.ok
    assert any(g.name == "live_disabled" and not g.ok for g in result.gates)


def test_signoff_v2_force_fail_extension_cps(tmp_path: Path):
    result = run_019_design_set_signoff_v2(
        REPO,
        out_dir=tmp_path / "badext",
        tip="badext",
        pytest_count=10,
        skip_pytest=True,
        force_fail="extension_cps_verified",
        write_project_state=False,
    )
    assert not result.ok
    assert any(g.name == "extension_cps_verified" and not g.ok for g in result.gates)


def test_capability_doc_v2():
    text = (REPO / "docs" / "capabilities" / "MESH_0.19_DESIGN_SET_SIGNOFF.md").read_text(
        encoding="utf-8"
    )
    assert "CP-0063" in text
    assert "CP-0055" in text
    assert "CLOSED" in text
    assert "0.18.0" in text
    assert "NO_HELD" in text
    assert "await_deepseek" in text
    assert "v2" in text.lower() or "V2" in text


def test_planning_doc_v2():
    text = (REPO / "docs" / "planning" / "0.19_DESIGN_SET_SIGNOFF.md").read_text(encoding="utf-8")
    assert "CP-0063" in text
    assert "v2" in text.lower() or "V2" in text
    assert "M2" in text and "M3" in text
    assert "agent_shell" in text.lower() or "AGENT_SHELL" in text
    assert "NO_CONSENSUS_YET" in text
    assert "0.18.0" in text
    assert "await_deepseek" in text


def test_agreement_cycle59():
    text = (REPO / "council" / "COUNCIL_AGREEMENT_CYCLE59.md").read_text(encoding="utf-8")
    assert "CP-0063" in text
    assert "design" in text.lower()
    assert "v2" in text.lower() or "V2" in text


def test_paste_has_last_sealed():
    text = (REPO / "council" / "PASTE_CYCLE59_M2M.md").read_text(encoding="utf-8")
    assert "LAST_SEALED:" in text
    assert "CP-0062" in text
    assert "PREFERRED_NEXT: await_deepseek" in text
    assert "CP-0063" in text


def test_tags_untouched_no_v019():
    assert (
        subprocess.run(
            ["git", "rev-parse", "--verify", "v0.18.0"],
            cwd=str(REPO),
            capture_output=True,
        ).returncode
        == 0
    )
    rc = subprocess.run(
        ["git", "rev-parse", "--verify", "v0.19.0"],
        cwd=str(REPO),
        capture_output=True,
    ).returncode
    assert rc != 0


def test_no_gia_in_signoff_docs_v2():
    for rel in (
        "docs/planning/0.19_DESIGN_SET_SIGNOFF.md",
        "docs/capabilities/MESH_0.19_DESIGN_SET_SIGNOFF.md",
    ):
        t = (REPO / rel).read_text(encoding="utf-8").lower()
        assert "we are gia" not in t
        assert "agi achieved" not in t


def test_c51_helper_still_importable():
    from neural_mesh.packaging.design_set_signoff_019 import (
        SEAL_CP_019D,
        run_019_design_set_signoff,
    )

    assert SEAL_CP_019D == "CP-0055"
    assert callable(run_019_design_set_signoff)
