"""CapabilityAwareStrategy — real R1 implementation (Cycle 10)."""

from __future__ import annotations

from typing import Sequence

from .capabilities import CapabilityRegistry, NodeCapability
from .models import RouteCandidate, TaskSpec
from .scoring import pick_best, score_node
from .strategy import RoutingStrategy


class CapabilityAwareStrategy(RoutingStrategy):
    """Deterministic capability-aware selection (no ML, no silent RR fallback).

    Score = capability_match + resource_fit + health − unavailable_penalty.
    On zero eligible / all stale / no positive score ⇒ select returns
    ``(None, None)`` and sets ``last_reason = CAPABILITY_NO_MATCH``.
    """

    name = "CAPABILITY_AWARE"
    STUB = False

    def __init__(
        self,
        registry: CapabilityRegistry | None = None,
        *,
        now_fn=None,
    ):
        self.registry = registry if registry is not None else CapabilityRegistry()
        self._now_fn = now_fn or self.registry._now_fn
        self.last_score: float | None = None
        self.last_factors: list[str] = []
        self.last_scores: dict = {}
        self.last_reason: str | None = None
        self.last_cap_state_fp: str = ""

    def select(
        self, task: TaskSpec, candidates: Sequence[RouteCandidate]
    ) -> tuple[RouteCandidate | None, int | None]:
        now = int(self._now_fn())
        fresh = {c.node_id: c for c in self.registry.list_fresh(now)}
        self.last_cap_state_fp = self.registry.fingerprint(fresh_only=True, now_ms=now)

        scored: list[tuple[RouteCandidate, float, list[str], dict]] = []
        for cand in candidates:
            cap: NodeCapability | None = fresh.get(cand.node_id)
            stale = False
            if cap is None:
                raw = self.registry.get(cand.node_id)
                if raw is not None and raw.is_stale(now):
                    # Stale: apply penalty path; do not treat as match.
                    stale = True
                    cap = raw
            total, factors, bd = score_node(task, cand, cap, stale=stale)
            # Hard filter: required capabilities must fully match for eligibility.
            if cap is None or stale:
                continue
            required = list(task.required_capabilities) or ["compute"]
            have = set(cap.supported_tasks) | set(cap.accelerators)
            if not all(r in have for r in required):
                continue
            if total <= 0:
                continue
            scored.append((cand, total, factors, bd))

        self.last_scores = {
            c.node_id: {"factors": list(f), "score": s} for c, s, f, _ in scored
        }
        chosen, idx, score, factors = pick_best(scored)
        if chosen is None:
            self.last_score = score
            self.last_factors = factors or ["no_match"]
            self.last_reason = "CAPABILITY_NO_MATCH"
            return None, None

        self.last_score = score
        self.last_factors = list(factors)
        self.last_reason = "CAPABILITY_AWARE"
        return chosen, idx


__all__ = ["CapabilityAwareStrategy"]
