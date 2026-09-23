"""Decision audit trail for Cognitive Router R0 (Cycle 9)."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import Any

from .models import RouteDecision, utc_now


def decision_hash(decision: RouteDecision) -> str:
    """SHA-256 of canonical RouteDecision bytes (reproducible)."""
    return hashlib.sha256(decision.canonical_bytes()).hexdigest()


@dataclass
class AuditRecord:
    """Full audit row for one RouteDecision (ChatGPT C8/C9 P0)."""

    task_id: str
    op_id: str
    epoch: int
    trace_id: str
    policy_hash: str
    candidates_fingerprint: str
    selected_node: str | None
    rejection_reasons: list[str] = field(default_factory=list)
    logical_timestamp: int = 0
    decision_hash: str = ""
    status: str = ""
    reason: str = ""
    wall_timestamp: str = field(default_factory=utc_now)

    def to_dict(self) -> dict[str, Any]:
        return {
            "task_id": self.task_id,
            "op_id": self.op_id,
            "epoch": int(self.epoch),
            "trace_id": self.trace_id,
            "policy_hash": self.policy_hash,
            "candidates_fingerprint": self.candidates_fingerprint,
            "selected_node": self.selected_node,
            "rejection_reasons": list(self.rejection_reasons),
            "logical_timestamp": int(self.logical_timestamp),
            "decision_hash": self.decision_hash,
            "status": self.status,
            "reason": self.reason,
            "wall_timestamp": self.wall_timestamp,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> AuditRecord:
        return cls(
            task_id=str(data.get("task_id", "")),
            op_id=str(data.get("op_id", "")),
            epoch=int(data.get("epoch", 0)),
            trace_id=str(data.get("trace_id", "")),
            policy_hash=str(data.get("policy_hash", "")),
            candidates_fingerprint=str(data.get("candidates_fingerprint", "")),
            selected_node=data.get("selected_node"),
            rejection_reasons=list(data.get("rejection_reasons", [])),
            logical_timestamp=int(data.get("logical_timestamp", 0)),
            decision_hash=str(data.get("decision_hash", "")),
            status=str(data.get("status", "")),
            reason=str(data.get("reason", "")),
            wall_timestamp=str(data.get("wall_timestamp", utc_now())),
        )


def audit_from_decision(
    decision: RouteDecision, *, logical_timestamp: int = 0
) -> AuditRecord:
    """Build AuditRecord from a committed RouteDecision."""
    reasons: list[str] = []
    if decision.reason:
        reasons.append(decision.reason)
    for ex in decision.excluded:
        r = ex.get("reason")
        if r and r not in reasons:
            reasons.append(str(r))
    status = (
        decision.status.value
        if hasattr(decision.status, "value")
        else str(decision.status)
    )
    return AuditRecord(
        task_id=decision.task_id,
        op_id=decision.op_id,
        epoch=int(decision.epoch),
        trace_id=decision.trace_id,
        policy_hash=decision.policy_hash,
        candidates_fingerprint=decision.candidates_fingerprint,
        selected_node=decision.selected_node_id,
        rejection_reasons=reasons,
        logical_timestamp=int(logical_timestamp),
        decision_hash=decision_hash(decision),
        status=status,
        reason=decision.reason,
        wall_timestamp=decision.timestamp or utc_now(),
    )


class AuditTrail:
    """In-memory + optional JSONL audit sink (separate from DecisionLog)."""

    def __init__(self, path: str | None = None):
        from pathlib import Path

        self.path = Path(path) if path else None
        self._rows: list[AuditRecord] = []
        self._logical = 0
        if self.path is not None:
            self.path.parent.mkdir(parents=True, exist_ok=True)

    def record(self, decision: RouteDecision) -> AuditRecord:
        self._logical += 1
        row = audit_from_decision(decision, logical_timestamp=self._logical)
        self._rows.append(row)
        if self.path is not None:
            with self.path.open("a", encoding="utf-8") as f:
                f.write(json.dumps(row.to_dict(), sort_keys=True) + "\n")
                f.flush()
        return row

    def by_trace_id(self, trace_id: str) -> list[AuditRecord]:
        return [r for r in self._rows if r.trace_id == trace_id]

    def by_op_id(self, op_id: str) -> AuditRecord | None:
        for r in reversed(self._rows):
            if r.op_id == op_id:
                return r
        return None

    def __len__(self) -> int:
        return len(self._rows)


__all__ = [
    "AuditRecord",
    "AuditTrail",
    "audit_from_decision",
    "decision_hash",
]
