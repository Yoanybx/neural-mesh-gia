"""Unix-domain socket frame transport (Cycle 7)."""

from __future__ import annotations

import os
import socket
from pathlib import Path
from typing import Any

from .framing import (
    CONNECT_TIMEOUT,
    HEADER_SIZE,
    READ_TIMEOUT,
    WRITE_TIMEOUT,
    FrameError,
    decode_payload,
    encode_frame,
    parse_header,
)


class TransportError(Exception):
    """Socket closed, timeout, or mid-frame cut."""


class FrameSocket:
    """Stop-and-wait framed connection over a connected stream socket."""

    def __init__(
        self,
        sock: socket.socket,
        *,
        read_timeout: float = READ_TIMEOUT,
        write_timeout: float = WRITE_TIMEOUT,
    ):
        self.sock = sock
        self.read_timeout = float(read_timeout)
        self.write_timeout = float(write_timeout)
        self._closed = False

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

    def __enter__(self) -> "FrameSocket":
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
                raise TransportError("read timeout") from exc
            except OSError as exc:
                raise TransportError(f"recv failed: {exc}") from exc
            if not chunk:
                raise TransportError("peer closed mid-frame")
            buf.extend(chunk)
        return bytes(buf)

    def recv_frame(self) -> dict[str, Any]:
        header = self._recv_exact(HEADER_SIZE)
        try:
            length = parse_header(header)
        except FrameError:
            self.close()
            raise
        body = self._recv_exact(length)
        return decode_payload(body)

    def send_frame(self, payload: dict[str, Any]) -> None:
        data = encode_frame(payload)
        self.sock.settimeout(self.write_timeout)
        view = memoryview(data)
        sent = 0
        while sent < len(data):
            try:
                n = self.sock.send(view[sent:])
            except socket.timeout as exc:
                raise TransportError("write timeout") from exc
            except OSError as exc:
                raise TransportError(f"send failed: {exc}") from exc
            if n == 0:
                raise TransportError("peer closed during send")
            sent += n

    def request(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Stop-and-wait: send then recv (Cycle 7 backpressure)."""
        self.send_frame(payload)
        return self.recv_frame()


def connect_unix(
    path: str | Path,
    *,
    connect_timeout: float = CONNECT_TIMEOUT,
    read_timeout: float = READ_TIMEOUT,
    write_timeout: float = WRITE_TIMEOUT,
) -> FrameSocket:
    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    sock.settimeout(connect_timeout)
    try:
        sock.connect(str(path))
    except OSError as exc:
        sock.close()
        raise TransportError(f"connect failed: {exc}") from exc
    return FrameSocket(sock, read_timeout=read_timeout, write_timeout=write_timeout)


def listen_unix(path: str | Path, *, backlog: int = 1) -> socket.socket:
    """Create a listening AF_UNIX socket; removes stale path if present."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    if p.exists():
        p.unlink()
    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(str(p))
    # Restrict to owner when possible (local IPC; TLS still explicit debt).
    try:
        os.chmod(str(p), 0o600)
    except OSError:
        pass
    sock.listen(backlog)
    return sock


__all__ = [
    "FrameSocket",
    "TransportError",
    "connect_unix",
    "listen_unix",
]
