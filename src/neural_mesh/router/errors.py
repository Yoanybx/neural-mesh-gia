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


__all__ = [
    "NoCapableNode",
    "RouterError",
    "SafetyPolicyBlocked",
    "SaturationError",
    "UnknownPolicy",
]
