
"""Tests for Cycle 28 / CP-0032: N2 soak, final audit, RC freeze (P30–P32).

Markers: packaging_n2, packaging_n2_cycle28
Aim: ≥12 new tests.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from neural_mesh.packaging import (
    FREEZE_CHANNEL_N2,
    SCHEMA_ID_N2,
    build_n2_bundle,
    run_n2_final_release_audit,
    run_n2_rc_soak,
    verify_n2_bundle,
)
from neural_mesh.packaging.manifest_n2 import N2FreezeInfo

pytestmark = [
    pytest.mark.packaging_n2,
    pytest.mark.packaging_n2_cycle28,
]

REPO = Path(__file__).resolve().parents[1]
SCRIPTS = REPO / "scripts"


# Reuse Cycle 27 mini root helper
from tests.test_packaging_n2_cycle27 import _mini_n2_root  # noqa: E402


# --- P30: n2_rc_soak ---------------------------------------------------------


def test_n2_rc_soak_small_n(tmp_path: Path):
    root = _mini_n2_root(tmp_path)
    result = run_n2_rc_soak(
        root,
        n=2,
        out_dir=tmp_path / "soak",
        tip="soakn2a",
        ver="0.17.0",
        variance_bound=1000.0,
        reuse_prefix=True,
    )
    assert result.ok, result.errors
    assert result.n == 2
    assert result.pass_count == 2
    assert result.total_p50_ms is not None
    assert result.total_p99_ms is not None
    assert result.dual_primary == 0
    assert result.freeze_channel == FREEZE_CHANNEL_N2
    assert result.report_path and Path(result.report_path).is_file()
    data = json.loads(Path(result.report_path).read_text(encoding="utf-8"))
    assert data["pass"] == 2
    assert "step_stats" in data


def test_n2_rc_soak_n3(tmp_path: Path):
    root = _mini_n2_root(tmp_path)
    result = run_n2_rc_soak(
        root,
        n=3,
        out_dir=tmp_path / "soak3",
        tip="soakn3",
        ver="0.17.0",
        variance_bound=1000.0,
    )
    assert result.ok, result.errors
    assert result.pass_count == 3
    assert "verify" in result.step_stats
    assert "install" in result.step_stats


def test_n2_rc_soak_force_fail(tmp_path: Path):
    root = _mini_n2_root(tmp_path)
    result = run_n2_rc_soak(
        root,
        n=2,
        out_dir=tmp_path / "soakfail",
        tip="soakbad",
        ver="0.17.0",
        force_fail_step="verify",
        variance_bound=1000.0,
    )
    assert not result.ok
    assert result.fail_count >= 1
    assert any("forced fail" in e or "verify" in e for e in result.errors)


def test_n2_rc_soak_script_cli(tmp_path: Path):
    root = _mini_n2_root(tmp_path)
    # Build a bundle first so script can consume it via --root
    py = REPO / ".venv" / "bin" / "python"
    if not py.is_file():
        py = Path(sys.executable)
    r = subprocess.run(
        [
            str(py),
            str(SCRIPTS / "n2_rc_soak.py"),
            "--root",
            str(root),
            "--out",
            str(tmp_path / "soak"),
            "--n",
            "2",
            "--ver",
            "0.18.0",
            "--tip",
            "soakcli",
            "--variance-bound",
            "1000",
            "--json",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert r.returncode == 0, r.stderr + r.stdout
    data = json.loads(r.stdout)
    assert data["ok"] is True
    assert data["pass"] == 2


# --- P31: n2_final_release_audit --------------------------------------------


def test_n2_final_audit_pass_injected(tmp_path: Path):
    result = run_n2_final_release_audit(
        REPO,
        expect_version="0.18.0",
        expect_cp="CP-0032",
        out_dir=tmp_path / "audit",
        tip="audpass",
        skip_verify=True,
        skip_soak=True,
        soak_ok=True,
        skip_pytest=True,
        skip_cp=True,
        packaging_n2_count=26,
    )
    assert result.ok, result.errors
    assert result.version == "0.18.0"
    assert result.freeze_channel == FREEZE_CHANNEL_N2
    assert result.packaging_n2_count == 26
    assert result.dual_primary == 0
    assert result.report_path and Path(result.report_path).is_file()
    names = {g.name for g in result.gates}
    assert "freeze_channel_017x_n2" in names
    assert "no_held_documented" in names
    assert "dual_primary_zero" in names


def test_n2_final_audit_fails_bad_version(tmp_path: Path):
    result = run_n2_final_release_audit(
        REPO,
        expect_version="9.9.9",
        expect_cp="CP-0032",
        out_dir=tmp_path / "audit",
        tip="audbadv",
        skip_verify=True,
        skip_soak=True,
        soak_ok=True,
        skip_pytest=True,
        skip_cp=True,
        packaging_n2_count=10,
    )
    assert not result.ok
    assert any("version" in g.name and not g.ok for g in result.gates)


def test_n2_final_audit_fails_soak_missing(tmp_path: Path):
    result = run_n2_final_release_audit(
        REPO,
        expect_version="0.18.0",
        expect_cp="CP-0032",
        out_dir=tmp_path / "audit",
        skip_verify=True,
        skip_soak=False,
        soak_ok=None,
        skip_pytest=True,
        skip_cp=True,
        packaging_n2_count=10,
    )
    assert not result.ok
    assert any(g.name == "n2_soak" and not g.ok for g in result.gates)


def test_n2_final_audit_script_json(tmp_path: Path):
    py = REPO / ".venv" / "bin" / "python"
    if not py.is_file():
        py = Path(sys.executable)
    r = subprocess.run(
        [
            str(py),
            str(SCRIPTS / "n2_final_release_audit.py"),
            "--out",
            str(tmp_path / "audit"),
            "--expect-version",
            "0.18.0",
            "--expect-cp",
            "CP-0032",
            "--skip-cp",
            "--skip-pytest",
            "--skip-verify",
            "--soak-ok",
            "true",
            "--packaging-n2-count",
            "20",
            "--tip",
            "audcli1",
            "--json",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert r.returncode == 0, r.stderr + r.stdout
    data = json.loads(r.stdout)
    assert data["ok"] is True
    assert data["dual_primary"] == 0


def test_n2_final_audit_doc_present():
    path = REPO / "docs" / "capabilities" / "MESH_PACKAGING_N2_FINAL_RELEASE_AUDIT.md"
    assert path.is_file()
    text = path.read_text(encoding="utf-8")
    assert "mesh.bundle.manifest/v1-n2" in text
    assert "0.17.x-n2" in text
    assert "FROZEN" in text
    assert "dual_primary=0" in text or "dual_primary" in text
    assert "NO_HELD" in text
    assert "Raft" in text


# --- P32: N2 RC freeze -------------------------------------------------------


def test_n2_build_always_embeds_freeze(tmp_path: Path):
    root = _mini_n2_root(tmp_path)
    m = build_n2_bundle(
        root,
        tmp_path / "out",
        ver="0.17.0",
        tip="frz001",
        cp_range="CP-0001..0032",
        freeze=False,  # must still embed for N2 RC
        single_node_for_parity=False,
    )
    assert m.freeze is not None
    assert m.freeze.channel == FREEZE_CHANNEL_N2
    assert m.freeze.schema_name == SCHEMA_ID_N2
    d = m.model_dump(by_alias=True)
    assert d["freeze"]["channel"] == "0.17.x-n2"
    assert d["freeze"]["schema"] == SCHEMA_ID_N2


def test_n2_verify_rejects_wrong_freeze_channel(tmp_path: Path):
    root = _mini_n2_root(tmp_path)
    out = tmp_path / "out"
    m = build_n2_bundle(
        root,
        out,
        ver="0.17.0",
        tip="frzbad",
        cp_range="CP-0001..0032",
        freeze=N2FreezeInfo(channel="wrong-channel", schema_name=SCHEMA_ID_N2),
        single_node_for_parity=False,
    )
    bundle = out / f"{m.name}-{m.ver}.tar.gz"
    man = out / f"{m.name}-{m.ver}.manifest.json"
    # Without expect: ok (freeze present with custom channel)
    ok_r = verify_n2_bundle(bundle, man, smoke=False)
    assert ok_r.ok, ok_r.errors
    # With expect: reject wrong channel
    bad = verify_n2_bundle(
        bundle,
        man,
        smoke=False,
        expect_freeze_channel=FREEZE_CHANNEL_N2,
    )
    assert not bad.ok
    assert any("freeze channel" in e for e in bad.errors)


def test_n2_verify_rejects_missing_freeze_when_expected(tmp_path: Path):
    root = _mini_n2_root(tmp_path)
    out = tmp_path / "out"
    m = build_n2_bundle(
        root,
        out,
        ver="0.17.0",
        tip="frzmiss",
        cp_range="CP-0001..0032",
        freeze=True,
        single_node_for_parity=False,
    )
    man_path = out / f"{m.name}-{m.ver}.manifest.json"
    data = json.loads(man_path.read_text(encoding="utf-8"))
    data.pop("freeze", None)
    man_path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    bundle = out / f"{m.name}-{m.ver}.tar.gz"
    bad = verify_n2_bundle(
        bundle,
        man_path,
        smoke=False,
        expect_freeze_channel=FREEZE_CHANNEL_N2,
    )
    assert not bad.ok
    assert any("freeze missing" in e for e in bad.errors)


def test_n2_freeze_does_not_touch_0163_single_node():
    """Closed 0.16.3 / single-node freeze channel stays 0.16.x."""
    from neural_mesh.packaging.manifest import FREEZE_CHANNEL, SCHEMA_ID

    assert FREEZE_CHANNEL == "0.16.x"
    assert SCHEMA_ID == "mesh.bundle.manifest/v1"
    assert FREEZE_CHANNEL_N2 != FREEZE_CHANNEL
    assert SCHEMA_ID_N2 != SCHEMA_ID
