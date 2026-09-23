"""Clean-node bundle smoke (CP-0025 / P9).

Extract a bundle into an empty temp root and prove the package runs with
**no** reach-back into the original repository tree (PYTHONPATH / __file__
isolation).
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tarfile
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .bundle import ARCHIVE_ROOT, verify_bundle
from .manifest import BundleManifest

__all__ = [
    "CleanSmokeResult",
    "clean_node_smoke",
    "assert_extract_isolation",
]


@dataclass
class CleanSmokeResult:
    ok: bool = True
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    extract_root: str | None = None
    neural_mesh_file: str | None = None
    version: str | None = None
    status_snapshot: dict[str, Any] | None = None
    verify_ok: bool | None = None

    def fail(self, msg: str) -> None:
        self.ok = False
        self.errors.append(msg)

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "errors": list(self.errors),
            "warnings": list(self.warnings),
            "extract_root": self.extract_root,
            "neural_mesh_file": self.neural_mesh_file,
            "version": self.version,
            "status_snapshot": self.status_snapshot,
            "verify_ok": self.verify_ok,
        }


def assert_extract_isolation(
    extract_root: Path,
    module_file: str,
    *,
    forbidden_roots: list[Path] | None = None,
) -> list[str]:
    """Return error strings if module_file escapes extract_root or hits forbidden."""
    errs: list[str] = []
    extract_root = extract_root.resolve()
    mod = Path(module_file).resolve()
    try:
        mod.relative_to(extract_root)
    except ValueError:
        errs.append(
            f"isolation: neural_mesh.__file__ {mod} not under extract {extract_root}"
        )
    if forbidden_roots:
        for fr in forbidden_roots:
            fr = fr.resolve()
            # Module must not live under the original repo src tree.
            try:
                mod.relative_to(fr)
            except ValueError:
                continue
            else:
                errs.append(
                    f"isolation: neural_mesh.__file__ {mod} reaches forbidden root {fr}"
                )
    return errs


def _extract_bundle(bundle_path: Path, dest: Path) -> Path:
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


def clean_node_smoke(
    bundle_path: Path | str,
    *,
    manifest_path: Path | str | None = None,
    python: str | None = None,
    forbidden_repo: Path | str | None = None,
    run_verify: bool = True,
    run_status_snapshot: bool = True,
    keep_extract: Path | str | None = None,
) -> CleanSmokeResult:
    """Build-independent smoke: extract → isolated import → optional status snapshot.

    The smoke subprocess forces ``sys.path`` to **only** the extracted ``src/``
    (plus stdlib), so an editable install of the original repo cannot win.
    """
    result = CleanSmokeResult()
    bundle_path = Path(bundle_path).resolve()
    if not bundle_path.is_file():
        result.fail(f"bundle missing: {bundle_path}")
        return result

    if run_verify:
        vr = verify_bundle(bundle_path, manifest_path, smoke=True)
        result.verify_ok = vr.ok
        if not vr.ok:
            result.fail("pre-smoke verify_bundle failed: " + "; ".join(vr.errors))
            return result

    py = python or os.environ.get("MESH_BUNDLE_PYTHON") or sys.executable
    forbidden = Path(forbidden_repo).resolve() if forbidden_repo else None

    tmp_owned = keep_extract is None
    if keep_extract is not None:
        extract_base = Path(keep_extract)
        extract_base.mkdir(parents=True, exist_ok=True)
        # Ensure empty-ish: only our extract
        for child in list(extract_base.iterdir()):
            if child.is_dir():
                shutil.rmtree(child)
            else:
                child.unlink()
    else:
        extract_base = Path(tempfile.mkdtemp(prefix="mesh-clean-node-"))

    try:
        extract_root = _extract_bundle(bundle_path, extract_base)
        result.extract_root = str(extract_root)
        src = extract_root / "src"
        if not src.is_dir():
            result.fail("extract missing src/")
            return result

        # Probe: prefer extracted src; drop any sys.path entries under forbidden repo
        # (editable installs), but keep site-packages for third-party deps.
        forbidden_lit = str(forbidden) if forbidden else ""
        run_snap = "1" if run_status_snapshot else "0"
        probe = f"""
import json, sys, os
from pathlib import Path
extract = Path({str(extract_root)!r}).resolve()
src = Path({str(src)!r}).resolve()
forbidden = {forbidden_lit!r}
run_snap = {run_snap!r}
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
        # Drop editable / repo *source* paths only. Keep repo/.venv site-packages
        # (third-party deps like pydantic) and all non-repo paths.
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
# Ensure cwd semantics match mesh CLI (status uses Path.cwd()).
os.chdir(extract)
import neural_mesh
mf = Path(neural_mesh.__file__).resolve()
try:
    mf.relative_to(extract)
except ValueError:
    print("ISOLATION_FAIL", mf, extract, file=sys.stderr)
    raise SystemExit(2)
if forbidden:
    try:
        mf.relative_to(Path(forbidden) / "src")
        print("ISOLATION_FAIL_REPO", mf, forbidden, file=sys.stderr)
        raise SystemExit(3)
    except ValueError:
        pass
print("IMPORT_OK", getattr(neural_mesh, "__version__", "?"), str(mf))
if run_snap == "1":
    # Equivalent to: mesh status --snapshot (library API; cwd=extract)
    from neural_mesh.status_snapshot import snapshot, snapshot_to_json
    from neural_mesh.cli import main as mesh_main
    snap = snapshot(extract)
    print("STATUS_JSON_BEGIN")
    print(snapshot_to_json(snap), end="")
    print("STATUS_JSON_END")
    # Also exercise CLI entry once (stdout discarded to avoid double JSON)
    import io
    from contextlib import redirect_stdout
    with redirect_stdout(io.StringIO()):
        mesh_main(["status", "--snapshot"])
"""
        env = os.environ.copy()
        # Do not inherit a PYTHONPATH that points at the original repo.
        env.pop("PYTHONPATH", None)
        env["PYTHONNOUSERSITE"] = "1"
        # cwd must be extract so mesh status finds .project_state
        proc = subprocess.run(
            [py, "-c", probe],
            cwd=str(extract_root),
            env=env,
            capture_output=True,
            text=True,
            timeout=60,
            check=False,
        )
        if proc.returncode != 0:
            result.fail(
                f"clean-node smoke failed (rc={proc.returncode}): "
                f"{proc.stderr.strip() or proc.stdout.strip()}"
            )
            return result

        version = None
        mod_file = None
        status_json = None
        lines = proc.stdout.splitlines()
        for i, line in enumerate(lines):
            if line.startswith("IMPORT_OK "):
                parts = line.split(" ", 2)
                if len(parts) >= 3:
                    version = parts[1]
                    mod_file = parts[2]
            if line == "STATUS_JSON_BEGIN":
                end = lines.index("STATUS_JSON_END", i + 1)
                blob = "\n".join(lines[i + 1 : end])
                try:
                    status_json = json.loads(blob) if blob.strip() else None
                except json.JSONDecodeError as exc:
                    result.fail(f"status snapshot JSON invalid: {exc}")
                break

        result.version = version
        result.neural_mesh_file = mod_file
        if run_status_snapshot:
            result.status_snapshot = status_json
            if status_json is None:
                result.fail("status --snapshot produced no JSON")
            elif status_json.get("schema") != "mesh.status.snapshot/v1":
                result.warn(
                    f"unexpected snapshot schema: {status_json.get('schema')!r}"
                )

        if mod_file:
            iso_errs = assert_extract_isolation(
                extract_root,
                mod_file,
                forbidden_roots=(
                    [forbidden / "src", forbidden] if forbidden else None
                ),
            )
            for e in iso_errs:
                result.fail(e)
        else:
            result.fail("clean-node smoke missing IMPORT_OK line")

    finally:
        if tmp_owned and extract_base.exists():
            shutil.rmtree(extract_base, ignore_errors=True)

    return result
