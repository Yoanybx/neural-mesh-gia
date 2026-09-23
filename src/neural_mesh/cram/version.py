"""CRAMVersion — explicit object versioning for Phase 5B consistency."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from .models import utc_now


@dataclass(frozen=True)
class CRAMVersion:
    """Monotonic version identity for a C-RAM object.

    Rules (see docs/phase5b_consistency.md):
    - same object_id + same hash → idempotent
    - same object_id + different hash → explicit conflict
    - lesser epoch → reject
    """

    object_id: str
    epoch: int
    sequence: int
    hash: str
    timestamp: str
    origin_node: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "CRAMVersion":
        return cls(
            object_id=str(data["object_id"]),
            epoch=int(data["epoch"]),
            sequence=int(data["sequence"]),
            hash=str(data["hash"]),
            timestamp=str(data.get("timestamp") or utc_now()),
            origin_node=str(data["origin_node"]),
        )

    def dominates(self, other: "CRAMVersion") -> bool:
        """True if self is strictly newer by (epoch, sequence)."""
        if self.epoch != other.epoch:
            return self.epoch > other.epoch
        return self.sequence > other.sequence

    def same_content(self, other: "CRAMVersion") -> bool:
        return self.object_id == other.object_id and self.hash == other.hash


def compare_versions(a: CRAMVersion, b: CRAMVersion) -> int:
    """Return -1 if a < b, 0 if equal position, 1 if a > b (epoch, then sequence)."""
    if a.epoch != b.epoch:
        return -1 if a.epoch < b.epoch else 1
    if a.sequence != b.sequence:
        return -1 if a.sequence < b.sequence else 1
    return 0


__all__ = ["CRAMVersion", "compare_versions"]
