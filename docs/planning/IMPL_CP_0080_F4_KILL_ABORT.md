# IMPL CP-0080 — F4 design seal + M-KILL-2 budget + M-ABORT-3 drill

**Status:** **AUTHORIZED OPS/DESIGN CP** under fences  
**Cycle / Checkpoint:** 76 / **CP-0080**  
**Date:** 2026-09-28 ~22:42 EDT (America/New_York)  
**Author:** Grok Bot `<grok-bot@local>`  
**Tip at mint base:** `c2ba1e2` (CP-0079)  
**Package:** **0.18.0 HELD** · **LIVE_API_ENABLED=False** · **NO_HELD unchanged** · D3 NOT ACKed · M1=NO_CONSENSUS_YET

---

## 0. What this is / is not

| Is | Is not |
|----|--------|
| F4 product-enable **safety amendment DESIGN_SEALED** + **unsigned** product ACK draft | Signed F4 product ACK / module True |
| Honest **M-KILL-2** ops kill→refuse budget (100 ms process-local) + drill | Network RTT product SLO |
| **M-ABORT-3** conflicting/missing judges fail-closed drill + evidence | Auto-majority execute auth |
| Leaves module LIVE **False** | Permanent product enable / NO_HELD / D3 / keys-in-git |

---

## 1. Artifacts

| Artifact | Path |
|----------|------|
| F4 amendment | `docs/planning/F4_PRODUCT_ENABLE_SAFETY_AMENDMENT.md` |
| F4 design seal | `docs/planning/F4_DESIGN_SEALED.md` |
| F4 product ACK draft | `docs/planning/F4_PRODUCT_ENABLE_ACK_DRAFT.md` (**UNSIGNED**) |
| M-KILL-2 budget | `docs/ops/M_KILL_2_OPS_KILL_REFUSE_BUDGET.md` |
| Budget module | `src/neural_mesh/packaging/m_kill_2_ops_budget.py` |
| Pack + E-CONFLICT | `src/neural_mesh/packaging/l_judge_multi_canary_pack.py` |
| Tests | `tests/test_m_kill_2_and_abort3_cycle76.py` |
| Evidence | `docs/planning/EVIDENCE_CP_0080_KILL_ABORT_DRILLS.md` |
| Council note | `council/NOTE_CP_0080_F4_KILL_ABORT.md` |

---

## 2. Outcomes

| Item | Result |
|------|--------|
| F4 DESIGN_SEALED | **YES** |
| F4 product ACK | **UNSIGNED** (ENABLE ≠ product; no invent) |
| M-KILL-2 budget | **100 ms** sealed; drill PASS |
| M-ABORT-3 | E-CONFLICT drill PASS |
| Module LIVE | **False** |

---

*End IMPL_CP_0080 — F4 design sealed; drills green; product ACK unsigned; LIVE False.*
