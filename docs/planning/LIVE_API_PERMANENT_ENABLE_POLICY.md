# Permanent LIVE_API enable policy / runbook

**Status:** **POLICY SEALED (docs)** — when module/`live_adapter` LIVE may remain True vs **must** return False  
**Does NOT** flip flags by itself · **does NOT** unlock NO_HELD · **does NOT** claim product-ready 「listo」 alone  
**Date:** 2026-09-28 ~22:40 EDT (America/New_York)  
**Author:** Grok Bot `<grok-bot@local>`  
**Tip at mint base:** `ee0c0c6` (CP-0078 LiveHttpTransport v0)  
**Cycle / companion:** 75 / **CP-0079** multi-canary pack  
**Package:** **0.18.0 HELD** · **NO_HELD unchanged** · D3 NOT ACKed · M1=NO_CONSENSUS_YET

**Upstream:** Gate1 `GATE1_ENABLE_UNDER_FENCES_ACK_SIGNED.md` (「Aprobado」) · `GATE5_LIVE_FLAG_FLIP_RUNBOOK.md` · CP-0075/0077/0078 · `GATE6_METRIC_COMPLETION_DESIGN.md`

---

## 0. What this is / is not

| Is | Is not |
|----|--------|
| Explicit policy for **when** LIVE flags may stay True vs **must** be False | An automatic flip of `LIVE_API_ENABLED` |
| Binding default: **product module constant stays False** | F4 product-enable substitute (F4 still OPEN if 「listo」 beyond fences) |
| Runbook alignment with Gate5 (1)–(7) + multi-canary restore | Permission to leave half-enabled transport after canary/pack |
| Honest wall for operators and agents | “100% live ready” claim |

**Invariant:** ENABLE_UNDER_FENCES authorizes **fenced canary / measurement windows** (runtime LIVE true only inside session). It does **not** authorize leaving the **module** constant `LIVE_API_ENABLED=True` as product default.

---

## 1. Flag layers (do not conflate)

| Layer | Symbol | Default | Who may flip | Persist after pack? |
|-------|--------|---------|--------------|---------------------|
| **Module constant** | `LIVE_API_ENABLED` in packaging modules (peer spike, CP-0075, CP-0078, CP-0079) | **False** | Code change + **this policy §3** + operator F4 if product | **No** — stays False for product |
| **Process runtime** | `runtime_live_api_enabled` / `MESH_LIVE_API_ENABLED` | False | Gate5 session under I5 + may_enable | **Must restore False** after every attempt/pack |
| **Adapter product flag** | `live_adapter.enabled` | false | Separate product enable (F4) | **No** without F4 |
| **CI** | `live_api_in_ci` | false | Never for live network | **Must stay false** |

---

## 2. When LIVE **must** return / remain False

| Condition | Binding |
|-----------|---------|
| Product / package default (0.18 HELD) | Module `LIVE_API_ENABLED=False` |
| After any Gate5 canary or multi-canary attempt | Runtime False · RefuseTransport · I5 `enabled=false` |
| After multi-canary **pack** completes (CP-0079) | Same — prefer leave False even though ENABLE signed |
| I5 kill / anomaly / failed NT / missing gate | Emergency False + RefuseTransport + continuity ABORT |
| CI / pytest | Never live network; mock or Refuse only |
| Quota / auth / TLS failure mid-pack | Abort path → False; document honestly |
| ENABLE_UNDER_FENCES revoked / superseded | All layers False |
| Permanent-enable §3 criteria **not** met | Module stays False |
| Streaming / unpaid Vertex / NO_HELD scopes | Out of scope → False |

**Hard preference (operator + this policy):** After measurement packs, **leave module LIVE False** until §3 permanent criteria are explicitly met — even when ENABLE_UNDER_FENCES is already signed.

---

## 3. When LIVE **may** remain True (permanent / product)

All of the following are **required**. Missing any → **must** stay False.

| # | Criterion | Today (2026-09-28) |
|---|-----------|---------------------|
| P1 | Gate1 ENABLE_UNDER_FENCES **SIGNED** (provider/env/data/kill/rollback named) | **Met** |
| P2 | Gates 2–4 **ENABLE_READY** + Gate5 runbook walked | **Met** (docs + canary) |
| P3 | Authorized impl path (CP-0075 canary + CP-0078 LiveHttpTransport v0) | **Met** (v0 unary; streaming residual) |
| P4 | Multi-canary pack **n≥N_min=5** + edge mix (CP-0077) measured with ledger | **This cycle (CP-0079)** — see evidence |
| P5 | Gate6 live-measurement **seal attempt** green (M-KILL live / M-ABORT / M-LEDGER) — n=1 cannot seal | **Met pack** (CP-0079 n=6 seal-candidate) + **M-KILL-2 budget PASS** + **M-ABORT-3 PASS** (CP-0080); final product seal still needs F4/P7 |
| P6 | **This policy** acknowledged on disk | **This document** |
| P7 | Operator **F4 product-enable ACK** naming permanent module/`live_adapter` True (separate from ENABLE_UNDER_FENCES canary intent) | **SIGNED** — `F4_PRODUCT_ENABLE_ACK_SIGNED.md` 「Firmalo por mi」~23:22 ET; flip CP-0087 |
| P8 | Kill-armed I5 + rollback owner on duty; audit sink up; secrets oob only | Ops ongoing |
| P9 | No CI live; free-tier bounds unless separate paid ACK | Binding |

**P7 SIGNED:** product-path module may be True in ACK’d env (CP-0087). Session flag still cleared after windows; I5 gates network. See residual NOTE for test hygiene.

**Permanent True means:** shipping / operating with module or `live_adapter.enabled` defaulting or staying True across process restarts — **not** a temporary canary session.

---

## 4. Runbook — temporary window vs permanent

### 4.1 Temporary (canary / multi-canary) — authorized today under fences

```
may_enable? → arm I5 → runtime LIVE=True (session)
        → one attempt (or pack attempt)
        → ledger
        → ALWAYS: runtime LIVE=False; I5 enabled=false; RefuseTransport
Module LIVE_API_ENABLED remains False throughout.
```

Re-enable next attempt: new `request_id` / idempotency key; restore refuse between attempts (CP-0077 independence).

### 4.2 Permanent product enable — **not** authorized until §3 complete

```
P1–P9 all met including F4 ACK
        → change control: module / adapter default True only in ACK'd env
        → Gate5 re-walk after any kill (M-KILL-3)
        → continuous I5 watch + ledger completeness
        → revoke → §2 restore False immediately
```

Agents **must not** invent F4 or flip module constants to True in git without operator F4 artifact.

---

## 5. Relation to ENABLE_UNDER_FENCES (already signed)

| ENABLE_UNDER_FENCES covers | Does **not** cover |
|----------------------------|--------------------|
| Fenced Gemini **free** canary / measurement | Permanent module `LIVE_API_ENABLED=True` |
| Runtime LIVE windows under Gate5 + I5 | CI live / Vertex paid / NO_HELD |
| CP-0075 / CP-0078 / CP-0079 under fences | Treating advisory as Mesh SoT / M1 |

Operator signed ENABLE for the fenced path. **This policy** states the default after packs remains **False** until F4 product-enable.

---

## 6. Explicit non-goals

- Push / tags / secrets in git  
- NO_HELD unlocks (GIA, Raft, N>2, train-70B, SaaS)  
- D3 / `MESH_PERF_EXPERIMENTAL`  
- Claiming Gate6 sealed solely because this policy exists  
- Leaving LIVE True after CP-0079 pack “for convenience”

---

## 7. Related

- `GATE5_LIVE_FLAG_FLIP_RUNBOOK.md` § permanent enable  
- `GATE6_METRIC_COMPLETION_DESIGN.md` · `IMPL_CP_0078_LIVE_HTTP_TRANSPORT.md`  
- `IMPL_CP_0079_MULTI_CANARY_PACK.md` · `GATE5_MULTI_CANARY_EVIDENCE.md`  
- `LIVE_READINESS_CHECKLIST.md` · `LIVE_100_OPERATOR_WALL.md` · `GEMINI_FREE_NEXT_STEPS.md`  
- `GATE1_ENABLE_UNDER_FENCES_ACK_SIGNED.md`
- `F4_DESIGN_SEALED.md` · `F4_PRODUCT_ENABLE_ACK_DRAFT.md` · `docs/ops/M_KILL_2_OPS_KILL_REFUSE_BUDGET.md`

---

*End LIVE_API_PERMANENT_ENABLE_POLICY — default False after packs; permanent True needs P1–P9 including F4; NO_HELD unchanged.*
