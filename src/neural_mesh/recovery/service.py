"""Recovery service: snapshot / restore / rebuild / ABORT→snapshot restore.

Builds on durable state + append-only WAL under a data root.
Fail-closed. dual_primary hard 0. No Vault/ACME. No plaintext.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .models import (
    SCHEMA_ID,
    DurableState,
    RebuildResult,
    RecoveryAbortRestore,
    RecoveryError,
    RecoveryMissingSnapshot,
    RecoveryRebuildFailed,
    RecoveryStatus,
    RecoveryTamper,
    RestoreResult,
    SnapshotMeta,
)
from .store import RecoveryStore, require_no_plaintext


def _utcnow() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


class RecoveryService:
    """H2 recovery + rebuild around a local data root (N≤2; no Raft)."""

    def __init__(self, data_root: str | Path):
        self.data_root = Path(data_root)
        self.store = RecoveryStore(self.data_root)

    # --- status ---

    def status(self) -> RecoveryStatus:
        durable = self.store.load_durable()
        st = self.store.state()
        issues: list[str] = []
        if st.get("abort_restore"):
            issues.append("abort_restore")
        ids = self.store.list_snapshot_ids()
        last_good = str(st.get("last_good_snapshot") or "")
        if last_good and last_good not in ids:
            issues.append("last_good_missing")
        ok = "abort_restore" not in issues and "last_good_missing" not in issues
        return RecoveryStatus(
            ok=ok,
            data_root=str(self.data_root),
            durable=durable.to_dict(),
            last_good_snapshot=last_good,
            snapshot_count=len(ids),
            wal_entries=self.store.wal_len(),
            abort_restore=bool(st.get("abort_restore")),
            abort_reason=str(st.get("abort_reason") or ""),
            issues=issues,
        )

    # --- mutations ---

    def apply(
        self,
        patch: dict[str, Any],
        *,
        mode: str = "local",
    ) -> DurableState:
        """Apply a payload patch: append WAL then update durable projection."""
        require_no_plaintext(mode)
        durable = self.store.load_durable()
        durable.seq += 1
        durable.payload = {**durable.payload, **dict(patch)}
        durable.updated_at = _utcnow()
        self.store.append_wal(
            {
                "op": "apply",
                "seq": durable.seq,
                "epoch": durable.epoch,
                "patch": dict(patch),
                "at": durable.updated_at,
            }
        )
        self.store.save_durable(durable)
        return durable

    # --- snapshot ---

    def create_snapshot(self, *, reason: str = "manual") -> SnapshotMeta:
        durable = self.store.load_durable()
        wal_offset = self.store.wal_len()
        snap_id = self.store._next_snap_id()
        meta = self.store.write_snapshot_files(
            snap_id,
            durable,
            wal_offset,
            reason=reason,
            created_at=_utcnow(),
        )
        durable.last_snapshot_id = snap_id
        durable.updated_at = _utcnow()
        self.store.save_durable(durable)
        self.store.set_last_good(snap_id)
        # successful snapshot clears abort if prior abort was resolved via restore
        return meta

    def list_snapshots(self) -> list[SnapshotMeta]:
        out: list[SnapshotMeta] = []
        for sid in self.store.list_snapshot_ids():
            out.append(self.store.load_snapshot_meta(sid))
        return out

    def verify_snapshot(self, snapshot_id: str) -> bool:
        return self.store.verify_snapshot(snapshot_id)

    # --- restore ---

    def restore(
        self,
        snapshot_id: str | None = None,
        *,
        mode: str = "local",
        clear_wal_after: bool = True,
    ) -> RestoreResult:
        """Restore durable state from a verified snapshot (fail-closed)."""
        require_no_plaintext(mode)
        sid = snapshot_id or self.store.last_good_snapshot
        if not sid:
            self.store.enter_abort_restore("no snapshot available for restore")
            raise RecoveryMissingSnapshot(
                "no snapshot_id and no last_good_snapshot",
                code="RECOVERY_MISSING_SNAPSHOT",
            )
        try:
            self.store.verify_snapshot(sid)
        except RecoveryTamper as exc:
            self.store.enter_abort_restore(f"tamper on restore: {sid}")
            return RestoreResult(
                ok=False,
                snapshot_id=sid,
                abort_restore=True,
                error=str(exc),
                error_code=exc.code,
            )
        except RecoveryMissingSnapshot as exc:
            self.store.enter_abort_restore(f"missing snapshot on restore: {sid}")
            return RestoreResult(
                ok=False,
                snapshot_id=sid,
                abort_restore=True,
                error=str(exc),
                error_code=exc.code,
            )

        meta = self.store.load_snapshot_meta(sid)
        state = self.store.load_snapshot_state(sid)
        state.last_snapshot_id = sid
        state.updated_at = _utcnow()
        self.store.save_durable(state)
        if clear_wal_after:
            # Keep WAL up to snapshot offset; drop divergent tail.
            self.store.truncate_wal_after(meta.wal_offset)
        self.store.set_last_good(sid)
        self.store.clear_abort_restore()
        return RestoreResult(
            ok=True,
            snapshot_id=sid,
            content_hash=meta.content_hash,
            restored_seq=state.seq,
            abort_restore=False,
        )

    # --- rebuild ---

    def rebuild(
        self,
        *,
        snapshot_id: str | None = None,
        mode: str = "local",
    ) -> RebuildResult:
        """Rebuild durable state from last good snapshot + WAL replay.

        On failure: ABORT→snapshot restore (not silent continue).
        """
        require_no_plaintext(mode)
        sid = snapshot_id or self.store.last_good_snapshot
        if not sid:
            self.store.enter_abort_restore("rebuild: no last good snapshot")
            raise RecoveryMissingSnapshot(
                "rebuild requires a last good snapshot",
                code="RECOVERY_MISSING_SNAPSHOT",
            )
        try:
            self.store.verify_snapshot(sid)
        except (RecoveryTamper, RecoveryMissingSnapshot) as exc:
            # ABORT→try alternate last_good if different, else enter abort
            return self._abort_restore_path(
                preferred=sid,
                error=str(exc),
                error_code=getattr(exc, "code", "RECOVERY_ERROR"),
            )

        meta = self.store.load_snapshot_meta(sid)
        base = self.store.load_snapshot_state(sid)
        entries = self.store.read_wal(after_offset=meta.wal_offset)
        try:
            for entry in entries:
                op = entry.get("op")
                if op == "apply":
                    patch = entry.get("patch") or {}
                    base.seq = int(entry.get("seq") or (base.seq + 1))
                    base.epoch = int(entry.get("epoch") or base.epoch)
                    base.payload = {**base.payload, **dict(patch)}
                else:
                    raise RecoveryRebuildFailed(
                        f"unknown WAL op: {op!r}",
                        code="RECOVERY_REBUILD_FAILED",
                    )
            base.last_snapshot_id = sid
            base.updated_at = _utcnow()
            self.store.save_durable(base)
            self.store.set_last_good(sid)
            self.store.clear_abort_restore()
            return RebuildResult(
                ok=True,
                snapshot_id=sid,
                wal_replayed=len(entries),
                final_seq=base.seq,
                abort_restore=False,
            )
        except RecoveryError as exc:
            return self._abort_restore_path(
                preferred=sid,
                error=str(exc),
                error_code=getattr(exc, "code", "RECOVERY_REBUILD_FAILED"),
            )
        except Exception as exc:  # noqa: BLE001 — fail-closed
            return self._abort_restore_path(
                preferred=sid,
                error=f"rebuild crashed: {exc}",
                error_code="RECOVERY_REBUILD_FAILED",
            )

    def _abort_restore_path(
        self,
        *,
        preferred: str,
        error: str,
        error_code: str,
    ) -> RebuildResult:
        """ABORT→snapshot restore: do not silent-continue; restore last good."""
        self.store.enter_abort_restore(error)
        # Prefer last_good if preferred itself is bad.
        candidates: list[str] = []
        last_good = self.store.last_good_snapshot
        if last_good and last_good != preferred:
            candidates.append(last_good)
        # any other verified snapshot, newest first
        for sid in reversed(self.store.list_snapshot_ids()):
            if sid not in candidates and sid != preferred:
                candidates.append(sid)
        # try preferred last only if we have no alternative (may still fail)
        if not candidates:
            candidates = [preferred]

        restored_sid = ""
        for sid in candidates:
            try:
                self.store.verify_snapshot(sid)
                state = self.store.load_snapshot_state(sid)
                meta = self.store.load_snapshot_meta(sid)
                state.last_snapshot_id = sid
                state.updated_at = _utcnow()
                self.store.save_durable(state)
                self.store.truncate_wal_after(meta.wal_offset)
                self.store.set_last_good(sid)
                restored_sid = sid
                break
            except (RecoveryTamper, RecoveryMissingSnapshot, OSError):
                continue

        if restored_sid:
            # Still in abort_restore until operator acknowledges, but state restored.
            return RebuildResult(
                ok=True,
                snapshot_id=restored_sid,
                wal_replayed=0,
                final_seq=self.store.load_durable().seq,
                abort_restore=True,
                error=error,
                error_code=error_code,
            )

        raise RecoveryAbortRestore(
            f"ABORT→snapshot restore failed; no usable snapshot ({error})",
            code="RECOVERY_ABORT_RESTORE",
        )

    def acknowledge_abort(self) -> dict[str, Any]:
        """Clear abort_restore after operator confirms restored state."""
        return self.store.clear_abort_restore()


__all__ = ["RecoveryService", "require_no_plaintext"]
