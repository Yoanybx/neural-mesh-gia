# M-KILL-2 — Ops kill→RefuseTransport latency budget

**Status:** **BUDGET SEALED (ops)** — ceiling recorded **before** re-measure (CP-0080)  
**Metric:** `M-KILL-2-BUDGET` (`GATE6_LIVE_ACCEPTANCE_METRICS.md` §2.2 · `GATE6_METRIC_COMPLETION_DESIGN.md` §4)  
**Date:** 2026-09-28 ~22:42 EDT (America/New_York)  
**Author:** Grok Bot `<grok-bot@local>`  
**Tip at seal base:** `c2ba1e2` (CP-0079 multi-canary n=6)  
**Package:** **0.18.0 HELD** · module `LIVE_API_ENABLED=False` · **NO_HELD unchanged**

---

## 0. What this is / is not

| Is | Is not |
|----|--------|
| Honest **ops-defined** ceiling for process-local I5 kill → RefuseTransport | A network / provider RTT SLO |
| Binding for E-KILL pack attempts under fences | Permission to leave LIVE True |
| Satisfies “budget recorded **before** measurement” | Claim that CP-0079 descriptive 0 ms alone sealed M-KILL-2 |
| Scoped to local box canary path | Remote kill fan-out / CI live |

---

## 1. Budget (binding)

| Field | Value |
|-------|-------|
| **Metric ID** | `M-KILL-2-BUDGET` |
| **Ceiling** | **100 ms** (`KILL_TO_REFUSE_CEILING_MS`) |
| **Path** | `I5.kill` → RefuseTransport binding + continuity `ABORT` + `enabled=false` + post-kill call refused |
| **Scope** | `process_local_i5_kill_to_refuse` |
| **Env** | `local_box_under_fences_gemini_free_canary_path` |
| **Pass** | `observed_ms ≤ 100` **and** ledger kinds include `oversight` + `abort` |
| **Fail** | Over ceiling **or** missing ledger kinds — record FAIL with ledger; do not invent PASS |

**Basis:** CP-0079 E-KILL observed `kill_to_refuse_latency_ms=0` (descriptive; budget was OPEN). CP-0080 seals ceiling **100 ms** with headroom for scheduling jitter — **not** an invented network product SLO.

**Excludes:** provider HTTP RTT · remote kill fan-out · permanent `LIVE_API_ENABLED=True` · CI live network.

---

## 2. Code / evidence

| Artifact | Path |
|----------|------|
| Budget module | `src/neural_mesh/packaging/m_kill_2_ops_budget.py` |
| Pack integration | `l_judge_multi_canary_pack.py` `_run_kill` → `evaluate_kill_to_refuse_budget` |
| Unit/ops tests | `tests/test_m_kill_2_and_abort3_cycle76.py` |
| Evidence | `docs/planning/EVIDENCE_CP_0080_KILL_ABORT_DRILLS.md` |

---

## 3. Fences held

- Module `LIVE_API_ENABLED=False`  
- RefuseTransport default ON after drill  
- No keys in git · no push/tags · NO_HELD unchanged  
- F4 product-enable **not** authorized by this budget  

---

*End M_KILL_2_OPS_KILL_REFUSE_BUDGET — ceiling 100 ms process-local; CP-0080.*
