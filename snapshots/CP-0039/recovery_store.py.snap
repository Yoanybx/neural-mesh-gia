"""Filesystem recovery store: durable state, WAL, snapshots.

Layout under ``<data_root>/recovery/``:

  recovery_state.json
  durable/state.json
  wal/wal.jsonl
  snapshots/SNAP-NNNN/{snapshot.json,state.json,content.sha256}
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any

from .models import (
    SCHEMA_ID,
    SCHEMA_STORE,
    DurableState,
    RecoveryError,
    RecoveryMissingSnapshot,
    RecoveryTamper,
    SnapshotMeta,
)


def require_no_plaintext(mode: str | None) -> None:
    """Refuse plaintext / cleartext as a recovery transport claim."""
    if mode is None:
        return
    m = str(mode).strip().lower()
    if m in ("plaintext", "plain", "tcp", "cleartext"):
        from .models import RecoveryPlaintextForbidden

        raise RecoveryPlaintextForbidden(
            f"plaintext mode forbidden for recovery ops: {mode!r}"
        )


class RecoveryStore:
    """Persist durable state, WAL, and content-hashed recovery snapshots."""

    def __init__(self, data_root: str | Path):
        self.data_root = Path(data_root)
        self.root = self.data_root / "recovery"
        self.durable_path = self.root / "durable" / "state.json"
        self.wal_path = self.root / "wal" / "wal.jsonl"
        self.snapshots_dir = self.root / "snapshots"
        self.state_path = self.root / "recovery_state.json"
        self.root.mkdir(parents=True, exist_ok=True)
        (self.root / "durable").mkdir(parents=True, exist_ok=True)
        (self.root / "wal").mkdir(parents=True, exist_ok=True)
        self.snapshots_dir.mkdir(parents=True, exist_ok=True)

    # --- atomic helpers ---

    def _atomic_json(self, path: Path, data: dict[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(path.suffix + ".tmp")
        tmp.write_text(
            json.dumps(data, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        os.replace(tmp, path)

    # --- recovery_state ---

    def _default_state(self) -> dict[str, Any]:
        return {
            "schema": SCHEMA_STORE,
            "abort_restore": False,
            "abort_reason": "",
            "last_good_snapshot": "",
            "dual_primary": 0,
            "vault_acme_required": 0,
            "plaintext_fallback": 0,
        }

    def _read_state(self) -> dict[str, Any]:
        if not self.state_path.is_file():
            return self._default_state()
        data = json.loads(self.state_path.read_text(encoding="utf-8"))
        data["dual_primary"] = 0
        data["vault_acme_required"] = 0
        data["plaintext_fallback"] = 0
        data["schema"] = SCHEMA_STORE
        return data

    def _write_state(self, data: dict[str, Any]) -> None:
        data = dict(data)
        data["schema"] = SCHEMA_STORE
        data["dual_primary"] = 0
        data["vault_acme_required"] = 0
        data["plaintext_fallback"] = 0
        self._atomic_json(self.state_path, data)

    def state(self) -> dict[str, Any]:
        return self._read_state()

    @property
    def abort_restore(self) -> bool:
        return bool(self._read_state().get("abort_restore"))

    @property
    def last_good_snapshot(self) -> str:
        return str(self._read_state().get("last_good_snapshot") or "")

    def enter_abort_restore(self, reason: str) -> dict[str, Any]:
        st = self._read_state()
        st["abort_restore"] = True
        st["abort_reason"] = reason
        self._write_state(st)
        return st

    def clear_abort_restore(self) -> dict[str, Any]:
        st = self._read_state()
        st["abort_restore"] = False
        st["abort_reason"] = ""
        self._write_state(st)
        return st

    def set_last_good(self, snapshot_id: str) -> None:
        st = self._read_state()
        st["last_good_snapshot"] = snapshot_id
        self._write_state(st)

    # --- durable state ---

    def load_durable(self) -> DurableState:
        if not self.durable_path.is_file():
            return DurableState()
        data = json.loads(self.durable_path.read_text(encoding="utf-8"))
        return DurableState.from_dict(data)

    def save_durable(self, state: DurableState) -> None:
        self._atomic_json(self.durable_path, state.to_dict())

    # --- WAL ---

    def wal_len(self) -> int:
        if not self.wal_path.is_file():
            return 0
        n = 0
        with self.wal_path.open("r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    n += 1
        return n

    def append_wal(self, entry: dict[str, Any]) -> int:
        """Append one WAL entry; return new 1-based offset (line count)."""
        self.wal_path.parent.mkdir(parents=True, exist_ok=True)
        rec = dict(entry)
        rec["schema"] = SCHEMA_ID
        rec["dual_primary"] = 0
        line = json.dumps(rec, sort_keys=True) + "\n"
        with self.wal_path.open("a", encoding="utf-8") as f:
            f.write(line)
            f.flush()
            os.fsync(f.fileno())
        return self.wal_len()

    def read_wal(self, after_offset: int = 0) -> list[dict[str, Any]]:
        """Read WAL entries with 1-based offset > after_offset."""
        if not self.wal_path.is_file():
            return []
        out: list[dict[str, Any]] = []
        with self.wal_path.open("r", encoding="utf-8") as f:
            for idx, line in enumerate(f, start=1):
                if idx <= after_offset:
                    continue
                s = line.strip()
                if not s:
                    continue
                out.append(json.loads(s))
        return out

    def truncate_wal_after(self, offset: int) -> None:
        """Keep first ``offset`` WAL lines (1-based); drop the rest."""
        if offset <= 0:
            if self.wal_path.is_file():
                self.wal_path.write_text("", encoding="utf-8")
            return
        if not self.wal_path.is_file():
            return
        lines: list[str] = []
        with self.wal_path.open("r", encoding="utf-8") as f:
            for idx, line in enumerate(f, start=1):
                if idx > offset:
                    break
                lines.append(line if line.endswith("\n") else line + "\n")
        tmp = self.wal_path.with_suffix(".tmp")
        tmp.write_text("".join(lines), encoding="utf-8")
        os.replace(tmp, self.wal_path)

    # --- snapshots ---

    def _next_snap_id(self) -> str:
        existing = list(self.snapshots_dir.glob("SNAP-*"))
        n = 1
        if existing:
            nums = []
            for p in existing:
                parts = p.name.split("-")
                if len(parts) >= 2 and parts[1].isdigit():
                    nums.append(int(parts[1]))
            if nums:
                n = max(nums) + 1
        return f"SNAP-{n:04d}"

    def snapshot_dir(self, snapshot_id: str) -> Path:
        return self.snapshots_dir / snapshot_id

    def list_snapshot_ids(self) -> list[str]:
        ids = []
        for p in sorted(self.snapshots_dir.glob("SNAP-*")):
            if (p / "snapshot.json").is_file():
                ids.append(p.name)
        return ids

    def compute_content_hash(self, state_bytes: bytes, wal_offset: int) -> str:
        h = hashlib.sha256()
        h.update(b"mesh.recovery.snapshot/v1\n")
        h.update(f"wal_offset={wal_offset}\n".encode("utf-8"))
        h.update(state_bytes)
        return h.hexdigest()

    def write_snapshot_files(
        self,
        snapshot_id: str,
        state: DurableState,
        wal_offset: int,
        *,
        reason: str = "",
        created_at: str | None = None,
    ) -> SnapshotMeta:
        folder = self.snapshot_dir(snapshot_id)
        if folder.exists():
            raise RecoveryError(f"snapshot already exists: {snapshot_id}")
        folder.mkdir(parents=True, exist_ok=False)
        state_bytes = (
            json.dumps(state.to_dict(), indent=2, sort_keys=True) + "\n"
        ).encode("utf-8")
        (folder / "state.json").write_bytes(state_bytes)
        content_hash = self.compute_content_hash(state_bytes, wal_offset)
        meta = SnapshotMeta(
            snapshot_id=snapshot_id,
            content_hash=content_hash,
            wal_offset=wal_offset,
            epoch=state.epoch,
            seq=state.seq,
            created_at=created_at,
            reason=reason,
        )
        self._atomic_json(folder / "snapshot.json", meta.to_dict())
        (folder / "content.sha256").write_text(
            f"{content_hash}  state.json\n", encoding="utf-8"
        )
        return meta

    def load_snapshot_meta(self, snapshot_id: str) -> SnapshotMeta:
        folder = self.snapshot_dir(snapshot_id)
        path = folder / "snapshot.json"
        if not path.is_file():
            raise RecoveryMissingSnapshot(f"snapshot not found: {snapshot_id}")
        return SnapshotMeta.from_dict(json.loads(path.read_text(encoding="utf-8")))

    def load_snapshot_state(self, snapshot_id: str) -> DurableState:
        folder = self.snapshot_dir(snapshot_id)
        path = folder / "state.json"
        if not path.is_file():
            raise RecoveryMissingSnapshot(f"snapshot state missing: {snapshot_id}")
        return DurableState.from_dict(json.loads(path.read_text(encoding="utf-8")))

    def verify_snapshot(self, snapshot_id: str) -> bool:
        """Verify content hash; raise RecoveryTamper on mismatch."""
        folder = self.snapshot_dir(snapshot_id)
        meta_path = folder / "snapshot.json"
        state_path = folder / "state.json"
        hash_path = folder / "content.sha256"
        if not meta_path.is_file() or not state_path.is_file() or not hash_path.is_file():
            raise RecoveryMissingSnapshot(f"snapshot incomplete: {snapshot_id}")
        meta = SnapshotMeta.from_dict(json.loads(meta_path.read_text(encoding="utf-8")))
        state_bytes = state_path.read_bytes()
        expected = self.compute_content_hash(state_bytes, meta.wal_offset)
        recorded = hash_path.read_text(encoding="utf-8").split()[0]
        if recorded != expected or meta.content_hash != expected:
            raise RecoveryTamper(
                f"snapshot content hash mismatch: {snapshot_id} "
                f"(recorded={recorded[:16]}… computed={expected[:16]}…)"
            )
        return True


__all__ = ["RecoveryStore", "require_no_plaintext", "RecoveryError"]
