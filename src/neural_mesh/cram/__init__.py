"""Phase 2 C-RAM core — content-addressable, verifiable, recoverable store."""

from .errors import (
    CRAMCorrupt,
    CRAMError,
    CRAMKeyError,
    CRAMNodeUnavailable,
    NodeUnavailable,
    ObjectMissing,
    StaleTopology,
)
from .hashing import content_hash, root_hash, shard_dirs
from .models import CRAMObject, ObjectType
from .recovery import (
    RecoveryBenchResult,
    RecoveryResult,
    recover_after_node_loss,
    run_recovery_bench,
)
from .store import CRAMStore

__all__ = [
    "CRAMCorrupt",
    "CRAMError",
    "CRAMKeyError",
    "CRAMNodeUnavailable",
    "CRAMObject",
    "CRAMStore",
    "NodeUnavailable",
    "ObjectMissing",
    "StaleTopology",
    "ObjectType",
    "RecoveryBenchResult",
    "RecoveryResult",
    "content_hash",
    "recover_after_node_loss",
    "root_hash",
    "run_recovery_bench",
    "shard_dirs",
]
