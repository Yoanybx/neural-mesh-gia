"""R1 NodeCapability model + CapabilityRegistry (C-RAM persisted) — Cycle 10."""

from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

from neural_mesh.cram.errors import CRAMError
from neural_mesh.cram.store import CRAMStore

from .errors import CramPersistError, StaleCapability, UnknownCapabilitySchema

CAPABILITY_SCHEMA_VERSION = 1
DEFAULT_CAP_TTL_MS = 5000
T_CONV_CAPABILITY_S = 5.0  # update propagation bound (P0)


def _now_ms() -> int:
    return int(time.time() * 1000)


@dataclass(frozen=True)
class NodeCapability:
    """Versioned capability advertisement for a mesh node (schema v1)."""

    node_id: str
    cpu: int = 0
    memory: int = 0
    accelerators: tuple[str, ...] = ()
    storage: int = 0
    network_class: str = "local"
    supported_tasks: tuple[str, ...] = ("compute",)
    health: float = 1.0
    advertised_at_ms: int = 0
    ttl_ms: int = DEFAULT_CAP_TTL_MS
    schema_version: int = CAPABILITY_SCHEMA_VERSION

    def to_dict(self) -> dict[str, Any]:
        return {
            "node_id": self.node_id,
            "cpu": int(self.cpu),
            "memory": int(self.memory),
            "accelerators": list(self.accelerators),
            "storage": int(self.storage),
            "network_class": self.network_class,
            "supported_tasks": list(self.supported_tasks),
            "health": float(self.health),
            "advertised_at_ms": int(self.advertised_at_ms),
            "ttl_ms": int(self.ttl_ms),
            "schema_version": int(self.schema_version),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> NodeCapability:
        ver = int(data.get("schema_version", CAPABILITY_SCHEMA_VERSION))
        if ver != CAPABILITY_SCHEMA_VERSION:
            raise UnknownCapabilitySchema(
                detail=f"unsupported capability schema_version: {ver}"
            )
        health = float(data.get("health", 1.0))
        if health < 0.0 or health > 1.0:
            health = max(0.0, min(1.0, health))
        return cls(
            node_id=str(data["node_id"]),
            cpu=int(data.get("cpu", 0)),
            memory=int(data.get("memory", 0)),
            accelerators=tuple(str(x) for x in data.get("accelerators", [])),
            storage=int(data.get("storage", 0)),
            network_class=str(data.get("network_class", "local")),
            supported_tasks=tuple(
                str(x) for x in data.get("supported_tasks", ["compute"])
            ),
            health=health,
            advertised_at_ms=int(data.get("advertised_at_ms", 0)),
            ttl_ms=int(data.get("ttl_ms", DEFAULT_CAP_TTL_MS)),
            schema_version=ver,
        )

    def is_stale(self, now_ms: int | None = None) -> bool:
        t = _now_ms() if now_ms is None else int(now_ms)
        return t > int(self.advertised_at_ms) + int(self.ttl_ms)

    def expires_at_ms(self) -> int:
        return int(self.advertised_at_ms) + int(self.ttl_ms)


def cap_state_fingerprint(caps: list[NodeCapability]) -> str:
    """Deterministic fingerprint of capability state (cap_state_fp)."""
    payload = [c.to_dict() for c in sorted(caps, key=lambda x: x.node_id)]
    blob = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()


def validate_capability(data: dict[str, Any]) -> NodeCapability:
    """Validate + build NodeCapability; raises UnknownCapabilitySchema."""
    if "node_id" not in data:
        raise UnknownCapabilitySchema(detail="node_id required")
    return NodeCapability.from_dict(data)


class CapabilityRegistry:
    """Capability advertisements persisted in C-RAM (op_id+epoch+trace_id).

    Layout under ``root``::

        .cram/...              # capability envelopes
        capability_index.json  # node_id → content_hash
        op_index.json          # op_id → content_hash (idempotent upserts)
    """

    def __init__(
        self,
        root: str | Path | None = None,
        *,
        available: bool = True,
        now_fn: Callable[[], int] | None = None,
        default_ttl_ms: int = DEFAULT_CAP_TTL_MS,
    ):
        self.root = Path(root) if root is not None else None
        self._available = bool(available)
        self._now_fn = now_fn or _now_ms
        self.default_ttl_ms = int(default_ttl_ms)
        self._by_node: dict[str, NodeCapability] = {}
        self._op_index: dict[str, str] = {}
        self._node_index: dict[str, str] = {}
        self.store: CRAMStore | None = None
        if self.root is not None:
            self.root.mkdir(parents=True, exist_ok=True)
            self.store = CRAMStore(self.root)
            self._index_path = self.root / "capability_index.json"
            self._op_path = self.root / "op_index.json"
            self._load()

    def mark_unavailable(self) -> None:
        self._available = False

    def mark_available(self) -> None:
        self._available = True

    @property
    def available(self) -> bool:
        return self._available

    def _load(self) -> None:
        if self.root is None:
            return
        if self._index_path.exists():
            raw = json.loads(self._index_path.read_text(encoding="utf-8"))
            self._node_index = {str(k): str(v) for k, v in raw.items()}
            for nid, key in self._node_index.items():
                try:
                    assert self.store is not None
                    blob = self.store.get(key)
                    env = json.loads(blob.decode("utf-8"))
                    cap = NodeCapability.from_dict(env.get("capability") or env)
                    self._by_node[nid] = cap
                except (CRAMError, KeyError, ValueError, TypeError):
                    continue
        if self._op_path.exists():
            raw = json.loads(self._op_path.read_text(encoding="utf-8"))
            self._op_index = {str(k): str(v) for k, v in raw.items()}

    def _save_indexes(self) -> None:
        if self.root is None:
            return
        self._index_path.write_text(
            json.dumps(self._node_index, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        self._op_path.write_text(
            json.dumps(self._op_index, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

    def upsert(
        self,
        cap: NodeCapability,
        *,
        op_id: str,
        epoch: int = 0,
        trace_id: str = "",
    ) -> str:
        """Persist capability advertisement; returns content_key as ACK.

        Idempotent on op_id. Raises CramPersistError if store unavailable.
        Raises UnknownCapabilitySchema on bad schema.
        """
        if cap.schema_version != CAPABILITY_SCHEMA_VERSION:
            raise UnknownCapabilitySchema(
                detail=f"unsupported capability schema_version: {cap.schema_version}"
            )
        if not op_id:
            raise CramPersistError(
                "op_id required for capability upsert",
                trace_id=trace_id or None,
            )
        if op_id in self._op_index:
            return self._op_index[op_id]

        # In-memory path (no C-RAM root): still record for routing.
        if self.store is None:
            self._by_node[cap.node_id] = cap
            self._op_index[op_id] = f"mem:{op_id}"
            return self._op_index[op_id]

        if not self._available:
            raise CramPersistError(
                "C-RAM unavailable for capability upsert",
                op_id=op_id,
                trace_id=trace_id or None,
                cause="store_marked_unavailable",
            )
        envelope = {
            "capability": cap.to_dict(),
            "op_id": op_id,
            "epoch": int(epoch),
            "trace_id": trace_id or op_id,
        }
        payload = json.dumps(
            envelope, sort_keys=True, separators=(",", ":")
        ).encode("utf-8")
        try:
            content_key = self.store.put(
                payload,
                metadata={
                    "type": "NODE_CAPABILITY",
                    "op_id": op_id,
                    "epoch": int(epoch),
                    "trace_id": trace_id or op_id,
                    "node_id": cap.node_id,
                },
            )
            self._op_index[op_id] = content_key
            self._node_index[cap.node_id] = content_key
            self._by_node[cap.node_id] = cap
            self._save_indexes()
            return content_key
        except CramPersistError:
            raise
        except Exception as exc:  # noqa: BLE001
            raise CramPersistError(
                "C-RAM capability persist failed",
                op_id=op_id,
                trace_id=trace_id or None,
                cause=str(exc),
            ) from exc

    def get(self, node_id: str) -> NodeCapability | None:
        return self._by_node.get(node_id)

    def list_all(self) -> list[NodeCapability]:
        return sorted(self._by_node.values(), key=lambda c: c.node_id)

    def list_fresh(self, now_ms: int | None = None) -> list[NodeCapability]:
        t = self._now_fn() if now_ms is None else int(now_ms)
        return [c for c in self.list_all() if not c.is_stale(t)]

    def list_stale(self, now_ms: int | None = None) -> list[NodeCapability]:
        t = self._now_fn() if now_ms is None else int(now_ms)
        return [c for c in self.list_all() if c.is_stale(t)]

    def require_fresh(self, node_id: str, now_ms: int | None = None) -> NodeCapability:
        """Return fresh capability or raise StaleCapability / KeyError."""
        cap = self.get(node_id)
        if cap is None:
            raise KeyError(node_id)
        t = self._now_fn() if now_ms is None else int(now_ms)
        if cap.is_stale(t):
            raise StaleCapability(
                f"capability expired for node {node_id}",
                node_id=node_id,
                advertised_at_ms=cap.advertised_at_ms,
                ttl_ms=cap.ttl_ms,
                now_ms=t,
            )
        return cap

    def fingerprint(self, *, fresh_only: bool = True, now_ms: int | None = None) -> str:
        caps = self.list_fresh(now_ms) if fresh_only else self.list_all()
        return cap_state_fingerprint(caps)

    def count(self) -> int:
        return len(self._by_node)

    def has_op_id(self, op_id: str) -> bool:
        return op_id in self._op_index


__all__ = [
    "CAPABILITY_SCHEMA_VERSION",
    "DEFAULT_CAP_TTL_MS",
    "T_CONV_CAPABILITY_S",
    "CapabilityRegistry",
    "NodeCapability",
    "cap_state_fingerprint",
    "validate_capability",
]
