"""Tests for Cycle 32 / CP-0036: 0.17 theme-set signoff closeout.

Markers: signoff_cycle32
Aim: ≥10 tests — signoff gates, archive, monitor, docs, no 0.16.3 reopen, no H1..H8.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from neural_mesh.packaging.theme_signoff_017 import (
    CYCLE_017,
    PRIOR_CP_017,
    SEAL_CP_017,
    THEME_CPS,
    THEME_DOCS,
    THEME_FREEZE,
    THEME_SCHEMA,
    THEME_VERSION,
    run_017_post_signoff_monitor,
    run_017_theme_archive,
    run_017_theme_signoff,
)

pytestmark = [pytest.mark.signoff_cycle32]

REPO = Path(__file__).resolve().parents[1]
SCRIPTS = REPO / "scripts"


def test_constants_017_channel():
    assert THEME_VERSION == "0.17.0"
    assert THEME_FREEZE == "0.17.x-n2"
    assert "n2" in THEME_SCHEMA
    assert SEAL_CP_017 == "CP-0036"
    assert PRIOR_CP_017 == "CP-0035"
    assert CYCLE_017 == 32
    assert list(THEME_CPS) == [
        "CP-0031",
        "CP-0032",
        "CP-0033",
        "CP-0034",
        "CP-0035",
    ]


def test_theme_docs_exist_on_disk():
    for name, rel in THEME_DOCS:
        assert (REPO / rel).is_file(), f"missing {name}: {rel}"


def test_theme_cps_sealed():
    for cp in THEME_CPS:
        snap = REPO / "snapshots" / cp
        assert snap.is_dir(), cp
        assert (snap / "CHECKPOINT.json").is_file(), cp


def test_signoff_pass_real_repo(tmp_path: Path):
    out = tmp_path / "releases" / "0.17.0"
    result = run_017_theme_signoff(
        REPO,
        out_dir=out,
        tip="sg017a",
        timestamp="2026-09-23T22:30:00Z",
        pytest_count=554,
        skip_pytest=True,
        write_project_state=False,
    )
    assert result.ok, result.errors
    assert result.version == "0.17.0"
    assert result.freeze_channel == THEME_FREEZE
    assert result.cp == SEAL_CP_017
    assert result.prior_cp == PRIOR_CP_017
    assert result.dual_primary == 0
    path = Path(result.signoff_path)
    assert path.is_file()
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["ok"] is True
    assert data["ver"] == "0.17.0"
    assert data["freeze"] == THEME_FREEZE
    assert data["themes"]["status"] == "CLOSED"
    assert data["line_status"] == "CLOSED_FROZEN_THEMES"
    assert (out / "CHECKLIST.json").is_file()


def test_signoff_force_fail_themes(tmp_path: Path):
    result = run_017_theme_signoff(
        REPO,
        out_dir=tmp_path / "bad",
        tip="sgbad",
        pytest_count=10,
        skip_pytest=True,
        force_fail="themes_1_4_shipped",
        write_project_state=False,
    )
    assert not result.ok
    assert any(g.name == "themes_1_4_shipped" and not g.ok for g in result.gates)


def test_signoff_force_fail_version(tmp_path: Path):
    result = run_017_theme_signoff(
        REPO,
        out_dir=tmp_path / "badver",
        tip="sgver",
        pytest_count=10,
        skip_pytest=True,
        force_fail="version_0170",
        write_project_state=False,
    )
    assert not result.ok
    assert any(g.name == "version_0170" and not g.ok for g in result.gates)


def test_archive_builds_without_tag(tmp_path: Path):
    out = tmp_path / "releases" / "0.17.0"
    sg = run_017_theme_signoff(
        REPO,
        out_dir=out,
        tip="arch017",
        pytest_count=40,
        skip_pytest=True,
        write_project_state=False,
    )
    assert sg.ok, sg.errors
    result = run_017_theme_archive(
        REPO,
        version="0.17.0",
        out_dir=out,
        tip="arch017",
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
    assert marker["tag"] == "v0.17.0"
    assert marker["freeze"] == THEME_FREEZE


def test_archive_fail_missing_signoff(tmp_path: Path):
    out = tmp_path / "empty"
    out.mkdir()
    result = run_017_theme_archive(
        REPO,
        version="0.17.0",
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
    out = tmp_path / "releases" / "0.17.0"
    assert run_017_theme_signoff(
        REPO,
        out_dir=out,
        tip="tagmock",
        pytest_count=12,
        skip_pytest=True,
        write_project_state=False,
    ).ok

    def _fake_tag(root: Path, name: str, message: str | None = None) -> tuple[bool, str]:
        return True, f"mock-created {name}"

    result = run_017_theme_archive(
        REPO,
        version="0.17.0",
        out_dir=out,
        tip="tagmock",
        create_tag=True,
        require_clean=False,
        skip_bundle=True,
        tag_fn=_fake_tag,
    )
    assert result.ok, result.errors
    assert result.tag_created is True
    assert result.tag_name == "v0.17.0"


def test_script_cli_signoff(tmp_path: Path):
    py = REPO / ".venv" / "bin" / "python"
    if not py.is_file():
        py = Path(sys.executable)
    r = subprocess.run(
        [
            str(py),
            str(SCRIPTS / "theme_signoff_017.py"),
            "signoff",
            "--root",
            str(REPO),
            "--out",
            str(tmp_path / "0.17.0"),
            "--tip",
            "cli017",
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
    assert data["version"] == "0.17.0"


def test_capability_doc_present():
    doc = REPO / "docs" / "capabilities" / "MESH_0.17_SIGNOFF.md"
    assert doc.is_file()
    text = doc.read_text(encoding="utf-8")
    assert "0.17" in text
    assert "CLOSED" in text or "FROZEN" in text
    assert "NO_HELD" in text
    assert "0.18" in text
    assert "H1" in text
    # must not claim H1..H8 implemented
    assert "H1 implemented" not in text.lower()
    assert "do not implement H1" in text.lower() or "signoff/closeout only" in text.lower()


def test_no_0163_reopen_and_no_h_impl():
    """0.16.3 remains closed; this cycle does not ship H1..H8 modules."""
    assert (REPO / "dist" / "releases" / "0.16.3" / "SIGNOFF.json").is_file()
    # local tag v0.16.3 must still exist
    proc = subprocess.run(
        ["git", "rev-parse", "-q", "--verify", "refs/tags/v0.16.3"],
        cwd=str(REPO),
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0
    # no H1 identity implementation module yet
    assert not (REPO / "src" / "neural_mesh" / "identity").exists()
    assert not (REPO / "docs" / "capabilities" / "MESH_H1_IDENTITY.md").exists()


def test_post_signoff_monitor_once(tmp_path: Path):
    out = tmp_path / "releases" / "0.17.0"
    sg = run_017_theme_signoff(
        REPO,
        out_dir=out,
        tip="mon017",
        pytest_count=20,
        skip_pytest=True,
        write_project_state=False,
    )
    assert sg.ok, sg.errors
    ar = run_017_theme_archive(
        REPO,
        version="0.17.0",
        out_dir=out,
        tip="mon017",
        create_tag=False,
        require_clean=False,
        skip_bundle=False,  # need N2 manifest for freeze check
    )
    assert ar.ok, ar.errors
    result = run_017_post_signoff_monitor(REPO, version="0.17.0", out_dir=out, tip="mon017")
    assert result.ok, getattr(result, "errors", None)
    assert (out / "MONITOR.json").is_file()
    data = json.loads((out / "MONITOR.json").read_text(encoding="utf-8"))
    assert data.get("ok") is True or data.get("theme_signoff") is True
