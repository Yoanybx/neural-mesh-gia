# LiveHttpTransport residual — FULL design (DESIGN ONLY)

**Status:** **DESIGN_ONLY** (historical seal) — formalized residual codec; **impl now authorized by CP-0078** (packaging v0; still does **NOT** permanently enable live)  
**Impl:** `docs/planning/IMPL_CP_0078_LIVE_HTTP_TRANSPORT.md` · `src/neural_mesh/packaging/l_judge_live_http_transport.py`  
**Cycle / Checkpoint:** 72 / **CP-0076** (DESIGN_ONLY)  
**Date:** 2026-09-28 ~19:54 EDT (America/New_York)  
**Author:** Grok Bot `<grok-bot@local>`  
**Tip at mint base:** `ca85688` (CP-0075 Gate5 canary)  
**Authority:** Dual council ACK Gate5 canary hygiene — DeepSeek Option 1 ranked + ChatGPT RANK 1 same Option 1  
**Package:** **0.18.0 HELD** · **`LIVE_API_ENABLED=False`** · RefuseTransport default ON · **NO_HELD unchanged** · D3 NOT ACKed · M1=NO_CONSENSUS_YET

**Schema stub:** `docs/schema/judge/live_http_transport_v0.md`  
**CP seal:** `docs/planning/DESIGN_CP_0076_LIVE_HTTP_TRANSPORT_RESIDUAL.md`  
**Council note:** `council/NOTE_DESIGN_CP_0076_LIVE_HTTP_TRANSPORT.md`  
**Compose:** CP-0058 RefuseTransport safety · CP-0068 continuity · CP-0069 oversight/I5 · CP-0075 canary = **separate minimum** (not this codec)

---

## 0. What this is / is not

| Is | Is not |
|----|--------|
| Load-bearing **design** of the residual full live HTTP transport codec named “NOT shipped” by CP-0075 | Permission to implement `LiveHttpTransport` in `src/` |
| Spec covering retries, backoff, idempotency, streaming vs unary, error taxonomy, timeouts, ABORT propagation, audit linkage | A live enable, flag flip, or canary re-run |
| Compose contract with continuity (CP-0068), oversight/I5 (CP-0069), RefuseTransport (CP-0058) | A claim that CP-0075 already shipped this adapter |
| Exit: design doc + schema stub + negative-test **descriptors** | Green live CI; keys; push/tags; 100% product live |

**Invariant fences (hard):**

- Does **NOT** authorize codec implementation  
- Does **NOT** enable live · module **`LIVE_API_ENABLED` stays False**  
- CP-0075 Gemini free canary path remains the **separate minimum** (already executed); this design does not subsume or re-authorize it  
- No secrets in repo · no push/tags · **NO_HELD unchanged**

---

## 1. Intent + ownership

CP-0075 cleared NT-10 for **one** fenced free-tier canary by reusing `GeminiFreeDryRunTransport` / canary transport behind a runtime LIVE window + kill-armed I5. It explicitly left:

> `LiveHttpTransport` generic codec in `src/neural_mesh/` — **NOT shipped** (design+spike)

This document is that residual **design**. Ownership:

```
┌──────────────────────────────────────────────────────────────────┐
│ LiveHttpTransport residual (this design — NOT implemented)       │
│  • Unary / optional streaming HTTP codec (TLS-only)              │
│  • Retry + backoff policy (bounded; never invents ACCEPT)        │
│  • Idempotency keys (compose Continuity InFlightTracker)         │
│  • Error taxonomy → Mesh ABORT codes                             │
│  • Timeout bounds (soft/hard) + ABORT propagation                │
│  • Audit linkage (JudgeReceipt + EvidenceEntry + OBS)            │
│  • Default binding remains RefuseTransport until future impl CP  │
└───────────────┬──────────────────┬───────────────────────────────┘
                │                  │
                ▼                  ▼
     Continuity plane         Oversight / I5
     (CP-0068)                (CP-0069)
                │                  │
                └────────┬─────────┘
                         ▼
              RefuseTransport / safety gate
              (CP-0058) — default ON
```

| Concern | Owner | Must NOT |
|---------|-------|----------|
| Network I/O codec | Future impl CP (not this) | Ship under this design CP |
| Default when live disabled | RefuseTransport (CP-0058) | Silent network on `enabled=false` |
| In-flight / orphan / resume | Continuity (CP-0068) | Engine chat as SoT |
| Kill / pause / deadman | Oversight I5 (CP-0069) | Keep calling after kill |
| Canary free path | CP-0075 (separate) | Pretend canary = full codec |
| Goals / evidence SoT | Mesh | Advisory as SoT / M1 |

---

## 2. Compose honestly (cite artifacts)

### 2.1 CP-0058 — RefuseTransport safety case

**Cite:** `docs/design/L_JUDGE_LIVE_ADAPTER_SAFETY_CASE.md` · `docs/schema/judge/live_adapter_safety_v0.md` · snapshot `snapshots/CP-0058/`

| Binding held | Residual implication |
|--------------|----------------------|
| Default `RefuseTransport` → `ENGINE_DISABLED` | Full codec, if ever shipped, stays **behind** `enabled=false` default |
| Floor limits: `max_retries=1`, `timeout_s=30`, rate floors | Residual design **must not loosen** floors without new evidence |
| ABORT codes: `ENGINE_*`, `PLAINTEXT_FORBIDDEN`, `NO_AUDIT`, `HUMAN_ABORT`, … | Residual taxonomy **extends**, does not replace |
| `src_live_codec_shipped` must stay **false** until authorized **impl** CP | This DESIGN_ONLY CP **does not** flip that flag |
| no-audit ⇒ no-action | Every residual path requires audit sink |

### 2.2 CP-0068 — Orchestrator continuity

**Cite:** `docs/design/ORCHESTRATOR_CONTINUITY_DESIGN.md` · snapshot `snapshots/CP-0068/`

| Continuity concern | Residual compose |
|--------------------|------------------|
| Invocation **idempotency** (`idempotency_key`) | Live HTTP calls carry Mesh-owned key; duplicate → same receipt / conflict → `CONT_IDEMPOTENCY_CONFLICT`; **no double-invoke** |
| Soft / hard timeout | Transport timeouts map into continuity timeout ledger kinds (`timeout` / ABORT) |
| ABORT propagation | Transport ABORT closes in-flight; ledger `invoke_end` / `abort`; no silent ACTIVE |
| Orphan on LEFT/REJOIN | In-flight live call orphaned → continuity orphan policy; transport must honor cancel/ABORT |
| Resume after restart | **Must not** reconstruct live call from LLM context; resume from Mesh registry+ledger only |

### 2.3 CP-0069 — Oversight / I5

**Cite:** `docs/design/ORCHESTRATOR_OVERSIGHT_HOOKS_DESIGN.md` · snapshot `snapshots/CP-0069/`

| Oversight concern | Residual compose |
|-------------------|------------------|
| `kill` / `HUMAN_ABORT` | Immediate refuse further live submits; bind RefuseTransport; open calls ABORT |
| `pause` | No new live routes; in-flight may complete under policy or ABORT on hard timeout |
| Dead-man TTL | A4 window expiry → auto-DRAIN; transport must not open new calls |
| A3/A4 human gate | Live side-effecting path remains oversight-gated; this design does not bypass |

### 2.4 CP-0075 — canary remains separate minimum

**Cite:** `docs/planning/IMPL_CP_0075_GEMINI_FREE_CANARY.md`

CP-0075 is **not** superseded. Free-tier canary transport ≠ generic `LiveHttpTransport`. Future impl of this residual would be a **new** authorized impl CP; until then `src_live_codec_shipped=false`.

---

## 3. Codec surface (design contract)

### 3.1 Interface (design)

```
LiveHttpTransport (DESIGN — not shipped)
  call(request, *, idempotency_key, mode=unary|stream_unary_fallback) -> TransportResult
  health() -> TransportHealth          # fail-closed if down
  cancel(idempotency_key | call_id)    # ABORT propagation hook
```

| Mode | Meaning | Default for residual |
|------|---------|----------------------|
| **unary** | Single request/response body within `timeout_s` | **Required** first |
| **streaming** | Chunked/SSE-style; Mesh reassembles to one `JudgeResponse` | **Optional**; if unsupported → `ENGINE_HTTP` / policy ABORT — never invent ACCEPT |
| **stream_unary_fallback** | Prefer stream; on provider non-support fall back to unary once | Design-allowed; counts as **one** logical attempt family under same idempotency key |

**Streaming rules (design):**

1. Streaming does not relax schema parse gates (CP-0052 / CP-0057).  
2. Partial stream + cancel/kill → ABORT; no half-ACCEPT.  
3. Byte cap `max_raw_bytes` applies to reassembled payload.  
4. CI / pytest remain Mock or Refuse only — no live stream in CI (`live_api_in_ci=false`).

### 3.2 Retries + backoff

| Parameter | Floor / rule | Notes |
|-----------|--------------|-------|
| `max_retries` | **1** (CP-0058 floor) | Then ABORT `ENGINE_HTTP` / mapped code |
| Retryable | Transient network, HTTP 5xx, selected 429 **only if** provider retry-after honored within timeout budget | Never retry 401/403 with alternate invented key |
| Non-retryable | 401/403, TLS/plaintext violations, schema invalid, `NO_AUDIT`, `HUMAN_ABORT`, fence | Immediate ABORT |
| Backoff | Exponential with full jitter; **bounded** by remaining `timeout_s` | Backoff **must not** invent ACCEPT or extend past hard timeout |
| Rate limit | Mesh counters (`max_calls_per_minute/hour`) | Trip → `ENGINE_RATE_LIMIT`; no silent queue past hard timeout |

### 3.3 Idempotency

| Rule | Detail |
|------|--------|
| Key owner | Mesh Continuity `InFlightTracker` (CP-0068) |
| Same key + same payload digest | Return prior receipt / in-flight handle — **no double-invoke** |
| Same key + different payload | ABORT `CONT_IDEMPOTENCY_CONFLICT` |
| Missing key on live path | ABORT / fence (align T-cont-c) |
| Provider-level idempotency header | Optional passthrough of Mesh key; Mesh ledger remains SoT |

### 3.4 Timeouts

| Bound | Design default | On fire |
|-------|----------------|---------|
| Soft timeout | ≤ `timeout_s` (floor 30s unless tightened) | Mark soft; may allow in-flight drain under pause policy |
| Hard timeout | = `timeout_s` for unary; stream hard ≥ soft, still capped | ABORT `ENGINE_TIMEOUT`; continuity `timeout` ledger |
| Connect / TLS handshake | Strict subset of hard budget | Fail → `ENGINE_TLS` / `ENGINE_HTTP` |
| Oversight kill | Immediate | `HUMAN_ABORT` / RefuseTransport; cancel in-flight |

### 3.5 Error taxonomy (extends CP-0057 §6 / CP-0058)

| Condition | Mesh code | Retry? | Continuity / oversight |
|-----------|-----------|--------|------------------------|
| Live disabled / RefuseTransport | `ENGINE_DISABLED` | No | Expected default |
| Secret_handle unresolved | `ENGINE_AUTH` | No | Fail closed |
| TLS / plaintext | `ENGINE_TLS` / `PLAINTEXT_FORBIDDEN` | No | Never fallback |
| HTTP 401/403 | `ENGINE_AUTH` | No | No key invent |
| HTTP 5xx / transient network | `ENGINE_HTTP` | ≤ max_retries | Then ABORT |
| HTTP 429 | `ENGINE_RATE_LIMIT` | Conditional | Honor budget |
| Timeout | `ENGINE_TIMEOUT` | No (after budget) | Ledger `timeout` |
| Truncation / oversize | `SCHEMA_INVALID` / policy | No | forbid_silent_accept |
| Parse / unknown verdict | `SCHEMA_INVALID` | No | Never invent ACCEPT |
| No audit sink | `NO_AUDIT` | No | no-audit=no-action |
| dual_primary ≠ 0 / fence | `FENCE` | No | Unchanged |
| I5 kill / human stop | `HUMAN_ABORT` | No | RefuseTransport |
| Idempotency conflict | `CONT_IDEMPOTENCY_CONFLICT` | No | Continuity |
| Stream unsupported / broken mid-stream | `ENGINE_HTTP` / policy | Per mode rules | No half-ACCEPT |

### 3.6 ABORT propagation

```
I5 kill / pause-hard / continuity orphan / hard timeout / taxonomy ABORT
        │
        ▼
cancel(call) → stop network wait → map code → close in-flight
        │
        ▼
JudgeReceipt + EvidenceEntry (abort/invoke_end) + OBS
        │
        ▼
Binding → RefuseTransport for subsequent submits (kill path)
```

Rules:

1. ABORT always beats advisory ACCEPT (Mesh ABORT > judge ACCEPT).  
2. Propagation is Mesh-owned; provider disconnect alone is insufficient without ledger.  
3. After kill: no new live calls until explicit re-approve path (CP-0069).

### 3.7 Audit linkage

| Artifact | When |
|----------|------|
| `JudgeReceipt` (hash-chained) | Every attempt family end-state (success or ABORT) when sink up |
| `EvidenceEntry` kinds | `invoke_start` / `invoke_end` / `timeout` / `abort` / `routing_receipt` / `oversight` as applicable |
| OBS | Latency, retry count, rate_limited flag, mode (unary/stream) — **no secrets** |
| Digests | Prompt / response digests only; raw keys forbidden |

---

## 4. Schema stub (summary)

Full stub: `docs/schema/judge/live_http_transport_v0.md`  
Schema id: **`mesh.judge.live_http_transport/v0`** (STUB)

Key fields (design): `enabled` (must false) · `mode` · `max_retries` · `backoff` · `timeout_s` · `idempotency_required` · `streaming_allowed` · `tls_required` · `secret_handle` · `audit_required` · `compose_continuity` · `compose_oversight` · `must_stay_false`.

---

## 5. Negative-test descriptors (design only — not executable suite claim)

Descriptors only; **do not** imply a shipped codec or live pytest network.

| ID | Scenario | Expected |
|----|----------|----------|
| **T-lht-a** | `enabled=false` / RefuseTransport default | Every `call` → `ENGINE_DISABLED`; **zero** network |
| **T-lht-b** | Missing / invalid `secret_handle` while enabled aspirational | `ENGINE_AUTH`; fail closed |
| **T-lht-c** | Plaintext / non-TLS endpoint | `PLAINTEXT_FORBIDDEN` / `ENGINE_TLS`; no fallback |
| **T-lht-d** | Duplicate `idempotency_key` same payload | No double-invoke; same receipt family |
| **T-lht-e** | Duplicate key different payload | `CONT_IDEMPOTENCY_CONFLICT` |
| **T-lht-f** | Exhaust `max_retries` on 5xx | Final `ENGINE_HTTP`; no ACCEPT invent |
| **T-lht-g** | Hard timeout | `ENGINE_TIMEOUT`; continuity timeout ledger |
| **T-lht-h** | I5 kill mid-call | `HUMAN_ABORT`; subsequent RefuseTransport |
| **T-lht-i** | Missing audit sink | `NO_AUDIT`; no-action |
| **T-lht-j** | Stream mid-break / oversize | ABORT; no half-ACCEPT |
| **T-lht-k** | `live_api_in_ci=true` aspirational in CI | Must stay refused / false |
| **T-lht-l** | Claim `src_live_codec_shipped=true` under this CP | **Forbidden** — DESIGN_ONLY |

Aligns with continuity T-cont-* and oversight T-ovs-* families; live measurement sample policy remains Gate6 (n=1 ≠ SLO).

---

## 6. Exit criteria (this design CP)

| Exit item | Status |
|-----------|--------|
| Design doc covering retries, backoff, idempotency, streaming vs unary, taxonomy, timeouts, ABORT, audit | **This doc** |
| Schema stub | `docs/schema/judge/live_http_transport_v0.md` |
| Negative-test descriptors | §5 above |
| Design CP minted | **CP-0076** DESIGN_ONLY |
| Dual council Option 1 noted | DeepSeek + ChatGPT ACK seal |

**Not exit / not authorized:** codec impl · LIVE flip · new network canary · keys · push/tags · Gate6 premature seal · NO_HELD unlocks.

---

## 7. Explicit non-goals / non-claims

- `LIVE_API_ENABLED=true` / permanent live product enable  
- Implementing `LiveHttpTransport` in `src/neural_mesh/` under this CP  
- Treating CP-0075 canary HTTP 200 / ~6621 ms as SLO or full-adapter proof  
- advisory = SoT · n=1 = SLO · design seals = live seals  
- D3 / `MESH_PERF_EXPERIMENTAL` · GIA · Raft/N>2 · train-70B · SaaS/economy  
- Push, tags, secrets in git  

**NO_HELD:** Raft,N>2,multi-primary,ML,R2,R3,plaintext,Vault-ACME-req,GIA,SLO_chase,tag_schema,EVERY_fsync (**unchanged**)

---

## 8. Related

- Dual ACK: `council/REPLY_DEEPSEEK_GATE5_CANARY_HYGIENE_ACK.md` · `council/REPLY_CHATGPT_GATE5_CANARY_HYGIENE_ACK.md` · `council/NOTE_DEEPSEEK_ACK_GATE5_CANARY.md`  
- `IMPL_CP_0075_GEMINI_FREE_CANARY.md` · `GATE5_CANARY_EVIDENCE.md` · `GATE6_CANARY_MEASUREMENT.md`  
- `L_JUDGE_LIVE_ADAPTER_DESIGN.md` §3–§8 · `L_JUDGE_LIVE_ADAPTER_SAFETY_CASE.md`  
- `ORCHESTRATOR_CONTINUITY_DESIGN.md` · `ORCHESTRATOR_OVERSIGHT_HOOKS_DESIGN.md`  
- `GEMINI_FREE_NEXT_STEPS.md` · `LIVE_READINESS_CHECKLIST.md` · `LIVE_100_OPERATOR_WALL.md`

---

*End LIVE_HTTP_TRANSPORT_RESIDUAL_DESIGN — DESIGN_ONLY seal retained; CP-0078 implements packaging v0 under fences; does NOT permanently enable live; CP-0075 canary path remains separate minimum.*
