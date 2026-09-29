# Evidence — CP-0080 M-KILL-2 budget + M-ABORT-3 conflict drills

**Status:** **MEASURED** (mock/unit under fences) · module LIVE False  
**Date:** 2026-09-28 ~22:43 EDT (America/New_York)  
**Author:** Grok Bot `<grok-bot@local>`  
**Tip at base:** `c2ba1e2`  
**Ledger:** `docs/planning/GATE5_CP0080_DRILL_LEDGER.json`  
**Tests:** `tests/test_m_kill_2_and_abort3_cycle76.py` (9 passed with pack suite)

**Does not** flip permanent LIVE · **does not** sign F4 product ACK · **does not** unlock NO_HELD.

---

## 1. M-KILL-2-BUDGET

| Field | Value |
|-------|-------|
| Ceiling (ops-defined **before** measure) | **100 ms** — `docs/ops/M_KILL_2_OPS_KILL_REFUSE_BUDGET.md` |
| Scope | process-local I5 kill → RefuseTransport |
| Observed `kill_to_refuse_latency_ms` | **0** |
| Ledger kinds | `oversight` + `abort` present |
| Verdict | **PASS** (`budget.ok=true`) |

Prior CP-0079 had latency descriptive only (budget OPEN). CP-0080 seals ceiling then re-measures.

---

## 2. M-ABORT-3 (E-CONFLICT)

| Sub-drill | Result |
|-----------|--------|
| Conflicting judges (ACCEPT vs REJECT) | Mesh **ABORT**; `auto_majority_execute=false`; `escalate_i5=true` |
| Missing judge (expected judge-b absent) | Mesh **ABORT** `JUDGE_MISSING`; fail-closed |
| Post refuse | RefuseTransport; `mesh_accept=false` |
| Verdict | **PASS** |

---

## 3. Pack summary (mock-only re-run)

| Field | Value |
|-------|-------|
| n | **7** (prior n=6 + E-CONFLICT) |
| seal_candidate | **true** (sample policy; ≠ product listo) |
| Module LIVE final | **False** |
| Binding final | RefuseTransport |
| ops_cp | CP-0080 |

---

## 4. F4 posture (companion)

| Item | Status |
|------|--------|
| F4 amendment DESIGN_SEALED | **YES** |
| F4 product ACK | **UNSIGNED** |
| Prefer leave LIVE False | **YES** |

---

*End EVIDENCE_CP_0080_KILL_ABORT_DRILLS — M-KILL-2 PASS; M-ABORT-3 PASS; F4 ACK unsigned; LIVE False.*
