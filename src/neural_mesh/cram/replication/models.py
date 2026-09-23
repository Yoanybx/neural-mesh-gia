"""Replica N=2 models — states, records, failover (Cycle 6)."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any


class ReplicaState(str, Enum):
    CREATED = "CREATED"
    SYNCING = "SYNCING"
    SYNCED = "SYNCED"
    FAILED = "FAILED"


class FailoverStatus(str, Enum):
    PRIMARY_HEALTHY = "PRIMARY_HEALTHY"
    FAILOVER_AVAILABLE = "FAILOVER_AVAILABLE"
    FAILOVER_BLOCKED = "FAILOVER_BLOCKED"


@dataclass
class ReplicaRecord:
    """Per-object N=2 replica descriptor."""

    content_hash: str
    primary_node: str
    replica_node: str
    status: ReplicaState = ReplicaState.CREATED
    epoch: int = 0
    version: int = 0
    verified: bool = False
    last_op_id: str | None = None
    error: str | None = None
    writable_primary: str | None = None  # who may accept writes (fencing)

    def __post_init__(self) -> None:
        if self.writable_primary is None:
            self.writable_primary = self.primary_node
        if isinstance(self.status, str):
            self.status = ReplicaState(self.status)

    @property
    def replica_nodes(self) -> list[str]:
        return [self.replica_node]

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["status"] = self.status.value if isinstance(self.status, ReplicaState) else self.status
        d["replica_nodes"] = self.replica_nodes
        return d

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ReplicaRecord":
        payload = dict(data)
        payload.pop("replica_nodes", None)
        return cls(
            content_hash=payload["content_hash"],
            primary_node=payload["primary_node"],
            replica_node=payload["replica_node"],
            status=ReplicaState(payload.get("status", ReplicaState.CREATED)),
            epoch=int(payload.get("epoch", 0)),
            version=int(payload.get("version", 0)),
            verified=bool(payload.get("verified", False)),
            last_op_id=payload.get("last_op_id"),
            error=payload.get("error"),
            writable_primary=payload.get("writable_primary"),
        )


@dataclass
class ReplicationOp:
    """Logged mutation with op_id + epoch for idempotent apply."""

    op_id: str
    op_type: str
    content_hash: str
    epoch: int
    node_id: str
    result: str = "APPLIED"  # APPLIED | DUPLICATE | REJECTED_STALE_EPOCH
    detail: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


__all__ = [
    "FailoverStatus",
    "ReplicaRecord",
    "ReplicaState",
    "ReplicationOp",
]
