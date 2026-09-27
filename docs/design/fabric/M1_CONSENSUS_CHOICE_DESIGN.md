# M1 Consensus Choice — Design-Only Scorecard

**Status:** DESIGN MATURED (no runtime; no candidate defaulted to Raft)  
**Cycle / Checkpoint:** 46 / CP-0050 (base); **50 / CP-0054 (maturation)**  
**Date:** 2026-09-26 America/New_York (EDT)  
**Theme:** (D) M1 from `0.19_SCOPE_FROZEN` / blueprint L4  
**ABORT rule:** M1..M3 fail review → N stays 2  
**Runtime:** Raft / N>2 / M4+ remain **NO_HELD**  
**Maturation:** see `M1_SCORECARD_MATURATION.md` (provisional scores + NO_CONSENSUS_YET)

---

## 1. Intent

Produce a **ratifiable scorecard** (≥80 / 100) for choosing a future consensus
approach **if and when** GOV unlocks N>2. This CP does **not** pick Raft, does
**not** implement consensus, and does **not** unlock G_Raft or G_Ngt2.

Blueprint artifact target (later): `rfc/0001-consensus-choice.md`  
This doc is the pre-RFC design scorecard + candidate axes.  
**CP-0054** fills provisional scores and records **NO_CONSENSUS_YET**.

## 2. Non-negotiable Mesh constraints

Any candidate MUST:

1. Preserve **dual_primary = 0** fence semantics (or prove stronger).
2. Preserve minority-write halt / clock-skew refuse-join / manifest parity reject.
3. Remain compatible with attested identity + OBS + audit hash-chain.
4. Not require silent plaintext.
5. Not smuggle GIA/ML-as-product unlocks.
6. Document ABORT → safe N=2 fallback.

**Hard rule:** `no default = Raft`. Raft may appear as **one scored candidate**
among others; selecting it still requires ≥80 + GOV — and **runtime remains NO_HELD**.

## 3. Scorecard axes (100 pts)

| Axis | Pts | What “good” means |
|------|----:|-------------------|
| Safety under partition | 20 | No dual-primary; no minority split-brain writes |
| Fence compatibility | 15 | Maps cleanly to H3/H6/H7 ABORT behaviors |
| Liveness @N=2 today | 10 | Does not regress current N=2 heal path |
| Liveness path @N>2 (design) | 10 | Clear theoretical progress under majority |
| Operational complexity | 10 | Ops burden, runbooks, footguns |
| Audit / OBS fit | 10 | Receipts, HLC, queryable decisions |
| WAN / HLC readiness | 10 | Works with M3 latency/partition model |
| Unlock evidence cost | 10 | Clarity of tests needed for G_Raft/G_Ngt2 |
| Reversibility | 5 | Can stay on N=2 fenced heal if rejected |

**Ratify threshold:** total ≥ **80**. Below 80 → keep N=2; no unlock prose.
Unlock ratification applies to C1..C5 only (C0 = status-quo baseline).

## 4. Candidate slots (provisional scores — CP-0054)

| ID | Candidate | Notes | Score |
|----|-----------|-------|------:|
| C0 | **Stay N=2 fenced_primary_heal** (status quo) | Always available baseline (not N>2 unlock) | 85† |
| C1 | Raft (etcd-class) | Common; **not default**; fence-compat proof required | 68 |
| C2 | Paxos / Multi-Paxos family | Classic; complexity cost | 59 |
| C3 | Flexible Paxos / EPaxos-class | WAN-friendly claims; evidence heavy | 62 |
| C4 | Mesh-native fence+quorum journal (non-Raft) | Design exploration only | 75 |
| C5 | Other (named later) | Must fill all axes | — |

† Baseline viability only — not an unlock score.

**Unlock verdict:** no C1..C4 ≥80 → **NO_CONSENSUS_YET** (see maturation doc).

## 5. Evidence checklist (for a future unlock — not now)

- [x] Scorecard ≥80 threshold + axes documented
- [x] Provisional scores filled (CP-0054)
- [x] Written justification if rejecting all unlock candidates (NO_CONSENSUS_YET)
- [ ] Fence probe matrix green at design review
- [x] M2 membership/rejoin SM draft exists (CP-0059)
- [x] M3 WAN+HLC model draft exists (CP-0060)
- [ ] GOV.2 quorum + evidence-bundle (GOV.3)
- [ ] Explicit: runtime still gated; prose unlock forbidden (GOV.6)

## 6. Pointers to M2 / M3 (design-only)

| Item | Pointer | Runtime |
|------|---------|---------|
| **M2** membership+rejoin | JOINING→ATTESTING→ACTIVE→DRAINING→LEFT→REJOIN (`M2_MEMBERSHIP_REJOIN_DESIGN.md` CP-0059); future `rfc/0002-membership.md` | NO_HELD |
| **M3** WAN latency/partition | RTT bands, loss%, heal windows; **HLC required**; `M3_WAN_MODEL_DESIGN.md` CP-0060; stubs `docs/wan/partition-v1.md` + `latency-bands-v1.md` | NO_HELD |
| **M4+** | N3 partition_suite etc. | NO_HELD until M1+M2+M3 ratified |

Stub pointer docs: `docs/design/fabric/M2_MEMBERSHIP_REJOIN_POINTER.md`,
`docs/design/fabric/M3_WAN_PARTITION_HLC_POINTER.md`.

## 7. Non-goals

- Implementing Raft/Paxos/any consensus runtime
- Opening N>2 topology
- Multi-primary reconciliation (M5 NO_HELD)
- Claiming Mesh already has world-scale consensus
- GIA / train / SaaS / economy
- Defaulting any candidate to Raft

**NO_HELD:** Raft,N>2,multi-primary,ML,R2,R3,plaintext,Vault-ACME-req,GIA,SLO_chase,tag_schema,EVERY_fsync

## Related

- `docs/design/fabric/M1_SCORECARD_MATURATION.md` (CP-0054)
- `council/blueprint/FINAL_BLUEPRINT_ROOT.md` (L4 M1..M7)
- `docs/planning/0.19_SCOPE_FROZEN.md`
- `council/COUNCIL_AGREEMENT_HYPERBRAIN_ASTRA.md`

---

## Addendum — Cycle 68 / CP-0072

See `M1_CONSENSUS_RERESEARCH.md` / `docs/planning/D2_M1_CONSENSUS_CANDIDATE_RERESEARCH.md`
for C67 weight re-score + C5 FQ-ED sketch. **M1=NO_CONSENSUS_YET** unchanged; no Raft default.


---

## Addendum — Cycle 69 / CP-0073

C5 FQ-ED refined to numeric **80** (`M1_C5_FQ_ED_REFINEMENT.md`). **M1=NO_CONSENSUS_YET** for unlock (design-review green + GOV.2 still open). No Raft default; live=DISABLED.

**CP-0074:** Permanent M1=NO_CONSENSUS_YET under N=2 scope + HOLD — see `M1_NO_CONSENSUS_N2_SCOPE.md`.
