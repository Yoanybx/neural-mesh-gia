"""Remote C-RAM store facade + Phase 5A feature flag (Cycle 12)."""

from __future__ import annotations

import os
import uuid
from pathlib import Path
from typing import Any

from neural_mesh.network.errors import PlaintextForbidden
from neural_mesh.network.session import NodeEndpoint
from neural_mesh.network.tls import NodeCertPaths
from neural_mesh.network.transport import TransportMode

from .observability import TraceStore
from .remote_client import RemoteCRAMClient, RemoteResult
from .remote_protocol import FEATURE_FLAG_ENV
from .store import CRAMStore


def replication_n2_enabled(env: dict[str, str] | None = None) -> bool:
    """Feature flag: OFF restores C11 single-node behavior."""
    src = env if env is not None else os.environ
    raw = str(src.get(FEATURE_FLAG_ENV, "0")).strip().lower()
    return raw in ("1", "true", "yes", "on")


class RemoteCRAMStore:
    """put_remote/get_remote/verify_remote/checkpoint_remote with tracing.

    When feature flag is OFF, remote methods raise unless ``force=True``.
    Local ``CRAMStore`` remains available always (C11 single-node intact).
    """

    def __init__(
        self,
        root: str | Path,
        *,
        local_node_id: str = "client",
        cert_paths: NodeCertPaths | None = None,
        tls_required: bool = True,
        endpoints: dict[str, NodeEndpoint] | None = None,
        enabled: bool | None = None,
    ):
        self.root = Path(root)
        self.local = CRAMStore(self.root)
        self.traces = TraceStore(self.root)
        self.local_node_id = str(local_node_id)
        self.cert_paths = cert_paths
        self.tls_required = bool(tls_required)
        self.enabled = replication_n2_enabled() if enabled is None else bool(enabled)
        self._client: RemoteCRAMClient | None = None
        if cert_paths is not None:
            self._client = RemoteCRAMClient(
                self.local_node_id,
                cert_paths,
                tls_required=tls_required,
                endpoints=endpoints,
            )

    def register(self, endpoint: NodeEndpoint) -> None:
        if self._client is None:
            raise RuntimeError("cert_paths required for remote client")
        self._client.register(endpoint)

    def _require_remote(self, *, force: bool = False) -> RemoteCRAMClient:
        if not self.enabled and not force:
            raise RuntimeError(
                f"Phase 5A replication disabled ({FEATURE_FLAG_ENV}=OFF); "
                "C11 single-node path active"
            )
        if self._client is None:
            raise RuntimeError("remote client not configured (missing cert_paths)")
        if self.tls_required:
            for ep in self._client.endpoints.values():
                if ep.mode != TransportMode.TLS:
                    raise PlaintextForbidden(
                        "remote C-RAM path requires TLS endpoints"
                    )
        return self._client

    def put_remote(
        self,
        node_id: str,
        content: bytes,
        *,
        metadata: dict[str, Any] | None = None,
        force: bool = False,
        **kw: Any,
    ) -> RemoteResult:
        client = self._require_remote(force=force)
        op_id = kw.get("op_id") or uuid.uuid4().hex
        trace_id = kw.get("trace_id") or op_id
        operation_id = kw.get("operation_id") or op_id
        tr = self.traces.begin(
            "put_remote",
            operation_id=operation_id,
            trace_id=trace_id,
            node_path=[self.local_node_id, node_id],
        )
        self.traces.add_span(tr, "Task", detail="put_remote", node_id=self.local_node_id)
        self.traces.add_span(tr, "Router", detail="direct", result="OK")
        self.traces.add_span(tr, "Network", detail="mTLS", node_id=node_id)
        result = client.put_remote(
            node_id,
            content,
            metadata=metadata,
            op_id=op_id,
            trace_id=trace_id,
            operation_id=operation_id,
            epoch=int(kw.get("epoch", 0)),
            version=int(kw.get("version", 0)),
        )
        self.traces.add_span(
            tr,
            "C-RAM",
            detail=f"put hash={result.content_hash}",
            latency_ms=result.latency_ms,
            result="OK" if result.ok else "FAIL",
            node_id=node_id,
        )
        self.traces.add_span(tr, "Checkpoint", detail="n/a", result="N/A")
        self.traces.commit(tr, result="OK" if result.ok else "FAIL")
        return result

    def get_remote(
        self,
        node_id: str,
        content_hash: str,
        *,
        force: bool = False,
        **kw: Any,
    ) -> RemoteResult:
        client = self._require_remote(force=force)
        op_id = kw.get("op_id") or uuid.uuid4().hex
        trace_id = kw.get("trace_id") or op_id
        operation_id = kw.get("operation_id") or op_id
        tr = self.traces.begin(
            "get_remote",
            operation_id=operation_id,
            trace_id=trace_id,
            node_path=[self.local_node_id, node_id],
        )
        self.traces.add_span(tr, "Task", detail="get_remote")
        self.traces.add_span(tr, "Router", detail="direct")
        self.traces.add_span(tr, "Network", detail="mTLS", node_id=node_id)
        result = client.get_remote(
            node_id,
            content_hash,
            op_id=op_id,
            trace_id=trace_id,
            operation_id=operation_id,
        )
        self.traces.add_span(
            tr,
            "C-RAM",
            detail=f"get {content_hash[:12]}",
            latency_ms=result.latency_ms,
            result="OK" if result.ok else "FAIL",
            node_id=node_id,
        )
        self.traces.add_span(tr, "Checkpoint", detail="n/a", result="N/A")
        self.traces.commit(tr, result="OK" if result.ok else "FAIL")
        return result

    def verify_remote(
        self,
        node_id: str,
        content_hash: str,
        *,
        force: bool = False,
        **kw: Any,
    ) -> RemoteResult:
        client = self._require_remote(force=force)
        op_id = kw.get("op_id") or uuid.uuid4().hex
        operation_id = kw.get("operation_id") or op_id
        return client.verify_remote(
            node_id,
            content_hash,
            op_id=op_id,
            trace_id=kw.get("trace_id") or op_id,
            operation_id=operation_id,
        )

    def checkpoint_remote(
        self,
        node_id: str,
        notice: dict[str, Any],
        *,
        force: bool = False,
        **kw: Any,
    ) -> RemoteResult:
        client = self._require_remote(force=force)
        op_id = kw.get("op_id") or uuid.uuid4().hex
        operation_id = kw.get("operation_id") or op_id
        tr = self.traces.begin(
            "checkpoint_remote",
            operation_id=operation_id,
            trace_id=kw.get("trace_id") or op_id,
            node_path=[self.local_node_id, node_id],
        )
        self.traces.add_span(tr, "Task", detail="checkpoint_remote")
        self.traces.add_span(tr, "Router", detail="direct")
        self.traces.add_span(tr, "Network", detail="mTLS", node_id=node_id)
        result = client.checkpoint_remote(
            node_id,
            notice,
            op_id=op_id,
            trace_id=kw.get("trace_id") or op_id,
            operation_id=operation_id,
        )
        self.traces.add_span(
            tr,
            "C-RAM",
            detail="checkpoint notice",
            latency_ms=result.latency_ms,
            result="OK" if result.ok else "FAIL",
            node_id=node_id,
        )
        self.traces.add_span(
            tr,
            "Checkpoint",
            detail=str(result.content_hash or ""),
            result="OK" if result.ok else "FAIL",
            node_id=node_id,
        )
        self.traces.commit(tr, result="OK" if result.ok else "FAIL")
        return result


__all__ = [
    "FEATURE_FLAG_ENV",
    "RemoteCRAMStore",
    "replication_n2_enabled",
]
