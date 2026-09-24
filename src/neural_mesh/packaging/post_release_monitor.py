"""Post-release monitor for single-node RC (CP-0028 / P20; CP-0029 / P21 continue).

Extends/complements post_rc_watch: --once checks after release signoff/tag/archive.
--continue re-runs --once, appends monitor_history.jsonl, exits 0 if still healthy.
Writes MONITOR.json under dist/releases/0.16.3/.
Schedule stub only — do NOT create Grok Bot routines.
"""

from __future__ import annotations

import json
import re
import subprocess
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .bundle import build_bundle, load_manifest
from .manifest import FREEZE_CHANNEL, SCHEMA_ID
from .post_rc_watch import (
    OBS_STABLE_FIELDS,
    _check_debt_schema_gated,
    _check_obs_fields_stable,
    _check_no_tag_schema_drift,
)
from .release_checklist import NO_HELD_DEFAULT
from .release_signoff import RELEASE_VERSION, SEAL_CP

__all__ = [
    "MONITOR_CHECKLIST",
    "HISTORY_BASENAME",
    "MonitorCheck",
    "MonitorResult",
    "run_post_release_monitor",
    "append_monitor_history",
]

MONITOR_CHECKLIST = (
    "signoff_present",
    "tag_or_archive_marker",
    "freeze_intact",
    "debt_schema_gated",
    "obs_stable_fields",
    "no_forbidden_drift",
)

HISTORY_BASENAME = "monitor_history.jsonl"
# Soft roll: keep last N entries when rewriting (rare; append-first).
HISTORY_ROLL_MAX = 500


@dataclass
class MonitorCheck:
    name: str
    ok: bool
    detail: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {"name": self.name, "ok": self.ok, "detail": self.detail}


@dataclass
class MonitorResult:
    ok: bool = True
    errors: list[str] = field(default_factory=list)
    checks: list[MonitorCheck] = field(default_factory=list)
    checklist: tuple[str, ...] = MONITOR_CHECKLIST
    version: str | None = None
    tip: str | None = None
    freeze_channel: str | None = None
    report_path: str | None = None
    history_path: str | None = None
    mode: str = "once"
    no_held: str = NO_HELD_DEFAULT
    notes: list[str] = field(default_factory=list)
    history_appended: bool = False

    def add(self, name: str, ok: bool, detail: str = "") -> None:
        self.checks.append(MonitorCheck(name=name, ok=ok, detail=detail))
        if not ok:
            self.ok = False
            self.errors.append(f"{name}: {detail or 'FAIL'}")

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "errors": list(self.errors),
            "mode": self.mode,
            "checklist": list(self.checklist),
            "checks": [c.to_dict() for c in self.checks],
            "version": self.version,
            "tip": self.tip,
            "freeze_channel": self.freeze_channel,
            "report_path": self.report_path,
            "history_path": self.history_path,
            "history_appended": self.history_appended,
            "no_held": self.no_held,
            "notes": list(self.notes),
            "cp": "CP-0029" if self.mode == "continue" else SEAL_CP,
            "cycle": 25 if self.mode == "continue" else 24,
            "scheduled_routine": {
                "status": "documented_only",
                "create_grok_bot_routine": False,
                "hint": (
                    "Future: cron/CI may invoke "
                    "scripts/post_release_monitor.py --once "
                    "or --continue"
                ),
            },
        }

    def to_json(self, *, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, sort_keys=True) + "\n"

    def history_record(self) -> dict[str, Any]:
        """Compact JSONL record for continue-mode history."""
        return {
            "ts": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "ok": self.ok,
            "mode": self.mode,
            "version": self.version,
            "tip": self.tip,
            "errors": list(self.errors),
            "checks": {c.name: c.ok for c in self.checks},
        }


def _check_signoff(root: Path, result: MonitorResult, version: str, release_dir: Path) -> None:
    candidates = [
        release_dir / "SIGNOFF.json",
        root / ".project_state" / f"RELEASE_SIGNOFF_{version}.json",
    ]
    found = None
    for p in candidates:
        if p.is_file():
            found = p
            break
    if found is None:
        result.add("signoff_present", False, "SIGNOFF.json missing")
        return
    try:
        data = json.loads(found.read_text(encoding="utf-8"))
        ok = bool(data.get("ok")) and str(data.get("ver")) == version
        result.version = str(data.get("ver") or version)
        result.tip = data.get("tip")
        result.add(
            "signoff_present",
            ok,
            f"path={found.name} ok={data.get('ok')} ver={data.get('ver')}",
        )
    except (OSError, json.JSONDecodeError) as exc:
        result.add("signoff_present", False, str(exc))


def _tag_exists(root: Path, name: str) -> bool:
    if not (root / ".git").exists():
        return False
    proc = subprocess.run(
        ["git", "rev-parse", "-q", "--verify", f"refs/tags/{name}"],
        cwd=str(root),
        capture_output=True,
        text=True,
        check=False,
    )
    return proc.returncode == 0


def _check_tag_or_marker(
    root: Path, result: MonitorResult, version: str, release_dir: Path
) -> None:
    tags = [f"v{version}", f"release-{version}"]
    tag_hit = any(_tag_exists(root, t) for t in tags)
    marker = release_dir / "TAG_MARKER.json"
    archive_manifest = release_dir / "ARCHIVE_MANIFEST.json"
    release_tar = release_dir / f"neural-mesh-gia-release-{version}.tar.gz"
    marker_ok = marker.is_file() or archive_manifest.is_file() or release_tar.is_file()
    ok = tag_hit or marker_ok
    result.add(
        "tag_or_archive_marker",
        ok,
        f"tag={tag_hit} marker={marker.is_file()} "
        f"archive_manifest={archive_manifest.is_file()} tar={release_tar.is_file()}",
    )


def _check_freeze(
    root: Path,
    result: MonitorResult,
    *,
    out_dir: Path,
    tip: str | None,
    ver: str | None,
    prebuilt_manifest: Path | None,
    expect_freeze_channel: str | None = None,
    expect_schema: str | None = None,
) -> None:
    want_freeze = expect_freeze_channel or FREEZE_CHANNEL
    want_schema = expect_schema or SCHEMA_ID

    # N2 / alternate freeze: prefer JSON channel check when expect differs
    if want_freeze != FREEZE_CHANNEL:
        man_path = None
        if prebuilt_manifest and Path(prebuilt_manifest).is_file():
            man_path = Path(prebuilt_manifest)
        else:
            release_mans = list(
                (root / "dist" / "releases" / (ver or RELEASE_VERSION)).glob(
                    "*.manifest.json"
                )
            )
            if release_mans:
                man_path = release_mans[0]
        if man_path is not None:
            try:
                from .bundle_n2 import load_n2_manifest

                m = load_n2_manifest(man_path)
                result.version = result.version or getattr(m, "ver", None)
                ch = m.freeze.channel if m.freeze else None
                sch = (
                    m.freeze.schema_name
                    if m.freeze and hasattr(m.freeze, "schema_name")
                    else getattr(m, "schema_name", None)
                )
                result.freeze_channel = ch
                ok = ch == want_freeze and (want_schema is None or sch == want_schema)
                result.add(
                    "freeze_intact",
                    ok,
                    f"n2 channel={ch!r} schema={sch!r} expect={want_freeze}/{want_schema}",
                )
                return
            except Exception as exc:  # noqa: BLE001 — fall through to single-node path
                pass  # N2 load failed; fall through to single-node path

    if prebuilt_manifest and prebuilt_manifest.is_file():
        m = load_manifest(prebuilt_manifest)
    else:
        # Prefer existing release manifest
        release_mans = list(
            (root / "dist" / "releases" / (ver or RELEASE_VERSION)).glob(
                "*.manifest.json"
            )
        )
        if release_mans:
            m = load_manifest(release_mans[0])
        else:
            m = build_bundle(
                root,
                out_dir / "monitor_probe",
                tip=tip or "mon01",
                ver=ver,
                freeze=True,
            )
    result.version = result.version or m.ver
    result.freeze_channel = m.freeze.channel if m.freeze else None
    ok = (
        m.freeze is not None
        and m.freeze.channel == want_freeze
        and m.freeze.schema_name == want_schema
        and m.schema_name == want_schema
    )
    result.add(
        "freeze_intact",
        ok,
        f"freeze={m.freeze.model_dump(by_alias=True) if m.freeze else None}",
    )


def _check_no_forbidden_drift(root: Path, result: MonitorResult) -> None:
    """Refuse drift into Raft / N>2 / multi-primary / ML / plaintext / GIA / SLO chase."""
    # Only flag *activation* of forbidden features, not detection/docs strings.
    forbidden_markers = [
        (r"ENABLE_RAFT\s*=\s*True", "Raft enabled"),
        (r"N_GT_2\s*=\s*True", "N>2 enabled"),
        (r"MULTI_PRIMARY\s*=\s*True", "multi-primary"),
        (r"SLO_CHASE\s*=\s*True", "SLO chase"),
        (r"ENABLE_TAG_SCHEMA_V2\s*=\s*True", "tag schema v2"),
        (r"EVERY_FSYNC_CHASE\s*=\s*True", "EVERY fsync chase"),
    ]
    scan_paths = [
        root / "src" / "neural_mesh",
        root / "docs" / "debt",
        root / ".project_state" / "CURRENT_STATE.md",
        root / ".project_state" / "NEXT_ACTION.md",
    ]
    # Skip packaging watch/monitor modules (they mention forbidden tokens as detectors)
    skip_names = {
        "post_rc_watch.py",
        "post_release_monitor.py",
        "release_signoff.py",
        "release_tag_archive.py",
        "final_release_audit.py",
        "release_checklist.py",
        "debt_gate_review.py",
        "theme_signoff_017.py",
    }
    hits: list[str] = []
    for path in scan_paths:
        files: list[Path]
        if path.is_dir():
            files = list(path.rglob("*.py")) + list(path.rglob("*.md"))
        elif path.is_file():
            files = [path]
        else:
            continue
        for f in files:
            if "__pycache__" in str(f):
                continue
            if f.name in skip_names:
                continue
            try:
                text = f.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError):
                continue
            for pat, label in forbidden_markers:
                if re.search(pat, text):
                    hits.append(f"{f.name}:{label}")
    # Also require NO_HELD still documented somewhere recent
    no_held_docs = [
        root / "docs" / "capabilities" / "MESH_PACKAGING_POST_RELEASE_MONITOR.md",
        root / "docs" / "capabilities" / "MESH_PACKAGING_RELEASE_SIGNOFF.md",
        root / "docs" / "capabilities" / "MESH_PACKAGING_FINAL_RELEASE_AUDIT.md",
        root / "docs" / "planning" / "0.17_NON_GOALS.md",
        root / "council" / "COUNCIL_AGREEMENT_CYCLE25.md",
        root / "council" / "COUNCIL_AGREEMENT_CYCLE24.md",
        root / "council" / "COUNCIL_AGREEMENT_CYCLE23.md",
    ]
    no_held_ok = False
    for d in no_held_docs:
        if d.is_file() and "NO_HELD" in d.read_text(encoding="utf-8"):
            no_held_ok = True
            break
    ok = not hits and no_held_ok
    result.add(
        "no_forbidden_drift",
        ok,
        f"hits={hits or 'none'} no_held_doc={no_held_ok}",
    )


def append_monitor_history(
    history_path: Path,
    record: dict[str, Any],
    *,
    roll_max: int = HISTORY_ROLL_MAX,
) -> Path:
    """Append one JSONL record; roll file if it exceeds roll_max lines."""
    history_path.parent.mkdir(parents=True, exist_ok=True)
    line = json.dumps(record, sort_keys=True) + "\n"
    if history_path.is_file():
        existing = history_path.read_text(encoding="utf-8").splitlines(keepends=True)
        if len(existing) >= roll_max:
            # Keep the last (roll_max - 1) and append the new line.
            kept = existing[-(roll_max - 1) :]
            history_path.write_text("".join(kept) + line, encoding="utf-8")
        else:
            with history_path.open("a", encoding="utf-8") as fh:
                fh.write(line)
    else:
        history_path.write_text(line, encoding="utf-8")
    return history_path


def run_post_release_monitor(
    root: Path | str,
    *,
    once: bool = True,
    continue_mode: bool = False,
    version: str = RELEASE_VERSION,
    out_dir: Path | str | None = None,
    report_path: Path | str | None = None,
    history_path: Path | str | None = None,
    tip: str | None = None,
    prebuilt_manifest: Path | str | None = None,
    force_fail: str | None = None,
    expect_freeze_channel: str | None = None,
    expect_schema: str | None = None,
) -> MonitorResult:
    """Run post-release --once checks. With continue_mode, also append history JSONL."""
    root = Path(root).resolve()
    mode = "continue" if continue_mode else ("once" if once else "once")
    result = MonitorResult(mode=mode)
    result.notes.append(
        "Scheduled routine stub: document-only; do NOT create Grok Bot routines."
    )
    if continue_mode:
        result.notes.append(
            "Continue mode: re-run once checks and append monitor_history.jsonl."
        )
    release_dir = root / "dist" / "releases" / version
    out = Path(out_dir) if out_dir else release_dir
    out.mkdir(parents=True, exist_ok=True)

    # Adapt debt/obs/tag checks via a thin WatchResult-compatible shim
    class _Shim:
        def __init__(self) -> None:
            self.checks: list[Any] = []
            self.ok = True
            self.errors: list[str] = []
            self.notes: list[str] = []

        def add(self, name: str, ok: bool, detail: str = "") -> None:
            self.checks.append(type("C", (), {"name": name, "ok": ok, "detail": detail})())
            if not ok:
                self.ok = False
                self.errors.append(f"{name}: {detail or 'FAIL'}")

    if force_fail == "signoff_present":
        result.add("signoff_present", False, "forced fail")
    else:
        _check_signoff(root, result, version, release_dir)

    if force_fail == "tag_or_archive_marker":
        result.add("tag_or_archive_marker", False, "forced fail")
    else:
        _check_tag_or_marker(root, result, version, release_dir)

    if force_fail == "freeze_intact":
        result.add("freeze_intact", False, "forced fail")
    else:
        _check_freeze(
            root,
            result,
            out_dir=out,
            tip=tip,
            ver=version,
            prebuilt_manifest=Path(prebuilt_manifest) if prebuilt_manifest else None,
            expect_freeze_channel=expect_freeze_channel,
            expect_schema=expect_schema,
        )

    if force_fail == "debt_schema_gated":
        result.add("debt_schema_gated", False, "forced fail")
    else:
        shim = _Shim()
        _check_debt_schema_gated(root, shim)  # type: ignore[arg-type]
        # Map name
        for c in shim.checks:
            result.add(
                "debt_schema_gated",
                c.ok,
                c.detail,
            )

    if force_fail == "obs_stable_fields":
        result.add("obs_stable_fields", False, "forced fail")
    else:
        shim = _Shim()
        _check_obs_fields_stable(root, shim)  # type: ignore[arg-type]
        for c in shim.checks:
            # rename
            result.add("obs_stable_fields", c.ok, c.detail)
        # ensure OBS_STABLE_FIELDS referenced
        result.notes.append(f"obs_fields={len(OBS_STABLE_FIELDS)}")

    if force_fail == "no_forbidden_drift":
        result.add("no_forbidden_drift", False, "forced fail")
    else:
        # Also run tag drift as part of forbidden
        shim = _Shim()
        _check_no_tag_schema_drift(root, shim)  # type: ignore[arg-type]
        tag_ok = all(c.ok for c in shim.checks) if shim.checks else False
        _check_no_forbidden_drift(root, result)
        # Fold tag drift into last check if it failed
        if not tag_ok:
            # Amend no_forbidden_drift if it passed but tag drifted
            for c in result.checks:
                if c.name == "no_forbidden_drift" and c.ok:
                    c.ok = False
                    c.detail += f" tag_drift={shim.errors}"
                    result.ok = False
                    result.errors.append(f"no_forbidden_drift: tag drift")
                    break

    result.ok = all(c.ok for c in result.checks)
    if not result.ok:
        result.errors = [
            f"{c.name}: {c.detail or 'FAIL'}" for c in result.checks if not c.ok
        ]

    rp = Path(report_path) if report_path else (release_dir / "MONITOR.json")
    rp.parent.mkdir(parents=True, exist_ok=True)
    rp.write_text(result.to_json(), encoding="utf-8")
    result.report_path = str(rp)

    if continue_mode:
        hp = (
            Path(history_path)
            if history_path
            else (release_dir / HISTORY_BASENAME)
        )
        append_monitor_history(hp, result.history_record())
        result.history_path = str(hp)
        result.history_appended = True
        # Refresh MONITOR.json with history fields
        rp.write_text(result.to_json(), encoding="utf-8")

    return result
