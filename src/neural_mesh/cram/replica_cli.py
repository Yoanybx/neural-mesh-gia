"""CLI handlers for ``mesh cram replica …`` (Cycle 6).

Exit codes (frozen Cycle 5 — unchanged):
  0 PASS | 1 generic | 2 corrupt | 3 missing/unavailable
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, TextIO

from neural_mesh.cram.errors import CRAMCorrupt, NodeUnavailable, ObjectMissing
from neural_mesh.cram.replication import ReplicaManager, ReplicaState
from neural_mesh.cram.replication.manager import T_CONV_SECONDS
from neural_mesh.cram.replication.merkle import diff_leaves
from neural_mesh.twin.schema import Topology, TopologyLink, TopologyNode

EXIT_OK = 0
EXIT_GENERIC = 1
EXIT_CORRUPT = 2
EXIT_MISSING = 3


def default_topology(*, seed: int = 42) -> Topology:
    return Topology(
        network_id="cram-replica-cli",
        seed=seed,
        nodes=[
            TopologyNode(id="node-01", cpu=4),
            TopologyNode(id="node-02", cpu=4),
            TopologyNode(id="node-03", cpu=4),
        ],
        links=[
            TopologyLink(source="node-01", target="node-02"),
            TopologyLink(source="node-02", target="node-03"),
        ],
    )


def load_topology(path: str | Path | None, *, seed: int = 42) -> Topology:
    if path is None:
        return default_topology(seed=seed)
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    if hasattr(Topology, "from_dict"):
        return Topology.from_dict(raw)
    return Topology(**{k: raw[k] for k in ("network_id", "seed", "nodes", "links") if k in raw})


def _mgr(root: Path, *, topology: Topology | None = None, seed: int = 42) -> ReplicaManager:
    return ReplicaManager(root, topology or default_topology(seed=seed), seed=seed)


def _status_json(status: dict[str, Any]) -> dict[str, Any]:
    return {
        "object_hash": status.get("object_hash"),
        "primary": status.get("primary"),
        "replica": status.get("replica"),
        "status": status.get("status"),
        "verified": status.get("verified"),
        "epoch": status.get("epoch"),
        "writable_primary": status.get("writable_primary"),
        "failover": status.get("failover"),
        "error": status.get("error"),
    }


def cmd_replica_create(
    object_hash: str | None = None,
    *,
    content: bytes | None = None,
    root: Path,
    topology_path: str | Path | None = None,
    seed: int = 42,
    out: TextIO = sys.stdout,
    err: TextIO = sys.stderr,
) -> int:
    try:
        topo = load_topology(topology_path, seed=seed)
        mgr = _mgr(root, topology=topo, seed=seed)
        if content is not None:
            key = mgr.put_replicated(content, sync=True)
        elif object_hash:
            primary, _ = mgr.placement.replicas(object_hash, topo)
            if not mgr._store(primary).exists(object_hash):
                found = None
                for nid in mgr.node_ids:
                    if mgr._store(nid).exists(object_hash):
                        found = mgr._store(nid).get(object_hash)
                        break
                if found is None:
                    err.write(f"MISSING: {object_hash}\n")
                    return EXIT_MISSING
                mgr._store(primary).put(found)
                mgr._store(primary).bind_to_node(object_hash, primary)
            rec = mgr.create_replica(object_hash)
            rec = mgr.sync_object(object_hash)
            key = object_hash
            if rec.status != ReplicaState.SYNCED:
                err.write(f"ERROR: sync failed: {rec.error}\n")
                return EXIT_GENERIC
        else:
            err.write("ERROR: provide object hash or --put/--file content\n")
            return EXIT_GENERIC
        status = mgr.replica_status(key)
        out.write(json.dumps(_status_json(status), indent=2, sort_keys=True) + "\n")
        return EXIT_OK
    except ObjectMissing as exc:
        err.write(f"MISSING: {exc}\n")
        return EXIT_MISSING
    except CRAMCorrupt as exc:
        err.write(f"CORRUPT: {exc}\n")
        return EXIT_CORRUPT
    except NodeUnavailable as exc:
        err.write(f"UNAVAILABLE: {exc}\n")
        return EXIT_MISSING
    except Exception as exc:  # noqa: BLE001
        err.write(f"ERROR: {exc}\n")
        return EXIT_GENERIC


def cmd_replica_status(
    object_hash: str,
    *,
    root: Path,
    topology_path: str | Path | None = None,
    seed: int = 42,
    out: TextIO = sys.stdout,
    err: TextIO = sys.stderr,
) -> int:
    try:
        topo = load_topology(topology_path, seed=seed)
        mgr = _mgr(root, topology=topo, seed=seed)
        status = mgr.replica_status(object_hash)
        out.write(json.dumps(_status_json(status), indent=2, sort_keys=True) + "\n")
        if status.get("status") == "MISSING":
            err.write(f"MISSING: {object_hash}\n")
            return EXIT_MISSING
        return EXIT_OK
    except Exception as exc:  # noqa: BLE001
        err.write(f"ERROR: {exc}\n")
        return EXIT_GENERIC


def cmd_replica_verify(
    object_hash: str,
    *,
    root: Path,
    topology_path: str | Path | None = None,
    seed: int = 42,
    out: TextIO = sys.stdout,
    err: TextIO = sys.stderr,
) -> int:
    try:
        topo = load_topology(topology_path, seed=seed)
        mgr = _mgr(root, topology=topo, seed=seed)
        result = mgr.verify_replica(object_hash)
        out.write(json.dumps(result, indent=2, sort_keys=True) + "\n")
        if result.get("verified"):
            return EXIT_OK
        if result.get("error") == "no replica record":
            return EXIT_MISSING
        err_s = str(result.get("error", "")).lower()
        code = str(result.get("error_code", ""))
        if "CORRU" in code or "corrupt" in err_s:
            return EXIT_CORRUPT
        return EXIT_CORRUPT
    except ObjectMissing as exc:
        err.write(f"MISSING: {exc}\n")
        return EXIT_MISSING
    except CRAMCorrupt as exc:
        err.write(f"CORRUPT: {exc}\n")
        return EXIT_CORRUPT
    except Exception as exc:  # noqa: BLE001
        err.write(f"ERROR: {exc}\n")
        return EXIT_GENERIC


def cmd_replica_repair(
    object_hash: str,
    *,
    root: Path,
    topology_path: str | Path | None = None,
    seed: int = 42,
    out: TextIO = sys.stdout,
    err: TextIO = sys.stderr,
) -> int:
    try:
        topo = load_topology(topology_path, seed=seed)
        mgr = _mgr(root, topology=topo, seed=seed)
        result = mgr.repair(object_hash)
        out.write(json.dumps(result, indent=2, sort_keys=True) + "\n")
        if result.get("ok") or result.get("converged"):
            return EXIT_OK
        if result.get("error") == "missing":
            return EXIT_MISSING
        return EXIT_GENERIC
    except ObjectMissing as exc:
        err.write(f"MISSING: {exc}\n")
        return EXIT_MISSING
    except CRAMCorrupt as exc:
        err.write(f"CORRUPT: {exc}\n")
        return EXIT_CORRUPT
    except Exception as exc:  # noqa: BLE001
        err.write(f"ERROR: {exc}\n")
        return EXIT_GENERIC


def cmd_replica_promote(
    object_hash: str,
    *,
    root: Path,
    node_id: str | None = None,
    topology_path: str | Path | None = None,
    seed: int = 42,
    out: TextIO = sys.stdout,
    err: TextIO = sys.stderr,
) -> int:
    try:
        topo = load_topology(topology_path, seed=seed)
        mgr = _mgr(root, topology=topo, seed=seed)
        status = mgr.replica_status(object_hash)
        if status.get("status") == "MISSING":
            err.write(f"MISSING: {object_hash}\n")
            return EXIT_MISSING
        # If primary still healthy, mark it lost so promote fencing applies
        primary = status.get("primary")
        if primary and mgr.node_available(primary) and (
            node_id is None or node_id != primary
        ):
            mgr.mark_node_lost(primary)
        result = mgr.promote(object_hash, node_id=node_id)
        out.write(json.dumps(result, indent=2, sort_keys=True) + "\n")
        return EXIT_OK
    except ObjectMissing as exc:
        err.write(f"MISSING: {exc}\n")
        return EXIT_MISSING
    except CRAMCorrupt as exc:
        err.write(f"CORRUPT: {exc}\n")
        return EXIT_CORRUPT
    except NodeUnavailable as exc:
        err.write(f"UNAVAILABLE: {exc}\n")
        return EXIT_MISSING
    except Exception as exc:  # noqa: BLE001
        err.write(f"ERROR: {exc}\n")
        return EXIT_GENERIC


def cmd_replica_verify_consistency(
    object_hash: str,
    *,
    root: Path,
    topology_path: str | Path | None = None,
    seed: int = 42,
    repair: bool = False,
    out: TextIO = sys.stdout,
    err: TextIO = sys.stderr,
) -> int:
    try:
        topo = load_topology(topology_path, seed=seed)
        mgr = _mgr(root, topology=topo, seed=seed)
        if repair:
            result = mgr.anti_entropy_rejoin(object_hash)
        else:
            rec = mgr._registry.get(object_hash)
            if rec is None:
                err.write(f"MISSING: {object_hash}\n")
                return EXIT_MISSING
            a = mgr._leaf_for(rec.writable_primary or rec.primary_node, object_hash)
            b = mgr._leaf_for(rec.replica_node, object_hash)
            reasons = diff_leaves(a, b)
            result = {
                "converged": not reasons,
                "reasons": reasons,
                "t_conv_bound": T_CONV_SECONDS,
                "repaired": False,
                "primary": rec.writable_primary or rec.primary_node,
                "replica": rec.replica_node,
            }
        out.write(json.dumps(result, indent=2, sort_keys=True) + "\n")
        if result.get("converged"):
            return EXIT_OK
        return EXIT_GENERIC
    except ObjectMissing as exc:
        err.write(f"MISSING: {exc}\n")
        return EXIT_MISSING
    except Exception as exc:  # noqa: BLE001
        err.write(f"ERROR: {exc}\n")
        return EXIT_GENERIC
