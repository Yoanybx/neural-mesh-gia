"""Mesh manifest parity @N2 (Cycle 41 / CP-0045 / H8).

Schema: mesh.manifest.parity/v1
Capability: docs/capabilities/MESH_MANIFEST_PARITY.md
CLI: mesh parity status|check|build-check
ABORT→reject build on byte-inequality under concurrent build.
Extends packaging/manifest_n2 — does not reopen 0.16.3 / 0.17.0.
"""

from .models import (
    FROZEN_CHANNELS,
    PARITY_CHANNEL,
    SCHEMA_BUILD,
    SCHEMA_ID,
    SCHEMA_REPORT,
    SCHEMA_STORE,
    SCHEMA_TOOLCHAIN,
    SOURCE_MANIFEST_SCHEMA,
    SOURCE_MANIFEST_SCHEMA_N2,
    BuildArtifact,
    ConcurrentBuildResult,
    ParityAbortRejectBuild,
    ParityCheckResult,
    ParityError,
    ParityFrozenChannel,
    ParityIncomplete,
    ParityMismatch,
    ParityN2Only,
    ParityPlaintextForbidden,
    ParityStatus,
    ParityToolchainMismatch,
    ToolchainPin,
)
from .service import (
    CORE_PARITY_CANDIDATES,
    ParityService,
    canonical_manifest_bytes,
    compare_checksum_maps,
    compute_toolchain_pin,
    core_parity_checksums,
)
from .store import ParityStore, require_no_plaintext
from .cli_ops import (
    cmd_parity_build_check,
    cmd_parity_check,
    cmd_parity_status,
)

__all__ = [
    "CORE_PARITY_CANDIDATES",
    "FROZEN_CHANNELS",
    "PARITY_CHANNEL",
    "SCHEMA_BUILD",
    "SCHEMA_ID",
    "SCHEMA_REPORT",
    "SCHEMA_STORE",
    "SCHEMA_TOOLCHAIN",
    "SOURCE_MANIFEST_SCHEMA",
    "SOURCE_MANIFEST_SCHEMA_N2",
    "BuildArtifact",
    "ConcurrentBuildResult",
    "ParityAbortRejectBuild",
    "ParityCheckResult",
    "ParityError",
    "ParityFrozenChannel",
    "ParityIncomplete",
    "ParityMismatch",
    "ParityN2Only",
    "ParityPlaintextForbidden",
    "ParityService",
    "ParityStatus",
    "ParityStore",
    "ParityToolchainMismatch",
    "ToolchainPin",
    "canonical_manifest_bytes",
    "cmd_parity_build_check",
    "cmd_parity_check",
    "cmd_parity_status",
    "compare_checksum_maps",
    "compute_toolchain_pin",
    "core_parity_checksums",
    "require_no_plaintext",
]
