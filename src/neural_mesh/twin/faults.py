"""Supported fault injection types for the Digital Twin."""

from __future__ import annotations

FAULT_NODE_LOSS = "NODE_LOSS"
FAULT_PACKET_DROP = "PACKET_DROP"
FAULT_PACKET_DELAY = "PACKET_DELAY"

SUPPORTED_FAULTS = frozenset(
    {FAULT_NODE_LOSS, FAULT_PACKET_DROP, FAULT_PACKET_DELAY}
)
