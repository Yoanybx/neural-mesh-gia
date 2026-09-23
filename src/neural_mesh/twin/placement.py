"""Deterministic C-RAM → node locality placement for the Digital Twin sandbox."""

from __future__ import annotations

from typing import Any, Sequence


def _node_ids_from_topology(topology: Any) -> list[str]:
    """Extract sorted node ids from Topology model, DigitalTwin, or dict/list."""
    if topology is None:
        raise ValueError("topology is required")

    # Topology dataclass (schema.Topology)
    if hasattr(topology, "nodes") and not callable(topology.nodes):
        nodes = topology.nodes
        if isinstance(nodes, dict):
            return sorted(str(k) for k in nodes.keys())
        ids: list[str] = []
        for n in nodes:
            if hasattr(n, "id"):
                ids.append(str(n.id))
            elif hasattr(n, "node_id"):
                ids.append(str(n.node_id))
            elif isinstance(n, dict):
                ids.append(str(n.get("id") or n.get("node_id")))
            else:
                ids.append(str(n))
        return sorted(ids)

    # DigitalTwin-like: .nodes is dict[str, TwinNode]
    if hasattr(topology, "nodes") and isinstance(topology.nodes, dict):
        return sorted(str(k) for k in topology.nodes.keys())

    if isinstance(topology, dict):
        if "nodes" in topology:
            return _node_ids_from_topology(type("T", (), {"nodes": topology["nodes"]})())
        return sorted(str(k) for k in topology.keys())

    if isinstance(topology, Sequence) and not isinstance(topology, (str, bytes)):
        return sorted(str(x) for x in topology)

    raise TypeError(f"unsupported topology type: {type(topology)!r}")


class CRAMPlacement:
    """Map a C-RAM content key to a deterministic node id via hash modulo."""

    def locate(self, cram_key: str, topology: Any) -> str:
        if not cram_key or not isinstance(cram_key, str):
            raise ValueError("cram_key must be a non-empty string")
        node_ids = _node_ids_from_topology(topology)
        if not node_ids:
            raise ValueError("topology has no nodes")
        # Use first 16 hex chars as unsigned int for stable assignment.
        hex_prefix = "".join(c for c in cram_key.lower() if c in "0123456789abcdef")
        if len(hex_prefix) < 1:
            raise ValueError(f"cram_key is not hex-like: {cram_key!r}")
        use = hex_prefix[:16] if len(hex_prefix) >= 16 else hex_prefix
        idx = int(use, 16) % len(node_ids)
        return node_ids[idx]
