"""Build and verify reproducible N=2 multi-node mesh bundles (CP-0031 / Cycle 27).

Sibling of single-node packaging. Does **not** invent Raft, N>2, or multi-primary.
"""

from __future__ import annotations

import json
import os
import subprocess
import tarfile
import tempfile
from pathlib import Path
from typing import Any, Mapping, Sequence

from .bundle import (
    ARCHIVE_ROOT,
    EXCLUDE_DIR_NAMES,
    EXCLUDE_SUFFIXES,
    FIXED_MTIME,
    INCLUDE_PATHS,
    _cp_range_from_root,
    _git_tip7,
    _load_project_state,
    _normalize_mode,
    _pytest_from_state,
    _read_pyproject_version,
    _write_deterministic_tar,
    build_bundle,
    collect_bundle_files,
    sha256_bytes,
    sha256_file,
)
from .manifest import PytestSummary
from .manifest_n2 import (
    DEFAULT_BUNDLE_NAME_N2,
    FREEZE_CHANNEL_N2,
    MAJORITY_FENCED,
    ROLES_N2,
    SCHEMA_ID_N2,
    SCHEMA_ID_SINGLE_FROZEN,
    N2BundleManifest,
    N2EntrypointPair,
    N2FreezeInfo,
    n2_manifest_to_json,
)

# N2-only paths relative to repo root (extras beyond single-node INCLUDE_PATHS).
N2_ONLY_INCLUDE: tuple[str, ...] = (
    "docs/phase5_replication_n2.md",
    "docs/cram_replica_n2_interface.md",
    "docs/cram_replica_n2_consistency.md",
    "docs/cram_replica_oop_transport.md",
    "docs/capabilities/MESH_PACKAGING_N2_MULTI_NODE.md",
    "src/neural_mesh/packaging/n2_stub_configs/node_a_primary.json",
    "src/neural_mesh/packaging/n2_stub_configs/node_b_secondary.json",
    "src/neural_mesh/packaging/n2_stub_configs/__init__.py",
    "scripts/build_n2_bundle.py",
    "scripts/verify_n2_bundle.py",
    "scripts/n2_install_rollback_smoke.py",
    "scripts/n2_rc_soak.py",
    "scripts/n2_final_release_audit.py",
    "docs/capabilities/MESH_PACKAGING_N2_FINAL_RELEASE_AUDIT.md",
)

# Also ship N2 packaging modules themselves (may already be under src/neural_mesh).
# Listed explicitly for n2_extras bookkeeping when tree is mini-fixture.
N2_PACKAGING_MODULES: tuple[str, ...] = (
    "src/neural_mesh/packaging/manifest_n2.py",
    "src/neural_mesh/packaging/bundle_n2.py",
    "src/neural_mesh/packaging/n2_install.py",
    "src/neural_mesh/packaging/n2_rc_soak.py",
    "src/neural_mesh/packaging/n2_final_release_audit.py",
)

EXECUTABLE_NAMES_N2 = {
    "build_n2_bundle.py",
    "verify_n2_bundle.py",
    "n2_install_rollback_smoke.py",
    "n2_rc_soak.py",
    "n2_final_release_audit.py",
}

# Core paths used for single-node parity (subset that always exists in mini roots).
CORE_PARITY_CANDIDATES: tuple[str, ...] = (
    "pyproject.toml",
    "src/neural_mesh/__init__.py",
)

__all__ = [
    "N2_ONLY_INCLUDE",
    "N2_PACKAGING_MODULES",
    "CORE_PARITY_CANDIDATES",
    "build_n2_bundle",
    "verify_n2_bundle",
    "collect_n2_bundle_files",
    "load_n2_manifest",
    "core_parity_checksums",
    "list_n2_extras",
    "N2VerifyResult",
]


def _should_exclude_n2(rel: Path) -> bool:
    parts = set(rel.parts)
    if parts & EXCLUDE_DIR_NAMES:
        return True
    if any(p.endswith(".egg-info") for p in rel.parts):
        return True
    if rel.suffix in EXCLUDE_SUFFIXES:
        return True
    return False


def collect_n2_bundle_files(root: Path) -> list[Path]:
    """Return sorted absolute file paths for N2 bundle (single-node + N2 extras)."""
    root = root.resolve()
    found: set[Path] = set(collect_bundle_files(root))
    for rel_s in (*N2_ONLY_INCLUDE, *N2_PACKAGING_MODULES):
        p = root / rel_s
        if not p.exists():
            continue
        if p.is_file():
            found.add(p.resolve())
            continue
        for fp in p.rglob("*"):
            if not fp.is_file():
                continue
            rel = fp.relative_to(root)
            if _should_exclude_n2(rel):
                continue
            found.add(fp.resolve())
    return sorted(found, key=lambda x: str(x.relative_to(root)).replace("\\", "/"))


def list_n2_extras(all_rels: Sequence[str], single_rels: Sequence[str]) -> list[str]:
    single_set = set(single_rels)
    return sorted(r for r in all_rels if r not in single_set)


def core_parity_checksums(
    n2_checksums: Mapping[str, str],
    single_checksums: Mapping[str, str],
    *,
    paths: Sequence[str] | None = None,
) -> tuple[bool, list[str]]:
    """Compare shared core path checksums between N2 and single-node manifests."""
    paths = list(paths) if paths is not None else list(CORE_PARITY_CANDIDATES)
    errors: list[str] = []
    for rel in paths:
        a = n2_checksums.get(rel)
        b = single_checksums.get(rel)
        if a is None or b is None:
            # Skip paths absent from either build (mini fixtures may omit some).
            continue
        if a != b:
            errors.append(f"core parity mismatch for {rel}: n2={a} single={b}")
    return (len(errors) == 0, errors)


def _normalize_mode_n2(path: Path) -> int:
    if path.suffix == ".sh" or path.name in EXECUTABLE_NAMES_N2:
        return 0o755
    return _normalize_mode(path)


def build_n2_bundle(
    root: Path | str,
    out_dir: Path | str,
    *,
    name: str = DEFAULT_BUNDLE_NAME_N2,
    ver: str | None = None,
    tip: str | None = None,
    cp_range: str | None = None,
    pytest: PytestSummary | Mapping[str, int] | None = None,
    entrypoint_primary: str = "mesh",
    entrypoint_secondary: str = "mesh",
    freeze: N2FreezeInfo | Mapping[str, str] | bool | None = True,
    single_node_for_parity: bool = True,
) -> N2BundleManifest:
    """Build a reproducible N=2 bundle tarball + manifest.json.

    Produces in ``out_dir``:
      - ``{name}-{ver}.tar.gz``
      - ``{name}-{ver}.manifest.json``
    """
    root = Path(root).resolve()
    out_dir = Path(out_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    state = _load_project_state(root)
    version = ver or _read_pyproject_version(root)
    tip_val = tip if tip is not None else _git_tip7(root)
    auto_range, cp_tip = _cp_range_from_root(root, state)
    range_val = cp_range or auto_range

    if pytest is None:
        pytest_sum = _pytest_from_state(state)
    elif isinstance(pytest, PytestSummary):
        pytest_sum = pytest
    else:
        pytest_sum = PytestSummary(
            passed=int(pytest.get("passed", 0)),
            failed=int(pytest.get("failed", 0)),
        )

    file_paths = collect_n2_bundle_files(root)
    single_paths = collect_bundle_files(root)
    single_rels = [
        str(p.relative_to(root)).replace("\\", "/") for p in single_paths
    ]

    members: list[tuple[str, bytes, int]] = []
    checksums: dict[str, str] = {}
    file_list: list[str] = []

    for fp in file_paths:
        rel = str(fp.relative_to(root)).replace("\\", "/")
        data = fp.read_bytes()
        mode = _normalize_mode_n2(fp)
        arc = f"{ARCHIVE_ROOT}/{rel}"
        members.append((arc, data, mode))
        checksums[rel] = sha256_bytes(data)
        file_list.append(rel)

    tar_name = f"{name}-{version}.tar.gz"
    man_name = f"{name}-{version}.manifest.json"
    tar_path = out_dir / tar_name
    man_path = out_dir / man_name

    bundle_sha = _write_deterministic_tar(members, tar_path)
    checksums["bundle.tar.gz"] = bundle_sha

    n2_extras = list_n2_extras(file_list, single_rels)
    core_paths = [p for p in CORE_PARITY_CANDIDATES if p in checksums]

    # P32 / CP-0032: N2 RC builds always embed freeze (omit not allowed for RC).
    if freeze is False or freeze is None:
        freeze_info = N2FreezeInfo(
            channel=FREEZE_CHANNEL_N2,
            schema_name=SCHEMA_ID_N2,
            single_node_schema_frozen=SCHEMA_ID_SINGLE_FROZEN,
        )
    elif freeze is True:
        freeze_info = N2FreezeInfo(
            channel=FREEZE_CHANNEL_N2,
            schema_name=SCHEMA_ID_N2,
            single_node_schema_frozen=SCHEMA_ID_SINGLE_FROZEN,
        )
    elif isinstance(freeze, N2FreezeInfo):
        freeze_info = freeze
    else:
        freeze_info = N2FreezeInfo(
            channel=str(freeze.get("channel", FREEZE_CHANNEL_N2)),
            schema_name=str(
                freeze.get("schema", freeze.get("schema_name", SCHEMA_ID_N2))
            ),
            single_node_schema_frozen=str(
                freeze.get(
                    "single_node_schema_frozen", SCHEMA_ID_SINGLE_FROZEN
                )
            ),
        )

    # Optional: build single-node sibling for parity bookkeeping (same overrides).
    if single_node_for_parity:
        try:
            single_man = build_bundle(
                root,
                out_dir / "_single_parity",
                ver=version,
                tip=tip_val,
                cp_range=range_val,
                pytest=pytest_sum,
                freeze=True,
            )
            ok, errs = core_parity_checksums(
                checksums, single_man.checksums, paths=core_paths
            )
            if not ok:
                # Soft: still emit manifest; verify_n2_bundle will enforce.
                pass
            _ = errs
        except Exception:  # noqa: BLE001
            pass

    manifest = N2BundleManifest(
        name=name,
        ver=version,
        tip=tip_val,
        cp_range=range_val,
        pytest=pytest_sum,
        topology="n2",
        roles=list(ROLES_N2),
        entrypoint=N2EntrypointPair(
            primary=entrypoint_primary, secondary=entrypoint_secondary
        ),
        dual_primary=0,
        majority=MAJORITY_FENCED,
        checksums=dict(sorted(checksums.items())),
        n2_extras=n2_extras,
        core_parity_paths=core_paths,
        cp_tip=cp_tip,
        created_utc="1970-01-01T00:00:00+00:00",
        files=file_list,
        bundle_sha256=bundle_sha,
        freeze=freeze_info,
    )

    man_path.write_text(n2_manifest_to_json(manifest), encoding="utf-8")
    return manifest


class N2VerifyResult:
    def __init__(self) -> None:
        self.ok: bool = True
        self.errors: list[str] = []
        self.warnings: list[str] = []
        self.manifest: N2BundleManifest | None = None
        self.smoke_ok: bool | None = None
        self.parity_ok: bool | None = None

    def fail(self, msg: str) -> None:
        self.ok = False
        self.errors.append(msg)

    def warn(self, msg: str) -> None:
        self.warnings.append(msg)

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "errors": list(self.errors),
            "warnings": list(self.warnings),
            "smoke_ok": self.smoke_ok,
            "parity_ok": self.parity_ok,
            "manifest": (
                self.manifest.model_dump(mode="json", by_alias=True)
                if self.manifest
                else None
            ),
        }


def load_n2_manifest(path: Path | str) -> N2BundleManifest:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return N2BundleManifest.model_validate(data)


def verify_n2_bundle(
    bundle_path: Path | str,
    manifest_path: Path | str | None = None,
    *,
    smoke: bool = True,
    expected_ver: str | None = None,
    single_manifest_path: Path | str | None = None,
    expect_freeze_channel: str | None = None,
) -> N2VerifyResult:
    """Verify N2 checksums + schema fields + optional import smoke + core parity."""
    result = N2VerifyResult()
    bundle_path = Path(bundle_path).resolve()
    if not bundle_path.is_file():
        result.fail(f"bundle missing: {bundle_path}")
        return result

    if manifest_path is None:
        stem = bundle_path.name
        if stem.endswith(".tar.gz"):
            base = stem[: -len(".tar.gz")]
        else:
            base = bundle_path.stem
        candidate = bundle_path.with_name(f"{base}.manifest.json")
        if not candidate.is_file():
            candidate = bundle_path.parent / "manifest.json"
        manifest_path = candidate
    else:
        manifest_path = Path(manifest_path).resolve()

    if not Path(manifest_path).is_file():
        result.fail(f"manifest missing: {manifest_path}")
        return result

    try:
        manifest = load_n2_manifest(manifest_path)
    except Exception as exc:  # noqa: BLE001
        result.fail(f"manifest invalid: {exc}")
        return result
    result.manifest = manifest

    if manifest.schema_name != SCHEMA_ID_N2:
        result.fail(
            f"schema mismatch: {manifest.schema_name!r} != {SCHEMA_ID_N2!r}"
        )
    if manifest.schema_name == SCHEMA_ID_SINGLE_FROZEN:
        result.fail("N2 bundle must not use frozen single-node schema id")

    if manifest.topology != "n2":
        result.fail(f"topology must be n2, got {manifest.topology!r}")
    if list(manifest.roles) != list(ROLES_N2):
        result.fail(f"roles must be {list(ROLES_N2)}, got {manifest.roles!r}")
    if manifest.dual_primary != 0:
        result.fail(f"dual_primary must be 0, got {manifest.dual_primary!r}")
    if manifest.majority != MAJORITY_FENCED:
        result.fail(
            f"majority must be {MAJORITY_FENCED!r} (NOT Raft), got {manifest.majority!r}"
        )
    if "raft" in (manifest.majority or "").lower():
        result.fail("Raft majority is forbidden in N2 packaging")

    if expect_freeze_channel is not None:
        if manifest.freeze is None:
            result.fail(
                f"freeze missing; expected channel {expect_freeze_channel!r}"
            )
        else:
            ch = manifest.freeze.channel
            if ch != expect_freeze_channel:
                result.fail(
                    f"freeze channel mismatch: {ch!r} != {expect_freeze_channel!r}"
                )
            if manifest.freeze.schema_name != SCHEMA_ID_N2:
                result.fail(
                    f"freeze.schema mismatch: {manifest.freeze.schema_name!r}"
                )
            if (
                manifest.freeze.single_node_schema_frozen
                != SCHEMA_ID_SINGLE_FROZEN
            ):
                result.fail(
                    "freeze.single_node_schema_frozen must record v1 frozen"
                )
    elif manifest.freeze is not None:
        if manifest.freeze.schema_name != SCHEMA_ID_N2:
            result.fail(
                f"freeze.schema mismatch: {manifest.freeze.schema_name!r}"
            )
        if (
            manifest.freeze.single_node_schema_frozen
            != SCHEMA_ID_SINGLE_FROZEN
        ):
            result.fail("freeze.single_node_schema_frozen must record v1 frozen")

    for field in ("name", "ver", "cp_range"):
        if not getattr(manifest, field):
            result.fail(f"manifest field empty: {field}")

    if expected_ver and manifest.ver != expected_ver:
        result.fail(f"ver mismatch: {manifest.ver!r} != {expected_ver!r}")

    actual_bundle = sha256_file(bundle_path)
    expected_bundle = (
        manifest.bundle_sha256
        or manifest.checksums.get("bundle.tar.gz")
        or manifest.checksums.get(bundle_path.name)
    )
    if not expected_bundle:
        result.fail("manifest missing bundle checksum")
    elif actual_bundle != expected_bundle:
        result.fail(
            f"bundle checksum mismatch: got {actual_bundle}, expected {expected_bundle}"
        )

    with tempfile.TemporaryDirectory(prefix="mesh-n2-verify-") as tmp:
        tmp_path = Path(tmp)
        try:
            with tarfile.open(bundle_path, mode="r:gz") as tar:
                try:
                    tar.extractall(tmp_path, filter="data")
                except TypeError:
                    tar.extractall(tmp_path)
        except Exception as exc:  # noqa: BLE001
            result.fail(f"extract failed: {exc}")
            return result

        root_dirs = [p for p in tmp_path.iterdir() if p.is_dir()]
        extract_root = root_dirs[0] if len(root_dirs) == 1 else tmp_path

        for rel, digest in sorted(manifest.checksums.items()):
            if rel in {"bundle.tar.gz", "manifest.json"}:
                continue
            fp = extract_root / rel
            if not fp.is_file():
                result.fail(f"missing file in bundle: {rel}")
                continue
            got = sha256_file(fp)
            if got != digest:
                result.fail(
                    f"checksum mismatch for {rel}: got {got}, expected {digest}"
                )

        # Require at least one stub config present when claimed in n2_extras / files
        stubs = [
            "src/neural_mesh/packaging/n2_stub_configs/node_a_primary.json",
            "src/neural_mesh/packaging/n2_stub_configs/node_b_secondary.json",
        ]
        for stub in stubs:
            if stub in manifest.files and not (extract_root / stub).is_file():
                result.fail(f"N2 stub missing after extract: {stub}")

        if smoke and result.ok:
            result.smoke_ok = _run_n2_smoke(extract_root, result)
        elif smoke:
            result.smoke_ok = False

    if single_manifest_path is not None:
        sp = Path(single_manifest_path)
        if sp.is_file():
            try:
                from .bundle import load_manifest

                single = load_manifest(sp)
                ok, errs = core_parity_checksums(
                    manifest.checksums,
                    single.checksums,
                    paths=manifest.core_parity_paths or list(CORE_PARITY_CANDIDATES),
                )
                result.parity_ok = ok
                if not ok:
                    for e in errs:
                        result.fail(e)
            except Exception as exc:  # noqa: BLE001
                result.fail(f"parity check failed: {exc}")
                result.parity_ok = False
        else:
            result.warn(f"single-node manifest missing for parity: {sp}")
            result.parity_ok = None

    return result


def _run_n2_smoke(extract_root: Path, result: N2VerifyResult) -> bool:
    src = extract_root / "src"
    if not src.is_dir():
        result.fail("smoke: src/ missing in extract")
        return False
    env = os.environ.copy()
    env["PYTHONPATH"] = str(src) + os.pathsep + env.get("PYTHONPATH", "")
    try:
        proc = subprocess.run(
            [
                os.environ.get("MESH_BUNDLE_PYTHON", "python3"),
                "-c",
                "import neural_mesh; print(getattr(neural_mesh, '__version__', 'ok'))",
            ],
            cwd=str(extract_root),
            env=env,
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
    except Exception as exc:  # noqa: BLE001
        result.fail(f"smoke failed: {exc}")
        return False
    if proc.returncode != 0:
        result.fail(f"smoke import failed: {proc.stderr.strip() or proc.stdout}")
        return False
    return True
