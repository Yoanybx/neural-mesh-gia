# M1 Consensus Choice — C67 Weight Re-Research (+ C5 refinement + N=2 posture)

**Status:** DESIGN ONLY (no runtime; no candidate defaulted to Raft)  
**Cycle / Checkpoint:** 68 / CP-0072 (re-research); **69 / CP-0073 (C5 refinement)**; **70 / CP-0074 (N=2 permanent posture)**  
**Date:** 2026-09-26 America/New_York (EDT)  
**Prior:** CP-0050 base · CP-0054 maturation · CP-0071 D1 consensus draft · CP-0072 C5 sketch@78 · CP-0073 C5@80 numeric  
**Canonical planning:** `docs/planning/D2_M1_CONSENSUS_CANDIDATE_RERESEARCH.md` · `docs/planning/C5_FQ_ED_REFINEMENT.md` · `docs/planning/M1_NO_CONSENSUS_N2_SCOPE.md`  
**Verdict:** **NO_CONSENSUS_YET** — **permanent under N=2 / NO_HELD scope** (C5 numeric **80**; unlock blocked — fence_green|GOV.2|n_gt2_safety; structural circularity on n_gt2_safety)

---

## Updated axes (sum 100)

| Axis | Pts |
|------|----:|
| Safety | 30 |
| Liveness | 15 |
| Fence-compat | 15 |
| No-Raft | 10 |
| WAN-tolerance | 15 |
| Adversary-resistance | 10 |
| Complexity | 5 |

**Ratify:** ≥80 + fence-probe design-review green + GOV.2 later. C0 not unlock-eligible. Threshold **not** lowered. Under current scope, ratify AND-gates cannot all close (`n_gt2_safety` structurally blocked while N>2 is NO_HELD).

## Totals (provisional)

| Candidate | Total | Notes |
|-----------|------:|-------|
| C0 Stay N=2 | 85† | Baseline only |
| C1 Raft | 54 | no-Raft axis = 0; not default |
| C2 Paxos | 53 | |
| C3 Flex/EPaxos | 60 | |
| C4 Mesh-native | 73 | |
| C5 FQ-ED (refined) | **80** | Numeric ≥80; unlock still NO_CONSENSUS_YET |

† Not an unlock score.

### C5 delta (CP-0072 → CP-0073)

| Axis | 78-era | Now | Honest justification |
|------|-------:|----:|----------------------|
| fence_compat | 12 | 13 | Fence-probe matrix DESIGN_DRAFTED |
| adversary_resistance | 8 | 9 | Measurable ED taxonomy/acceptance |
| safety | 23 | 23 | N>2 evidence still absent — no fudge |

## Decision

**NO_CONSENSUS_YET** — **permanent under N=2 scope** (CP-0074). Numeric bar met by C5; ratify AND-gates incomplete; re-research loop under this scope **closed**. Runtime Raft/N>2 **NO_HELD**. live=DISABLED. D3 NOT ACKed. HOLD active.

## Related

- `M1_CONSENSUS_CHOICE_DESIGN.md` · `M1_SCORECARD_MATURATION.md` · `M1_C5_FQ_ED_REFINEMENT.md` · `M1_NO_CONSENSUS_N2_SCOPE.md`
- `docs/planning/D1_L_JUDGE_SAFETY_CASE_MATURATION.md` §4
- `docs/planning/D2_M1_CONSENSUS_CANDIDATE_RERESEARCH.md`
- `docs/planning/C5_FQ_ED_REFINEMENT.md`
- `docs/planning/M1_NO_CONSENSUS_N2_SCOPE.md`
- `council/NOTE_M1_NO_CONSENSUS_N2_SCOPE.md`
