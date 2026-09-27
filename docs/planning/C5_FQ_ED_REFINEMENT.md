# C5 FQ-ED Refinement (Cycle 69 / CP-0073)

**Status:** DESIGN ONLY — C5 sketch + scorecard refinement; **no runtime**; **no Raft default**  
**Cycle / Checkpoint:** 69 / CP-0073  
**Date:** 2026-09-26 America/New_York (EDT)  
**Authority:** Operator resume after Hold post-D2 (`council/NOTE_OPERATOR_HOLD_POST_D2.md`); DeepSeek C68 PASS + hold ACK; refine C5 toward ≥80  
**Prior tip / CP:** feature ~`1e028d2` / CP-0072 (D2 sealed; M1=NO_CONSENSUS_YET; C5=78)  
**Composes:** CP-0050 · CP-0054 · CP-0071 · **CP-0072**  
**Runtime:** Raft / N>2 / M4+ remain **NO_HELD** · live=DISABLED · MESH_PERF_EXPERIMENTAL=OFF · pkg0190 NOT_OPENED · v0.19 ABSENT · 0.18.0 HELD · **D3 NOT ACKed**

---

## 0. Resume gates (post-Hold)

| Check | Result |
|-------|--------|
| Hold note present | **PASS** (`NOTE_OPERATOR_HOLD_POST_D2.md`) |
| D2 / CP-0072 VERIFIED | **PASS** |
| D3 ACKed? | **NO** — remains ACK-gated; not started |
| live enabled? | **NO** — live=DISABLED |
| Threshold lowered? | **NO** — ≥80 held |
| Raft defaulted? | **NO** |

---

## 1. Intent

Refine **C5 FQ-ED** (Fence-Quorum + Evidence-Diversity) so the scorecard either:

- reaches honest total **≥80** with written +2 justification (no fudge), or
- stays **<80** with clear remaining gaps and **NO_CONSENSUS_YET**.

This CP does **not** implement consensus, does **not** open N>2, does **not** default to Raft, does **not** enable live, does **not** flip MESH_PERF_EXPERIMENTAL, does **not** open pkg0190, and does **not** start D3.

---

## 2. Where can +2 come from without fudge?

Prior C5 (CP-0072) = **78**. Caps were explicit: fence-probe matrix not green suppressed **fence_compat**; N>2 safety evidence absence suppressed **safety**; adversary rules were sketch-level.

| Candidate bump | Honest? | Decision |
|----------------|---------|----------|
| fence_compat 12→14/15 (claim matrix green) | **No** — self-authored matrix ≠ independent design-review green; no runtime probes | Reject full bump |
| fence_compat 12→13 (matrix DESIGN_DRAFTED complete) | **Yes** — fills the missing design artifact that suppressed the axis | **Take +1** |
| safety 23→25 (N>2 “feels safer”) | **No** — N>2 partition evidence still absent | **Reject** (stay 23) |
| adversary 8→10 (claim independence proven) | **No** — D1 requirements recorded, not proven | Reject full bump |
| adversary 8→9 (measurable ED taxonomy + acceptance) | **Yes** — turns sketch bullets into testable criteria | **Take +1** |
| complexity / liveness / WAN +1 | Weak — no new runbook simplification or WAN proof | **Reject** |

**Honest +2 = fence_compat +1 + adversary_resistance +1 → C5 = 80 numeric.**

---

## 3. Updated C5 axis scores

| Axis | max | C5@CP-0072 | C5@CP-0073 | Delta |
|------|----:|----------:|----------:|------:|
| Safety | 30 | 23 | **23** | 0 (N>2 evidence still absent) |
| Liveness | 15 | 11 | 11 | 0 |
| Fence-compat | 15 | 12 | **13** | **+1** |
| No-Raft | 10 | 10 | 10 | 0 |
| WAN-tolerance | 15 | 11 | 11 | 0 |
| Adversary-resistance | 10 | 8 | **9** | **+1** |
| Complexity | 5 | 3 | 3 | 0 |
| **Total** | **100** | **78** | **80** | **+2** |

C0..C4 totals unchanged from CP-0072 (85† / 54 / 53 / 60 / 73).

† C0 baseline only — not unlock-eligible.

---

## 4. C5 FQ-ED refined sketch (design-only)

Inherits CP-0072 §4.1 and adds:

### 4.1 Fence-probe matrix (DESIGN_DRAFTED)

**Status:** `DESIGN_DRAFTED` — complete design rows with expected outcomes; **not** `DESIGN_REVIEW_GREEN` (no independent design review this CP); **not** runtime-executed.

| Probe ID | Scenario | Expected C5 behavior | Maps |
|----------|----------|----------------------|------|
| FP-H3-a | Two members claim primary | ABORT; dual_primary=0; fallback C0 | H3 |
| FP-H3-b | Split-brain write attempt | ABORT; no dual/minority write | H3 |
| FP-H6-a | Majority Active unavailable | Halt writes; refuse journal append | H6 |
| FP-H6-b | Attested Active < majority | Halt; no minority quorum claim | H6 |
| FP-H7-a | Join with HLC skew beyond bound | Refuse-join; no silent ACTIVE | H7 |
| FP-H7-b | Rejoin after skew heal | M2 REJOIN + re-attest; no skip | H7 |
| FP-ED-a | N-agree on single evidence kind | No consensus *claim*; diversity FAIL | ED |
| FP-ED-b | ≥2 kinds, same correlation class | Weak evidence; ABORT/escalate | ED/CG4 |
| FP-ED-c | ≥2 kinds AND ≥2 correlation classes | Evidence convergence allowed (≠ exec auth) | ED |
| FP-ADV-a | Judges/members agree on unsafe | Mesh policy + I5 still ABORT | ADV |
| FP-ADV-b | Judges contradict / unavailable | No silent majority; ABORT/FALLBACK | ADV |
| FP-WAN-a | WAN partition with HLC | Leaderless/rotating proposer; no sticky WAN leader write | WAN/M3 |
| FP-ABORT-a | Any fence ABORT | Always revert to C0 N=2 fenced_primary_heal | ABORT |

### 4.2 Evidence-diversity acceptance (measurable)

**Evidence kinds (design taxonomy):**  
`routing_receipt` · `continuity_orphan_resume` · `oversight_decision` · `injection_digest` · `fence_event` · `membership_attest` · `journal_decision`

**Correlation classes:**  
`same_engine_id` · `same_provider` · `same_weights` · `same_prompt_template` · `shared_failure_domain`

**Acceptance before any consensus *claim*:** ≥2 distinct evidence kinds **AND** ≥2 distinct correlation classes.  
Correlated blind-spot agreement = weak evidence (ABORT/escalate).  
Consensus *claim* ≠ execution authorization (A3/A4 human gate unchanged).

### 4.3 Unchanged hard rules

Membership compose M2; majority attested Active; hash-chained journal; HLC required; ABORT→C0; runtime **NO_HELD** until fence-probe design-review green + GOV unlock.

---

## 5. Decision — NO_CONSENSUS_YET (3rd)

**Scorecard numeric:** C5 FQ-ED = **80** (meets ≥80 numeric threshold).  
**Unlock verdict:** **NO_CONSENSUS_YET**.

**Why still not unlocked (P-18 / RK53 / F9):**

1. Fence-probe status is **DESIGN_DRAFTED**, not **design-review green** (ratify AND-gate incomplete).
2. **GOV.2** quorum + evidence-bundle still open.
3. **N>2 safety evidence** still absent (safety axis intentionally held at 23).
4. Runtime Raft / N>2 remain **NO_HELD**; prose unlock forbidden (GOV.6).
5. Numeric ≥80 alone must not silently select a default (especially not Raft).

**Remaining unlock gaps:**

- `fence_probe_not_design_review_green`
- `gov2_quorum_evidence_bundle_open`
- `n_gt2_safety_evidence_absent`
- `runtime_raft_n_gt2_no_held`

**What changed vs CP-0072:** C5 fence-probe matrix drafted; ED taxonomy + acceptance formalized; honest +2 → 80 numeric; unlock still blocked.  
**What did not change:** threshold ≥80; no Raft default; no N>2; live=DISABLED; no pkg0190; D3 not ACKed; no GIA/train/SaaS.

---

## 6. Full scoreboard (unchanged C0..C4)

| Axis | max | C0† | C1 | C2 | C3 | C4 | C5 |
|------|----:|----:|---:|---:|---:|---:|---:|
| Safety | 30 | 30 | 20 | 18 | 17 | 22 | 23 |
| Liveness | 15 | 10 | 12 | 10 | 12 | 10 | 11 |
| Fence-compat | 15 | 15 | 6 | 5 | 5 | 12 | **13** |
| No-Raft | 10 | 10 | 0 | 8 | 8 | 10 | 10 |
| WAN | 15 | 7 | 8 | 6 | 12 | 10 | 11 |
| Adversary | 10 | 8 | 5 | 4 | 4 | 6 | **9** |
| Complexity | 5 | 5 | 3 | 2 | 2 | 3 | 3 |
| **Total** | **100** | **85†** | **54** | **53** | **60** | **73** | **80** |

---

## 7. Evidence checklist

- [x] Honest +2 justification written (no fudge / no threshold lower)
- [x] C5 fence-probe matrix DESIGN_DRAFTED (FP-H3/H6/H7/ED/ADV/WAN/ABORT)
- [x] Evidence-diversity measurable criteria
- [x] C5 total = 80 numeric
- [x] Written **NO_CONSENSUS_YET** with remaining gaps
- [x] D3 not ACKed; live=DISABLED; no Raft default
- [ ] Fence-probe **design-review green** (still open)
- [ ] GOV.2 quorum + evidence-bundle
- [ ] N>2 safety evidence
- [ ] Explicit runtime unlock (GOV.6)

---

## 8. Non-goals / must-stay-false

| Flag / claim | Must stay |
|--------------|-----------|
| Runtime Raft / N>2 | **NO_HELD** |
| M1 unlock / default | **NO_CONSENSUS_YET** (no silent Raft; no silent C5 runtime default) |
| `live_adapter.enabled` | **false** |
| `MESH_PERF_EXPERIMENTAL` | **OFF** |
| pkg0190 / v0.19.0 | **NOT_OPENED / ABSENT** |
| D3 started | **No** (ACK-gated) |

**NO_HELD:** Raft,N>2,multi-primary,ML,R2,R3,plaintext,Vault-ACME-req,GIA,SLO_chase,tag_schema,EVERY_fsync

---

## 9. Related

- `docs/planning/D2_M1_CONSENSUS_CANDIDATE_RERESEARCH.md` (CP-0072)
- `docs/design/fabric/M1_C5_FQ_ED_REFINEMENT.md`
- `docs/design/fabric/M1_CONSENSUS_RERESEARCH.md`
- `docs/planning/D1_L_JUDGE_SAFETY_CASE_MATURATION.md` §4
- `council/NOTE_OPERATOR_HOLD_POST_D2.md`
- `council/COUNCIL_AGREEMENT_CYCLE69.md`

*End C5 FQ-ED refinement — design-only; C5=80 numeric; M1=NO_CONSENSUS_YET.*

---

## Addendum — Cycle 70 / CP-0074

Operator formalized **permanent** M1=NO_CONSENSUS_YET under N=2 scope + HOLD
(`docs/planning/M1_NO_CONSENSUS_N2_SCOPE.md`, `council/NOTE_M1_NO_CONSENSUS_N2_SCOPE.md`).
C5 numeric 80 unchanged; unlock still blocked; no Raft default; no N>2; D3 not ACKed;
live=DISABLED. Re-research loop under this scope closed. This addendum does not alter
CP-0073 scores or fence-probe DESIGN_DRAFTED status.
