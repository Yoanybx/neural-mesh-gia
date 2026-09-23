"""Router R0 metrics helpers (bench aggregation; no ML)."""

from __future__ import annotations

import statistics
from collections import Counter
from typing import Any, Sequence

from .models import DecisionStatus, RouteDecision


def percentile(xs: Sequence[float], p: float) -> float:
    if not xs:
        return 0.0
    ys = sorted(float(x) for x in xs)
    k = (len(ys) - 1) * (p / 100.0)
    f = int(k)
    c = min(f + 1, len(ys) - 1)
    if f == c:
        return ys[f]
    return ys[f] + (ys[c] - ys[f]) * (k - f)


def summarize_decisions(decisions: Sequence[RouteDecision]) -> dict[str, Any]:
    """Aggregate distribution, rejects, and latency from RouteDecision list."""
    accepted = [d for d in decisions if d.status == DecisionStatus.ACCEPTED]
    rejected = [d for d in decisions if d.status == DecisionStatus.REJECTED]
    lat = [
        float(d.metrics.get("decision_latency_ms", 0.0))
        for d in decisions
        if d.metrics
    ]
    dist = Counter(d.selected_node_id for d in accepted)
    return {
        "n": len(decisions),
        "accepted": len(accepted),
        "rejected": len(rejected),
        "distribution": dict(sorted(dist.items(), key=lambda kv: kv[0] or "")),
        "rejected_reasons": dict(Counter(d.reason for d in rejected)),
        "decision_latency_ms": {
            "p50": percentile(lat, 50),
            "p99": percentile(lat, 99),
            "mean": statistics.fmean(lat) if lat else 0.0,
        },
    }


__all__ = ["percentile", "summarize_decisions"]
