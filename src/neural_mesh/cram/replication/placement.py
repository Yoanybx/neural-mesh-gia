"""Deterministic N=2 replica placement — primary ≠ secondary."""

from __future__ import annotations

import hashlib
from typing import Any, Sequence

from neural_mesh.twin.placement import CRAMPlacement, _node_ids_from_topology


class ReplicaPlacement:
    """Pick primary via CRAMPlacement; secondary via seeded deterministic offset.

    Rules (Cycle 6 / ChatGPT P1):
    - primary != replica
    - reproducible with the same seed + topology + key
    - no ML / learned placement
    """

    def __init__(self, seed: int = 0):
        self.seed = int(seed)
        self._primary = CRAMPlacement()

    def primary(self, cram_key: str, topology: Any) -> str:
        return self._primary.locate(cram_key, topology)

    def secondary(self, cram_key: str, topology: Any) -> str:
        node_ids = _node_ids_from_topology(topology)
        if len(node_ids) < 2:
            raise ValueError("N=2 replica requires topology with ≥2 nodes")
        prim = self.primary(cram_key, topology)
        others = [n for n in node_ids if n != prim]
        if not others:
            raise ValueError("no eligible secondary distinct from primary")
        material = f"{self.seed}:{cram_key}:{prim}".encode("utf-8")
        digest = hashlib.sha256(material).hexdigest()
        idx = int(digest[:16], 16) % len(others)
        return others[idx]

    def replicas(self, cram_key: str, topology: Any) -> tuple[str, str]:
        p = self.primary(cram_key, topology)
        s = self.secondary(cram_key, topology)
        if p == s:
            raise RuntimeError("invariant violated: primary == secondary")
        return (p, s)

    def eligible_secondary(
        self,
        cram_key: str,
        topology: Any,
        *,
        healthy_nodes: Sequence[str] | None = None,
    ) -> str:
        sec = self.secondary(cram_key, topology)
        if healthy_nodes is None:
            return sec
        healthy = set(healthy_nodes)
        if sec in healthy:
            return sec
        prim = self.primary(cram_key, topology)
        node_ids = _node_ids_from_topology(topology)
        candidates = [n for n in node_ids if n != prim and n in healthy]
        if not candidates:
            raise ValueError("no healthy secondary eligible")
        material = f"{self.seed}:{cram_key}:{prim}:elig".encode("utf-8")
        digest = hashlib.sha256(material).hexdigest()
        idx = int(digest[:16], 16) % len(candidates)
        return candidates[idx]


__all__ = ["ReplicaPlacement"]
