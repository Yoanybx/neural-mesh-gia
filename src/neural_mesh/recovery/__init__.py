"""Mesh recovery + rebuild (Cycle 35 / CP-0039 / H2).

Schema: mesh.recovery/v1
Capability: docs/capabilities/MESH_RECOVERY_REBUILD.md
CLI: mesh recover status|snapshot|restore|rebuild
ABORT→snapshot restore on recovery failure.
"""

from .models import (
    SCHEMA_ID,
    SCHEMA_SNAPSHOT,
    SCHEMA_STORE,
    DurableState,
    RebuildResult,
    RecoveryAbortRestore,
    RecoveryError,
    RecoveryMissingSnapshot,
    RecoveryPlaintextForbidden,
    RecoveryRebuildFailed,
    RecoveryStatus,
    RecoveryTamper,
    RecoveryVerifyFailed,
    RestoreResult,
    SnapshotMeta,
)
from .service import RecoveryService
from .store import RecoveryStore, require_no_plaintext
from .cli_ops import (
    cmd_recover_rebuild,
    cmd_recover_restore,
    cmd_recover_snapshot,
    cmd_recover_status,
)

__all__ = [
    "SCHEMA_ID",
    "SCHEMA_SNAPSHOT",
    "SCHEMA_STORE",
    "DurableState",
    "RebuildResult",
    "RecoveryAbortRestore",
    "RecoveryError",
    "RecoveryMissingSnapshot",
    "RecoveryPlaintextForbidden",
    "RecoveryRebuildFailed",
    "RecoveryService",
    "RecoveryStatus",
    "RecoveryStore",
    "RecoveryTamper",
    "RecoveryVerifyFailed",
    "RestoreResult",
    "SnapshotMeta",
    "cmd_recover_rebuild",
    "cmd_recover_restore",
    "cmd_recover_snapshot",
    "cmd_recover_status",
    "require_no_plaintext",
]
