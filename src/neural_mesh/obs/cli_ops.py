"""CLI helpers for ``mesh obs telemetry|validate|schema``."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from .contract import (
    emit_telemetry,
    format_telemetry_m2m,
    schema_descriptor,
    telemetry_to_json,
    validate_telemetry,
)
from .models import (
    ObsAbortBlockCp,
    ObsCadenceInvalid,
    ObsError,
    ObsN2Only,
    ObsPlaintextForbidden,
    ObsSchemaMismatch,
    TelemetryDocument,
)


def _print_err(payload: dict[str, Any]) -> None:
    print(json.dumps(payload, indent=2, sort_keys=True))


def cmd_obs_telemetry(
    *,
    repo: str | Path,
    node_id: str = "local",
    cadence: str = "10s",
    packaging: str = "0.18-H4-obs-telemetry",
    as_json: bool = True,
    m2m: bool = False,
    mode: str = "local",
    cycle: int | None = None,
) -> int:
    try:
        doc = emit_telemetry(
            repo,
            node_id=node_id,
            cadence=cadence,
            packaging=packaging,
            mode=mode,
            cycle=cycle,
        )
    except ObsPlaintextForbidden as exc:
        _print_err(
            {
                "ok": False,
                "error": str(exc),
                "error_code": exc.code,
                "abort_block_cp": True,
                "dual_primary": 0,
                "plaintext_fallback": 0,
            }
        )
        return 1
    except (ObsAbortBlockCp, ObsSchemaMismatch, ObsCadenceInvalid, ObsN2Only, ObsError) as exc:
        _print_err(
            {
                "ok": False,
                "error": str(exc),
                "error_code": getattr(exc, "code", "OBS_ERROR"),
                "abort_block_cp": True,
                "dual_primary": 0,
            }
        )
        return 2
    if m2m:
        print(format_telemetry_m2m(doc))
    elif as_json:
        print(telemetry_to_json(doc), end="")
    else:
        print(
            f"ok=True schema={doc.schema} cadence={doc.cadence} "
            f"dual_primary={doc.dual_primary} abort_block_cp={doc.abort_block_cp}"
        )
        print(f"node={doc.node_id} cycle={doc.cycle} ver={doc.ver} cp={doc.cp_tip}")
        print(f"window={doc.window.window_id}")
    return 0 if doc.invariants_ok and not doc.abort_block_cp else 2


def cmd_obs_validate(
    *,
    file: str | Path | None = None,
    use_stdin: bool = False,
    abort_on_breach: bool = True,
) -> int:
    try:
        if use_stdin or file in (None, "-", ""):
            raw_text = sys.stdin.read()
        else:
            raw_text = Path(file).read_text(encoding="utf-8")
        data = json.loads(raw_text)
    except (OSError, json.JSONDecodeError) as exc:
        _print_err(
            {
                "ok": False,
                "error": f"cannot read telemetry JSON: {exc}",
                "error_code": "OBS_SCHEMA_MISMATCH",
                "abort_block_cp": True,
                "dual_primary": 0,
            }
        )
        return 2

    try:
        doc = validate_telemetry(data, abort_on_breach=abort_on_breach)
    except ObsAbortBlockCp as exc:
        _print_err(
            {
                "ok": False,
                "error": str(exc),
                "error_code": exc.code,
                "abort_block_cp": True,
                "dual_primary": 0,
                "invariants_ok": False,
            }
        )
        return 2
    except ObsError as exc:
        _print_err(
            {
                "ok": False,
                "error": str(exc),
                "error_code": getattr(exc, "code", "OBS_ERROR"),
                "abort_block_cp": True,
                "dual_primary": 0,
            }
        )
        return 2

    payload = doc.to_dict()
    payload["ok"] = True
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


def cmd_obs_schema(*, as_json: bool = True) -> int:
    desc = schema_descriptor()
    if as_json:
        print(json.dumps(desc, indent=2, sort_keys=True))
    else:
        print(f"schema={desc['schema']}")
        print(f"cadence_tiers={','.join(desc['cadence_tiers'])}")
        print(f"signals={','.join(desc['signals'])}")
        print(f"adversary={','.join(desc['adversary'])}")
        print(f"abort={desc['abort']}")
        print(f"note={desc['deprecation_note']}")
    return 0
