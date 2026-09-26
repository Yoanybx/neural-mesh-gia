"""Mesh clock-skew join fence (Cycle 40 / CP-0044 / H7).

Schema: mesh.clock/v1
Capability: docs/capabilities/MESH_CLOCK_SKEW_FENCE.md
CLI: mesh clock status|probe|join-check
ABORT→refuse join on clock_skew @N2 (wall_clock_as_authority=0; HLC+mono).
Blueprint P-02: HLC + monotonic counters; wall-clock non-authoritative.
"""

from .models import (
    DEFAULT_SKEW_THRESHOLD_MS,
    SCHEMA_HLC,
    SCHEMA_ID,
    SCHEMA_JOIN,
    SCHEMA_SAMPLE,
    SCHEMA_STORE,
    ClockAbortRefuseJoin,
    ClockError,
    ClockJoinRefused,
    ClockN2Only,
    ClockNodeUnknown,
    ClockPlaintextForbidden,
    ClockSample,
    ClockSkewDetected,
    ClockStatus,
    HLC,
    JoinCheckResult,
    ProbeResult,
)
from .hlc import (
    HLCClock,
    MonotonicCounter,
    compare_hlc,
    skew_ms_diagnostic,
    wall_ms_now,
)
from .service import ClockService
from .store import ClockStore, require_no_plaintext
from .cli_ops import (
    cmd_clock_join_check,
    cmd_clock_probe,
    cmd_clock_status,
)

__all__ = [
    "DEFAULT_SKEW_THRESHOLD_MS",
    "SCHEMA_HLC",
    "SCHEMA_ID",
    "SCHEMA_JOIN",
    "SCHEMA_SAMPLE",
    "SCHEMA_STORE",
    "ClockAbortRefuseJoin",
    "ClockError",
    "ClockJoinRefused",
    "ClockN2Only",
    "ClockNodeUnknown",
    "ClockPlaintextForbidden",
    "ClockSample",
    "ClockService",
    "ClockSkewDetected",
    "ClockStatus",
    "ClockStore",
    "HLC",
    "HLCClock",
    "JoinCheckResult",
    "MonotonicCounter",
    "ProbeResult",
    "cmd_clock_join_check",
    "cmd_clock_probe",
    "cmd_clock_status",
    "compare_hlc",
    "require_no_plaintext",
    "skew_ms_diagnostic",
    "wall_ms_now",
]
