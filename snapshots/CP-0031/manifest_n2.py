"""N=2 bundle manifest schema: mesh.bundle.manifest/v1-n2 (CP-0031 / Cycle 27).

Sibling of frozen single-node ``mesh.bundle.manifest/v1`` — does not mutate v1.
"""

from __future__ import annotations

import json
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from .manifest import PytestSummary

SCHEMA_ID_N2 = "mesh.bundle.manifest/v1-n2"
SCHEMA_ID_SINGLE_FROZEN = "mesh.bundle.manifest/v1"
FREEZE_CHANNEL_N2 = "0.17.x-n2"
DEFAULT_BUNDLE_NAME_N2 = "neural-mesh-gia-n2"
TOPOLOGY_N2: Literal["n2"] = "n2"
ROLES_N2: tuple[str, ...] = ("primary", "secondary")
MAJORITY_FENCED = "fenced_primary_heal"

__all__ = [
    "SCHEMA_ID_N2",
    "SCHEMA_ID_SINGLE_FROZEN",
    "FREEZE_CHANNEL_N2",
    "DEFAULT_BUNDLE_NAME_N2",
    "TOPOLOGY_N2",
    "ROLES_N2",
    "MAJORITY_FENCED",
    "PytestSummary",
    "N2EntrypointPair",
    "N2FreezeInfo",
    "N2BundleManifest",
    "n2_manifest_to_dict",
    "n2_manifest_to_json",
]


class N2EntrypointPair(BaseModel):
    """Primary/secondary console entrypoint pair (same CLI; role via stub config)."""

    model_config = ConfigDict(extra="forbid")

    primary: str = "mesh"
    secondary: str = "mesh"


class N2FreezeInfo(BaseModel):
    """N2 channel freeze metadata; records that single-node v1 stays frozen."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    channel: str = FREEZE_CHANNEL_N2
    schema_name: str = Field(default=SCHEMA_ID_N2, alias="schema")
    single_node_schema_frozen: str = SCHEMA_ID_SINGLE_FROZEN


class N2BundleManifest(BaseModel):
    """JSON-serializable N=2 multi-node bundle manifest (v1-n2).

    Required: name, ver, tip, cp_range, pytest, topology, roles, entrypoint,
    dual_primary (=0), majority, checksums.
    """

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    schema_name: str = Field(default=SCHEMA_ID_N2, alias="schema")
    name: str = DEFAULT_BUNDLE_NAME_N2
    ver: str
    tip: str | None = None
    cp_range: str
    pytest: PytestSummary = Field(default_factory=PytestSummary)
    topology: Literal["n2"] = "n2"
    roles: list[str] = Field(default_factory=lambda: list(ROLES_N2))
    entrypoint: N2EntrypointPair = Field(default_factory=N2EntrypointPair)
    dual_primary: int = 0
    majority: str = MAJORITY_FENCED
    checksums: dict[str, str] = Field(default_factory=dict)
    n2_extras: list[str] = Field(default_factory=list)
    core_parity_paths: list[str] = Field(default_factory=list)
    cp_tip: str | None = None
    created_utc: str | None = None
    files: list[str] = Field(default_factory=list)
    bundle_sha256: str | None = None
    freeze: N2FreezeInfo | None = None

    @field_validator("dual_primary")
    @classmethod
    def _dual_primary_must_be_zero(cls, v: int) -> int:
        if v != 0:
            raise ValueError("dual_primary must remain 0 (no multi-primary)")
        return v

    @field_validator("roles")
    @classmethod
    def _roles_must_be_n2(cls, v: list[str]) -> list[str]:
        if list(v) != list(ROLES_N2):
            raise ValueError(f"roles must be {list(ROLES_N2)}, got {v!r}")
        return v

    @field_validator("majority")
    @classmethod
    def _majority_fenced_not_raft(cls, v: str) -> str:
        if v != MAJORITY_FENCED:
            raise ValueError(
                f"majority must be {MAJORITY_FENCED!r} (NOT Raft); got {v!r}"
            )
        if "raft" in v.lower():
            raise ValueError("Raft majority is out of scope for N2 packaging")
        return v

    @field_validator("topology")
    @classmethod
    def _topology_n2_only(cls, v: str) -> str:
        if v != "n2":
            raise ValueError(f"topology must be 'n2' (N>2 held); got {v!r}")
        return v


def n2_manifest_to_dict(m: N2BundleManifest) -> dict[str, Any]:
    return m.model_dump(mode="json", by_alias=True)


def n2_manifest_to_json(m: N2BundleManifest, *, indent: int = 2) -> str:
    return json.dumps(n2_manifest_to_dict(m), indent=indent, sort_keys=True) + "\n"
