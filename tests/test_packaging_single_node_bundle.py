"""Tests for Mesh Packaging: Single-Node Bundle (CP-0024 / Cycle 20).

Marker / keyword: packaging_single_node_bundle
PYTEST_MIN: ≥10
"""

from __future__ import annotations

import json
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest

from neural_mesh.packaging import (
    SCHEMA_ID,
    BundleManifest,
    PytestSummary,
    build_bundle,
    collect_bundle_files,
    load_manifest,
    manifest_to_dict,
    manifest_to_json,
    sha256_bytes,
    sha256_file,
    verify_bundle,
)
from neural_mesh.packaging.bundle import ARCHIVE_ROOT, FIXED_MTIME
from neural_mesh.packaging.manifest import BundleManifest as BM

pytestmark = pytest.mark.packaging_single_node_bundle

REPO = Path(__file__).resolve().parents[1]
SCRIPTS = REPO / "scripts"


def _mini_root(tmp_path: Path, *, ver: str = "0.16.0") -> Path:
    """Create a minimal repo layout suitable for bundling."""
    root = tmp_path / "repo"
    (root / "src" / "neural_mesh").mkdir(parents=True)
    (root / "src" / "neural_mesh" / "__init__.py").write_text(
        f'__version__ = "{ver}"\n', encoding="utf-8"
    )
    (root / "src" / "neural_mesh" / "cli.py").write_text(
        "def main():\n    print('mesh')\n", encoding="utf-8"
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
    (root / "scripts" / "build_bundle.py").write_text("# stub\n", encoding="utf-8")
    (root / "scripts" / "verify_bundle.py").write_text("# stub\n", encoding="utf-8")
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
                "last_checkpoint": "CP-0024",
                "project_version": ver,
                "test_summary": {"passed": 396, "failed": 0},
                "status": "VERIFIED",
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    # snapshots for cp_range detection
    (root / "snapshots" / "CP-0023").mkdir(parents=True)
    (root / "snapshots" / "CP-0024").mkdir(parents=True)
    # noise that must be excluded
    (root / ".venv").mkdir()
    (root / ".venv" / "x").write_text("nope", encoding="utf-8")
    (root / "src" / "neural_mesh" / "__pycache__").mkdir()
    (root / "src" / "neural_mesh" / "__pycache__" / "cli.cpython-313.pyc").write_bytes(
        b"\0"
    )
    (root / "experiments").mkdir()
    (root / "experiments" / "big.bin").write_bytes(b"x" * 1000)
    return root


# --- unit: schema -----------------------------------------------------------


def test_manifest_schema_id_and_required_fields():
    m = BundleManifest(
        name="neural-mesh-gia-single-node",
        ver="0.16.0",
        tip="abc1234",
        cp_range="CP-0001..0024",
        pytest=PytestSummary(passed=396, failed=0),
        entrypoint="mesh",
        checksums={"bundle.tar.gz": "0" * 64},
    )
    d = manifest_to_dict(m)
    assert d["schema"] == SCHEMA_ID
    for key in ("name", "ver", "tip", "cp_range", "pytest", "entrypoint", "checksums"):
        assert key in d
    assert d["pytest"] == {"passed": 396, "failed": 0}
    raw = manifest_to_json(m)
    assert '"schema": "mesh.bundle.manifest/v1"' in raw
    # roundtrip
    m2 = BundleManifest.model_validate(json.loads(raw))
    assert m2.name == m.name and m2.ver == m.ver


def test_manifest_rejects_unknown_fields():
    with pytest.raises(Exception):
        BM.model_validate(
            {
                "schema": SCHEMA_ID,
                "name": "n",
                "ver": "0.16.0",
                "cp_range": "CP-0001..0024",
                "pytest": {"passed": 0, "failed": 0},
                "entrypoint": "mesh",
                "checksums": {},
                "evil_extra": True,
            }
        )


def test_sha256_helpers_stable():
    assert sha256_bytes(b"abc") == sha256_bytes(b"abc")
    assert len(sha256_bytes(b"abc")) == 64


def test_collect_excludes_venv_pycache_experiments(tmp_path: Path):
    root = _mini_root(tmp_path)
    files = collect_bundle_files(root)
    rels = [str(p.relative_to(root)).replace("\\", "/") for p in files]
    assert "pyproject.toml" in rels
    assert "src/neural_mesh/__init__.py" in rels
    assert all(".venv" not in r for r in rels)
    assert all("__pycache__" not in r for r in rels)
    assert all(not r.startswith("experiments/") for r in rels)
    assert all(not r.startswith("snapshots/") for r in rels)


# --- integration: build / verify / determinism ------------------------------


def test_build_bundle_produces_tar_and_manifest(tmp_path: Path):
    root = _mini_root(tmp_path)
    out = tmp_path / "dist"
    m = build_bundle(root, out, tip="deadbee", ver="0.16.0")
    assert m.schema_name == SCHEMA_ID
    assert m.ver == "0.16.0"
    assert m.tip == "deadbee"
    assert m.cp_range.startswith("CP-0001..")
    assert m.entrypoint == "mesh"
    assert "bundle.tar.gz" in m.checksums
    tar = out / f"{m.name}-{m.ver}.tar.gz"
    man = out / f"{m.name}-{m.ver}.manifest.json"
    assert tar.is_file() and man.is_file()
    assert m.bundle_sha256 == sha256_file(tar)
    loaded = load_manifest(man)
    assert loaded.bundle_sha256 == m.bundle_sha256


def test_build_bundle_deterministic_same_checksum(tmp_path: Path):
    root = _mini_root(tmp_path)
    out1 = tmp_path / "d1"
    out2 = tmp_path / "d2"
    m1 = build_bundle(root, out1, tip="fixed01", ver="0.16.0", cp_range="CP-0001..0024")
    m2 = build_bundle(root, out2, tip="fixed01", ver="0.16.0", cp_range="CP-0001..0024")
    assert m1.bundle_sha256 == m2.bundle_sha256
    assert sha256_file(out1 / f"{m1.name}-{m1.ver}.tar.gz") == sha256_file(
        out2 / f"{m2.name}-{m2.ver}.tar.gz"
    )
    # manifests equal when tip/ver/cp fixed
    assert manifest_to_json(m1) == manifest_to_json(m2)


def test_verify_bundle_clean_roundtrip(tmp_path: Path):
    root = _mini_root(tmp_path)
    out = tmp_path / "dist"
    m = build_bundle(root, out, tip="cafebabe"[:7], ver="0.16.0")
    tar = out / f"{m.name}-{m.ver}.tar.gz"
    man = out / f"{m.name}-{m.ver}.manifest.json"
    result = verify_bundle(tar, man, smoke=True, expected_ver="0.16.0")
    assert result.ok, result.errors
    assert result.smoke_ok is True
    assert result.manifest is not None
    assert result.manifest.name == m.name


def test_verify_detects_tampered_member(tmp_path: Path):
    root = _mini_root(tmp_path)
    out = tmp_path / "dist"
    m = build_bundle(root, out, tip="tamper0", ver="0.16.0")
    tar = out / f"{m.name}-{m.ver}.tar.gz"
    man = out / f"{m.name}-{m.ver}.manifest.json"
    # Flip checksum entry to force failure without rewriting tar.
    data = json.loads(man.read_text(encoding="utf-8"))
    # pick a file key
    file_keys = [k for k in data["checksums"] if k not in {"bundle.tar.gz", "manifest.json"}]
    assert file_keys
    data["checksums"][file_keys[0]] = "ff" * 32
    man.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    result = verify_bundle(tar, man, smoke=False)
    assert not result.ok
    assert any("checksum mismatch" in e for e in result.errors)


def test_verify_detects_bundle_checksum_mismatch(tmp_path: Path):
    root = _mini_root(tmp_path)
    out = tmp_path / "dist"
    m = build_bundle(root, out, tip="badbund", ver="0.16.0")
    tar = out / f"{m.name}-{m.ver}.tar.gz"
    man = out / f"{m.name}-{m.ver}.manifest.json"
    data = json.loads(man.read_text(encoding="utf-8"))
    data["bundle_sha256"] = "aa" * 32
    data["checksums"]["bundle.tar.gz"] = "aa" * 32
    man.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    result = verify_bundle(tar, man, smoke=False)
    assert not result.ok
    assert any("bundle checksum mismatch" in e for e in result.errors)


def test_golden_manifest_fixture_fields(tmp_path: Path):
    """Golden: fixed tip/ver produce stable known field set."""
    root = _mini_root(tmp_path, ver="0.16.0")
    out = tmp_path / "dist"
    m = build_bundle(
        root,
        out,
        tip="GOLDENT",
        ver="0.16.0",
        cp_range="CP-0001..0024",
        pytest={"passed": 396, "failed": 0},
    )
    d = manifest_to_dict(m)
    assert d["schema"] == "mesh.bundle.manifest/v1"
    assert d["name"] == "neural-mesh-gia-single-node"
    assert d["ver"] == "0.16.0"
    assert d["tip"] == "GOLDENT"
    assert d["cp_range"] == "CP-0001..0024"
    assert d["pytest"] == {"passed": 396, "failed": 0}
    assert d["entrypoint"] == "mesh"
    assert isinstance(d["checksums"], dict) and "bundle.tar.gz" in d["checksums"]
    assert d["created_utc"] == "1970-01-01T00:00:00+00:00"
    assert FIXED_MTIME == 0
    assert ARCHIVE_ROOT == "neural-mesh-gia"
    # CP-0025 additive freeze (default on)
    assert d.get("freeze") == {
        "channel": "0.16.x",
        "schema": "mesh.bundle.manifest/v1",
    }


def test_scripts_build_and_verify_cli(tmp_path: Path):
    """CLI scripts (DeepSeek names) build+verify against mini root."""
    root = _mini_root(tmp_path)
    out = tmp_path / "dist"
    py = REPO / ".venv" / "bin" / "python"
    if not py.is_file():
        py = Path(sys.executable)
    build = SCRIPTS / "build_bundle.py"
    verify = SCRIPTS / "verify_bundle.py"
    assert build.is_file() and verify.is_file()
    r1 = subprocess.run(
        [
            str(py),
            str(build),
            "--root",
            str(root),
            "--out",
            str(out),
            "--ver",
            "0.16.0",
            "--tip",
            "cli0001",
            "--cp-range",
            "CP-0001..0024",
            "--pytest-passed",
            "10",
            "--pytest-failed",
            "0",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert r1.returncode == 0, r1.stderr + r1.stdout
    tar = out / "neural-mesh-gia-single-node-0.16.0.tar.gz"
    assert tar.is_file()
    r2 = subprocess.run(
        [
            str(py),
            str(verify),
            str(tar),
            "--expected-ver",
            "0.16.0",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert r2.returncode == 0, r2.stderr + r2.stdout
    assert "VERIFY: PASS" in r2.stdout


def test_repo_version_is_0162_when_installed():
    """Package version bump gate for CP-0026 (0.16.2 patch on 0.16.1)."""
    import neural_mesh

    # Allow running mid-implement; assert file source of truth.
    init = (REPO / "src" / "neural_mesh" / "__init__.py").read_text(encoding="utf-8")
    pyproject = (REPO / "pyproject.toml").read_text(encoding="utf-8")
    assert 'version = "0.16.2"' in pyproject or "version = '0.16.2'" in pyproject
    assert '__version__ = "0.16.2"' in init
    # If already imported older, still check file; prefer live if matches.
    if hasattr(neural_mesh, "__version__"):
        # May be stale if module imported before bump in same session — file is SoT.
        assert neural_mesh.__version__ in {"0.15.0", "0.16.0", "0.16.1", "0.16.2"}
