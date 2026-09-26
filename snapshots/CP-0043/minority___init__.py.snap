"""Mesh minority-write safety (Cycle 39 / CP-0043 / H6).

Schema: mesh.minority/v1
Capability: docs/capabilities/MESH_MINORITY_WRITE_FENCE.md
CLI: mesh minority status|probe|halt
ABORT→halt writes on minority-write @N2 (never silent MINORITY_WRITES>0).
"""

from .models import (
    SCHEMA_ATTEMPT,
    SCHEMA_HALT,
    SCHEMA_ID,
    SCHEMA_STORE,
    HaltResult,
    MinorityAbortHaltWrites,
    MinorityError,
    MinorityN2Only,
    MinorityNodeUnknown,
    MinorityPlaintextForbidden,
    MinorityStatus,
    MinorityWriteDetected,
    MinorityWritesHalted,
    ProbeResult,
    WriteAttempt,
    WriteResult,
)
from .service import MinorityService
from .store import MinorityStore, require_no_plaintext
from .cli_ops import (
    cmd_minority_halt,
    cmd_minority_probe,
    cmd_minority_status,
)

__all__ = [
    "SCHEMA_ATTEMPT",
    "SCHEMA_HALT",
    "SCHEMA_ID",
    "SCHEMA_STORE",
    "HaltResult",
    "MinorityAbortHaltWrites",
    "MinorityError",
    "MinorityN2Only",
    "MinorityNodeUnknown",
    "MinorityPlaintextForbidden",
    "MinorityService",
    "MinorityStatus",
    "MinorityStore",
    "MinorityWriteDetected",
    "MinorityWritesHalted",
    "ProbeResult",
    "WriteAttempt",
    "WriteResult",
    "cmd_minority_halt",
    "cmd_minority_probe",
    "cmd_minority_status",
    "require_no_plaintext",
]
