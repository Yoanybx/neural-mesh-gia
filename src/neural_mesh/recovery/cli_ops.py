"""CLI helpers for ``mesh recover status|snapshot|restore|rebuild``."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .models import (
    RecoveryAbortRestore,
    RecoveryError,
    RecoveryMissingSnapshot,
    RecoveryPlaintextForbidden,
)
from .service import RecoveryService


def _svc(data_root: str | Path) -> RecoveryService:
    return RecoveryService(data_root)


def cmd_recover_status(*, data_root: str | Path, as_json: bool = False) -> int:
    svc = _svc(data_root)
    st = svc.status()
    payload = st.to_dict()
    if as_json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(f"ok={st.ok} abort_restore={st.abort_restore} snaps={st.snapshot_count}")
        print(f"data_root={st.data_root}")
        print(f"last_good={st.last_good_snapshot or '<none>'} wal={st.wal_entries}")
        print(f"seq={st.durable.get('seq')} epoch={st.durable.get('epoch')}")
        print(f"dual_primary={st.dual_primary} vault_acme_required={st.vault_acme_required}")
        if st.issues:
            print("issues=" + ",".join(st.issues))
        if st.abort_reason:
            print(f"abort_reason={st.abort_reason}")
    return 0 if st.ok else 1


def cmd_recover_snapshot(
    *,
    data_root: str | Path,
    reason: str = "manual",
    list_only: bool = False,
    verify: str | None = None,
    as_json: bool = False,
) -> int:
    svc = _svc(data_root)
    try:
        if list_only:
            metas = [m.to_dict() for m in svc.list_snapshots()]
            print(json.dumps({"snapshots": metas, "dual_primary": 0}, indent=2, sort_keys=True))
            return 0
        if verify:
            ok = svc.verify_snapshot(verify)
            print(
                json.dumps(
                    {"ok": ok, "snapshot_id": verify, "dual_primary": 0},
                    indent=2,
                    sort_keys=True,
                )
            )
            return 0 if ok else 1
        meta = svc.create_snapshot(reason=reason)
    except RecoveryError as exc:
        print(
            json.dumps(
                {
                    "ok": False,
                    "error": str(exc),
                    "error_code": getattr(exc, "code", "RECOVERY_ERROR"),
                    "dual_primary": 0,
                    "vault_acme_required": 0,
                    "plaintext_fallback": 0,
                },
                indent=2,
                sort_keys=True,
            )
        )
        return 1
    payload = meta.to_dict()
    payload["ok"] = True
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


def cmd_recover_restore(
    *,
    data_root: str | Path,
    snapshot_id: str | None = None,
    mode: str = "local",
    as_json: bool = False,
) -> int:
    svc = _svc(data_root)
    try:
        result = svc.restore(snapshot_id, mode=mode)
    except RecoveryPlaintextForbidden as exc:
        print(
            json.dumps(
                {
                    "ok": False,
                    "error": str(exc),
                    "error_code": exc.code,
                    "dual_primary": 0,
                    "plaintext_fallback": 0,
                },
                indent=2,
                sort_keys=True,
            )
        )
        return 1
    except RecoveryMissingSnapshot as exc:
        print(
            json.dumps(
                {
                    "ok": False,
                    "error": str(exc),
                    "error_code": exc.code,
                    "abort_restore": svc.store.abort_restore,
                    "dual_primary": 0,
                },
                indent=2,
                sort_keys=True,
            )
        )
        return 2
    except RecoveryError as exc:
        print(
            json.dumps(
                {
                    "ok": False,
                    "error": str(exc),
                    "error_code": getattr(exc, "code", "RECOVERY_ERROR"),
                    "dual_primary": 0,
                },
                indent=2,
                sort_keys=True,
            )
        )
        return 1
    print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
    if not result.ok:
        return 2 if result.abort_restore else 1
    return 0


def cmd_recover_rebuild(
    *,
    data_root: str | Path,
    snapshot_id: str | None = None,
    mode: str = "local",
    as_json: bool = False,
) -> int:
    svc = _svc(data_root)
    try:
        result = svc.rebuild(snapshot_id=snapshot_id, mode=mode)
    except RecoveryPlaintextForbidden as exc:
        print(
            json.dumps(
                {
                    "ok": False,
                    "error": str(exc),
                    "error_code": exc.code,
                    "dual_primary": 0,
                    "plaintext_fallback": 0,
                },
                indent=2,
                sort_keys=True,
            )
        )
        return 1
    except (RecoveryAbortRestore, RecoveryMissingSnapshot) as exc:
        print(
            json.dumps(
                {
                    "ok": False,
                    "error": str(exc),
                    "error_code": getattr(exc, "code", "RECOVERY_ABORT_RESTORE"),
                    "abort_restore": True,
                    "dual_primary": 0,
                },
                indent=2,
                sort_keys=True,
            )
        )
        return 2
    except RecoveryError as exc:
        print(
            json.dumps(
                {
                    "ok": False,
                    "error": str(exc),
                    "error_code": getattr(exc, "code", "RECOVERY_ERROR"),
                    "dual_primary": 0,
                },
                indent=2,
                sort_keys=True,
            )
        )
        return 1
    print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
    if result.abort_restore and result.ok:
        return 0  # restored via abort path; operator should acknowledge
    return 0 if result.ok else 1


__all__ = [
    "cmd_recover_status",
    "cmd_recover_snapshot",
    "cmd_recover_restore",
    "cmd_recover_rebuild",
]
