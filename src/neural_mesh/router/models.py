"""P0 Cognitive Router R0 contract: TaskSpec, RouteCandidate, RouteDecision."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class NodeAvailability(str, Enum):
    AVAILABLE = "AVAILABLE"
    UNAVAILABLE = "UNAVAILABLE"


class DecisionStatus(str, Enum):
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"


@dataclass(frozen=True)
class TaskSpec:
    """Declarative task for R0 routing (no execution).

    Cycle 6/8 core fields + DeepSeek audit fields (op_id, trace_id) +
    optional Cycle 7 ChatGPT extensions. R0 Round-Robin does not score
    priority yet (R1+).
    """

    task_id: str
    required_capabilities: tuple[str, ...] = ("compute",)
    requires_network: bool = False
    requires_physical: bool = False
    payload_hint: str = ""
    objective: str = ""
    priority: int = 0
    resource_requirements: dict[str, Any] = field(default_factory=dict)
    safety_level: str = "default"
    state_refs: tuple[str, ...] = ()
    op_id: str = ""
    trace_id: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "task_id": self.task_id,
            "required_capabilities": list(self.required_capabilities),
            "requires_network": bool(self.requires_network),
            "requires_physical": bool(self.requires_physical),
            "payload_hint": self.payload_hint,
            "objective": self.objective,
            "priority": int(self.priority),
            "resource_requirements": dict(self.resource_requirements),
            "safety_level": self.safety_level,
            "state_refs": list(self.state_refs),
            "op_id": self.op_id,
            "trace_id": self.trace_id,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> TaskSpec:
        caps = data.get("required_capabilities") or data.get(
            "resource_requirements", {}
        ).get("capabilities", ["compute"])
        if isinstance(caps, dict):
            caps = caps.get("capabilities", ["compute"])
        rr = data.get("resource_requirements", {})
        if not isinstance(rr, dict):
            rr = {}
        return cls(
            task_id=str(data["task_id"]),
            required_capabilities=tuple(str(c) for c in caps),
            requires_network=bool(data.get("requires_network", False)),
            requires_physical=bool(data.get("requires_physical", False)),
            payload_hint=str(data.get("payload_hint", "")),
            objective=str(data.get("objective", "")),
            priority=int(data.get("priority", 0)),
            resource_requirements=dict(rr),
            safety_level=str(data.get("safety_level", "default")),
            state_refs=tuple(str(x) for x in data.get("state_refs", [])),
            op_id=str(data.get("op_id", "")),
            trace_id=str(data.get("trace_id", "")),
        )


@dataclass(frozen=True)
class RouteCandidate:
    """A mesh node that may receive work."""

    node_id: str
    capabilities: tuple[str, ...] = ("compute",)
    status: NodeAvailability = NodeAvailability.AVAILABLE
    cpu: int = 0
    memory: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "node_id": self.node_id,
            "capabilities": list(self.capabilities),
            "status": self.status.value
            if isinstance(self.status, NodeAvailability)
            else str(self.status),
            "cpu": int(self.cpu),
            "memory": int(self.memory),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> RouteCandidate:
        status_raw = data.get("status", NodeAvailability.AVAILABLE.value)
        if isinstance(status_raw, NodeAvailability):
            status = status_raw
        else:
            status = NodeAvailability(str(status_raw))
        caps = data.get("capabilities", ["compute"])
        return cls(
            node_id=str(data["node_id"]),
            capabilities=tuple(str(c) for c in caps),
            status=status,
            cpu=int(data.get("cpu", 0)),
            memory=int(data.get("memory", 0)),
        )


def candidates_fingerprint(candidates: list[RouteCandidate]) -> str:
    payload = [c.to_dict() for c in sorted(candidates, key=lambda x: x.node_id)]
    blob = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()


@dataclass
class RouteDecision:
    """Deterministic routing outcome with reasons, metrics, and audit stamps."""

    task_id: str
    status: DecisionStatus
    reason: str
    selected_node_id: str | None
    candidates_considered: list[str] = field(default_factory=list)
    eligible: list[str] = field(default_factory=list)
    excluded: list[dict[str, str]] = field(default_factory=list)
    metrics: dict[str, Any] = field(default_factory=dict)
    seed: int = 0
    timestamp: str = field(default_factory=utc_now)
    policy_hash: str = ""
    op_id: str = ""
    epoch: int = 0
    trace_id: str = ""
    candidates_fingerprint: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "task_id": self.task_id,
            "status": self.status.value
            if isinstance(self.status, DecisionStatus)
            else str(self.status),
            "reason": self.reason,
            "selected_node_id": self.selected_node_id,
            "candidates_considered": list(self.candidates_considered),
            "eligible": list(self.eligible),
            "excluded": [dict(x) for x in self.excluded],
            "metrics": dict(self.metrics),
            "seed": int(self.seed),
            "timestamp": self.timestamp,
            "policy_hash": self.policy_hash,
            "op_id": self.op_id,
            "epoch": int(self.epoch),
            "trace_id": self.trace_id,
            "candidates_fingerprint": self.candidates_fingerprint,
        }

    def canonical_dict(self) -> dict[str, Any]:
        """Determinism payload: excludes volatile timestamp/latency."""
        d = self.to_dict()
        d.pop("timestamp", None)
        metrics = dict(d.get("metrics") or {})
        metrics.pop("decision_latency_ms", None)
        d["metrics"] = metrics
        return d

    def canonical_bytes(self) -> bytes:
        return json.dumps(
            self.canonical_dict(), sort_keys=True, separators=(",", ":")
        ).encode("utf-8")

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> RouteDecision:
        status_raw = data.get("status", DecisionStatus.REJECTED.value)
        if isinstance(status_raw, DecisionStatus):
            status = status_raw
        else:
            status = DecisionStatus(str(status_raw))
        return cls(
            task_id=str(data["task_id"]),
            status=status,
            reason=str(data.get("reason", "")),
            selected_node_id=data.get("selected_node_id"),
            candidates_considered=list(data.get("candidates_considered", [])),
            eligible=list(data.get("eligible", [])),
            excluded=[dict(x) for x in data.get("excluded", [])],
            metrics=dict(data.get("metrics", {})),
            seed=int(data.get("seed", 0)),
            timestamp=str(data.get("timestamp", utc_now())),
            policy_hash=str(data.get("policy_hash", "")),
            op_id=str(data.get("op_id", "")),
            epoch=int(data.get("epoch", 0)),
            trace_id=str(data.get("trace_id", "")),
            candidates_fingerprint=str(data.get("candidates_fingerprint", "")),
        )


__all__ = [
    "DecisionStatus",
    "NodeAvailability",
    "RouteCandidate",
    "RouteDecision",
    "TaskSpec",
    "asdict",
    "candidates_fingerprint",
    "utc_now",
]
