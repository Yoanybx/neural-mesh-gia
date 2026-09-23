"""Trace-id helpers and replay envelope for Cognitive Router R0 (Cycle 9)."""

from __future__ import annotations

import hashlib
import json
import uuid
from typing import Any

from .models import RouteCandidate, RouteDecision, TaskSpec


def new_trace_id() -> str:
    return uuid.uuid4().hex


def ensure_trace_id(task: TaskSpec, op_id: str) -> str:
    if task.trace_id:
        return task.trace_id
    return op_id or new_trace_id()


def trace_id_consistent(decision: RouteDecision, task: TaskSpec) -> bool:
    """True iff decision.trace_id matches task.trace_id when task set one."""
    if not task.trace_id:
        return bool(decision.trace_id)
    return decision.trace_id == task.trace_id


def build_replay_envelope(
    *,
    task: TaskSpec,
    candidates: list[RouteCandidate],
    policy: dict[str, Any] | None,
    seed: int,
    epoch: int,
    rr_index_before: int,
    decision: RouteDecision,
) -> dict[str, Any]:
    """Inputs required to recompute RouteDecision byte-identically."""
    return {
        "task": task.to_dict(),
        "candidates": [c.to_dict() for c in candidates],
        "policy": dict(policy) if policy else None,
        "seed": int(seed),
        "epoch": int(epoch),
        "rr_index_before": int(rr_index_before),
        "decision_canonical_hash": hashlib.sha256(
            decision.canonical_bytes()
        ).hexdigest(),
        "trace_id": decision.trace_id,
        "op_id": decision.op_id,
    }


def envelope_fingerprint(envelope: dict[str, Any]) -> str:
    blob = json.dumps(envelope, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()


__all__ = [
    "build_replay_envelope",
    "ensure_trace_id",
    "envelope_fingerprint",
    "new_trace_id",
    "trace_id_consistent",
]
