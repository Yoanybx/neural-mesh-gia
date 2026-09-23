"""Size-limited length-prefixed framing for OOP replica transport (Cycle 7)."""

from __future__ import annotations

import json
import struct
from typing import Any

# Frozen in docs/cram_replica_oop_transport.md
MAX_FRAME_BYTES = 16_777_216  # 16 MiB
HEADER_STRUCT = struct.Struct("!I")
HEADER_SIZE = HEADER_STRUCT.size

CONNECT_TIMEOUT = 2.0
READ_TIMEOUT = 5.0
WRITE_TIMEOUT = 5.0
IDLE_TIMEOUT = 30.0


class FrameError(Exception):
    """Protocol / framing fault (oversized, truncated, bad JSON)."""


class FrameTooLarge(FrameError):
    def __init__(self, length: int, limit: int = MAX_FRAME_BYTES):
        self.length = length
        self.limit = limit
        super().__init__(f"frame length {length} exceeds limit {limit}")


def encode_frame(payload: dict[str, Any] | bytes) -> bytes:
    """Encode a JSON object (or raw bytes) into a length-prefixed frame."""
    if isinstance(payload, bytes):
        body = payload
    else:
        body = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode(
            "utf-8"
        )
    if len(body) > MAX_FRAME_BYTES:
        raise FrameTooLarge(len(body))
    return HEADER_STRUCT.pack(len(body)) + body


def decode_payload(body: bytes) -> dict[str, Any]:
    try:
        data = json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise FrameError(f"invalid JSON payload: {exc}") from exc
    if not isinstance(data, dict):
        raise FrameError("payload must be a JSON object")
    return data


def parse_header(header: bytes) -> int:
    if len(header) != HEADER_SIZE:
        raise FrameError(f"short header: {len(header)} bytes")
    (length,) = HEADER_STRUCT.unpack(header)
    if length > MAX_FRAME_BYTES:
        raise FrameTooLarge(length)
    return length


__all__ = [
    "CONNECT_TIMEOUT",
    "FrameError",
    "FrameTooLarge",
    "HEADER_SIZE",
    "IDLE_TIMEOUT",
    "MAX_FRAME_BYTES",
    "READ_TIMEOUT",
    "WRITE_TIMEOUT",
    "decode_payload",
    "encode_frame",
    "parse_header",
]
