"""Persist RouteDecision in C-RAM with op_id idempotency (DeepSeek C8)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from neural_mesh.cram.store import CRAMStore

from .models import RouteDecision


class DecisionStore:
    """CAS-backed decision audit store.

    Layout under ``root``::

        .cram/...                 # decision payloads (canonical JSON bytes)
        decision_index.json       # op_id → content_hash
    """

    def __init__(self, root: str | Path):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.store = CRAMStore(self.root)
        self._index_path = self.root / "decision_index.json"
        self._index: dict[str, str] = {}
        self._load_index()

    def _load_index(self) -> None:
        if not self._index_path.exists():
            return
        raw = json.loads(self._index_path.read_text(encoding="utf-8"))
        self._index = {str(k): str(v) for k, v in raw.items()}

    def _save_index(self) -> None:
        self._index_path.write_text(
            json.dumps(self._index, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

    def get_by_op_id(self, op_id: str) -> RouteDecision | None:
        key = self._index.get(op_id)
        if not key:
            return None
        raw = self.store.get(key)
        data = json.loads(raw.decode("utf-8"))
        return RouteDecision.from_dict(data)

    def put(self, decision: RouteDecision) -> str:
        """Persist decision; idempotent on op_id (first write wins)."""
        op_id = decision.op_id
        if not op_id:
            raise ValueError("decision.op_id required for C-RAM persistence")
        existing = self.get_by_op_id(op_id)
        if existing is not None:
            return self._index[op_id]
        # Store full dict (incl. timestamp) for audit; idempotency is by op_id.
        payload = json.dumps(
            decision.to_dict(), sort_keys=True, separators=(",", ":")
        ).encode("utf-8")
        content_key = self.store.put(
            payload,
            metadata={
                "type": "ROUTE_DECISION",
                "op_id": op_id,
                "epoch": decision.epoch,
                "trace_id": decision.trace_id,
                "task_id": decision.task_id,
            },
        )
        self._index[op_id] = content_key
        self._save_index()
        return content_key

    def count(self) -> int:
        return len(self._index)

    def op_ids(self) -> list[str]:
        return sorted(self._index.keys())


__all__ = ["DecisionStore"]
