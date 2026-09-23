"""Conflict detection & deterministic resolution — Phase 5B (no silent LWW)."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any

from .models import utc_now
from .version import CRAMVersion, compare_versions


class ConflictOutcome(str, Enum):
    IDEMPOTENT = "IDEMPOTENT"
    CONFLICT = "CONFLICT"
    REJECTED_STALE_EPOCH = "REJECTED_STALE_EPOCH"
    ACCEPTED = "ACCEPTED"


class ConflictPolicy(str, Enum):
    """How to handle an explicit hash conflict once detected."""

    CONFLICT_REJECT = "CONFLICT_REJECT"
    CONFLICT_RESOLVE_DETERMINISTIC = "CONFLICT_RESOLVE_DETERMINISTIC"


@dataclass
class ConflictRecord:
    """Auditable conflict / compare outcome — never silent."""

    object_id: str
    outcome: ConflictOutcome
    existing: dict[str, Any] | None
    incoming: dict[str, Any]
    resolved: dict[str, Any] | None = None
    reason: str = ""
    recorded_at: str = field(default_factory=utc_now)
    detail: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["outcome"] = (
            self.outcome.value if isinstance(self.outcome, ConflictOutcome) else self.outcome
        )
        return d


def classify_write(
    existing: CRAMVersion | None,
    incoming: CRAMVersion,
) -> ConflictOutcome:
    """Classify an incoming version against the current stored version."""
    if existing is None:
        return ConflictOutcome.ACCEPTED
    if incoming.epoch < existing.epoch:
        return ConflictOutcome.REJECTED_STALE_EPOCH
    if existing.object_id == incoming.object_id and existing.hash == incoming.hash:
        return ConflictOutcome.IDEMPOTENT
    if existing.object_id == incoming.object_id and existing.hash != incoming.hash:
        # Same logical id, different content — conflict unless incoming is a
        # strictly newer epoch (post-promote rewrite of same key is still a
        # content change that must be audited as conflict-or-accept by policy).
        if incoming.epoch > existing.epoch:
            return ConflictOutcome.ACCEPTED
        if incoming.epoch == existing.epoch and incoming.sequence > existing.sequence:
            return ConflictOutcome.CONFLICT
        return ConflictOutcome.CONFLICT
    return ConflictOutcome.ACCEPTED


def resolve_deterministic(a: CRAMVersion, b: CRAMVersion) -> CRAMVersion:
    """Deterministic winner: higher epoch, then sequence, then lex greater hash.

    Always used with an accompanying ConflictRecord — never silent LWW.
    """
    cmp = compare_versions(a, b)
    if cmp > 0:
        return a
    if cmp < 0:
        return b
    # Tie on epoch+sequence → lex greater hash (stable, auditable)
    return a if a.hash >= b.hash else b


def record_conflict(
    existing: CRAMVersion | None,
    incoming: CRAMVersion,
    outcome: ConflictOutcome,
    *,
    resolved: CRAMVersion | None = None,
    reason: str = "",
    detail: dict[str, Any] | None = None,
) -> ConflictRecord:
    return ConflictRecord(
        object_id=incoming.object_id,
        outcome=outcome,
        existing=existing.to_dict() if existing else None,
        incoming=incoming.to_dict(),
        resolved=resolved.to_dict() if resolved else None,
        reason=reason,
        detail=dict(detail or {}),
    )


__all__ = [
    "ConflictOutcome",
    "ConflictPolicy",
    "ConflictRecord",
    "classify_write",
    "record_conflict",
    "resolve_deterministic",
]
