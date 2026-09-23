"""Framed stream transport over TLS (TCP) or AF_UNIX (Cycle 11).

Reuses Cycle 7 framing (16 MiB) from ``cram.replication.framing``.
"""

from __future__ import annotations

import socket
import ssl
from enum import Enum
from pathlib import Path
from typing import Any

from neural_mesh.cram.replication.framing import (
    CONNECT_TIMEOUT,
    HEADER_SIZE,
    MAX_FRAME_BYTES,
    READ_TIMEOUT,
    WRITE_TIMEOUT,
    FrameError,
    FrameTooLarge,
    decode_payload,
    encode_frame,
    parse_header,
)

from .errors import (
    ConnectionDrop,
    FabricTLSError,
    MessageCorruption,
    NetworkTimeout,
    PlaintextForbidden,
)
from .tls import NodeCertPaths, build_ssl_context, verify_peer_identity


class TransportMode(str, Enum):
    TLS = "tls"
    UNIX = "unix"


class FrameStream:
    """Stop-and-wait framed connection over a connected stream (TLS or plain)."""

    def __init__(
        self,
        sock: socket.socket,
        *,
        mode: TransportMode,
        peer_node_id: str | None = None,
        read_timeout: float = READ_TIMEOUT,
        write_timeout: float = WRITE_TIMEOUT,
    ):
        self.sock = sock
        self.mode = TransportMode(mode)
        self.peer_node_id = peer_node_id
        self.read_timeout = float(read_timeout)
        self.write_timeout = float(write_timeout)
        self._closed = False

    @property
    def is_tls(self) -> bool:
        return isinstance(self.sock, ssl.SSLSocket)

    def close(self) -> None:
        if self._closed:
            return
        self._closed = True
        try:
            self.sock.shutdown(socket.SHUT_RDWR)
        except OSError:
            pass
        try:
            self.sock.close()
        except OSError:
            pass

    def __enter__(self) -> "FrameStream":
        return self

    def __exit__(self, *args: object) -> None:
        self.close()

    def _recv_exact(self, n: int) -> bytes:
        buf = bytearray()
        self.sock.settimeout(self.read_timeout)
        while len(buf) < n:
            try:
                chunk = self.sock.recv(n - len(buf))
            except socket.timeout as exc:
                raise NetworkTimeout("read timeout", op="recv") from exc
            except ssl.SSLError as exc:
                raise FabricTLSError(f"tls recv failed: {exc}") from exc
            except OSError as exc:
                raise ConnectionDrop(f"recv failed: {exc}") from exc
            if not chunk:
                raise ConnectionDrop("peer closed mid-frame")
            buf.extend(chunk)
        return bytes(buf)

    def recv_frame(self) -> dict[str, Any]:
        try:
            header = self._recv_exact(HEADER_SIZE)
            length = parse_header(header)
            body = self._recv_exact(length)
            return decode_payload(body)
        except FrameTooLarge as exc:
            self.close()
            raise MessageCorruption(str(exc)) from exc
        except FrameError as exc:
            self.close()
            raise MessageCorruption(str(exc)) from exc

    def send_frame(self, payload: dict[str, Any]) -> None:
        try:
            data = encode_frame(payload)
        except FrameTooLarge as exc:
            raise MessageCorruption(str(exc)) from exc
        self.sock.settimeout(self.write_timeout)
        view = memoryview(data)
        sent = 0
        while sent < len(data):
            try:
                n = self.sock.send(view[sent:])
            except socket.timeout as exc:
                raise NetworkTimeout("write timeout", op="send") from exc
            except ssl.SSLError as exc:
                raise FabricTLSError(f"tls send failed: {exc}") from exc
            except OSError as exc:
                raise ConnectionDrop(f"send failed: {exc}") from exc
            if n == 0:
                raise ConnectionDrop("peer closed during send")
            sent += n

    def request(self, payload: dict[str, Any]) -> dict[str, Any]:
        self.send_frame(payload)
        return self.recv_frame()


def connect_tls(
    host: str,
    port: int,
    paths: NodeCertPaths,
    *,
    expected_peer: str,
    connect_timeout: float = CONNECT_TIMEOUT,
    read_timeout: float = READ_TIMEOUT,
    write_timeout: float = WRITE_TIMEOUT,
) -> FrameStream:
    """Client connect with mTLS; verify peer identity = expected_peer."""
    raw = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    raw.settimeout(connect_timeout)
    try:
        raw.connect((host, int(port)))
    except OSError as exc:
        raw.close()
        raise ConnectionDrop(f"connect failed: {exc}") from exc
    ctx = build_ssl_context(paths, server_side=False)
    try:
        ssock = ctx.wrap_socket(raw, server_hostname=expected_peer)
    except ssl.SSLError as exc:
        raw.close()
        raise FabricTLSError(f"TLS handshake failed: {exc}", peer=expected_peer) from exc
    except OSError as exc:
        raw.close()
        raise ConnectionDrop(f"TLS wrap failed: {exc}") from exc
    try:
        verify_peer_identity(ssock, expected_peer)
    except FabricTLSError:
        try:
            ssock.close()
        except OSError:
            pass
        raise
    return FrameStream(
        ssock,
        mode=TransportMode.TLS,
        peer_node_id=expected_peer,
        read_timeout=read_timeout,
        write_timeout=write_timeout,
    )


def connect_unix(
    path: str | Path,
    *,
    connect_timeout: float = CONNECT_TIMEOUT,
    read_timeout: float = READ_TIMEOUT,
    write_timeout: float = WRITE_TIMEOUT,
    tls_required: bool = False,
) -> FrameStream:
    """AF_UNIX framed connect (test/local). Forbidden if tls_required."""
    if tls_required:
        raise PlaintextForbidden("AF_UNIX connect blocked: TLS required")
    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    sock.settimeout(connect_timeout)
    try:
        sock.connect(str(path))
    except OSError as exc:
        sock.close()
        raise ConnectionDrop(f"unix connect failed: {exc}") from exc
    return FrameStream(
        sock,
        mode=TransportMode.UNIX,
        peer_node_id=None,
        read_timeout=read_timeout,
        write_timeout=write_timeout,
    )


def listen_tcp(host: str = "127.0.0.1", port: int = 0, *, backlog: int = 16) -> socket.socket:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind((host, int(port)))
    sock.listen(backlog)
    return sock


def accept_tls(
    listen_sock: socket.socket,
    paths: NodeCertPaths,
    *,
    expected_peer: str | None = None,
    accept_timeout: float = CONNECT_TIMEOUT,
    read_timeout: float = READ_TIMEOUT,
    write_timeout: float = WRITE_TIMEOUT,
) -> FrameStream:
    """Accept one TCP connection and complete mTLS handshake."""
    listen_sock.settimeout(accept_timeout)
    try:
        raw, _addr = listen_sock.accept()
    except socket.timeout as exc:
        raise NetworkTimeout("accept timeout", op="accept") from exc
    except OSError as exc:
        raise ConnectionDrop(f"accept failed: {exc}") from exc
    ctx = build_ssl_context(paths, server_side=True)
    try:
        ssock = ctx.wrap_socket(raw, server_side=True)
    except ssl.SSLError as exc:
        raw.close()
        raise FabricTLSError(f"TLS handshake failed (server): {exc}") from exc
    except OSError as exc:
        raw.close()
        raise ConnectionDrop(f"TLS server wrap failed: {exc}") from exc
    peer_id = None
    if expected_peer is not None:
        try:
            peer_id = verify_peer_identity(ssock, expected_peer)
        except FabricTLSError:
            try:
                ssock.close()
            except OSError:
                pass
            raise
    else:
        from .tls import peer_identities

        ids = peer_identities(ssock)
        peer_id = ids[0] if ids else None
    return FrameStream(
        ssock,
        mode=TransportMode.TLS,
        peer_node_id=peer_id,
        read_timeout=read_timeout,
        write_timeout=write_timeout,
    )


def listen_unix(path: str | Path, *, backlog: int = 1, tls_required: bool = False) -> socket.socket:
    if tls_required:
        raise PlaintextForbidden("AF_UNIX listen blocked: TLS required")
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    if p.exists():
        p.unlink()
    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(str(p))
    try:
        import os

        os.chmod(str(p), 0o600)
    except OSError:
        pass
    sock.listen(backlog)
    return sock


__all__ = [
    "FrameStream",
    "MAX_FRAME_BYTES",
    "TransportMode",
    "accept_tls",
    "connect_tls",
    "connect_unix",
    "listen_tcp",
    "listen_unix",
]
