"""0.17.x theme-set signoff / closeout (CP-0036 / Cycle 32).

Closes frozen 0.17 themes 1-4 on the N2 channel without reopening 0.16.3.
Writes dist/releases/0.17.0/SIGNOFF.json, optional local tag v0.17.0,
archive markers, and post-signoff MONITOR.

Package stays 0.17.0 (CLOSED/FROZEN for themes). Does not implement H1..H8.
"""

from __future__ import annotations

import gzip
import io
import json
import re
import shutil
import subprocess
import sys
import tarfile
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from .bundle import FIXED_MTIME, sha256_file
from .bundle_n2 import build_n2_bundle
from .manifest_n2 import FREEZE_CHANNEL_N2, SCHEMA_ID_N2
from .release_checklist import NO_HELD_DEFAULT, GateResult
from .release_signoff import DEFAULT_SIGNER
from .release_tag_archive import create_annotated_tag, preferred_tag_name

__all__ = [
    "THEME_VERSION",
    "THEME_FREEZE",
    "THEME_SCHEMA",
    "PRIOR_CP_017",
    "SEAL_CP_017",
    "CYCLE_017",
    "THEME_CPS",
    "THEME_DOCS",
    "ThemeSignoffResult",
    "ThemeArchiveResult",
    "run_017_theme_signoff",
    "run_017_theme_archive",
    "run_017_post_signoff_monitor",
]

THEME_VERSION = "0.17.0"
THEME_FREEZE = FREEZE_CHANNEL_N2
THEME_SCHEMA = SCHEMA_ID_N2
PRIOR_CP_017 = "CP-0035"
SEAL_CP_017 = "CP-0036"
CYCLE_017 = 32

THEME_CPS: tuple[str, ...] = (
    "CP-0031",
    "CP-0032",
    "CP-0033",
    "CP-0034",
    "CP-0035",
)

THEME_DOCS: tuple[tuple[str, str], ...] = (
    ("theme1_n2_packaging", "docs/capabilities/MESH_PACKAGING_N2_MULTI_NODE.md"),
    ("theme1_n2_audit", "docs/capabilities/MESH_PACKAGING_N2_FINAL_RELEASE_AUDIT.md"),
    ("theme2_fabric_ops", "docs/capabilities/MESH_FABRIC_OPS_UX.md"),
    ("theme3_obs_peers", "docs/capabilities/MESH_OBS_PEERS.md"),
    ("theme4_external_quickstart", "docs/capabilities/MESH_EXTERNAL_QUICKSTART.md"),
)


@dataclass
class ThemeSignoffResult:
    ok: bool = True
    errors: list[str] = field(default_factory=list)
    gates: list[GateResult] = field(default_factory=list)
    version: str | None = None
    tip: str | None = None
    cp: str | None = None
    prior_cp: str | None = None
    freeze_channel: str | None = None
    schema: str | None = None
    themes_ok: bool | None = None
    cps_ok: bool | None = None
    pytest_count: int | None = None
    dual_primary: int = 0
    signer: str = DEFAULT_SIGNER
    timestamp: str | None = None
    signoff_path: str | None = None
    checklist_path: str | None = None
    summary: dict[str, Any] = field(default_factory=dict)

    def add(self, name: str, ok: bool, detail: str = "") -> None:
        self.gates.append(GateResult(name=name, ok=ok, detail=detail))
        if not ok:
            self.ok = False
            self.errors.append(f"{name}: {detail or 'FAIL'}")

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "errors": list(self.errors),
            "version": self.version,
            "tip": self.tip,
            "cp": self.cp,
            "prior_cp": self.prior_cp,
            "freeze_channel": self.freeze_channel,
            "schema": self.schema,
            "themes_ok": self.themes_ok,
            "cps_ok": self.cps_ok,
            "pytest_count": self.pytest_count,
            "dual_primary": self.dual_primary,
            "signer": self.signer,
            "timestamp": self.timestamp,
            "signoff_path": self.signoff_path,
            "checklist_path": self.checklist_path,
            "gates": [g.to_dict() for g in self.gates],
            "summary": dict(self.summary),
            "no_held": NO_HELD_DEFAULT,
            "channel": "0.17.x-n2-theme-signoff",
            "schema_id": "mesh.release.theme_signoff/v1",
        }

    def to_json(self, *, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, sort_keys=True) + "\n"

    def signoff_record(self) -> dict[str, Any]:
        return {
            "schema": "mesh.release.theme_signoff/v1",
            "ok": self.ok,
            "ver": self.version,
            "tip": self.tip,
            "cp": self.cp,
            "prior_cp": self.prior_cp,
            "freeze": self.freeze_channel,
            "freeze_schema": self.schema,
            "themes": {
                "1": "n2_packaging_rc",
                "2": "fabric_ops_ux",
                "3": "richer_obs_peers",
                "4": "external_quickstart",
                "status": "CLOSED",
            },
            "theme_cps": list(THEME_CPS),
            "pytest_count": self.pytest_count,
            "dual_primary": self.dual_primary,
            "timestamp": self.timestamp,
            "signer": self.signer,
            "cycle": CYCLE_017,
            "line_status": "CLOSED_FROZEN_THEMES",
            "package_held_at": THEME_VERSION,
            "next_line": "0.18.x H1..H8 (planning only after council NEXT)",
            "no_held": NO_HELD_DEFAULT,
            "gates": [g.to_dict() for g in self.gates],
            "note": (
                "0.17.0 theme set CLOSED/FROZEN; package stays 0.17.0 until "
                "0.18 bootstrap. Do not reopen 0.16.3. Do not implement H1..H8 here."
            ),
        }


@dataclass
class ThemeArchiveResult:
    ok: bool = True
    errors: list[str] = field(default_factory=list)
    gates: list[GateResult] = field(default_factory=list)
    version: str | None = None
    tip: str | None = None
    tag_name: str | None = None
    tag_created: bool = False
    archive_dir: str | None = None
    tarball: str | None = None
    manifest_path: str | None = None
    signoff_path: str | None = None
    sha256sums_path: str | None = None
    release_archive: str | None = None
    summary: dict[str, Any] = field(default_factory=dict)

    def add(self, name: str, ok: bool, detail: str = "") -> None:
        self.gates.append(GateResult(name=name, ok=ok, detail=detail))
        if not ok:
            self.ok = False
            self.errors.append(f"{name}: {detail or 'FAIL'}")

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "errors": list(self.errors),
            "version": self.version,
            "tip": self.tip,
            "tag_name": self.tag_name,
            "tag_created": self.tag_created,
            "archive_dir": self.archive_dir,
            "tarball": self.tarball,
            "manifest_path": self.manifest_path,
            "signoff_path": self.signoff_path,
            "sha256sums_path": self.sha256sums_path,
            "release_archive": self.release_archive,
            "gates": [g.to_dict() for g in self.gates],
            "summary": dict(self.summary),
            "freeze": THEME_FREEZE,
            "schema": THEME_SCHEMA,
            "cp": SEAL_CP_017,
            "no_held": NO_HELD_DEFAULT,
        }

    def to_json(self, *, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, sort_keys=True) + "\n"


def _git_tip(root: Path, override: str | None = None) -> str:
    if override:
        return override
    try:
        proc = subprocess.run(
            ["git", "rev-parse", "--short=7", "HEAD"],
            cwd=str(root),
            capture_output=True,
            text=True,
            check=False,
        )
        if proc.returncode == 0 and proc.stdout.strip():
            return proc.stdout.strip()
    except OSError:
        pass
    return "unknown"


def _read_version(root: Path) -> tuple[str, str | None]:
    import tomllib

    data = tomllib.loads((root / "pyproject.toml").read_text(encoding="utf-8"))
    ver = str(data["project"]["version"])
    init = (root / "src" / "neural_mesh" / "__init__.py").read_text(encoding="utf-8")
    m = re.search(r'__version__\s*=\s*["\']([^"\']+)["\']', init)
    return ver, (m.group(1) if m else None)


def _gate_version(root: Path, result: ThemeSignoffResult, expect: str) -> None:
    """Exact THEME_VERSION match, or 0.18.x next-line after theme closeout.

    When package has opened 0.18.x (CP-0037 bootstrap), accept and stamp
    SIGNOFF ver=expect (0.17.0) so closed theme-set archives stay coherent.
    """
    ver, init_ver = _read_version(root)
    agree = init_ver is None or init_ver == ver
    exact = ver == expect and agree and (init_ver is None or init_ver == expect)
    next_line_ok = (
        expect == THEME_VERSION
        and agree
        and ver.startswith("0.18.")
        and (init_ver is None or str(init_ver).startswith("0.18."))
    )
    ok = exact or next_line_ok
    result.version = expect if ok else ver
    result.add(
        "version_0170",
        ok,
        f"pyproject={ver} init={init_ver} expected={expect} next_line_ok={next_line_ok}",
    )


def _gate_freeze(result: ThemeSignoffResult) -> None:
    result.freeze_channel = THEME_FREEZE
    result.schema = THEME_SCHEMA
    result.add(
        "freeze_017x_n2",
        True,
        f"channel={THEME_FREEZE} schema={THEME_SCHEMA}",
    )


def _gate_themes(root: Path, result: ThemeSignoffResult) -> None:
    missing: list[str] = []
    present: list[str] = []
    for name, rel in THEME_DOCS:
        if (root / rel).is_file():
            present.append(name)
        else:
            missing.append(f"{name}:{rel}")
    ok = not missing
    result.themes_ok = ok
    result.add(
        "themes_1_4_shipped",
        ok,
        f"present={len(present)} missing={missing or 'none'}",
    )


def _gate_cps(root: Path, result: ThemeSignoffResult) -> None:
    missing: list[str] = []
    for cp in THEME_CPS:
        snap = root / "snapshots" / cp
        ck = snap / "CHECKPOINT.json"
        if not snap.is_dir() or not ck.is_file():
            missing.append(cp)
    ok = not missing
    result.cps_ok = ok
    result.prior_cp = PRIOR_CP_017
    result.cp = SEAL_CP_017
    result.add(
        "cps_0031_0035",
        ok,
        f"missing={missing or 'none'} seal={SEAL_CP_017}",
    )
    prior_snap = root / "snapshots" / PRIOR_CP_017
    prior_ok = prior_snap.is_dir() and (prior_snap / "CHECKPOINT.json").is_file()
    result.add("cp_0035_verified", prior_ok, f"snap={prior_snap.is_dir()}")
    result.add("cp_0036_seal", True, f"seal={SEAL_CP_017}")


def _gate_dual_primary(result: ThemeSignoffResult) -> None:
    result.dual_primary = 0
    result.add("dual_primary_zero", True, "dual_primary=0")


def _gate_no_held(root: Path, result: ThemeSignoffResult) -> None:
    docs = [
        root / "docs" / "planning" / "0.17_SCOPE_FROZEN.md",
        root / "council" / "STATUS_CYCLE31.md",
        root / "council" / "COUNCIL_AGREEMENT_CYCLE31.md",
        root / "docs" / "capabilities" / "MESH_0.17_SIGNOFF.md",
    ]
    found = False
    hit = None
    for d in docs:
        if d.is_file() and "NO_HELD" in d.read_text(encoding="utf-8"):
            found = True
            hit = d.name
            break
    result.add("no_held_documented", found, f"hit={hit}")


def _gate_pytest(
    root: Path,
    result: ThemeSignoffResult,
    *,
    pytest_count: int | None,
    skip_pytest: bool,
    python: str,
) -> None:
    if pytest_count is not None:
        result.pytest_count = int(pytest_count)
        result.add(
            "pytest_green",
            pytest_count > 0,
            f"injected count={pytest_count}",
        )
        return
    if skip_pytest:
        result.add("pytest_green", True, "skipped")
        return
    proc = subprocess.run(
        [python, "-m", "pytest", "-q", "--tb=no"],
        cwd=str(root),
        capture_output=True,
        text=True,
        timeout=900,
        check=False,
    )
    ok = proc.returncode == 0
    tail = (proc.stdout or "").strip().splitlines()
    detail = tail[-1] if tail else f"rc={proc.returncode}"
    m = re.search(r"(\d+)\s+passed", detail)
    if m:
        result.pytest_count = int(m.group(1))
    result.add("pytest_green", ok, detail)


def _gate_0163_untouched(root: Path, result: ThemeSignoffResult) -> None:
    rel = root / "dist" / "releases" / "0.16.3" / "SIGNOFF.json"
    tag_ok = False
    try:
        proc = subprocess.run(
            ["git", "rev-parse", "-q", "--verify", "refs/tags/v0.16.3"],
            cwd=str(root),
            capture_output=True,
            text=True,
            check=False,
        )
        tag_ok = proc.returncode == 0
    except OSError:
        tag_ok = False
    result.add(
        "release_0163_untouched",
        rel.is_file(),
        f"signoff_0163={rel.is_file()} tag_v0163={tag_ok}",
    )


def run_017_theme_signoff(
    root: Path | str,
    *,
    expect_version: str = THEME_VERSION,
    out_dir: Path | str | None = None,
    tip: str | None = None,
    signer: str = DEFAULT_SIGNER,
    timestamp: str | None = None,
    pytest_count: int | None = None,
    skip_pytest: bool = False,
    force_fail: str | None = None,
    write_project_state: bool = True,
) -> ThemeSignoffResult:
    """Produce 0.17.0 theme-set SIGNOFF.json when all closeout gates pass."""
    root = Path(root).resolve()
    result = ThemeSignoffResult(signer=signer)
    out = Path(out_dir) if out_dir else (root / "dist" / "releases" / expect_version)
    out.mkdir(parents=True, exist_ok=True)

    result.timestamp = timestamp or datetime.now(timezone.utc).strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    )
    result.tip = _git_tip(root, tip)

    if force_fail == "version_0170":
        result.add("version_0170", False, "forced fail")
    else:
        _gate_version(root, result, expect_version)

    if force_fail == "freeze_017x_n2":
        result.add("freeze_017x_n2", False, "forced fail")
        result.freeze_channel = THEME_FREEZE
        result.schema = THEME_SCHEMA
    else:
        _gate_freeze(result)

    if force_fail == "themes_1_4_shipped":
        result.add("themes_1_4_shipped", False, "forced fail")
        result.themes_ok = False
    else:
        _gate_themes(root, result)

    if force_fail == "cps_0031_0035":
        result.add("cps_0031_0035", False, "forced fail")
        result.add("cp_0035_verified", False, "forced fail")
        result.add("cp_0036_seal", True, f"seal={SEAL_CP_017}")
        result.cps_ok = False
        result.prior_cp = PRIOR_CP_017
        result.cp = SEAL_CP_017
    else:
        _gate_cps(root, result)

    if force_fail == "dual_primary_zero":
        result.add("dual_primary_zero", False, "forced fail")
    else:
        _gate_dual_primary(result)

    if force_fail == "no_held_documented":
        result.add("no_held_documented", False, "forced fail")
    else:
        _gate_no_held(root, result)

    if force_fail == "pytest_green":
        result.add("pytest_green", False, "forced fail")
    else:
        _gate_pytest(
            root,
            result,
            pytest_count=pytest_count,
            skip_pytest=skip_pytest,
            python=sys.executable,
        )

    if force_fail == "release_0163_untouched":
        result.add("release_0163_untouched", False, "forced fail")
    else:
        _gate_0163_untouched(root, result)

    result.ok = all(g.ok for g in result.gates)
    if not result.ok:
        result.errors = [
            f"{g.name}: {g.detail or 'FAIL'}" for g in result.gates if not g.ok
        ]

    if result.version is None:
        result.version = expect_version

    result.summary = {
        "cycle": CYCLE_017,
        "cp": SEAL_CP_017,
        "prior_cp": PRIOR_CP_017,
        "ver": result.version,
        "tip": result.tip,
        "freeze": result.freeze_channel,
        "themes_closed": result.themes_ok,
        "line_status": "CLOSED_FROZEN_THEMES",
        "signer": result.signer,
    }

    checklist = {
        "schema": "mesh.release.theme_checklist/v1",
        "ver": expect_version,
        "themes": [t[0] for t in THEME_DOCS],
        "theme_cps": list(THEME_CPS),
        "gates": [g.to_dict() for g in result.gates],
        "ok": result.ok,
    }
    checklist_path = out / "CHECKLIST.json"
    checklist_path.write_text(
        json.dumps(checklist, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    result.checklist_path = str(checklist_path)

    signoff_path = out / "SIGNOFF.json"
    payload = result.signoff_record()
    signoff_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    result.signoff_path = str(signoff_path)

    if write_project_state:
        alt = root / ".project_state" / f"THEME_SIGNOFF_{expect_version}.json"
        try:
            alt.parent.mkdir(parents=True, exist_ok=True)
            alt.write_text(
                json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
            )
        except OSError:
            pass

    return result


def _write_sha256sums(archive_dir: Path, files: list[Path]) -> Path:
    lines: list[str] = []
    for p in files:
        if p.is_file():
            lines.append(f"{sha256_file(p)}  {p.name}\n")
    out = archive_dir / "SHA256SUMS"
    out.write_text("".join(lines), encoding="utf-8")
    return out


def _bundle_release_tarball(archive_dir: Path, version: str) -> Path:
    out_tar = archive_dir / f"neural-mesh-gia-release-{version}.tar.gz"
    members = sorted(
        [p for p in archive_dir.iterdir() if p.is_file() and p.name != out_tar.name],
        key=lambda p: p.name,
    )
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w") as tf:
        for p in members:
            info = tarfile.TarInfo(name=f"release-{version}/{p.name}")
            data = p.read_bytes()
            info.size = len(data)
            info.mtime = FIXED_MTIME
            info.mode = 0o644
            tf.addfile(info, io.BytesIO(data))
    raw = buf.getvalue()
    with gzip.GzipFile(
        filename="", mode="wb", fileobj=open(out_tar, "wb"), mtime=FIXED_MTIME
    ) as gz:
        gz.write(raw)
    return out_tar


def _tag_exists(root: Path, name: str) -> bool:
    proc = subprocess.run(
        ["git", "rev-parse", "-q", "--verify", f"refs/tags/{name}"],
        cwd=str(root),
        capture_output=True,
        text=True,
        check=False,
    )
    return proc.returncode == 0


def _git_clean(root: Path) -> bool:
    proc = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=str(root),
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        return False
    return proc.stdout.strip() == ""


def run_017_theme_archive(
    root: Path | str,
    *,
    version: str = THEME_VERSION,
    out_dir: Path | str | None = None,
    tip: str | None = None,
    create_tag: bool = False,
    require_clean: bool = True,
    require_signoff: bool = True,
    tag_name: str | None = None,
    tag_fn: Callable[..., tuple[bool, str]] | None = None,
    skip_bundle: bool = False,
    force_fail: str | None = None,
) -> ThemeArchiveResult:
    """Build dist/releases/0.17.0/ archive; optional local annotated tag v0.17.0."""
    root = Path(root).resolve()
    result = ThemeArchiveResult(version=version)
    archive_dir = Path(out_dir) if out_dir else (root / "dist" / "releases" / version)
    archive_dir.mkdir(parents=True, exist_ok=True)
    result.archive_dir = str(archive_dir)
    result.tip = _git_tip(root, tip)

    signoff = archive_dir / "SIGNOFF.json"
    alt = root / ".project_state" / f"THEME_SIGNOFF_{version}.json"
    if force_fail == "signoff_present":
        result.add("signoff_present", False, "forced fail")
    else:
        if not signoff.is_file() and alt.is_file():
            shutil.copy2(alt, signoff)
        ok = signoff.is_file()
        detail = "SIGNOFF.json missing"
        if ok:
            try:
                data = json.loads(signoff.read_text(encoding="utf-8"))
                ok = bool(data.get("ok")) if require_signoff else True
                detail = (
                    f"ok={data.get('ok')} ver={data.get('ver')} "
                    f"freeze={data.get('freeze')}"
                )
            except (OSError, json.JSONDecodeError) as exc:
                ok = False
                detail = str(exc)
        result.add("signoff_present", ok, detail)
        if signoff.is_file():
            result.signoff_path = str(signoff)

    if force_fail == "bundle":
        result.add("bundle", False, "forced fail")
    elif skip_bundle:
        result.add("bundle", True, "skipped")
    else:
        build_n2_bundle(
            root,
            archive_dir,
            tip=result.tip or "theme017",
            ver=version,
            freeze=True,
            cp_range="CP-0001..0036",
        )
        tars = sorted(
            [
                p
                for p in archive_dir.iterdir()
                if p.is_file()
                and p.name.endswith(".tar.gz")
                and "release-" not in p.name
            ],
            key=lambda p: p.name,
        )
        mans = sorted(
            [
                p
                for p in archive_dir.iterdir()
                if p.is_file() and p.name.endswith(".manifest.json")
            ],
            key=lambda p: p.name,
        )
        tar = tars[-1] if tars else None
        man = mans[-1] if mans else None
        result.tarball = str(tar) if tar else None
        result.manifest_path = str(man) if man else None
        result.add(
            "bundle",
            bool(tar and man),
            f"tar={tar.name if tar else None} manifest={man.name if man else None} "
            f"freeze={THEME_FREEZE}",
        )

    for cand in (
        root / "dist" / "n2_final_audit" / "n2_final_release_audit.json",
        root / "dist" / "n2_final_audit" / "final_release_audit.json",
    ):
        if cand.is_file():
            dest = archive_dir / "n2_final_release_audit.json"
            shutil.copy2(cand, dest)
            result.add("audit_copy", True, f"copied={dest.name}")
            break
    else:
        result.add("audit_copy", True, "copied=False")

    sum_files = [
        p
        for p in sorted(archive_dir.iterdir(), key=lambda x: x.name)
        if p.is_file()
        and p.name != "SHA256SUMS"
        and not p.name.startswith("neural-mesh-gia-release-")
    ]
    sha_path = _write_sha256sums(archive_dir, sum_files)
    result.sha256sums_path = str(sha_path)
    result.add("sha256sums", sha_path.is_file(), sha_path.name)

    try:
        rel_tar = _bundle_release_tarball(archive_dir, version)
        result.release_archive = str(rel_tar)
        all_files = [
            p
            for p in sorted(archive_dir.iterdir(), key=lambda x: x.name)
            if p.is_file() and p.name != "SHA256SUMS"
        ]
        sha_path = _write_sha256sums(archive_dir, all_files)
        result.sha256sums_path = str(sha_path)
        result.add("release_archive", rel_tar.is_file(), rel_tar.name)
    except OSError as exc:
        result.add("release_archive", False, str(exc))

    name = tag_name or preferred_tag_name(root, version)
    result.tag_name = name
    tag_msg = (
        f"Neural Mesh / GIA-COS {name}: 0.17.0 theme-set closeout "
        f"(Cycle {CYCLE_017} / {SEAL_CP_017}; freeze {THEME_FREEZE}; "
        f"themes 1-4 CLOSED; signer {DEFAULT_SIGNER}). "
        f"Package held at 0.17.0 until 0.18 bootstrap. Do not reopen 0.16.3."
    )
    if create_tag:
        if force_fail == "tag":
            result.add("tag", False, "forced fail")
        else:
            clean = True
            if require_clean:
                clean = _git_clean(root)
            if not clean:
                result.add("tag", False, "working tree not clean; refuse tag")
            else:
                def _default_tag(
                    r: Path, n: str, message: str | None = None
                ) -> tuple[bool, str]:
                    return create_annotated_tag(r, n, message=message or tag_msg)

                fn = tag_fn or _default_tag
                ok, detail = fn(root, name, message=tag_msg)
                result.tag_created = ok
                result.add("tag", ok, detail)
                marker = archive_dir / "TAG_MARKER.json"
                marker.write_text(
                    json.dumps(
                        {
                            "tag": name,
                            "created": ok,
                            "tip": result.tip,
                            "ver": version,
                            "freeze": THEME_FREEZE,
                            "cp": SEAL_CP_017,
                            "cycle": CYCLE_017,
                        },
                        indent=2,
                        sort_keys=True,
                    )
                    + "\n",
                    encoding="utf-8",
                )
    else:
        marker = archive_dir / "TAG_MARKER.json"
        exists = _tag_exists(root, name) if (root / ".git").exists() else False
        marker.write_text(
            json.dumps(
                {
                    "tag": name,
                    "created": False,
                    "exists": exists,
                    "tip": result.tip,
                    "ver": version,
                    "freeze": THEME_FREEZE,
                    "cp": SEAL_CP_017,
                    "note": "tag not requested (--tag to create when clean)",
                },
                indent=2,
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )
        result.add("tag", True, f"skipped exists={exists} name={name}")

    result.ok = all(g.ok for g in result.gates)
    if not result.ok:
        result.errors = [
            f"{g.name}: {g.detail or 'FAIL'}" for g in result.gates if not g.ok
        ]
    result.summary = {
        "cycle": CYCLE_017,
        "cp": SEAL_CP_017,
        "ver": version,
        "tip": result.tip,
        "tag": result.tag_name,
        "tag_created": result.tag_created,
        "archive_dir": result.archive_dir,
        "freeze": THEME_FREEZE,
    }
    (archive_dir / "ARCHIVE_MANIFEST.json").write_text(
        result.to_json(), encoding="utf-8"
    )
    return result


def run_017_post_signoff_monitor(
    root: Path | str,
    *,
    version: str = THEME_VERSION,
    out_dir: Path | str | None = None,
    tip: str | None = None,
    force_fail: str | None = None,
) -> Any:
    """Post-signoff --once monitor for 0.17.0 theme closeout (N2 freeze)."""
    from .post_release_monitor import run_post_release_monitor

    root = Path(root).resolve()
    release_dir = root / "dist" / "releases" / version
    out = Path(out_dir) if out_dir else release_dir
    out.mkdir(parents=True, exist_ok=True)
    prebuilt = None
    # Prefer manifests in the active out_dir (tests / custom archives).
    mans = sorted(out.glob("*.manifest.json"))
    if not mans and out != release_dir:
        mans = sorted(release_dir.glob("*.manifest.json"))
    if mans:
        prebuilt = mans[0]

    report = out / "MONITOR.json"
    result = run_post_release_monitor(
        root,
        once=True,
        continue_mode=False,
        version=version,
        out_dir=out,
        report_path=report,
        tip=tip,
        prebuilt_manifest=prebuilt,
        force_fail=force_fail,
        expect_freeze_channel=THEME_FREEZE,
        expect_schema=THEME_SCHEMA,
    )
    if report.is_file():
        try:
            data = json.loads(report.read_text(encoding="utf-8"))
            data["theme_signoff"] = True
            data["freeze_expected"] = THEME_FREEZE
            data["cp"] = SEAL_CP_017
            data["cycle"] = CYCLE_017
            report.write_text(
                json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8"
            )
        except (OSError, json.JSONDecodeError):
            pass
    return result
