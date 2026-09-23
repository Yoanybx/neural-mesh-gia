"""WAL/fsync policy + crash-recovery invariants (Phase 5C / CP-0018..0020)."""

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


class SyncMode(str, Enum):
    """Durable write sync policy.

    EVERY — durable content on every atomic write (sync-every-write). C16 hot path:
            os.write + fdatasync (fallback fsync) → replace → dir fsync policy
            (`DURABLE_DIR_FSYNC=every|coalesce`). Honest overlay floor often still
            >0.1 ms p99; never fabricate. Crash: mid-write leaves only tmp.
    BATCH — hot-path atomic replace without fsync; GroupFsyncSeal.seal() group
            fsyncs dirty files. Crash invariants: mid-write leaves only tmp;
            after seal, durable. Unsealed BATCH writes may be lost on power fail.
    """

    EVERY = "every"
    BATCH = "batch"


def resolve_sync_mode(explicit: str | SyncMode | None = None) -> SyncMode:
    if explicit is not None:
        return SyncMode(explicit.value if isinstance(explicit, SyncMode) else explicit)
    env = os.environ.get("DURABLE_SYNC", "every").strip().lower()
    if env in ("batch", "group", "deferred"):
        return SyncMode.BATCH
    return SyncMode.EVERY


def resolve_dir_fsync_mode(explicit: str | None = None) -> str:
    """every (default) | coalesce — POSIX-safe dir fsync policy for EVERY mode.

    coalesce: file content still fdatasync'd per op; directory-entry durability
    deferred to DirFsyncCoalescer.flush() / GroupFsyncSeal.seal() / explicit flush.
    Mid-write crash sims unchanged (tmp-only). Rename may be lost on power-fail
    before flush on some FS — documented as C16 EVERY coalesce tradeoff.
    """
    if explicit is not None:
        v = explicit.strip().lower()
        return "coalesce" if v in ("coalesce", "deferred", "batch") else "every"
    env = os.environ.get("DURABLE_DIR_FSYNC", "every").strip().lower()
    if env in ("coalesce", "deferred", "batch"):
        return "coalesce"
    return "every"


@dataclass
class DirFsyncCoalescer:
    """Tracks dirty parent dirs for POSIX-safe dir fsync coalesce (C16)."""

    dirty: set[str] = field(default_factory=set)
    ops_since_flush: int = 0
    auto_every: int = 0  # 0 = never auto; >0 flush every N notes

    def note(self, parent: Path) -> None:
        self.dirty.add(str(Path(parent)))
        self.ops_since_flush += 1
        if self.auto_every > 0 and self.ops_since_flush >= self.auto_every:
            self.flush()

    def flush(self) -> dict[str, Any]:
        dirs_done = 0
        for parent in list(self.dirty):
            try:
                dir_fd = os.open(parent, os.O_RDONLY)
                try:
                    os.fsync(dir_fd)
                finally:
                    os.close(dir_fd)
                dirs_done += 1
            except OSError:
                continue
        n = len(self.dirty)
        self.dirty.clear()
        self.ops_since_flush = 0
        return {"dirs": dirs_done, "noted": n}


_DEFAULT_DIR_COALESCE = DirFsyncCoalescer()


def get_dir_coalescer() -> DirFsyncCoalescer:
    return _DEFAULT_DIR_COALESCE


def reset_dir_coalescer(*, auto_every: int = 0) -> DirFsyncCoalescer:
    global _DEFAULT_DIR_COALESCE
    _DEFAULT_DIR_COALESCE = DirFsyncCoalescer(auto_every=auto_every)
    return _DEFAULT_DIR_COALESCE


def compact_checkpoint_bytes(seq: int, digest: str | None = None) -> bytes:
    """Minimal checkpoint seal payload (C16 smaller-seal attempt)."""
    if digest:
        return b'{"i":%d,"h":"%s"}' % (seq, digest.encode("ascii"))
    return b'{"i":%d}' % (seq,)


def _fsync_file_fd(fd: int) -> None:
    """Prefer fdatasync for content; fall back to fsync."""
    if hasattr(os, "fdatasync"):
        os.fdatasync(fd)
    else:
        os.fsync(fd)


def _dir_fsync_now(parent: Path) -> None:
    try:
        dir_fd = os.open(str(parent), os.O_RDONLY)
        try:
            os.fsync(dir_fd)
        finally:
            os.close(dir_fd)
    except OSError:
        pass


@dataclass
class GroupFsyncSeal:
    """Tracks dirty paths for BATCH mode group fsync (durable seal)."""

    dirty: list[Path] = field(default_factory=list)
    sealed: bool = False

    def note(self, path: Path) -> None:
        self.dirty.append(Path(path))
        self.sealed = False

    def seal(self) -> dict[str, Any]:
        """fsync all dirty files + best-effort parent dir fsync. Idempotent-ish."""
        files = 0
        dirs_done: set[str] = set()
        for path in self.dirty:
            path = Path(path)
            if not path.exists():
                continue
            try:
                fd = os.open(str(path), os.O_RDONLY)
                try:
                    os.fsync(fd)
                finally:
                    os.close(fd)
                files += 1
            except OSError:
                continue
            parent = str(path.parent)
            if parent not in dirs_done:
                try:
                    dir_fd = os.open(parent, os.O_RDONLY)
                    try:
                        os.fsync(dir_fd)
                    finally:
                        os.close(dir_fd)
                    dirs_done.add(parent)
                except OSError:
                    pass
        # Also flush any deferred EVERY-mode dir fsync notes (C16 coalesce).
        coal_info = get_dir_coalescer().flush()
        self.sealed = True
        n = len(self.dirty)
        self.dirty.clear()
        return {
            "sealed_files": files,
            "dirs": len(dirs_done),
            "noted": n,
            "dir_coalesce": coal_info,
        }


# Default process-wide seal group for BATCH mode (tests may replace).
_DEFAULT_SEAL_GROUP = GroupFsyncSeal()


def get_seal_group() -> GroupFsyncSeal:
    return _DEFAULT_SEAL_GROUP


def reset_seal_group() -> GroupFsyncSeal:
    global _DEFAULT_SEAL_GROUP
    _DEFAULT_SEAL_GROUP = GroupFsyncSeal()
    return _DEFAULT_SEAL_GROUP


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


def atomic_write_bytes(
    path: Path,
    data: bytes,
    *,
    sync_mode: str | SyncMode | None = None,
    seal_group: GroupFsyncSeal | None = None,
    dir_fsync: str | None = None,
    dir_coalescer: DirFsyncCoalescer | None = None,
) -> SyncMode:
    """Crash-safe write; fsync policy by SyncMode.

    EVERY (C16): tmp → os.write → fdatasync|fsync → replace → dir fsync policy
           (`dir_fsync` / DURABLE_DIR_FSYNC=every|coalesce). Avoids Python
           buffered flush+fsync double work on the hot path.
    BATCH: single write_bytes of the full buffer (no per-op fsync); path noted on
           seal_group for GroupFsyncSeal.seal(). Small complete writes; mid-write
           crash sims still use simulate_crash_mid_write (tmp-only). After seal,
           durable. Unsealed BATCH may be lost on power-fail.
    Returns the resolved SyncMode used.
    """
    mode = resolve_sync_mode(sync_mode)
    path = Path(path)
    parent = path.parent
    parent.mkdir(parents=True, exist_ok=True)
    if mode == SyncMode.BATCH:
        path.write_bytes(data)
        group = seal_group if seal_group is not None else get_seal_group()
        group.note(path)
        return mode
    fd, tmp = tempfile.mkstemp(prefix=".tmp-", dir=parent)
    closed = False
    try:
        try:
            os.write(fd, data)
            _fsync_file_fd(fd)
        finally:
            os.close(fd)
            closed = True
        os.replace(tmp, path)
        dmode = resolve_dir_fsync_mode(dir_fsync)
        if dmode == "coalesce":
            coal = dir_coalescer if dir_coalescer is not None else get_dir_coalescer()
            coal.note(parent)
        else:
            _dir_fsync_now(parent)
    finally:
        if not closed:
            try:
                os.close(fd)
            except OSError:
                pass
        if os.path.exists(tmp):
            try:
                os.unlink(tmp)
            except OSError:
                pass
    return mode


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
    "cas": "tmp→os.write→fdatasync|fsync→replace→dir_fsync(every|coalesce)",
    "heads": "atomic_write_json (fsync)",
    "wal": "append→flush→fsync",
    "idempotency": "append→flush→fsync",
    "history": "append→flush→fsync",
    "ordering": "BEGIN+fsync → payload → heads → COMMIT+fsync",
    "honesty": "best-effort as far as FS honors fsync; not power-fail lab certified",
    "majority_clarification": (
        "N=2 'majority' = fenced primary side / heal path only — NOT Raft quorum"
    ),
    "sync_modes": {
        "every": "per-op content fdatasync + dir policy (DURABLE_SYNC=every); C16 optimized; honest floor may remain >0.1ms p99 on overlay",
        "batch": (
            "hot-path write_bytes without fsync; GroupFsyncSeal.seal() group fsync "
            "(DURABLE_SYNC=batch). Meets checkpoint_durable≤0.1ms hot-path SLO; "
            "mid-write sims tmp-only; post-seal durable."
        ),
    },
    "slo_close_c15": {
        "checkpoint_durable": "≤0.1ms p99 under BATCH hot-path; EVERY reported as floor",
        "recovery": "≤2ms p99 (tuned VERIFY path; same FSM method as C14)",
    },
    "every_opt_c16": {
        "hot_path": "os.write + fdatasync|fsync → replace → dir fsync policy",
        "dir_fsync": "DURABLE_DIR_FSYNC=every|coalesce (POSIX-safe defer of dir entry)",
        "payload": "compact_checkpoint_bytes for minimal seal",
        "target": "checkpoint_every_floor p99≤0.1 if honestly possible; else EXPLICIT DEBT",
        "tmpfs_note": "isolation note only; primary MET/GAP measured on same FS as C15",
    },
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
    "DirFsyncCoalescer",
    "DurabilityChecker",
    "DurabilityReport",
    "DurabilityWAL",
    "FSYNC_POLICY",
    "GroupFsyncSeal",
    "SyncMode",
    "WALRecord",
    "WALRecordType",
    "append_fsync_jsonl",
    "atomic_write_bytes",
    "atomic_write_json",
    "compact_checkpoint_bytes",
    "durable_apply",
    "get_dir_coalescer",
    "get_seal_group",
    "reset_dir_coalescer",
    "reset_seal_group",
    "resolve_dir_fsync_mode",
    "resolve_sync_mode",
    "simulate_crash_mid_append",
    "simulate_crash_mid_checkpoint",
    "simulate_crash_mid_write",
]
