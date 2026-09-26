"""Tests for Cycle 42 / CP-0046: 0.18 H1..H8 theme-set signoff closeout.

Markers: signoff_cycle42
Aim: ≥10 tests — signoff gates, archive, monitor, docs, no prior reopen, no GIA claims.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from neural_mesh.packaging.theme_signoff_018 import (
    CYCLE_018,
    PREFERRED_NEXT_DEFAULT,
    PRIOR_CP_018,
    SEAL_CP_018,
    THEME_CPS,
    THEME_DOCS,
    THEME_FREEZE,
    THEME_SCHEMA,
    THEME_VERSION,
    run_018_post_signoff_monitor,
    run_018_theme_archive,
    run_018_theme_signoff,
)

pytestmark = [pytest.mark.signoff_cycle42]

REPO = Path(__file__).resolve().parents[1]
SCRIPTS = REPO / "scripts"


def test_constants_018_channel():
    assert THEME_VERSION == "0.18.0"
    assert THEME_FREEZE == "0.18.x"
    assert THEME_SCHEMA == "mesh.bundle/v1"
    assert SEAL_CP_018 == "CP-0046"
    assert PRIOR_CP_018 == "CP-0045"
    assert CYCLE_018 == 42
    assert PREFERRED_NEXT_DEFAULT == "0.19_bootstrap_plan"
    assert list(THEME_CPS) == [
        "CP-0038",
        "CP-0039",
        "CP-0040",
        "CP-0041",
        "CP-0042",
        "CP-0043",
        "CP-0044",
        "CP-0045",
    ]
    assert len(THEME_DOCS) == 8


def test_theme_docs_exist_on_disk():
    for name, rel in THEME_DOCS:
        assert (REPO / rel).is_file(), f"missing {name}: {rel}"


def test_theme_cps_sealed():
    for cp in THEME_CPS:
        snap = REPO / "snapshots" / cp
        assert snap.is_dir(), cp
        ck = snap / "CHECKPOINT.json"
        assert ck.is_file(), cp
        data = json.loads(ck.read_text(encoding="utf-8"))
        assert str(data.get("status", "")).upper() == "VERIFIED", cp


def test_signoff_pass_real_repo(tmp_path: Path):
    out = tmp_path / "releases" / "0.18.0"
    result = run_018_theme_signoff(
        REPO,
        out_dir=out,
        tip="sg018a",
        timestamp="2026-09-26T23:10:00Z",
        pytest_count=722,
        skip_pytest=True,
        write_project_state=False,
    )
    assert result.ok, result.errors
    assert result.version == "0.18.0"
    assert result.freeze_channel == THEME_FREEZE
    assert result.cp == SEAL_CP_018
    assert result.prior_cp == PRIOR_CP_018
    assert result.dual_primary == 0
    path = Path(result.signoff_path)
    assert path.is_file()
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["ok"] is True
    assert data["ver"] == "0.18.0"
    assert data["freeze"] == THEME_FREEZE
    assert data["themes"]["status"] == "CLOSED"
    assert data["line_status"] == "CLOSED_FROZEN_THEMES"
    assert data["preferred_next"] == PREFERRED_NEXT_DEFAULT
    assert "1" in data["themes"] and "8" in data["themes"]
    assert (out / "CHECKLIST.json").is_file()


def test_signoff_force_fail_themes(tmp_path: Path):
    result = run_018_theme_signoff(
        REPO,
        out_dir=tmp_path / "bad",
        tip="sgbad",
        pytest_count=10,
        skip_pytest=True,
        force_fail="themes_h1_h8_shipped",
        write_project_state=False,
    )
    assert not result.ok
    assert any(g.name == "themes_h1_h8_shipped" and not g.ok for g in result.gates)


def test_signoff_force_fail_version(tmp_path: Path):
    result = run_018_theme_signoff(
        REPO,
        out_dir=tmp_path / "badver",
        tip="sgver",
        pytest_count=10,
        skip_pytest=True,
        force_fail="version_0180",
        write_project_state=False,
    )
    assert not result.ok
    assert any(g.name == "version_0180" and not g.ok for g in result.gates)


def test_signoff_force_fail_gia(tmp_path: Path):
    result = run_018_theme_signoff(
        REPO,
        out_dir=tmp_path / "badgia",
        tip="sggia",
        pytest_count=10,
        skip_pytest=True,
        force_fail="no_gia_claim",
        write_project_state=False,
    )
    assert not result.ok
    assert any(g.name == "no_gia_claim" and not g.ok for g in result.gates)


def test_archive_builds_without_tag(tmp_path: Path):
    out = tmp_path / "releases" / "0.18.0"
    sg = run_018_theme_signoff(
        REPO,
        out_dir=out,
        tip="arch018",
        pytest_count=40,
        skip_pytest=True,
        write_project_state=False,
    )
    assert sg.ok, sg.errors
    result = run_018_theme_archive(
        REPO,
        version="0.18.0",
        out_dir=out,
        tip="arch018",
        create_tag=False,
        require_clean=False,
        skip_bundle=True,
    )
    assert result.ok, result.errors
    assert (out / "SIGNOFF.json").is_file()
    assert (out / "SHA256SUMS").is_file()
    assert (out / "ARCHIVE_MANIFEST.json").is_file()
    assert (out / "TAG_MARKER.json").is_file()
    assert result.release_archive and Path(result.release_archive).is_file()
    assert result.tag_created is False
    marker = json.loads((out / "TAG_MARKER.json").read_text(encoding="utf-8"))
    from neural_mesh.packaging.release_tag_archive import preferred_tag_name

    expect_tag = preferred_tag_name(REPO, "0.18.0")
    assert marker["tag"] == expect_tag
    assert marker["freeze"] == THEME_FREEZE
    mans = list(out.glob("*.manifest.json"))
    assert mans
    man = json.loads(mans[0].read_text(encoding="utf-8"))
    assert man["channel"] == THEME_FREEZE


def test_archive_fail_missing_signoff(tmp_path: Path):
    out = tmp_path / "empty"
    out.mkdir()
    result = run_018_theme_archive(
        REPO,
        version="0.18.0",
        out_dir=out,
        tip="nosg",
        create_tag=False,
        require_clean=False,
        skip_bundle=True,
        force_fail="signoff_present",
    )
    assert not result.ok
    assert any(g.name == "signoff_present" and not g.ok for g in result.gates)


def test_archive_mock_tag(tmp_path: Path):
    out = tmp_path / "releases" / "0.18.0"
    assert run_018_theme_signoff(
        REPO,
        out_dir=out,
        tip="tagmock",
        pytest_count=12,
        skip_pytest=True,
        write_project_state=False,
    ).ok

    def _fake_tag(root: Path, name: str, message: str | None = None) -> tuple[bool, str]:
        return True, f"mock-created {name}"

    result = run_018_theme_archive(
        REPO,
        version="0.18.0",
        out_dir=out,
        tip="tagmock",
        create_tag=True,
        require_clean=False,
        skip_bundle=True,
        tag_fn=_fake_tag,
    )
    assert result.ok, result.errors
    assert result.tag_created is True
    from neural_mesh.packaging.release_tag_archive import preferred_tag_name

    assert result.tag_name == preferred_tag_name(REPO, "0.18.0")


def test_script_cli_signoff(tmp_path: Path):
    py = REPO / ".venv" / "bin" / "python"
    if not py.is_file():
        py = Path(sys.executable)
    r = subprocess.run(
        [
            str(py),
            str(SCRIPTS / "theme_signoff_018.py"),
            "signoff",
            "--root",
            str(REPO),
            "--out",
            str(tmp_path / "0.18.0"),
            "--tip",
            "cli018",
            "--pytest-count",
            "50",
            "--skip-pytest",
            "--json",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert r.returncode == 0, r.stderr + r.stdout
    data = json.loads(r.stdout)
    assert data["ok"] is True
    assert data["version"] == "0.18.0"


def test_capability_doc_present():
    doc = REPO / "docs" / "capabilities" / "MESH_0.18_SIGNOFF.md"
    assert doc.is_file()
    text = doc.read_text(encoding="utf-8")
    assert "0.18" in text
    assert "CLOSED" in text or "FROZEN" in text
    assert "NO_HELD" in text
    assert "H1" in text and "H8" in text
    assert "0.19" in text
    low = text.lower()
    assert "do not claim gia" in low or "gia remains no_held" in low
    assert "gia achieved" not in low
    assert "we have gia" not in low
    assert "l_gia = unlock" not in low


def test_no_prior_reopen_and_no_gia():
    """0.16.3 / 0.17.0 remain closed; Cycle 42 does not claim GIA."""
    assert (REPO / "dist" / "releases" / "0.16.3" / "SIGNOFF.json").is_file()
    assert (REPO / "dist" / "releases" / "0.17.0" / "SIGNOFF.json").is_file()
    for tag in ("v0.16.3", "v0.17.0"):
        proc = subprocess.run(
            ["git", "rev-parse", "-q", "--verify", f"refs/tags/{tag}"],
            cwd=str(REPO),
            capture_output=True,
            text=True,
            check=False,
        )
        assert proc.returncode == 0, tag
    signoff = (
        REPO / "docs" / "capabilities" / "MESH_0.18_SIGNOFF.md"
    ).read_text(encoding="utf-8").lower()
    assert "do not claim gia" in signoff or "gia remains no_held" in signoff
    assert preferred_next_safe()


def preferred_next_safe() -> bool:
    return PREFERRED_NEXT_DEFAULT in (
        "0.19_bootstrap_plan",
        "L_judge_adapter_design",
        "HOLD_L_JUDGE",
        "0.19_plan",
    )


def test_post_signoff_monitor_once(tmp_path: Path):
    out = tmp_path / "releases" / "0.18.0"
    sg = run_018_theme_signoff(
        REPO,
        out_dir=out,
        tip="mon018",
        pytest_count=20,
        skip_pytest=True,
        write_project_state=False,
    )
    assert sg.ok, sg.errors
    ar = run_018_theme_archive(
        REPO,
        version="0.18.0",
        out_dir=out,
        tip="mon018",
        create_tag=False,
        require_clean=False,
        skip_bundle=False,
    )
    assert ar.ok, ar.errors
    result = run_018_post_signoff_monitor(
        REPO, version="0.18.0", out_dir=out, tip="mon018"
    )
    assert result.ok, result.errors
    assert (out / "MONITOR.json").is_file()
    data = json.loads((out / "MONITOR.json").read_text(encoding="utf-8"))
    assert data.get("ok") is True
    assert data.get("theme_signoff") is True
    assert data.get("freeze_expected") == THEME_FREEZE
    assert data.get("preferred_next") == PREFERRED_NEXT_DEFAULT
