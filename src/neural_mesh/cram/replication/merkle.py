"""Minimal per-object Merkle leaf / diff for anti-entropy rejoin."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Iterable


def leaf_hash(content_hash: str, epoch: int, node_id: str) -> str:
    material = f"{content_hash}|{epoch}|{node_id}".encode("utf-8")
    return hashlib.sha256(material).hexdigest()


@dataclass(frozen=True)
class ObjectLeaf:
    content_hash: str
    epoch: int
    node_id: str
    blob_hash: str  # should equal content_hash when intact

    @property
    def digest(self) -> str:
        return leaf_hash(self.content_hash, self.epoch, self.node_id)


def merkle_root(leaves: Iterable[ObjectLeaf]) -> str:
    digests = sorted(leaf.digest for leaf in leaves)
    if not digests:
        return hashlib.sha256(b"").hexdigest()
    h = hashlib.sha256()
    for d in digests:
        h.update(d.encode("utf-8"))
    return h.hexdigest()


def diff_leaves(a: ObjectLeaf | None, b: ObjectLeaf | None) -> list[str]:
    """Return list of divergence reasons between two per-object leaves."""
    reasons: list[str] = []
    if a is None and b is None:
        return reasons
    if a is None:
        return ["missing_a"]
    if b is None:
        return ["missing_b"]
    if a.content_hash != b.content_hash:
        reasons.append("content_hash_mismatch")
    if a.epoch != b.epoch:
        reasons.append("epoch_mismatch")
    if a.blob_hash != b.blob_hash:
        reasons.append("blob_hash_mismatch")
    # Note: leaf digest includes node_id, so it differs across nodes by design.
    # Anti-entropy compares content_hash/epoch/blob_hash only.
    return reasons


__all__ = ["ObjectLeaf", "diff_leaves", "leaf_hash", "merkle_root"]
