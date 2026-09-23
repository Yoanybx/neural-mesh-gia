"""Network Fabric — Router selection → mTLS dispatch → C-RAM checkpoint."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from neural_mesh.cram.store import CRAMStore
from neural_mesh.router.models import RouteDecision, TaskSpec

from .errors import FabricError, InvalidSession
from .protocol import FabricMessage, MessageType
from .session import NodeEndpoint, NodeSession
from .tls import NodeCertPaths
from .transport import TransportMode


@dataclass
class DispatchResult:
    ok: bool
    node_id: str | None
    decision: RouteDecision | None
    response: FabricMessage | None = None
    checkpoint_hash: str | None = None
    error: str | None = None
    error_code: str | None = None
    extras: dict[str, Any] = field(default_factory=dict)


class NetworkFabric:
    """Dispatch accepted RouteDecisions to node endpoints over the fabric."""

    def __init__(
        self,
        local_node_id: str,
        cert_paths: NodeCertPaths,
        *,
        endpoints: dict[str, NodeEndpoint] | None = None,
        cram_root: str | Path | None = None,
        tls_required: bool = True,
    ):
        self.local_node_id = str(local_node_id)
        self.cert_paths = cert_paths
        self.endpoints: dict[str, NodeEndpoint] = dict(endpoints or {})
        self.cram_root = Path(cram_root) if cram_root else None
        self.tls_required = bool(tls_required)

    def register(self, endpoint: NodeEndpoint) -> None:
        self.endpoints[endpoint.node_id] = endpoint

    def dispatch(
        self,
        decision: RouteDecision,
        task: TaskSpec,
        *,
        timeout: float | None = None,  # reserved; session uses transport defaults
    ) -> DispatchResult:
        if decision.status.value != "ACCEPTED" or not decision.selected_node_id:
            return DispatchResult(
                ok=False,
                node_id=decision.selected_node_id,
                decision=decision,
                error="decision not accepted",
                error_code="INVALID_SESSION",
            )
        node_id = decision.selected_node_id
        ep = self.endpoints.get(node_id)
        if ep is None:
            return DispatchResult(
                ok=False,
                node_id=node_id,
                decision=decision,
                error=f"no endpoint for {node_id}",
                error_code="INVALID_SESSION",
            )
        session = NodeSession(
            self.local_node_id,
            cert_paths=self.cert_paths,
            tls_required=self.tls_required,
        )
        try:
            session.connect(ep)
            msg = FabricMessage(
                MessageType.TASK_REQUEST,
                from_node=self.local_node_id,
                to_node=node_id,
                payload={
                    "task_id": task.task_id,
                    "op_id": task.op_id or decision.op_id,
                    "trace_id": task.trace_id or decision.trace_id,
                    "required_capabilities": list(task.required_capabilities),
                    "resource_requirements": dict(task.resource_requirements or {}),
                },
            )
            resp = session.request(msg)
        except FabricError as exc:
            return DispatchResult(
                ok=False,
                node_id=node_id,
                decision=decision,
                error=str(exc),
                error_code=getattr(exc, "code", "FABRIC_ERROR"),
            )
        finally:
            session.close()

        ok = resp.type == MessageType.ACK and bool(resp.payload.get("ok", True))
        result = (resp.payload or {}).get("result") or {}
        checkpoint_hash = result.get("checkpoint_content_hash")

        # Client-side checkpoint notice into local C-RAM (durable audit)
        if ok and self.cram_root is not None:
            store = CRAMStore(self.cram_root)
            notice = {
                "type": MessageType.CHECKPOINT_NOTICE.value,
                "task_id": task.task_id,
                "op_id": task.op_id or decision.op_id,
                "trace_id": task.trace_id or decision.trace_id,
                "selected_node": node_id,
                "remote_checkpoint": checkpoint_hash,
                "result": result,
            }
            import json

            raw = json.dumps(notice, sort_keys=True, separators=(",", ":")).encode(
                "utf-8"
            )
            local_hash = store.put(
                raw,
                metadata={
                    "kind": "fabric_dispatch_checkpoint",
                    "task_id": task.task_id,
                    "op_id": str(task.op_id or decision.op_id or ""),
                },
            )
            if not checkpoint_hash:
                checkpoint_hash = local_hash
            else:
                # Prefer remote hash but always have local durable copy
                pass

        return DispatchResult(
            ok=ok,
            node_id=node_id,
            decision=decision,
            response=resp,
            checkpoint_hash=checkpoint_hash,
            error=None if ok else str((resp.payload or {}).get("error") or "nack"),
            error_code=None if ok else (resp.payload or {}).get("code") or "FABRIC_ERROR",
            extras={"result": result},
        )

    def heartbeat(self, node_id: str) -> FabricMessage:
        ep = self.endpoints.get(node_id)
        if ep is None:
            raise InvalidSession(f"no endpoint for {node_id}")
        session = NodeSession(
            self.local_node_id,
            cert_paths=self.cert_paths,
            tls_required=self.tls_required,
        )
        try:
            session.connect(ep)
            msg = FabricMessage(
                MessageType.HEARTBEAT,
                from_node=self.local_node_id,
                to_node=node_id,
                payload={},
            )
            return session.request(msg)
        finally:
            session.close()


def default_tls_endpoint(node_id: str, host: str, port: int) -> NodeEndpoint:
    return NodeEndpoint(
        node_id=node_id, mode=TransportMode.TLS, host=host, port=port
    )


__all__ = [
    "DispatchResult",
    "NetworkFabric",
    "default_tls_endpoint",
]
