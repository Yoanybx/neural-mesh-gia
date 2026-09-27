# M1 Consensus Choice — C67 Weight Re-Research

**Status:** DESIGN ONLY (no runtime; no candidate defaulted to Raft)  
**Cycle / Checkpoint:** 68 / CP-0072  
**Date:** 2026-09-26 America/New_York (EDT)  
**Prior:** CP-0050 base · CP-0054 maturation (old axes) · CP-0071 D1 consensus draft  
**Canonical planning:** `docs/planning/D2_M1_CONSENSUS_CANDIDATE_RERESEARCH.md`  
**Verdict:** **NO_CONSENSUS_YET** (closest: C5 FQ-ED = 78 < 80)

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

**Ratify:** ≥80 + fence-probe green + GOV.2 later. C0 not unlock-eligible.

## Totals (provisional)

| Candidate | Total | Notes |
|-----------|------:|-------|
| C0 Stay N=2 | 85† | Baseline only |
| C1 Raft | 54 | no-Raft axis = 0; not default |
| C2 Paxos | 53 | |
| C3 Flex/EPaxos | 60 | |
| C4 Mesh-native | 73 | |
| C5 FQ-ED (custom) | **78** | Closest; still <80 |

† Not an unlock score.

## Decision

**NO_CONSENSUS_YET** — see planning doc §6. Runtime Raft/N>2 **NO_HELD**. live=DISABLED.

## Related

- `M1_CONSENSUS_CHOICE_DESIGN.md` · `M1_SCORECARD_MATURATION.md`
- `docs/planning/D1_L_JUDGE_SAFETY_CASE_MATURATION.md` §4
- `docs/planning/D2_M1_CONSENSUS_CANDIDATE_RERESEARCH.md`
