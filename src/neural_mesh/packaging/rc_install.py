"""RC install verify (CP-0026 / P12).

Extract a single-node RC bundle into a clean prefix and prove the install works
using only the tarball + manifest (no live-repo reach-back).
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
import textwrap
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .bundle import ARCHIVE_ROOT, DEFAULT_ENTRYPOINT, load_manifest, verify_bundle
from .manifest import FREEZE_CHANNEL, SCHEMA_ID, BundleManifest

__all__ = [
    "InstallResult",
    "rc_install",
    "rc_install_verify",
    "assert_entrypoint_present",
    "write_mesh_launcher",
]

MESH_LAUNCHER = textwrap.dedent(
    """\
    #!/usr/bin/env python3
    import os, sys
    from pathlib import Path
    PREFIX = Path(__file__).resolve().parents[1]
    SRC = PREFIX / "root" / "src"
    if not SRC.is_dir():
        # flat layout: prefix/src
        alt = PREFIX / "src"
        SRC = alt if alt.is_dir() else SRC
    sys.path.insert(0, str(SRC))
    os.environ.pop("PYTHONPATH", None)
    from neural_mesh.cli import main
    raise SystemExit(main())
    """
)


@dataclass
class InstallResult:
    ok: bool = True
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    prefix: str | None = None
    extract_root: str | None = None
    version: str | None = None
    entrypoint: str | None = None
    freeze_channel: str | None = None
    freeze_schema: str | None = None
    help_ok: bool | None = None
    status_ok: bool | None = None
    import_ok: bool | None = None
    verify_ok: bool | None = None
    manifest: dict[str, Any] | None = None

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
            "prefix": self.prefix,
            "extract_root": self.extract_root,
            "version": self.version,
            "entrypoint": self.entrypoint,
            "freeze_channel": self.freeze_channel,
            "freeze_schema": self.freeze_schema,
            "help_ok": self.help_ok,
            "status_ok": self.status_ok,
            "import_ok": self.import_ok,
            "verify_ok": self.verify_ok,
            "manifest": self.manifest,
        }


def _extract_bundle(bundle_path: Path, dest: Path) -> Path:
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


def assert_entrypoint_present(extract_root: Path, *, entrypoint: str = DEFAULT_ENTRYPOINT) -> list[str]:
    """Return error strings if console entrypoint / CLI module is missing or corrupt."""
    errs: list[str] = []
    pyproject = extract_root / "pyproject.toml"
    if not pyproject.is_file():
        errs.append("missing pyproject.toml in extract")
        return errs
    text = pyproject.read_text(encoding="utf-8")
    # Require [project.scripts] mesh = "neural_mesh.cli:main" (or similar)
    if "[project.scripts]" not in text:
        errs.append("pyproject.toml missing [project.scripts] section")
    else:
        # Look for mesh = ... neural_mesh.cli
        pattern = rf'(?m)^\s*{re.escape(entrypoint)}\s*=\s*["\']([^"\']+)["\']'
        m = re.search(pattern, text)
        if not m:
            errs.append(f"entrypoint {entrypoint!r} missing from [project.scripts]")
        else:
            target = m.group(1)
            if "neural_mesh.cli" not in target and ":" not in target:
                errs.append(f"entrypoint target looks corrupt: {target!r}")
    cli = extract_root / "src" / "neural_mesh" / "cli.py"
    if not cli.is_file():
        errs.append("missing src/neural_mesh/cli.py (entrypoint module)")
    else:
        body = cli.read_text(encoding="utf-8", errors="replace")
        if "def main" not in body:
            errs.append("src/neural_mesh/cli.py missing def main (corrupt entrypoint)")
    init = extract_root / "src" / "neural_mesh" / "__init__.py"
    if not init.is_file():
        errs.append("missing src/neural_mesh/__init__.py")
    return errs


def write_mesh_launcher(prefix: Path, *, python: str | None = None) -> Path:
    """Write prefix/bin/mesh launcher (PYTHONPATH install; no OS package manager)."""
    bin_dir = prefix / "bin"
    bin_dir.mkdir(parents=True, exist_ok=True)
    launcher = bin_dir / "mesh"
    # Prefer shebang from python if provided; else env python3
    body = MESH_LAUNCHER
    if python:
        body = body.replace("#!/usr/bin/env python3", f"#!{python}", 1)
    launcher.write_text(body, encoding="utf-8")
    launcher.chmod(0o755)
    return launcher


def rc_install(
    bundle_path: Path | str,
    prefix: Path | str,
    *,
    manifest_path: Path | str | None = None,
    python: str | None = None,
    run_verify: bool = True,
    clear_prefix: bool = True,
) -> InstallResult:
    """Extract bundle into ``prefix/root`` and install a ``bin/mesh`` launcher.

    Must not depend on the live repo beyond the built tarball + manifest.
    """
    result = InstallResult()
    bundle_path = Path(bundle_path).resolve()
    prefix = Path(prefix).resolve()
    result.prefix = str(prefix)

    if not bundle_path.is_file():
        result.fail(f"bundle missing: {bundle_path}")
        return result

    if run_verify:
        vr = verify_bundle(bundle_path, manifest_path, smoke=True)
        result.verify_ok = vr.ok
        if not vr.ok:
            result.fail("pre-install verify_bundle failed: " + "; ".join(vr.errors))
            return result
        if vr.manifest is not None:
            result.manifest = vr.manifest.model_dump(mode="json", by_alias=True)
            result.entrypoint = vr.manifest.entrypoint
            if vr.manifest.freeze:
                result.freeze_channel = vr.manifest.freeze.channel
                result.freeze_schema = vr.manifest.freeze.schema_name

    if clear_prefix and prefix.exists():
        for child in list(prefix.iterdir()):
            if child.is_dir():
                shutil.rmtree(child)
            else:
                child.unlink()
    prefix.mkdir(parents=True, exist_ok=True)

    extract_base = prefix / "_extract"
    if extract_base.exists():
        shutil.rmtree(extract_base)
    extract_base.mkdir(parents=True)
    try:
        extract_root = _extract_bundle(bundle_path, extract_base)
    except Exception as exc:  # noqa: BLE001
        result.fail(f"extract failed: {exc}")
        return result

    # Move/copy into stable prefix/root
    root_dest = prefix / "root"
    if root_dest.exists():
        shutil.rmtree(root_dest)
    shutil.copytree(extract_root, root_dest)
    shutil.rmtree(extract_base, ignore_errors=True)
    result.extract_root = str(root_dest)

    ep_errs = assert_entrypoint_present(root_dest, entrypoint=result.entrypoint or DEFAULT_ENTRYPOINT)
    for e in ep_errs:
        result.fail(e)
    if not result.ok:
        return result

    # Persist manifest sidecar for rollback / checklist
    if manifest_path and Path(manifest_path).is_file():
        man = Path(manifest_path)
    else:
        stem = bundle_path.name
        if stem.endswith(".tar.gz"):
            base = stem[: -len(".tar.gz")]
        else:
            base = bundle_path.stem
        man = bundle_path.with_name(f"{base}.manifest.json")
    if man.is_file():
        dest_man = prefix / "bundle.manifest.json"
        shutil.copy2(man, dest_man)
        try:
            m = load_manifest(dest_man)
            result.manifest = m.model_dump(mode="json", by_alias=True)
            result.entrypoint = m.entrypoint
            result.version = m.ver
            if m.freeze:
                result.freeze_channel = m.freeze.channel
                result.freeze_schema = m.freeze.schema_name
        except Exception as exc:  # noqa: BLE001
            result.warn(f"could not load sidecar manifest: {exc}")

    py = python or os.environ.get("MESH_BUNDLE_PYTHON") or sys.executable
    write_mesh_launcher(prefix, python=py)

    # Marker for install tip/ver
    (prefix / "INSTALL.json").write_text(
        json.dumps(
            {
                "ver": result.version,
                "entrypoint": result.entrypoint or DEFAULT_ENTRYPOINT,
                "freeze_channel": result.freeze_channel,
                "freeze_schema": result.freeze_schema,
                "bundle": str(bundle_path),
                "method": "pythonpath",
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    return result


def rc_install_verify(
    bundle_path: Path | str,
    *,
    prefix: Path | str | None = None,
    manifest_path: Path | str | None = None,
    python: str | None = None,
    forbidden_repo: Path | str | None = None,
    expect_freeze_channel: str = FREEZE_CHANNEL,
    keep_prefix: bool = False,
    run_help: bool = True,
    run_status_snapshot: bool = True,
) -> InstallResult:
    """Install into a clean prefix then run help / status / import / freeze checks."""
    tmp_owned = prefix is None
    if prefix is None:
        prefix = Path(tempfile.mkdtemp(prefix="mesh-rc-install-"))
    else:
        prefix = Path(prefix)

    result = rc_install(
        bundle_path,
        prefix,
        manifest_path=manifest_path,
        python=python,
        run_verify=True,
        clear_prefix=True,
    )
    if not result.ok:
        if tmp_owned and not keep_prefix:
            shutil.rmtree(prefix, ignore_errors=True)
        return result

    py = python or os.environ.get("MESH_BUNDLE_PYTHON") or sys.executable
    root = Path(result.extract_root or (prefix / "root"))
    src = root / "src"
    launcher = Path(prefix) / "bin" / "mesh"

    env = os.environ.copy()
    env.pop("PYTHONPATH", None)
    env["PYTHONNOUSERSITE"] = "1"
    # Prefer launcher; fall back to -c with forced src path
    forbidden = Path(forbidden_repo).resolve() if forbidden_repo else None

    # Import check (isolated)
    import_probe = f"""
import sys, os
from pathlib import Path
src = Path({str(src)!r}).resolve()
forbidden = {str(forbidden) if forbidden else ''!r}
clean = [str(src)]
forb = Path(forbidden).resolve() if forbidden else None
forb_src = (forb / "src").resolve() if forb else None
for p in list(sys.path):
    if not p or p == str(src):
        continue
    if forb is not None:
        try:
            rp = Path(p).resolve()
        except OSError:
            clean.append(p)
            continue
        drop = False
        if forb_src is not None:
            try:
                rp.relative_to(forb_src)
                drop = True
            except ValueError:
                pass
        if not drop and rp == forb:
            drop = True
        if drop:
            continue
    clean.append(p)
sys.path[:] = clean
os.chdir({str(root)!r})
import neural_mesh
mf = Path(neural_mesh.__file__).resolve()
try:
    mf.relative_to(Path({str(root)!r}).resolve())
except ValueError:
    print("ISOLATION_FAIL", mf, file=sys.stderr)
    raise SystemExit(2)
print("IMPORT_OK", getattr(neural_mesh, "__version__", "?"), str(mf))
"""
    proc = subprocess.run(
        [py, "-c", import_probe],
        cwd=str(root),
        env=env,
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    if proc.returncode != 0:
        result.import_ok = False
        result.fail(f"import check failed: {proc.stderr.strip() or proc.stdout.strip()}")
    else:
        result.import_ok = True
        for line in proc.stdout.splitlines():
            if line.startswith("IMPORT_OK "):
                parts = line.split(" ", 2)
                if len(parts) >= 2:
                    result.version = parts[1]

    # mesh --help via launcher
    if run_help and launcher.is_file():
        help_proc = subprocess.run(
            [py, str(launcher), "--help"],
            cwd=str(root),
            env=env,
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
        result.help_ok = help_proc.returncode == 0 and (
            "usage" in help_proc.stdout.lower() or "mesh" in help_proc.stdout.lower() or help_proc.stdout.strip() != ""
        )
        if not result.help_ok:
            # CLI may print to stderr; still accept rc=0
            if help_proc.returncode == 0:
                result.help_ok = True
            else:
                result.fail(f"mesh --help failed: {help_proc.stderr.strip() or help_proc.stdout.strip()}")
    elif run_help:
        result.help_ok = False
        result.fail("mesh launcher missing after install")
    else:
        result.help_ok = None

    # mesh status --snapshot
    if run_status_snapshot and launcher.is_file() and result.ok:
        st = subprocess.run(
            [py, str(launcher), "status", "--snapshot"],
            cwd=str(root),
            env=env,
            capture_output=True,
            text=True,
            timeout=60,
            check=False,
        )
        if st.returncode != 0:
            result.status_ok = False
            result.fail(f"mesh status --snapshot failed: {st.stderr.strip() or st.stdout.strip()}")
        else:
            result.status_ok = True
            try:
                # snapshot may be pure JSON or have noise; try parse whole stdout
                blob = st.stdout.strip()
                if blob.startswith("{"):
                    snap = json.loads(blob)
                    if snap.get("schema") != "mesh.status.snapshot/v1":
                        result.warn(f"unexpected snapshot schema: {snap.get('schema')!r}")
            except json.JSONDecodeError:
                result.warn("status --snapshot stdout not pure JSON (accepted if rc=0)")

    elif not run_status_snapshot:
        result.status_ok = None

    # Freeze channel gate
    if expect_freeze_channel:
        ch = result.freeze_channel
        if not ch:
            result.fail("freeze channel missing from installed manifest")
        elif ch != expect_freeze_channel:
            result.fail(f"freeze channel mismatch: {ch!r} != {expect_freeze_channel!r}")
        if result.freeze_schema and result.freeze_schema != SCHEMA_ID:
            result.fail(f"freeze schema mismatch: {result.freeze_schema!r}")

    if tmp_owned and not keep_prefix:
        shutil.rmtree(prefix, ignore_errors=True)
        result.prefix = None
        result.extract_root = None

    return result
