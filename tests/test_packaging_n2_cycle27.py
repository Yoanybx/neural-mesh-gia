"""Tests for Cycle 27 / CP-0031: N=2 multi-node packaging (P27–P29).

Markers: packaging_n2, packaging_single_node_bundle
Aim: ≥12 new tests.
"""

from __future__ import annotations

import json
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest

from neural_mesh import __version__
from neural_mesh.packaging import (
    SCHEMA_ID,
    SCHEMA_ID_N2,
    SCHEMA_ID_SINGLE_FROZEN,
    DEFAULT_BUNDLE_NAME_N2,
    FREEZE_CHANNEL_N2,
    MAJORITY_FENCED,
    ROLES_N2,
    build_bundle,
    build_n2_bundle,
    collect_n2_bundle_files,
    core_parity_checksums,
    load_n2_manifest,
    n2_install_dual,
    n2_install_rollback_smoke,
    n2_manifest_to_dict,
    n2_manifest_to_json,
    read_n2_install_marker,
    replica_status_mock,
    verify_n2_bundle,
)
from neural_mesh.packaging.manifest_n2 import (
    N2BundleManifest,
    N2EntrypointPair,
    N2FreezeInfo,
)

pytestmark = [
    pytest.mark.packaging_n2,
    pytest.mark.packaging_single_node_bundle,
]

REPO = Path(__file__).resolve().parents[1]
SCRIPTS = REPO / "scripts"


def _mini_n2_root(tmp_path: Path, *, ver: str = "0.17.0") -> Path:
    """Minimal repo layout with single-node + N2 extras for bundling."""
    root = tmp_path / f"repo-n2-{ver.replace('+', '_')}"
    (root / "src" / "neural_mesh" / "packaging" / "n2_stub_configs").mkdir(parents=True)
    (root / "src" / "neural_mesh" / "__init__.py").write_text(
        f'__version__ = "{ver}"\n', encoding="utf-8"
    )
    (root / "src" / "neural_mesh" / "cli.py").write_text(
        "def main(argv=None):\n"
        "    import sys\n"
        "    argv = list(sys.argv[1:] if argv is None else argv)\n"
        "    if not argv or argv[0] in ('--help', '-h'):\n"
        "        print('usage: mesh')\n"
        "        return 0\n"
        "    print('mesh', argv)\n"
        "    return 0\n",
        encoding="utf-8",
    )
    (root / "src" / "neural_mesh" / "packaging" / "__init__.py").write_text(
        "# packaging stub\n", encoding="utf-8"
    )
    for name, role, peer in (
        ("node_a_primary.json", "primary", "node-b"),
        ("node_b_secondary.json", "secondary", "node-a"),
    ):
        (root / "src" / "neural_mesh" / "packaging" / "n2_stub_configs" / name).write_text(
            json.dumps(
                {
                    "schema": "mesh.n2.node_stub/v1",
                    "node_id": name.split("_")[1] if False else name[:6],
                    "role": role,
                    "topology": "n2",
                    "peer": peer,
                    "dual_primary": 0,
                    "majority": "fenced_primary_heal",
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
    (root / "src" / "neural_mesh" / "packaging" / "n2_stub_configs" / "__init__.py").write_text(
        "STUB_DIR = None\n", encoding="utf-8"
    )
    # N2 packaging modules (stubs so collect finds them)
    for mod in ("manifest_n2.py", "bundle_n2.py", "n2_install.py"):
        (root / "src" / "neural_mesh" / "packaging" / mod).write_text(
            f"# stub {mod}\n", encoding="utf-8"
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
    for s in (
        "build_bundle.py",
        "verify_bundle.py",
        "build_n2_bundle.py",
        "verify_n2_bundle.py",
        "n2_install_rollback_smoke.py",
        "audit.sh",
        "bootstrap.sh",
    ):
        content = "#!/bin/sh\necho ok\n" if s.endswith(".sh") else "# stub\n"
        (root / "scripts" / s).write_text(content, encoding="utf-8")

    debt = root / "docs" / "debt"
    debt.mkdir(parents=True)
    (debt / "CHECKPOINT_EVERY_FLOOR.md").write_text(
        "# debt\nStatus: SCHEMA-GATED\n", encoding="utf-8"
    )
    cap = root / "docs" / "capabilities"
    cap.mkdir(parents=True)
    (cap / "MESH_PACKAGING_SINGLE_NODE_BUNDLE.md").write_text("# sn\n", encoding="utf-8")
    (cap / "MESH_PACKAGING_N2_MULTI_NODE.md").write_text(
        "# N2\nmajority = fenced primary/heal NOT Raft\ndual_primary must remain 0\n",
        encoding="utf-8",
    )
    for doc in (
        "phase5_replication_n2.md",
        "cram_replica_n2_interface.md",
        "cram_replica_n2_consistency.md",
        "cram_replica_oop_transport.md",
    ):
        (root / "docs" / doc).write_text(f"# {doc}\n", encoding="utf-8")

    state = root / ".project_state"
    state.mkdir()
    (state / "CHECKPOINT.json").write_text(
        json.dumps(
            {
                "last_checkpoint": "CP-0031",
                "project_version": ver,
                "test_summary": {"passed": 489, "failed": 0},
                "status": "VERIFIED",
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    (root / "snapshots" / "CP-0030").mkdir(parents=True)
    (root / "snapshots" / "CP-0031").mkdir(parents=True)
    (root / ".venv").mkdir()
    (root / ".venv" / "x").write_text("nope", encoding="utf-8")
    return root


# --- P27 design --------------------------------------------------------------


def test_n2_design_doc_present_and_bounds():
    path = REPO / "docs" / "capabilities" / "MESH_PACKAGING_N2_MULTI_NODE.md"
    assert path.is_file()
    text = path.read_text(encoding="utf-8")
    assert "mesh.bundle.manifest/v1-n2" in text
    assert "neural-mesh-gia-n2" in text
    assert "topology" in text.lower() and "n2" in text
    assert "primary" in text and "secondary" in text
    assert "fenced" in text.lower() or "fenced_primary_heal" in text
    assert "NOT Raft" in text or "not Raft" in text.lower() or "NOT Raft" in text
    assert "dual_primary" in text
    assert "0" in text
    assert "Raft" in text
    assert "N>2" in text or "N>2" in text
    # must not claim Raft as majority
    assert "majority = Raft" not in text


def test_n2_schema_distinct_from_frozen_v1():
    assert SCHEMA_ID_N2 == "mesh.bundle.manifest/v1-n2"
    assert SCHEMA_ID_SINGLE_FROZEN == SCHEMA_ID == "mesh.bundle.manifest/v1"
    assert SCHEMA_ID_N2 != SCHEMA_ID


# --- P28 manifest + build/verify --------------------------------------------


def test_n2_manifest_golden_fields():
    m = N2BundleManifest(
        name=DEFAULT_BUNDLE_NAME_N2,
        ver="0.17.0",
        tip="abc1234",
        cp_range="CP-0001..0031",
        topology="n2",
        roles=list(ROLES_N2),
        entrypoint=N2EntrypointPair(primary="mesh", secondary="mesh"),
        dual_primary=0,
        majority=MAJORITY_FENCED,
        checksums={"bundle.tar.gz": "0" * 64},
        freeze=N2FreezeInfo(),
    )
    d = n2_manifest_to_dict(m)
    assert d["schema"] == SCHEMA_ID_N2
    assert d["topology"] == "n2"
    assert d["roles"] == ["primary", "secondary"]
    assert d["entrypoint"] == {"primary": "mesh", "secondary": "mesh"}
    assert d["dual_primary"] == 0
    assert d["majority"] == MAJORITY_FENCED
    assert d["freeze"]["schema"] == SCHEMA_ID_N2
    assert d["freeze"]["single_node_schema_frozen"] == SCHEMA_ID
    raw = n2_manifest_to_json(m)
    assert SCHEMA_ID_N2 in raw
    m2 = N2BundleManifest.model_validate(json.loads(raw))
    assert m2.dual_primary == 0


def test_n2_manifest_rejects_dual_primary_and_raft():
    with pytest.raises(Exception):
        N2BundleManifest(
            name="x",
            ver="0.17.0",
            cp_range="CP-0001..0031",
            dual_primary=1,
        )
    with pytest.raises(Exception):
        N2BundleManifest(
            name="x",
            ver="0.17.0",
            cp_range="CP-0001..0031",
            majority="raft_quorum",
        )
    with pytest.raises(Exception):
        N2BundleManifest(
            name="x",
            ver="0.17.0",
            cp_range="CP-0001..0031",
            topology="n3",  # type: ignore[arg-type]
        )


def test_n2_build_determinism(tmp_path: Path):
    root = _mini_n2_root(tmp_path)
    out = tmp_path / "out"
    kwargs = dict(
        ver="0.17.0",
        tip="deadbee",
        cp_range="CP-0001..0031",
        pytest={"passed": 10, "failed": 0},
        single_node_for_parity=False,
    )
    a = build_n2_bundle(root, out / "a", **kwargs)
    b = build_n2_bundle(root, out / "b", **kwargs)
    assert a.bundle_sha256 == b.bundle_sha256
    assert a.checksums == b.checksums
    assert a.schema_name == SCHEMA_ID_N2
    assert a.dual_primary == 0
    assert a.topology == "n2"


def test_n2_verify_ok_and_schema(tmp_path: Path):
    root = _mini_n2_root(tmp_path)
    out = tmp_path / "out"
    m = build_n2_bundle(
        root,
        out,
        ver="0.17.0",
        tip="cafe000",
        cp_range="CP-0001..0031",
        single_node_for_parity=False,
    )
    bundle = out / f"{m.name}-{m.ver}.tar.gz"
    man = out / f"{m.name}-{m.ver}.manifest.json"
    result = verify_n2_bundle(bundle, man, smoke=True, expected_ver="0.17.0")
    assert result.ok, result.errors
    assert result.smoke_ok is True
    assert result.manifest is not None
    assert result.manifest.schema_name == SCHEMA_ID_N2
    assert result.manifest.dual_primary == 0


def test_n2_parity_with_single_node_core_hashes(tmp_path: Path):
    root = _mini_n2_root(tmp_path)
    out = tmp_path / "out"
    tip, ver, cp = "parity01", "0.17.0", "CP-0001..0031"
    n2 = build_n2_bundle(
        root,
        out / "n2",
        ver=ver,
        tip=tip,
        cp_range=cp,
        pytest={"passed": 1, "failed": 0},
        single_node_for_parity=False,
    )
    single = build_bundle(
        root,
        out / "single",
        ver=ver,
        tip=tip,
        cp_range=cp,
        pytest={"passed": 1, "failed": 0},
    )
    ok, errs = core_parity_checksums(n2.checksums, single.checksums)
    assert ok, errs
    # N2 must list extras not in single-node
    assert any("n2_stub_configs" in x or "phase5_replication" in x for x in n2.n2_extras)
    assert n2.schema_name != single.schema_name
    # verify with single manifest path
    bundle = out / "n2" / f"{n2.name}-{n2.ver}.tar.gz"
    man = out / "n2" / f"{n2.name}-{n2.ver}.manifest.json"
    single_man = out / "single" / f"{single.name}-{single.ver}.manifest.json"
    vr = verify_n2_bundle(
        bundle, man, smoke=False, single_manifest_path=single_man
    )
    assert vr.ok, vr.errors
    assert vr.parity_ok is True


def test_n2_extras_listed_and_collected(tmp_path: Path):
    root = _mini_n2_root(tmp_path)
    files = collect_n2_bundle_files(root)
    rels = [str(p.relative_to(root)).replace("\\", "/") for p in files]
    assert any("node_a_primary.json" in r for r in rels)
    assert any("MESH_PACKAGING_N2_MULTI_NODE.md" in r for r in rels)
    assert any("phase5_replication_n2.md" in r for r in rels)
    assert not any(".venv" in r for r in rels)


# --- P29 install / rollback --------------------------------------------------


def test_n2_install_dual_smoke(tmp_path: Path):
    root = _mini_n2_root(tmp_path)
    out = tmp_path / "dist"
    m = build_n2_bundle(
        root,
        out,
        ver="0.17.0",
        tip="inst001",
        cp_range="CP-0001..0031",
        single_node_for_parity=False,
    )
    bundle = out / f"{m.name}-{m.ver}.tar.gz"
    prefix = tmp_path / "prefixes"
    result = n2_install_dual(bundle, prefix, run_replica_mock=True)
    assert result.ok, result.errors
    assert result.dual_primary == 0
    assert result.schema == SCHEMA_ID_N2
    assert Path(result.prefix_a).is_dir()
    assert Path(result.prefix_b).is_dir()
    assert (Path(result.prefix_a) / "INSTALL_N2.json").is_file()
    assert (Path(result.prefix_b) / "config").is_dir()
    assert result.replica_mock_a and result.replica_mock_a["mock"] is True
    assert result.replica_mock_a["out_of_band_serve"] is True
    ma = read_n2_install_marker(result.prefix_a)
    mb = read_n2_install_marker(result.prefix_b)
    assert ma["role"] == "primary" and mb["role"] == "secondary"
    assert ma["ver"] == "0.17.0"


def test_n2_rollback_one_node_restore(tmp_path: Path):
    root = _mini_n2_root(tmp_path, ver="0.17.0")
    out = tmp_path / "dist"
    prior = build_n2_bundle(
        root,
        out,
        ver="0.17.0",
        tip="prior01",
        cp_range="CP-0001..0031",
        single_node_for_parity=False,
    )
    # new uses distinct ver for clear marker rollback
    root_b = _mini_n2_root(tmp_path / "b", ver="0.17.0+n2b")
    newer = build_n2_bundle(
        root_b,
        out,
        ver="0.17.0+n2b",
        tip="new0001",
        cp_range="CP-0001..0031",
        single_node_for_parity=False,
    )
    bundle_a = out / f"{prior.name}-{prior.ver}.tar.gz"
    bundle_b = out / f"{newer.name}-{newer.ver}.tar.gz"
    result = n2_install_rollback_smoke(
        bundle_a,
        bundle_b,
        tmp_path / "rb",
        roll_node="node-a",
        expect_ver_prior="0.17.0",
    )
    assert result.ok, result.errors
    assert result.ver_before == "0.17.0+n2b"
    assert result.ver_after == "0.17.0"
    assert result.rolled_node == "node-a"
    # peer (node-b) still on new
    peer = read_n2_install_marker(result.prefix_b)
    assert peer.get("ver") == "0.17.0+n2b"


def test_replica_status_mock_fields():
    mock = replica_status_mock(role="primary", node_id="node-a", peer="node-b")
    assert mock["dual_primary"] == 0
    assert mock["topology"] == "n2"
    assert mock["majority"] == MAJORITY_FENCED
    assert mock["out_of_band_serve"] is True


# --- scripts + version / council wiring --------------------------------------


def test_n2_scripts_help():
    for name in ("build_n2_bundle.py", "verify_n2_bundle.py", "n2_install_rollback_smoke.py"):
        script = SCRIPTS / name
        assert script.is_file()
        proc = subprocess.run(
            [sys.executable, str(script), "--help"],
            cwd=str(REPO),
            capture_output=True,
            text=True,
            check=False,
        )
        assert proc.returncode == 0, proc.stderr


def test_package_version_stays_0170_and_stub_configs_exist():
    assert __version__ == "0.18.0"
    stub_dir = REPO / "src" / "neural_mesh" / "packaging" / "n2_stub_configs"
    assert (stub_dir / "node_a_primary.json").is_file()
    assert (stub_dir / "node_b_secondary.json").is_file()
    a = json.loads((stub_dir / "node_a_primary.json").read_text(encoding="utf-8"))
    b = json.loads((stub_dir / "node_b_secondary.json").read_text(encoding="utf-8"))
    assert a["role"] == "primary" and b["role"] == "secondary"
    assert a["dual_primary"] == 0 and b["dual_primary"] == 0
    assert a["majority"] == MAJORITY_FENCED


def test_load_n2_manifest_roundtrip(tmp_path: Path):
    root = _mini_n2_root(tmp_path)
    out = tmp_path / "out"
    m = build_n2_bundle(
        root,
        out,
        ver="0.17.0",
        tip="round01",
        cp_range="CP-0001..0031",
        single_node_for_parity=False,
    )
    path = out / f"{m.name}-{m.ver}.manifest.json"
    loaded = load_n2_manifest(path)
    assert loaded.name == DEFAULT_BUNDLE_NAME_N2
    assert loaded.freeze is not None
    assert loaded.freeze.channel == FREEZE_CHANNEL_N2
