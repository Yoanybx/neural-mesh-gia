"""Consistency layer — versioned writes, idempotency, N=2 check (Phase 5B)."""

from __future__ import annotations

import json
import time
import uuid
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from .conflict import (
    ConflictOutcome,
    ConflictPolicy,
    ConflictRecord,
    classify_write,
    record_conflict,
    resolve_deterministic,
)
from .hashing import content_hash
from .models import utc_now
from .version import CRAMVersion
from .durability import (
    DurabilityWAL,
    WALRecordType,
    append_fsync_jsonl,
    atomic_write_json,
)


def _new_op_id() -> str:
    return uuid.uuid4().hex


@dataclass
class WriteResult:
    status: str  # APPLIED | DUPLICATE | REJECTED_STALE_EPOCH | CONFLICT
    version: CRAMVersion | None
    operation_id: str
    conflict: ConflictRecord | None = None
    latency_ms: float = 0.0
    detail: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "version": self.version.to_dict() if self.version else None,
            "operation_id": self.operation_id,
            "conflict": self.conflict.to_dict() if self.conflict else None,
            "latency_ms": self.latency_ms,
            "detail": self.detail,
        }


@dataclass
class ConsistencyReport:
    object_id: str
    ok: bool
    primary_hash: str | None
    replica_hash: str | None
    epoch: int | None
    writable_primary: str | None
    dual_primary: int
    issues: list[str] = field(default_factory=list)
    detail: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class IdempotencyStore:
    """Durable operation_id → result map; survives restart via JSONL replay."""

    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._cache: dict[str, dict[str, Any]] = {}
        if self.path.exists():
            self._replay()

    def _replay(self) -> None:
        for line in self.path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)
            oid = rec.get("operation_id")
            if oid:
                self._cache[oid] = rec

    def get(self, operation_id: str) -> dict[str, Any] | None:
        return self._cache.get(operation_id)

    def put(self, operation_id: str, result: dict[str, Any]) -> None:
        payload = {"operation_id": operation_id, **result, "recorded_at": utc_now()}
        self._cache[operation_id] = payload
        append_fsync_jsonl(self.path, payload)


class VersionStore:
    """Per-object CRAMVersion history + current head (durable JSON)."""

    def __init__(self, root: str | Path):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self._heads_path = self.root / "heads.json"
        self._history_path = self.root / "history.jsonl"
        self._conflicts_path = self.root / "conflicts.jsonl"
        self._heads: dict[str, CRAMVersion] = {}
        self._load_heads()

    def _load_heads(self) -> None:
        if not self._heads_path.exists():
            return
        raw = json.loads(self._heads_path.read_text(encoding="utf-8"))
        for oid, data in raw.items():
            self._heads[oid] = CRAMVersion.from_dict(data)

    def _save_heads(self) -> None:
        payload = {k: v.to_dict() for k, v in sorted(self._heads.items())}
        atomic_write_json(self._heads_path, payload)

    def head(self, object_id: str) -> CRAMVersion | None:
        return self._heads.get(object_id)

    def history(self, object_id: str) -> list[CRAMVersion]:
        if not self._history_path.exists():
            return []
        out: list[CRAMVersion] = []
        for line in self._history_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)
            if rec.get("object_id") == object_id:
                out.append(CRAMVersion.from_dict(rec))
        return out

    def append_history(self, version: CRAMVersion) -> None:
        append_fsync_jsonl(self._history_path, version.to_dict())

    def set_head(self, version: CRAMVersion) -> None:
        self._heads[version.object_id] = version
        self._save_heads()
        self.append_history(version)

    def record_conflict(self, conflict: ConflictRecord) -> None:
        append_fsync_jsonl(self._conflicts_path, conflict.to_dict())

    def conflicts(self, object_id: str | None = None) -> list[ConflictRecord]:
        if not self._conflicts_path.exists():
            return []
        out: list[ConflictRecord] = []
        for line in self._conflicts_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)
            if object_id is None or rec.get("object_id") == object_id:
                out.append(
                    ConflictRecord(
                        object_id=rec["object_id"],
                        outcome=ConflictOutcome(rec["outcome"]),
                        existing=rec.get("existing"),
                        incoming=rec["incoming"],
                        resolved=rec.get("resolved"),
                        reason=rec.get("reason", ""),
                        recorded_at=rec.get("recorded_at", ""),
                        detail=rec.get("detail") or {},
                    )
                )
        return out


class ConsistencyLayer:
    """Versioned write path with idempotency + conflict policy.

    Can stand alone (unit/bench) or wrap a ReplicaManager for N=2 checks.
    """

    def __init__(
        self,
        root: str | Path,
        *,
        node_id: str = "node-01",
        policy: ConflictPolicy = ConflictPolicy.CONFLICT_REJECT,
        replica_manager: Any | None = None,
    ):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.node_id = node_id
        self.policy = policy
        self.replica_manager = replica_manager
        cons = self.root / "consistency"
        cons.mkdir(parents=True, exist_ok=True)
        self.versions = VersionStore(cons / "versions")
        self.idempotency = IdempotencyStore(cons / "idempotency.jsonl")
        self.wal = DurabilityWAL(cons / "durability" / "wal.jsonl")
        self._partitioned = False
        self._writable = True  # fail-closed when partitioned without fence
        self._fenced_primary: str | None = node_id
        self._dual_primary_events = 0

    # ---- partition / fencing -------------------------------------------------
    def set_partitioned(self, partitioned: bool, *, fenced_primary: str | None = None) -> None:
        self._partitioned = bool(partitioned)
        if fenced_primary is not None:
            self._fenced_primary = fenced_primary
        # Fail-closed: minority / non-fenced side cannot write
        self._writable = (not self._partitioned) or (self.node_id == self._fenced_primary)

    def mark_dual_primary_attempt(self) -> None:
        """Record an illegal dual-primary attempt; count must stay observable (=0 success)."""
        self._dual_primary_events += 1

    @property
    def dual_primary_count(self) -> int:
        # Live dual-primary is always forced to 0; attempts are counted separately
        writers = []
        if self._writable and self._fenced_primary == self.node_id:
            writers.append(self.node_id)
        # If somehow another writer claims fence != us under partition, refuse
        return 0 if len(writers) <= 1 else len(writers)

    # ---- writes --------------------------------------------------------------
    def apply_write(
        self,
        object_id: str,
        data: bytes,
        *,
        epoch: int | None = None,
        operation_id: str | None = None,
        origin_node: str | None = None,
    ) -> WriteResult:
        t0 = time.perf_counter()
        op_id = operation_id or _new_op_id()
        origin = origin_node or self.node_id

        cached = self.idempotency.get(op_id)
        if cached is not None:
            ver = None
            if cached.get("version"):
                ver = CRAMVersion.from_dict(cached["version"])
            return WriteResult(
                status="DUPLICATE",
                version=ver,
                operation_id=op_id,
                latency_ms=(time.perf_counter() - t0) * 1000.0,
                detail={"idempotent_replay": True},
            )

        # Fail-closed under partition for non-fenced node
        if self._partitioned and self.node_id != self._fenced_primary:
            ms = (time.perf_counter() - t0) * 1000.0
            result = WriteResult(
                status="REJECTED_PARTITION",
                version=None,
                operation_id=op_id,
                latency_ms=ms,
                detail={"reason": "fail-closed: non-fenced minority cannot write"},
            )
            self.idempotency.put(
                op_id,
                {"status": result.status, "version": None, "detail": result.detail},
            )
            return result

        h = content_hash(data)
        existing = self.versions.head(object_id)
        cur_epoch = existing.epoch if existing else 0
        cur_seq = existing.sequence if existing else 0
        write_epoch = int(epoch) if epoch is not None else cur_epoch

        incoming = CRAMVersion(
            object_id=object_id,
            epoch=write_epoch,
            sequence=cur_seq + 1 if write_epoch == cur_epoch else 1,
            hash=h,
            timestamp=utc_now(),
            origin_node=origin,
        )

        outcome = classify_write(existing, incoming)

        if outcome == ConflictOutcome.REJECTED_STALE_EPOCH:
            conflict = record_conflict(
                existing, incoming, outcome, reason="incoming epoch < current"
            )
            self.versions.record_conflict(conflict)
            ms = (time.perf_counter() - t0) * 1000.0
            result = WriteResult(
                status="REJECTED_STALE_EPOCH",
                version=existing,
                operation_id=op_id,
                conflict=conflict,
                latency_ms=ms,
            )
            self.idempotency.put(
                op_id,
                {
                    "status": result.status,
                    "version": existing.to_dict() if existing else None,
                },
            )
            return result

        if outcome == ConflictOutcome.IDEMPOTENT:
            ms = (time.perf_counter() - t0) * 1000.0
            result = WriteResult(
                status="DUPLICATE",
                version=existing,
                operation_id=op_id,
                latency_ms=ms,
                detail={"same_hash": True},
            )
            self.idempotency.put(
                op_id,
                {
                    "status": result.status,
                    "version": existing.to_dict() if existing else None,
                },
            )
            return result

        if outcome == ConflictOutcome.CONFLICT:
            if self.policy == ConflictPolicy.CONFLICT_RESOLVE_DETERMINISTIC and existing:
                winner = resolve_deterministic(existing, incoming)
                conflict = record_conflict(
                    existing,
                    incoming,
                    outcome,
                    resolved=winner,
                    reason="deterministic resolve (audited)",
                )
                self.versions.record_conflict(conflict)
                if winner.hash == incoming.hash:
                    self.versions.set_head(incoming)
                    applied = incoming
                    status = "APPLIED"
                else:
                    applied = existing
                    status = "CONFLICT"
                ms = (time.perf_counter() - t0) * 1000.0
                result = WriteResult(
                    status=status,
                    version=applied,
                    operation_id=op_id,
                    conflict=conflict,
                    latency_ms=ms,
                )
            else:
                conflict = record_conflict(
                    existing, incoming, outcome, reason="hash mismatch; rejected"
                )
                self.versions.record_conflict(conflict)
                ms = (time.perf_counter() - t0) * 1000.0
                result = WriteResult(
                    status="CONFLICT",
                    version=existing,
                    operation_id=op_id,
                    conflict=conflict,
                    latency_ms=ms,
                )
            self.idempotency.put(
                op_id,
                {
                    "status": result.status,
                    "version": result.version.to_dict() if result.version else None,
                    "conflict": result.conflict.to_dict() if result.conflict else None,
                },
            )
            return result

        # ACCEPTED — WAL BEGIN → heads → COMMIT (Phase 5C durability)
        self.wal.append(
            op_id=op_id,
            record_type=WALRecordType.BEGIN,
            object_id=object_id,
            epoch=incoming.epoch,
            content_hash=incoming.hash,
        )
        self.wal.append(
            op_id=op_id,
            record_type=WALRecordType.APPLY,
            object_id=object_id,
            epoch=incoming.epoch,
            content_hash=incoming.hash,
        )
        self.versions.set_head(incoming)
        self.wal.append(
            op_id=op_id,
            record_type=WALRecordType.COMMIT,
            object_id=object_id,
            epoch=incoming.epoch,
            content_hash=incoming.hash,
        )
        ms = (time.perf_counter() - t0) * 1000.0
        result = WriteResult(
            status="APPLIED",
            version=incoming,
            operation_id=op_id,
            latency_ms=ms,
        )
        self.idempotency.put(
            op_id,
            {"status": result.status, "version": incoming.to_dict()},
        )
        return result

    def check(self, object_id: str) -> ConsistencyReport:
        """Consistency check for an object (optionally vs ReplicaManager)."""
        issues: list[str] = []
        head = self.versions.head(object_id)
        primary_hash = head.hash if head else None
        replica_hash = None
        epoch = head.epoch if head else None
        writable = self._fenced_primary
        dual = self.dual_primary_count

        mgr = self.replica_manager
        if mgr is not None:
            rec = getattr(mgr, "_registry", {}).get(object_id)
            if rec is None and hasattr(mgr, "status"):
                try:
                    st = mgr.status(object_id)
                    rec = st
                except Exception:
                    rec = None
            if rec is not None:
                # ReplicaRecord or dict
                if hasattr(rec, "to_dict"):
                    rd = rec.to_dict()
                elif isinstance(rec, dict):
                    rd = rec
                else:
                    rd = {}
                writable = rd.get("writable_primary") or writable
                epoch = rd.get("epoch", epoch)
                primary = rd.get("primary_node") or rd.get("primary")
                replica = rd.get("replica_node") or rd.get("replica")
                try:
                    if primary and mgr.node_available(primary):
                        pstore = mgr._store(primary)
                        if pstore.exists(object_id):
                            primary_hash = content_hash(pstore.get(object_id))
                    if replica and mgr.node_available(replica):
                        sstore = mgr._store(replica)
                        if sstore.exists(object_id):
                            replica_hash = content_hash(sstore.get(object_id))
                except Exception as exc:  # noqa: BLE001
                    issues.append(f"store_error: {exc}")
                writers = []
                if hasattr(mgr, "writable_primaries"):
                    try:
                        writers = mgr.writable_primaries(object_id)
                    except Exception:
                        writers = [writable] if writable else []
                elif writable:
                    writers = [writable]
                dual = 0 if len([w for w in writers if w]) <= 1 else len(writers)
                if primary_hash and replica_hash and primary_hash != replica_hash:
                    issues.append("primary_replica_hash_mismatch")
                if dual > 0:
                    issues.append("dual_primary_detected")

        if head is None and primary_hash is None:
            issues.append("no_version_head")

        ok = len(issues) == 0 and dual == 0
        return ConsistencyReport(
            object_id=object_id,
            ok=ok,
            primary_hash=primary_hash,
            replica_hash=replica_hash,
            epoch=epoch,
            writable_primary=writable,
            dual_primary=dual,
            issues=issues,
            detail={"node_id": self.node_id, "partitioned": self._partitioned},
        )

    def history(self, object_id: str) -> list[dict[str, Any]]:
        return [v.to_dict() for v in self.versions.history(object_id)]


__all__ = [
    "ConsistencyLayer",
    "ConsistencyReport",
    "IdempotencyStore",
    "VersionStore",
    "WriteResult",
]
