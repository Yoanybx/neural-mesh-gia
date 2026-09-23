"""SAFETY_POLICY helpers for Cognitive Router R0 — versioned, fail-closed."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from neural_mesh.safety import DEFAULT_POLICY, load_policy

from .errors import UnknownPolicy
from .models import TaskSpec

POLICY_SCHEMA_VERSION = 1
ALLOWED_POLICY_KEYS = frozenset(
    {
        "policy_schema_version",
        "allow_network_actions",
        "allow_physical_actions",
        "require_human_approval",
        "routing_strategy",  # Cycle 10: optional "rr" | "capability"
    }
)

ALLOWED_ROUTING_STRATEGIES = frozenset({"rr", "capability", "ROUND_ROBIN", "CAPABILITY_AWARE"})


def resolve_policy(
    policy: dict[str, Any] | None = None,
    *,
    root: Path | None = None,
) -> dict[str, Any]:
    """Return effective policy dict (defaults harden: network/physical denied)."""
    if policy is not None:
        return dict(policy)
    if root is not None:
        return load_policy(root)
    return dict(DEFAULT_POLICY)


def normalize_policy(policy: dict[str, Any]) -> dict[str, Any]:
    """Normalize for hashing; raises UnknownPolicy on unknown key/version."""
    unknown = sorted(set(policy.keys()) - ALLOWED_POLICY_KEYS)
    if unknown:
        raise UnknownPolicy(
            detail=f"unknown policy keys: {', '.join(unknown)}"
        )
    version = policy.get("policy_schema_version", POLICY_SCHEMA_VERSION)
    try:
        version_i = int(version)
    except (TypeError, ValueError) as exc:
        raise UnknownPolicy(detail=f"invalid policy_schema_version: {version!r}") from exc
    if version_i != POLICY_SCHEMA_VERSION:
        raise UnknownPolicy(
            detail=f"unsupported policy_schema_version: {version_i}"
        )
    out = {
        "policy_schema_version": POLICY_SCHEMA_VERSION,
        "allow_network_actions": bool(policy.get("allow_network_actions", False)),
        "allow_physical_actions": bool(policy.get("allow_physical_actions", False)),
        "require_human_approval": bool(policy.get("require_human_approval", True)),
    }
    if "routing_strategy" in policy:
        rs = str(policy.get("routing_strategy", "rr"))
        if rs not in ALLOWED_ROUTING_STRATEGIES:
            raise UnknownPolicy(detail=f"unknown routing_strategy: {rs!r}")
        # Canonicalize for stable hashing
        if rs in ("ROUND_ROBIN", "rr"):
            out["routing_strategy"] = "rr"
        else:
            out["routing_strategy"] = "capability"
    return out


def policy_hash(policy: dict[str, Any]) -> str:
    """SHA-256 of canonical normalized policy JSON."""
    norm = normalize_policy(policy)
    blob = json.dumps(norm, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()


def safety_block_reason(
    task: TaskSpec,
    policy: dict[str, Any],
) -> str | None:
    """Return rejection reason if SAFETY_POLICY blocks the task, else None.

    R0 never executes physical/external-network actions; it only refuses to
    route tasks that declare such requirements when policy denies them.
    """
    # Ensure we operate on a validated view (caller may already have normalized).
    try:
        pol = normalize_policy(policy)
    except UnknownPolicy:
        return "UNKNOWN_POLICY"
    if task.requires_network and pol.get("allow_network_actions") is not True:
        return "SAFETY_POLICY_BLOCKS_NETWORK"
    if task.requires_physical and pol.get("allow_physical_actions") is not True:
        return "SAFETY_POLICY_BLOCKS_PHYSICAL"
    return None


__all__ = [
    "ALLOWED_POLICY_KEYS",
    "ALLOWED_ROUTING_STRATEGIES",
    "POLICY_SCHEMA_VERSION",
    "normalize_policy",
    "policy_hash",
    "resolve_policy",
    "safety_block_reason",
]
