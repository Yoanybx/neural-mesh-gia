"""NodeSession — connect / send / receive / close (Cycle 11)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .errors import InvalidSession, PlaintextForbidden
from .protocol import FabricMessage
from .tls import NodeCertPaths
from .transport import (
    FrameStream,
    TransportMode,
    connect_tls,
    connect_unix,
)


@dataclass
class NodeEndpoint:
    """How to reach a remote node."""

    node_id: str
    mode: TransportMode = TransportMode.TLS
    host: str = "127.0.0.1"
    port: int = 0
    unix_path: str | Path | None = None


class NodeSession:
    """Authenticated framed session to a single peer node."""

    def __init__(
        self,
        local_node_id: str,
        *,
        cert_paths: NodeCertPaths | None = None,
        tls_required: bool = True,
    ):
        self.local_node_id = str(local_node_id)
        self.cert_paths = cert_paths
        self.tls_required = bool(tls_required)
        self._stream: FrameStream | None = None
        self.peer_node_id: str | None = None
        self.mode: TransportMode | None = None

    @property
    def connected(self) -> bool:
        return self._stream is not None and not self._stream._closed

    def connect(self, node: NodeEndpoint) -> None:
        mode = TransportMode(node.mode)
        if self.tls_required and mode != TransportMode.TLS:
            raise PlaintextForbidden(
                f"refusing mode={mode.value}: TLS required (no plaintext fallback)"
            )
        if mode == TransportMode.TLS:
            if self.cert_paths is None:
                raise InvalidSession("TLS mode requires cert_paths")
            stream = connect_tls(
                node.host,
                int(node.port),
                self.cert_paths,
                expected_peer=node.node_id,
            )
        else:
            if node.unix_path is None:
                raise InvalidSession("unix mode requires unix_path")
            stream = connect_unix(
                node.unix_path, tls_required=self.tls_required
            )
        self._stream = stream
        self.peer_node_id = node.node_id
        self.mode = mode

    def send(self, message: FabricMessage | dict[str, Any]) -> None:
        if not self.connected or self._stream is None:
            raise InvalidSession("not connected")
        if isinstance(message, FabricMessage):
            payload = message.to_dict()
        else:
            payload = dict(message)
        self._stream.send_frame(payload)

    def receive(self) -> FabricMessage:
        if not self.connected or self._stream is None:
            raise InvalidSession("not connected")
        raw = self._stream.recv_frame()
        return FabricMessage.from_dict(raw)

    def request(self, message: FabricMessage) -> FabricMessage:
        self.send(message)
        return self.receive()

    def close(self) -> None:
        if self._stream is not None:
            self._stream.close()
            self._stream = None
        # Keep peer_node_id for diagnostics; mark unusable
        # subsequent send/receive → InvalidSession

    def __enter__(self) -> "NodeSession":
        return self

    def __exit__(self, *args: object) -> None:
        self.close()


__all__ = ["NodeEndpoint", "NodeSession"]
