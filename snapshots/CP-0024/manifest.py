"""Bundle manifest schema: mesh.bundle.manifest/v1."""

from __future__ import annotations

import json
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

SCHEMA_ID = "mesh.bundle.manifest/v1"

__all__ = [
    "SCHEMA_ID",
    "PytestSummary",
    "BundleManifest",
    "manifest_to_dict",
    "manifest_to_json",
]


class PytestSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    passed: int = 0
    failed: int = 0


class BundleManifest(BaseModel):
    """Stable, JSON-serializable single-node bundle manifest (v1).

    Required fields per DeepSeek CP-0024:
    name, ver, tip, cp_range, pytest, entrypoint, checksums.
    """

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    schema_name: str = Field(default=SCHEMA_ID, alias="schema")
    name: str
    ver: str
    tip: str | None = None
    cp_range: str
    pytest: PytestSummary = Field(default_factory=PytestSummary)
    entrypoint: str = "mesh"
    checksums: dict[str, str] = Field(default_factory=dict)
    # Optional advisory fields (still schema-stable).
    cp_tip: str | None = None
    created_utc: str | None = None
    files: list[str] = Field(default_factory=list)
    bundle_sha256: str | None = None


def manifest_to_dict(m: BundleManifest) -> dict[str, Any]:
    return m.model_dump(mode="json", by_alias=True)


def manifest_to_json(m: BundleManifest, *, indent: int = 2) -> str:
    return json.dumps(manifest_to_dict(m), indent=indent, sort_keys=True) + "\n"
