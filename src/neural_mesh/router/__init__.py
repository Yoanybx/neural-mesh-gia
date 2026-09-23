"""Phase 3 Cognitive Router — R0 deterministic Round-Robin (+ safety filters)."""

from .errors import (
    NoCapableNode,
    RouterError,
    SafetyPolicyBlocked,
    SaturationError,
    UnknownPolicy,
)
from .log import DecisionLog
from .metrics import percentile, summarize_decisions
from .models import (
    DecisionStatus,
    NodeAvailability,
    RouteCandidate,
    RouteDecision,
    TaskSpec,
    candidates_fingerprint,
)
from .persist import DecisionStore
from .policy import (
    ALLOWED_POLICY_KEYS,
    POLICY_SCHEMA_VERSION,
    normalize_policy,
    policy_hash,
    resolve_policy,
    safety_block_reason,
)
from .router import CognitiveRouterR0, candidates_from_topology, explain_decision

__all__ = [
    "ALLOWED_POLICY_KEYS",
    "CognitiveRouterR0",
    "DecisionLog",
    "DecisionStatus",
    "DecisionStore",
    "NoCapableNode",
    "NodeAvailability",
    "POLICY_SCHEMA_VERSION",
    "RouteCandidate",
    "RouteDecision",
    "RouterError",
    "SafetyPolicyBlocked",
    "SaturationError",
    "TaskSpec",
    "UnknownPolicy",
    "candidates_fingerprint",
    "candidates_from_topology",
    "explain_decision",
    "normalize_policy",
    "percentile",
    "policy_hash",
    "resolve_policy",
    "safety_block_reason",
    "summarize_decisions",
]
