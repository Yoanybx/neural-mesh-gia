# Council Agreement — D4 External Review Triple (LOCKED)

**STATUS:** LOCKED — triple-council agreement (DeepSeek + ChatGPT + Grok)  
**Date:** 2026-09-26 America/New_York (EDT)  
**Topic:** D4_EXTERNAL_REVIEW_TRIPLE  
**Tip reality NOW:** feature tip `65e4985` / **CP-0070** VERIFIED · D4 pause commit `703f46c` · pytest **1078/0** · package **0.18.0 HELD** · **live=DISABLED** · **M1=NO_CONSENSUS_YET** · **MESH_PERF_EXPERIMENTAL=OFF** · pkg0190 **NOT_OPENED** · v0.19 tag **ABSENT**  
**Inputs:**  
- `council/CHATGPT_REPLY_ORCHESTRATOR_D4_REVIEW.md`  
- `council/D4_CHATGPT_FINDINGS.md` (durable extract D4-A..K — fence F2)  
- `council/NOTE_D4_EXTERNAL_REVIEW_PAUSE.md`  
- `council/NOTE_D4_GROK_POSITION.md`  
- `council/DEEPSEEK_REPLY_D4_TRIPLE_AGREEMENT.md` (**PASS_WITH_FENCES**)  
- `council/CHATGPT_REPLY_D4_TRIPLE_AGREEMENT.md` (**PASS_WITH_FENCES**)  
- `council/DEEPSEEK_REPLY_CYCLE66.md` (operator queue D1..D5)  
**Related locked:** `COUNCIL_AGREEMENT_HYPERBRAIN_ASTRA.md` · `COUNCIL_AGREEMENT_NORTH_STAR.md` · `COUNCIL_AGREEMENT_CYCLE66.md`

---

## BEST (agreed)

**Orchestrator design set stays sealed (CP-0064..0070). ChatGPT D4 review is binding governance debt (D4-A..K). DeepSeek C66 operator IDs stay. D1 absorbs ChatGPT authority/safety/continuity/oversight/rollback/evidence artifacts. This lock is governance bookkeeping — not verification, not live enable, not hyperbrain proof.**

---

## Operator queue IDs (DeepSeek C66 — authoritative labels)

| ID | Meaning | Status under this lock |
|----|---------|------------------------|
| **D1** | L_judge live-adapter **safety-case maturation** (design-only) | **NEXT after lock** — must absorb D4-A..K + ChatGPT amendments |
| **D2** | M1 consensus candidate **re-research** (design-only) | After D1; no skip (F10) |
| **D3** | Perf A/B (**ACK-gated**; flag OFF) | After D2; needs explicit operator ACK to flip flag (F8) |
| **D4** | External review pause | **DONE** (ChatGPT review + this triple lock) |
| **D5** | Hold | Available; not selected by this agreement |

ChatGPT’s remap (authority → safety → evaluation) is **substance inside D1**, not a rename of these IDs. ChatGPT “evaluation readiness” = **D1 exit criteria**, not DeepSeek D3.

---

## Binding debt inside D1 (must cite D4-A..K)

From `D4_CHATGPT_FINDINGS.md`:

| ID | Debt |
|----|------|
| D4-A | Authority Matrix (propose/approve/veto/execute) |
| D4-B | Consensus semantics (+ independence / correlation — ChatGPT amendment) |
| D4-C | Continuity limits (verified state only) |
| D4-D | Oversight I5 bounds |
| D4-E | Evaluation categories beyond pytest |
| D4-F | Claim hygiene |
| D4-G | Decision lifecycle / identity-trust / policy versioning / failure classes |
| D4-H | Safety invariants + containment + rollback (**incl. rollback verification** — ChatGPT amendment) |
| D4-I | Evidence chain + explainability (+ provenance, policy version, audit completeness — ChatGPT amendment) |
| D4-J | Acceptance metrics (+ **adversarial disagreement** handling — ChatGPT amendment) |
| D4-K | Signoff conditions before any live *discussion* |

**F1:** D1 evidence-bundle MUST cite these section IDs or D1 cannot seal.

---

## Order post-lock

```text
D4 DONE + this TRIPLE LOCK
  → D1 (design/docs only; live=DISABLED; cite D4-A..K)
  → D2 (M1 re-research; design-only)
  → D3 (perf A/B only after explicit ACK)
  → reconsider live=ENABLED only via SEPARATE cycle + SEPARATE operator ACK + safety-case amendment
```

Strict: if D1 slips, D2/D3 do not skip ahead (**F10**).

---

## Fences (union DeepSeek F1–F10 + ChatGPT)

1. **F1** D1 evidence-bundle cites D4-A..K or cannot seal.  
2. **F2** Findings durable in `D4_CHATGPT_FINDINGS.md` (no prose-only debt).  
3. **F3** D1 design-only; does not enable live.  
4. **F4** live=ENABLED = separate cycle + separate operator ACK + safety-case amendment; this agreement does not pre-authorize.  
5. **F5** Hyperbrain/Astra LOCKED = design alignment ≠ proof; no surpass claim; no consciousness vocabulary outside L6.  
6. **F6** Orchestrator CP-0064..0070 stays sealed; this agreement adds no new feature scope.  
7. **F7** pkg0190 NOT_OPENED; v0.19 tag ABSENT; 0.18.0 held; no tag movement under this ACK.  
8. **F8** MESH_PERF_EXPERIMENTAL stays OFF until explicit operator ACK for D3.  
9. **F9** M1=NO_CONSENSUS_YET; no consensus default introduced.  
10. **F10** Strict D1→D2→D3 order.  
11. **CG1** ACK = governance/design alignment only, not implementation approval.  
12. **CG2** No feature CP mint before this triple lock (satisfied at seal). After lock: only fenced design/docs CPs unless separately authorized.  
13. **CG3** No review→ops transition without separate operator ACK.  
14. **CG4** D1 required artifacts include independence/correlation analysis, adversarial disagreement criteria, rollback **verification**, and observability provenance (policy version, evidence refs, audit completeness).

---

## PARKED / NO_HELD (unchanged)

| Item | Status |
|------|--------|
| L_GIA | NO_HELD |
| SAAS | PARKED |
| ECONOMY | PARKED |
| TRAIN_70B | DO_NOT_TRAIN_70B_NOW |
| NO_HELD list | Raft, N>2, multi-primary, ML, R2, R3, plaintext, Vault-ACME-req, GIA, SLO_chase, tag_schema, EVERY_fsync — **unchanged** |

---

## Signatures (ACK)

| Voice | Verdict | When (ET) |
|-------|---------|-----------|
| **DeepSeek** | PASS_WITH_FENCES — ACK findings, ID bridge, order; F1–F10 | 2026-09-26 |
| **ChatGPT** | PASS_WITH_FENCES — findings preserved; ID bridge; order; F1–F10; amendments CG4 | 2026-09-26 |
| **Grok** | ACK — bridge IDs; durable D4-A..K; union fences; seal without unlock | 2026-09-26 |

**Sealed:** 2026-09-26. Not an unlock. Not live enable. Not operational readiness. Not a claim we surpass Astra/GPT. Tip remains `65e4985` / CP-0070 / `0.18.0 HELD` / live=DISABLED.

**NEXT_AFTER_LOCK (non-binding observation):** Operator may authorize **D1** design-only cycle after confirming durable findings path; council does not select D1/D2/D3 for the operator.

---

*End COUNCIL_AGREEMENT_D4 — LOCKED.*
