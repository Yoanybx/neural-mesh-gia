# F4 — Product-enable safety-case amendment (DESIGN)

**Status:** **DESIGN** — product permanent-vs-session policy binding under D4 F4  
**Does NOT** flip `LIVE_API_ENABLED` · **does NOT** invent operator product ACK · **does NOT** unlock NO_HELD  
**Date:** 2026-09-28 ~22:42 EDT (America/New_York)  
**Author (docs):** Grok Bot `<grok-bot@local>`  
**Tip at draft base:** `c2ba1e2` (CP-0079 multi-canary n=6; permanent enable policy; LIVE_API=False)  
**Cycle / CP:** 76 / **CP-0080**  
**Package:** **0.18.0 HELD** · Gate1 **SIGNED ENABLE_UNDER_FENCES** · module LIVE **False** · M1=NO_CONSENSUS_YET · D3 NOT ACKed

**Design-seal companion:** `docs/planning/F4_DESIGN_SEALED.md`  
**Unsigned product ACK draft:** `docs/planning/F4_PRODUCT_ENABLE_ACK_DRAFT.md`  
**Upstream:** D4 F4 · Gate2 live safety amendment · D1 safety maturation · `LIVE_API_PERMANENT_ENABLE_POLICY.md` · Gates 5–6 · CP-0075..0079

---

## 0. What this is / is not

| Is | Is not |
|----|--------|
| Safety-case **amendment** distinguishing **session/canary LIVE** vs **product permanent LIVE** | A signed product-enable ACK |
| Binding of P1–P9 (`LIVE_API_PERMANENT_ENABLE_POLICY.md`) to D4 F4 | Permission to set module `LIVE_API_ENABLED=True` in git |
| Clarifies ENABLE_UNDER_FENCES (already SIGNED) ≠ F4 product permanent | A re-signature of ENABLE_UNDER_FENCES |
| DESIGN sealable under Gemini **free** path fences | Vertex paid / streaming / NO_HELD unlock |

**Invariant (D4 F4):** `live=ENABLED` (product / permanent module or `live_adapter.enabled` default True across restarts) requires a **separate cycle** + **separate operator ACK** + **this amendment** + Gates 1–6 evidence. ENABLE_UNDER_FENCES covers **fenced canary / measurement windows only**.

---

## 1. Layer split (binding — do not conflate)

| Layer | Covered by ENABLE_UNDER_FENCES (SIGNED 「Aprobado」)? | Covered by F4 product ACK? |
|-------|------------------------------------------------------|----------------------------|
| Runtime LIVE window under Gate5 + I5 (session) | **Yes** (canary / multi-canary) | No (orthogonal; restore False after) |
| Module constant `LIVE_API_ENABLED=True` as product default | **No** | **Yes — required (P7)** |
| `live_adapter.enabled=true` persistent product flag | **No** | **Yes — required** |
| CI `live_api_in_ci` | **Never** | **Never** |
| Free-tier Gemini advisory peer under fences | Yes (session) | Permanent product still F4 |
| Vertex paid / streaming / NO_HELD | **No** | Separate ACK beyond F4 free-path |

**Today:** ENABLE_UNDER_FENCES **SIGNED**; permanent policy on disk (**default False**); F4 product ACK **UNSIGNED** → module **must** stay False.

---

## 2. Amendment to D1 / Gate2 for product-enable

Extends Gate2 live safety amendment + D1 for the **product permanent** path (design only until F4 ACK):

| Topic | Session/canary (ENABLE signed) | Product permanent (needs F4 ACK) |
|-------|--------------------------------|----------------------------------|
| Blast radius | One canary / pack attempt; restore Refuse | Continuous advisory peer slot under I5 watch; still advisory≠SoT |
| Kill | Mid-window I5 → Refuse + ABORT (M-KILL-*) | Same chain **plus** ops budget (M-KILL-2) continuous; re-walk Gate5 after kill (M-KILL-3) |
| Key compromise | Revoke handle → Refuse; module stays False | Same + force product flags False; operator re-ACK before any permanent True restore |
| Continuity | Quarantine on kill/anomaly | Same; never silent ACTIVE after peer failure |
| Evidence | Canary / multi-canary ledger | Continuous ledger completeness (M-LEDGER); claim hygiene: permanent ≠ 100% without fences |
| Judges | Mesh ABORT > ACCEPT; conflict/missing fail-closed (M-ABORT-3) | Same; no auto-majority execute as product auth |

---

## 3. Preconditions for product permanent True (P1–P9)

All required; missing any → **must** stay False (`LIVE_API_PERMANENT_ENABLE_POLICY.md` §3):

| # | Criterion | Status @ CP-0080 |
|---|-----------|------------------|
| P1 | ENABLE_UNDER_FENCES SIGNED | **Met** |
| P2 | Gates 2–4 ENABLE_READY + Gate5 walked | **Met** |
| P3 | Authorized impl (CP-0075 + CP-0078) | **Met** (v0 unary) |
| P4 | Multi-canary n≥5 + edges | **Met** (CP-0079 n=6) |
| P5 | Gate6 measurement seal-candidate + M-KILL/M-ABORT | **Met pack** + **M-KILL-2 budget** + **M-ABORT-3** (this CP) |
| P6 | Permanent enable policy on disk | **Met** |
| P7 | **F4 product-enable operator ACK** | **OPEN — do not invent** |
| P8 | I5 + rollback owner + audit + secrets oob | Ops ongoing |
| P9 | No CI live; free-tier bounds | Binding |

**Until P7 signed:** agents **must not** flip module/`live_adapter` defaults to True.

---

## 4. Relation to already-signed ENABLE_UNDER_FENCES

Operator chat **「Aprobado」** (~19:41 ET) signed **ENABLE_UNDER_FENCES** for the **fenced Gemini free canary / measurement** path. That signature:

- **Does** authorize temporary runtime LIVE under Gate5 + I5 with restore False  
- **Does not** authorize product permanent module True  
- **Must not** be rewritten or extended by bots into an F4 product ACK  

F4 product ACK (draft: `F4_PRODUCT_ENABLE_ACK_DRAFT.md`) is a **separate** operator-written artifact naming permanent module / `live_adapter` intent.

---

## 5. Explicit non-goals

- Setting `LIVE_API_ENABLED=True` in source without P7  
- Claiming 「listo」 product-permanent from ENABLE alone  
- Push / tags / secrets in git / NO_HELD / D3 / Vertex paid / streaming as implied  

---

## 6. Related

- `F4_DESIGN_SEALED.md` · `F4_PRODUCT_ENABLE_ACK_DRAFT.md`  
- `LIVE_API_PERMANENT_ENABLE_POLICY.md` · `GATE2_LIVE_SAFETY_CASE_AMENDMENT.md`  
- `D1_L_JUDGE_SAFETY_CASE_MATURATION.md` · `council/COUNCIL_AGREEMENT_D4.md`  
- `GATE1_ENABLE_UNDER_FENCES_ACK_SIGNED.md` · `GATE6_MULTI_CANARY_MEASUREMENT.md`  
- `docs/ops/M_KILL_2_OPS_KILL_REFUSE_BUDGET.md` · `EVIDENCE_CP_0080_KILL_ABORT_DRILLS.md`

---

*End F4_PRODUCT_ENABLE_SAFETY_AMENDMENT — DESIGN; ENABLE ≠ product permanent; P7 OPEN.*
