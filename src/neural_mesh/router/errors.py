"""Typed Cognitive Router errors (R0) — fail-closed, no silent fallback."""

from __future__ import annotations


class RouterError(Exception):
    """Base router error."""

    code: str = "ROUTER_ERROR"

    def __init__(self, message: str = "", *, code: str | None = None):
        super().__init__(message)
        if code is not None:
            self.code = code


class NoCapableNode(RouterError):
    """No eligible node after capability/availability/safety filters."""

    code = "ROUTER_NO_CAPABLE_NODE"

    def __init__(self, message: str = "no capable node", *, task_id: str | None = None):
        self.task_id = task_id
        prefix = f"no capable node for task {task_id}" if task_id else message
        super().__init__(prefix if task_id else message)


class SafetyPolicyBlocked(RouterError):
    """Task requires actions denied by SAFETY_POLICY."""

    code = "ROUTER_SAFETY_POLICY_BLOCKED"

    def __init__(
        self,
        message: str = "safety policy blocked",
        *,
        task_id: str | None = None,
        policy_key: str | None = None,
    ):
        self.task_id = task_id
        self.policy_key = policy_key
        detail = message
        if policy_key:
            detail = f"safety policy blocked ({policy_key})"
        if task_id:
            detail = f"{detail} for task {task_id}"
        super().__init__(detail)


class UnknownPolicy(RouterError):
    """Policy schema/key unknown — fail-closed (DeepSeek C8)."""

    code = "ROUTER_UNKNOWN_POLICY"

    def __init__(
        self,
        message: str = "unknown policy",
        *,
        detail: str | None = None,
    ):
        self.detail = detail
        super().__init__(detail or message)


class SaturationError(RouterError):
    """Inflight queue exceeded bound — reject, do not silent-drop."""

    code = "ROUTER_SATURATION_QUEUE_FULL"

    def __init__(
        self,
        message: str = "saturation queue full",
        *,
        queue_bound: int | None = None,
        inflight: int | None = None,
    ):
        self.queue_bound = queue_bound
        self.inflight = inflight
        super().__init__(message)


class CramPersistError(RouterError):
    """C-RAM persist ack missing/failed — no RouteDecision may be emitted (C9).

    Phantom-decision guard: a decision returned to the caller without a durable
    C-RAM ack is forbidden. Callers must treat this as typed fail-closed ERROR.
    """

    code = "ROUTER_CRAM_PERSIST_FAILED"

    def __init__(
        self,
        message: str = "C-RAM persist ack failed",
        *,
        op_id: str | None = None,
        trace_id: str | None = None,
        cause: str | None = None,
    ):
        self.op_id = op_id
        self.trace_id = trace_id
        self.cause = cause
        parts = [message]
        if op_id:
            parts.append(f"op_id={op_id}")
        if trace_id:
            parts.append(f"trace_id={trace_id}")
        if cause:
            parts.append(f"cause={cause}")
        super().__init__("; ".join(parts))




class CapabilityNoMatch(RouterError):
    """No node matched capability requirements (R1 fail-closed; never silent RR)."""

    code = "ROUTER_CAPABILITY_NO_MATCH"

    def __init__(
        self,
        message: str = "capability no match",
        *,
        task_id: str | None = None,
    ):
        self.task_id = task_id
        detail = message
        if task_id:
            detail = f"capability no match for task {task_id}"
        super().__init__(detail)


class StaleCapability(RouterError):
    """Capability advertisement expired past TTL — must not be routed to."""

    code = "ROUTER_STALE_CAPABILITY"

    def __init__(
        self,
        message: str = "stale capability",
        *,
        node_id: str | None = None,
        advertised_at_ms: int | None = None,
        ttl_ms: int | None = None,
        now_ms: int | None = None,
    ):
        self.node_id = node_id
        self.advertised_at_ms = advertised_at_ms
        self.ttl_ms = ttl_ms
        self.now_ms = now_ms
        parts = [message]
        if node_id:
            parts.append(f"node_id={node_id}")
        super().__init__("; ".join(parts))


class UnknownCapabilitySchema(RouterError):
    """Capability schema version/key unknown — fail-closed."""

    code = "ROUTER_UNKNOWN_CAPABILITY_SCHEMA"

    def __init__(
        self,
        message: str = "unknown capability schema",
        *,
        detail: str | None = None,
    ):
        self.detail = detail
        super().__init__(detail or message)

__all__ = [
    "CapabilityNoMatch",
    "CramPersistError",
    "NoCapableNode",
    "RouterError",
    "SafetyPolicyBlocked",
    "SaturationError",
    "StaleCapability",
    "UnknownCapabilitySchema",
    "UnknownPolicy",
]
