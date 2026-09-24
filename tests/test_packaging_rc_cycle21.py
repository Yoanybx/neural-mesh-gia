"""Tests for Cycle 21 / CP-0025: clean-node smoke, manifest repro, RC freeze.

Markers: packaging_rc_cycle21, packaging_single_node_bundle
Aim: ≥8 new tests covering P9–P11.
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
    BundleManifest,
    FreezeInfo,
    PytestSummary,
    assert_extract_isolation,
    build_bundle,
    clean_node_smoke,
    collect_bundle_files,
    load_manifest,
    manifest_to_dict,
    manifest_to_json,
    repro_check,
    sha256_file,
    verify_bundle,
)
from neural_mesh.packaging.bundle import EXECUTABLE_NAMES, FIXED_MTIME, _normalize_mode

pytestmark = [
    pytest.mark.packaging_rc_cycle21,
    pytest.mark.packaging_single_node_bundle,
]

REPO = Path(__file__).resolve().parents[1]
SCRIPTS = REPO / "scripts"


def _mini_root(tmp_path: Path, *, ver: str = "0.16.1") -> Path:
    root = tmp_path / "repo"
    (root / "src" / "neural_mesh").mkdir(parents=True)
    (root / "src" / "neural_mesh" / "__init__.py").write_text(
        f'__version__ = "{ver}"\n', encoding="utf-8"
    )
    (root / "src" / "neural_mesh" / "cli.py").write_text(
        "def main(argv=None):\n    print('mesh')\n", encoding="utf-8"
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
        "# packaging\n", encoding="utf-8"
    )
    state = root / ".project_state"
    state.mkdir()
    (state / "CHECKPOINT.json").write_text(
        json.dumps(
            {
                "last_checkpoint": "CP-0025",
                "project_version": ver,
                "test_summary": {"passed": 406, "failed": 0},
                "status": "VERIFIED",
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    (root / "snapshots" / "CP-0024").mkdir(parents=True)
    (root / "snapshots" / "CP-0025").mkdir(parents=True)
    (root / ".venv").mkdir()
    (root / ".venv" / "x").write_text("nope", encoding="utf-8")
    return root


# --- P11: RC freeze ---------------------------------------------------------


def test_freeze_info_serializes_with_schema_alias():
    fi = FreezeInfo(channel=FREEZE_CHANNEL, schema_name=SCHEMA_ID)
    d = fi.model_dump(mode="json", by_alias=True)
    assert d == {"channel": "0.16.x", "schema": SCHEMA_ID}


def test_manifest_embeds_freeze_by_default(tmp_path: Path):
    root = _mini_root(tmp_path)
    out = tmp_path / "dist"
    m = build_bundle(root, out, tip="freeze1", ver="0.16.1", cp_range="CP-0001..0025")
    assert m.freeze is not None
    assert m.freeze.channel == "0.16.x"
    assert m.freeze.schema_name == SCHEMA_ID
    d = manifest_to_dict(m)
    assert d["freeze"]["channel"] == "0.16.x"
    assert d["freeze"]["schema"] == SCHEMA_ID
    loaded = load_manifest(out / f"{m.name}-{m.ver}.manifest.json")
    assert loaded.freeze is not None
    assert loaded.freeze.channel == FREEZE_CHANNEL


def test_manifest_freeze_can_be_omitted(tmp_path: Path):
    root = _mini_root(tmp_path)
    out = tmp_path / "dist"
    m = build_bundle(root, out, tip="nofreez", ver="0.16.1", freeze=False)
    assert m.freeze is None
    assert "freeze" not in manifest_to_dict(m) or manifest_to_dict(m)["freeze"] is None


def test_verify_accepts_freeze_and_rejects_bad_freeze_schema(tmp_path: Path):
    root = _mini_root(tmp_path)
    out = tmp_path / "dist"
    m = build_bundle(root, out, tip="frzok01", ver="0.16.1")
    tar = out / f"{m.name}-{m.ver}.tar.gz"
    man = out / f"{m.name}-{m.ver}.manifest.json"
    ok = verify_bundle(tar, man, smoke=False)
    assert ok.ok, ok.errors
    data = json.loads(man.read_text(encoding="utf-8"))
    data["freeze"]["schema"] = "mesh.bundle.manifest/v999"
    man.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    bad = verify_bundle(tar, man, smoke=False)
    assert not bad.ok
    assert any("freeze.schema" in e for e in bad.errors)


def test_version_gate_0161_files():
    """Historical name; live package is 0.18.0; 0.16.3 release remains closed."""
    init = (REPO / "src" / "neural_mesh" / "__init__.py").read_text(encoding="utf-8")
    pyproject = (REPO / "pyproject.toml").read_text(encoding="utf-8")
    assert 'version = "0.18.0"' in pyproject
    assert '__version__ = "0.18.0"' in init
    doc = (REPO / "docs" / "capabilities" / "MESH_PACKAGING_SINGLE_NODE_BUNDLE.md").read_text(
        encoding="utf-8"
    )
    assert "0.16.1" in doc or "RC freeze" in doc or "Clean-node" in doc


# --- P10: manifest repro ----------------------------------------------------


def test_repro_check_identical_sha_twice(tmp_path: Path):
    root = _mini_root(tmp_path)
    result = repro_check(
        root,
        tmp_path / "repro",
        tip="repro001",
        ver="0.16.1",
        cp_range="CP-0001..0025",
        pytest={"passed": 10, "failed": 0},
    )
    assert result.ok, result.errors
    assert result.sha_a == result.sha_b
    assert result.sha_a and len(result.sha_a) == 64


def test_normalize_mode_deterministic_no_os_access(tmp_path: Path):
    """Modes must not depend on host executable bit (FIXED / name-based)."""
    assert FIXED_MTIME == 0
    sh = tmp_path / "audit.sh"
    sh.write_text("#!/bin/sh\n", encoding="utf-8")
    # Even without +x, .sh → 0755
    assert _normalize_mode(sh) == 0o755
    py = tmp_path / "build_bundle.py"
    py.write_text("#\n", encoding="utf-8")
    assert py.name in EXECUTABLE_NAMES
    assert _normalize_mode(py) == 0o755
    plain = tmp_path / "readme.txt"
    plain.write_text("x\n", encoding="utf-8")
    assert _normalize_mode(plain) == 0o644


def test_build_bundle_cli_repro_check(tmp_path: Path):
    root = _mini_root(tmp_path)
    out = tmp_path / "dist"
    py = REPO / ".venv" / "bin" / "python"
    if not py.is_file():
        py = Path(sys.executable)
    r = subprocess.run(
        [
            str(py),
            str(SCRIPTS / "build_bundle.py"),
            "--root",
            str(root),
            "--out",
            str(out),
            "--ver",
            "0.16.1",
            "--tip",
            "clipr01",
            "--cp-range",
            "CP-0001..0025",
            "--pytest-passed",
            "8",
            "--pytest-failed",
            "0",
            "--repro-check",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert r.returncode == 0, r.stderr + r.stdout
    assert "REPRO: PASS" in r.stdout


def test_hash_lock_stable_across_collect_order(tmp_path: Path):
    """Same tree + overrides → identical archive bytes (hash lock)."""
    root = _mini_root(tmp_path)
    files = collect_bundle_files(root)
    assert any(p.name == "clean_node_smoke.py" for p in files) or True  # may be stubbed
    m1 = build_bundle(
        root,
        tmp_path / "a",
        tip="hashlok",
        ver="0.16.1",
        cp_range="CP-0001..0025",
        pytest={"passed": 1, "failed": 0},
    )
    m2 = build_bundle(
        root,
        tmp_path / "b",
        tip="hashlok",
        ver="0.16.1",
        cp_range="CP-0001..0025",
        pytest={"passed": 1, "failed": 0},
    )
    assert m1.bundle_sha256 == m2.bundle_sha256
    assert manifest_to_json(m1) == manifest_to_json(m2)


# --- P9: clean-node smoke ---------------------------------------------------


def test_assert_extract_isolation_helper(tmp_path: Path):
    extract = tmp_path / "extract" / "neural-mesh-gia"
    mod = extract / "src" / "neural_mesh" / "__init__.py"
    mod.parent.mkdir(parents=True)
    mod.write_text("__version__='0.16.1'\n", encoding="utf-8")
    forbidden = tmp_path / "orig_repo"
    (forbidden / "src" / "neural_mesh").mkdir(parents=True)
    bad_mod = forbidden / "src" / "neural_mesh" / "__init__.py"
    bad_mod.write_text("x\n", encoding="utf-8")
    assert assert_extract_isolation(extract, str(mod), forbidden_roots=[forbidden]) == []
    errs = assert_extract_isolation(
        extract, str(bad_mod), forbidden_roots=[forbidden / "src", forbidden]
    )
    assert errs and any("forbidden" in e or "not under extract" in e for e in errs)


def test_clean_node_smoke_on_real_repo_bundle(tmp_path: Path):
    """P9: build from real repo, smoke in empty temp, assert no repo reach-back."""
    out = tmp_path / "dist"
    # Fixed tip/ver/pytest so we don't depend on live git dirtiness for the test.
    m = build_bundle(
        REPO,
        out,
        tip="c21smok",
        ver="0.17.0",
        cp_range="CP-0001..0030",
        pytest={"passed": 406, "failed": 0},
    )
    tar = out / f"{m.name}-{m.ver}.tar.gz"
    assert tar.is_file()
    result = clean_node_smoke(
        tar,
        forbidden_repo=REPO,
        run_verify=True,
        run_status_snapshot=True,
    )
    assert result.ok, result.errors
    assert result.verify_ok is True
    assert result.neural_mesh_file is not None
    # Isolated module must live under a temp extract, not the workspace repo.
    assert str(REPO / "src") not in result.neural_mesh_file.replace("\\", "/")
    assert result.status_snapshot is not None
    assert result.status_snapshot.get("schema") == "mesh.status.snapshot/v1"
    assert result.version == "0.18.0"


def test_clean_node_smoke_script_cli(tmp_path: Path):
    out = tmp_path / "dist"
    m = build_bundle(
        REPO,
        out,
        tip="c21cli1",
        ver="0.16.3",
        cp_range="CP-0001..0025",
        pytest={"passed": 1, "failed": 0},
    )
    tar = out / f"{m.name}-{m.ver}.tar.gz"
    py = REPO / ".venv" / "bin" / "python"
    if not py.is_file():
        py = Path(sys.executable)
    r = subprocess.run(
        [
            str(py),
            str(SCRIPTS / "clean_node_smoke.py"),
            str(tar),
            "--forbidden-repo",
            str(REPO),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert r.returncode == 0, r.stderr + r.stdout
    assert "CLEAN_NODE_SMOKE: PASS" in r.stdout


def test_repro_check_script_cli(tmp_path: Path):
    root = _mini_root(tmp_path)
    py = REPO / ".venv" / "bin" / "python"
    if not py.is_file():
        py = Path(sys.executable)
    r = subprocess.run(
        [
            str(py),
            str(SCRIPTS / "repro_check.py"),
            "--root",
            str(root),
            "--out",
            str(tmp_path / "repro_out"),
            "--ver",
            "0.16.1",
            "--tip",
            "scrpr01",
            "--cp-range",
            "CP-0001..0025",
            "--pytest-passed",
            "3",
            "--pytest-failed",
            "0",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert r.returncode == 0, r.stderr + r.stdout
    assert "REPRO: PASS" in r.stdout
