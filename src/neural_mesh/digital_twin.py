"""Backward-compatible re-exports from neural_mesh.twin (Cycle 2 → Cycle 3)."""

from __future__ import annotations

from neural_mesh.twin.events import FaultEvent
from neural_mesh.twin.faults import (
    FAULT_NODE_LOSS,
    FAULT_PACKET_DELAY,
    FAULT_PACKET_DROP,
    SUPPORTED_FAULTS,
)
from neural_mesh.twin.simulator import (
    BenchmarkMetrics,
    DigitalTwin,
    SimulationReport,
    TaskResult,
    TwinLink,
    TwinNode,
    TwinTask,
)

__all__ = [
    "FAULT_NODE_LOSS",
    "FAULT_PACKET_DELAY",
    "FAULT_PACKET_DROP",
    "SUPPORTED_FAULTS",
    "BenchmarkMetrics",
    "DigitalTwin",
    "FaultEvent",
    "SimulationReport",
    "TaskResult",
    "TwinLink",
    "TwinNode",
    "TwinTask",
]
