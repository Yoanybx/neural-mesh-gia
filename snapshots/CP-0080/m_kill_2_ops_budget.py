"""M-KILL-2 — Ops-defined kill→RefuseTransport latency budget (CP-0080).

Honest ceiling for the **process-local** I5 kill → RefuseTransport + continuity
ABORT path under fences (E-KILL mid-window). Recorded **before** measurement
per GATE6_METRIC_COMPLETION_DESIGN §4 M-KILL-2-BUDGET.

Does NOT claim network/provider RTT, remote kill fans, or product permanent LIVE.
Module LIVE_API_ENABLED stays False; NO_HELD unchanged.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

__all__ = [
    "CYCLE",
    "SEAL_CP",
    "BUDGET_ID",
    "KILL_TO_REFUSE_CEILING_MS",
    "BUDGET_SCOPE",
    "BUDGET_ENV",
    "KillBudgetVerdict",
    "evaluate_kill_to_refuse_budget",
    "budget_artifact_dict",
]

CYCLE = 76
SEAL_CP = "CP-0080"
BUDGET_ID = "M-KILL-2-BUDGET"
# Process-local in-box kill path observed ~0 ms on CP-0079 pack; honest ops
# ceiling leaves headroom for scheduling jitter without inventing network SLO.
KILL_TO_REFUSE_CEILING_MS = 100
BUDGET_SCOPE = "process_local_i5_kill_to_refuse"
BUDGET_ENV = "local_box_under_fences_gemini_free_canary_path"


@dataclass(frozen=True)
class KillBudgetVerdict:
    metric_id: str
    observed_ms: int
    ceiling_ms: int
    within_budget: bool
    scope: str
    env: str
    ledger_kinds_ok: bool
    ok: bool
    notes: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "metric_id": self.metric_id,
            "observed_ms": self.observed_ms,
            "ceiling_ms": self.ceiling_ms,
            "within_budget": self.within_budget,
            "scope": self.scope,
            "env": self.env,
            "ledger_kinds_ok": self.ledger_kinds_ok,
            "ok": self.ok,
            "notes": list(self.notes),
            "seal_cp": SEAL_CP,
            "cycle": CYCLE,
        }


def evaluate_kill_to_refuse_budget(
    *,
    observed_ms: int,
    ledger_kinds: list[str] | tuple[str, ...] | None = None,
    ceiling_ms: int = KILL_TO_REFUSE_CEILING_MS,
) -> KillBudgetVerdict:
    """Pass iff observed ≤ ceiling and oversight+abort ledger kinds present."""
    kinds = list(ledger_kinds or [])
    ledger_ok = "oversight" in kinds and "abort" in kinds
    within = int(observed_ms) <= int(ceiling_ms)
    notes: list[str] = []
    if within:
        notes.append(
            f"kill→refuse {observed_ms}ms ≤ ceiling {ceiling_ms}ms ({BUDGET_SCOPE})"
        )
    else:
        notes.append(
            f"BUDGET MISS: kill→refuse {observed_ms}ms > ceiling {ceiling_ms}ms"
        )
    if not ledger_ok:
        notes.append("ledger missing oversight+abort (M-KILL-2 fail)")
    return KillBudgetVerdict(
        metric_id=BUDGET_ID,
        observed_ms=int(observed_ms),
        ceiling_ms=int(ceiling_ms),
        within_budget=within,
        scope=BUDGET_SCOPE,
        env=BUDGET_ENV,
        ledger_kinds_ok=ledger_ok,
        ok=within and ledger_ok,
        notes=tuple(notes),
    )


def budget_artifact_dict() -> dict[str, Any]:
    """Static budget record (ops-defined before measurement)."""
    return {
        "schema": "mesh.ops.m_kill_2_budget/v0",
        "metric_id": BUDGET_ID,
        "ceiling_ms": KILL_TO_REFUSE_CEILING_MS,
        "scope": BUDGET_SCOPE,
        "env": BUDGET_ENV,
        "unit": "ms",
        "path": "I5.kill → RefuseTransport binding + continuity ABORT + enabled=false",
        "excludes": [
            "provider_http_rtt",
            "remote_kill_fanout",
            "permanent_LIVE_API_ENABLED",
            "CI_live_network",
        ],
        "basis": (
            "CP-0079 E-KILL observed kill_to_refuse_latency_ms=0 (descriptive); "
            "CP-0080 seals honest process-local ceiling=100ms before re-measure"
        ),
        "seal_cp": SEAL_CP,
        "cycle": CYCLE,
        "doc": "docs/ops/M_KILL_2_OPS_KILL_REFUSE_BUDGET.md",
        "LIVE_API_ENABLED_module_default": False,
    }
