"""Phase 2 C-RAM core — content-addressable, verifiable, recoverable store."""

from .errors import (
    CRAMCorrupt,
    CRAMError,
    CRAMKeyError,
    CRAMNodeUnavailable,
    ConflictError,
    NodeUnavailable,
    ObjectMissing,
    PartitionFailClosed,
    StaleEpoch,
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
from .version import CRAMVersion, compare_versions
from .conflict import ConflictOutcome, ConflictPolicy, ConflictRecord
from .consistency import ConsistencyLayer, ConsistencyReport, WriteResult
from .durability import (
    DirFsyncCoalescer,
    DurabilityChecker,
    DurabilityReport,
    DurabilityWAL,
    FSYNC_POLICY,
    GroupFsyncSeal,
    SyncMode,
    atomic_write_bytes,
    compact_checkpoint_bytes,
    get_dir_coalescer,
    get_seal_group,
    reset_dir_coalescer,
    reset_seal_group,
    resolve_dir_fsync_mode,
)
from .partition_suite import PartitionSuiteReport, run_partition_suite
from .compaction import CompactionReport, SnapshotCompactor
from .recovery_protocol import (
    RecoveryFSM,
    RecoveryFSMResult,
    RecoveryMsgType,
    RecoveryState,
    run_recovery_test,
)

__all__ = [
    "CRAMCorrupt",
    "CRAMError",
    "CRAMKeyError",
    "CRAMNodeUnavailable",
    "CRAMObject",
    "CRAMStore",
    "CRAMVersion",
    "ConflictError",
    "ConflictOutcome",
    "ConflictPolicy",
    "ConflictRecord",
    "ConsistencyLayer",
    "ConsistencyReport",
    "NodeUnavailable",
    "ObjectMissing",
    "PartitionFailClosed",
    "StaleEpoch",
    "StaleTopology",
    "ObjectType",
    "RecoveryBenchResult",
    "RecoveryFSM",
    "RecoveryFSMResult",
    "RecoveryMsgType",
    "RecoveryResult",
    "RecoveryState",
    "WriteResult",
    "compare_versions",
    "content_hash",
    "recover_after_node_loss",
    "root_hash",
    "run_recovery_bench",
    "run_recovery_test",
    "DurabilityChecker",
    "DurabilityReport",
    "DurabilityWAL",
    "FSYNC_POLICY",
    "GroupFsyncSeal",
    "resolve_dir_fsync_mode",
    "reset_dir_coalescer",
    "get_dir_coalescer",
    "atomic_write_bytes",
    "compact_checkpoint_bytes",
    "DirFsyncCoalescer",
    "SyncMode",
    "get_seal_group",
    "reset_seal_group",
    "PartitionSuiteReport",
    "run_partition_suite",
    "CompactionReport",
    "SnapshotCompactor",
    "shard_dirs",
]
