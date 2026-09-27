# D2 — M1 Consensus Candidate Re-Research (Cycle 68 / CP-0072)

**Status:** DESIGN ONLY — scorecard re-research; **no runtime**; **no Raft default**  
**Cycle / Checkpoint:** 68 / CP-0072  
**Date:** 2026-09-26 America/New_York (EDT)  
**Authority:** DeepSeek C67 VERDICT PASS; NEXT = D2; COUNCIL_AGREEMENT_D4 LOCKED (F10: D1→D2→D3)  
**Prior tip:** feature `c6e824a` / CP-0071 (D1 sealed)  
**Composes:** CP-0050 (M1 base) · CP-0054 (scorecard maturation) · CP-0071 (D1 consensus draft §4) · CP-0059 (M2) · CP-0060 (M3)  
**Runtime:** Raft / N>2 / M4+ remain **NO_HELD** · live=DISABLED · MESH_PERF_EXPERIMENTAL=OFF · pkg0190 NOT_OPENED · v0.19 ABSENT · 0.18.0 HELD

---

## 0. D2 opening — gate checks (F2 / F10 / D1 exit)

### 0.1 Fence F2 — durable D4 findings

| Check | Result |
|-------|--------|
| `council/D4_CHATGPT_FINDINGS.md` exists | **PASS** (durable extract D4-A..K) |
| `council/COUNCIL_AGREEMENT_D4.md` LOCKED | **PASS** (tip `97735e9`) |

### 0.2 D1 exit criteria (from `docs/planning/D1_L_JUDGE_SAFETY_CASE_MATURATION.md` §10)

| Criterion | Status | Notes |
|-----------|--------|-------|
| Authority model frozen (§3 / D4-A) | **PASS** | Authority Matrix in CP-0071 |
| Consensus definition status explicit (D4-B) | **PASS** | Draft + **NO_CONSENSUS_YET**; no default |
| Oversight powers bounded (§6 / D4-D) | **PASS** | I5 bounds CP-0069 compose |
| Continuity limits (§5 / D4-C) | **PASS** | Verified-state-only |
| Rollback/containment + RV-1..RV-7 (D4-H) | **PASS** | CP-0071 |
| Evidence chain / provenance (D4-I) | **PASS** | CP-0071 |
| Acceptance criteria measurable (D4-E/J) | **PASS** (design) | Categories + metrics documented |
| Claim hygiene (D4-F) | **PASS** | Reframed |
| Disagreement process (§4.4) | **PASS** (design) | Mock adversarial scenarios |
| No hidden review→ops (F3/F4) | **PASS** | live=DISABLED unchanged |
| **D1 seal exit** (artifacts + F1 + tests + live=DISABLED) | **PASS** | CP-0071 VERIFIED |
| **D1 live-discussion exit** (`d1_exit_ready_for_live`) | **NOT PASS / must stay false** | Separate ACK + safety-case amendment (F4) |

**Gaps carried into D2 (not D1 failures):**

1. Protocol consensus algorithm still **unselected** (intentional; F9) — this D2 cycle.
2. Fence-probe matrix for C1..C5 still **not** design-green (unlock blocker).
3. GOV.2 quorum + evidence-bundle for G_Raft/G_Ngt2 still open.
4. Independence/correlation **requirements** recorded in D1 §4.3; not yet proven for any unlock candidate.

**F10:** D1 sealed before D2 started → D2 authorized.

---

## 1. Intent

Re-score M1 candidates against **updated** DeepSeek C67 criteria, optionally draft a custom sketch (C5), and either:

- **Ratify** a candidate with total ≥ **80**, or
- Document **NO_CONSENSUS_YET** again with written justification.

This CP does **not** implement consensus, does **not** open N>2, does **not** default to Raft, does **not** enable live, does **not** flip MESH_PERF_EXPERIMENTAL, and does **not** open pkg0190.

---

## 2. Updated scorecard axes (100 pts) — C67 weights

| Axis | Pts | What “good” means (D2) |
|------|----:|------------------------|
| **Safety** | 30 | No dual-primary; no minority split-brain writes; ABORT-prefer under ambiguity |
| **Liveness** | 15 | Progress under majority / heal; does not regress N=2 fenced heal |
| **Fence-compat** | 15 | Maps cleanly to H3/H6/H7 ABORT behaviors + Mesh fence semantics |
| **No-Raft** | 10 | Non-Raft preference axis — Raft scores **0** here (hard rule: no default = Raft) |
| **WAN-tolerance** | 15 | Works with M3 latency/partition + HLC model (CP-0060) |
| **Adversary-resistance** | 10 | Independence/correlation honesty + adversarial disagreement (D1 §4.3–4.4 / D4-B / D4-J / CG4) |
| **Complexity** | 5 | Ops burden, runbooks, footguns (higher = simpler) |

**Ratify threshold:** unlock-eligible total ≥ **80** *and* fence-probe matrix design-green *and* GOV.2 later.  
Below 80 → keep N=2; written **NO_CONSENSUS_YET**.  
C0 = status-quo baseline only (not an N>2 unlock score).

**Hard rules (unchanged):**

1. `no default = Raft` — Raft is C1 only; never auto-selected.
2. Preserve dual_primary=0, minority-write halt, clock-skew refuse-join, manifest parity.
3. Compatible with attested identity + OBS + audit hash-chain.
4. No silent plaintext; no GIA/ML-as-product smuggle.
5. Document ABORT → safe N=2 fenced_primary_heal fallback.
6. Runtime Raft / N>2 remain **NO_HELD** regardless of design scores.
7. Multi-judge ≠ independence ≠ protocol consensus (D1 §4).

---

## 3. Composition with D1 consensus draft (CP-0071 §4)

D2 **does not replace** D1 vocabulary; it scores *protocol* candidates against it.

| D1 term | Role in D2 scoring |
|---------|-------------------|
| Advisory agreement | Not protocol consensus; does not unlock M1 |
| Evidence convergence | Feeds **adversary-resistance** (diversity requirement) |
| Protocol consensus | What C1..C5 compete to become — still unset until ≥80 + probes + GOV |
| Execution authorization | Remains A3/A4 human gate — never judge/protocol majority alone |
| Independence / correlation (CG4) | Suppresses scores unless candidate documents correlation analysis |
| Adversarial disagreement (CG4) | Prefer ABORT/escalate; correlated blind-spot agreement = weak evidence |

---

## 4. Candidates

| ID | Candidate | Unlock-eligible? |
|----|-----------|------------------|
| C0 | Stay N=2 **fenced_primary_heal** (status quo) | No (baseline) |
| C1 | Raft (etcd-class) | Yes — **not default** |
| C2 | Paxos / Multi-Paxos family | Yes |
| C3 | Flexible Paxos / EPaxos-class | Yes |
| C4 | Mesh-native fence+quorum journal (prior sketch) | Yes |
| C5 | **FQ-ED** — Fence-Quorum + Evidence-Diversity (custom sketch, this CP) | Yes |

### 4.1 C5 custom sketch (design-only)

**Name:** Mesh Fence-Quorum + Evidence-Diversity (**FQ-ED**)

**Sketch intent:** Prefer a non-Raft quorum journal that *inherits* Mesh fence ABORT semantics and D1 evidence-diversity / adversarial-disagreement rules, with N=2 fenced heal as permanent ABORT fallback.

| Element | Design rule |
|---------|-------------|
| Membership | Compose M2 SM (JOINING→…→LEFT→REJOIN); no silent ACTIVE after LEFT |
| Quorum | Majority of *attested Active* members; never minority write |
| Journal | Append-only hash-chained decisions; OBS-queryable |
| Fence map | H3 dual_primary→ABORT; H6 minority→halt; H7 skew→refuse-join |
| Evidence diversity | Require ≥2 evidence *kinds* (not N copies of one blind spot) before any “consensus claim” |
| Correlation | Distinct engine_ids ⇏ independent failure; shared provider/weights = high correlation |
| Adversarial | Judges/members agree on unsafe → Mesh policy + I5 still ABORT; contradict → no silent majority |
| WAN | HLC required (M3); leaderless or rotating proposer preferred over sticky WAN leader |
| ABORT fallback | Always revert to C0 N=2 fenced_primary_heal |
| Runtime | **NO_HELD** until fence-probe matrix + GOV unlock |

C5 is a **sketch**, not an implementation and not a silent default.

---

## 5. Re-scored provisional totals (design-only)

Scores are **provisional design estimates** under C67 weights. Evidence gaps intentionally suppress unlock-eligible totals (RK53: no vibes). Fence-probe matrix not green → fence-compat and safety capped below theoretical max for C1..C5.

| Axis | max | C0† | C1 Raft | C2 Paxos | C3 Flex/EPaxos | C4 Mesh-nat | C5 FQ-ED |
|------|----:|----:|--------:|---------:|---------------:|------------:|---------:|
| Safety | 30 | 30 | 20 | 18 | 17 | 22 | 23 |
| Liveness | 15 | 10 | 12 | 10 | 12 | 10 | 11 |
| Fence-compat | 15 | 15 | 6 | 5 | 5 | 12 | 12 |
| No-Raft | 10 | 10 | **0** | 8 | 8 | 10 | 10 |
| WAN-tolerance | 15 | 7 | 8 | 6 | 12 | 10 | 11 |
| Adversary-resistance | 10 | 8 | 5 | 4 | 4 | 6 | 8 |
| Complexity | 5 | 5 | 3 | 2 | 2 | 3 | 3 |
| **Total** | **100** | **85†** | **54** | **53** | **60** | **73** | **78** |

† C0 = baseline viability only — **not** an N>2 unlock score.

### 5.1 Narrative

- **C0** — Proven dual_primary=0 path; permanent ABORT fallback. Not a protocol unlock.
- **C1 Raft** — Classical majority story; **no-Raft axis = 0** by design; fence-compat incomplete; WAN leader tax; adversary model (single leader / non-Byzantine) weak vs CG4 → **54 ≪ 80**. Selecting Raft by familiarity would violate hard rule.
- **C2 Paxos** — Classic safety; high ops cost; weak Mesh fence mapping → **53**.
- **C3 Flex/EPaxos** — Best WAN claim among classics; thin Mesh fence + adversary evidence → **60**.
- **C4 Mesh-native** — Best prior fence fit; lacks D1 evidence-diversity / adversarial formalization → **73**.
- **C5 FQ-ED** — Closest: absorbs D1 §4.3–4.4 into adversary-resistance; non-Raft; fence-first. Still **78 < 80** because fence-probe matrix is not design-green and N>2 safety evidence is absent (scores suppressed, not vibes-inflated).

---

## 6. Decision — NO_CONSENSUS_YET (written justification)

**Verdict:** **NO_CONSENSUS_YET** for any N>2 / G_Raft / G_Ngt2 unlock.

**Why (P-18 / RK53 / F9):**

1. No unlock-eligible candidate (C1..C5) reaches **≥80** on the C67 re-weighted scorecard.
2. Closest is **C5 FQ-ED at 78** — promising sketch, not ratification.
3. Fence-probe matrix remains **not** design-green for C1..C5 (H3/H6/H7 mapping gaps).
4. D1 independence/correlation requirements are **recorded**, not yet satisfied with evidence for any candidate.
5. Selecting Raft would score **0** on the explicit no-Raft axis and violate `no default = Raft`.
6. Safe action: **N stays 2**; C0 remains operational baseline; runtime Raft/N>2 stay **NO_HELD**; M1 status stays **NO_CONSENSUS_YET**.

**What changed vs CP-0054:** axes re-weighted (safety↑, adversary-resistance added, no-Raft explicit); C5 custom sketch drafted; Raft further demoted; C5 is new “closest” at 78 (was C4 at 75 under old axes).

**What did not change:** no runtime; no Raft default; no N>2; no live enable; no pkg0190; no GIA/train/SaaS.

---

## 7. Independence / correlation & adversarial disagreement (affect M1)

Carried from D1 §4.3–4.4 / D4-B / D4-J / CG4 into **adversary-resistance** scoring:

| Rule | Effect on M1 |
|------|----------------|
| Distinct engine_ids ⇏ independent failure | Candidates that assume multi-judge = Byzantine quorum are penalized |
| Shared provider / weights / prompt = high correlation | Evidence diversity required before any consensus *claim* |
| Correlated blind-spot agreement = weak evidence | Suppresses safety + adversary scores until diversity proven |
| Adversarial agreement on unsafe → still ABORT | Protocol cannot outrank Mesh policy + I5 |
| Contradict / unavailable → no invented vote | Prefer ABORT/FALLBACK; no silent majority |

These rules raise the bar for C1..C3 (classical protocols without Mesh-native ABORT/diversity story) and partially credit C5 (sketch includes them) without granting ≥80 without evidence.

---

## 8. Evidence checklist

- [x] Updated axes (C67 weights) documented; sum = 100
- [x] Re-scores filled for C0..C5
- [x] C5 FQ-ED custom sketch drafted (design-only)
- [x] Written justification → **NO_CONSENSUS_YET**
- [x] D1 consensus draft composed (vocabulary + CG4)
- [x] F2 confirmed (`D4_CHATGPT_FINDINGS.md`)
- [x] D1 seal-exit PASS / live-discussion-exit NOT PASS noted
- [ ] Fence-probe matrix green at design review (still open)
- [ ] GOV.2 quorum + evidence-bundle (GOV.3)
- [ ] Explicit runtime unlock (GOV.6 forbids prose unlock) — still gated

---

## 9. Non-goals / must-stay-false

| Flag / claim | Must stay |
|--------------|-----------|
| Runtime Raft / N>2 | **NO_HELD** |
| M1 algorithm default | **NO_CONSENSUS_YET** (no silent Raft) |
| `live_adapter.enabled` | **false** |
| `MESH_PERF_EXPERIMENTAL` | **OFF** |
| pkg0190 / v0.19.0 tag | **NOT_OPENED / ABSENT** |
| GIA / train / SaaS / settlement | **NO_HELD / PARKED** |
| D3 started | **No** (F10: after D2 + separate ACK for flag) |

**NO_HELD:** Raft,N>2,multi-primary,ML,R2,R3,plaintext,Vault-ACME-req,GIA,SLO_chase,tag_schema,EVERY_fsync

---

## 10. Related

- `docs/design/fabric/M1_CONSENSUS_CHOICE_DESIGN.md` (CP-0050)
- `docs/design/fabric/M1_SCORECARD_MATURATION.md` (CP-0054)
- `docs/design/fabric/M1_CONSENSUS_RERESEARCH.md` (this cycle pointer + tables)
- `docs/planning/D1_L_JUDGE_SAFETY_CASE_MATURATION.md` §4 (consensus draft)
- `docs/design/fabric/M2_MEMBERSHIP_REJOIN_DESIGN.md` (CP-0059)
- `docs/design/fabric/M3_WAN_MODEL_DESIGN.md` (CP-0060)
- `council/D4_CHATGPT_FINDINGS.md` · `council/COUNCIL_AGREEMENT_D4.md`
- `council/COUNCIL_AGREEMENT_CYCLE68.md`

*End D2 M1 re-research — design-only; M1=NO_CONSENSUS_YET.*
