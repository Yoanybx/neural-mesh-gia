# F4 — Product-enable operator ACK — **UNSIGNED DRAFT**

**Status:** **UNSIGNED DRAFT** — product permanent LIVE / module default True  
**Effect (when signed by operator):** Authorizes **product permanent** enable under P1–P9 + F4 amendment (separate from ENABLE_UNDER_FENCES canary intent).  
**This draft alone does not authorize flips**; bots must **not** invent signature.  
**Date drafted:** 2026-09-28 ~22:42 EDT (America/New_York)  
**Author (draft only):** Grok Bot `<grok-bot@local>`  
**Tip at draft:** atop `c2ba1e2` / CP-0080 F4 design seal  
**Package posture:** **0.18.0 HELD** · **LIVE_API_ENABLED=False** · Gate1 **SIGNED ENABLE_UNDER_FENCES** · F4 design **SEALED** · **NO_HELD** stays NO_HELD

**Prior ENABLE (session/canary — not this ACK):** `GATE1_ENABLE_UNDER_FENCES_ACK_SIGNED.md`  
**Amendment:** `F4_PRODUCT_ENABLE_SAFETY_AMENDMENT.md` · seal `F4_DESIGN_SEALED.md`  
**Policy:** `LIVE_API_PERMANENT_ENABLE_POLICY.md`

---

## 0. What this is / is not

| Is | Is not |
|----|--------|
| **Unsigned** draft for **product permanent** enable (module / `live_adapter` default True in ACK’d env) | A signed ACK today |
| Separate cycle from ENABLE_UNDER_FENCES (D4 F4) | A re-use of 「Aprobado」 canary intent |
| Requires P1–P9 all met including this signature (P7) | Permission to flip before operator signs |
| Compatible with leaving False after packs | CI live / Vertex paid / NO_HELD implied |

**Invariant:** ENABLE_UNDER_FENCES **SIGNED** ≠ this F4 product ACK. Session LIVE windows restore False. Permanent True needs **this** ACK signed.

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

---

## 3. Signature block — **ACK F4 PRODUCT ENABLE** (blank until operator)

| Field | Value |
|-------|-------|
| Intent | **F4_PRODUCT_ENABLE** (permanent module / adapter under fences) |
| Operator | Joan / Yoan V (repo owner) |
| Signature / mark | _unsigned — await operator user-written mark_ |
| Date | _pending_ |
| Tip at sign | _pending_ |

**Selected intent (operator):** `[ ] F4_PRODUCT_ENABLE` · `[x] unsigned / none`

---

## 4. Prefer leave False

Until this ACK is signed, agents **must** leave module `LIVE_API_ENABLED=False` and restore runtime False after every canary/pack (`LIVE_API_PERMANENT_ENABLE_POLICY.md`).

---

*End F4_PRODUCT_ENABLE_ACK_DRAFT — UNSIGNED; do not invent signature; ENABLE ≠ product permanent.*
