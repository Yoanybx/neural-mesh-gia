"""Tests for Cycle 22 / CP-0026: RC install verify, rollback smoke, release checklist.

Markers: packaging_rc_cycle22, packaging_single_node_bundle
Aim: ≥10 new tests covering P12–P14.
"""

from __future__ import annotations

import json
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest

from neural_mesh.packaging import (
    FREEZE_CHANNEL,
    SCHEMA_ID,
    assert_entrypoint_present,
    build_bundle,
    load_manifest,
    rc_install,
    rc_install_verify,
    read_install_marker,
    rollback_smoke,
    run_release_checklist,
)

pytestmark = [
    pytest.mark.packaging_rc_cycle22,
    pytest.mark.packaging_single_node_bundle,
]

REPO = Path(__file__).resolve().parents[1]
SCRIPTS = REPO / "scripts"


def _mini_root(tmp_path: Path, *, ver: str = "0.16.2", tip_cp: str = "CP-0026") -> Path:
    root = tmp_path / f"repo-{ver}"
    (root / "src" / "neural_mesh").mkdir(parents=True)
    (root / "src" / "neural_mesh" / "__init__.py").write_text(
        f'__version__ = "{ver}"\n', encoding="utf-8"
    )
    (root / "src" / "neural_mesh" / "cli.py").write_text(
        "def main(argv=None):\n"
        "    import sys\n"
        "    argv = list(sys.argv[1:] if argv is None else argv)\n"
        "    if argv and argv[0] == '--help':\n"
        "        print('usage: mesh')\n"
        "        return 0\n"
        "    print('mesh', argv)\n"
        "    return 0\n",
        encoding="utf-8",
    )
    (root / "pyproject.toml").write_text(
        textwrap.dedent(
            f"""
            [build-system]
            requires = ["setuptools>=69"]
            build-backend = "setuptools.build_meta"
            [project]
            name = "neural-mesh-gia"
            version = "{ver}"
            requires-python = ">=3.10"
            [project.scripts]
            mesh = "neural_mesh.cli:main"
            [tool.setuptools.packages.find]
            where = ["src"]
            """
        ).strip()
        + "\n",
        encoding="utf-8",
    )
    (root / "scripts").mkdir()
    for name in (
        "build_bundle.py",
        "verify_bundle.py",
        "clean_node_smoke.py",
        "repro_check.py",
        "rc_install_verify.py",
        "rollback_smoke.py",
        "release_checklist.py",
    ):
        (root / "scripts" / name).write_text(f"# stub {name}\n", encoding="utf-8")
    (root / "scripts" / "audit.sh").write_text("#!/bin/sh\necho ok\n", encoding="utf-8")
    (root / "scripts" / "bootstrap.sh").write_text(
        "#!/bin/sh\necho boot\n", encoding="utf-8"
    )
    debt = root / "docs" / "debt"
    debt.mkdir(parents=True)
    (debt / "CHECKPOINT_EVERY_FLOOR.md").write_text(
        "# debt\nStatus: SCHEMA-GATED\n", encoding="utf-8"
    )
    cap = root / "docs" / "capabilities"
    cap.mkdir(parents=True)
    (cap / "MESH_PACKAGING_SINGLE_NODE_BUNDLE.md").write_text(
        "# packaging\nNO: Raft\n", encoding="utf-8"
    )
    (cap / "MESH_PACKAGING_RELEASE_CHECKLIST.md").write_text(
        "# checklist\nNO_HELD: Raft,N>2,SLO_chase,tag_schema,EVERY_fsync\n",
        encoding="utf-8",
    )
    state = root / ".project_state"
    state.mkdir()
    (state / "CHECKPOINT.json").write_text(
        json.dumps(
            {
                "last_checkpoint": tip_cp,
                "project_version": ver,
                "test_summary": {"passed": 411, "failed": 0},
                "status": "VERIFIED",
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    (root / "snapshots" / "CP-0025").mkdir(parents=True)
    (root / "snapshots" / tip_cp).mkdir(parents=True)
    (root / "council").mkdir(parents=True)
    (root / "council" / "COUNCIL_AGREEMENT_CYCLE22.md").write_text(
        "NO_HELD: Raft,N>2,multi-primary,ML,R2,R3,plaintext,Vault-ACME-req,GIA,"
        "SLO_chase,tag_schema,EVERY_fsync\n",
        encoding="utf-8",
    )
    return root


# --- P12: rc_install_verify -------------------------------------------------


def test_assert_entrypoint_present_ok_and_missing(tmp_path: Path):
    root = _mini_root(tmp_path)
    assert assert_entrypoint_present(root) == []
    (root / "src" / "neural_mesh" / "cli.py").unlink()
    errs = assert_entrypoint_present(root)
    assert errs and any("cli.py" in e for e in errs)


def test_assert_entrypoint_corrupt_fails(tmp_path: Path):
    root = _mini_root(tmp_path)
    (root / "src" / "neural_mesh" / "cli.py").write_text(
        "# no main here\n", encoding="utf-8"
    )
    errs = assert_entrypoint_present(root)
    assert any("def main" in e or "corrupt" in e for e in errs)
    # Also strip scripts section
    py = (root / "pyproject.toml").read_text(encoding="utf-8")
    (root / "pyproject.toml").write_text(
        py.replace("[project.scripts]\nmesh = \"neural_mesh.cli:main\"\n", ""),
        encoding="utf-8",
    )
    errs2 = assert_entrypoint_present(root)
    assert any("entrypoint" in e or "project.scripts" in e for e in errs2)


def test_rc_install_verify_success_real_bundle(tmp_path: Path):
    out = tmp_path / "dist"
    m = build_bundle(
        REPO,
        out,
        tip="c22inst",
        ver="0.17.0",
        cp_range="CP-0001..0030",
        pytest={"passed": 411, "failed": 0},
    )
    tar = out / f"{m.name}-{m.ver}.tar.gz"
    result = rc_install_verify(
        tar,
        prefix=tmp_path / "prefix",
        forbidden_repo=REPO,
        keep_prefix=True,
    )
    assert result.ok, result.errors
    assert result.import_ok is True
    assert result.help_ok is True
    assert result.status_ok is True
    assert result.freeze_channel == FREEZE_CHANNEL
    assert result.version == "0.18.0"
    marker = read_install_marker(tmp_path / "prefix")
    assert marker.get("ver") == "0.17.0"  # manifest ver param; live __version__ is 0.18.0
    assert (tmp_path / "prefix" / "bin" / "mesh").is_file()


def test_rc_install_verify_fails_missing_entrypoint(tmp_path: Path):
    root = _mini_root(tmp_path / "r")
    # Remove entrypoint before build by rewriting pyproject without scripts, but
    # then assert_entrypoint during install fails. Instead: build OK then corrupt extract
    # via rc_install path — mutate after build by rebuilding without scripts.
    (root / "pyproject.toml").write_text(
        textwrap.dedent(
            """
            [build-system]
            requires = ["setuptools>=69"]
            build-backend = "setuptools.build_meta"
            [project]
            name = "neural-mesh-gia"
            version = "0.16.2"
            requires-python = ">=3.10"
            [tool.setuptools.packages.find]
            where = ["src"]
            """
        ).strip()
        + "\n",
        encoding="utf-8",
    )
    out = tmp_path / "dist"
    m = build_bundle(root, out, tip="badep01", ver="0.16.2", freeze=True)
    tar = out / f"{m.name}-{m.ver}.tar.gz"
    # verify_bundle smoke may still pass (import works); install entrypoint check fails
    result = rc_install(
        tar,
        tmp_path / "prefix",
        run_verify=True,
        clear_prefix=True,
    )
    assert not result.ok
    assert any("entrypoint" in e or "project.scripts" in e for e in result.errors)


def test_rc_install_verify_script_cli(tmp_path: Path):
    out = tmp_path / "dist"
    m = build_bundle(
        REPO,
        out,
        tip="c22cli1",
        ver="0.16.3",
        cp_range="CP-0001..0027",
        pytest={"passed": 1, "failed": 0},
    )
    tar = out / f"{m.name}-{m.ver}.tar.gz"
    py = REPO / ".venv" / "bin" / "python"
    if not py.is_file():
        py = Path(sys.executable)
    r = subprocess.run(
        [
            str(py),
            str(SCRIPTS / "rc_install_verify.py"),
            str(tar),
            "--prefix",
            str(tmp_path / "pfx"),
            "--forbidden-repo",
            str(REPO),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert r.returncode == 0, r.stderr + r.stdout
    assert "RC_INSTALL_VERIFY: PASS" in r.stdout


# --- P13: rollback_smoke ----------------------------------------------------


def test_rollback_smoke_a_then_b_then_a(tmp_path: Path):
    """Build ver A=0.16.1-like and B=0.16.2-like; install B; rollback to A."""
    root_a = _mini_root(tmp_path / "a", ver="0.16.1")
    root_b = _mini_root(tmp_path / "b", ver="0.16.2")
    out = tmp_path / "dist"
    ma = build_bundle(
        root_a, out, tip="tipaaa1", ver="0.16.1", cp_range="CP-0001..0025"
    )
    mb = build_bundle(
        root_b, out, tip="tipbbb2", ver="0.16.2", cp_range="CP-0001..0026"
    )
    tar_a = out / f"{ma.name}-{ma.ver}.tar.gz"
    tar_b = out / f"{mb.name}-{mb.ver}.tar.gz"
    prefix = tmp_path / "prefix"
    # Mini roots lack status_snapshot — skip post smoke that needs full mesh;
    # use rollback_smoke with run_post_smoke=False then assert markers.
    result = rollback_smoke(
        tar_a,
        tar_b,
        prefix,
        expect_ver_a="0.16.1",
        run_post_smoke=False,
    )
    assert result.ok, result.errors
    assert result.ver_before == "0.16.2"
    assert result.ver_after == "0.16.1"
    assert result.tip_after == "tipaaa1"
    loaded = load_manifest(prefix / "bundle.manifest.json")
    assert loaded.ver == "0.16.1"
    assert loaded.tip == "tipaaa1"
    assert (prefix / "bin" / "mesh").is_file()


def test_rollback_smoke_real_repo_ver_overrides(tmp_path: Path):
    out = tmp_path / "dist"
    ma = build_bundle(
        REPO, out, tip="realrola", ver="0.16.1", cp_range="CP-0001..0026",
        pytest={"passed": 1, "failed": 0},
    )
    mb = build_bundle(
        REPO, out, tip="realrolb", ver="0.16.2", cp_range="CP-0001..0026",
        pytest={"passed": 1, "failed": 0},
    )
    result = rollback_smoke(
        out / f"{ma.name}-{ma.ver}.tar.gz",
        out / f"{mb.name}-{mb.ver}.tar.gz",
        tmp_path / "prefix",
        expect_ver_a="0.16.1",
        forbidden_repo=REPO,
        run_post_smoke=True,
    )
    assert result.ok, result.errors
    assert result.ver_after == "0.16.1"
    assert result.tip_after == "realrola"
    assert result.smoke_after and result.smoke_after.get("ok") is True


def test_rollback_smoke_script_cli(tmp_path: Path):
    py = REPO / ".venv" / "bin" / "python"
    if not py.is_file():
        py = Path(sys.executable)
    r = subprocess.run(
        [
            str(py),
            str(SCRIPTS / "rollback_smoke.py"),
            "--build",
            "--root",
            str(REPO),
            "--out",
            str(tmp_path / "dist"),
            "--ver-a",
            "0.16.1",
            "--ver-b",
            "0.16.2",
            "--tip-a",
            "scrpa01",
            "--tip-b",
            "scrpb01",
            "--prefix",
            str(tmp_path / "pfx"),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert r.returncode == 0, r.stderr + r.stdout
    assert "ROLLBACK_SMOKE: PASS" in r.stdout


# --- P14: release_checklist -------------------------------------------------


def test_release_checklist_pass_with_skips(tmp_path: Path):
    """Checklist passes when gates forced via skips + freeze build (no live CP yet)."""
    # Use REPO but skip cp (CP-0026 may not exist mid-test) and skip pytest/smoke cost
    # by using marker + skip_pytest; still run freeze + version + no_held.
    result = run_release_checklist(
        REPO,
        expect_version="0.18.0",
        expect_cp="CP-0027",
        out_dir=tmp_path / "chk",
        tip="chkpass",
        skip_repro=False,
        skip_smoke=True,
        skip_pytest=True,
        skip_cp=True,
        require_freeze=True,
    )
    assert result.ok, result.errors
    assert result.version == "0.18.0"
    assert result.freeze_channel == FREEZE_CHANNEL
    names = {g.name for g in result.gates}
    assert "version_match" in names
    assert "freeze_present" in names
    assert "no_held_documented" in names
    d = result.to_dict()
    assert d["ok"] is True
    assert "no_held" in d


def test_release_checklist_fails_when_freeze_missing(tmp_path: Path):
    out = tmp_path / "dist"
    m = build_bundle(
        REPO,
        out,
        tip="nofreez",
        ver="0.16.2",
        freeze=False,
        pytest={"passed": 1, "failed": 0},
    )
    tar = out / f"{m.name}-{m.ver}.tar.gz"
    result = run_release_checklist(
        REPO,
        expect_version="0.18.0",
        expect_cp="CP-0027",
        out_dir=tmp_path / "chk",
        skip_repro=True,
        skip_smoke=True,
        skip_pytest=True,
        skip_cp=True,
        require_freeze=True,
        prebuilt_tar=tar,
    )
    assert not result.ok
    assert any(g.name == "freeze_present" and not g.ok for g in result.gates)


def test_release_checklist_fails_version_mismatch(tmp_path: Path):
    result = run_release_checklist(
        REPO,
        expect_version="9.9.9",
        expect_cp="CP-0027",
        out_dir=tmp_path / "chk",
        tip="verfail",
        skip_repro=True,
        skip_smoke=True,
        skip_pytest=True,
        skip_cp=True,
    )
    assert not result.ok
    assert any(g.name == "version_match" and not g.ok for g in result.gates)


def test_release_checklist_script_json(tmp_path: Path):
    py = REPO / ".venv" / "bin" / "python"
    if not py.is_file():
        py = Path(sys.executable)
    r = subprocess.run(
        [
            str(py),
            str(SCRIPTS / "release_checklist.py"),
            "--out",
            str(tmp_path / "chk"),
            "--expect-version",
            "0.18.0",
            "--expect-cp",
            "CP-0027",
            "--skip-cp",
            "--skip-pytest",
            "--skip-smoke",
            "--tip",
            "scrchk1",
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
    assert data["freeze_channel"] == FREEZE_CHANNEL


def test_version_gate_0162_files():
    """Historical name; live package is 0.18.0; 0.16.3 release remains closed."""
    init = (REPO / "src" / "neural_mesh" / "__init__.py").read_text(encoding="utf-8")
    pyproject = (REPO / "pyproject.toml").read_text(encoding="utf-8")
    assert 'version = "0.18.0"' in pyproject
    assert '__version__ = "0.18.0"' in init
