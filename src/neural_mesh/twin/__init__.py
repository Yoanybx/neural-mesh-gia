"""Phase 1 Digital Twin package — faults, topology schema, deterministic simulator."""

from .events import FaultEvent
from .faults import (
    FAULT_NODE_LOSS,
    FAULT_PACKET_DELAY,
    FAULT_PACKET_DROP,
    SUPPORTED_FAULTS,
)
from .schema import Topology, Workload
from .simulator import (
    BenchmarkMetrics,
    DigitalTwin,
    SimulationReport,
    TaskResult,
    TwinLink,
    TwinNode,
    TwinTask,
)
from .placement import CRAMPlacement
from .storage import load_faults, load_json, save_json

__all__ = [
    "FAULT_NODE_LOSS",
    "FAULT_PACKET_DELAY",
    "FAULT_PACKET_DROP",
    "SUPPORTED_FAULTS",
    "BenchmarkMetrics",
    "CRAMPlacement",
    "DigitalTwin",
    "FaultEvent",
    "SimulationReport",
    "TaskResult",
    "Topology",
    "TwinLink",
    "TwinNode",
    "TwinTask",
    "Workload",
    "load_faults",
    "load_json",
    "save_json",
]
