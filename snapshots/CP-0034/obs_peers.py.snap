"""Richer OBS peers — injection helpers + optional RO fabric probe (CP-0034 / C30).

Extends ``mesh.status.snapshot/v1`` peer ergonomics. Live probe is **opt-in**,
**read-only**, **fail-closed**, and capped at **N≤2**. Never opens Raft,
multi-primary, consensus writes, or plaintext fallback.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping, Sequence

from .network.ops import FabricOps, PeerProbe
from .network.session import NodeEndpoint
from .network.transport import TransportMode
from .status_snapshot import (
    PeerSummary,
    load_peers_json,
    merge_peer_summaries,
    normalize_peer_summaries,
    parse_peers_json,
    peer_summary_from_mapping,
)

# Hard ceiling: OBS peer probe stays inside Phase 5A/5B N=2 (no N>2).
MAX_OBS_PEER_PROBES = 2

__all__ = [
    "MAX_OBS_PEER_PROBES",
    "load_peers_json",
    "merge_peer_summaries",
    "normalize_peer_summaries",
    "parse_peers_json",
    "peer_summary_from_fabric_probe",
    "peer_summary_from_mapping",
    "probe_peer_readonly",
    "probe_peers_readonly",
]


def peer_summary_from_fabric_probe(
    probe: PeerProbe | Mapping[str, Any],
    *,
    source: str = "probed",
) -> PeerSummary:
    """Map a FabricOps ``PeerProbe`` (or dict) into a richer ``PeerSummary``."""
    if isinstance(probe, PeerProbe):
        d = probe.to_dict()
    else:
        d = dict(probe)
    reachable = bool(d.get("reachable"))
    summary: dict[str, Any] = {}
    if d.get("peer_identity") is not None:
        summary["peer_identity"] = d.get("peer_identity")
    if d.get("mode") is not None:
        summary["mode"] = d.get("mode")
    if d.get("plaintext_attempted"):
        summary["plaintext_attempted"] = True
    return PeerSummary(
        node_id=str(d["node_id"]),
        reachable=reachable,
        summary=summary,
        source=source,
        latency_ms=d.get("latency_ms"),
        tls_ok=d.get("tls_ok"),
        heartbeat_ok=d.get("heartbeat_ok"),
        error=d.get("error"),
        error_code=d.get("error_code"),
        host=d.get("host"),
        port=d.get("port"),
        role=None,
    )


def _as_endpoint(peer: NodeEndpoint | Mapping[str, Any] | str, *, default_port: int = 0) -> NodeEndpoint:
    if isinstance(peer, NodeEndpoint):
        return peer
    if isinstance(peer, str):
        return NodeEndpoint(
            node_id=peer,
            mode=TransportMode.TLS,
            host="127.0.0.1",
            port=default_port,
        )
    mode_s = peer.get("mode") or TransportMode.TLS.value
    mode = mode_s if isinstance(mode_s, TransportMode) else TransportMode(str(mode_s))
    return NodeEndpoint(
        node_id=str(peer["node_id"]),
        mode=mode,
        host=str(peer.get("host") or "127.0.0.1"),
        port=int(peer.get("port") or default_port),
        unix_path=peer.get("unix_path"),
    )


def probe_peer_readonly(
    *,
    local_node_id: str,
    peer: NodeEndpoint | Mapping[str, Any] | str,
    fabric_root: str | Path | None = None,
    endpoints_path: str | Path | None = None,
    tls_required: bool = True,
    ops: FabricOps | None = None,
) -> PeerSummary:
    """Single-peer **read-only** TLS heartbeat probe → ``PeerSummary``.

    Fail-closed: uses ``FabricOps`` diagnose/status probe path only (HEARTBEAT).
    Never reconnects with plaintext, never writes under fabric_root, never
    opens Raft / consensus / multi-primary.
    """
    if ops is None:
        if fabric_root is None:
            raise ValueError("fabric_root or ops required for RO peer probe")
        ops = FabricOps.from_fabric_root(
            fabric_root,
            local_node_id,
            tls_required=tls_required,
            endpoints_path=endpoints_path,
        )
    if isinstance(peer, str) and peer in ops.endpoints:
        ep = ops.endpoints[peer]
    else:
        ep = _as_endpoint(peer)
    # Refuse non-TLS when tls_required (FabricOps._probe_peer also enforces).
    probe = ops._probe_peer(ep)  # noqa: SLF001 — intentional RO reuse of status probe
    return peer_summary_from_fabric_probe(probe, source="probed")


def probe_peers_readonly(
    *,
    local_node_id: str,
    peers: Sequence[NodeEndpoint | Mapping[str, Any] | str],
    fabric_root: str | Path | None = None,
    endpoints_path: str | Path | None = None,
    tls_required: bool = True,
    ops: FabricOps | None = None,
) -> list[PeerSummary]:
    """Probe up to ``MAX_OBS_PEER_PROBES`` (2) peers RO; refuses N>2."""
    items = list(peers)
    if len(items) > MAX_OBS_PEER_PROBES:
        raise ValueError(
            f"OBS peer probe refuses N>{MAX_OBS_PEER_PROBES} "
            f"(got {len(items)}); no Raft / multi-primary / N>2"
        )
    if ops is None:
        if fabric_root is None:
            raise ValueError("fabric_root or ops required for RO peer probe")
        ops = FabricOps.from_fabric_root(
            fabric_root,
            local_node_id,
            tls_required=tls_required,
            endpoints_path=endpoints_path,
        )
    out: list[PeerSummary] = []
    for p in items:
        out.append(
            probe_peer_readonly(
                local_node_id=local_node_id,
                peer=p,
                fabric_root=fabric_root,
                endpoints_path=endpoints_path,
                tls_required=tls_required,
                ops=ops,
            )
        )
    return normalize_peer_summaries(out)
