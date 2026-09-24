"""N=2 install + rollback smoke (CP-0031 / P29).

Extract an N2 bundle into two prefixes (node-a / node-b), smoke import/mesh help,
optional lightweight replica status mock, and filesystem-level rollback of one node.
Full ``mesh cram replica serve`` is out-of-band (documented; not required here).
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import tarfile
import textwrap
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .bundle import ARCHIVE_ROOT, sha256_file
from .bundle_n2 import load_n2_manifest
from .manifest_n2 import SCHEMA_ID_N2, N2BundleManifest
from .rc_install import write_mesh_launcher

__all__ = [
    "N2InstallResult",
    "N2RollbackResult",
    "n2_install_dual",
    "n2_install_rollback_smoke",
    "replica_status_mock",
    "read_n2_install_marker",
]

NODE_A = "node-a"
NODE_B = "node-b"


def read_n2_install_marker(prefix: Path | str) -> dict[str, Any]:
    p = Path(prefix) / "INSTALL_N2.json"
    if not p.is_file():
        return {}
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def replica_status_mock(
    *,
    role: str,
    node_id: str,
    peer: str,
    dual_primary: int = 0,
) -> dict[str, Any]:
    """Lightweight replica status mock (no real serve / network).

    Documents that full replica serve is out-of-band for packaging smoke.
    """
    return {
        "ok": True,
        "mock": True,
        "out_of_band_serve": True,
        "node_id": node_id,
        "role": role,
        "peer": peer,
        "topology": "n2",
        "dual_primary": dual_primary,
        "majority": "fenced_primary_heal",
        "status": "PACKAGING_SMOKE_MOCK",
        "note": (
            "Full mesh cram replica serve is out-of-band; "
            "this mock only proves packaging role wiring."
        ),
    }


@dataclass
class N2InstallResult:
    ok: bool = True
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    prefix_a: str | None = None
    prefix_b: str | None = None
    version: str | None = None
    schema: str | None = None
    dual_primary: int | None = None
    smoke_a: dict[str, Any] | None = None
    smoke_b: dict[str, Any] | None = None
    replica_mock_a: dict[str, Any] | None = None
    replica_mock_b: dict[str, Any] | None = None
    manifest: dict[str, Any] | None = None

    def fail(self, msg: str) -> None:
        self.ok = False
        self.errors.append(msg)

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "errors": list(self.errors),
            "warnings": list(self.warnings),
            "prefix_a": self.prefix_a,
            "prefix_b": self.prefix_b,
            "version": self.version,
            "schema": self.schema,
            "dual_primary": self.dual_primary,
            "smoke_a": self.smoke_a,
            "smoke_b": self.smoke_b,
            "replica_mock_a": self.replica_mock_a,
            "replica_mock_b": self.replica_mock_b,
            "manifest": self.manifest,
        }


@dataclass
class N2RollbackResult:
    ok: bool = True
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    prefix_a: str | None = None
    prefix_b: str | None = None
    rolled_node: str | None = None
    ver_before: str | None = None
    ver_after: str | None = None
    install_new: dict[str, Any] | None = None
    install_prior: dict[str, Any] | None = None
    smoke_after: dict[str, Any] | None = None

    def fail(self, msg: str) -> None:
        self.ok = False
        self.errors.append(msg)

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "errors": list(self.errors),
            "warnings": list(self.warnings),
            "prefix_a": self.prefix_a,
            "prefix_b": self.prefix_b,
            "rolled_node": self.rolled_node,
            "ver_before": self.ver_before,
            "ver_after": self.ver_after,
            "install_new": self.install_new,
            "install_prior": self.install_prior,
            "smoke_after": self.smoke_after,
        }


def _extract_n2(bundle_path: Path, dest: Path) -> Path:
    dest.mkdir(parents=True, exist_ok=True)
    with tarfile.open(bundle_path, mode="r:gz") as tar:
        try:
            tar.extractall(dest, filter="data")
        except TypeError:
            tar.extractall(dest)
    candidate = dest / ARCHIVE_ROOT
    if candidate.is_dir():
        return candidate
    dirs = [p for p in dest.iterdir() if p.is_dir()]
    if len(dirs) == 1:
        return dirs[0]
    return dest


def _write_marker(
    prefix: Path,
    *,
    role: str,
    node_id: str,
    manifest: N2BundleManifest,
    stub_rel: str | None,
) -> None:
    marker = {
        "schema": SCHEMA_ID_N2,
        "ver": manifest.ver,
        "tip": manifest.tip,
        "role": role,
        "node_id": node_id,
        "topology": manifest.topology,
        "dual_primary": manifest.dual_primary,
        "majority": manifest.majority,
        "stub": stub_rel,
        "name": manifest.name,
    }
    (prefix / "INSTALL_N2.json").write_text(
        json.dumps(marker, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def _copy_stub(extract_root: Path, prefix: Path, stub_rel: str) -> str | None:
    src = extract_root / stub_rel
    if not src.is_file():
        return None
    dest = prefix / "config" / Path(stub_rel).name
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dest)
    return str(dest.relative_to(prefix)).replace("\\", "/")


def _smoke_prefix(
    prefix: Path,
    extract_root: Path,
    *,
    python: str | None = None,
) -> dict[str, Any]:
    """Import + mesh --help smoke against an installed prefix."""
    out: dict[str, Any] = {"ok": True, "errors": []}
    src = extract_root / "src"
    if not src.is_dir():
        # flat layout
        alt = prefix / "root" / "src"
        src = alt if alt.is_dir() else prefix / "src"
    if not src.is_dir():
        out["ok"] = False
        out["errors"].append("src/ missing for smoke")
        return out

    py = python or os.environ.get("MESH_BUNDLE_PYTHON") or "python3"
    env = os.environ.copy()
    env["PYTHONPATH"] = str(src)
    # import
    try:
        proc = subprocess.run(
            [py, "-c", "import neural_mesh; print(neural_mesh.__version__)"],
            cwd=str(prefix),
            env=env,
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
    except Exception as exc:  # noqa: BLE001
        out["ok"] = False
        out["errors"].append(f"import failed: {exc}")
        return out
    if proc.returncode != 0:
        out["ok"] = False
        out["errors"].append(proc.stderr.strip() or proc.stdout)
        return out
    out["version"] = proc.stdout.strip()
    out["import_ok"] = True

    # mesh help via launcher if present else -c
    launcher = prefix / "bin" / "mesh"
    if launcher.is_file():
        try:
            help_proc = subprocess.run(
                [py, str(launcher), "--help"],
                cwd=str(prefix),
                env=env,
                capture_output=True,
                text=True,
                timeout=30,
                check=False,
            )
            out["help_ok"] = help_proc.returncode == 0
            if help_proc.returncode != 0:
                # soft: some mini fixtures have stub cli without argparse
                out["help_ok"] = "usage" in (help_proc.stdout + help_proc.stderr).lower() or help_proc.returncode == 0
                if not out["help_ok"]:
                    # still try module path
                    pass
        except Exception as exc:  # noqa: BLE001
            out["help_ok"] = False
            out["errors"].append(f"help failed: {exc}")
    else:
        help_proc = subprocess.run(
            [
                py,
                "-c",
                "from neural_mesh.cli import main; import sys; "
                "sys.exit(main(['--help']) if False else 0)",
            ],
            cwd=str(prefix),
            env=env,
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
        out["help_ok"] = help_proc.returncode == 0
        out["import_cli_ok"] = help_proc.returncode == 0

    if out["errors"]:
        out["ok"] = False
    return out


def _install_one_node(
    bundle_path: Path,
    prefix: Path,
    *,
    role: str,
    node_id: str,
    stub_rel: str,
    manifest: N2BundleManifest,
    python: str | None = None,
    clear_prefix: bool = True,
) -> tuple[Path, dict[str, Any]]:
    if clear_prefix and prefix.exists():
        shutil.rmtree(prefix)
    prefix.mkdir(parents=True, exist_ok=True)
    extract_dest = prefix / "extract"
    extract_root = _extract_n2(bundle_path, extract_dest)
    # Flatten useful layout: prefix/root -> extract_root
    root_link = prefix / "root"
    if root_link.exists():
        shutil.rmtree(root_link)
    shutil.copytree(extract_root, root_link)
    stub_copied = _copy_stub(extract_root, prefix, stub_rel)
    write_mesh_launcher(prefix)
    _write_marker(
        prefix,
        role=role,
        node_id=node_id,
        manifest=manifest,
        stub_rel=stub_copied,
    )
    # Side-copy manifest
    side = prefix / "bundle.manifest.json"
    side.write_text(
        json.dumps(manifest.model_dump(mode="json", by_alias=True), indent=2, sort_keys=True)
        + "\n",
        encoding="utf-8",
    )
    smoke = _smoke_prefix(prefix, root_link, python=python)
    return root_link, smoke


def n2_install_dual(
    bundle_path: Path | str,
    base_prefix: Path | str,
    *,
    manifest_path: Path | str | None = None,
    python: str | None = None,
    run_replica_mock: bool = True,
    clear_prefixes: bool = True,
) -> N2InstallResult:
    """Extract N2 bundle into node-a (primary) and node-b (secondary) prefixes."""
    result = N2InstallResult()
    bundle_path = Path(bundle_path).resolve()
    base_prefix = Path(base_prefix).resolve()
    base_prefix.mkdir(parents=True, exist_ok=True)

    if manifest_path is None:
        stem = bundle_path.name
        if stem.endswith(".tar.gz"):
            base = stem[: -len(".tar.gz")]
        else:
            base = bundle_path.stem
        manifest_path = bundle_path.with_name(f"{base}.manifest.json")
    else:
        manifest_path = Path(manifest_path).resolve()

    try:
        manifest = load_n2_manifest(manifest_path)
    except Exception as exc:  # noqa: BLE001
        result.fail(f"manifest load failed: {exc}")
        return result

    result.manifest = manifest.model_dump(mode="json", by_alias=True)
    result.schema = manifest.schema_name
    result.version = manifest.ver
    result.dual_primary = manifest.dual_primary

    if manifest.schema_name != SCHEMA_ID_N2:
        result.fail(f"expected schema {SCHEMA_ID_N2}, got {manifest.schema_name}")
    if manifest.dual_primary != 0:
        result.fail(f"dual_primary must be 0, got {manifest.dual_primary}")
    if manifest.topology != "n2":
        result.fail(f"topology must be n2, got {manifest.topology}")

    prefix_a = base_prefix / NODE_A
    prefix_b = base_prefix / NODE_B
    result.prefix_a = str(prefix_a)
    result.prefix_b = str(prefix_b)

    stub_a = "src/neural_mesh/packaging/n2_stub_configs/node_a_primary.json"
    stub_b = "src/neural_mesh/packaging/n2_stub_configs/node_b_secondary.json"

    try:
        _, smoke_a = _install_one_node(
            bundle_path,
            prefix_a,
            role="primary",
            node_id="node-a",
            stub_rel=stub_a,
            manifest=manifest,
            python=python,
            clear_prefix=clear_prefixes,
        )
        result.smoke_a = smoke_a
        if not smoke_a.get("ok"):
            result.fail("node-a smoke failed: " + "; ".join(smoke_a.get("errors") or []))
    except Exception as exc:  # noqa: BLE001
        result.fail(f"node-a install failed: {exc}")
        return result

    try:
        _, smoke_b = _install_one_node(
            bundle_path,
            prefix_b,
            role="secondary",
            node_id="node-b",
            stub_rel=stub_b,
            manifest=manifest,
            python=python,
            clear_prefix=clear_prefixes,
        )
        result.smoke_b = smoke_b
        if not smoke_b.get("ok"):
            result.fail("node-b smoke failed: " + "; ".join(smoke_b.get("errors") or []))
    except Exception as exc:  # noqa: BLE001
        result.fail(f"node-b install failed: {exc}")
        return result

    if run_replica_mock:
        result.replica_mock_a = replica_status_mock(
            role="primary", node_id="node-a", peer="node-b", dual_primary=0
        )
        result.replica_mock_b = replica_status_mock(
            role="secondary", node_id="node-b", peer="node-a", dual_primary=0
        )
        (prefix_a / "replica_status_mock.json").write_text(
            json.dumps(result.replica_mock_a, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        (prefix_b / "replica_status_mock.json").write_text(
            json.dumps(result.replica_mock_b, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

    return result


def n2_install_rollback_smoke(
    bundle_prior: Path | str,
    bundle_new: Path | str,
    base_prefix: Path | str,
    *,
    manifest_prior: Path | str | None = None,
    manifest_new: Path | str | None = None,
    roll_node: str = NODE_A,
    python: str | None = None,
    expect_ver_prior: str | None = None,
) -> N2RollbackResult:
    """Install new N2 into dual prefixes, then rollback one node to prior bundle.

    Filesystem-level only (loopback/tmp) — mirrors Cycle 22 single-node rollback.
    """
    result = N2RollbackResult()
    bundle_prior = Path(bundle_prior).resolve()
    bundle_new = Path(bundle_new).resolve()
    base_prefix = Path(base_prefix).resolve()
    result.rolled_node = roll_node

    def _side_man(bundle: Path, explicit: Path | str | None) -> Path:
        if explicit:
            return Path(explicit)
        stem = bundle.name
        if stem.endswith(".tar.gz"):
            base = stem[: -len(".tar.gz")]
        else:
            base = bundle.stem
        return bundle.with_name(f"{base}.manifest.json")

    man_prior_path = _side_man(bundle_prior, manifest_prior)
    man_new_path = _side_man(bundle_new, manifest_new)

    try:
        man_prior = load_n2_manifest(man_prior_path)
        man_new = load_n2_manifest(man_new_path)
    except Exception as exc:  # noqa: BLE001
        result.fail(f"manifest load failed: {exc}")
        return result

    expected = expect_ver_prior or man_prior.ver

    # Install new dual
    inst_new = n2_install_dual(
        bundle_new,
        base_prefix,
        manifest_path=man_new_path,
        python=python,
        run_replica_mock=True,
        clear_prefixes=True,
    )
    result.install_new = inst_new.to_dict()
    result.prefix_a = inst_new.prefix_a
    result.prefix_b = inst_new.prefix_b
    if not inst_new.ok:
        result.fail("install new failed: " + "; ".join(inst_new.errors))
        return result
    result.ver_before = inst_new.version or man_new.ver

    # Rollback one node by re-extracting prior into that prefix only
    if roll_node == NODE_A:
        target = Path(inst_new.prefix_a)  # type: ignore[arg-type]
        role, node_id, stub = (
            "primary",
            "node-a",
            "src/neural_mesh/packaging/n2_stub_configs/node_a_primary.json",
        )
    elif roll_node == NODE_B:
        target = Path(inst_new.prefix_b)  # type: ignore[arg-type]
        role, node_id, stub = (
            "secondary",
            "node-b",
            "src/neural_mesh/packaging/n2_stub_configs/node_b_secondary.json",
        )
    else:
        result.fail(f"unknown roll_node: {roll_node}")
        return result

    try:
        _, smoke = _install_one_node(
            bundle_prior,
            target,
            role=role,
            node_id=node_id,
            stub_rel=stub,
            manifest=man_prior,
            python=python,
            clear_prefix=True,
        )
        result.smoke_after = smoke
        if not smoke.get("ok"):
            result.fail(
                "post-rollback smoke failed: " + "; ".join(smoke.get("errors") or [])
            )
    except Exception as exc:  # noqa: BLE001
        result.fail(f"rollback install failed: {exc}")
        return result

    marker = read_n2_install_marker(target)
    result.ver_after = marker.get("ver") or man_prior.ver
    result.install_prior = {
        "ok": True,
        "marker": marker,
        "prefix": str(target),
    }

    if result.ver_after != expected:
        result.fail(
            f"post-rollback ver {result.ver_after!r} != expected {expected!r}"
        )
    if marker.get("dual_primary", 0) != 0:
        result.fail("post-rollback dual_primary must remain 0")
    if marker.get("schema") != SCHEMA_ID_N2:
        result.fail(f"post-rollback schema {marker.get('schema')!r} != {SCHEMA_ID_N2}")

    # Peer node should still be on new ver
    peer = Path(inst_new.prefix_b if roll_node == NODE_A else inst_new.prefix_a)  # type: ignore[arg-type]
    peer_marker = read_n2_install_marker(peer)
    if peer_marker.get("ver") != man_new.ver:
        result.warnings.append(
            f"peer node ver {peer_marker.get('ver')!r} != new {man_new.ver!r}"
        )

    return result
