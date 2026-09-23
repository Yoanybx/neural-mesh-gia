"""Idempotent replication log — op_id + epoch fencing."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .models import ReplicationOp


class ReplicationLog:
    """Append-only JSONL log; tracks seen op_ids and per-key epochs."""

    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._seen_ops: set[str] = set()
        self._epochs: dict[str, int] = {}  # content_hash -> current epoch
        if self.path.exists():
            self._replay()

    def _replay(self) -> None:
        for line in self.path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)
            op_id = rec.get("op_id")
            if op_id:
                self._seen_ops.add(op_id)
            key = rec.get("content_hash")
            epoch = int(rec.get("epoch", 0))
            result = rec.get("result")
            if key and result == "APPLIED":
                self._epochs[key] = max(self._epochs.get(key, 0), epoch)

    def current_epoch(self, content_hash: str) -> int:
        return int(self._epochs.get(content_hash, 0))

    def has_op(self, op_id: str) -> bool:
        return op_id in self._seen_ops

    def apply(
        self,
        *,
        op_id: str,
        op_type: str,
        content_hash: str,
        epoch: int,
        node_id: str,
        detail: dict[str, Any] | None = None,
        bump_epoch: bool = False,
    ) -> ReplicationOp:
        """Apply with idempotency + stale-epoch rejection.

        - Duplicate op_id → DUPLICATE (no epoch change)
        - epoch < current → REJECTED_STALE_EPOCH
        - else APPLIED; optionally bump stored epoch to ``epoch`` (or epoch+1 if bump)
        """
        if op_id in self._seen_ops:
            op = ReplicationOp(
                op_id=op_id,
                op_type=op_type,
                content_hash=content_hash,
                epoch=epoch,
                node_id=node_id,
                result="DUPLICATE",
                detail=dict(detail or {}),
            )
            self._append(op)
            return op

        current = self.current_epoch(content_hash)
        if epoch < current:
            op = ReplicationOp(
                op_id=op_id,
                op_type=op_type,
                content_hash=content_hash,
                epoch=epoch,
                node_id=node_id,
                result="REJECTED_STALE_EPOCH",
                detail={"current_epoch": current, **(detail or {})},
            )
            self._seen_ops.add(op_id)
            self._append(op)
            return op

        new_epoch = epoch + 1 if bump_epoch else max(current, epoch)
        self._epochs[content_hash] = new_epoch
        self._seen_ops.add(op_id)
        op = ReplicationOp(
            op_id=op_id,
            op_type=op_type,
            content_hash=content_hash,
            epoch=new_epoch if bump_epoch else epoch,
            node_id=node_id,
            result="APPLIED",
            detail=dict(detail or {}),
        )
        self._append(op)
        return op

    def _append(self, op: ReplicationOp) -> None:
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(op.to_dict(), sort_keys=True) + "\n")


__all__ = ["ReplicationLog"]
