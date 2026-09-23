"""N=2 active-passive replication over Network Fabric mTLS (Cycle 12 Phase 5A)."""

from __future__ import annotations

import json
import threading
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from neural_mesh.network.endpoint import ExecutionEndpoint
from neural_mesh.network.errors import FabricError, PlaintextForbidden
from neural_mesh.network.protocol import FabricMessage, MessageType, make_ack, make_error
from neural_mesh.network.session import NodeEndpoint, NodeSession
from neural_mesh.network.tls import NodeCertPaths
from neural_mesh.network.transport import TransportMode
from neural_mesh.network.witness import PrimaryWitness

from ..hashing import content_hash
from ..observability import TraceStore
from ..remote_protocol import (
    ReplicaRole,
    b64decode,
    b64encode,
    make_promote_request,
    make_replica_ack,
    make_replica_append,
    make_role_status,
)
from ..store import CRAMStore


@dataclass
class ReplicaNodeState:
    node_id: str
    role: ReplicaRole = ReplicaRole.UNKNOWN
    epoch: int = 0
    writable: bool = False
    object_epochs: dict[str, int] = field(default_factory=dict)
    object_versions: dict[str, int] = field(default_factory=dict)


class FabricReplicaNode:
    """One side of an N=2 pair: PRIMARY (writable) or STANDBY (reject writes)."""

    def __init__(
        self,
        node_id: str,
        role: ReplicaRole | str,
        cert_paths: NodeCertPaths,
        *,
        cram_root: str | Path,
        host: str = "127.0.0.1",
        port: int = 0,
        witness: PrimaryWitness | None = None,
        peer_id: str | None = None,
        peer_endpoint: NodeEndpoint | None = None,
        tls_required: bool = True,
        enabled: bool = True,
    ):
        self.node_id = str(node_id)
        self.role = ReplicaRole(role) if not isinstance(role, ReplicaRole) else role
        self.cert_paths = cert_paths
        self.cram_root = Path(cram_root)
        self.store = CRAMStore(self.cram_root)
        self.traces = TraceStore(self.cram_root)
        self.witness = witness or PrimaryWitness(
            self.cram_root / ".cram" / "witness.json"
        )
        self.peer_id = peer_id
        self.peer_endpoint = peer_endpoint
        self.tls_required = bool(tls_required)
        self.enabled = bool(enabled)
        self.epoch = 0
        self.state = ReplicaNodeState(
            node_id=self.node_id,
            role=self.role,
            epoch=0,
            writable=self.role == ReplicaRole.PRIMARY,
        )
        self._lock = threading.RLock()
        self._partitioned = False
        self.dual_primary_events = 0
        self.rejected_writes = 0
        self.rejected_stale = 0
        self.rejected_hash = 0
        self.last_error: str | None = None
        self._peer_session: NodeSession | None = None
        self._endpoint: ExecutionEndpoint | None = None
        self.host = host
        self.port = int(port)

        if self.role == ReplicaRole.PRIMARY:
            self.witness.claim(self.node_id, epoch=self.epoch)

    @property
    def writable_primary(self) -> str | None:
        return self.witness.writable_primary()

    def count_writable(self) -> int:
        with self._lock:
            return 1 if self.state.writable and self.role == ReplicaRole.PRIMARY else 0

    def set_partitioned(self, value: bool) -> None:
        self._partitioned = bool(value)

    def start(self) -> "FabricReplicaNode":
        self._endpoint = ExecutionEndpoint(
            self.node_id,
            self.cert_paths,
            host=self.host,
            port=self.port,
            cram_root=self.cram_root,
            witness=self.witness,
            handler=self.handle_message,
        )
        self._endpoint.start()
        return self

    def stop(self) -> None:
        self._drop_peer_session()
        if self._endpoint is not None:
            self._endpoint.stop()
            self._endpoint = None

    @property
    def bound_port(self) -> int:
        if self._endpoint is None:
            raise RuntimeError("not started")
        return self._endpoint.bound_port

    def as_endpoint(self) -> NodeEndpoint:
        return NodeEndpoint(
            node_id=self.node_id,
            mode=TransportMode.TLS,
            host=self.host,
            port=self.bound_port,
        )

    def handle_message(self, msg: FabricMessage) -> FabricMessage:
        if not self.enabled and msg.type in (
            MessageType.CRAM_PUT,
            MessageType.CRAM_GET,
            MessageType.CRAM_VERIFY,
            MessageType.CRAM_CHECKPOINT,
            MessageType.REPLICA_APPEND,
            MessageType.ROLE_STATUS,
            MessageType.PROMOTE_REQUEST,
        ):
            return make_error(
                from_node=self.node_id,
                to_node=msg.from_node,
                code="PHASE5A_DISABLED",
                message="feature flag OFF — single-node C11 path",
                ref_msg_id=msg.msg_id,
            )
        try:
            if msg.type == MessageType.CRAM_PUT:
                return self._handle_cram_put(msg)
            if msg.type == MessageType.CRAM_GET:
                return self._handle_cram_get(msg)
            if msg.type == MessageType.CRAM_VERIFY:
                return self._handle_cram_verify(msg)
            if msg.type == MessageType.CRAM_CHECKPOINT:
                return self._handle_cram_checkpoint(msg)
            if msg.type == MessageType.REPLICA_APPEND:
                return self._handle_replica_append(msg)
            if msg.type == MessageType.ROLE_STATUS:
                return self._handle_role_status(msg)
            if msg.type == MessageType.PROMOTE_REQUEST:
                return self._handle_promote_request(msg)
            if msg.type == MessageType.HEARTBEAT:
                return make_ack(
                    from_node=self.node_id,
                    to_node=msg.from_node,
                    ref_msg_id=msg.msg_id,
                    extra={"pong": True, "role": self.role.value, "epoch": self.epoch},
                )
            if msg.type == MessageType.STATE_QUERY:
                return FabricMessage(
                    MessageType.STATE_RESPONSE,
                    from_node=self.node_id,
                    to_node=msg.from_node,
                    payload={
                        "node_id": self.node_id,
                        "role": self.role.value,
                        "epoch": self.epoch,
                        "writable_primary": self.writable_primary,
                        "writable": self.state.writable,
                    },
                )
            return make_error(
                from_node=self.node_id,
                to_node=msg.from_node,
                code="UNKNOWN_TYPE",
                message=f"unsupported type {msg.type}",
                ref_msg_id=msg.msg_id,
            )
        except Exception as exc:  # noqa: BLE001
            self.last_error = str(exc)
            return make_error(
                from_node=self.node_id,
                to_node=msg.from_node,
                code="REPLICA_ERROR",
                message=str(exc),
                ref_msg_id=msg.msg_id,
            )

    def _handle_cram_put(self, msg: FabricMessage) -> FabricMessage:
        with self._lock:
            if self.role != ReplicaRole.PRIMARY or not self.state.writable:
                self.rejected_writes += 1
                return make_ack(
                    from_node=self.node_id,
                    to_node=msg.from_node,
                    ref_msg_id=msg.msg_id,
                    ok=False,
                    error="standby rejects writes",
                    extra={"code": "STANDBY_READ_ONLY"},
                )
            if self._partitioned:
                wp = self.writable_primary
                if wp is not None and wp != self.node_id:
                    self.rejected_writes += 1
                    return make_ack(
                        from_node=self.node_id,
                        to_node=msg.from_node,
                        ref_msg_id=msg.msg_id,
                        ok=False,
                        error="partitioned; not writable primary",
                        extra={"code": "PARTITION_FENCED"},
                    )
            content = b64decode(str(msg.payload["content_b64"]))
            epoch = int(msg.payload.get("epoch", 0))
            version = int(msg.payload.get("version", 0))
            meta = dict(msg.payload.get("metadata") or {})
            key = content_hash(content)
            current = self.state.object_epochs.get(key, 0)
            if epoch < current:
                self.rejected_stale += 1
                return make_ack(
                    from_node=self.node_id,
                    to_node=msg.from_node,
                    ref_msg_id=msg.msg_id,
                    ok=False,
                    error="stale epoch",
                    extra={
                        "code": "REJECTED_STALE_EPOCH",
                        "object_hash": key,
                        "epoch": epoch,
                        "current_epoch": current,
                    },
                )
            meta.setdefault("epoch", epoch)
            meta.setdefault("version", version or epoch)
            meta.setdefault("node_id", self.node_id)
            stored = self.store.put(content, metadata=meta)
            if stored != key:
                self.rejected_hash += 1
                return make_ack(
                    from_node=self.node_id,
                    to_node=msg.from_node,
                    ref_msg_id=msg.msg_id,
                    ok=False,
                    error="hash mismatch",
                    extra={"code": "HASH_MISMATCH"},
                )
            self.state.object_epochs[key] = max(current, epoch)
            self.state.object_versions[key] = int(meta["version"])
            return make_ack(
                from_node=self.node_id,
                to_node=msg.from_node,
                ref_msg_id=msg.msg_id,
                extra={
                    "object_hash": key,
                    "content_hash": key,
                    "epoch": self.state.object_epochs[key],
                    "version": self.state.object_versions[key],
                    "node_id": self.node_id,
                    "role": self.role.value,
                },
            )

    def _handle_cram_get(self, msg: FabricMessage) -> FabricMessage:
        key = str(msg.payload.get("object_hash") or "")
        if not self.store.exists(key):
            return make_ack(
                from_node=self.node_id,
                to_node=msg.from_node,
                ref_msg_id=msg.msg_id,
                ok=False,
                error="object missing",
                extra={"code": "CRAM_OBJECT_MISSING", "object_hash": key},
            )
        raw = self.store.get(key)
        return make_ack(
            from_node=self.node_id,
            to_node=msg.from_node,
            ref_msg_id=msg.msg_id,
            extra={
                "object_hash": key,
                "content_b64": b64encode(raw),
                "epoch": self.state.object_epochs.get(key, 0),
                "node_id": self.node_id,
            },
        )

    def _handle_cram_verify(self, msg: FabricMessage) -> FabricMessage:
        key = str(msg.payload.get("object_hash") or "")
        ok = self.store.verify(key)
        return make_ack(
            from_node=self.node_id,
            to_node=msg.from_node,
            ref_msg_id=msg.msg_id,
            ok=ok,
            error=None if ok else "verify failed",
            extra={"verified": ok, "object_hash": key, "node_id": self.node_id},
        )

    def _handle_cram_checkpoint(self, msg: FabricMessage) -> FabricMessage:
        notice = dict(msg.payload.get("notice") or {})
        notice.setdefault("node_id", self.node_id)
        notice.setdefault("role", self.role.value)
        notice.setdefault("epoch", self.epoch)
        raw = json.dumps(notice, sort_keys=True, separators=(",", ":")).encode("utf-8")
        key = self.store.put(
            raw,
            metadata={
                "kind": "remote_checkpoint_notice",
                "op_id": str(msg.payload.get("op_id") or ""),
            },
        )
        return make_ack(
            from_node=self.node_id,
            to_node=msg.from_node,
            ref_msg_id=msg.msg_id,
            extra={
                "object_hash": key,
                "checkpoint_hash": key,
                "node_id": self.node_id,
            },
        )

    def _handle_replica_append(self, msg: FabricMessage) -> FabricMessage:
        with self._lock:
            key = str(msg.payload.get("object_hash") or "")
            epoch = int(msg.payload.get("epoch", 0))
            version = int(msg.payload.get("version", 0))
            content = b64decode(str(msg.payload["content_b64"]))
            actual = content_hash(content)
            if key and actual != key:
                self.rejected_hash += 1
                return make_replica_ack(
                    from_node=self.node_id,
                    to_node=msg.from_node,
                    ref_msg_id=msg.msg_id,
                    ok=False,
                    object_hash=key,
                    epoch=epoch,
                    error="hash mismatch",
                    code="HASH_MISMATCH",
                )
            key = actual
            current = self.state.object_epochs.get(key, 0)
            if epoch < current:
                self.rejected_stale += 1
                return make_replica_ack(
                    from_node=self.node_id,
                    to_node=msg.from_node,
                    ref_msg_id=msg.msg_id,
                    ok=False,
                    object_hash=key,
                    epoch=epoch,
                    error="stale epoch",
                    code="REJECTED_STALE_EPOCH",
                )
            meta = dict(msg.payload.get("metadata") or {})
            meta.setdefault("epoch", epoch)
            meta.setdefault("version", version or epoch)
            meta.setdefault("replicated_from", msg.from_node)
            self.store.put(content, metadata=meta)
            self.state.object_epochs[key] = max(current, epoch)
            self.state.object_versions[key] = int(meta["version"])
            return make_replica_ack(
                from_node=self.node_id,
                to_node=msg.from_node,
                ref_msg_id=msg.msg_id,
                ok=True,
                object_hash=key,
                epoch=self.state.object_epochs[key],
            )

    def _handle_role_status(self, msg: FabricMessage) -> FabricMessage:
        return make_role_status(
            from_node=self.node_id,
            to_node=msg.from_node,
            role=self.role,
            epoch=self.epoch,
            writable_primary=self.writable_primary,
        )

    def _handle_promote_request(self, msg: FabricMessage) -> FabricMessage:
        """Controlled promote with fencing — never creates dual-primary."""
        with self._lock:
            target = str(msg.payload.get("target_node") or self.node_id)
            object_hash = str(msg.payload.get("object_hash") or "")
            req_epoch = int(msg.payload.get("epoch", 0))

            if target != self.node_id:
                return make_ack(
                    from_node=self.node_id,
                    to_node=msg.from_node,
                    ref_msg_id=msg.msg_id,
                    ok=False,
                    error="promote target mismatch",
                    extra={"code": "PROMOTE_TARGET_MISMATCH"},
                )

            claimed = self.witness.claim(
                self.node_id, epoch=max(self.epoch, req_epoch) + 1
            )
            if not claimed:
                return make_ack(
                    from_node=self.node_id,
                    to_node=msg.from_node,
                    ref_msg_id=msg.msg_id,
                    ok=False,
                    error="promote refused; witness held elsewhere",
                    extra={
                        "code": "PROMOTE_REFUSED",
                        "writable_primary": self.writable_primary,
                        "dual_primary": 0,
                    },
                )

            old_role = self.role
            self.role = ReplicaRole.PRIMARY
            self.state.role = ReplicaRole.PRIMARY
            self.state.writable = True
            self.epoch = max(self.epoch, req_epoch) + 1
            self.state.epoch = self.epoch
            if object_hash:
                self.state.object_epochs[object_hash] = self.epoch
                self.state.object_versions[object_hash] = self.epoch

            if self.witness.count_writable() > 1:
                self.dual_primary_events += 1
                self.witness.release(self.node_id)
                self.role = old_role
                self.state.role = old_role
                self.state.writable = old_role == ReplicaRole.PRIMARY
                return make_ack(
                    from_node=self.node_id,
                    to_node=msg.from_node,
                    ref_msg_id=msg.msg_id,
                    ok=False,
                    error="dual-primary prevented",
                    extra={"code": "DUAL_PRIMARY_PREVENTED", "dual_primary": 0},
                )

            return make_ack(
                from_node=self.node_id,
                to_node=msg.from_node,
                ref_msg_id=msg.msg_id,
                extra={
                    "promoted": True,
                    "role": self.role.value,
                    "epoch": self.epoch,
                    "writable_primary": self.node_id,
                    "dual_primary": 0,
                    "object_hash": object_hash or None,
                },
            )


    def _get_peer_session(self) -> "NodeSession":
        """Reuse a persistent mTLS session to the peer (C11-style hot path)."""
        if self._peer_session is not None and getattr(self._peer_session, "connected", False):
            return self._peer_session
        self._drop_peer_session()
        if self.peer_endpoint is None:
            raise FabricError("no peer endpoint")
        session = NodeSession(
            self.node_id,
            cert_paths=self.cert_paths,
            tls_required=self.tls_required,
        )
        session.connect(self.peer_endpoint)
        self._peer_session = session
        return session

    def _drop_peer_session(self) -> None:
        if self._peer_session is not None:
            try:
                self._peer_session.close()
            except Exception:
                pass
            self._peer_session = None

    def put_and_replicate(
        self,
        content: bytes,
        *,
        metadata: dict[str, Any] | None = None,
        op_id: str | None = None,
        trace_id: str | None = None,
    ) -> dict[str, Any]:
        if self.role != ReplicaRole.PRIMARY or not self.state.writable:
            self.rejected_writes += 1
            raise PermissionError("standby rejects writes")
        if self.tls_required and self.peer_endpoint is not None:
            if self.peer_endpoint.mode != TransportMode.TLS:
                raise PlaintextForbidden("replica path requires TLS")

        op_id = op_id or uuid.uuid4().hex
        trace_id = trace_id or op_id
        tr = self.traces.begin(
            "put_and_replicate",
            operation_id=op_id,
            trace_id=trace_id,
            node_path=[self.node_id] + ([self.peer_id] if self.peer_id else []),
        )
        self.traces.add_span(tr, "Task", detail="put_and_replicate", node_id=self.node_id)
        self.traces.add_span(tr, "Router", detail="primary-local")
        t0 = time.perf_counter()
        meta = dict(metadata or {})
        meta.setdefault("epoch", self.epoch)
        meta.setdefault("version", self.epoch)
        meta.setdefault("node_id", self.node_id)
        key = self.store.put(content, metadata=meta)
        self.state.object_epochs[key] = self.epoch
        self.state.object_versions[key] = self.epoch
        local_ms = (time.perf_counter() - t0) * 1000.0
        self.traces.add_span(
            tr,
            "C-RAM",
            detail=f"local put {key[:12]}",
            latency_ms=local_ms,
            node_id=self.node_id,
        )

        replica_ok = None
        replica_ms = 0.0
        if self.peer_endpoint is not None and not self._partitioned:
            self.traces.add_span(
                tr, "Network", detail="REPLICA_APPEND", node_id=self.peer_id
            )
            t1 = time.perf_counter()
            try:
                session = self._get_peer_session()
                msg = make_replica_append(
                    from_node=self.node_id,
                    to_node=self.peer_id or self.peer_endpoint.node_id,
                    content=content,
                    object_hash=key,
                    epoch=self.epoch,
                    version=self.epoch,
                    metadata=meta,
                    op_id=op_id,
                    trace_id=trace_id,
                    operation_id=op_id,
                )
                resp = session.request(msg)
                replica_ok = resp.type in (
                    MessageType.REPLICA_ACK,
                    MessageType.ACK,
                ) and bool(resp.payload.get("ok", True))
            except FabricError as exc:
                replica_ok = False
                self.last_error = str(exc)
                self._drop_peer_session()
            finally:
                replica_ms = (time.perf_counter() - t1) * 1000.0
            self.traces.add_span(
                tr,
                "Network",
                detail=f"replica_ok={replica_ok}",
                latency_ms=replica_ms,
                result="OK" if replica_ok else "FAIL",
                node_id=self.peer_id,
            )
        else:
            self.traces.add_span(
                tr, "Network", detail="no peer or partitioned", result="N/A"
            )

        self.traces.add_span(tr, "Checkpoint", detail="n/a", result="N/A")
        self.traces.commit(tr, result="OK" if replica_ok is not False else "PARTIAL")
        return {
            "object_hash": key,
            "epoch": self.epoch,
            "replica_ok": replica_ok,
            "local_ms": local_ms,
            "replica_ms": replica_ms,
            "operation_id": op_id,
            "dual_primary": 0,
        }

    def promote_self(self, object_hash: str = "") -> dict[str, Any]:
        fake = FabricMessage(
            MessageType.PROMOTE_REQUEST,
            from_node=self.node_id,
            to_node=self.node_id,
            payload={
                "object_hash": object_hash,
                "epoch": self.epoch,
                "target_node": self.node_id,
            },
        )
        resp = self._handle_promote_request(fake)
        return dict(resp.payload)

    def demote_to_standby(self) -> None:
        with self._lock:
            self.role = ReplicaRole.STANDBY
            self.state.role = ReplicaRole.STANDBY
            self.state.writable = False
            if self.writable_primary == self.node_id:
                self.witness.release(self.node_id)

    def checkpoint_after_recovery(
        self, notice: dict[str, Any] | None = None
    ) -> str:
        payload = dict(notice or {})
        payload.setdefault("kind", "recovery_checkpoint")
        payload.setdefault("node_id", self.node_id)
        payload.setdefault("role", self.role.value)
        payload.setdefault("epoch", self.epoch)
        payload.setdefault("ts_ms", int(time.time() * 1000))
        raw = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
        return self.store.put(raw, metadata={"kind": "recovery_checkpoint"})


class FabricReplicaPair:
    """Convenience: PRIMARY + STANDBY with shared witness."""

    def __init__(
        self,
        work: str | Path,
        ca_leaves: dict[str, NodeCertPaths],
        *,
        primary_id: str = "node-01",
        standby_id: str = "node-02",
        enabled: bool = True,
    ):
        self.work = Path(work)
        self.witness = PrimaryWitness(self.work / "witness.json")
        self.primary = FabricReplicaNode(
            primary_id,
            ReplicaRole.PRIMARY,
            ca_leaves[primary_id],
            cram_root=self.work / f"cram-{primary_id}",
            witness=self.witness,
            peer_id=standby_id,
            enabled=enabled,
        )
        self.standby = FabricReplicaNode(
            standby_id,
            ReplicaRole.STANDBY,
            ca_leaves[standby_id],
            cram_root=self.work / f"cram-{standby_id}",
            witness=self.witness,
            peer_id=primary_id,
            enabled=enabled,
        )

    def start(self) -> "FabricReplicaPair":
        self.primary.start()
        self.standby.start()
        self.primary.peer_endpoint = self.standby.as_endpoint()
        self.standby.peer_endpoint = self.primary.as_endpoint()
        time.sleep(0.05)
        return self

    def stop(self) -> None:
        self.primary.stop()
        self.standby.stop()

    def dual_primary_count(self) -> int:
        return self.witness.count_writable()


__all__ = [
    "FabricReplicaNode",
    "FabricReplicaPair",
    "ReplicaNodeState",
]
