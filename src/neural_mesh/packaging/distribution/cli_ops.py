"""CLI helpers for ``mesh dist distribute|verify|pin-prior|schema``."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from .models import (
    DistAbortPinPrior,
    DistError,
    DistFrozenChannel,
    DistN2Only,
    DistPlaintextForbidden,
    DistReplayDetected,
    DistSignatureInvalid,
    DistToolchainMismatch,
    schema_descriptor,
)
from .service import (
    distribute,
    document_to_json,
    format_dist_m2m,
    load_prior_pin,
    pin_prior,
    verify_distribution,
)


def _print_err(payload: dict[str, Any]) -> None:
    print(json.dumps(payload, indent=2, sort_keys=True))


def cmd_dist_distribute(
    *,
    repo: str | Path,
    out_dir: str | Path | None = None,
    name: str = "neural-mesh-gia-dist",
    channel: str = "0.18.x",
    cycle: int = 38,
    mode: str = "local",
    as_json: bool = True,
    m2m: bool = False,
) -> int:
    try:
        doc = distribute(
            repo,
            out_dir=out_dir,
            name=name,
            channel=channel,
            cycle=cycle,
            mode=mode,
        )
    except DistPlaintextForbidden as exc:
        _print_err(
            {
                "ok": False,
                "error": str(exc),
                "error_code": exc.code,
                "abort_pin_prior": True,
                "dual_primary": 0,
                "plaintext_fallback": 0,
            }
        )
        return 1
    except (
        DistAbortPinPrior,
        DistFrozenChannel,
        DistN2Only,
        DistReplayDetected,
        DistError,
    ) as exc:
        _print_err(
            {
                "ok": False,
                "error": str(exc),
                "error_code": getattr(exc, "code", "DIST_ERROR"),
                "abort_pin_prior": True,
                "dual_primary": 0,
            }
        )
        return 2
    if m2m:
        print(format_dist_m2m(doc))
    elif as_json:
        print(document_to_json(doc), end="")
    else:
        print(
            f"ok=True schema={doc.schema} channel={doc.channel} "
            f"bundle_id={doc.bundle_id} abort_pin_prior={doc.abort_pin_prior}"
        )
        print(f"ver={doc.ver} cp={doc.cp_tip} sha={doc.bundle_sha256[:16]}")
    return 0 if doc.invariants_ok and not doc.abort_pin_prior else 2


def cmd_dist_verify(
    *,
    file: str | Path | None = None,
    use_stdin: bool = False,
    repo: str | Path | None = None,
    abort_on_breach: bool = True,
    mark_replay_seen: bool = False,
) -> int:
    try:
        if use_stdin or file in (None, "-", ""):
            raw_text = sys.stdin.read()
            data = json.loads(raw_text)
            doc = verify_distribution(
                data,
                repo=repo,
                abort_on_breach=abort_on_breach,
                mark_replay_seen=mark_replay_seen,
            )
        else:
            doc = verify_distribution(
                file,
                repo=repo,
                abort_on_breach=abort_on_breach,
                mark_replay_seen=mark_replay_seen,
            )
    except (OSError, json.JSONDecodeError) as exc:
        _print_err(
            {
                "ok": False,
                "error": f"cannot read distribution JSON: {exc}",
                "error_code": "DIST_SCHEMA_MISMATCH",
                "abort_pin_prior": True,
                "dual_primary": 0,
            }
        )
        return 2
    except DistAbortPinPrior as exc:
        _print_err(
            {
                "ok": False,
                "error": str(exc),
                "error_code": exc.code,
                "abort_pin_prior": True,
                "dual_primary": 0,
                "invariants_ok": False,
            }
        )
        return 2
    except (
        DistSignatureInvalid,
        DistReplayDetected,
        DistToolchainMismatch,
        DistError,
    ) as exc:
        _print_err(
            {
                "ok": False,
                "error": str(exc),
                "error_code": getattr(exc, "code", "DIST_ERROR"),
                "abort_pin_prior": True,
                "dual_primary": 0,
            }
        )
        return 2

    payload = doc.to_dict()
    payload["ok"] = True
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


def cmd_dist_pin_prior(
    *,
    repo: str | Path,
    reason: str = "ABORT distribution breach",
    ver: str = "0.17.0",
    as_json: bool = True,
) -> int:
    try:
        pin = pin_prior(repo, reason=reason, ver=ver)
    except DistError as exc:
        _print_err(
            {
                "ok": False,
                "error": str(exc),
                "error_code": getattr(exc, "code", "DIST_ERROR"),
                "abort_pin_prior": True,
            }
        )
        return 2
    record = load_prior_pin(repo) or {
        "ok": True,
        "abort_pin_prior": True,
        "prior_pin": pin.to_dict(),
        "retag": False,
        "tags_untouched": ["v0.16.3", "v0.17.0"],
    }
    if as_json:
        print(json.dumps(record, indent=2, sort_keys=True))
    else:
        print(
            f"ok=True abort_pin_prior=True prior_ver={pin.ver} "
            f"retag=False tags_untouched=v0.16.3,v0.17.0"
        )
    return 0


def cmd_dist_schema(*, as_json: bool = True) -> int:
    desc = schema_descriptor()
    if as_json:
        print(json.dumps(desc, indent=2, sort_keys=True))
    else:
        print(f"schema={desc['schema']}")
        print(f"channel={desc['channel']}")
        print(f"ops={','.join(desc['ops'])}")
        print(f"tests={','.join(desc['tests'])}")
        print(f"abort={desc['abort']}")
        print(f"note={desc['deprecation_note']}")
    return 0
