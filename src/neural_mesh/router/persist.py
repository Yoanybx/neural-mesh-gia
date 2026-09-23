"""Persist RouteDecision in C-RAM with op_id idempotency (DeepSeek C8/C9)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from neural_mesh.cram.errors import CRAMError
from neural_mesh.cram.store import CRAMStore

from .errors import CramPersistError
from .models import RouteDecision


class DecisionStore:
    """CAS-backed decision audit store with persist-ack semantics (C9).

    Layout under ``root``::

        .cram/...                 # envelopes (decision + optional replay)
        decision_index.json       # op_id → content_hash
        trace_index.json          # trace_id → [content_hash, ...]
    """

    def __init__(self, root: str | Path, *, available: bool = True):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.store = CRAMStore(self.root)
        self._index_path = self.root / "decision_index.json"
        self._trace_path = self.root / "trace_index.json"
        self._index: dict[str, str] = {}
        self._trace_index: dict[str, list[str]] = {}
        self._available = bool(available)
        self._load_index()
        self._load_trace_index()

    def mark_unavailable(self) -> None:
        """Simulate C-RAM down (fail-closed path for benches/tests)."""
        self._available = False

    def mark_available(self) -> None:
        self._available = True

    @property
    def available(self) -> bool:
        return self._available

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

    def _load_trace_index(self) -> None:
        if not self._trace_path.exists():
            return
        raw = json.loads(self._trace_path.read_text(encoding="utf-8"))
        self._trace_index = {
            str(k): [str(x) for x in (v or [])] for k, v in raw.items()
        }

    def _save_trace_index(self) -> None:
        self._trace_path.write_text(
            json.dumps(self._trace_index, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

    def _read_envelope(self, content_key: str) -> dict[str, Any]:
        raw = self.store.get(content_key)
        data = json.loads(raw.decode("utf-8"))
        # Back-compat: bare decision dict vs envelope
        if "decision" in data:
            return data
        return {"decision": data, "replay": {}}

    def get_by_op_id(self, op_id: str) -> RouteDecision | None:
        key = self._index.get(op_id)
        if not key:
            return None
        try:
            env = self._read_envelope(key)
        except CRAMError as exc:
            raise CramPersistError(
                "C-RAM get failed", op_id=op_id, cause=str(exc)
            ) from exc
        return RouteDecision.from_dict(env["decision"])

    def get_envelope_by_op_id(self, op_id: str) -> dict[str, Any] | None:
        key = self._index.get(op_id)
        if not key:
            return None
        return self._read_envelope(key)

    def get_by_trace_id(self, trace_id: str) -> RouteDecision | None:
        keys = self._trace_index.get(trace_id) or []
        if not keys:
            # Fallback scan for stores written before trace_index existed
            for op_id, key in self._index.items():
                env = self._read_envelope(key)
                d = env.get("decision") or {}
                if str(d.get("trace_id", "")) == trace_id:
                    return RouteDecision.from_dict(d)
            return None
        env = self._read_envelope(keys[-1])
        return RouteDecision.from_dict(env["decision"])

    def get_envelope_by_trace_id(self, trace_id: str) -> dict[str, Any] | None:
        keys = self._trace_index.get(trace_id) or []
        if keys:
            return self._read_envelope(keys[-1])
        for _op_id, key in self._index.items():
            env = self._read_envelope(key)
            d = env.get("decision") or {}
            if str(d.get("trace_id", "")) == trace_id:
                return env
        return None

    def put(
        self,
        decision: RouteDecision,
        *,
        replay: dict[str, Any] | None = None,
    ) -> str:
        """Persist decision envelope; returns content_key as persist ACK.

        Idempotent on op_id (first write wins). Raises CramPersistError when
        the store is unavailable or the underlying CAS write fails — callers
        must not emit RouteDecision without this ACK (Cycle 9 P1).
        """
        if not self._available:
            raise CramPersistError(
                "C-RAM unavailable",
                op_id=decision.op_id,
                trace_id=decision.trace_id,
                cause="store_marked_unavailable",
            )
        op_id = decision.op_id
        if not op_id:
            raise CramPersistError(
                "decision.op_id required for C-RAM persistence",
                trace_id=decision.trace_id,
            )
        existing = self._index.get(op_id)
        if existing is not None:
            return existing
        envelope = {
            "decision": decision.to_dict(),
            "replay": dict(replay) if replay else {},
        }
        payload = json.dumps(
            envelope, sort_keys=True, separators=(",", ":")
        ).encode("utf-8")
        try:
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
            tid = decision.trace_id or op_id
            bucket = self._trace_index.setdefault(tid, [])
            if content_key not in bucket:
                bucket.append(content_key)
                self._save_trace_index()
            return content_key
        except CramPersistError:
            raise
        except Exception as exc:  # noqa: BLE001 — map any CAS failure to typed error
            raise CramPersistError(
                "C-RAM persist failed",
                op_id=op_id,
                trace_id=decision.trace_id,
                cause=str(exc),
            ) from exc

    def count(self) -> int:
        return len(self._index)

    def op_ids(self) -> list[str]:
        return sorted(self._index.keys())

    def has_op_id(self, op_id: str) -> bool:
        return op_id in self._index


__all__ = ["DecisionStore"]
