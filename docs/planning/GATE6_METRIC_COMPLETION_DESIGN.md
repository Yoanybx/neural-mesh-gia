# Gate 6 — Metric completion design (DESIGN_ONLY)

**Status:** **DESIGN_ONLY** — remaining Gate6 acceptance for **M-KILL live**, **M-ABORT**, **M-LEDGER** + **sample-size policy (n≥N)** so **n=1 cannot seal**  
**Does NOT** measure live · **does NOT** re-run canary · **does NOT** flip `LIVE_API_ENABLED` · **does NOT** authorize codec impl · **does NOT** claim product-ready live  
**Cycle / Checkpoint:** 73 / **CP-0077** (DESIGN_ONLY)  
**Date:** 2026-09-28 ~22:29 EDT (America/New_York)  
**Author:** Grok Bot `<grok-bot@local>`  
**Tip at mint base:** `e739c82` (CP-0076 DESIGN_ONLY LiveHttpTransport residual)  
**Authority:** DeepSeek ACK CP-0076 design hygiene PASS; ranked NEXT #1 `GATE6_METRIC_COMPLETION_DESIGN` (this artifact) · #2 STOP — `council/REPLY_DEEPSEEK_CP0076_DESIGN_HYGIENE_ACK.md`  
**Package:** **0.18.0 HELD** · **`LIVE_API_ENABLED=False`** · RefuseTransport default ON · **NO_HELD unchanged** · D3 NOT ACKed · M1=NO_CONSENSUS_YET

**Upstream metrics seal:** `GATE6_LIVE_ACCEPTANCE_METRICS.md` (DESIGN_SEALED) · `GATE6_DESIGN_SEALED.md`  
**Sample today:** `GATE6_CANARY_MEASUREMENT.md` — **n=1** free canary (CP-0075); M-KILL live / M-ABORT / M-LEDGER **not** live-sealed  
**CP seal:** `docs/planning/DESIGN_CP_0077_GATE6_METRIC_COMPLETION.md`  
**Council note:** `council/NOTE_DESIGN_CP_0077_GATE6_METRIC_COMPLETION.md`

---

## 0. What this is / is not

| Is | Is not |
|----|--------|
| Design completion of Gate6 acceptance for families still **design/unit-only** after n=1 canary | A live measurement claim or Gate6 live-seal |
| Explicit **n≥N** sample policy + variance/edge requirements so **n=1 cannot seal** | Permission to re-canary, flip flags, or ship codec |
| Attachment path for future multi-canary under kill-armed I5 (still operator-gated) | Permanent `LIVE_API_ENABLED=true` product enable |
| Honest wall for what 「listo」 still needs | “100% live ready” |

**Invariant:** Metrics **DESIGN_SEALED** (Gate6) ≠ live measurement complete ≠ product-ready live. CP-0075 n=1 = **sample evidence only**. This CP **codifies** why n=1 cannot seal and what remaining families require.

---

## 1. Gap map after CP-0075 / GATE6_CANARY_MEASUREMENT (n=1)

| Metric family | Today (honest) | Gap this design closes |
|---------------|----------------|------------------------|
| **M-REFUSE-*** | PASS (post + unit) | Held; not reopened |
| **M-SEC-*** | PASS (greppable) | Held |
| **M-ADV-*** | PASS (advisory; mesh_accept=false) | Held |
| **M-KILL-1** | **DESIGN+UNIT** — unit kill→Refuse; **not** mid-flight live kill | Need **live** kill observation under ACK’d canary window |
| **M-KILL-2** | Design only — ops latency budget **not** filled | Need budget + observed kill→refuse latency distribution |
| **M-KILL-3** | Design only — no live post-kill resume drill | Need explicit no-auto-resume evidence |
| **M-ABORT-1..3** | Design intent; abort path **unused** on happy-path n=1 | Need forced ABORT>ACCEPT + anomaly→Refuse + conflict/missing judge |
| **M-LEDGER-1..3** | Partial — canary ledger present; kill/`abort` kinds **not** exercised live | Need completeness gate across n≥N including kill/abort kinds |
| Sample size | **n=1** | **n=1 ≠ seal**; policy below |

DeepSeek unanswered (hygiene ACK / prior canary ACK): M-ABORT / M-LEDGER Gate6 status — addressed here as **design completion**, not as measured seal.

---

## 2. Sample-size policy (n≥N) — n=1 cannot seal

### 2.1 Hard rule

| Rule | Binding |
|------|---------|
| **n=1 cannot seal** Gate6 live-measurement exit | Explicit — CP-0075 / `GATE6_CANARY_MEASUREMENT.md` remain **sample ≠ SLO ≠ seal** |
| **Seal attempt** requires **n ≥ N_min** independent canary **attempts** under kill-armed I5 + Gate5 (1)–(7) walk | Defined below |
| Pytest / unit / mock alone | **Necessary, insufficient** (unchanged from Gate6 seal) |
| Happy-path-only set | **Cannot seal** even if n ≥ N_min — edge set §3 required |

### 2.2 N_min (design defaults)

| Symbol | Value (design) | Meaning |
|--------|----------------|---------|
| **N_min** | **5** | Minimum independent canary **attempts** before any Gate6 **live-measurement seal attempt** |
| **N_edge** | **≥3** of the N_min must be **edge** scenarios (§3), not all happy-path |
| **N_kill_live** | **≥1** | At least one attempt exercises **mid-window I5 kill** (M-KILL live) |
| **N_abort** | **≥1** | At least one attempt forces Mesh **ABORT > judge ACCEPT** (or advisory ACCEPT ignored) |
| **N_ledger_kill** | **≥1** | At least one attempt records `oversight` + `abort` ledger kinds on kill/deny |
| Independence | Separate `request_id` / idempotency key; restore RefuseTransport + `LIVE_API` runtime false between attempts | No batch-as-one |
| Provider bound | Gemini **free-tier** under existing ENABLE_UNDER_FENCES unless operator opens new ACK | Vertex paid OUT |

**Rationale:** DeepSeek honesty — single ~6621 ms RTT has **no distribution, no failure mode, no tail**. N_min=5 + edge mix forces variance visibility without inventing a production SLO number in this design CP.

### 2.3 What n≥N does **not** authorize

- Permanent module `LIVE_API_ENABLED=True`
- Codec impl (still needs **future authorized impl CP** after CP-0076 design)
- Treating advisory digests as Mesh SoT / M1
- Multi-provider / paid / NO_HELD unlocks
- Skipping Gate5 re-walk after kill (M-KILL-3)

---

## 3. Variance + edge requirements

### 3.1 Variance (reporting — not an invented SLO)

On any future multi-canary measurement pack, record **per attempt** and **aggregate**:

| Field | Required |
|-------|----------|
| `latency_ms` per attempt | Yes |
| Aggregate **p50 / p95** (or min/median/max if n small) | Yes — **descriptive only** until ops sets budget |
| HTTP / abort / kill outcome histogram | Yes |
| `i5_killed` count | Yes |
| Final binding always RefuseTransport + module LIVE false | Yes |

**Fail seal attempt if:** only a single latency point is presented as “live ready,” or p95/tail omitted when claiming reliability.

### 3.2 Edge set (minimum coverage inside n≥N)

| Edge ID | Scenario | Primary metrics |
|---------|----------|-----------------|
| **E-KILL** | I5 kill **mid-window** (after runtime LIVE true, before/during call) | M-KILL-1, M-KILL-2, M-LEDGER-2 |
| **E-ABORT-ACCEPT** | Mesh ABORT while peer/advisory would ACCEPT | M-ABORT-1 |
| **E-ANOMALY** | Missing gate / failed NT / half-enable attempt | M-ABORT-2 → full RefuseTransport |
| **E-CONFLICT** | Conflicting or missing judges | M-ABORT-3 fail-closed |
| **E-AUTH** | Missing/invalid secret_handle (no raw key invent) | M-REFUSE / ENGINE_AUTH; M-SEC held |
| **E-TIMEOUT** | Hard timeout / cancel path | M-KILL compose / taxonomy; ledger `timeout`/`abort` |
| **E-RESUME** | Post-kill re-enable attempt without A3/A4 + Gate5 re-walk | M-KILL-3 **must fail** (no auto-resume) |

Happy-path HTTP 200 / `MESH_CANARY_OK` (CP-0075 style) may count toward N_min but **never alone**.

---

## 4. Remaining acceptance — M-KILL live

| ID | Design acceptance (when measured later) | Evidence required | Today |
|----|------------------------------------------|-------------------|-------|
| **M-KILL-1-LIVE** | Mid-window I5 kill → RefuseTransport + continuity ABORT + runtime/module enabled false; further routes refused | Ledger `oversight`+`abort`; post-kill call → ENGINE_DISABLED; unit alone **insufficient** for live seal | UNIT only |
| **M-KILL-2-BUDGET** | Ops-defined kill→refuse ceiling recorded **before** measurement; observed latency ≤ budget **or** miss recorded as FAIL with ledger | Budget artifact + per-kill latency | Budget **OPEN** (ops) |
| **M-KILL-3-RESUME** | After kill, re-enable requires A3/A4 + Gate5 (1)–(7) re-walk; auto-resume = FAIL | Negative attempt evidence | Design only |

**Compose:** CP-0069 I5 · CP-0058 RefuseTransport · Gate5 NT-6 · CP-0076 residual cancel/ABORT (design; codec still not shipped).

---

## 5. Remaining acceptance — M-ABORT

| ID | Design acceptance | Evidence required | Today |
|----|-------------------|-------------------|-------|
| **M-ABORT-1** | Mesh ABORT beats judge/advisory ACCEPT; no silent ACCEPT | Controlled inject: peer ACCEPT + Mesh ABORT → Mesh wins; `mesh_accept=false` | Unused on n=1 happy path |
| **M-ABORT-2** | Anomaly / missing gate / failed NT → abort→RefuseTransport; never partial enable | Attempt with intentional missing precondition; binding final RefuseTransport | Design+NT |
| **M-ABORT-3** | Conflicting/missing judges → fail-closed ABORT / escalate I5; no auto-majority execute | Dual-conflict or missing-judge drill | Design |

---

## 6. Remaining acceptance — M-LEDGER

| ID | Design acceptance | Evidence required | Today |
|----|-------------------|-------------------|-------|
| **M-LEDGER-1** | Each attempt records required kinds: request/invoke/goal/continuity digests · `policy_version` · handle id · abort/allow codes | Gate5 step (7) completeness across **n≥N** | Partial (happy-path ledger) |
| **M-LEDGER-2** | Kill/deny attempts include `oversight` (+ `abort`); kill without ledger = FAIL | E-KILL pack | Not live-exercised |
| **M-LEDGER-3** | No secrets in explain; claim hygiene — forbid “live ready” / “100%” from sample | Grep + review | PASS on n=1 docs; must hold on multi |

**Missing required kind on any seal-candidate attempt → refuse further enable / fail seal attempt.**

---

## 7. Attach path to future measurement (still gated)

```
ENABLE_UNDER_FENCES (already SIGNED)
        │
        ▼
Gate5 (1)–(5) green · I5 armed · authorized impl path
        │
        ▼
Multi-canary pack: n ≥ N_min with E-* mix (§2–§3)
        │
        ▼
Fill M-KILL live · M-ABORT · M-LEDGER evidence
        │
        ▼
Gate6 live-measurement seal attempt  ← forbidden while n<N_min or edges missing
        │
        ▼
Permanent enable policy (separate) — NOT this CP; module LIVE stays False without runbook
```

**This CP stops at design.** Executing the pack needs operator intent + fences already in force; **no** permanent flag flip without Gate5 runbook + explicit permanent-enable policy (still OPEN).

---

## 8. What 「listo」 / product-ready live still needs (honest)

| Blocker | Status | Notes |
|---------|--------|-------|
| Gate6 metric **design** completion (this CP) | **DONE (DESIGN_ONLY)** | Does not measure |
| Multi-canary **n≥N** + edge pack measured | **OPEN** | n=1 today |
| M-KILL **live** + budget + resume drill | **OPEN** | Unit ≠ live |
| M-ABORT forced drills | **OPEN** | |
| M-LEDGER kill/abort completeness across n | **OPEN** | |
| **Codec impl** authorization | **OPEN** | CP-0076 = design only; needs **future impl CP** |
| Permanent `LIVE_API_ENABLED` enable policy / runbook | **OPEN** | Do **not** permanently flip without runbook |
| Full LiveHttpTransport shipped + default-off | **DONE (CP-0078 v0)** | `src_live_codec_shipped=true`; module LIVE false; streaming residual |
| NO_HELD / D3 / M1 / keys-in-git / push-tags | **Unchanged fences** | Not part of 「listo」 unlock |

**Bottom line:** Canary path under fences is met for **one** free-tier sample. Product-ready live is **not** listo until codec auth + multi-canary metric completion + permanent-enable policy land under fences.

---

## 9. Explicit non-goals / non-claims

- Re-running canary or flipping `LIVE_API_ENABLED` in this CP  
- Authorizing `LiveHttpTransport` impl (CP-0076 residual remains design-only)  
- Inventing kill latency SLO numbers beyond “ops-defined before measure”  
- Claiming Gate6 live-measurement sealed  
- 100% live product / advisory=SoT / n=1=SLO  
- Push, tags, secrets in git · NO_HELD unlocks · D3  

---

## 10. Exit criteria (this design CP)

| Exit item | Status |
|-----------|--------|
| Remaining M-KILL live / M-ABORT / M-LEDGER acceptance designed | **This doc** §§4–6 |
| Sample policy n≥N + variance/edge so n=1 cannot seal | **§2–§3** |
| DESIGN_ONLY CP minted | **CP-0077** |
| DeepSeek CP-0076 hygiene ACK cited; NEXT #1 executed | `REPLY_DEEPSEEK_CP0076_DESIGN_HYGIENE_ACK.md` |
| Checklist / wall / next-steps updated honestly | Companion updates |

**Not exit:** live measurement · multi-canary execute · codec impl · permanent enable.

---

## 11. Related

- `council/REPLY_DEEPSEEK_CP0076_DESIGN_HYGIENE_ACK.md`  
- `DESIGN_CP_0076_LIVE_HTTP_TRANSPORT_RESIDUAL.md` · `LIVE_HTTP_TRANSPORT_RESIDUAL_DESIGN.md`  
- `IMPL_CP_0075_GEMINI_FREE_CANARY.md` · `GATE5_CANARY_EVIDENCE.md` · `GATE6_CANARY_MEASUREMENT.md`  
- `GATE6_LIVE_ACCEPTANCE_METRICS.md` · `GATE6_DESIGN_SEALED.md`  
- `GEMINI_FREE_NEXT_STEPS.md` · `LIVE_READINESS_CHECKLIST.md` · `LIVE_100_OPERATOR_WALL.md`  
- `GATE5_LIVE_FLAG_FLIP_RUNBOOK.md` · CP-0058 / CP-0068 / CP-0069

---

*End GATE6_METRIC_COMPLETION_DESIGN — DESIGN_ONLY; n=1 cannot seal; M-KILL live / M-ABORT / M-LEDGER acceptance designed; no live enable; no codec impl; NO_HELD unchanged.*
