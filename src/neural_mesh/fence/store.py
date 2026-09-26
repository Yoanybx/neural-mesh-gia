"""Filesystem fence store: pair roles, fence epoch, durable token, abort flag.

Layout under ``<data_root>/fence/``:

  fence_state.json
  epoch.json
  roles/<node_id>.json
  witness.json   # PrimaryWitness-compatible sole writable primary
"""

from __future__ import annotations

import hashlib
import json
import os
import secrets
from pathlib import Path
from typing import Any

from neural_mesh.network.witness import PrimaryWitness

from .models import (
    SCHEMA_STORE,
    FenceEpoch,
    FenceN2Only,
    FencePlaintextForbidden,
    NodeRole,
)


def require_no_plaintext(mode: str | None) -> None:
    """Refuse plaintext / cleartext as a fence transport claim."""
    if mode is None:
        return
    m = str(mode).strip().lower()
    if m in ("plaintext", "plain", "tcp", "cleartext"):
        raise FencePlaintextForbidden(
            f"plaintext mode forbidden for fence ops: {mode!r}"
        )


def new_durable_token(*, epoch: int, primary: str) -> str:
    """Content-ish durable fence token (not a Raft term / consensus ballots)."""
    nonce = secrets.token_hex(8)
    raw = f"mesh.fence/v1|{epoch}|{primary}|{nonce}".encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


class FenceStore:
    """Persist N=2 pair roles + fence epoch under a data root."""

    MAX_NODES = 2

    def __init__(self, data_root: str | Path):
        self.data_root = Path(data_root)
        self.root = self.data_root / "fence"
        self.state_path = self.root / "fence_state.json"
        self.epoch_path = self.root / "epoch.json"
        self.roles_dir = self.root / "roles"
        self.witness_path = self.root / "witness.json"
        self.root.mkdir(parents=True, exist_ok=True)
        self.roles_dir.mkdir(parents=True, exist_ok=True)
        self.witness = PrimaryWitness(self.witness_path)

    def _atomic_json(self, path: Path, data: dict[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(path.suffix + ".tmp")
        tmp.write_text(
            json.dumps(data, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        os.replace(tmp, path)

    # --- fence_state ---

    def _default_state(self) -> dict[str, Any]:
        return {
            "schema": SCHEMA_STORE,
            "pair": [],
            "abort_demote_reelect": False,
            "abort_reason": "",
            "dual_primary": 0,
            "vault_acme_required": 0,
            "plaintext_fallback": 0,
        }

    def _read_state(self) -> dict[str, Any]:
        if not self.state_path.is_file():
            return self._default_state()
        data = json.loads(self.state_path.read_text(encoding="utf-8"))
        data["dual_primary"] = 0
        data["vault_acme_required"] = 0
        data["plaintext_fallback"] = 0
        data["schema"] = SCHEMA_STORE
        if "pair" not in data or data["pair"] is None:
            data["pair"] = []
        return data

    def _write_state(self, data: dict[str, Any]) -> None:
        data = dict(data)
        data["schema"] = SCHEMA_STORE
        data["dual_primary"] = 0
        data["vault_acme_required"] = 0
        data["plaintext_fallback"] = 0
        pair = list(data.get("pair") or [])
        if len(pair) > self.MAX_NODES:
            raise FenceN2Only(
                f"N>2 refused: pair has {len(pair)} nodes (max {self.MAX_NODES})"
            )
        data["pair"] = pair
        self._atomic_json(self.state_path, data)

    def state(self) -> dict[str, Any]:
        return self._read_state()

    @property
    def abort_demote_reelect(self) -> bool:
        return bool(self._read_state().get("abort_demote_reelect"))

    @property
    def pair(self) -> list[str]:
        return list(self._read_state().get("pair") or [])

    def set_pair(self, node_ids: list[str]) -> list[str]:
        ids = [str(n) for n in node_ids]
        if len(ids) > self.MAX_NODES:
            raise FenceN2Only(
                f"N>2 refused: cannot register {len(ids)} nodes (max {self.MAX_NODES})"
            )
        if len(ids) != len(set(ids)):
            raise FenceN2Only("duplicate node_id in pair refused")
        st = self._read_state()
        st["pair"] = ids
        self._write_state(st)
        # ensure role files exist
        for nid in ids:
            if not (self.roles_dir / f"{nid}.json").is_file():
                self.save_role(NodeRole(node_id=nid, role="none"))
        return ids

    def enter_abort(self, reason: str) -> dict[str, Any]:
        st = self._read_state()
        st["abort_demote_reelect"] = True
        st["abort_reason"] = str(reason or "")
        self._write_state(st)
        return st

    def clear_abort(self) -> dict[str, Any]:
        st = self._read_state()
        st["abort_demote_reelect"] = False
        st["abort_reason"] = ""
        self._write_state(st)
        return st

    # --- epoch ---

    def load_epoch(self) -> FenceEpoch:
        if not self.epoch_path.is_file():
            return FenceEpoch(pair=self.pair)
        data = json.loads(self.epoch_path.read_text(encoding="utf-8"))
        fe = FenceEpoch.from_dict(data)
        if not fe.pair:
            fe.pair = self.pair
        return fe

    def save_epoch(self, fe: FenceEpoch) -> None:
        fe.dual_primary = 0
        fe.vault_acme_required = 0
        fe.plaintext_fallback = 0
        if not fe.pair:
            fe.pair = self.pair
        if len(fe.pair) > self.MAX_NODES:
            raise FenceN2Only("N>2 refused on epoch save")
        self._atomic_json(self.epoch_path, fe.to_dict())

    # --- roles ---

    def role_path(self, node_id: str) -> Path:
        return self.roles_dir / f"{node_id}.json"

    def load_role(self, node_id: str) -> NodeRole:
        path = self.role_path(node_id)
        if not path.is_file():
            return NodeRole(node_id=node_id, role="none")
        data = json.loads(path.read_text(encoding="utf-8"))
        nr = NodeRole.from_dict(data)
        nr.node_id = node_id
        return nr

    def save_role(self, role: NodeRole) -> None:
        role.dual_primary = 0
        role.vault_acme_required = 0
        role.plaintext_fallback = 0
        self._atomic_json(self.role_path(role.node_id), role.to_dict())

    def list_roles(self) -> dict[str, NodeRole]:
        out: dict[str, NodeRole] = {}
        for nid in self.pair:
            out[nid] = self.load_role(nid)
        # also pick up any role files not yet in pair (still N<=2 enforced on set_pair)
        for path in sorted(self.roles_dir.glob("*.json")):
            nid = path.stem
            if nid not in out:
                out[nid] = self.load_role(nid)
        return out

    def primary_claimants(self) -> list[str]:
        return [
            nid
            for nid, role in self.list_roles().items()
            if role.role == "primary"
        ]

    def sync_witness(self, primary: str | None, *, epoch: int) -> None:
        """Align PrimaryWitness file with sole elected primary (or clear)."""
        if primary is None:
            data = {"writable_primary": None, "epoch": int(epoch)}
            self._atomic_json(self.witness_path, data)
            return
        # release any other, then claim
        cur = self.witness.writable_primary()
        if cur and cur != primary:
            self.witness.release(cur)
        self.witness.claim(primary, epoch=epoch)


__all__ = [
    "FenceStore",
    "require_no_plaintext",
    "new_durable_token",
]
