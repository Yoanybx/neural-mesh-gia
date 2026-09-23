"""RoutingStrategy interface — RoundRobin live; CapabilityAware STUB (Cycle 9).

R1 is NOT activated. CapabilityAwareStrategy exists only as a typed stub so
Cycle 10+ can plug in without changing the R0 determinism contract.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Sequence

from .models import RouteCandidate, TaskSpec


class RoutingStrategy(ABC):
    """Select one eligible candidate (or None) for a task."""

    name: str = "abstract"

    @abstractmethod
    def select(
        self, task: TaskSpec, candidates: Sequence[RouteCandidate]
    ) -> tuple[RouteCandidate | None, int | None]:
        """Return (chosen, pick_index) or (None, None) if empty."""


class RoundRobinStrategy(RoutingStrategy):
    """Deterministic Round-Robin over eligible candidates (R0 live)."""

    name = "ROUND_ROBIN"

    def __init__(self, *, index: int = 0):
        self.index = int(index)

    def select(
        self, task: TaskSpec, candidates: Sequence[RouteCandidate]
    ) -> tuple[RouteCandidate | None, int | None]:
        if not candidates:
            return None, None
        pick = self.index % len(candidates)
        return candidates[pick], pick

    def advance(self) -> None:
        self.index += 1


class CapabilityAwareStrategy(RoutingStrategy):
    """STUB — R1 capability-aware scoring is NOT implemented / NOT activated."""

    name = "CAPABILITY_AWARE_STUB"
    STUB = True

    def select(
        self, task: TaskSpec, candidates: Sequence[RouteCandidate]
    ) -> tuple[RouteCandidate | None, int | None]:
        raise NotImplementedError(
            "CapabilityAwareStrategy is a Cycle 9 STUB only; R1 not activated"
        )


__all__ = [
    "CapabilityAwareStrategy",
    "RoundRobinStrategy",
    "RoutingStrategy",
]
