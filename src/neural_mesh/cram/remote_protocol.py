"""Remote C-RAM + Phase 5A replica message contracts over Fabric (Cycle 12)."""

from __future__ import annotations

import base64
from enum import Enum
from typing import Any

from neural_mesh.network.protocol import FabricMessage, MessageType


class RemoteOp(str, Enum):
    PUT = "PUT"
    GET = "GET"
    VERIFY = "VERIFY"
    CHECKPOINT = "CHECKPOINT"


class ReplicaRole(str, Enum):
    PRIMARY = "PRIMARY"
    STANDBY = "STANDBY"
    UNKNOWN = "UNKNOWN"


# Phase 5A fabric message types (extend C11 set)
PHASE5A_MESSAGE_TYPES = (
    MessageType.REPLICA_APPEND,
    MessageType.REPLICA_ACK,
    MessageType.ROLE_STATUS,
    MessageType.PROMOTE_REQUEST,
    MessageType.CRAM_PUT,
    MessageType.CRAM_GET,
    MessageType.CRAM_VERIFY,
    MessageType.CRAM_CHECKPOINT,
)

PHASE5B_MESSAGE_TYPES = (
    MessageType.RECOVERY_REQUEST,
    MessageType.RECOVERY_RESPONSE,
    MessageType.RECOVERY_VERIFY,
    MessageType.RECOVERY_COMMIT,
)

FEATURE_FLAG_ENV = "NEURAL_MESH_PHASE5A_REPLICATION"


def b64encode(data: bytes) -> str:
    return base64.b64encode(data).decode("ascii")


def b64decode(text: str) -> bytes:
    return base64.b64decode(text.encode("ascii"))


def make_cram_put(
    *,
    from_node: str,
    to_node: str,
    content: bytes,
    metadata: dict[str, Any] | None = None,
    epoch: int = 0,
    version: int = 0,
    op_id: str | None = None,
    trace_id: str | None = None,
    operation_id: str | None = None,
) -> FabricMessage:
    payload: dict[str, Any] = {
        "op": RemoteOp.PUT.value,
        "content_b64": b64encode(content),
        "metadata": dict(metadata or {}),
        "epoch": int(epoch),
        "version": int(version),
    }
    if op_id:
        payload["op_id"] = op_id
    if trace_id:
        payload["trace_id"] = trace_id
    if operation_id:
        payload["operation_id"] = operation_id
    return FabricMessage(
        MessageType.CRAM_PUT, from_node=from_node, to_node=to_node, payload=payload
    )


def make_cram_get(
    *,
    from_node: str,
    to_node: str,
    content_hash: str,
    op_id: str | None = None,
    trace_id: str | None = None,
    operation_id: str | None = None,
) -> FabricMessage:
    payload: dict[str, Any] = {
        "op": RemoteOp.GET.value,
        "object_hash": content_hash,
    }
    if op_id:
        payload["op_id"] = op_id
    if trace_id:
        payload["trace_id"] = trace_id
    if operation_id:
        payload["operation_id"] = operation_id
    return FabricMessage(
        MessageType.CRAM_GET, from_node=from_node, to_node=to_node, payload=payload
    )


def make_cram_verify(
    *,
    from_node: str,
    to_node: str,
    content_hash: str,
    op_id: str | None = None,
    trace_id: str | None = None,
    operation_id: str | None = None,
) -> FabricMessage:
    payload: dict[str, Any] = {
        "op": RemoteOp.VERIFY.value,
        "object_hash": content_hash,
    }
    if op_id:
        payload["op_id"] = op_id
    if trace_id:
        payload["trace_id"] = trace_id
    if operation_id:
        payload["operation_id"] = operation_id
    return FabricMessage(
        MessageType.CRAM_VERIFY, from_node=from_node, to_node=to_node, payload=payload
    )


def make_cram_checkpoint(
    *,
    from_node: str,
    to_node: str,
    notice: dict[str, Any],
    op_id: str | None = None,
    trace_id: str | None = None,
    operation_id: str | None = None,
) -> FabricMessage:
    payload: dict[str, Any] = {
        "op": RemoteOp.CHECKPOINT.value,
        "notice": dict(notice),
    }
    if op_id:
        payload["op_id"] = op_id
    if trace_id:
        payload["trace_id"] = trace_id
    if operation_id:
        payload["operation_id"] = operation_id
    return FabricMessage(
        MessageType.CRAM_CHECKPOINT,
        from_node=from_node,
        to_node=to_node,
        payload=payload,
    )


def make_replica_append(
    *,
    from_node: str,
    to_node: str,
    content: bytes,
    object_hash: str,
    epoch: int,
    version: int,
    metadata: dict[str, Any] | None = None,
    op_id: str | None = None,
    trace_id: str | None = None,
    operation_id: str | None = None,
) -> FabricMessage:
    payload: dict[str, Any] = {
        "object_hash": object_hash,
        "epoch": int(epoch),
        "version": int(version),
        "node_id": from_node,
        "content_b64": b64encode(content),
        "metadata": dict(metadata or {}),
    }
    if op_id:
        payload["op_id"] = op_id
    if trace_id:
        payload["trace_id"] = trace_id
    if operation_id:
        payload["operation_id"] = operation_id
    return FabricMessage(
        MessageType.REPLICA_APPEND,
        from_node=from_node,
        to_node=to_node,
        payload=payload,
    )


def make_replica_ack(
    *,
    from_node: str,
    to_node: str,
    ref_msg_id: str,
    ok: bool,
    object_hash: str | None = None,
    epoch: int | None = None,
    error: str | None = None,
    code: str | None = None,
) -> FabricMessage:
    payload: dict[str, Any] = {
        "ref_msg_id": ref_msg_id,
        "ok": bool(ok),
        "node_id": from_node,
    }
    if object_hash is not None:
        payload["object_hash"] = object_hash
    if epoch is not None:
        payload["epoch"] = int(epoch)
    if error:
        payload["error"] = error
    if code:
        payload["code"] = code
    return FabricMessage(
        MessageType.REPLICA_ACK,
        from_node=from_node,
        to_node=to_node,
        payload=payload,
    )


def make_role_status(
    *,
    from_node: str,
    to_node: str,
    role: ReplicaRole | str,
    epoch: int,
    writable_primary: str | None,
    object_hash: str | None = None,
) -> FabricMessage:
    payload: dict[str, Any] = {
        "role": role.value if isinstance(role, ReplicaRole) else str(role),
        "epoch": int(epoch),
        "writable_primary": writable_primary,
        "node_id": from_node,
    }
    if object_hash:
        payload["object_hash"] = object_hash
    return FabricMessage(
        MessageType.ROLE_STATUS,
        from_node=from_node,
        to_node=to_node,
        payload=payload,
    )


def make_promote_request(
    *,
    from_node: str,
    to_node: str,
    object_hash: str,
    epoch: int,
    target_node: str,
    op_id: str | None = None,
    trace_id: str | None = None,
    operation_id: str | None = None,
) -> FabricMessage:
    payload: dict[str, Any] = {
        "object_hash": object_hash,
        "epoch": int(epoch),
        "target_node": target_node,
        "node_id": from_node,
    }
    if op_id:
        payload["op_id"] = op_id
    if trace_id:
        payload["trace_id"] = trace_id
    if operation_id:
        payload["operation_id"] = operation_id
    return FabricMessage(
        MessageType.PROMOTE_REQUEST,
        from_node=from_node,
        to_node=to_node,
        payload=payload,
    )


__all__ = [
    "FEATURE_FLAG_ENV",
    "PHASE5A_MESSAGE_TYPES",
    "PHASE5B_MESSAGE_TYPES",
    "RemoteOp",
    "ReplicaRole",
    "b64decode",
    "b64encode",
    "make_cram_checkpoint",
    "make_cram_get",
    "make_cram_put",
    "make_cram_verify",
    "make_promote_request",
    "make_replica_ack",
    "make_replica_append",
    "make_role_status",
]
