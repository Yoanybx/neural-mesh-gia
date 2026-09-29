# F4 — Product-enable operator ACK — **SIGNED**

**Status:** **SIGNED — F4_PRODUCT_ENABLE**  
**Effect:** Authorizes **product permanent** enable under P1–P9 + F4 amendment: module `LIVE_API_ENABLED=True` **and** `live_adapter.enabled=true` in ACK’d local / product env (Gemini free-tier only).  
**It does NOT alone:** unlock NO_HELD · authorize Vertex paid · authorize streaming · mint keys into git · push/tag · start D3 · claim advisory = Mesh SoT / M1.  
**Prior ENABLE (session/canary — not this ACK):** `docs/planning/GATE1_ENABLE_UNDER_FENCES_ACK_SIGNED.md` — 「Aprobado」  
**Unsigned draft (historical):** `docs/planning/F4_PRODUCT_ENABLE_ACK_DRAFT.md`

**Date drafted:** 2026-09-28 ~22:42 EDT (America/New_York)  
**Date signed:** 2026-09-28 ~23:22 EDT (America/New_York)  
**Author (docs):** Grok Bot `<grok-bot@local>` — recorded operator signature; did not invent claims beyond operator mark  
**Operator ACK:** Joan / Yoan V (repo owner) — chat **「Firmalo por mi」** 2026-09-28 ~23:22 ET (sign F4 product-enable ACK) · follow-up **「Ponlo live y seguimos」** (flip product permanent LIVE under fences after sign)  
**Tip at sign base:** `c64c0e0` (CP-0086 Gate6 live-measurement SEALED; R5 was OPEN)  
**Package posture:** **0.18.0 HELD** · Gate1 **SIGNED ENABLE_UNDER_FENCES** · F4 design **SEALED** · product ACK **SIGNED** · module product-path **`LIVE_API_ENABLED=True`** (post-flip CP-0087) · RefuseTransport when I5 not armed · **streaming OUT** · **NO_HELD** stays NO_HELD

**Amendment:** `F4_PRODUCT_ENABLE_SAFETY_AMENDMENT.md` · seal `F4_DESIGN_SEALED.md`  
**Policy:** `LIVE_API_PERMANENT_ENABLE_POLICY.md` (P7 **SIGNED**)  
**Checklist / wall:** `LIVE_READINESS_CHECKLIST.md` · `LIVE_100_OPERATOR_WALL.md`

---

## 0. What this is / is not

| Is | Is not |
|----|--------|
| **Signed** ACK for **product permanent** enable (module / `live_adapter` True in ACK’d env) | A re-use of ENABLE_UNDER_FENCES 「Aprobado」 alone |
| Separate cycle from ENABLE_UNDER_FENCES (D4 F4) | Vertex paid / streaming / CI live / NO_HELD |
| P7 met → permanent True authorized under P1–P9 | Permission to skip I5 kill-arm / RefuseTransport when not armed |
| Compatible with secrets oob + Gemini free-tier fences | Claim that advisory output = Mesh SoT / M1 consensus |

**Invariant:** ENABLE_UNDER_FENCES **SIGNED** ≠ this F4 product ACK. Session LIVE windows remain I5-gated. Permanent True needs **this** ACK signed (now recorded).

---

## 1. Explicit non-implication (binding)

The following **do NOT count** as substitutes for this F4 product ACK:

| Prior artifact | Why not this ACK |
|----------------|------------------|
| Gate1 **SIGNED ENABLE_UNDER_FENCES** 「Aprobado」 | Canary/fenced session intent ≠ permanent product |
| Gates 2–6 DESIGN_SEALED / ENABLE_READY | Design/enable-ready ≠ permanent True |
| CP-0075..0086 canary / multi-canary / Gate6 / R0–R4 | Measurement under fences; not F4 product signature |
| F4 **DESIGN_SEALED** | Design ≠ operator product signature |
| Unsigned draft | Draft ≠ signature |

**Operator checkbox (recorded on signature via 「Firmalo por mi」):**  
- [x] I confirm none of the above substitute for this F4 **product-enable** ACK.  
- [x] I confirm ENABLE_UNDER_FENCES remains the canary/session ACK and is **not** being re-used here.

---

## 2. Scope (operator filled on signature)

| Field | Operator fill |
|-------|---------------|
| Product flag intent | `[x]` **both** — module `LIVE_API_ENABLED=True` in ACK’d env **and** `live_adapter.enabled=true` authorized |
| Provider | `[x]` Gemini free-tier only |
| Vertex paid | **OUT** — `[x]` still OUT |
| Env | `[x]` local box / ACK’d product env |
| Kill / rollback owner on duty | `[x]` Joan / Yoan V (repo owner) |
| Streaming | **OUT** of this ACK — `[x]` OUT (CP-0085 DEFER) |
| NO_HELD (Raft/N>2/GIA/train/SaaS) | **unchanged** — `[x]` confirmed |

---

## 3. Signature block — **ACK F4 PRODUCT ENABLE**

| Field | Value |
|-------|-------|
| Intent | **F4_PRODUCT_ENABLE** (permanent module / adapter under fences) |
| Operator | Joan / Yoan V (repo owner) |
| Signature / mark | **「Firmalo por mi」** — operator chat 2026-09-28 ~23:22 ET (sign F4 product-enable ACK) |
| Follow-up mark | **「Ponlo live y seguimos」** — flip product permanent LIVE under fences after sign |
| Date (America/New_York) | 2026-09-28 ~23:22 EDT |
| Tip at sign | `c64c0e0` |
| Scope string complete | `[x]` Yes — §2 filled |
| Non-implication confirmed | `[x]` §1 checkboxes |
| Streaming OUT | `[x]` confirmed |
| NO_HELD unchanged | `[x]` confirmed |

**Status:** **SIGNED — F4_PRODUCT_ENABLE.**  
**Signature mark recorded.** P7 met. Product permanent True authorized for Gemini free-tier in ACK’d local env under I5 / RefuseTransport when not armed.

---

## 4. Post-signature posture (honest)

| Layer | Posture after sign + CP-0087 flip |
|-------|-----------------------------------|
| Module `LIVE_API_ENABLED` (product path) | **True** (authorized + flipped) |
| `live_adapter.enabled` | **Authorized true** in ACK’d local env (docs + enablement lift) |
| I5 / RefuseTransport | Still required for network; kill-armed before live windows |
| Streaming | **OUT** (CP-0085 DEFER) |
| Vertex paid / CI live / NO_HELD | **OUT** / unchanged |
| Secrets | oob only (`mesh://secrets/...`; no keys in git) |

---

## 5. Explicit non-goals (this signature)

- Inventing Vertex / paid / streaming / NO_HELD unlocks  
- Committing secrets / keys  
- Push / tags  
- Starting D3 / `MESH_PERF_EXPERIMENTAL`  
- Claiming Gemini advisory = Mesh SoT / M1  
- Waiving I5 kill-arm for live network windows  

---

## 6. Related

- `docs/planning/F4_PRODUCT_ENABLE_ACK_DRAFT.md` (historical UNSIGNED)  
- `docs/planning/GATE1_ENABLE_UNDER_FENCES_ACK_SIGNED.md`  
- `docs/planning/F4_DESIGN_SEALED.md` · `F4_PRODUCT_ENABLE_SAFETY_AMENDMENT.md`  
- `docs/planning/LIVE_API_PERMANENT_ENABLE_POLICY.md` · `IMPL_CP_0087_F4_PRODUCT_ENABLE_R5.md`  
- `docs/planning/LIVE_100_OPERATOR_WALL.md` · `LIVE_READINESS_CHECKLIST.md`

---

*End F4_PRODUCT_ENABLE_ACK_SIGNED — SIGNED F4_PRODUCT_ENABLE; 「Firmalo por mi」; tip c64c0e0; streaming OUT; NO_HELD unchanged.*
