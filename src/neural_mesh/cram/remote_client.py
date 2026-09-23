"""Remote C-RAM client over Network Fabric mTLS (Cycle 12)."""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass
from typing import Any

from neural_mesh.network.errors import FabricError, PlaintextForbidden
from neural_mesh.network.protocol import FabricMessage, MessageType, make_ack
from neural_mesh.network.session import NodeEndpoint, NodeSession
from neural_mesh.network.tls import NodeCertPaths
from neural_mesh.network.transport import TransportMode

from .errors import CRAMError, ObjectMissing
from .hashing import content_hash
from .remote_protocol import (
    b64decode,
    make_cram_checkpoint,
    make_cram_get,
    make_cram_put,
    make_cram_verify,
)


@dataclass
class RemoteResult:
    ok: bool
    content_hash: str | None = None
    content: bytes | None = None
    verified: bool | None = None
    latency_ms: float = 0.0
    error: str | None = None
    error_code: str | None = None
    response: FabricMessage | None = None
    extras: dict[str, Any] | None = None


class RemoteCRAMClient:
    """put_remote / get_remote / verify_remote / checkpoint_remote via mTLS."""

    def __init__(
        self,
        local_node_id: str,
        cert_paths: NodeCertPaths,
        *,
        tls_required: bool = True,
        endpoints: dict[str, NodeEndpoint] | None = None,
    ):
        self.local_node_id = str(local_node_id)
        self.cert_paths = cert_paths
        self.tls_required = bool(tls_required)
        self.endpoints: dict[str, NodeEndpoint] = dict(endpoints or {})
        self._sessions: dict[str, NodeSession] = {}
        self.persist_sessions: bool = False

    def register(self, endpoint: NodeEndpoint) -> None:
        self.endpoints[endpoint.node_id] = endpoint

    def _session(self) -> NodeSession:
        return NodeSession(
            self.local_node_id,
            cert_paths=self.cert_paths,
            tls_required=self.tls_required,
        )

    def _require_tls_endpoint(self, node_id: str) -> NodeEndpoint:
        ep = self.endpoints.get(node_id)
        if ep is None:
            raise CRAMError(f"no endpoint for {node_id}", code="CRAM_NO_ENDPOINT")
        if self.tls_required and ep.mode != TransportMode.TLS:
            raise PlaintextForbidden(
                f"remote C-RAM refuses mode={ep.mode.value}: TLS required"
            )
        return ep

    def _request(self, node_id: str, msg: FabricMessage) -> tuple[FabricMessage, float]:
        ep = self._require_tls_endpoint(node_id)
        t0 = time.perf_counter()
        if self.persist_sessions:
            session = self._sessions.get(node_id)
            if session is None or not session.connected:
                session = self._session()
                session.connect(ep)
                self._sessions[node_id] = session
            resp = session.request(msg)
            return resp, (time.perf_counter() - t0) * 1000.0
        session = self._session()
        try:
            session.connect(ep)
            resp = session.request(msg)
            return resp, (time.perf_counter() - t0) * 1000.0
        finally:
            session.close()

    def close(self) -> None:
        for s in list(self._sessions.values()):
            try:
                s.close()
            except Exception:
                pass
        self._sessions.clear()

    def put_remote(
        self,
        node_id: str,
        content: bytes,
        *,
        metadata: dict[str, Any] | None = None,
        epoch: int = 0,
        version: int = 0,
        op_id: str | None = None,
        trace_id: str | None = None,
        operation_id: str | None = None,
    ) -> RemoteResult:
        op_id = op_id or uuid.uuid4().hex
        operation_id = operation_id or op_id
        msg = make_cram_put(
            from_node=self.local_node_id,
            to_node=node_id,
            content=content,
            metadata=metadata,
            epoch=epoch,
            version=version,
            op_id=op_id,
            trace_id=trace_id,
            operation_id=operation_id,
        )
        try:
            resp, lat = self._request(node_id, msg)
        except FabricError as exc:
            return RemoteResult(
                ok=False,
                latency_ms=0.0,
                error=str(exc),
                error_code=getattr(exc, "code", "FABRIC_ERROR"),
            )
        ok = resp.type == MessageType.ACK and bool(resp.payload.get("ok", True))
        return RemoteResult(
            ok=ok,
            content_hash=resp.payload.get("object_hash") or resp.payload.get("content_hash"),
            latency_ms=lat,
            error=None if ok else str(resp.payload.get("error") or "nack"),
            error_code=None if ok else resp.payload.get("code"),
            response=resp,
            extras=dict(resp.payload),
        )

    def get_remote(
        self,
        node_id: str,
        content_hash_key: str,
        *,
        op_id: str | None = None,
        trace_id: str | None = None,
        operation_id: str | None = None,
    ) -> RemoteResult:
        op_id = op_id or uuid.uuid4().hex
        operation_id = operation_id or op_id
        msg = make_cram_get(
            from_node=self.local_node_id,
            to_node=node_id,
            content_hash=content_hash_key,
            op_id=op_id,
            trace_id=trace_id,
            operation_id=operation_id,
        )
        try:
            resp, lat = self._request(node_id, msg)
        except FabricError as exc:
            return RemoteResult(
                ok=False,
                latency_ms=0.0,
                error=str(exc),
                error_code=getattr(exc, "code", "FABRIC_ERROR"),
            )
        ok = resp.type == MessageType.ACK and bool(resp.payload.get("ok", True))
        raw = None
        if ok and resp.payload.get("content_b64"):
            raw = b64decode(str(resp.payload["content_b64"]))
            if content_hash(raw) != content_hash_key:
                return RemoteResult(
                    ok=False,
                    latency_ms=lat,
                    error="hash mismatch on get",
                    error_code="HASH_MISMATCH",
                    response=resp,
                )
        elif ok and not resp.payload.get("content_b64"):
            return RemoteResult(
                ok=False,
                latency_ms=lat,
                error="object missing",
                error_code="CRAM_OBJECT_MISSING",
                response=resp,
            )
        return RemoteResult(
            ok=ok,
            content_hash=content_hash_key if ok else None,
            content=raw,
            latency_ms=lat,
            error=None if ok else str(resp.payload.get("error") or "nack"),
            error_code=None if ok else resp.payload.get("code"),
            response=resp,
            extras=dict(resp.payload),
        )

    def verify_remote(
        self,
        node_id: str,
        content_hash_key: str,
        *,
        op_id: str | None = None,
        trace_id: str | None = None,
        operation_id: str | None = None,
    ) -> RemoteResult:
        op_id = op_id or uuid.uuid4().hex
        operation_id = operation_id or op_id
        msg = make_cram_verify(
            from_node=self.local_node_id,
            to_node=node_id,
            content_hash=content_hash_key,
            op_id=op_id,
            trace_id=trace_id,
            operation_id=operation_id,
        )
        try:
            resp, lat = self._request(node_id, msg)
        except FabricError as exc:
            return RemoteResult(
                ok=False,
                latency_ms=0.0,
                error=str(exc),
                error_code=getattr(exc, "code", "FABRIC_ERROR"),
            )
        ok = resp.type == MessageType.ACK and bool(resp.payload.get("ok", True))
        verified = bool(resp.payload.get("verified")) if ok else False
        return RemoteResult(
            ok=ok and verified,
            content_hash=content_hash_key,
            verified=verified,
            latency_ms=lat,
            error=None if (ok and verified) else str(resp.payload.get("error") or "unverified"),
            error_code=None if (ok and verified) else resp.payload.get("code") or "VERIFY_FAIL",
            response=resp,
            extras=dict(resp.payload),
        )

    def checkpoint_remote(
        self,
        node_id: str,
        notice: dict[str, Any],
        *,
        op_id: str | None = None,
        trace_id: str | None = None,
        operation_id: str | None = None,
    ) -> RemoteResult:
        op_id = op_id or uuid.uuid4().hex
        operation_id = operation_id or op_id
        msg = make_cram_checkpoint(
            from_node=self.local_node_id,
            to_node=node_id,
            notice=notice,
            op_id=op_id,
            trace_id=trace_id,
            operation_id=operation_id,
        )
        try:
            resp, lat = self._request(node_id, msg)
        except FabricError as exc:
            return RemoteResult(
                ok=False,
                latency_ms=0.0,
                error=str(exc),
                error_code=getattr(exc, "code", "FABRIC_ERROR"),
            )
        ok = resp.type == MessageType.ACK and bool(resp.payload.get("ok", True))
        return RemoteResult(
            ok=ok,
            content_hash=resp.payload.get("object_hash") or resp.payload.get("checkpoint_hash"),
            latency_ms=lat,
            error=None if ok else str(resp.payload.get("error") or "nack"),
            error_code=None if ok else resp.payload.get("code"),
            response=resp,
            extras=dict(resp.payload),
        )


__all__ = ["RemoteCRAMClient", "RemoteResult"]
