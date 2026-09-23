"""Phase 3 Cognitive Router — R0 deterministic Round-Robin (+ safety filters)."""

from .audit import AuditRecord, AuditTrail, audit_from_decision, decision_hash
from .errors import (
    CramPersistError,
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
from .router import (
    CognitiveRouterR0,
    candidates_from_topology,
    explain_decision,
    replay_from_store,
)
from .strategy import CapabilityAwareStrategy, RoundRobinStrategy, RoutingStrategy
from .trace import (
    build_replay_envelope,
    ensure_trace_id,
    new_trace_id,
    trace_id_consistent,
)

__all__ = [
    "ALLOWED_POLICY_KEYS",
    "AuditRecord",
    "AuditTrail",
    "CapabilityAwareStrategy",
    "CognitiveRouterR0",
    "CramPersistError",
    "DecisionLog",
    "DecisionStatus",
    "DecisionStore",
    "NoCapableNode",
    "NodeAvailability",
    "POLICY_SCHEMA_VERSION",
    "RoundRobinStrategy",
    "RouteCandidate",
    "RouteDecision",
    "RouterError",
    "RoutingStrategy",
    "SafetyPolicyBlocked",
    "SaturationError",
    "TaskSpec",
    "UnknownPolicy",
    "audit_from_decision",
    "build_replay_envelope",
    "candidates_fingerprint",
    "candidates_from_topology",
    "decision_hash",
    "ensure_trace_id",
    "explain_decision",
    "new_trace_id",
    "normalize_policy",
    "percentile",
    "policy_hash",
    "replay_from_store",
    "resolve_policy",
    "safety_block_reason",
    "summarize_decisions",
    "trace_id_consistent",
]
