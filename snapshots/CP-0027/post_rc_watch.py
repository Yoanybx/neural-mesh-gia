"""Post-RC watch harness (CP-0027 / P17).

Lightweight, non-daemon watch checklist for RC channel health:
- manifest freeze intact
- debt SCHEMA-GATED unchanged
- no tag schema drift
- snapshot OBS fields stable

``--once`` produces a watch report JSON under dist/ or .project_state.
Scheduled routine is documented only — do NOT create Grok Bot routines.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .bundle import build_bundle, load_manifest
from .manifest import FREEZE_CHANNEL, SCHEMA_ID
from .release_checklist import NO_HELD_DEFAULT

__all__ = [
    "OBS_STABLE_FIELDS",
    "WatchCheck",
    "WatchResult",
    "WATCH_CHECKLIST",
    "run_post_rc_watch",
]

OBS_STABLE_FIELDS = (
    "schema",
    "node_id",
    "cycle",
    "ver",
    "tip",
    "cp_range",
    "cp_tip",
    "pytest",
    "slo_state",
    "debt_gates",
    "peers",
    "local",
)

WATCH_CHECKLIST = (
    "manifest_freeze_intact",
    "debt_schema_gated_unchanged",
    "no_tag_schema_drift",
    "snapshot_obs_fields_stable",
)


@dataclass
class WatchCheck:
    name: str
    ok: bool
    detail: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {"name": self.name, "ok": self.ok, "detail": self.detail}


@dataclass
class WatchResult:
    ok: bool = True
    errors: list[str] = field(default_factory=list)
    checks: list[WatchCheck] = field(default_factory=list)
    checklist: tuple[str, ...] = WATCH_CHECKLIST
    version: str | None = None
    freeze_channel: str | None = None
    report_path: str | None = None
    mode: str = "once"
    no_held: str = NO_HELD_DEFAULT
    notes: list[str] = field(default_factory=list)

    def add(self, name: str, ok: bool, detail: str = "") -> None:
        self.checks.append(WatchCheck(name=name, ok=ok, detail=detail))
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
            "freeze_channel": self.freeze_channel,
            "report_path": self.report_path,
            "no_held": self.no_held,
            "notes": list(self.notes),
            "scheduled_routine": {
                "status": "documented_only",
                "create_grok_bot_routine": False,
                "hint": "Future: cron/CI may invoke scripts/post_rc_watch.py --once",
            },
        }

    def to_json(self, *, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, sort_keys=True) + "\n"


def _check_manifest_freeze(
    root: Path,
    result: WatchResult,
    *,
    out_dir: Path,
    tip: str | None,
    ver: str | None,
    prebuilt_manifest: Path | None,
) -> None:
    if prebuilt_manifest and prebuilt_manifest.is_file():
        m = load_manifest(prebuilt_manifest)
    else:
        built = build_bundle(
            root,
            out_dir / "watch_probe",
            tip=tip or "watch01",
            ver=ver,
            freeze=True,
        )
        m = built
    result.version = m.ver
    result.freeze_channel = m.freeze.channel if m.freeze else None
    ok = (
        m.freeze is not None
        and m.freeze.channel == FREEZE_CHANNEL
        and m.freeze.schema_name == SCHEMA_ID
        and m.schema_name == SCHEMA_ID
    )
    detail = (
        f"freeze={m.freeze.model_dump(by_alias=True) if m.freeze else None} "
        f"schema={m.schema_name}"
    )
    result.add("manifest_freeze_intact", ok, detail)


def _check_debt_schema_gated(root: Path, result: WatchResult) -> None:
    debt = root / "docs" / "debt" / "CHECKPOINT_EVERY_FLOOR.md"
    if not debt.is_file():
        result.add("debt_schema_gated_unchanged", False, "debt doc missing")
        return
    text = debt.read_text(encoding="utf-8")
    ok = "SCHEMA-GATED" in text and (
        "Status: SCHEMA-GATED" in text or "SCHEMA-GATED (CP-0022)" in text
    )
    # Ensure no chase language was flipped on
    chase_on = bool(re.search(r"SLO_CHASE\s*=\s*True", text)) or (
        "No SLO chase" not in text and "no chase" not in text.lower()
    )
    # Prefer explicit SCHEMA-GATED + no chase markers
    if "no chase" in text.lower() or "No SLO chase" in text or "SLO_CHASE=False" in text:
        chase_on = False
    result.add(
        "debt_schema_gated_unchanged",
        ok and not chase_on,
        f"SCHEMA-GATED present={ok} chase_on={chase_on}",
    )


def _check_no_tag_schema_drift(root: Path, result: WatchResult) -> None:
    """Tag schema must remain CHECKPOINT@floor:<n>; schema_gate present."""
    tags = root / "src" / "neural_mesh" / "tags.py"
    if not tags.is_file():
        result.add("no_tag_schema_drift", False, "tags.py missing")
        return
    text = tags.read_text(encoding="utf-8")
    has_gate = "schema_gate_checkpoint_every_floor" in text
    has_floor = "CHECKPOINT@floor" in text or "floor_checkpoint" in text.lower() or (
        "CHECKPOINT" in text and "floor" in text
    )
    # Drift signal: new required schema id for tags besides known pattern
    drifted = "mesh.tag.schema/v2" in text or "TAG_SCHEMA_V2" in text
    result.add(
        "no_tag_schema_drift",
        has_gate and has_floor and not drifted,
        f"gate={has_gate} floor={has_floor} drifted={drifted}",
    )


def _check_obs_fields_stable(root: Path, result: WatchResult) -> None:
    """Status snapshot schema fields must remain the OBS_STABLE_FIELDS set."""
    mod = root / "src" / "neural_mesh" / "status_snapshot.py"
    if not mod.is_file():
        result.add("snapshot_obs_fields_stable", False, "status_snapshot.py missing")
        return
    text = mod.read_text(encoding="utf-8")
    # Prefer live model if importable from this tree
    missing: list[str] = []
    try:
        import sys

        src = str((root / "src").resolve())
        if src not in sys.path:
            sys.path.insert(0, src)
        from neural_mesh.status_snapshot import StatusSnapshot, SCHEMA_ID as SNAP_SCHEMA

        fields = set(StatusSnapshot.model_fields.keys())
        # schema_name is aliased as schema
        aliased = set()
        for name, finfo in StatusSnapshot.model_fields.items():
            alias = getattr(finfo, "alias", None)
            aliased.add(alias or name)
        # Required OBS keys as documented
        for key in OBS_STABLE_FIELDS:
            if key == "schema":
                if "schema" not in aliased and "schema_name" not in fields:
                    missing.append(key)
            elif key not in fields and key not in aliased:
                missing.append(key)
        schema_ok = SNAP_SCHEMA == "mesh.status.snapshot/v1"
    except Exception as exc:  # noqa: BLE001
        # Fallback: textual presence
        for key in OBS_STABLE_FIELDS:
            if key == "schema":
                if 'SCHEMA_ID = "mesh.status.snapshot/v1"' not in text:
                    missing.append(key)
            elif f"{key}:" not in text and f"{key} =" not in text:
                missing.append(key)
        schema_ok = 'SCHEMA_ID = "mesh.status.snapshot/v1"' in text
        result.notes.append(f"obs import fallback: {exc}")

    result.add(
        "snapshot_obs_fields_stable",
        not missing and schema_ok,
        f"missing={missing or 'none'} schema_ok={schema_ok}",
    )


def run_post_rc_watch(
    root: Path | str,
    *,
    once: bool = True,
    out_dir: Path | str | None = None,
    report_path: Path | str | None = None,
    tip: str | None = None,
    ver: str | None = None,
    prebuilt_manifest: Path | str | None = None,
    force_fail: str | None = None,
) -> WatchResult:
    """Run watch checklist once (default). Not a long-lived daemon."""
    root = Path(root).resolve()
    result = WatchResult(mode="once" if once else "once")
    result.notes.append(
        "Scheduled routine stub: document-only; do NOT create Grok Bot routines."
    )
    out = Path(out_dir) if out_dir else (root / "dist" / "post_rc_watch")
    out.mkdir(parents=True, exist_ok=True)

    if force_fail == "manifest_freeze_intact":
        result.add("manifest_freeze_intact", False, "forced fail")
    else:
        _check_manifest_freeze(
            root,
            result,
            out_dir=out,
            tip=tip,
            ver=ver,
            prebuilt_manifest=Path(prebuilt_manifest) if prebuilt_manifest else None,
        )

    if force_fail == "debt_schema_gated_unchanged":
        result.add("debt_schema_gated_unchanged", False, "forced fail")
    else:
        _check_debt_schema_gated(root, result)

    if force_fail == "no_tag_schema_drift":
        result.add("no_tag_schema_drift", False, "forced fail")
    else:
        _check_no_tag_schema_drift(root, result)

    if force_fail == "snapshot_obs_fields_stable":
        result.add("snapshot_obs_fields_stable", False, "forced fail")
    else:
        _check_obs_fields_stable(root, result)

    result.ok = all(c.ok for c in result.checks)
    if not result.ok:
        result.errors = [f"{c.name}: {c.detail or 'FAIL'}" for c in result.checks if not c.ok]

    # Prefer dist/; also allow .project_state via report_path
    default_rp = out / "post_rc_watch_report.json"
    alt = root / ".project_state" / "post_rc_watch_report.json"
    rp = Path(report_path) if report_path else default_rp
    rp.parent.mkdir(parents=True, exist_ok=True)
    rp.write_text(result.to_json(), encoding="utf-8")
    result.report_path = str(rp)
    # Mirror into .project_state when writing under dist (convenience)
    if rp != alt and rp.parent.name != ".project_state":
        try:
            alt.write_text(result.to_json(), encoding="utf-8")
        except OSError:
            pass
    return result
