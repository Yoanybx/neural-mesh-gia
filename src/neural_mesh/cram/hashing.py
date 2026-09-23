"""Content-addressable hashing helpers for C-RAM."""

from __future__ import annotations

import hashlib
import json
from typing import Any, Iterable


def content_hash(content: bytes) -> str:
    """SHA-256 hex digest of raw content bytes."""
    if not isinstance(content, (bytes, bytearray)):
        raise TypeError("content must be bytes")
    return hashlib.sha256(bytes(content)).hexdigest()


def canonical_json_bytes(data: Any) -> bytes:
    """Deterministic JSON encoding for metadata / root digests."""
    return json.dumps(
        data, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")


def metadata_hash(metadata: dict[str, Any] | None) -> str:
    """Hash of canonical metadata (empty dict if None)."""
    return content_hash(canonical_json_bytes(metadata or {}))


def shard_dirs(key: str) -> tuple[str, str]:
    """Return (shard2, remainder) for on-disk layout `.cram/<aa>/<rest>`.

    Example: key a91f82... → ('a9', '1f82...')
    """
    if len(key) < 3:
        raise ValueError(f"cram key too short for sharding: {key!r}")
    return key[:2], key[2:]


def root_hash(keys: Iterable[str]) -> str:
    """Deterministic root hash over a set of C-RAM object keys.

    Sorted unique keys → newline-joined → SHA-256. Empty set → well-known empty hash.
    """
    ordered = sorted(set(str(k) for k in keys))
    if not ordered:
        return content_hash(b"")
    payload = "\n".join(ordered).encode("utf-8")
    return content_hash(payload)
