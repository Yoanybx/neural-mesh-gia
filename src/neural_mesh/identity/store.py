"""Filesystem identity store (JSON under fabric/identity root)."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from .models import SCHEMA_STORE, IdentityError, NodeIdentityRecord


class IdentityStore:
    """Persist NodeIdentityRecord objects under ``<root>/identities/<node_id>.json``.

    Also tracks global abort mode: pinned-only (ABORT path for H1).
    """

    def __init__(self, root: str | Path):
        self.root = Path(root)
        self.identities_dir = self.root / "identities"
        self.state_path = self.root / "identity_state.json"
        self.identities_dir.mkdir(parents=True, exist_ok=True)

    def _node_path(self, node_id: str) -> Path:
        safe = node_id.replace("/", "_").replace("..", "_")
        return self.identities_dir / f"{safe}.json"

    def load(self, node_id: str) -> NodeIdentityRecord | None:
        path = self._node_path(node_id)
        if not path.is_file():
            return None
        data = json.loads(path.read_text(encoding="utf-8"))
        return NodeIdentityRecord.from_dict(data)

    def save(self, record: NodeIdentityRecord) -> Path:
        path = self._node_path(record.node_id)
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = record.to_dict()
        tmp = path.with_suffix(".tmp")
        tmp.write_text(
            json.dumps(payload, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        os.replace(tmp, path)
        return path

    def list_ids(self) -> list[str]:
        out: list[str] = []
        if not self.identities_dir.is_dir():
            return out
        for p in sorted(self.identities_dir.glob("*.json")):
            out.append(p.stem)
        return out

    def all_records(self) -> list[NodeIdentityRecord]:
        recs: list[NodeIdentityRecord] = []
        for nid in self.list_ids():
            r = self.load(nid)
            if r is not None:
                recs.append(r)
        return recs

    def _read_state(self) -> dict[str, Any]:
        if not self.state_path.is_file():
            return {
                "schema": SCHEMA_STORE,
                "pinned_only": False,
                "pinned_only_reason": "",
                "dual_primary": 0,
                "vault_acme_required": 0,
                "plaintext_fallback": 0,
            }
        data = json.loads(self.state_path.read_text(encoding="utf-8"))
        data["dual_primary"] = 0
        data["vault_acme_required"] = 0
        data["plaintext_fallback"] = 0
        data["schema"] = SCHEMA_STORE
        return data

    def _write_state(self, data: dict[str, Any]) -> None:
        data = dict(data)
        data["schema"] = SCHEMA_STORE
        data["dual_primary"] = 0
        data["vault_acme_required"] = 0
        data["plaintext_fallback"] = 0
        tmp = self.state_path.with_suffix(".tmp")
        tmp.write_text(
            json.dumps(data, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        os.replace(tmp, self.state_path)

    @property
    def pinned_only(self) -> bool:
        return bool(self._read_state().get("pinned_only"))

    def enter_pinned_only(self, reason: str) -> dict[str, Any]:
        state = self._read_state()
        state["pinned_only"] = True
        state["pinned_only_reason"] = reason
        self._write_state(state)
        return state

    def clear_pinned_only(self) -> dict[str, Any]:
        state = self._read_state()
        state["pinned_only"] = False
        state["pinned_only_reason"] = ""
        self._write_state(state)
        return state

    def state(self) -> dict[str, Any]:
        return self._read_state()


def require_no_plaintext(mode: str | None) -> None:
    """Refuse plaintext / unix as an identity trust claim."""
    if mode is None:
        return
    m = str(mode).strip().lower()
    if m in ("plaintext", "plain", "tcp", "cleartext"):
        from .models import IdentityPlaintextForbidden

        raise IdentityPlaintextForbidden(
            f"plaintext mode forbidden for identity ops: {mode!r}"
        )


__all__ = ["IdentityStore", "require_no_plaintext", "IdentityError"]
