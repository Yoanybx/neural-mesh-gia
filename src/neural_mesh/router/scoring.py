"""Deterministic capability scoring for R1 (no ML) — Cycle 10."""

from __future__ import annotations

from typing import Any, Sequence

from .capabilities import NodeCapability
from .models import NodeAvailability, RouteCandidate, TaskSpec

# Fixed weights (deterministic; not learned).
W_CAPABILITY_MATCH = 40.0
W_RESOURCE_FIT = 30.0
W_HEALTH = 30.0
UNAVAILABLE_PENALTY = 1000.0


def capability_match_score(
    task: TaskSpec, cap: NodeCapability
) -> tuple[float, list[str]]:
    """Fraction of required capabilities present in supported_tasks ∪ accelerators."""
    required = list(task.required_capabilities) or ["compute"]
    have = set(cap.supported_tasks) | set(cap.accelerators)
    if not required:
        return W_CAPABILITY_MATCH, ["capability_match"]
    hits = sum(1 for r in required if r in have)
    frac = hits / len(required)
    factors: list[str] = []
    if frac >= 1.0:
        factors.append("capability_match")
        for r in required:
            if r in cap.accelerators:
                factors.append(f"{r}_match")
            elif r in cap.supported_tasks:
                factors.append(f"{r}_supported")
    elif frac > 0:
        factors.append("partial_capability_match")
    return W_CAPABILITY_MATCH * frac, factors


def resource_fit_score(
    task: TaskSpec, cap: NodeCapability, candidate: RouteCandidate
) -> tuple[float, list[str]]:
    """How well node resources fit declared task requirements (0..W_RESOURCE_FIT)."""
    req = dict(task.resource_requirements or {})
    need_cpu = int(req.get("cpu", 0) or 0)
    need_mem = int(req.get("memory", 0) or 0)
    factors: list[str] = []
    parts: list[float] = []

    cpu = max(int(cap.cpu), int(candidate.cpu))
    mem = max(int(cap.memory), int(candidate.memory))

    if need_cpu <= 0 and need_mem <= 0:
        # No explicit needs: prefer richer nodes slightly but stay deterministic.
        # Normalize against a soft ceiling so scores stay in [0,1].
        cpu_frac = min(1.0, cpu / 16.0) if cpu else 0.0
        mem_frac = min(1.0, mem / 32768.0) if mem else 0.0
        parts = [cpu_frac, mem_frac]
        if cpu_frac > 0:
            factors.append("cpu_present")
        if mem_frac > 0:
            factors.append("memory_fit")
    else:
        if need_cpu > 0:
            if cpu >= need_cpu:
                parts.append(1.0)
                factors.append("cpu_fit")
            else:
                parts.append(cpu / need_cpu if need_cpu else 0.0)
        if need_mem > 0:
            if mem >= need_mem:
                parts.append(1.0)
                factors.append("memory_fit")
            else:
                parts.append(mem / need_mem if need_mem else 0.0)
    if not parts:
        return 0.0, factors
    return W_RESOURCE_FIT * (sum(parts) / len(parts)), factors


def health_score(cap: NodeCapability) -> tuple[float, list[str]]:
    h = max(0.0, min(1.0, float(cap.health)))
    factors = ["health"] if h > 0 else ["health_zero"]
    return W_HEALTH * h, factors


def unavailable_penalty(
    candidate: RouteCandidate, *, stale: bool = False
) -> tuple[float, list[str]]:
    if stale:
        return UNAVAILABLE_PENALTY, ["stale_penalty"]
    if candidate.status != NodeAvailability.AVAILABLE:
        return UNAVAILABLE_PENALTY, ["unavailable_penalty"]
    return 0.0, []


def score_node(
    task: TaskSpec,
    candidate: RouteCandidate,
    cap: NodeCapability | None,
    *,
    stale: bool = False,
) -> tuple[float, list[str], dict[str, float]]:
    """Return (total_score, factors, component_breakdown).

    Missing capability ⇒ score 0 with factor ``missing_capability`` (caller
    should treat as non-match; never silent RR).
    """
    if cap is None:
        return 0.0, ["missing_capability"], {"capability_match": 0.0}

    cm, f1 = capability_match_score(task, cap)
    rf, f2 = resource_fit_score(task, cap, candidate)
    hs, f3 = health_score(cap)
    pen, f4 = unavailable_penalty(candidate, stale=stale)
    total = cm + rf + hs - pen
    factors = list(dict.fromkeys(f1 + f2 + f3 + f4))  # stable unique
    breakdown = {
        "capability_match": cm,
        "resource_fit": rf,
        "health": hs,
        "unavailable_penalty": pen,
        "total": total,
    }
    return total, factors, breakdown


def pick_best(
    scored: Sequence[tuple[RouteCandidate, float, list[str], dict[str, float]]]
) -> tuple[RouteCandidate | None, int | None, float | None, list[str]]:
    """Deterministic best: max score, then lex node_id. Returns (cand, idx, score, factors)."""
    if not scored:
        return None, None, None, []
    # Attach original index for stable pick_index among eligible list order.
    ranked = sorted(
        enumerate(scored),
        key=lambda iv: (-iv[1][1], iv[1][0].node_id, iv[0]),
    )
    idx, (cand, score, factors, _bd) = ranked[0]
    if score <= 0:
        return None, None, score, factors
    return cand, idx, score, factors


def scores_summary(
    scored: Sequence[tuple[RouteCandidate, float, list[str], dict[str, float]]]
) -> dict[str, Any]:
    return {
        c.node_id: {"score": s, "factors": list(f), "breakdown": dict(bd)}
        for c, s, f, bd in scored
    }


__all__ = [
    "UNAVAILABLE_PENALTY",
    "W_CAPABILITY_MATCH",
    "W_HEALTH",
    "W_RESOURCE_FIT",
    "capability_match_score",
    "health_score",
    "pick_best",
    "resource_fit_score",
    "score_node",
    "scores_summary",
    "unavailable_penalty",
]
