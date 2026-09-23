"""ReplicaManager — controlled in-process N=2 C-RAM replication (Cycle 6)."""

from __future__ import annotations

import json
import time
import uuid
from pathlib import Path
from typing import Any

from neural_mesh.cram.errors import CRAMCorrupt, NodeUnavailable, ObjectMissing
from neural_mesh.cram.hashing import content_hash
from neural_mesh.cram.models import utc_now
from neural_mesh.cram.store import CRAMStore
from neural_mesh.twin.placement import _node_ids_from_topology

from .log import ReplicationLog
from .merkle import ObjectLeaf, diff_leaves
from .models import FailoverStatus, ReplicaRecord, ReplicaState
from .placement import ReplicaPlacement

T_CONV_SECONDS = 5.0
WITNESS_NAME = "witness"


def _new_op_id() -> str:
    return uuid.uuid4().hex


class ReplicaManager:
    """Coordinate primary + secondary node-scoped stores (sandbox, not real net).

    Layout under ``root``::

        nodes/<node_id>/.cram/...
        replication/log.jsonl
        replication/registry.json
    """

    def __init__(self, root: str | Path, topology: Any, *, seed: int = 0):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.topology = topology
        self.seed = int(seed)
        self.placement = ReplicaPlacement(seed=self.seed)
        self.node_ids = list(_node_ids_from_topology(topology))
        if len(self.node_ids) < 2:
            raise ValueError("ReplicaManager requires >=2 topology nodes")

        self.nodes: dict[str, CRAMStore] = {
            nid: CRAMStore(self.root / "nodes" / nid) for nid in self.node_ids
        }

        self._repl_dir = self.root / "replication"
        self._repl_dir.mkdir(parents=True, exist_ok=True)
        self.log = ReplicationLog(self._repl_dir / "log.jsonl")
        self._registry_path = self._repl_dir / "registry.json"
        self._registry: dict[str, ReplicaRecord] = {}
        self._load_registry()

        self._partition: dict[str, int] = {nid: 0 for nid in self.node_ids}
        self._lost: set[str] = set()

    # persistence --------------------------------------------------------------
    def _load_registry(self) -> None:
        if not self._registry_path.exists():
            return
        raw = json.loads(self._registry_path.read_text(encoding="utf-8"))
        for key, rec in raw.items():
            self._registry[key] = ReplicaRecord.from_dict(rec)

    def _save_registry(self) -> None:
        payload = {k: v.to_dict() for k, v in sorted(self._registry.items())}
        self._registry_path.write_text(
            json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8"
        )

    def _store(self, node_id: str) -> CRAMStore:
        if node_id not in self.nodes:
            raise ValueError(f"unknown node {node_id}")
        return self.nodes[node_id]


    def _force_put(self, node_id: str, data: bytes, *, metadata: dict | None = None) -> str:
        """Overwrite even if CAS path already exists (anti-entropy / repair)."""
        key = content_hash(data)
        store = self._store(node_id)
        store._atomic_write(store._object_path(key), data)
        meta = dict(metadata or {})
        from neural_mesh.cram.models import utc_now
        meta.setdefault("stored_at", utc_now())
        store._atomic_write(
            store._meta_path(key),
            __import__("json").dumps(meta, indent=2, sort_keys=True).encode("utf-8"),
        )
        return key


    # node / partition ---------------------------------------------------------
    def node_available(self, node_id: str) -> bool:
        return node_id not in self._lost

    def mark_node_lost(self, node_id: str) -> None:
        self._lost.add(node_id)

    def restore_node(self, node_id: str) -> None:
        self._lost.discard(node_id)

    def set_partition(self, groups: list[list[str]]) -> None:
        self._partition = {nid: 0 for nid in self.node_ids}
        for gid, members in enumerate(groups):
            for nid in members:
                if nid in self._partition:
                    self._partition[nid] = gid

    def clear_partition(self) -> None:
        self._partition = {nid: 0 for nid in self.node_ids}

    def _can_communicate(self, a: str, b: str) -> bool:
        return self._partition.get(a, 0) == self._partition.get(b, 0)

    # witness ------------------------------------------------------------------
    def _witness_path(self, node_id: str) -> Path:
        return self._store(node_id).cram_dir / WITNESS_NAME

    def _write_witness(
        self, node_id: str, *, object_hash: str, epoch: int
    ) -> dict[str, Any]:
        data = {
            "node_id": node_id,
            "object_hash": object_hash,
            "epoch": epoch,
            "promoted_at": utc_now(),
        }
        path = self._witness_path(node_id)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, indent=2, sort_keys=True), encoding="utf-8")
        return data

    def _read_witness(self, node_id: str) -> dict[str, Any] | None:
        path = self._witness_path(node_id)
        if not path.exists():
            return None
        return json.loads(path.read_text(encoding="utf-8"))

    # ChatGPT surface ----------------------------------------------------------
    def create_replica(self, content_hash_key: str) -> ReplicaRecord:
        if content_hash_key in self._registry:
            return self._registry[content_hash_key]

        primary, secondary = self.placement.replicas(content_hash_key, self.topology)
        pstore = self._store(primary)
        if not pstore.exists(content_hash_key):
            raise ObjectMissing(content_hash_key)

        if content_hash_key not in pstore.keys_on_node(primary):
            pstore.bind_to_node(content_hash_key, primary)

        epoch = self.log.current_epoch(content_hash_key)
        rec = ReplicaRecord(
            content_hash=content_hash_key,
            primary_node=primary,
            replica_node=secondary,
            status=ReplicaState.CREATED,
            epoch=epoch,
            version=epoch,
            writable_primary=primary,
        )
        self._registry[content_hash_key] = rec
        self._save_registry()
        return rec

    def sync_object(
        self, content_hash_key: str, *, op_id: str | None = None
    ) -> ReplicaRecord:
        op_id = op_id or _new_op_id()
        rec = self._registry.get(content_hash_key) or self.create_replica(
            content_hash_key
        )
        rec.status = ReplicaState.SYNCING
        rec.error = None
        self._save_registry()

        primary = rec.primary_node
        secondary = rec.replica_node

        if not self.node_available(primary):
            rec.status = ReplicaState.FAILED
            rec.error = f"primary {primary} unavailable"
            self._save_registry()
            return rec
        if not self.node_available(secondary):
            rec.status = ReplicaState.FAILED
            rec.error = f"secondary {secondary} unavailable"
            self._save_registry()
            return rec
        if not self._can_communicate(primary, secondary):
            rec.status = ReplicaState.FAILED
            rec.error = "partition: primary cannot reach secondary"
            self._save_registry()
            return rec

        epoch = self.log.current_epoch(content_hash_key)
        op = self.log.apply(
            op_id=op_id,
            op_type="SYNC",
            content_hash=content_hash_key,
            epoch=epoch,
            node_id=secondary,
        )
        if op.result == "DUPLICATE":
            return self._registry[content_hash_key]
        if op.result == "REJECTED_STALE_EPOCH":
            rec.status = ReplicaState.FAILED
            rec.error = "stale epoch on sync"
            self._save_registry()
            return rec

        try:
            data = self._store(primary).get(content_hash_key)
            if content_hash(data) != content_hash_key:
                raise CRAMCorrupt(content_hash_key)
            sstore = self._store(secondary)
            self._force_put(
                secondary,
                data,
                metadata={
                    "replica_of": primary,
                    "epoch": epoch,
                    "stored_at": utc_now(),
                },
            )
            sstore.bind_to_node(content_hash_key, secondary)
            if not sstore.verify(content_hash_key):
                raise CRAMCorrupt(content_hash_key, message="secondary hash mismatch")
            if content_hash(sstore.get(content_hash_key)) != content_hash_key:
                raise CRAMCorrupt(
                    content_hash_key, message="secondary re-hash mismatch"
                )
        except (ObjectMissing, CRAMCorrupt, OSError, KeyError) as exc:
            rec.status = ReplicaState.FAILED
            rec.verified = False
            rec.error = str(exc)
            self._save_registry()
            return rec

        rec.status = ReplicaState.SYNCED
        rec.verified = True
        rec.epoch = epoch
        rec.version = epoch
        rec.last_op_id = op_id
        rec.error = None
        self._save_registry()
        return rec

    def verify_replica(self, content_hash_key: str) -> dict[str, Any]:
        rec = self._registry.get(content_hash_key)
        if rec is None:
            return {
                "ok": False,
                "verified": False,
                "error": "no replica record",
                "object_hash": content_hash_key,
            }
        primary = rec.primary_node
        secondary = rec.replica_node
        result: dict[str, Any] = {
            "object_hash": content_hash_key,
            "primary": primary,
            "replica": secondary,
            "status": rec.status.value,
            "epoch": rec.epoch,
            "version": rec.version,
        }
        try:
            if not self.node_available(secondary):
                raise NodeUnavailable(
                    f"node {secondary} unavailable", node_id=secondary
                )
            sstore = self._store(secondary)
            sstore.verify_or_raise(content_hash_key)
            p_ok = False
            if self.node_available(primary):
                pstore = self._store(primary)
                p_ok = pstore.exists(content_hash_key) and pstore.verify(
                    content_hash_key
                )
            meta: dict[str, Any] = {}
            try:
                meta = sstore.get_metadata(content_hash_key)
            except ObjectMissing:
                pass
            meta_epoch = int(meta.get("epoch", rec.epoch))
            version_ok = meta_epoch == rec.epoch or rec.status == ReplicaState.SYNCED
            ok = bool(version_ok)
            rec.verified = ok
            result.update(
                {
                    "ok": ok,
                    "verified": ok,
                    "primary_intact": p_ok,
                    "secondary_intact": True,
                    "version_ok": version_ok,
                }
            )
            self._save_registry()
            return result
        except (ObjectMissing, CRAMCorrupt, NodeUnavailable) as exc:
            rec.verified = False
            if rec.status == ReplicaState.SYNCED:
                rec.status = ReplicaState.FAILED
                rec.error = str(exc)
            self._save_registry()
            result.update(
                {
                    "ok": False,
                    "verified": False,
                    "error": str(exc),
                    "error_code": getattr(exc, "code", type(exc).__name__),
                }
            )
            return result

    def remove_replica(self, content_hash_key: str) -> None:
        rec = self._registry.pop(content_hash_key, None)
        self._save_registry()
        if rec is None:
            return
        sstore = self._store(rec.replica_node)
        sstore._node_index.get(rec.replica_node, set()).discard(content_hash_key)

    def replica_status(self, content_hash_key: str) -> dict[str, Any]:
        rec = self._registry.get(content_hash_key)
        if rec is None:
            return {
                "object_hash": content_hash_key,
                "status": "MISSING",
                "verified": False,
            }
        failover = self.check_failover(content_hash_key)
        return {
            "object_hash": content_hash_key,
            "primary": rec.primary_node,
            "replica": rec.replica_node,
            "status": rec.status.value,
            "verified": rec.verified,
            "epoch": rec.epoch,
            "version": rec.version,
            "writable_primary": rec.writable_primary,
            "failover": failover.value,
            "error": rec.error,
        }

    # put path (W=1) -----------------------------------------------------------
    def put_replicated(
        self,
        content: bytes,
        *,
        op_id: str | None = None,
        metadata: dict | None = None,
        sync: bool = True,
    ) -> str:
        if not isinstance(content, (bytes, bytearray)):
            raise TypeError("content must be bytes")
        op_id = op_id or _new_op_id()
        data = bytes(content)
        key = content_hash(data)
        primary, secondary = self.placement.replicas(key, self.topology)

        existing = self._registry.get(key)
        if existing is not None:
            writer = existing.writable_primary or existing.primary_node
            primary = writer
            secondary = existing.replica_node
            if not self._partition_has_authority(primary, key):
                raise NodeUnavailable(
                    f"node {primary} not writable for {key}", node_id=primary
                )

        if not self.node_available(primary):
            raise NodeUnavailable(f"node {primary} unavailable", node_id=primary)

        epoch = self.log.current_epoch(key)
        op = self.log.apply(
            op_id=op_id,
            op_type="PUT",
            content_hash=key,
            epoch=epoch,
            node_id=primary,
            detail={"bytes": len(data)},
        )
        if op.result == "DUPLICATE":
            return key
        if op.result == "REJECTED_STALE_EPOCH":
            raise NodeUnavailable(
                f"stale epoch rejected for {key}", node_id=primary
            )

        store = self._store(primary)
        store.put(data, metadata=metadata)
        store.bind_to_node(key, primary)

        if key not in self._registry:
            self._registry[key] = ReplicaRecord(
                content_hash=key,
                primary_node=primary,
                replica_node=secondary,
                status=ReplicaState.CREATED,
                epoch=self.log.current_epoch(key),
                version=self.log.current_epoch(key),
                writable_primary=primary,
                last_op_id=op_id,
            )
        else:
            rec = self._registry[key]
            rec.last_op_id = op_id
            rec.epoch = self.log.current_epoch(key)
            rec.version = rec.epoch
            if rec.status == ReplicaState.SYNCED:
                rec.status = ReplicaState.CREATED
                rec.verified = False
        self._save_registry()

        if sync:
            self.sync_object(key, op_id=f"{op_id}:sync")
        return key

    # failover / promote -------------------------------------------------------
    def check_failover(self, content_hash_key: str) -> FailoverStatus:
        rec = self._registry.get(content_hash_key)
        if rec is None:
            return FailoverStatus.FAILOVER_BLOCKED
        if self.node_available(rec.primary_node):
            return FailoverStatus.PRIMARY_HEALTHY
        v = self.verify_replica(content_hash_key)
        if v.get("verified") and self.node_available(rec.replica_node):
            return FailoverStatus.FAILOVER_AVAILABLE
        return FailoverStatus.FAILOVER_BLOCKED

    def _partition_has_authority(
        self, node_id: str, content_hash_key: str | None
    ) -> bool:
        """Fail-closed split-brain guard.

        Only the designated writable_primary may write when it is reachable in
        this partition. If the designated primary is partitioned away, the
        minority side is read-only until an explicit promote() with fencing.
        Combined with lex node_id + witness on promote, this guarantees ≤1
        writable primary under any simulated partition.
        """
        if content_hash_key is None:
            return True
        rec = self._registry.get(content_hash_key)
        if rec is None:
            return True
        gid = self._partition.get(node_id, 0)
        peers = [
            n
            for n in self.node_ids
            if self._partition.get(n, 0) == gid and self.node_available(n)
        ]
        if not peers:
            return False
        designated = rec.writable_primary or rec.primary_node
        if designated not in peers:
            # Designated unreachable — fail closed (no writer) until promote.
            return False
        return node_id == designated

    def writable_primaries(self, content_hash_key: str) -> list[str]:
        writers: list[str] = []
        for nid in self.node_ids:
            if not self.node_available(nid):
                continue
            if self._partition_has_authority(nid, content_hash_key):
                writers.append(nid)
        return writers

    def promote(
        self,
        content_hash_key: str,
        *,
        node_id: str | None = None,
        op_id: str | None = None,
    ) -> dict[str, Any]:
        op_id = op_id or _new_op_id()
        rec = self._registry.get(content_hash_key)
        if rec is None:
            raise ObjectMissing(content_hash_key)

        target = node_id or rec.replica_node
        if not self.node_available(target):
            raise NodeUnavailable(f"node {target} unavailable", node_id=target)

        status = self.check_failover(content_hash_key)
        if (
            status == FailoverStatus.FAILOVER_BLOCKED
            and not self.node_available(rec.primary_node)
        ):
            raise CRAMCorrupt(
                content_hash_key,
                message="promote refused: failover blocked (corrupt/unverified)",
            )

        if status == FailoverStatus.PRIMARY_HEALTHY and target == rec.primary_node:
            return {
                "promoted": False,
                "reason": "already_primary",
                "writable_primary": rec.writable_primary,
                "epoch": rec.epoch,
            }

        # Fencing rules:
        # - If designated writable is reachable, only it (or authority) may promote.
        # - If primary is lost and failover is AVAILABLE, the verified replica may
        #   promote (this is the controlled failover path).
        # - Under partition with designated unreachable, refuse unless target wins
        #   lex among live holders (split-brain guard).
        primary_lost = not self.node_available(rec.primary_node)
        failover_ok = status == FailoverStatus.FAILOVER_AVAILABLE
        if primary_lost and failover_ok and target == (rec.replica_node if node_id is None else target):
            pass  # controlled failover promote allowed
        elif not self._partition_has_authority(target, content_hash_key):
            live = [n for n in self.node_ids if self.node_available(n)]
            holders = [n for n in live if self._store(n).exists(content_hash_key)]
            pool = holders or live
            if not pool or target != max(pool):
                raise NodeUnavailable(
                    f"promote refused by tie-breaker for {target}",
                    node_id=target,
                )

        current = self.log.current_epoch(content_hash_key)
        op = self.log.apply(
            op_id=op_id,
            op_type="PROMOTE",
            content_hash=content_hash_key,
            epoch=current,
            node_id=target,
            bump_epoch=True,
            detail={"from": rec.primary_node, "to": target},
        )
        if op.result == "DUPLICATE":
            return {
                "promoted": True,
                "duplicate": True,
                "writable_primary": rec.writable_primary,
                "epoch": rec.epoch,
            }
        if op.result == "REJECTED_STALE_EPOCH":
            raise NodeUnavailable("promote rejected: stale epoch", node_id=target)

        new_epoch = op.epoch
        witness = self._write_witness(
            target, object_hash=content_hash_key, epoch=new_epoch
        )
        old_primary = rec.primary_node
        rec.primary_node = target
        if old_primary != target:
            rec.replica_node = old_primary
        rec.writable_primary = target
        rec.epoch = new_epoch
        rec.version = new_epoch
        rec.last_op_id = op_id
        rec.status = ReplicaState.SYNCED
        rec.verified = True
        self._save_registry()
        return {
            "promoted": True,
            "writable_primary": target,
            "epoch": new_epoch,
            "witness": witness,
            "previous_primary": old_primary,
        }

    # anti-entropy -------------------------------------------------------------
    def _leaf_for(self, node_id: str, content_hash_key: str) -> ObjectLeaf | None:
        store = self._store(node_id)
        if not store.exists(content_hash_key):
            return None
        try:
            raw = store.get(content_hash_key)
            blob = content_hash(raw)
        except Exception:
            return None
        epoch = self.log.current_epoch(content_hash_key)
        rec = self._registry.get(content_hash_key)
        if rec is not None:
            epoch = rec.epoch
        try:
            meta = store.get_metadata(content_hash_key)
            if "epoch" in meta:
                epoch = int(meta["epoch"])
        except Exception:
            pass
        return ObjectLeaf(
            content_hash=content_hash_key,
            epoch=epoch,
            node_id=node_id,
            blob_hash=blob,
        )

    def anti_entropy_rejoin(self, content_hash_key: str) -> dict[str, Any]:
        t0 = time.perf_counter()
        rec = self._registry.get(content_hash_key)
        if rec is None:
            primary, _ = self.placement.replicas(content_hash_key, self.topology)
            if self._store(primary).exists(content_hash_key):
                rec = self.create_replica(content_hash_key)
            else:
                elapsed = time.perf_counter() - t0
                return {
                    "converged": False,
                    "t_conv_seconds": elapsed,
                    "t_conv_bound": T_CONV_SECONDS,
                    "within_bound": elapsed < T_CONV_SECONDS,
                    "reasons": ["missing_record"],
                    "repaired": False,
                }

        self.clear_partition()
        primary = rec.writable_primary or rec.primary_node
        secondary = rec.replica_node
        if primary == secondary:
            others = [
                n for n in self.node_ids if n != primary and self.node_available(n)
            ]
            if others:
                secondary = others[0]
                rec.replica_node = secondary
                self._save_registry()

        a = self._leaf_for(primary, content_hash_key)
        b = self._leaf_for(secondary, content_hash_key)
        reasons = diff_leaves(a, b)
        repaired = False
        if reasons:
            if not self.node_available(primary) or a is None:
                elapsed = time.perf_counter() - t0
                return {
                    "converged": False,
                    "t_conv_seconds": elapsed,
                    "t_conv_bound": T_CONV_SECONDS,
                    "within_bound": elapsed < T_CONV_SECONDS,
                    "reasons": reasons + ["primary_unavailable"],
                    "repaired": False,
                }
            data = self._store(primary).get(content_hash_key)
            epoch = rec.epoch
            self._force_put(
                secondary,
                data,
                metadata={
                    "replica_of": primary,
                    "epoch": epoch,
                    "anti_entropy": True,
                },
            )
            self._store(secondary).bind_to_node(content_hash_key, secondary)
            rec.status = ReplicaState.SYNCED
            rec.verified = True
            rec.error = None
            self._save_registry()
            repaired = True
            b = self._leaf_for(secondary, content_hash_key)
            reasons = diff_leaves(a, b)

        elapsed = time.perf_counter() - t0
        return {
            "converged": not reasons,
            "t_conv_seconds": elapsed,
            "t_conv_bound": T_CONV_SECONDS,
            "within_bound": elapsed < T_CONV_SECONDS,
            "reasons": reasons,
            "repaired": repaired,
            "primary": primary,
            "replica": secondary,
        }

    def repair(self, content_hash_key: str) -> dict[str, Any]:
        rec = self._registry.get(content_hash_key)
        if rec is None:
            try:
                rec = self.create_replica(content_hash_key)
            except ObjectMissing:
                return {
                    "ok": False,
                    "error": "missing",
                    "object_hash": content_hash_key,
                }
        if self.node_available(rec.primary_node) and self.node_available(
            rec.replica_node
        ):
            synced = self.sync_object(content_hash_key, op_id=_new_op_id())
            return {
                "ok": synced.status == ReplicaState.SYNCED,
                "status": synced.status.value,
                "verified": synced.verified,
                "object_hash": content_hash_key,
            }
        return self.anti_entropy_rejoin(content_hash_key)

    def get_from_live(self, content_hash_key: str) -> bytes:
        rec = self._registry.get(content_hash_key)
        order: list[str] = []
        if rec:
            wp = rec.writable_primary or rec.primary_node
            order = [wp, rec.replica_node]
        seen: set[str] = set()
        for nid in order + self.node_ids:
            if nid in seen:
                continue
            seen.add(nid)
            if not self.node_available(nid):
                continue
            store = self._store(nid)
            if store.exists(content_hash_key):
                return store.get(content_hash_key)
        raise ObjectMissing(content_hash_key)


__all__ = ["ReplicaManager", "T_CONV_SECONDS"]
