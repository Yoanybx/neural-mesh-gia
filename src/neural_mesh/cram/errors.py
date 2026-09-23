"""Typed C-RAM errors — NodeUnavailable (retryable) vs ObjectMissing (terminal)."""

from __future__ import annotations


class CRAMError(Exception):
    """Base C-RAM error."""

    code: str = "CRAM_ERROR"

    def __init__(self, message: str = "", *, code: str | None = None):
        super().__init__(message)
        if code is not None:
            self.code = code


class NodeUnavailable(CRAMError):
    """Node-local C-RAM view unavailable (e.g. after NODE_LOSS). Retryable if node returns."""

    code = "CRAM_NODE_UNAVAILABLE"

    def __init__(self, message: str = "node unavailable", *, node_id: str | None = None):
        self.node_id = node_id
        prefix = f"node {node_id} unavailable" if node_id else message
        super().__init__(prefix if not message or node_id else message)


class ObjectMissing(CRAMError, KeyError):
    """Object not present in durable store or placement index. Terminal without replica."""

    code = "CRAM_OBJECT_MISSING"

    def __init__(self, key: str = "", *, message: str | None = None):
        self.key = key
        super().__init__(message or f"object missing: {key}")


class StaleTopology(CRAMError):
    """Topology hash drifted since checkpoint; refuse silent stale locate."""

    code = "CRAM_STALE_TOPOLOGY"

    def __init__(
        self,
        message: str = "topology hash mismatch",
        *,
        expected: str | None = None,
        actual: str | None = None,
    ):
        self.expected = expected
        self.actual = actual
        super().__init__(message)


class CRAMCorrupt(CRAMError):

    """Blob bytes do not re-hash to the content key."""

    code = "CRAM_CORRUPT"

    def __init__(self, key: str = "", *, message: str | None = None):
        self.key = key
        super().__init__(message or f"corrupt blob: {key}")


# Back-compat aliases used by Cycle 4 call sites / imports
CRAMNodeUnavailable = NodeUnavailable
CRAMKeyError = ObjectMissing

__all__ = [
    "CRAMCorrupt",
    "CRAMError",
    "CRAMKeyError",
    "CRAMNodeUnavailable",
    "NodeUnavailable",
    "ObjectMissing",
    "StaleTopology",
]
