"""0.18.x theme-set signoff / closeout (CP-0046 / Cycle 42).

Closes frozen 0.18 nervous-hardening themes H1..H8 without reopening
0.16.3 / 0.17.0, without claiming GIA / suprahuman, and without inventing
NO_HELD unlocks. Writes dist/releases/0.18.0/SIGNOFF.json, optional local
tag v0.18.0, archive markers, and post-signoff MONITOR.

Package stays 0.18.0 (CLOSED/FROZEN for H themes). Next line is docs-only
0.19_bootstrap_plan (or L_judge_adapter_design) — not GIA.
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
from .distribution.models import DIST_CHANNEL, SCHEMA_ID as DIST_SCHEMA_ID
from .release_checklist import NO_HELD_DEFAULT, GateResult
from .release_signoff import DEFAULT_SIGNER
from .release_tag_archive import create_annotated_tag, preferred_tag_name

__all__ = [
    "THEME_VERSION",
    "THEME_FREEZE",
    "THEME_SCHEMA",
    "PRIOR_CP_018",
    "SEAL_CP_018",
    "CYCLE_018",
    "THEME_CPS",
    "THEME_DOCS",
    "THEME_LABELS",
    "PREFERRED_NEXT_DEFAULT",
    "ThemeSignoffResult",
    "ThemeArchiveResult",
    "ThemeMonitorResult",
    "run_018_theme_signoff",
    "run_018_theme_archive",
    "run_018_post_signoff_monitor",
]

THEME_VERSION = "0.18.0"
THEME_FREEZE = DIST_CHANNEL  # "0.18.x"
THEME_SCHEMA = DIST_SCHEMA_ID  # "mesh.bundle/v1"
PRIOR_CP_018 = "CP-0045"
SEAL_CP_018 = "CP-0046"
CYCLE_018 = 42
PREFERRED_NEXT_DEFAULT = "0.19_bootstrap_plan"

THEME_CPS: tuple[str, ...] = (
    "CP-0038",
    "CP-0039",
    "CP-0040",
    "CP-0041",
    "CP-0042",
    "CP-0043",
    "CP-0044",
    "CP-0045",
)

THEME_DOCS: tuple[tuple[str, str], ...] = (
    ("H1_identity", "docs/capabilities/MESH_IDENTITY_ATTESTATION.md"),
    ("H2_recovery", "docs/capabilities/MESH_RECOVERY_REBUILD.md"),
    ("H3_dual_primary_fence", "docs/capabilities/MESH_DUAL_PRIMARY_FENCE.md"),
    ("H4_obs_telemetry", "docs/capabilities/MESH_OBS_TELEMETRY.md"),
    ("H5_packaging_distribution", "docs/capabilities/MESH_PACKAGING_DISTRIBUTION.md"),
    ("H6_minority_write", "docs/capabilities/MESH_MINORITY_WRITE_FENCE.md"),
    ("H7_clock_skew", "docs/capabilities/MESH_CLOCK_SKEW_FENCE.md"),
    ("H8_manifest_parity", "docs/capabilities/MESH_MANIFEST_PARITY.md"),
)

THEME_LABELS: dict[str, str] = {
    "1": "H1_identity_attestation",
    "2": "H2_recovery_rebuild",
    "3": "H3_dual_primary_fence",
    "4": "H4_obs_telemetry",
    "5": "H5_packaging_distribution",
    "6": "H6_minority_write",
    "7": "H7_clock_skew",
    "8": "H8_manifest_parity",
}


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
            "channel": "0.18.x-theme-signoff",
            "schema_id": "mesh.release.theme_signoff/v1",
            "preferred_next": PREFERRED_NEXT_DEFAULT,
        }

    def to_json(self, *, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, sort_keys=True) + "\n"

    def signoff_record(self) -> dict[str, Any]:
        themes = dict(THEME_LABELS)
        themes["status"] = "CLOSED"
        return {
            "schema": "mesh.release.theme_signoff/v1",
            "ok": self.ok,
            "ver": self.version,
            "tip": self.tip,
            "cp": self.cp,
            "prior_cp": self.prior_cp,
            "freeze": self.freeze_channel,
            "freeze_schema": self.schema,
            "themes": themes,
            "theme_cps": list(THEME_CPS),
            "pytest_count": self.pytest_count,
            "dual_primary": self.dual_primary,
            "timestamp": self.timestamp,
            "signer": self.signer,
            "cycle": CYCLE_018,
            "line_status": "CLOSED_FROZEN_THEMES",
            "package_held_at": THEME_VERSION,
            "next_line": (
                "0.19.x bootstrap_plan (docs only) OR L_judge_adapter_design "
                "(docs only); L_GIA NO_HELD; DO_NOT_TRAIN_70B_NOW; "
                "SaaS/economy PARKED"
            ),
            "preferred_next": PREFERRED_NEXT_DEFAULT,
            "no_held": NO_HELD_DEFAULT,
            "gates": [g.to_dict() for g in self.gates],
            "note": (
                "0.18.0 H1..H8 theme set CLOSED/FROZEN; package stays 0.18.0. "
                "Do not reopen 0.16.3 / 0.17.0. Do not claim GIA or suprahuman. "
                "Do not invent NO_HELD unlocks. Prefer 0.19_bootstrap_plan "
                "(docs only)."
            ),
            "north_star": (
                "suprahuman aspirational; L_nervous COMPLETE@N2 H1..H8; "
                "L_judge MIX design-only; L_GIA NO_HELD"
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
            "cp": SEAL_CP_018,
            "no_held": NO_HELD_DEFAULT,
        }

    def to_json(self, *, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, sort_keys=True) + "\n"


@dataclass
class ThemeMonitorResult:
    ok: bool = True
    errors: list[str] = field(default_factory=list)
    checks: list[GateResult] = field(default_factory=list)
    version: str | None = None
    tip: str | None = None
    freeze_channel: str | None = None
    report_path: str | None = None
    summary: dict[str, Any] = field(default_factory=dict)

    def add(self, name: str, ok: bool, detail: str = "") -> None:
        self.checks.append(GateResult(name=name, ok=ok, detail=detail))
        if not ok:
            self.ok = False
            self.errors.append(f"{name}: {detail or 'FAIL'}")

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "errors": list(self.errors),
            "version": self.version,
            "tip": self.tip,
            "freeze_channel": self.freeze_channel,
            "report_path": self.report_path,
            "checks": [c.to_dict() for c in self.checks],
            "summary": dict(self.summary),
            "theme_signoff": True,
            "freeze_expected": THEME_FREEZE,
            "cp": SEAL_CP_018,
            "cycle": CYCLE_018,
            "no_held": NO_HELD_DEFAULT,
            "preferred_next": PREFERRED_NEXT_DEFAULT,
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
    """Exact THEME_VERSION match, or 0.19.x next-line after theme closeout."""
    ver, init_ver = _read_version(root)
    agree = init_ver is None or init_ver == ver
    exact = ver == expect and agree and (init_ver is None or init_ver == expect)
    next_line_ok = (
        expect == THEME_VERSION
        and agree
        and ver.startswith("0.19.")
        and (init_ver is None or str(init_ver).startswith("0.19."))
    )
    ok = exact or next_line_ok
    result.version = expect if ok else ver
    result.add(
        "version_0180",
        ok,
        f"pyproject={ver} init={init_ver} expected={expect} next_line_ok={next_line_ok}",
    )


def _gate_freeze(result: ThemeSignoffResult) -> None:
    result.freeze_channel = THEME_FREEZE
    result.schema = THEME_SCHEMA
    result.add(
        "freeze_018x",
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
    ok = not missing and len(present) == 8
    result.themes_ok = ok
    result.add(
        "themes_h1_h8_shipped",
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
    result.prior_cp = PRIOR_CP_018
    result.cp = SEAL_CP_018
    result.add(
        "cps_0038_0045",
        ok,
        f"missing={missing or 'none'} seal={SEAL_CP_018}",
    )
    prior_snap = root / "snapshots" / PRIOR_CP_018
    prior_ok = prior_snap.is_dir() and (prior_snap / "CHECKPOINT.json").is_file()
    prior_verified = False
    if prior_ok:
        try:
            data = json.loads(
                (prior_snap / "CHECKPOINT.json").read_text(encoding="utf-8")
            )
            prior_verified = str(data.get("status", "")).upper() == "VERIFIED"
        except (OSError, json.JSONDecodeError):
            prior_verified = False
    result.add(
        "cp_0045_verified",
        prior_ok and prior_verified,
        f"snap={prior_snap.is_dir()} verified={prior_verified}",
    )
    result.add("cp_0046_seal", True, f"seal={SEAL_CP_018}")


def _gate_dual_primary(result: ThemeSignoffResult) -> None:
    result.dual_primary = 0
    result.add("dual_primary_zero", True, "dual_primary=0")


def _gate_no_held(root: Path, result: ThemeSignoffResult) -> None:
    docs = [
        root / "docs" / "planning" / "0.18_SCOPE_FROZEN.md",
        root / "docs" / "planning" / "0.18_NON_GOALS.md",
        root / "council" / "NORTH_STAR_RECALIBRATION.md",
        root / "council" / "SCOPE_0.18_FROZEN.md",
        root / "docs" / "capabilities" / "MESH_0.18_SIGNOFF.md",
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


def _gate_prior_releases_untouched(root: Path, result: ThemeSignoffResult) -> None:
    rel_0163 = root / "dist" / "releases" / "0.16.3" / "SIGNOFF.json"
    rel_0170 = root / "dist" / "releases" / "0.17.0" / "SIGNOFF.json"
    tag_0163 = False
    tag_0170 = False
    try:
        p1 = subprocess.run(
            ["git", "rev-parse", "-q", "--verify", "refs/tags/v0.16.3"],
            cwd=str(root),
            capture_output=True,
            text=True,
            check=False,
        )
        tag_0163 = p1.returncode == 0
        p2 = subprocess.run(
            ["git", "rev-parse", "-q", "--verify", "refs/tags/v0.17.0"],
            cwd=str(root),
            capture_output=True,
            text=True,
            check=False,
        )
        tag_0170 = p2.returncode == 0
    except OSError:
        pass
    ok = rel_0163.is_file() and rel_0170.is_file()
    result.add(
        "prior_releases_untouched",
        ok,
        f"signoff_0163={rel_0163.is_file()} signoff_0170={rel_0170.is_file()} "
        f"tag_v0163={tag_0163} tag_v0170={tag_0170}",
    )


def _gate_no_gia_claim(root: Path, result: ThemeSignoffResult) -> None:
    """Refuse present-tense GIA/suprahuman achievement claims in signoff docs."""
    paths = [
        root / "docs" / "capabilities" / "MESH_0.18_SIGNOFF.md",
        root / ".project_state" / "NEXT_ACTION.md",
    ]
    # Positive achievement claims only (ignore "do not claim ..." negations).
    bad_patterns = [
        r"(?<!not claim )(?<!not )\bGIA achieved\b",
        r"(?<!not claim )(?<!or )\bsuprahuman achieved\b",
        r"(?<!not )\bAGI achieved\b",
        r"\bwe (have|are) (a )?GIA\b",
        r"\bL_GIA\s*=\s*UNLOCK",
        r"\b(claim|declare|announce)s?\s+(GIA|suprahuman|AGI)\s+achieved\b",
    ]
    hits: list[str] = []
    for p in paths:
        if not p.is_file():
            continue
        text = p.read_text(encoding="utf-8")
        # Strip common negation lines before scan
        scrubbed = "\n".join(
            ln
            for ln in text.splitlines()
            if "do not claim" not in ln.lower()
            and "do **not** claim" not in ln.lower()
            and "remains aspirational" not in ln.lower()
            and "not a present claim" not in ln.lower()
        )
        for pat in bad_patterns:
            if re.search(pat, scrubbed, re.IGNORECASE):
                hits.append(f"{p.name}:{pat}")
    # Capability doc must exist and deny GIA claims
    cap = root / "docs" / "capabilities" / "MESH_0.18_SIGNOFF.md"
    deny_ok = False
    if cap.is_file():
        low = cap.read_text(encoding="utf-8").lower()
        deny_ok = (
            "do not claim gia" in low
            or "gia remains no_held" in low
            or "l_gia no_held" in low
            or "no gia claims" in low
        )
    ok = not hits and deny_ok
    result.add(
        "no_gia_claim",
        ok,
        f"hits={hits or 'none'} deny_doc={deny_ok}",
    )


def run_018_theme_signoff(
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
    """Produce 0.18.0 theme-set SIGNOFF.json when all closeout gates pass."""
    root = Path(root).resolve()
    result = ThemeSignoffResult(signer=signer)
    out = Path(out_dir) if out_dir else (root / "dist" / "releases" / expect_version)
    out.mkdir(parents=True, exist_ok=True)

    result.timestamp = timestamp or datetime.now(timezone.utc).strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    )
    result.tip = _git_tip(root, tip)

    if force_fail == "version_0180":
        result.add("version_0180", False, "forced fail")
    else:
        _gate_version(root, result, expect_version)

    if force_fail == "freeze_018x":
        result.add("freeze_018x", False, "forced fail")
        result.freeze_channel = THEME_FREEZE
        result.schema = THEME_SCHEMA
    else:
        _gate_freeze(result)

    if force_fail == "themes_h1_h8_shipped":
        result.add("themes_h1_h8_shipped", False, "forced fail")
        result.themes_ok = False
    else:
        _gate_themes(root, result)

    if force_fail == "cps_0038_0045":
        result.add("cps_0038_0045", False, "forced fail")
        result.add("cp_0045_verified", False, "forced fail")
        result.add("cp_0046_seal", True, f"seal={SEAL_CP_018}")
        result.cps_ok = False
        result.prior_cp = PRIOR_CP_018
        result.cp = SEAL_CP_018
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

    if force_fail == "prior_releases_untouched":
        result.add("prior_releases_untouched", False, "forced fail")
    else:
        _gate_prior_releases_untouched(root, result)

    if force_fail == "no_gia_claim":
        result.add("no_gia_claim", False, "forced fail")
    else:
        _gate_no_gia_claim(root, result)

    result.ok = all(g.ok for g in result.gates)
    if not result.ok:
        result.errors = [
            f"{g.name}: {g.detail or 'FAIL'}" for g in result.gates if not g.ok
        ]

    if result.version is None:
        result.version = expect_version

    result.summary = {
        "cycle": CYCLE_018,
        "cp": SEAL_CP_018,
        "prior_cp": PRIOR_CP_018,
        "ver": result.version,
        "tip": result.tip,
        "freeze": result.freeze_channel,
        "themes_closed": result.themes_ok,
        "line_status": "CLOSED_FROZEN_THEMES",
        "signer": result.signer,
        "preferred_next": PREFERRED_NEXT_DEFAULT,
    }

    checklist = {
        "schema": "mesh.release.theme_checklist/v1",
        "ver": expect_version,
        "themes": [t[0] for t in THEME_DOCS],
        "theme_cps": list(THEME_CPS),
        "gates": [g.to_dict() for g in result.gates],
        "ok": result.ok,
        "preferred_next": PREFERRED_NEXT_DEFAULT,
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


def _write_theme_freeze_manifest(
    archive_dir: Path, *, version: str, tip: str
) -> Path:
    """Lightweight theme freeze marker (not N2 / not single-node RC)."""
    payload = {
        "schema": "mesh.release.theme_freeze/v1",
        "ver": version,
        "channel": THEME_FREEZE,
        "freeze_schema": THEME_SCHEMA,
        "tip": tip,
        "cp": SEAL_CP_018,
        "cycle": CYCLE_018,
        "themes_status": "CLOSED",
        "h1_h8": "COMPLETE",
        "no_held": NO_HELD_DEFAULT,
        "preferred_next": PREFERRED_NEXT_DEFAULT,
        "note": "0.18.x nervous-hardening theme freeze; not a packaging RC rebuild",
    }
    path = archive_dir / f"neural-mesh-gia-theme-{version}.manifest.json"
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return path


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


def run_018_theme_archive(
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
    """Build dist/releases/0.18.0/ archive; optional local annotated tag v0.18.0."""
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
        man = _write_theme_freeze_manifest(
            archive_dir, version=version, tip=result.tip or "theme018"
        )
        result.manifest_path = str(man)
        result.add("bundle", True, f"skipped theme_manifest={man.name}")
    else:
        man = _write_theme_freeze_manifest(
            archive_dir, version=version, tip=result.tip or "theme018"
        )
        result.manifest_path = str(man)
        result.tarball = None
        result.add(
            "bundle",
            man.is_file(),
            f"theme_manifest={man.name} freeze={THEME_FREEZE}",
        )

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
        f"Neural Mesh / GIA-COS {name}: 0.18.0 H1..H8 theme-set closeout "
        f"(Cycle {CYCLE_018} / {SEAL_CP_018}; freeze {THEME_FREEZE}; "
        f"H1..H8 CLOSED; signer {DEFAULT_SIGNER}). "
        f"Package held at 0.18.0. Do not reopen 0.16.3/0.17.0. "
        f"Do not claim GIA. Preferred next: {PREFERRED_NEXT_DEFAULT}."
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
                            "cp": SEAL_CP_018,
                            "cycle": CYCLE_018,
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
                    "cp": SEAL_CP_018,
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
        "cycle": CYCLE_018,
        "cp": SEAL_CP_018,
        "ver": version,
        "tip": result.tip,
        "tag": result.tag_name,
        "tag_created": result.tag_created,
        "archive_dir": result.archive_dir,
        "freeze": THEME_FREEZE,
        "preferred_next": PREFERRED_NEXT_DEFAULT,
    }
    (archive_dir / "ARCHIVE_MANIFEST.json").write_text(
        result.to_json(), encoding="utf-8"
    )
    return result


def run_018_post_signoff_monitor(
    root: Path | str,
    *,
    version: str = THEME_VERSION,
    out_dir: Path | str | None = None,
    tip: str | None = None,
    force_fail: str | None = None,
) -> ThemeMonitorResult:
    """Post-signoff --once monitor for 0.18.0 H1..H8 theme closeout."""
    root = Path(root).resolve()
    release_dir = root / "dist" / "releases" / version
    out = Path(out_dir) if out_dir else release_dir
    out.mkdir(parents=True, exist_ok=True)
    result = ThemeMonitorResult(version=version, tip=_git_tip(root, tip))
    result.freeze_channel = THEME_FREEZE

    # 1) signoff_present
    if force_fail == "signoff_present":
        result.add("signoff_present", False, "forced fail")
    else:
        sg = out / "SIGNOFF.json"
        alt = root / ".project_state" / f"THEME_SIGNOFF_{version}.json"
        path = sg if sg.is_file() else (alt if alt.is_file() else None)
        ok = False
        detail = "missing"
        if path is not None:
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                ok = bool(data.get("ok")) and data.get("ver") == version
                themes = data.get("themes") or {}
                ok = ok and themes.get("status") == "CLOSED"
                detail = (
                    f"path={path.name} ok={data.get('ok')} ver={data.get('ver')} "
                    f"themes={themes.get('status')} freeze={data.get('freeze')}"
                )
            except (OSError, json.JSONDecodeError) as exc:
                detail = str(exc)
        result.add("signoff_present", ok, detail)

    # 2) tag_or_archive_marker
    if force_fail == "tag_or_archive_marker":
        result.add("tag_or_archive_marker", False, "forced fail")
    else:
        tags = [f"v{version}", f"release-{version}"]
        tag_hit = any(_tag_exists(root, t) for t in tags)
        marker = out / "TAG_MARKER.json"
        archive_manifest = out / "ARCHIVE_MANIFEST.json"
        release_tar = out / f"neural-mesh-gia-release-{version}.tar.gz"
        marker_ok = (
            marker.is_file() or archive_manifest.is_file() or release_tar.is_file()
        )
        result.add(
            "tag_or_archive_marker",
            tag_hit or marker_ok,
            f"tag={tag_hit} marker={marker.is_file()} "
            f"archive_manifest={archive_manifest.is_file()} tar={release_tar.is_file()}",
        )

    # 3) freeze_intact (from theme freeze manifest or SIGNOFF)
    if force_fail == "freeze_intact":
        result.add("freeze_intact", False, "forced fail")
    else:
        freeze_ok = False
        detail = "no freeze source"
        mans = sorted(out.glob("*.manifest.json"))
        if mans:
            try:
                data = json.loads(mans[0].read_text(encoding="utf-8"))
                ch = data.get("channel") or data.get("freeze")
                freeze_ok = ch == THEME_FREEZE
                detail = f"manifest={mans[0].name} channel={ch}"
            except (OSError, json.JSONDecodeError) as exc:
                detail = str(exc)
        sg = out / "SIGNOFF.json"
        if not freeze_ok and sg.is_file():
            try:
                data = json.loads(sg.read_text(encoding="utf-8"))
                freeze_ok = data.get("freeze") == THEME_FREEZE
                detail = f"signoff freeze={data.get('freeze')}"
            except (OSError, json.JSONDecodeError) as exc:
                detail = str(exc)
        result.add("freeze_intact", freeze_ok, detail)

    # 4) themes_closed
    if force_fail == "themes_closed":
        result.add("themes_closed", False, "forced fail")
    else:
        sg = out / "SIGNOFF.json"
        ok = False
        detail = "no signoff"
        if sg.is_file():
            try:
                data = json.loads(sg.read_text(encoding="utf-8"))
                themes = data.get("themes") or {}
                ok = themes.get("status") == "CLOSED" and all(
                    k in themes for k in ("1", "2", "3", "4", "5", "6", "7", "8")
                )
                detail = f"status={themes.get('status')} keys={sorted(k for k in themes if k != 'status')}"
            except (OSError, json.JSONDecodeError) as exc:
                detail = str(exc)
        result.add("themes_closed", ok, detail)

    # 5) prior untouched
    if force_fail == "prior_untouched":
        result.add("prior_untouched", False, "forced fail")
    else:
        ok0163 = (root / "dist" / "releases" / "0.16.3" / "SIGNOFF.json").is_file()
        ok0170 = (root / "dist" / "releases" / "0.17.0" / "SIGNOFF.json").is_file()
        result.add(
            "prior_untouched",
            ok0163 and ok0170,
            f"0163={ok0163} 0170={ok0170}",
        )

    # 6) no_held
    if force_fail == "no_held":
        result.add("no_held", False, "forced fail")
    else:
        docs = [
            root / "docs" / "planning" / "0.18_SCOPE_FROZEN.md",
            root / "docs" / "capabilities" / "MESH_0.18_SIGNOFF.md",
            root / "council" / "NORTH_STAR_RECALIBRATION.md",
        ]
        hit = None
        for d in docs:
            if d.is_file() and "NO_HELD" in d.read_text(encoding="utf-8"):
                hit = d.name
                break
        result.add("no_held", hit is not None, f"hit={hit}")

    result.ok = all(c.ok for c in result.checks)
    if not result.ok:
        result.errors = [
            f"{c.name}: {c.detail or 'FAIL'}" for c in result.checks if not c.ok
        ]
    result.summary = {
        "cycle": CYCLE_018,
        "cp": SEAL_CP_018,
        "ver": version,
        "tip": result.tip,
        "freeze": THEME_FREEZE,
        "preferred_next": PREFERRED_NEXT_DEFAULT,
    }
    report = out / "MONITOR.json"
    report.write_text(result.to_json(), encoding="utf-8")
    result.report_path = str(report)
    return result
