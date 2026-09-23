"""Deterministic, verifiable, recoverable C-RAM content-addressable store."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any

from .errors import CRAMCorrupt, CRAMError, NodeUnavailable, ObjectMissing
from .hashing import content_hash, root_hash, shard_dirs
from .models import CRAMObject, ObjectType, utc_now

# Re-export names expected by Cycle 4 imports
CRAMKeyError = ObjectMissing
CRAMNodeUnavailable = NodeUnavailable


class CRAMStore:
    """On-disk CAS under ``<root>/.cram/<aa>/<rest>`` (+ optional ``.meta.json``).

    Identity is content hash only. Metadata is sidecar and never affects the key.
    Writes use temp-file + fsync + os.replace for crash-safe durability as far as
    the underlying filesystem honors fsync (honest best-effort on this box).
    """

    def __init__(self, root: str | Path):
        self.root = Path(root)
        self.cram_dir = self.root / ".cram"
        self.cram_dir.mkdir(parents=True, exist_ok=True)
        # node_id -> set of keys placed on that node (sandbox locality index)
        self._node_index: dict[str, set[str]] = {}
        # keys that are unreachable via node-local get after NODE_LOSS
        self._lost_nodes: set[str] = set()

    def _object_path(self, key: str) -> Path:
        shard, rest = shard_dirs(key)
        return self.cram_dir / shard / rest

    def _meta_path(self, key: str) -> Path:
        return Path(str(self._object_path(key)) + ".meta.json")

    def _atomic_write(self, path: Path, data: bytes) -> None:
        """Crash-safe write: tmp → fsync file → replace → fsync parent dir."""
        path.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp = tempfile.mkstemp(prefix=".tmp-", dir=path.parent)
        try:
            with os.fdopen(fd, "wb") as f:
                f.write(data)
                f.flush()
                os.fsync(f.fileno())
            os.replace(tmp, path)
            # Best-effort directory fsync so the rename itself is durable.
            try:
                dir_fd = os.open(str(path.parent), os.O_RDONLY)
                try:
                    os.fsync(dir_fd)
                finally:
                    os.close(dir_fd)
            except OSError:
                # Some FSes / platforms disallow directory fsync; content fsync still done.
                pass
        finally:
            if os.path.exists(tmp):
                os.unlink(tmp)

    def put(self, content: bytes, metadata: dict | None = None) -> str:
        """Store content; return content hash (key). Idempotent for same bytes."""
        if not isinstance(content, (bytes, bytearray)):
            raise TypeError("content must be bytes")
        key = content_hash(bytes(content))
        path = self._object_path(key)
        if not path.exists():
            self._atomic_write(path, bytes(content))
        meta = dict(metadata or {})
        meta.setdefault("stored_at", utc_now())
        self._atomic_write(
            self._meta_path(key),
            json.dumps(meta, indent=2, sort_keys=True).encode("utf-8"),
        )
        return key

    def get(self, key: str) -> bytes:
        path = self._object_path(key)
        if not path.exists():
            raise ObjectMissing(key)
        return path.read_bytes()

    def exists(self, key: str) -> bool:
        return self._object_path(key).exists()

    def verify(self, key: str) -> bool:
        """True iff object exists and on-disk bytes re-hash to ``key``."""
        path = self._object_path(key)
        if not path.exists():
            return False
        return content_hash(path.read_bytes()) == key

    def verify_or_raise(self, key: str) -> None:
        """Raise ObjectMissing or CRAMCorrupt; return None if intact."""
        path = self._object_path(key)
        if not path.exists():
            raise ObjectMissing(key)
        if content_hash(path.read_bytes()) != key:
            raise CRAMCorrupt(key)

    def get_metadata(self, key: str) -> dict[str, Any]:
        mp = self._meta_path(key)
        if not mp.exists():
            if not self.exists(key):
                raise ObjectMissing(key)
            return {}
        return json.loads(mp.read_text(encoding="utf-8"))

    def put_object(
        self,
        content: bytes,
        object_type: ObjectType | str,
        *,
        object_id: str | None = None,
        parent_refs: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
        place_on: str | None = None,
    ) -> CRAMObject:
        """Store content and return a typed CRAMObject descriptor."""
        key = self.put(content, metadata=metadata)
        ot = ObjectType(object_type) if not isinstance(object_type, ObjectType) else object_type
        obj = CRAMObject(
            id=object_id or key,
            object_type=ot,
            content_hash=key,
            parent_refs=list(parent_refs or []),
            metadata=dict(metadata or {}),
        )
        desc_path = Path(str(self._object_path(key)) + ".object.json")
        self._atomic_write(
            desc_path,
            json.dumps(obj.to_dict(), indent=2, sort_keys=True).encode("utf-8"),
        )
        if place_on is not None:
            self.bind_to_node(key, place_on)
        return obj

    def bind_to_node(self, key: str, node_id: str) -> None:
        """Record sandbox placement of ``key`` on ``node_id``."""
        if not self.exists(key):
            raise ObjectMissing(key)
        self._node_index.setdefault(node_id, set()).add(key)
        meta = self.get_metadata(key)
        meta["placed_on"] = node_id
        self._atomic_write(
            self._meta_path(key),
            json.dumps(meta, indent=2, sort_keys=True).encode("utf-8"),
        )

    def keys_on_node(self, node_id: str) -> set[str]:
        return set(self._node_index.get(node_id, set()))

    def mark_node_lost(self, node_id: str) -> None:
        """Simulate NODE_LOSS: node-local gets for that node become unavailable."""
        self._lost_nodes.add(node_id)

    def restore_node(self, node_id: str) -> None:
        self._lost_nodes.discard(node_id)

    def node_available(self, node_id: str) -> bool:
        return node_id not in self._lost_nodes

    def get_from_node(self, key: str, node_id: str) -> bytes:
        """Node-local get. Raises NodeUnavailable if node lost; ObjectMissing if not placed there."""
        if node_id in self._lost_nodes:
            raise NodeUnavailable(
                f"node {node_id} unavailable (NODE_LOSS)", node_id=node_id
            )
        if key not in self._node_index.get(node_id, set()):
            raise ObjectMissing(key, message=f"{key} not on node {node_id}")
        return self.get(key)

    def list_keys(self) -> list[str]:
        keys: list[str] = []
        if not self.cram_dir.exists():
            return keys
        for shard in sorted(p for p in self.cram_dir.iterdir() if p.is_dir()):
            for f in sorted(shard.iterdir()):
                if f.is_file() and not f.name.endswith((".meta.json", ".object.json")):
                    keys.append(shard.name + f.name)
        return keys

    def compute_root_hash(self, keys: list[str] | None = None) -> str:
        return root_hash(keys if keys is not None else self.list_keys())

    def fsck(self) -> dict[str, Any]:
        """Filesystem check: verify every blob; report corrupt + orphan sidecars."""
        keys = self.list_keys()
        ok: list[str] = []
        missing: list[str] = []
        corrupt: list[str] = []
        for key in keys:
            if not self.exists(key):
                missing.append(key)
            elif not self.verify(key):
                corrupt.append(key)
            else:
                ok.append(key)

        orphans: list[str] = []
        if self.cram_dir.exists():
            for shard in self.cram_dir.iterdir():
                if not shard.is_dir():
                    continue
                for f in shard.iterdir():
                    if not f.is_file():
                        continue
                    name = f.name
                    if name.endswith(".meta.json"):
                        base = name[: -len(".meta.json")]
                        if not (shard / base).exists():
                            orphans.append(str(f.relative_to(self.cram_dir)))
                    elif name.endswith(".object.json"):
                        base = name[: -len(".object.json")]
                        if not (shard / base).exists():
                            orphans.append(str(f.relative_to(self.cram_dir)))

        status = "OK"
        if corrupt:
            status = "CORRUPT"
        elif missing:
            status = "INCOMPLETE"
        elif orphans:
            status = "ORPHANS"
        return {
            "fsck_schema": 1,
            "status": status,
            "ok": ok,
            "missing": missing,
            "corrupt": corrupt,
            "orphans": orphans,
            "checked": len(keys),
        }

    def recover_from_checkpoint(
        self,
        cram_objects: list[str],
        *,
        expect_root_hash: str | None = None,
    ) -> dict[str, Any]:
        """Verify checkpoint-listed objects are present and intact in durable store.

        Returns a status dict with ``status`` = RECOVERABLE | INCOMPLETE | CORRUPT.

        Note (Cycle 5): this is *durable integrity* recovery (bytes on disk), not
        live placement recovery after NODE_LOSS. For placement semantics use
        ``cram.recovery.recover_after_node_loss`` (ERROR when locate unresolved).
        """
        missing: list[str] = []
        corrupt: list[str] = []
        recovered: list[str] = []
        for key in cram_objects:
            if not self.exists(key):
                missing.append(key)
            elif not self.verify(key):
                corrupt.append(key)
            else:
                recovered.append(key)
        actual_root = root_hash(cram_objects)
        if expect_root_hash is not None and actual_root != expect_root_hash:
            return {
                "status": "CORRUPT",
                "recovered": recovered,
                "missing": missing,
                "corrupt": corrupt,
                "cram_root_hash": actual_root,
                "expected_root_hash": expect_root_hash,
            }
        if missing or corrupt:
            return {
                "status": "INCOMPLETE",
                "recovered": recovered,
                "missing": missing,
                "corrupt": corrupt,
                "cram_root_hash": actual_root,
            }
        return {
            "status": "RECOVERABLE",
            "recovered": recovered,
            "missing": [],
            "corrupt": [],
            "cram_root_hash": actual_root,
        }


__all__ = [
    "CRAMCorrupt",
    "CRAMError",
    "CRAMKeyError",
    "CRAMNodeUnavailable",
    "CRAMStore",
    "NodeUnavailable",
    "ObjectMissing",
]
