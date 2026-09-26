"""CLI helpers for ``mesh clock status|probe|join-check``."""

from __future__ import annotations

import json
from pathlib import Path

from .models import (
    ClockAbortRefuseJoin,
    ClockError,
    ClockN2Only,
    ClockPlaintextForbidden,
    ClockSkewDetected,
)
from .service import ClockService


def _svc(data_root: str | Path) -> ClockService:
    return ClockService(data_root)


def cmd_clock_status(*, data_root: str | Path, as_json: bool = False) -> int:
    svc = _svc(data_root)
    st = svc.status()
    payload = st.to_dict()
    if as_json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(
            f"ok={st.ok} skew_ms={st.skew_ms} threshold={st.skew_threshold_ms} "
            f"detected={st.skew_detected} join_refused={st.join_refused}"
        )
        print(f"data_root={st.data_root}")
        print(f"pair={','.join(st.pair) or '<none>'}")
        print(
            f"abort_refuse_join={st.abort_refuse_join} "
            f"wall_clock_as_authority={st.wall_clock_as_authority} "
            f"mono={st.local_mono} dual_primary={st.dual_primary}"
        )
        if st.issues:
            print("issues=" + ",".join(st.issues))
        if st.abort_reason:
            print(f"abort_reason={st.abort_reason}")
    return 0 if st.ok else 1


def cmd_clock_probe(
    *,
    data_root: str | Path,
    auto_refuse: bool = True,
    mode: str = "local",
    as_json: bool = False,
) -> int:
    svc = _svc(data_root)
    try:
        result = svc.probe(auto_refuse=auto_refuse, mode=mode)
    except ClockPlaintextForbidden as exc:
        print(
            json.dumps(
                {
                    "ok": False,
                    "error": str(exc),
                    "error_code": exc.code,
                    "wall_clock_as_authority": 0,
                    "dual_primary": 0,
                    "minority_writes": 0,
                    "plaintext_fallback": 0,
                },
                indent=2,
                sort_keys=True,
            )
        )
        return 1
    except (ClockAbortRefuseJoin, ClockN2Only, ClockError) as exc:
        print(
            json.dumps(
                {
                    "ok": False,
                    "error": str(exc),
                    "error_code": getattr(exc, "code", "CLOCK_ERROR"),
                    "wall_clock_as_authority": 0,
                    "dual_primary": 0,
                    "minority_writes": 0,
                },
                indent=2,
                sort_keys=True,
            )
        )
        return 2
    print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
    if not result.ok:
        return 2 if result.abort_refuse_join else 1
    return 0


def cmd_clock_join_check(
    *,
    data_root: str | Path,
    node_id: str,
    peer_wall_ms: int | None = None,
    local_wall_ms: int | None = None,
    mode: str = "local",
    auto_refuse: bool = True,
    as_json: bool = False,
) -> int:
    svc = _svc(data_root)
    try:
        result = svc.join_check(
            node_id,
            peer_wall_ms=peer_wall_ms,
            local_wall_ms=local_wall_ms,
            mode=mode,
            auto_refuse=auto_refuse,
        )
    except ClockPlaintextForbidden as exc:
        print(
            json.dumps(
                {
                    "ok": False,
                    "error": str(exc),
                    "error_code": exc.code,
                    "wall_clock_as_authority": 0,
                    "dual_primary": 0,
                    "minority_writes": 0,
                    "plaintext_fallback": 0,
                },
                indent=2,
                sort_keys=True,
            )
        )
        return 1
    except (ClockError, ClockSkewDetected, ClockN2Only) as exc:
        print(
            json.dumps(
                {
                    "ok": False,
                    "error": str(exc),
                    "error_code": getattr(exc, "code", "CLOCK_ERROR"),
                    "wall_clock_as_authority": 0,
                    "dual_primary": 0,
                    "minority_writes": 0,
                },
                indent=2,
                sort_keys=True,
            )
        )
        return 1
    print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
    return 0 if result.ok else 1


__all__ = [
    "cmd_clock_status",
    "cmd_clock_probe",
    "cmd_clock_join_check",
]
