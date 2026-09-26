"""Mesh dual-primary fence (Cycle 36 / CP-0040 / H3).

Schema: mesh.fence/v1
Capability: docs/capabilities/MESH_DUAL_PRIMARY_FENCE.md
CLI: mesh fence status|probe|demote|reelect
ABORT→demote+re-elect on unresolved dual-primary (never silent dual_primary>0).
"""

from .models import (
    SCHEMA_EPOCH,
    SCHEMA_ID,
    SCHEMA_ROLE,
    SCHEMA_STORE,
    DemoteResult,
    FenceAbortDemoteReelect,
    FenceActionResult,
    FenceDualPrimary,
    FenceEpoch,
    FenceError,
    FenceN2Only,
    FenceNodeUnknown,
    FencePlaintextForbidden,
    FenceStatus,
    FenceUnresolved,
    NodeRole,
    ProbeResult,
    ReelectResult,
)
from .service import FenceService
from .store import FenceStore, new_durable_token, require_no_plaintext
from .cli_ops import (
    cmd_fence_demote,
    cmd_fence_probe,
    cmd_fence_reelect,
    cmd_fence_status,
)

__all__ = [
    "SCHEMA_EPOCH",
    "SCHEMA_ID",
    "SCHEMA_ROLE",
    "SCHEMA_STORE",
    "DemoteResult",
    "FenceAbortDemoteReelect",
    "FenceActionResult",
    "FenceDualPrimary",
    "FenceEpoch",
    "FenceError",
    "FenceN2Only",
    "FenceNodeUnknown",
    "FencePlaintextForbidden",
    "FenceService",
    "FenceStatus",
    "FenceStore",
    "FenceUnresolved",
    "NodeRole",
    "ProbeResult",
    "ReelectResult",
    "cmd_fence_demote",
    "cmd_fence_probe",
    "cmd_fence_reelect",
    "cmd_fence_status",
    "new_durable_token",
    "require_no_plaintext",
]
