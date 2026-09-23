"""C-RAM object model — states/data/refs/results/evidence/artifacts only."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, field_validator


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class ObjectType(str, Enum):
    """Allowed C-RAM object kinds (no free-text private thoughts)."""

    STATE = "STATE"
    MEMORY = "MEMORY"
    TASK = "TASK"
    PLAN = "PLAN"
    EVIDENCE = "EVIDENCE"
    CHECKPOINT = "CHECKPOINT"


# Metadata keys that look like free-text private thoughts — reject on put_object.
FORBIDDEN_METADATA_KEYS = frozenset(
    {
        "private_thoughts",
        "private_thought",
        "inner_monologue",
        "secret_thoughts",
        "stream_of_consciousness",
    }
)


class CRAMObject(BaseModel):
    """Content-addressed mesh object descriptor (identity + refs + typed metadata)."""

    id: str
    object_type: ObjectType
    content_hash: str
    parent_refs: list[str] = Field(default_factory=list)
    created_at: str = Field(default_factory=utc_now)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("metadata")
    @classmethod
    def _no_private_thoughts(cls, v: dict[str, Any]) -> dict[str, Any]:
        bad = FORBIDDEN_METADATA_KEYS.intersection(v.keys())
        if bad:
            raise ValueError(
                "C-RAM must not store free-text private thoughts; "
                f"forbidden metadata keys: {sorted(bad)}"
            )
        return v

    def to_dict(self) -> dict[str, Any]:
        return self.model_dump(mode="json")
