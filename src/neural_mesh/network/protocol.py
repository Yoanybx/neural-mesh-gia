"""Fabric message envelope and types (Cycle 11)."""

from __future__ import annotations

import json
import time
import uuid
from enum import Enum
from typing import Any


class MessageType(str, Enum):
    TASK_REQUEST = "TASK_REQUEST"
    STATE_QUERY = "STATE_QUERY"
    STATE_RESPONSE = "STATE_RESPONSE"
    HEARTBEAT = "HEARTBEAT"
    CAPABILITY_UPDATE = "CAPABILITY_UPDATE"
    CHECKPOINT_NOTICE = "CHECKPOINT_NOTICE"
    ACK = "ACK"
    ERROR = "ERROR"


REQUIRED_MESSAGE_TYPES = (
    MessageType.TASK_REQUEST,
    MessageType.STATE_QUERY,
    MessageType.STATE_RESPONSE,
    MessageType.HEARTBEAT,
    MessageType.CAPABILITY_UPDATE,
    MessageType.CHECKPOINT_NOTICE,
)


class FabricMessage:
    """JSON-serializable fabric envelope."""

    __slots__ = ("type", "msg_id", "from_node", "to_node", "payload", "ts_ms")

    def __init__(
        self,
        type: MessageType | str,
        *,
        from_node: str,
        to_node: str,
        payload: dict[str, Any] | None = None,
        msg_id: str | None = None,
        ts_ms: int | None = None,
    ):
        self.type = MessageType(type) if not isinstance(type, MessageType) else type
        self.msg_id = msg_id or uuid.uuid4().hex
        self.from_node = str(from_node)
        self.to_node = str(to_node)
        self.payload = dict(payload or {})
        self.ts_ms = int(ts_ms if ts_ms is not None else time.time() * 1000)

    def to_dict(self) -> dict[str, Any]:
        return {
            "type": self.type.value,
            "msg_id": self.msg_id,
            "from_node": self.from_node,
            "to_node": self.to_node,
            "payload": self.payload,
            "ts_ms": self.ts_ms,
        }

    def to_json_bytes(self) -> bytes:
        return json.dumps(self.to_dict(), separators=(",", ":"), sort_keys=True).encode(
            "utf-8"
        )

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "FabricMessage":
        if not isinstance(data, dict):
            raise ValueError("envelope must be object")
        if "type" not in data:
            raise ValueError("missing type")
        return cls(
            type=data["type"],
            from_node=str(data.get("from_node", "")),
            to_node=str(data.get("to_node", "")),
            payload=dict(data.get("payload") or {}),
            msg_id=str(data.get("msg_id") or uuid.uuid4().hex),
            ts_ms=int(data.get("ts_ms") or 0),
        )

    @classmethod
    def from_json_bytes(cls, raw: bytes) -> "FabricMessage":
        data = json.loads(raw.decode("utf-8"))
        return cls.from_dict(data)


def make_ack(
    *,
    from_node: str,
    to_node: str,
    ref_msg_id: str,
    ok: bool = True,
    error: str | None = None,
    extra: dict[str, Any] | None = None,
) -> FabricMessage:
    payload: dict[str, Any] = {"ref_msg_id": ref_msg_id, "ok": bool(ok)}
    if error:
        payload["error"] = error
    if extra:
        payload.update(extra)
    return FabricMessage(
        MessageType.ACK, from_node=from_node, to_node=to_node, payload=payload
    )


def make_error(
    *,
    from_node: str,
    to_node: str,
    code: str,
    message: str,
    ref_msg_id: str | None = None,
) -> FabricMessage:
    payload: dict[str, Any] = {"code": code, "message": message}
    if ref_msg_id:
        payload["ref_msg_id"] = ref_msg_id
    return FabricMessage(
        MessageType.ERROR, from_node=from_node, to_node=to_node, payload=payload
    )


__all__ = [
    "FabricMessage",
    "MessageType",
    "REQUIRED_MESSAGE_TYPES",
    "make_ack",
    "make_error",
]
