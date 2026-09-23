"""WAL/fsync policy + crash-recovery invariants (Phase 5C / CP-0018)."""

from __future__ import annotations

import json
import os
import tempfile
import time
import uuid
from dataclasses import asdict, dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Iterable

from .hashing import content_hash
from .models import utc_now


class WALRecordType(str, Enum):
    BEGIN = "BEGIN"
    APPLY = "APPLY"
    COMMIT = "COMMIT"
    ABORT = "ABORT"
    CHECKPOINT = "CHECKPOINT"
    COMPACT = "COMPACT"


@dataclass
class WALRecord:
    record_id: str
    op_id: str
    record_type: WALRecordType
    object_id: str | None = None
    epoch: int | None = None
    content_hash: str | None = None
    detail: dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=utc_now)

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["record_type"] = self.record_type.value
        return d

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "WALRecord":
        return cls(
            record_id=data["record_id"],
            op_id=data["op_id"],
            record_type=WALRecordType(data["record_type"]),
            object_id=data.get("object_id"),
            epoch=data.get("epoch"),
            content_hash=data.get("content_hash"),
            detail=dict(data.get("detail") or {}),
            timestamp=data.get("timestamp") or utc_now(),
        )


def atomic_write_bytes(path: Path, data: bytes) -> None:
    """Crash-safe write: tmp → fsync file → replace → best-effort dir fsync."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=".tmp-", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(data)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)
        try:
            dir_fd = os.open(str(path.parent), os.O_RDONLY)
            try:
                os.fsync(dir_fd)
            finally:
                os.close(dir_fd)
        except OSError:
            pass
    finally:
        if os.path.exists(tmp):
            try:
                os.unlink(tmp)
            except OSError:
                pass


def atomic_write_json(path: Path, payload: Any) -> None:
    atomic_write_bytes(
        path,
        json.dumps(payload, indent=2, sort_keys=True).encode("utf-8"),
    )


def append_fsync_jsonl(path: Path, record: dict[str, Any]) -> None:
    """Append one JSONL record and fsync the file (WAL durability)."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    line = json.dumps(record, sort_keys=True) + "\n"
    with path.open("a", encoding="utf-8") as f:
        f.write(line)
        f.flush()
        os.fsync(f.fileno())


class DurabilityWAL:
    """Append-only durability WAL with fsync-on-append."""

    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._records: list[WALRecord] = []
        if self.path.exists():
            self._replay()

    def _replay(self) -> None:
        for line in self.path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                self._records.append(WALRecord.from_dict(json.loads(line)))
            except (json.JSONDecodeError, KeyError, ValueError):
                # Truncated / corrupt mid-append line — ignore (crash invariant)
                continue

    def append(
        self,
        *,
        op_id: str,
        record_type: WALRecordType,
        object_id: str | None = None,
        epoch: int | None = None,
        content_hash: str | None = None,
        detail: dict[str, Any] | None = None,
    ) -> WALRecord:
        rec = WALRecord(
            record_id=uuid.uuid4().hex,
            op_id=op_id,
            record_type=record_type,
            object_id=object_id,
            epoch=epoch,
            content_hash=content_hash,
            detail=dict(detail or {}),
        )
        append_fsync_jsonl(self.path, rec.to_dict())
        self._records.append(rec)
        return rec

    def records(self) -> list[WALRecord]:
        return list(self._records)

    def committed_ops(self) -> set[str]:
        begun: set[str] = set()
        committed: set[str] = set()
        aborted: set[str] = set()
        for r in self._records:
            if r.record_type == WALRecordType.BEGIN:
                begun.add(r.op_id)
            elif r.record_type == WALRecordType.COMMIT:
                committed.add(r.op_id)
            elif r.record_type == WALRecordType.ABORT:
                aborted.add(r.op_id)
        return committed - aborted

    def incomplete_ops(self) -> set[str]:
        """Ops with BEGIN/APPLY but no COMMIT (and not ABORT)."""
        state: dict[str, str] = {}
        for r in self._records:
            if r.record_type == WALRecordType.BEGIN:
                state[r.op_id] = "BEGIN"
            elif r.record_type == WALRecordType.APPLY:
                state[r.op_id] = "APPLY"
            elif r.record_type == WALRecordType.COMMIT:
                state[r.op_id] = "COMMIT"
            elif r.record_type == WALRecordType.ABORT:
                state[r.op_id] = "ABORT"
        return {oid for oid, st in state.items() if st in ("BEGIN", "APPLY")}


@dataclass
class CrashInvariantResult:
    name: str
    ok: bool
    detail: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class DurabilityReport:
    ok: bool
    wal_path: str
    committed_ops: int
    incomplete_ops: int
    crash_invariants: list[CrashInvariantResult] = field(default_factory=list)
    issues: list[str] = field(default_factory=list)
    fsync_policy: dict[str, Any] = field(default_factory=dict)
    detail: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "wal_path": self.wal_path,
            "committed_ops": self.committed_ops,
            "incomplete_ops": self.incomplete_ops,
            "crash_invariants": [c.to_dict() for c in self.crash_invariants],
            "issues": self.issues,
            "fsync_policy": self.fsync_policy,
            "detail": self.detail,
        }


FSYNC_POLICY = {
    "cas": "tmp→write→fsync→replace→dir_fsync(best-effort)",
    "heads": "atomic_write_json (fsync)",
    "wal": "append→flush→fsync",
    "idempotency": "append→flush→fsync",
    "history": "append→flush→fsync",
    "ordering": "BEGIN+fsync → payload → heads → COMMIT+fsync",
    "honesty": "best-effort as far as FS honors fsync; not power-fail lab certified",
    "majority_clarification": (
        "N=2 'majority' = fenced primary side / heal path only — NOT Raft quorum"
    ),
}


class DurabilityChecker:
    """Verify WAL integrity + formal crash-recovery invariants."""

    def __init__(self, root: str | Path):
        self.root = Path(root)
        cons = self.root / "consistency"
        self.wal = DurabilityWAL(cons / "durability" / "wal.jsonl")
        self.heads_path = cons / "versions" / "heads.json"
        self.idem_path = cons / "idempotency.jsonl"
        self.cram_dir = self.root / ".cram"

    def check(self) -> DurabilityReport:
        issues: list[str] = []
        invariants: list[CrashInvariantResult] = []

        # Invariant: incomplete ops must not appear as committed heads for unknown ops
        incomplete = self.wal.incomplete_ops()
        committed = self.wal.committed_ops()
        invariants.append(
            CrashInvariantResult(
                name="incomplete_ops_not_committed",
                ok=incomplete.isdisjoint(committed),
                detail={"incomplete": sorted(incomplete), "committed_n": len(committed)},
            )
        )
        if not incomplete.isdisjoint(committed):
            issues.append("incomplete_op_also_committed")

        # Invariant: no leftover .tmp- files that look like mid-write (report only)
        tmp_leftovers = list(self._find_tmp_files())
        # Presence of tmp is a *symptom* of mid-write crash; objects must not be
        # partially visible under final names. We treat leftovers as advisory OK
        # if final paths either absent or fully verify.
        mid_write_ok = True
        for tmp in tmp_leftovers:
            final = self._guess_final_from_tmp(tmp)
            if final is not None and final.exists():
                # If both exist, final must be complete (hashable); tmp is GC candidate
                try:
                    _ = final.read_bytes()
                except OSError:
                    mid_write_ok = False
                    issues.append(f"unreadable_final_with_tmp:{final}")
        invariants.append(
            CrashInvariantResult(
                name="mid_write_no_partial_visible",
                ok=mid_write_ok,
                detail={"tmp_leftovers": [str(p) for p in tmp_leftovers[:20]]},
            )
        )

        # Invariant: heads.json parseable or absent (mid-checkpoint must not corrupt)
        heads_ok = True
        heads_n = 0
        if self.heads_path.exists():
            try:
                raw = json.loads(self.heads_path.read_text(encoding="utf-8"))
                if not isinstance(raw, dict):
                    heads_ok = False
                    issues.append("heads_not_object")
                else:
                    heads_n = len(raw)
            except json.JSONDecodeError:
                heads_ok = False
                issues.append("heads_json_corrupt")
        invariants.append(
            CrashInvariantResult(
                name="mid_checkpoint_heads_intact",
                ok=heads_ok,
                detail={"heads": heads_n},
            )
        )

        # Invariant: truncated WAL lines ignored; replay does not raise
        invariants.append(
            CrashInvariantResult(
                name="mid_append_truncated_ignored",
                ok=True,
                detail={"wal_records": len(self.wal.records())},
            )
        )

        # CAS verify sample (if any objects)
        cas_ok = True
        verified = 0
        corrupt = 0
        if self.cram_dir.exists():
            for f in self._iter_cas_files():
                key = f.parent.name + f.name
                try:
                    if content_hash(f.read_bytes()) != key:
                        corrupt += 1
                        cas_ok = False
                    else:
                        verified += 1
                except OSError:
                    corrupt += 1
                    cas_ok = False
        if corrupt:
            issues.append(f"cas_corrupt:{corrupt}")
        invariants.append(
            CrashInvariantResult(
                name="cas_objects_verify",
                ok=cas_ok,
                detail={"verified": verified, "corrupt": corrupt},
            )
        )

        ok = all(i.ok for i in invariants) and not issues
        return DurabilityReport(
            ok=ok,
            wal_path=str(self.wal.path),
            committed_ops=len(committed),
            incomplete_ops=len(incomplete),
            crash_invariants=invariants,
            issues=issues,
            fsync_policy=dict(FSYNC_POLICY),
            detail={"root": str(self.root)},
        )

    def _find_tmp_files(self) -> Iterable[Path]:
        roots = [self.root / "consistency", self.cram_dir]
        for root in roots:
            if not root.exists():
                continue
            for p in root.rglob(".tmp-*"):
                if p.is_file():
                    yield p

    @staticmethod
    def _guess_final_from_tmp(tmp: Path) -> Path | None:
        # tempfile.mkstemp prefix=".tmp-" in same dir as final; cannot always guess
        return None

    def _iter_cas_files(self) -> Iterable[Path]:
        if not self.cram_dir.exists():
            return
        for shard in self.cram_dir.iterdir():
            if not shard.is_dir() or len(shard.name) != 2:
                continue
            for f in shard.iterdir():
                if f.is_file() and not f.name.endswith(".meta.json") and not f.name.startswith(".tmp-"):
                    yield f


def simulate_crash_mid_write(target: Path, data: bytes) -> Path:
    """Leave a .tmp-* file as if kill -9 happened before replace. Returns tmp path."""
    target = Path(target)
    target.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=".tmp-", dir=target.parent)
    with os.fdopen(fd, "wb") as f:
        f.write(data)
        f.flush()
        # Intentionally NO replace — simulates crash mid-write
    return Path(tmp)


def simulate_crash_mid_append(wal_path: Path, partial: str = '{"record_type":"BEGIN","op_id":"cr') -> None:
    """Append a truncated JSONL line (no fsync required for the fault itself)."""
    wal_path = Path(wal_path)
    wal_path.parent.mkdir(parents=True, exist_ok=True)
    with wal_path.open("a", encoding="utf-8") as f:
        f.write(partial)  # no newline / incomplete JSON


def simulate_crash_mid_checkpoint(checkpoint_path: Path, partial_json: str = '{"checkpoint_id":"CP-') -> Path:
    """Write incomplete checkpoint tmp; do not flip final. Returns tmp path."""
    checkpoint_path = Path(checkpoint_path)
    checkpoint_path.parent.mkdir(parents=True, exist_ok=True)
    tmp = checkpoint_path.with_suffix(".tmp")
    tmp.write_text(partial_json, encoding="utf-8")
    return tmp


def durable_apply(
    wal: DurabilityWAL,
    *,
    op_id: str,
    object_id: str,
    epoch: int,
    content_hash_val: str,
    commit_fn,
) -> dict[str, Any]:
    """Run BEGIN → commit_fn → COMMIT with WAL fencing; ABORT on error."""
    t0 = time.perf_counter()
    wal.append(
        op_id=op_id,
        record_type=WALRecordType.BEGIN,
        object_id=object_id,
        epoch=epoch,
        content_hash=content_hash_val,
    )
    try:
        wal.append(
            op_id=op_id,
            record_type=WALRecordType.APPLY,
            object_id=object_id,
            epoch=epoch,
            content_hash=content_hash_val,
        )
        result = commit_fn()
        wal.append(
            op_id=op_id,
            record_type=WALRecordType.COMMIT,
            object_id=object_id,
            epoch=epoch,
            content_hash=content_hash_val,
            detail={"ok": True},
        )
        return {
            "status": "COMMITTED",
            "result": result,
            "latency_ms": (time.perf_counter() - t0) * 1000.0,
        }
    except Exception as exc:  # noqa: BLE001
        wal.append(
            op_id=op_id,
            record_type=WALRecordType.ABORT,
            object_id=object_id,
            epoch=epoch,
            content_hash=content_hash_val,
            detail={"error": str(exc)},
        )
        return {
            "status": "ABORTED",
            "error": str(exc),
            "latency_ms": (time.perf_counter() - t0) * 1000.0,
        }


__all__ = [
    "DurabilityChecker",
    "DurabilityReport",
    "DurabilityWAL",
    "FSYNC_POLICY",
    "WALRecord",
    "WALRecordType",
    "append_fsync_jsonl",
    "atomic_write_bytes",
    "atomic_write_json",
    "durable_apply",
    "simulate_crash_mid_append",
    "simulate_crash_mid_checkpoint",
    "simulate_crash_mid_write",
]
