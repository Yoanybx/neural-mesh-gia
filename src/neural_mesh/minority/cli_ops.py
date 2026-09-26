"""CLI helpers for ``mesh minority status|probe|halt``."""

from __future__ import annotations

import json
from pathlib import Path

from .models import (
    MinorityAbortHaltWrites,
    MinorityError,
    MinorityN2Only,
    MinorityPlaintextForbidden,
    MinorityWriteDetected,
    MinorityWritesHalted,
)
from .service import MinorityService


def _svc(data_root: str | Path) -> MinorityService:
    return MinorityService(data_root)


def cmd_minority_status(*, data_root: str | Path, as_json: bool = False) -> int:
    svc = _svc(data_root)
    st = svc.status()
    payload = st.to_dict()
    if as_json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(
            f"ok={st.ok} minority_writes={st.minority_writes} "
            f"detected={st.minority_write_detected} halted={st.writes_halted}"
        )
        print(f"data_root={st.data_root}")
        print(
            f"pair={','.join(st.pair) or '<none>'} "
            f"primary={st.writable_primary or '<none>'}"
        )
        print(
            f"abort_halt_writes={st.abort_halt_writes} "
            f"rejected_minority={st.rejected_minority_count} "
            f"dual_primary={st.dual_primary}"
        )
        if st.issues:
            print("issues=" + ",".join(st.issues))
        if st.abort_reason:
            print(f"abort_reason={st.abort_reason}")
    return 0 if st.ok else 1


def cmd_minority_probe(
    *,
    data_root: str | Path,
    auto_halt: bool = True,
    mode: str = "local",
    as_json: bool = False,
) -> int:
    svc = _svc(data_root)
    try:
        result = svc.probe(auto_halt=auto_halt, mode=mode)
    except MinorityPlaintextForbidden as exc:
        print(
            json.dumps(
                {
                    "ok": False,
                    "error": str(exc),
                    "error_code": exc.code,
                    "minority_writes": 0,
                    "dual_primary": 0,
                    "plaintext_fallback": 0,
                },
                indent=2,
                sort_keys=True,
            )
        )
        return 1
    except (MinorityAbortHaltWrites, MinorityN2Only, MinorityError) as exc:
        print(
            json.dumps(
                {
                    "ok": False,
                    "error": str(exc),
                    "error_code": getattr(exc, "code", "MINORITY_ERROR"),
                    "minority_writes": 0,
                    "dual_primary": 0,
                },
                indent=2,
                sort_keys=True,
            )
        )
        return 2
    print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
    if not result.ok:
        return 2 if result.abort_halt_writes else 1
    return 0


def cmd_minority_halt(
    *,
    data_root: str | Path,
    reason: str = "operator halt",
    mode: str = "local",
    as_json: bool = False,
) -> int:
    svc = _svc(data_root)
    try:
        result = svc.halt(reason=reason, mode=mode)
    except MinorityPlaintextForbidden as exc:
        print(
            json.dumps(
                {
                    "ok": False,
                    "error": str(exc),
                    "error_code": exc.code,
                    "minority_writes": 0,
                    "dual_primary": 0,
                    "plaintext_fallback": 0,
                },
                indent=2,
                sort_keys=True,
            )
        )
        return 1
    except (MinorityError, MinorityWritesHalted, MinorityWriteDetected) as exc:
        print(
            json.dumps(
                {
                    "ok": False,
                    "error": str(exc),
                    "error_code": getattr(exc, "code", "MINORITY_ERROR"),
                    "minority_writes": 0,
                    "dual_primary": 0,
                },
                indent=2,
                sort_keys=True,
            )
        )
        return 1
    print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
    return 0 if result.ok else 1


__all__ = [
    "cmd_minority_status",
    "cmd_minority_probe",
    "cmd_minority_halt",
]
