"""Typed Network Fabric errors — fail-closed, no silent plaintext fallback."""

from __future__ import annotations


class FabricError(Exception):
    """Base fabric / network error."""

    code: str = "FABRIC_ERROR"

    def __init__(self, message: str = "", *, code: str | None = None):
        super().__init__(message)
        if code is not None:
            self.code = code


class FabricTLSError(FabricError):
    """TLS handshake / identity / cert failure — fail-closed."""

    code = "FABRIC_TLS_ERROR"

    def __init__(self, message: str = "fabric TLS error", *, peer: str | None = None):
        self.peer = peer
        detail = message if not peer else f"{message} (peer={peer})"
        super().__init__(detail)


class NetworkTimeout(FabricError):
    """Connect / read / write timeout."""

    code = "NETWORK_TIMEOUT"

    def __init__(self, message: str = "network timeout", *, op: str | None = None):
        self.op = op
        super().__init__(message if not op else f"{message}: {op}")


class ConnectionDrop(FabricError):
    """Peer closed / RST / kill mid-stream."""

    code = "CONNECTION_DROP"

    def __init__(self, message: str = "connection drop"):
        super().__init__(message)


class InvalidSession(FabricError):
    """Session not connected, closed, or identity mismatch on reuse."""

    code = "INVALID_SESSION"

    def __init__(self, message: str = "invalid session"):
        super().__init__(message)


class MessageCorruption(FabricError):
    """Frame / JSON / envelope corruption."""

    code = "MESSAGE_CORRUPTION"

    def __init__(self, message: str = "message corruption"):
        super().__init__(message)


class PlaintextForbidden(FabricError):
    """Attempted plaintext when TLS mode required — never silent fallback."""

    code = "FABRIC_PLAINTEXT_FORBIDDEN"

    def __init__(self, message: str = "plaintext forbidden when TLS required"):
        super().__init__(message)


__all__ = [
    "ConnectionDrop",
    "FabricError",
    "FabricTLSError",
    "InvalidSession",
    "MessageCorruption",
    "NetworkTimeout",
    "PlaintextForbidden",
]
