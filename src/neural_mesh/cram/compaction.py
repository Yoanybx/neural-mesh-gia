"""Safe snapshot compaction — no corruption, no loss of verified objects (Phase 5C)."""

from __future__ import annotations

import json
import time
import uuid
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from .durability import (
    DurabilityWAL,
    WALRecordType,
    atomic_write_bytes,
    atomic_write_json,
)
from .hashing import content_hash
from .models import utc_now
from .store import CRAMStore


@dataclass
class CompactionReport:
    ok: bool
    snapshot_id: str
    retained: int
    garbage_candidates: int
    deleted: int
    verified: int
    aborted: bool = False
    latency_ms: float = 0.0
    issues: list[str] = field(default_factory=list)
    detail: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class SnapshotCompactor:
    """Transactional compaction of CAS + consistency snapshot pointer.

    Protocol:
      1. VERIFY all retained keys (content hash)
      2. Write new snapshot manifest (atomic fsync)
      3. Flip ``CURRENT`` pointer (atomic)
      4. Only then GC orphan objects not in any verified snapshot
    Mid-compact crash → prior snapshot remains; no data loss.
    """

    def __init__(self, root: str | Path):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.store = CRAMStore(self.root)
        self.snap_root = self.root / "consistency" / "snapshots"
        self.snap_root.mkdir(parents=True, exist_ok=True)
        self.current_ptr = self.snap_root / "CURRENT.json"
        self.wal = DurabilityWAL(self.root / "consistency" / "durability" / "wal.jsonl")

    def _read_current(self) -> str | None:
        if not self.current_ptr.exists():
            return None
        try:
            data = json.loads(self.current_ptr.read_text(encoding="utf-8"))
            return data.get("snapshot_id")
        except (json.JSONDecodeError, OSError):
            return None

    def compact(
        self,
        *,
        retain_keys: list[str] | None = None,
        delete_orphans: bool = True,
        simulate_crash_before_flip: bool = False,
    ) -> CompactionReport:
        t0 = time.perf_counter()
        issues: list[str] = []
        op_id = f"compact-{uuid.uuid4().hex[:12]}"
        self.wal.append(
            op_id=op_id, record_type=WALRecordType.BEGIN, detail={"phase": "compact"}
        )

        keys = list(retain_keys) if retain_keys is not None else self.store.list_keys()
        verified: list[str] = []
        for key in keys:
            if not self.store.exists(key):
                issues.append(f"missing:{key}")
                continue
            if not self.store.verify(key):
                issues.append(f"corrupt:{key}")
                continue
            verified.append(key)

        if issues and retain_keys is not None:
            self.wal.append(
                op_id=op_id,
                record_type=WALRecordType.ABORT,
                detail={"issues": issues},
            )
            return CompactionReport(
                ok=False,
                snapshot_id="",
                retained=0,
                garbage_candidates=0,
                deleted=0,
                verified=len(verified),
                aborted=True,
                latency_ms=(time.perf_counter() - t0) * 1000.0,
                issues=issues,
            )

        snap_id = f"snap-{uuid.uuid4().hex}"
        snap_dir = self.snap_root / snap_id
        snap_dir.mkdir(parents=True, exist_ok=True)
        manifest = {
            "snapshot_id": snap_id,
            "created_at": utc_now(),
            "keys": sorted(verified),
            "count": len(verified),
            "root_hash": (
                self.store.compute_root_hash(verified)
                if verified
                else content_hash(b"")
            ),
        }
        atomic_write_json(snap_dir / "manifest.json", manifest)
        self.wal.append(
            op_id=op_id,
            record_type=WALRecordType.COMPACT,
            detail={"snapshot_id": snap_id, "keys": len(verified)},
        )

        if simulate_crash_before_flip:
            self.wal.append(
                op_id=op_id,
                record_type=WALRecordType.ABORT,
                detail={"reason": "simulated_crash_before_flip"},
            )
            return CompactionReport(
                ok=True,
                snapshot_id=snap_id,
                retained=len(verified),
                garbage_candidates=0,
                deleted=0,
                verified=len(verified),
                aborted=True,
                latency_ms=(time.perf_counter() - t0) * 1000.0,
                issues=[],
                detail={"crash": "before_flip", "prior_current": self._read_current()},
            )

        prior = self._read_current()
        atomic_write_json(
            self.current_ptr,
            {"snapshot_id": snap_id, "prior": prior, "flipped_at": utc_now()},
        )
        atomic_write_bytes(
            self.snap_root / "CURRENT.txt", (snap_id + "\n").encode("utf-8")
        )

        deleted = 0
        garbage = 0
        if delete_orphans:
            retain_set = set(verified)
            if prior:
                prior_manifest = self.snap_root / prior / "manifest.json"
                if prior_manifest.exists():
                    try:
                        pm = json.loads(prior_manifest.read_text(encoding="utf-8"))
                        retain_set |= set(pm.get("keys") or [])
                    except json.JSONDecodeError:
                        pass
            for key in self.store.list_keys():
                if key not in retain_set:
                    garbage += 1
                    if self.store.verify(key):
                        path = self.store._object_path(key)
                        meta = self.store._meta_path(key)
                        try:
                            path.unlink(missing_ok=True)
                            meta.unlink(missing_ok=True)
                            deleted += 1
                        except OSError as exc:
                            issues.append(f"gc_error:{key}:{exc}")

        self.wal.append(
            op_id=op_id,
            record_type=WALRecordType.COMMIT,
            detail={"snapshot_id": snap_id, "deleted": deleted},
        )
        ok = not any(i.startswith("corrupt:") for i in issues)
        return CompactionReport(
            ok=ok,
            snapshot_id=snap_id,
            retained=len(verified),
            garbage_candidates=garbage,
            deleted=deleted,
            verified=len(verified),
            aborted=False,
            latency_ms=(time.perf_counter() - t0) * 1000.0,
            issues=issues,
            detail={"prior": prior},
        )


__all__ = ["CompactionReport", "SnapshotCompactor"]
