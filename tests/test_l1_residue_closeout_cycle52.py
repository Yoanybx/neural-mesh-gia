"""Tests for Cycle 52 / CP-0056: L1 residue closeout (R1/R2/R3).

Markers: l1_residue_closeout_cycle52
Closeout only — package stays 0.18.0; no GIA; NO_HELD product R2/R3 stay locked.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from neural_mesh import __version__
from neural_mesh.packaging.l1_residue_closeout import (
    CYCLE,
    EVIDENCE_CPS,
    EVIDENCE_DOCS,
    PACKAGE_HELD,
    PREFERRED_NEXT_DEFAULT,
    PRIOR_CP,
    SEAL_CP,
    THEME_LABELS,
    run_l1_residue_closeout,
)

pytestmark = [pytest.mark.l1_residue_closeout_cycle52]

REPO = Path(__file__).resolve().parents[1]


def test_constants_l1_residue():
    assert PACKAGE_HELD == "0.18.0"
    assert SEAL_CP == "CP-0056"
    assert PRIOR_CP == "CP-0055"
    assert CYCLE == 52
    assert PREFERRED_NEXT_DEFAULT == "L_judge_live_adapter_design"
    assert set(THEME_LABELS) >= {"R1", "R2", "R3", "R4", "R5", "R6", "R7"}
    assert "CP-0033" in EVIDENCE_CPS and "CP-0036" in EVIDENCE_CPS
    assert len(EVIDENCE_DOCS) >= 14


def test_version_held():
    assert __version__ == "0.18.0"


def test_evidence_docs_exist():
    for name, rel in EVIDENCE_DOCS:
        assert (REPO / rel).is_file(), f"missing {name}: {rel}"


def test_evidence_cps_sealed():
    for cp in EVIDENCE_CPS:
        snap = REPO / "snapshots" / cp
        assert snap.is_dir(), cp
        data = json.loads((snap / "CHECKPOINT.json").read_text(encoding="utf-8"))
        assert str(data.get("status", "")).upper() == "VERIFIED", cp


def test_blueprint_l1_closed():
    text = (REPO / "council" / "blueprint" / "FINAL_BLUEPRINT_ROOT.md").read_text(
        encoding="utf-8"
    )
    assert "L1 REMAINING_0.17 [CLOSED]" in text
    assert "L1 REMAINING_0.17 [OPEN]" not in text


def test_closeout_doc_closed():
    text = (REPO / "docs" / "planning" / "L1_RESIDUE_CLOSEOUT.md").read_text(
        encoding="utf-8"
    )
    assert "**Status:** CLOSED" in text
    assert "ML-router" in text
    assert "e1d5e50" in text and "64747b9" in text and "e6a0964" in text


def test_ops_docs_and_quickstart_alias():
    assert (REPO / "docs" / "ops" / "obs-peers-v1.md").is_file()
    assert (REPO / "docs" / "ops" / "fabric-ops-ux-v1.md").is_file()
    alias = REPO / "scripts" / "quickstart.sh"
    assert alias.is_file()
    body = alias.read_text(encoding="utf-8")
    assert "quickstart_0.16.3.sh" in body


def test_closeout_pass(tmp_path: Path):
    out = tmp_path / "releases" / "l1-residue"
    result = run_l1_residue_closeout(
        REPO,
        out_dir=out,
        tip="l1c52",
        timestamp="2026-09-26T20:40:00Z",
        pytest_count=844,
        skip_pytest=True,
        write_project_state=False,
    )
    assert result.ok, result.errors
    assert result.version == "0.18.0"
    assert result.cp == SEAL_CP
    assert result.l1_status == "CLOSED"
    assert result.dual_primary == 0
    path = Path(result.closeout_path)
    assert path.is_file()
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["ok"] is True
    assert data["l1_status"] == "CLOSED"
    assert data["package_held"] == "0.18.0"
    assert data["package_open_0190"] is False
    assert data["themes"]["status"] == "CLOSED"
    assert data["preferred_next"] == PREFERRED_NEXT_DEFAULT
    assert (out / "CHECKLIST.json").is_file()


def test_closeout_force_fail_docs(tmp_path: Path):
    result = run_l1_residue_closeout(
        REPO,
        out_dir=tmp_path / "bad",
        tip="bad",
        pytest_count=10,
        skip_pytest=True,
        force_fail="evidence_docs_present",
        write_project_state=False,
    )
    assert not result.ok
    assert result.l1_status == "PARTIAL"
    assert any(g.name == "evidence_docs_present" and not g.ok for g in result.gates)


def test_closeout_force_fail_blueprint(tmp_path: Path):
    result = run_l1_residue_closeout(
        REPO,
        out_dir=tmp_path / "bad2",
        tip="bad2",
        pytest_count=10,
        skip_pytest=True,
        force_fail="blueprint_l1_closed",
        write_project_state=False,
    )
    assert not result.ok
    assert any(g.name == "blueprint_l1_closed" and not g.ok for g in result.gates)


def test_no_held_product_layers_not_unlocked():
    text = (REPO / "docs" / "planning" / "L1_RESIDUE_CLOSEOUT.md").read_text(
        encoding="utf-8"
    )
    assert "NO_HELD" in text
    assert "ML-router" in text
    assert "Do **not** unlock NO_HELD product R2/R3" in text
    assert "product R2/R3 unlocked" not in text.lower()


def test_r1_r2_r3_prior_tests_still_collectable():
    """Prior cycle markers remain registered and files present."""
    for rel in (
        "tests/test_fabric_ops_cycle29.py",
        "tests/test_obs_peers_cycle30.py",
        "tests/test_quickstart_cycle31.py",
    ):
        assert (REPO / rel).is_file()


def test_capability_doc_present():
    p = REPO / "docs" / "capabilities" / "MESH_L1_RESIDUE_CLOSEOUT.md"
    assert p.is_file()
    text = p.read_text(encoding="utf-8")
    assert "MESH_L1_RESIDUE_CLOSEOUT" in text
    assert "CP-0056" in text


def test_pyproject_marker_registered():
    text = (REPO / "pyproject.toml").read_text(encoding="utf-8")
    assert "l1_residue_closeout_cycle52" in text
