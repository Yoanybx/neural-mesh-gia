"""Tests for Cycle 66 / CP-0070: orchestrator design-set signoff.

Markers: orchestrator_design_set_signoff_cycle66
Formal ledger close for CP-0064..CP-0069 (routing/continuity/oversight/spikes/
perf/safety). Analogous to 0.19 design-set signoff_v2. Package stays 0.18.0;
pkg0190 NOT_OPENED; no v0.19.0; live=DISABLED; M1=NO_CONSENSUS_YET;
MESH_PERF_EXPERIMENTAL=OFF; no Raft/N>2/GIA/train/SaaS.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from neural_mesh import __version__
from neural_mesh.packaging.orchestrator_design_set_signoff import (
    BASELINE_SIGNOFF_CP,
    CONTRACT_CPS,
    CYCLE,
    DESIGN_CHANNEL,
    PACKAGE_HELD,
    PREFERRED_NEXT_DEFAULT,
    PRIOR_CP,
    SEAL_CP,
    SUPPORTING_CPS,
    THEME_CPS,
    THEME_DOCS,
    THEME_LABELS,
    run_orchestrator_design_set_signoff,
)

pytestmark = [pytest.mark.orchestrator_design_set_signoff_cycle66]

REPO = Path(__file__).resolve().parents[1]


def test_constants_orchestrator_design_signoff():
    assert PACKAGE_HELD == "0.18.0"
    assert DESIGN_CHANNEL == "orchestrator-design"
    assert SEAL_CP == "CP-0070"
    assert PRIOR_CP == "CP-0069"
    assert BASELINE_SIGNOFF_CP == "CP-0063"
    assert CYCLE == 66
    assert PREFERRED_NEXT_DEFAULT == "await_deepseek"
    assert set(THEME_LABELS) == {"A", "B", "C", "D", "E", "F"}
    assert CONTRACT_CPS == (
        "CP-0064",
        "CP-0065",
        "CP-0066",
        "CP-0067",
        "CP-0068",
        "CP-0069",
    )
    assert SUPPORTING_CPS == ("CP-0058", "CP-0061")
    assert "CP-0064" in THEME_CPS and "CP-0069" in THEME_CPS
    assert "CP-0058" in THEME_CPS and "CP-0061" in THEME_CPS
    assert len(THEME_DOCS) >= 12


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


def test_contract_cps_sealed():
    for cp in CONTRACT_CPS:
        data = json.loads(
            (REPO / "snapshots" / cp / "CHECKPOINT.json").read_text(encoding="utf-8")
        )
        assert str(data.get("status", "")).upper() == "VERIFIED", cp


def test_supporting_cps_sealed():
    for cp in SUPPORTING_CPS:
        data = json.loads(
            (REPO / "snapshots" / cp / "CHECKPOINT.json").read_text(encoding="utf-8")
        )
        assert str(data.get("status", "")).upper() == "VERIFIED", cp


def test_signoff_pass(tmp_path: Path):
    out = tmp_path / "releases" / "orchestrator-design"
    result = run_orchestrator_design_set_signoff(
        REPO,
        out_dir=out,
        tip="orch0070",
        timestamp="2026-09-27T01:50:00Z",
        pytest_count=1075,
        skip_pytest=True,
        write_project_state=False,
    )
    assert result.ok, result.errors
    assert result.version == "0.18.0"
    assert result.channel == DESIGN_CHANNEL
    assert result.cp == SEAL_CP
    assert result.prior_cp == PRIOR_CP
    assert result.baseline_signoff_cp == BASELINE_SIGNOFF_CP
    assert result.dual_primary == 0
    path = Path(result.signoff_path)
    assert path.is_file()
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["ok"] is True
    assert data["schema"] == "mesh.release.orchestrator_design_set_signoff/v1"
    assert data["package_held"] == "0.18.0"
    assert data["package_open_0190"] is False
    assert data["themes"]["status"] == "CLOSED"
    assert data["line_status"] == "CLOSED_ORCHESTRATOR_DESIGN_SET"
    assert data["m1_unlock"] == "NO_CONSENSUS_YET"
    assert data["preferred_next"] == PREFERRED_NEXT_DEFAULT
    assert data["live"] == "DISABLED"
    assert data["mesh_perf_experimental"] == "OFF"
    assert data["contract_cps"] == list(CONTRACT_CPS)
    assert "CP-0069" in data["contract_cps"]
    assert "CP-0058" in data["supporting_cps"]
    assert (out / "CHECKLIST.json").is_file()


def test_signoff_force_fail_themes(tmp_path: Path):
    result = run_orchestrator_design_set_signoff(
        REPO,
        out_dir=tmp_path / "bad",
        tip="bad",
        pytest_count=10,
        skip_pytest=True,
        force_fail="themes_a_f_present",
        write_project_state=False,
    )
    assert not result.ok
    assert any(g.name == "themes_a_f_present" and not g.ok for g in result.gates)


def test_signoff_force_fail_version(tmp_path: Path):
    result = run_orchestrator_design_set_signoff(
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
    result = run_orchestrator_design_set_signoff(
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


def test_signoff_force_fail_live(tmp_path: Path):
    result = run_orchestrator_design_set_signoff(
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


def test_signoff_force_fail_experimental(tmp_path: Path):
    result = run_orchestrator_design_set_signoff(
        REPO,
        out_dir=tmp_path / "badexp",
        tip="badexp",
        pytest_count=10,
        skip_pytest=True,
        force_fail="mesh_perf_experimental_off",
        write_project_state=False,
    )
    assert not result.ok
    assert any(g.name == "mesh_perf_experimental_off" and not g.ok for g in result.gates)


def test_signoff_force_fail_contract_cps(tmp_path: Path):
    result = run_orchestrator_design_set_signoff(
        REPO,
        out_dir=tmp_path / "badext",
        tip="badext",
        pytest_count=10,
        skip_pytest=True,
        force_fail="contract_cps_verified",
        write_project_state=False,
    )
    assert not result.ok
    assert any(g.name == "contract_cps_verified" and not g.ok for g in result.gates)


def test_capability_doc():
    text = (
        REPO / "docs" / "capabilities" / "MESH_ORCHESTRATOR_DESIGN_SET_SIGNOFF.md"
    ).read_text(encoding="utf-8")
    assert "CP-0070" in text
    assert "CP-0064" in text
    assert "CLOSED" in text
    assert "0.18.0" in text
    assert "NO_HELD" in text
    assert "await_deepseek" in text
    assert "MESH_PERF_EXPERIMENTAL" in text
    assert "NOT_OPENED" in text or "not opened" in text.lower()


def test_planning_doc():
    text = (REPO / "docs" / "planning" / "ORCHESTRATOR_DESIGN_SET_SIGNOFF.md").read_text(
        encoding="utf-8"
    )
    assert "CP-0070" in text
    assert "CP-0064" in text and "CP-0069" in text
    assert "routing" in text.lower()
    assert "continuity" in text.lower()
    assert "oversight" in text.lower()
    assert "NO_CONSENSUS_YET" in text
    assert "0.18.0" in text
    assert "await_deepseek" in text
    assert "MESH_PERF_EXPERIMENTAL" in text
    assert "CP-0063" in text


def test_agreement_cycle66():
    text = (REPO / "council" / "COUNCIL_AGREEMENT_CYCLE66.md").read_text(encoding="utf-8")
    assert "CP-0070" in text
    assert "orchestrator" in text.lower()
    assert "signoff" in text.lower()


def test_paste_has_last_sealed():
    text = (REPO / "council" / "PASTE_CYCLE66_M2M.md").read_text(encoding="utf-8")
    assert "LAST_SEALED:" in text
    assert "CP-0069" in text
    assert "PREFERRED_NEXT: await_deepseek" in text
    assert "CP-0070" in text
    assert "2a5312c" in text


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


def test_no_gia_in_signoff_docs():
    for rel in (
        "docs/planning/ORCHESTRATOR_DESIGN_SET_SIGNOFF.md",
        "docs/capabilities/MESH_ORCHESTRATOR_DESIGN_SET_SIGNOFF.md",
    ):
        t = (REPO / rel).read_text(encoding="utf-8").lower()
        assert "we are gia" not in t
        assert "agi achieved" not in t


def test_019_v2_helper_still_importable():
    from neural_mesh.packaging.design_set_signoff_019_v2 import (
        SEAL_CP_019D_V2,
        run_019_design_set_signoff_v2,
    )

    assert SEAL_CP_019D_V2 == "CP-0063"
    assert callable(run_019_design_set_signoff_v2)


def test_experimental_flag_default_off(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    monkeypatch.delenv("MESH_PERF_EXPERIMENTAL", raising=False)
    result = run_orchestrator_design_set_signoff(
        REPO,
        out_dir=tmp_path / "expoff",
        tip="expoff",
        pytest_count=10,
        skip_pytest=True,
        write_project_state=False,
    )
    assert result.ok, result.errors
    assert any(g.name == "mesh_perf_experimental_off" and g.ok for g in result.gates)
