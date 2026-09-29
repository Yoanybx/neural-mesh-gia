# F4 — Product-enable operator ACK — **UNSIGNED DRAFT (HISTORICAL)**

**Status:** **HISTORICAL UNSIGNED DRAFT** — superseded by **SIGNED** artifact  
**Signed copy:** `docs/planning/F4_PRODUCT_ENABLE_ACK_SIGNED.md` — operator **「Firmalo por mi」** 2026-09-28 ~23:22 ET  
**Effect (when signed):** Authorizes **product permanent** enable under P1–P9 + F4 amendment (separate from ENABLE_UNDER_FENCES canary intent).  
**This draft file alone does not authorize flips**; use the SIGNED copy as the ACK of record.

**Date drafted:** 2026-09-28 ~22:42 EDT (America/New_York)  
**Author (draft only):** Grok Bot `<grok-bot@local>`  
**Date signed:** 2026-09-28 ~23:22 EDT — see SIGNED artifact  
**Operator ACK:** Joan / Yoan V — **「Firmalo por mi」** (recorded on SIGNED copy) · follow-up **「Ponlo live y seguimos」**  
**Tip at draft:** atop `c2ba1e2` / CP-0080 F4 design seal  
**Tip at sign:** `c64c0e0`  
**Package posture at draft:** **0.18.0 HELD** · **LIVE_API_ENABLED=False** · Gate1 **SIGNED ENABLE_UNDER_FENCES** · F4 design **SEALED** · **NO_HELD** stays NO_HELD

**Prior ENABLE (session/canary — not this ACK):** `GATE1_ENABLE_UNDER_FENCES_ACK_SIGNED.md`  
**Amendment:** `F4_PRODUCT_ENABLE_SAFETY_AMENDMENT.md` · seal `F4_DESIGN_SEALED.md`  
**Policy:** `LIVE_API_PERMANENT_ENABLE_POLICY.md`

---

## 0. What this is / is not

| Is | Is not |
|----|--------|
| **Unsigned** draft for **product permanent** enable (module / `live_adapter` default True in ACK’d env) | A signed ACK (see SIGNED copy) |
| Separate cycle from ENABLE_UNDER_FENCES (D4 F4) | A re-use of 「Aprobado」 canary intent |
| Requires P1–P9 all met including this signature (P7) | Permission to flip before operator signs |
| Compatible with leaving False after packs | CI live / Vertex paid / NO_HELD implied |

**Invariant:** ENABLE_UNDER_FENCES **SIGNED** ≠ this F4 product ACK. Session LIVE windows restore False. Permanent True needs **this** ACK signed — **now on SIGNED artifact**.

---

## 1. Explicit non-implication (binding)

The following **do NOT count** as this F4 product ACK:

| Prior artifact | Why not this ACK |
|----------------|------------------|
| Gate1 **SIGNED ENABLE_UNDER_FENCES** 「Aprobado」 | Canary/fenced session intent ≠ permanent product |
| Gates 2–6 DESIGN_SEALED / ENABLE_READY | Design/enable-ready ≠ permanent True |
| CP-0075..0079 canary / multi-canary / policy | Measurement under fences; policy default False |
| F4 **DESIGN_SEALED** | Design ≠ operator product signature |
| This draft while **UNSIGNED** | Draft ≠ signature |

**Operator checkbox (required when signing):**  
- [ ] I confirm none of the above substitute for this F4 **product-enable** ACK.  
- [ ] I confirm ENABLE_UNDER_FENCES remains the canary/session ACK and is **not** being re-used here.

*(Checkboxes filled on SIGNED copy via 「Firmalo por mi」.)*

---

## 2. Scope (operator fills when signing)

| Field | Operator fill |
|-------|---------------|
| Product flag intent | `[ ]` module `LIVE_API_ENABLED=True` in ACK’d env · `[ ]` `live_adapter.enabled=true` · `[ ]` both |
| Provider | `[ ]` Gemini free-tier only · `[ ]` other (separate): _______________ |
| Vertex paid | **OUT** unless separate — `[ ]` still OUT |
| Env | `[ ]` named env: _______________ |
| Kill / rollback owner on duty | `[ ]` named: _______________ |
| Streaming | **OUT** of this ACK unless named — `[ ]` OUT |
| NO_HELD (Raft/N>2/GIA/train/SaaS) | **unchanged** — `[ ]` confirmed |

*(Filled on SIGNED copy.)*

---

## 3. Signature block — **ACK F4 PRODUCT ENABLE** (blank — see SIGNED)

| Field | Value |
|-------|-------|
| Intent | **F4_PRODUCT_ENABLE** (permanent module / adapter under fences) |
| Operator | Joan / Yoan V (repo owner) |
| Signature / mark | _see SIGNED artifact — 「Firmalo por mi」_ |
| Date | _see SIGNED_ |
| Tip at sign | _see SIGNED — `c64c0e0`_ |

**Selected intent (historical draft):** `[ ] F4_PRODUCT_ENABLE` · `[x] unsigned / none` → superseded by SIGNED

---

## 4. Prefer leave False (historical at draft time)

Until this ACK is signed, agents **must** leave module `LIVE_API_ENABLED=False` and restore runtime False after every canary/pack (`LIVE_API_PERMANENT_ENABLE_POLICY.md`).  
**Now signed:** see `F4_PRODUCT_ENABLE_ACK_SIGNED.md` + CP-0087 flip.

---

*End F4_PRODUCT_ENABLE_ACK_DRAFT — HISTORICAL UNSIGNED; see F4_PRODUCT_ENABLE_ACK_SIGNED.md.*
