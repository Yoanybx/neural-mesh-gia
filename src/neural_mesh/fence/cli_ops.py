"""CLI helpers for ``mesh fence status|probe|demote|reelect``."""

from __future__ import annotations

import json
from pathlib import Path

from .models import (
    FenceAbortDemoteReelect,
    FenceDualPrimary,
    FenceError,
    FenceN2Only,
    FenceNodeUnknown,
    FencePlaintextForbidden,
    FenceUnresolved,
)
from .service import FenceService


def _svc(data_root: str | Path) -> FenceService:
    return FenceService(data_root)


def cmd_fence_status(*, data_root: str | Path, as_json: bool = False) -> int:
    svc = _svc(data_root)
    st = svc.status()
    payload = st.to_dict()
    if as_json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(
            f"ok={st.ok} dual_primary={st.dual_primary} "
            f"detected={st.dual_primary_detected} epoch={st.fence_epoch}"
        )
        print(f"data_root={st.data_root}")
        print(f"pair={','.join(st.pair) or '<none>'} primary={st.writable_primary or '<none>'}")
        print(f"roles={st.roles}")
        print(
            f"abort_demote_reelect={st.abort_demote_reelect} "
            f"vault_acme_required={st.vault_acme_required}"
        )
        if st.issues:
            print("issues=" + ",".join(st.issues))
        if st.abort_reason:
            print(f"abort_reason={st.abort_reason}")
    return 0 if st.ok else 1


def cmd_fence_probe(
    *,
    data_root: str | Path,
    auto_fence: bool = True,
    preferred: str | None = None,
    mode: str = "local",
    as_json: bool = False,
) -> int:
    svc = _svc(data_root)
    try:
        result = svc.probe(auto_fence=auto_fence, preferred=preferred, mode=mode)
    except FencePlaintextForbidden as exc:
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
    except (FenceAbortDemoteReelect, FenceN2Only, FenceError) as exc:
        print(
            json.dumps(
                {
                    "ok": False,
                    "error": str(exc),
                    "error_code": getattr(exc, "code", "FENCE_ERROR"),
                    "dual_primary": 0,
                },
                indent=2,
                sort_keys=True,
            )
        )
        return 2
    print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
    if not result.ok:
        return 2 if result.abort_demote_reelect else 1
    return 0


def cmd_fence_demote(
    *,
    data_root: str | Path,
    node_id: str,
    mode: str = "local",
    as_json: bool = False,
) -> int:
    svc = _svc(data_root)
    try:
        result = svc.demote(node_id, mode=mode)
    except FencePlaintextForbidden as exc:
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
    except (FenceNodeUnknown, FenceError) as exc:
        print(
            json.dumps(
                {
                    "ok": False,
                    "error": str(exc),
                    "error_code": getattr(exc, "code", "FENCE_ERROR"),
                    "dual_primary": 0,
                },
                indent=2,
                sort_keys=True,
            )
        )
        return 1
    print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
    return 0 if result.ok else 1


def cmd_fence_reelect(
    *,
    data_root: str | Path,
    preferred: str | None = None,
    mode: str = "local",
    as_json: bool = False,
) -> int:
    svc = _svc(data_root)
    try:
        result = svc.reelect(preferred=preferred, mode=mode)
    except FencePlaintextForbidden as exc:
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
    except (FenceN2Only, FenceNodeUnknown, FenceDualPrimary, FenceUnresolved, FenceError) as exc:
        print(
            json.dumps(
                {
                    "ok": False,
                    "error": str(exc),
                    "error_code": getattr(exc, "code", "FENCE_ERROR"),
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
    "cmd_fence_status",
    "cmd_fence_probe",
    "cmd_fence_demote",
    "cmd_fence_reelect",
]
