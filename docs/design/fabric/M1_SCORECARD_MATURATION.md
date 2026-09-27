# M1 Consensus Choice — Scorecard Maturation

**Status:** DESIGN MATURED (no runtime; no candidate defaulted to Raft)  
**Cycle / Checkpoint:** 50 / CP-0054  
**Date:** 2026-09-26 America/New_York (EDT)  
**Theme:** (D) M1 scorecard maturation from `0.19_SCOPE_FROZEN`  
**Prior:** CP-0050 `M1_CONSENSUS_CHOICE_DESIGN` (empty candidate scores)  
**ABORT rule:** M1..M3 fail review → N stays 2  
**Runtime:** Raft / N>2 / M4+ remain **NO_HELD**

---

## 1. Intent

Mature the M1 pre-RFC scorecard by (a) filling provisional axis scores for
candidates C0..C4, (b) applying the ≥80 ratification rule for any *unlock*
choice, and (c) recording a written **NO_CONSENSUS_YET** justification when no
unlock-eligible candidate clears the bar with Mesh fence evidence.

This CP does **not** pick Raft, does **not** implement consensus, and does
**not** unlock G_Raft or G_Ngt2.

Blueprint: `scorecard ≥80 to ratify; no candidate → written justification`.

## 2. Hard rules (unchanged)

1. **`no default = Raft`** — Raft is C1 only; never auto-selected.
2. Preserve dual_primary=0, minority-write halt, clock-skew refuse-join, manifest parity.
3. Compatible with attested identity + OBS + audit hash-chain.
4. No silent plaintext; no GIA/ML-as-product smuggle.
5. Document ABORT → safe N=2 fallback.
6. Runtime Raft / N>2 remain **NO_HELD** regardless of design scores.

## 3. Axes (100 pts) — ratification threshold ≥80

| Axis | Pts | What “good” means |
|------|----:|-------------------|
| Safety under partition | 20 | No dual-primary; no minority split-brain writes |
| Fence compatibility | 15 | Maps cleanly to H3/H6/H7 ABORT behaviors |
| Liveness @N=2 today | 10 | Does not regress current N=2 heal path |
| Liveness path @N>2 (design) | 10 | Clear theoretical progress under majority |
| Operational complexity | 10 | Ops burden, runbooks, footguns (higher=simpler) |
| Audit / OBS fit | 10 | Receipts, HLC, queryable decisions |
| WAN / HLC readiness | 10 | Works with M3 latency/partition model |
| Unlock evidence cost | 10 | Clarity/cheapness of tests for G_Raft/G_Ngt2 |
| Reversibility | 5 | Can stay on N=2 fenced heal if rejected |

**Ratify (unlock) threshold:** total ≥ **80** *and* fence-probe matrix design-green
*and* GOV.2 later. Below 80 → keep N=2; no unlock prose.

**Baseline note:** C0 (stay N=2) is scored as *status-quo viability*, not as an
N>2 unlock choice. Unlock ratification applies to C1..C5 only.

## 4. Provisional candidate scores (design-only)

Scores are **provisional design estimates** (CP-0054). They are not GOV
unlocks and not runtime authorization. Evidence gaps intentionally suppress
unlock-eligible totals (RK53: no vibes).

| Axis | C0 Stay N=2 | C1 Raft | C2 Paxos | C3 Flex/EPaxos | C4 Mesh-native |
|------|------------:|--------:|---------:|---------------:|---------------:|
| Safety (20) | 20 | 16 | 15 | 14 | 17 |
| Fence compat (15) | 15 | 8 | 7 | 7 | 12 |
| Liveness N=2 (10) | 10 | 7 | 6 | 6 | 9 |
| Liveness N>2 (10) | 0 | 9 | 8 | 9 | 7 |
| Ops complexity (10) | 10 | 6 | 4 | 5 | 6 |
| Audit/OBS (10) | 10 | 7 | 7 | 6 | 8 |
| WAN/HLC (10) | 5 | 6 | 5 | 8 | 7 |
| Unlock evidence (10) | 10† | 5 | 4 | 4 | 5 |
| Reversibility (5) | 5 | 4 | 3 | 3 | 4 |
| **Total** | **85†** | **68** | **59** | **62** | **75** |

† C0 total is baseline viability, **not** an N>2 unlock score. Unlock evidence
axis for C0 means “no unlock required / evidence already on N=2 path.”

### Narrative per candidate

- **C0 Stay N=2 fenced_primary_heal** — Proven dual_primary=0 path; always
  available ABORT fallback. Not a consensus-protocol pick for N>2.
- **C1 Raft (etcd-class)** — Strong classical majority story; **not default**.
  Fence-compat proof vs H3/H6/H7 incomplete; WAN leader tax; unlock evidence
  cost high → **68 < 80**.
- **C2 Paxos / Multi-Paxos** — Classic safety; higher ops/complexity cost;
  weaker Mesh fence mapping today → **59 < 80**.
- **C3 Flexible Paxos / EPaxos-class** — WAN-friendly claims; Mesh evidence and
  audit/OBS mapping thin → **62 < 80**.
- **C4 Mesh-native fence+quorum journal** — Best conceptual fence fit; still
  design exploration only; no probe matrix / RFC evidence → **75 < 80**.
- **C5 Other** — empty slot; must fill all axes before scoring.

## 5. NO_CONSENSUS_YET — written justification

**Verdict:** **NO_CONSENSUS_YET** for any N>2 / G_Raft / G_Ngt2 unlock.

**Why (P-18 / RK53):**

1. No unlock-eligible candidate (C1..C4) reaches **≥80** on the matured scorecard.
2. Fence-probe matrix is **not** design-green for C1..C4 (H3/H6/H7 mapping gaps).
3. M2 membership/rejoin SM **designed** (CP-0059); M3 WAN+HLC model **designed** (CP-0060).
   Remaining unlock blockers: fence-probe matrix + GOV — not absence of M2/M3 drafts.
4. Selecting Raft by familiarity would violate **`no default = Raft`** and GOV.6
   (no prose unlock).
5. Safe action: **N stays 2**; C0 remains the operational baseline; runtime
   Raft/N>2 stay **NO_HELD**.

This written justification satisfies blueprint M1: *no candidate → written
justification*. A future RFC CP may re-score after fence-compat proofs and
M2/M3 drafts exist.

## 6. Evidence checklist (still open for future unlock)

- [x] Scorecard axes + ≥80 threshold documented
- [x] Provisional candidate scores filled (this CP)
- [x] Written justification if rejecting all unlock candidates (NO_CONSENSUS_YET)
- [ ] Fence probe matrix green at design review
- [x] M2 membership/rejoin SM draft (beyond pointer) — CP-0059
- [x] M3 WAN+HLC model draft (beyond pointer) — CP-0060
- [ ] GOV.2 quorum + evidence-bundle (GOV.3)
- [ ] Explicit: runtime still gated; prose unlock forbidden (GOV.6)

## 7. Non-goals

- Implementing Raft/Paxos/any consensus runtime
- Opening N>2 topology
- Defaulting any candidate to Raft
- Multi-primary reconciliation (M5 NO_HELD)
- GIA / train / SaaS / economy

**NO_HELD:** Raft,N>2,multi-primary,ML,R2,R3,plaintext,Vault-ACME-req,GIA,SLO_chase,tag_schema,EVERY_fsync

## Related

- `docs/design/fabric/M1_CONSENSUS_CHOICE_DESIGN.md` (CP-0050 base)
- `docs/design/fabric/M2_MEMBERSHIP_REJOIN_POINTER.md`
- `docs/design/fabric/M3_WAN_MODEL_DESIGN.md` (CP-0060)
- `docs/design/fabric/M3_WAN_PARTITION_HLC_POINTER.md` (stub)
- `docs/planning/0.19_SCOPE_FROZEN.md`
- `council/blueprint/FINAL_BLUEPRINT_ROOT.md` (L4 M1)

---

## Addendum — Cycle 68 / CP-0072 re-research

C67 re-weighted axes and C5 FQ-ED sketch live in
`docs/planning/D2_M1_CONSENSUS_CANDIDATE_RERESEARCH.md` and
`docs/design/fabric/M1_CONSENSUS_RERESEARCH.md`.

**Verdict unchanged:** **NO_CONSENSUS_YET** (closest C5=78 under new weights; Raft further demoted via explicit no-Raft axis). This addendum does not alter CP-0054 provisional scores under the *old* axes; those remain historical.

