"""Build and verify reproducible single-node mesh bundles (CP-0024..CP-0026)."""

from __future__ import annotations

import hashlib
import io
import json
import os
import re
import shutil
import subprocess
import tarfile
import tempfile
import tomllib
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from .manifest import (
    SCHEMA_ID,
    FREEZE_CHANNEL,
    BundleManifest,
    FreezeInfo,
    PytestSummary,
    manifest_to_json,
)

DEFAULT_BUNDLE_NAME = "neural-mesh-gia-single-node"
DEFAULT_ENTRYPOINT = "mesh"
# Fixed epoch for reproducible archives (SOURCE_DATE_EPOCH style).
FIXED_MTIME = 0
# Archive root directory name inside the tarball.
ARCHIVE_ROOT = "neural-mesh-gia"

# Paths relative to repo root included in the single-node bundle.
INCLUDE_PATHS: tuple[str, ...] = (
    "pyproject.toml",
    "src/neural_mesh",
    "scripts/audit.sh",
    "scripts/bootstrap.sh",
    "scripts/build_bundle.py",
    "scripts/verify_bundle.py",
    "scripts/clean_node_smoke.py",
    "scripts/repro_check.py",
    "scripts/rc_install_verify.py",
    "scripts/rollback_smoke.py",
    "scripts/release_checklist.py",
    "docs/debt/CHECKPOINT_EVERY_FLOOR.md",
    "docs/capabilities/MESH_PACKAGING_SINGLE_NODE_BUNDLE.md",
    "docs/capabilities/MESH_PACKAGING_RELEASE_CHECKLIST.md",
    ".project_state/CHECKPOINT.json",
)

# Name-based executable modes (avoid os.access flake across hosts).
EXECUTABLE_NAMES = {
    "audit.sh",
    "bootstrap.sh",
    "build_bundle.py",
    "verify_bundle.py",
    "clean_node_smoke.py",
    "repro_check.py",
    "rc_install_verify.py",
    "rollback_smoke.py",
    "release_checklist.py",
}

EXCLUDE_DIR_NAMES = {
    ".venv",
    ".git",
    "__pycache__",
    ".pytest_cache",
    ".ruff_cache",
    ".cram",
    "htmlcov",
    "*.egg-info",
    "experiments",
    "snapshots",
    "council",
    "obsidian",
}

EXCLUDE_SUFFIXES = {".pyc", ".pyo", ".so", ".tmp", ".sock"}

__all__ = [
    "DEFAULT_BUNDLE_NAME",
    "DEFAULT_ENTRYPOINT",
    "FIXED_MTIME",
    "ARCHIVE_ROOT",
    "INCLUDE_PATHS",
    "EXECUTABLE_NAMES",
    "build_bundle",
    "verify_bundle",
    "collect_bundle_files",
    "sha256_file",
    "sha256_bytes",
    "load_manifest",
]


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _should_exclude(rel: Path) -> bool:
    parts = set(rel.parts)
    if parts & EXCLUDE_DIR_NAMES:
        return True
    if any(p.endswith(".egg-info") for p in rel.parts):
        return True
    if rel.suffix in EXCLUDE_SUFFIXES:
        return True
    name = rel.name
    if name.startswith(".") and name not in {
        ".project_state",
        # allow files under include list that start with .
    }:
        # Still allow explicit includes like .project_state/CHECKPOINT.json
        if ".project_state" not in rel.parts:
            # skip stray dotfiles unless under an included tree that is not excluded
            if not any(str(rel).startswith(p) for p in INCLUDE_PATHS):
                return True
    return False


def collect_bundle_files(root: Path) -> list[Path]:
    """Return sorted absolute file paths to include in the bundle."""
    root = root.resolve()
    found: set[Path] = set()
    for rel_s in INCLUDE_PATHS:
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
            if _should_exclude(rel):
                continue
            found.add(fp.resolve())
    return sorted(found, key=lambda x: str(x.relative_to(root)).replace("\\", "/"))


def _read_pyproject_version(root: Path) -> str:
    data = tomllib.loads((root / "pyproject.toml").read_text(encoding="utf-8"))
    return str(data["project"]["version"])


def _git_tip7(root: Path) -> str | None:
    try:
        out = subprocess.check_output(
            ["git", "rev-parse", "--short=7", "HEAD"],
            cwd=root,
            stderr=subprocess.DEVNULL,
            text=True,
        ).strip()
        return out or None
    except (subprocess.CalledProcessError, FileNotFoundError, OSError):
        return None


def _load_project_state(root: Path) -> dict[str, Any]:
    p = root / ".project_state" / "CHECKPOINT.json"
    if not p.is_file():
        return {}
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def _cp_range_from_root(root: Path, state: Mapping[str, Any]) -> tuple[str, str]:
    tip = state.get("last_checkpoint") or "CP-0000"
    snaps = sorted(
        (p.name for p in (root / "snapshots").glob("CP-*") if p.is_dir()),
        key=lambda n: int(n.split("-")[1]) if n.split("-")[1].isdigit() else 0,
    )
    if snaps:
        tip = snaps[-1]
        last_n = snaps[-1].split("-")[1]
        return f"CP-0001..{last_n}", tip
    m = re.match(r"CP-(\d+)", str(tip))
    if m:
        return f"CP-0001..{m.group(1)}", str(tip)
    return "CP-0001..0000", str(tip)


def _pytest_from_state(state: Mapping[str, Any]) -> PytestSummary:
    ts = state.get("test_summary") or {}
    return PytestSummary(
        passed=int(ts.get("passed") or 0),
        failed=int(ts.get("failed") or 0),
    )


def _normalize_mode(path: Path) -> int:
    """Deterministic mode: .sh / known scripts → 0755; else 0644 (no os.access)."""
    if path.is_dir():
        return 0o755
    if path.suffix == ".sh" or path.name in EXECUTABLE_NAMES:
        return 0o755
    return 0o644


def _add_deterministic(
    tar: tarfile.TarFile,
    arcname: str,
    data: bytes,
    *,
    mode: int = 0o644,
) -> None:
    info = tarfile.TarInfo(name=arcname)
    info.size = len(data)
    info.mtime = FIXED_MTIME
    info.uid = 0
    info.gid = 0
    info.uname = ""
    info.gname = ""
    info.mode = mode
    info.type = tarfile.REGTYPE
    tar.addfile(info, io.BytesIO(data))


def _write_deterministic_tar(
    files: Sequence[tuple[str, bytes, int]],
    dest: Path,
) -> str:
    """Write gzipped tar with sorted members; return sha256 of archive bytes."""
    # Build uncompressed tar in memory first for stable gzip of content,
    # then gzip with mtime=0.
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w") as tar:
        for arcname, data, mode in sorted(files, key=lambda t: t[0]):
            _add_deterministic(tar, arcname, data, mode=mode)
    raw = buf.getvalue()
    # gzip with fixed mtime
    import gzip

    out = io.BytesIO()
    with gzip.GzipFile(filename="", mode="wb", fileobj=out, mtime=FIXED_MTIME) as gz:
        gz.write(raw)
    payload = out.getvalue()
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(payload)
    return sha256_bytes(payload)


def build_bundle(
    root: Path | str,
    out_dir: Path | str,
    *,
    name: str = DEFAULT_BUNDLE_NAME,
    ver: str | None = None,
    tip: str | None = None,
    cp_range: str | None = None,
    pytest: PytestSummary | Mapping[str, int] | None = None,
    entrypoint: str = DEFAULT_ENTRYPOINT,
    include_extra: Sequence[str] | None = None,
    freeze: FreezeInfo | Mapping[str, str] | bool | None = True,
) -> BundleManifest:
    """Build a reproducible single-node bundle tarball + manifest.json.

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

    file_paths = collect_bundle_files(root)
    if include_extra:
        for rel in include_extra:
            p = (root / rel).resolve()
            if p.is_file() and p not in file_paths:
                file_paths.append(p)
        file_paths = sorted(
            file_paths, key=lambda x: str(x.relative_to(root)).replace("\\", "/")
        )

    members: list[tuple[str, bytes, int]] = []
    checksums: dict[str, str] = {}
    file_list: list[str] = []

    for fp in file_paths:
        rel = str(fp.relative_to(root)).replace("\\", "/")
        data = fp.read_bytes()
        mode = _normalize_mode(fp)
        arc = f"{ARCHIVE_ROOT}/{rel}"
        members.append((arc, data, mode))
        checksums[rel] = sha256_bytes(data)
        file_list.append(rel)

    # Placeholder: we compute tar sha after writing, then embed in manifest.
    tar_name = f"{name}-{version}.tar.gz"
    man_name = f"{name}-{version}.manifest.json"
    tar_path = out_dir / tar_name
    man_path = out_dir / man_name

    bundle_sha = _write_deterministic_tar(members, tar_path)
    checksums["bundle.tar.gz"] = bundle_sha

    freeze_info: FreezeInfo | None
    if freeze is False or freeze is None:
        freeze_info = None
    elif freeze is True:
        freeze_info = FreezeInfo(channel=FREEZE_CHANNEL, schema_name=SCHEMA_ID)
    elif isinstance(freeze, FreezeInfo):
        freeze_info = freeze
    else:
        freeze_info = FreezeInfo(
            channel=str(freeze.get("channel", FREEZE_CHANNEL)),
            schema_name=str(freeze.get("schema", freeze.get("schema_name", SCHEMA_ID))),
        )

    manifest = BundleManifest(
        name=name,
        ver=version,
        tip=tip_val,
        cp_range=range_val,
        pytest=pytest_sum,
        entrypoint=entrypoint,
        checksums=dict(sorted(checksums.items())),
        cp_tip=cp_tip,
        created_utc="1970-01-01T00:00:00+00:00",  # fixed for determinism
        files=file_list,
        bundle_sha256=bundle_sha,
        freeze=freeze_info,
    )

    # Single write — checksums cover member files + bundle.tar.gz only
    # (manifest.json is verified by schema load + bundle_sha256 match).
    man_path.write_text(manifest_to_json(manifest), encoding="utf-8")
    return manifest


class VerifyResult:
    def __init__(self) -> None:
        self.ok: bool = True
        self.errors: list[str] = []
        self.warnings: list[str] = []
        self.manifest: BundleManifest | None = None
        self.smoke_ok: bool | None = None

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
            "manifest": (
                self.manifest.model_dump(mode="json", by_alias=True)
                if self.manifest
                else None
            ),
        }


def load_manifest(path: Path | str) -> BundleManifest:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return BundleManifest.model_validate(data)


def verify_bundle(
    bundle_path: Path | str,
    manifest_path: Path | str | None = None,
    *,
    smoke: bool = True,
    expected_ver: str | None = None,
) -> VerifyResult:
    """Verify checksums + manifest fields + optional import smoke test."""
    result = VerifyResult()
    bundle_path = Path(bundle_path).resolve()
    if not bundle_path.is_file():
        result.fail(f"bundle missing: {bundle_path}")
        return result

    if manifest_path is None:
        # Convention: same stem with .manifest.json
        stem = bundle_path.name
        if stem.endswith(".tar.gz"):
            base = stem[: -len(".tar.gz")]
        else:
            base = bundle_path.stem
        candidate = bundle_path.with_name(f"{base}.manifest.json")
        if not candidate.is_file():
            # also try sibling manifest.json
            candidate = bundle_path.parent / "manifest.json"
        manifest_path = candidate
    else:
        manifest_path = Path(manifest_path).resolve()

    if not Path(manifest_path).is_file():
        result.fail(f"manifest missing: {manifest_path}")
        return result

    try:
        manifest = load_manifest(manifest_path)
    except Exception as exc:  # noqa: BLE001
        result.fail(f"manifest invalid: {exc}")
        return result
    result.manifest = manifest

    if manifest.schema_name != SCHEMA_ID:
        result.fail(f"schema mismatch: {manifest.schema_name!r} != {SCHEMA_ID!r}")

    if manifest.freeze is not None:
        if manifest.freeze.schema_name != SCHEMA_ID:
            result.fail(
                f"freeze.schema mismatch: {manifest.freeze.schema_name!r} != {SCHEMA_ID!r}"
            )
        if not manifest.freeze.channel:
            result.fail("freeze.channel empty")

    for field in ("name", "ver", "cp_range", "entrypoint"):
        if not getattr(manifest, field):
            result.fail(f"manifest field empty: {field}")

    if expected_ver and manifest.ver != expected_ver:
        result.fail(f"ver mismatch: {manifest.ver!r} != {expected_ver!r}")

    # Bundle archive checksum
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

    # Extract and verify per-file checksums
    with tempfile.TemporaryDirectory(prefix="mesh-bundle-verify-") as tmp:
        tmp_path = Path(tmp)
        try:
            with tarfile.open(bundle_path, mode="r:gz") as tar:
                # Python 3.12+ filter; fall back for older.
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
                result.fail(f"checksum mismatch for {rel}: got {got}, expected {digest}")

        if smoke and result.ok:
            result.smoke_ok = _run_smoke(extract_root, result)
        elif smoke:
            result.smoke_ok = False

    return result


def _run_smoke(extract_root: Path, result: VerifyResult) -> bool:
    """Fast smoke: import neural_mesh from extracted src layout."""
    src = extract_root / "src"
    if not src.is_dir():
        result.fail("smoke: src/ missing in extract")
        return False
    env = os.environ.copy()
    # Prefer isolated path
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
