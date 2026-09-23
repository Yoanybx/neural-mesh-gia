"""Out-of-process replica client — Unix socket sync (Cycle 7)."""

from __future__ import annotations

import base64
import time
import uuid
from pathlib import Path
from typing import Any

from .framing import CONNECT_TIMEOUT, READ_TIMEOUT, WRITE_TIMEOUT
from .unix_transport import FrameSocket, TransportError, connect_unix


def _b64encode(data: bytes) -> str:
    return base64.b64encode(data).decode("ascii")


def _b64decode(s: str) -> bytes:
    return base64.b64decode(s.encode("ascii"), validate=True)


class OOPReplicaClient:
    """Stop-and-wait client for ``mesh cram replica serve``."""

    def __init__(
        self,
        socket_path: str | Path,
        *,
        local_node_id: str = "node-01",
        connect_timeout: float = CONNECT_TIMEOUT,
        read_timeout: float = READ_TIMEOUT,
        write_timeout: float = WRITE_TIMEOUT,
    ):
        self.socket_path = Path(socket_path)
        self.local_node_id = local_node_id
        self.connect_timeout = connect_timeout
        self.read_timeout = read_timeout
        self.write_timeout = write_timeout
        self._fs: FrameSocket | None = None
        self.peer_node_id: str | None = None

    def connect(self) -> dict[str, Any]:
        self.close()
        self._fs = connect_unix(
            self.socket_path,
            connect_timeout=self.connect_timeout,
            read_timeout=self.read_timeout,
            write_timeout=self.write_timeout,
        )
        ack = self._fs.request(
            {
                "type": "HELLO",
                "node_id": self.local_node_id,
                "role": "primary",
            }
        )
        if ack.get("type") != "HELLO_ACK" or not ack.get("ready"):
            self.close()
            raise TransportError(f"HELLO failed: {ack}")
        self.peer_node_id = str(ack.get("node_id") or "")
        return ack

    def close(self) -> None:
        if self._fs is not None:
            self._fs.close()
            self._fs = None

    def __enter__(self) -> "OOPReplicaClient":
        self.connect()
        return self

    def __exit__(self, *args: object) -> None:
        self.close()

    def _req(self, msg: dict[str, Any]) -> dict[str, Any]:
        """Send one RPC. Reuses connection if open (stop-and-wait)."""
        if self._fs is None:
            # Lightweight connect without nested HELLO if already handshaking
            self.connect()
        assert self._fs is not None
        return self._fs.request(msg)

    def request_oneshot(self, msg: dict[str, Any]) -> dict[str, Any]:
        """Connect, HELLO if needed, one RPC, then close — frees server slot."""
        try:
            if self._fs is None:
                self.connect()
            assert self._fs is not None
            # HELLO already done in connect; send business message
            if msg.get("type") == "HELLO":
                return self._fs.request(msg)
            return self._fs.request(msg)
        finally:
            self.close()

    def ping(self) -> dict[str, Any]:
        return self.request_oneshot({"type": "PING"})

    def status(self) -> dict[str, Any]:
        return self.request_oneshot({"type": "STATUS"})

    def put(
        self,
        data: bytes,
        *,
        content_hash: str,
        op_id: str | None = None,
        epoch: int = 0,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        op_id = op_id or uuid.uuid4().hex
        return self.request_oneshot(
            {
                "type": "PUT",
                "op_id": op_id,
                "epoch": epoch,
                "content_hash": content_hash,
                "metadata": dict(metadata or {}),
                "data_b64": _b64encode(data),
            }
        )

    def get(self, content_hash: str) -> dict[str, Any]:
        resp = self.request_oneshot({"type": "GET", "content_hash": content_hash})
        if resp.get("ok") and resp.get("data_b64"):
            resp = dict(resp)
            resp["data"] = _b64decode(str(resp["data_b64"]))
        return resp

    def sync_bytes(
        self,
        data: bytes,
        *,
        content_hash: str,
        op_id: str | None = None,
        epoch: int = 0,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """PUT then verify GET — returns timing + ack."""
        t0 = time.perf_counter()
        ack = self.put(
            data,
            content_hash=content_hash,
            op_id=op_id,
            epoch=epoch,
            metadata=metadata,
        )
        elapsed = time.perf_counter() - t0
        return {"ack": ack, "t_seconds": elapsed, "ok": bool(ack.get("ok"))}


__all__ = ["OOPReplicaClient"]
