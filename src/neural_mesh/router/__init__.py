"""Phase 3 Cognitive Router — R0 Round-Robin + R1 Capability-aware."""

from .audit import AuditRecord, AuditTrail, audit_from_decision, decision_hash
from .capabilities import (
    CAPABILITY_SCHEMA_VERSION,
    DEFAULT_CAP_TTL_MS,
    T_CONV_CAPABILITY_S,
    CapabilityRegistry,
    NodeCapability,
    cap_state_fingerprint,
    validate_capability,
)
from .errors import (
    CapabilityNoMatch,
    CramPersistError,
    NoCapableNode,
    RouterError,
    SafetyPolicyBlocked,
    SaturationError,
    StaleCapability,
    UnknownCapabilitySchema,
    UnknownPolicy,
)
from .scoring import score_node
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
    "CAPABILITY_SCHEMA_VERSION",
    "CapabilityAwareStrategy",
    "CapabilityNoMatch",
    "CapabilityRegistry",
    "CognitiveRouterR0",
    "CramPersistError",
    "DEFAULT_CAP_TTL_MS",
    "DecisionLog",
    "DecisionStatus",
    "DecisionStore",
    "NoCapableNode",
    "NodeAvailability",
    "NodeCapability",
    "POLICY_SCHEMA_VERSION",
    "RoundRobinStrategy",
    "RouteCandidate",
    "RouteDecision",
    "RouterError",
    "RoutingStrategy",
    "SafetyPolicyBlocked",
    "SaturationError",
    "StaleCapability",
    "T_CONV_CAPABILITY_S",
    "TaskSpec",
    "UnknownCapabilitySchema",
    "UnknownPolicy",
    "audit_from_decision",
    "build_replay_envelope",
    "cap_state_fingerprint",
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
    "score_node",
    "summarize_decisions",
    "trace_id_consistent",
    "validate_capability",
]
