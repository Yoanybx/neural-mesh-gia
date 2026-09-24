"""CLI helpers for ``mesh id status|attest|tier|rotate|revoke``."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .models import IdentityError, IdentityPinnedOnlyAbort, parse_tier
from .service import IdentityService


def _svc(fabric_root: str | Path, node_id: str | None = None) -> IdentityService:
    return IdentityService(fabric_root, node_id=node_id)


def cmd_id_status(
    *,
    fabric_root: str | Path,
    node_id: str,
    as_json: bool = False,
) -> int:
    svc = _svc(fabric_root, node_id)
    st = svc.status(node_id)
    payload = st.to_dict()
    if as_json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(f"node_id={st.node_id} ok={st.ok} pinned_only={st.pinned_only}")
        print(f"fabric_root={st.fabric_root}")
        print(f"store={st.store_path}")
        print(f"dual_primary={st.dual_primary} vault_acme_required={st.vault_acme_required}")
        if st.record:
            print(
                f"tier=T{st.record.get('tier')} fp={str(st.record.get('cert_fingerprint', ''))[:16]}..."
            )
            print(f"revoked={st.record.get('revoked')} pinned={st.record.get('pinned')}")
        else:
            print("record=<none>")
        if st.issues:
            print("issues=" + ",".join(st.issues))
    return 0 if st.ok else 1


def cmd_id_attest(
    *,
    fabric_root: str | Path,
    node_id: str,
    expected: str | None = None,
    as_json: bool = False,
    mode: str = "tls",
) -> int:
    svc = _svc(fabric_root, node_id)
    try:
        result = svc.attest(node_id, expected_node_id=expected, mode=mode)
    except IdentityError as exc:
        payload: dict[str, Any] = {
            "ok": False,
            "node_id": node_id,
            "error": str(exc),
            "error_code": getattr(exc, "code", "IDENTITY_ERROR"),
            "pinned_only": svc.store.pinned_only,
            "dual_primary": 0,
            "vault_acme_required": 0,
            "plaintext_fallback": 0,
        }
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 2 if isinstance(exc, IdentityPinnedOnlyAbort) else 1
    payload = result.to_dict()
    if as_json or True:
        print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if result.ok else 1


def cmd_id_tier(
    *,
    fabric_root: str | Path,
    node_id: str,
    tier: str | None = None,
    pin: bool = False,
    downgrade: bool = False,
    reason: str = "",
    as_json: bool = False,
) -> int:
    svc = _svc(fabric_root, node_id)
    try:
        if downgrade:
            rec = svc.downgrade(node_id, reason=reason or "downgrade")
        elif tier is not None:
            rec = svc.set_tier(node_id, tier, reason=reason, pin=pin)
        else:
            t = svc.get_tier(node_id)
            rec_existing = svc.store.load(node_id)
            payload = {
                "node_id": node_id,
                "tier": int(t),
                "tier_name": f"T{int(t)}",
                "record": rec_existing.to_dict() if rec_existing else None,
                "dual_primary": 0,
                "vault_acme_required": 0,
            }
            print(json.dumps(payload, indent=2, sort_keys=True))
            return 0
    except IdentityError as exc:
        print(
            json.dumps(
                {
                    "ok": False,
                    "error": str(exc),
                    "error_code": getattr(exc, "code", "IDENTITY_ERROR"),
                    "dual_primary": 0,
                },
                indent=2,
                sort_keys=True,
            )
        )
        return 1
    payload = rec.to_dict()
    payload["ok"] = True
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


def cmd_id_rotate(
    *,
    fabric_root: str | Path,
    node_id: str,
    days: int = 825,
    keep_tier: bool = True,
    as_json: bool = False,
) -> int:
    svc = _svc(fabric_root, node_id)
    try:
        rec = svc.rotate(node_id, days=days, keep_tier=keep_tier)
    except IdentityError as exc:
        print(
            json.dumps(
                {
                    "ok": False,
                    "error": str(exc),
                    "error_code": getattr(exc, "code", "IDENTITY_ERROR"),
                    "dual_primary": 0,
                    "vault_acme_required": 0,
                },
                indent=2,
                sort_keys=True,
            )
        )
        return 1
    payload = rec.to_dict()
    payload["ok"] = True
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


def cmd_id_revoke(
    *,
    fabric_root: str | Path,
    node_id: str,
    reason: str = "revoked",
    as_json: bool = False,
) -> int:
    svc = _svc(fabric_root, node_id)
    try:
        rec = svc.revoke(node_id, reason=reason)
    except IdentityError as exc:
        print(
            json.dumps(
                {
                    "ok": False,
                    "error": str(exc),
                    "error_code": getattr(exc, "code", "IDENTITY_ERROR"),
                    "dual_primary": 0,
                },
                indent=2,
                sort_keys=True,
            )
        )
        return 1
    payload = rec.to_dict()
    payload["ok"] = True
    payload["pinned_only"] = svc.store.pinned_only
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


__all__ = [
    "cmd_id_status",
    "cmd_id_attest",
    "cmd_id_tier",
    "cmd_id_rotate",
    "cmd_id_revoke",
    "parse_tier",
]
