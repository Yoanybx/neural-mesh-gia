"""Mesh OBS telemetry contract (Cycle 37 / CP-0041 / H4).

Schema: mesh.obs/v1
Capability: docs/capabilities/MESH_OBS_TELEMETRY.md
CLI: mesh obs telemetry|validate|schema
ABORT→block CP mint on schema/invariant breach.
"""

from .models import (
    CADENCE_TIERS,
    REQUIRED_TOP_FIELDS,
    SCHEMA_ADVERSARY,
    SCHEMA_ID,
    SCHEMA_SIGNALS,
    SCHEMA_WINDOW,
    SOURCE_SNAPSHOT_SCHEMA,
    ObsAbortBlockCp,
    ObsAdversary,
    ObsCadenceInvalid,
    ObsError,
    ObsInvariantBreach,
    ObsN2Only,
    ObsPlaintextForbidden,
    ObsSchemaMismatch,
    ObsSignals,
    ObsWindow,
    TelemetryDocument,
    schema_descriptor,
)
from .contract import (
    emit_from_snapshot,
    emit_telemetry,
    format_telemetry_m2m,
    require_no_plaintext,
    telemetry_to_json,
    validate_dict,
    validate_telemetry,
)
from .cli_ops import cmd_obs_schema, cmd_obs_telemetry, cmd_obs_validate

__all__ = [
    "CADENCE_TIERS",
    "REQUIRED_TOP_FIELDS",
    "SCHEMA_ADVERSARY",
    "SCHEMA_ID",
    "SCHEMA_SIGNALS",
    "SCHEMA_WINDOW",
    "SOURCE_SNAPSHOT_SCHEMA",
    "ObsAbortBlockCp",
    "ObsAdversary",
    "ObsCadenceInvalid",
    "ObsError",
    "ObsInvariantBreach",
    "ObsN2Only",
    "ObsPlaintextForbidden",
    "ObsSchemaMismatch",
    "ObsSignals",
    "ObsWindow",
    "TelemetryDocument",
    "cmd_obs_schema",
    "cmd_obs_telemetry",
    "cmd_obs_validate",
    "emit_from_snapshot",
    "emit_telemetry",
    "format_telemetry_m2m",
    "require_no_plaintext",
    "schema_descriptor",
    "telemetry_to_json",
    "validate_dict",
    "validate_telemetry",
]
