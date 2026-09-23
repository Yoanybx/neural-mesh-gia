"""Fault event model (ChatGPT Cycle-2/3 interface)."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from typing import Any

from .faults import (
    FAULT_NODE_LOSS,
    FAULT_PACKET_DELAY,
    FAULT_PACKET_DROP,
    SUPPORTED_FAULTS,
)


@dataclass(frozen=True)
class FaultEvent:
    """Deterministic fault injection event.

    Canonical fields (ChatGPT):
      event_id, fault_type, target_id, tick, seed, parameters

    NODE_LOSS: target_id is a node id; parameters.duration_ticks (-1 = permanent).
    PACKET_DROP: target_id is ``src->dst``; parameters.drop_rate in [0,1].
    PACKET_DELAY: target_id is ``src->dst``; parameters.delay_ticks / delay_ms.
    """

    event_id: str
    fault_type: str
    target_id: str
    tick: int
    seed: int = 0
    parameters: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.fault_type not in SUPPORTED_FAULTS:
            raise ValueError(f"unsupported fault_type: {self.fault_type}")
        if self.tick < 0:
            raise ValueError("tick must be >= 0")
        rate = float(self.parameters.get("drop_rate", 1.0))
        if not (0.0 <= rate <= 1.0):
            raise ValueError("drop_rate must be in [0, 1]")

    # --- compatibility aliases used by older Cycle-2 call sites ---
    @property
    def at_tick(self) -> int:
        return self.tick

    @property
    def target(self) -> str:
        return self.target_id

    @property
    def drop_rate(self) -> float:
        return float(self.parameters.get("drop_rate", 1.0))

    @property
    def duration_ticks(self) -> int:
        return int(self.parameters.get("duration_ticks", -1))

    @property
    def delay_ticks(self) -> int:
        return int(self.parameters.get("delay_ticks", 0))

    @property
    def delay_ms(self) -> float:
        return float(self.parameters.get("delay_ms", 0.0))

    def to_dict(self) -> dict[str, Any]:
        return {
            "event_id": self.event_id,
            "fault_type": self.fault_type,
            "target_id": self.target_id,
            "tick": self.tick,
            "seed": self.seed,
            "parameters": dict(self.parameters),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> FaultEvent:
        # Accept ChatGPT schema and Cycle-2 legacy keys.
        if "target_id" in data or "event_id" in data:
            params = dict(data.get("parameters") or {})
            # Promote legacy flat keys into parameters if present.
            for key in ("drop_rate", "duration_ticks", "delay_ticks", "delay_ms"):
                if key in data and key not in params:
                    params[key] = data[key]
            return cls(
                event_id=str(data.get("event_id") or _auto_event_id(data)),
                fault_type=str(data["fault_type"]),
                target_id=str(data.get("target_id") or data.get("target", "")),
                tick=int(data.get("tick", data.get("at_tick", 0))),
                seed=int(data.get("seed", 0)),
                parameters=params,
            )
        # Pure legacy {fault_type, at_tick, target, ...}
        params: dict[str, Any] = {}
        if "drop_rate" in data:
            params["drop_rate"] = data["drop_rate"]
        if "duration_ticks" in data:
            params["duration_ticks"] = data["duration_ticks"]
        if "delay_ticks" in data:
            params["delay_ticks"] = data["delay_ticks"]
        if "delay_ms" in data:
            params["delay_ms"] = data["delay_ms"]
        return cls(
            event_id=str(data.get("event_id") or _auto_event_id(data)),
            fault_type=str(data["fault_type"]),
            target_id=str(data["target"]),
            tick=int(data["at_tick"]),
            seed=int(data.get("seed", 0)),
            parameters=params,
        )

    @classmethod
    def create(
        cls,
        fault_type: str,
        target: str,
        *,
        at_tick: int = 0,
        tick: int | None = None,
        event_id: str | None = None,
        seed: int = 0,
        drop_rate: float = 1.0,
        duration_ticks: int = -1,
        delay_ticks: int = 0,
        delay_ms: float = 0.0,
        parameters: dict[str, Any] | None = None,
    ) -> FaultEvent:
        """Convenience constructor (legacy-friendly kwargs)."""
        t = int(tick if tick is not None else at_tick)
        params = dict(parameters or {})
        if fault_type == FAULT_PACKET_DROP:
            params.setdefault("drop_rate", drop_rate)
        if fault_type == FAULT_NODE_LOSS:
            params.setdefault("duration_ticks", duration_ticks)
        if fault_type == FAULT_PACKET_DELAY:
            params.setdefault("delay_ticks", delay_ticks)
            params.setdefault("delay_ms", delay_ms)
        elif duration_ticks != -1:
            params.setdefault("duration_ticks", duration_ticks)
        payload = {
            "fault_type": fault_type,
            "target_id": target,
            "tick": t,
            "seed": seed,
            "parameters": params,
        }
        eid = event_id or _auto_event_id(payload)
        return cls(
            event_id=eid,
            fault_type=fault_type,
            target_id=target,
            tick=t,
            seed=seed,
            parameters=params,
        )


def _auto_event_id(data: dict[str, Any]) -> str:
    blob = repr(
        (
            data.get("fault_type"),
            data.get("target_id") or data.get("target"),
            data.get("tick", data.get("at_tick")),
            data.get("seed", 0),
            data.get("parameters") or {},
        )
    ).encode()
    return "fault-" + hashlib.sha256(blob).hexdigest()[:8]


def faults_to_legacy_dicts(events: list[FaultEvent]) -> list[dict[str, Any]]:
    """Cycle-2 style dicts for digest / report compatibility."""
    out = []
    for f in sorted(events, key=lambda e: (e.tick, e.fault_type, e.target_id, e.event_id)):
        d: dict[str, Any] = {
            "fault_type": f.fault_type,
            "at_tick": f.tick,
            "target": f.target_id,
            "drop_rate": f.drop_rate,
            "duration_ticks": f.duration_ticks,
            "event_id": f.event_id,
            "seed": f.seed,
            "parameters": dict(f.parameters),
        }
        out.append(d)
    return out
