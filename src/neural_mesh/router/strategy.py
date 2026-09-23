"""RoutingStrategy interface — RoundRobin + CapabilityAware (R1 live, Cycle 10)."""

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
        """Return (chosen, pick_index) or (None, None) if empty / no-match."""


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


# R1 live implementation (Cycle 10) — imported below to keep ABC local.
from .strategy_capability import CapabilityAwareStrategy  # noqa: E402

__all__ = [
    "CapabilityAwareStrategy",
    "RoundRobinStrategy",
    "RoutingStrategy",
]
