# Live readiness checklist (design-only)

**Status:** DESIGN ONLY — ordered gates for any future **live+API discussion**.  
**Does not** enable live · **does not** mint keys · **does not** call Gemini/providers · **does not** start D3 · **does not** push/tag.  
**Date:** 2026-09-28 ~23:16 ET — Gate1 **SIGNED ENABLE_UNDER_FENCES**; Gates 2–4 **ENABLE_READY**; **CP-0075..0085**; multi-canary n=6; Gate6 seal_candidate + R3 policy; full-adapter R0–R4 DONE / R5 OPEN; streaming DEFERRED; module LIVE_API_ENABLED=False  
**Operator decision:** Hold A **LEFT**; Gate1 upgraded DISCUSS_ONLY → **ENABLE_UNDER_FENCES**; `LIVE_API_ENABLED` still **False**; see leave-Hold note + `GEMINI_FREE_NEXT_STEPS.md` · `MESH_FULL_ADAPTER_LIVE_RV_DESIGN.md` · `DESIGN_CP_0081_MESH_FULL_ADAPTER_LIVE_RV.md`  
**Tip context:** `f30c4bb` → **CP-0082** Phase R1 compose / ENABLE signed / CP-0075..0081 chain / Gate6 DESIGN_SEALED / Gates 2–4  
**Wall:** `LIVE_100_OPERATOR_WALL.md` — ENABLE **SIGNED**; CP-0075..0085 **done** under fences; **R4 DONE** / **R5 OPEN**; streaming DEFERRED; Gate6 candidate remains; module LIVE_API=False / RefuseTransport  
**Dual council canary hygiene ACK:** DeepSeek + ChatGPT PASS → CP-0076. **DeepSeek handoff audit:** PASS_WITH_GAPS; NEXT-3 → **CP-0081**; R1–R4 → **CP-0082..0085**; Gate6 live-measurement → **CP-0086** (does **not** authorize R5 / flip LIVE / invent F4).
**Authority base:** `council/COUNCIL_AGREEMENT_D4.md` (F3/F4) · `docs/planning/D1_L_JUDGE_SAFETY_CASE_MATURATION.md` · `docs/planning/M1_NO_CONSENSUS_N2_SCOPE.md` · `docs/planning/GOOGLE_L_JUDGE_PEER_SPIKE.md`  
**Council note:** `council/NOTE_LIVE_READINESS.md` · Gate1 draft: `council/NOTE_GATE1_ACK_DRAFT.md` / `docs/planning/GATE1_LIVE_OPERATOR_ACK_DRAFT.md` · ENABLE draft: `docs/planning/GATE1_ENABLE_UNDER_FENCES_ACK_DRAFT.md` (**UNSIGNED**) · Gate2: `council/NOTE_GATE2_DESIGN_SEALED.md` / `docs/planning/GATE2_DESIGN_SEALED.md` · Gate3: `council/NOTE_GATE3_DESIGN_SEALED.md` / `docs/planning/GATE3_DESIGN_SEALED.md` · Gate4: `council/NOTE_GATE4_DESIGN_SEALED.md` / `docs/planning/GATE4_DESIGN_SEALED.md` / `GATE4_LIVE_DATA_POLICY.md` · Gate5: `council/NOTE_GATE5_FLIP_RUNBOOK.md` / `council/NOTE_GATE5_DESIGN_SEALED.md` / `docs/planning/GATE5_DESIGN_SEALED.md` / `GATE5_LIVE_FLAG_FLIP_RUNBOOK.md` · Gate6: `council/NOTE_GATE6_ACCEPTANCE_METRICS.md` / `council/NOTE_GATE6_DESIGN_SEALED.md` / `docs/planning/GATE6_DESIGN_SEALED.md` / `GATE6_LIVE_ACCEPTANCE_METRICS.md`

---

## 0. What this is / is not

| Is | Is not |
|----|--------|
| Ordered **governance gates** before any live *discussion* or enable cycle | An unlock, ACK, or `live=ENABLED` flip |
| Operator-facing answer to “what is missing for live+API?” | Permission to ship keys, network transports, or real Gemini calls |
| Compatible with mock / RefuseTransport / Google peer spike | A claim that D1/D2 sealed = live-ready |
| Explicit that **M1 N=2 NO_CONSENSUS_YET** does **not** block local mock judge API work | A Raft/N>2 / GIA / pkg0190 / train-70B path |

**Invariant:** flipping `live_adapter.enabled` / `LIVE_API_ENABLED` requires a **separate cycle** + **separate operator ACK** + **safety-case amendment** (D4 F4). This checklist does not pre-authorize that cycle.

---

## 1. Ordered gates (must pass in order)

Gates are **serial**. A later gate may be drafted in parallel as design text, but **cannot seal for enable** until earlier gates are satisfied. Checkbox state today reflects Gate1 **SIGNED ENABLE_UNDER_FENCES** + Gates **2–4 ENABLE_READY** + Gates **2–6** prior DESIGN_SEALED + Gate5 step (5) PASS / step (6) blocked + dry-run peer wire + CP-0074 posture. **`LIVE_API_ENABLED=False`.**

### Gate 1 — Operator ACK (live discussion / enable)

| Item | Rule | Today |
|------|------|-------|
| Separate ACK | Live *discussion* ≠ D4 lock ≠ Google tools APPROVE_WITH_FENCES ≠ D1 seal | **SIGNED — ENABLE_UNDER_FENCES** — `GATE1_ENABLE_UNDER_FENCES_ACK_SIGNED.md` (prior DISCUSS_ONLY retained) |
| Scope string | ACK must name provider(s), env, data classes, kill authority, rollback owner | **Filled** — Gemini free-tier canary only; Vertex OUT; local box/canary; single canary under kill-armed I5 after Gates 2–5 |
| Non-implication | Tool approvals, mock spikes, design seals, hygiene ACK do **not** count as ENABLE | Binding; confirmed on 「Aprobado」 signature |

**Exit:** Written operator ACK recording intent to *discuss* or *enable* under named fences. Still not an automatic `enabled=true`.  
**Today:** Gate1 exit met; CP-0075 + Gate5 canary done; module LIVE_API remains False (RefuseTransport-safe).

### Gate 2 — Safety evidence (D1 / D4-H)

| Item | Rule | Today |
|------|------|-------|
| Safety-case maturation | D1 artifacts cite D4-A..K; fail-closed RefuseTransport; containment + rollback **verification** (RV-*) | **Design sealed** (CP-0071) — evidence exists as *design*, not as live proof |
| Live amendment | Any live path needs safety-case **amendment** for real transport, keys, blast radius, compromise response | **ENABLE_READY** — `GATE2_ENABLE_READY.md` (+ prior DESIGN_SEALED); live RV under Mesh transport still **OPEN** (post-canary) |
| Kill path | I5 kill → RefuseTransport + continuity ABORT remains default until amended | Binding (amended wording in Gate2 doc §4; **not** live-armed) |

**Exit (design/discuss):** Live-safety amendment reviewed; mock RV drills still green; no silent codec; Gate1 DISCUSS_ONLY signed.  
**Today:** Gate2 **ENABLE_READY** under SIGNED ENABLE; mock RV green; Gate5 canary executed (advisory evidence); Mesh full-adapter live RV still OPEN (**R0–R4 DONE** CP-0081..0085; streaming DEFERRED; Gate6 live-measurement **SEALED** CP-0086; **R5 OPEN** operator F4); `LIVE_API_ENABLED=False`.

### Gate 3 — Authority Matrix in use (D4-A)

| Item | Rule | Today |
|------|------|-------|
| Frozen matrix | L_judge propose-only; I5 approve/veto; Operator sole live-enable ACK; RefuseTransport veto | **DESIGN_SEALED** (discuss/eval) — D1 §3 cited; AM-* IDs frozen in binding |
| In use | Runtime / adapter config and ops runbooks **reference** the matrix (propose/approve/veto/execute) — not prose-only | **ENABLE_READY** — `GATE3_ENABLE_READY.md` (+ prior DESIGN_SEALED); canary ops cite ready; runtime `enabled=true` still OPEN |
| Disagreement | Mesh ABORT > judge ACCEPT; I5 may stop post-advisory; no judge-over-judge override | Binding sealed for discuss (+ Gate3 AM-NT-1..7 intent) |

**Exit (design/discuss):** Matrix IDs bound in config/ops cite for DISCUSS_ONLY/eval; no role invents execute; Gate1 discuss + Gate2 design-sealed.  
**Today:** Gate3 **ENABLE_READY**; matrix cited for canary ops; runtime not live-enabled (`LIVE_API_ENABLED=False`).

### Gate 4 — Keys + data policy

| Item | Rule | Today |
|------|------|-------|
| No keys in repo | Raw API keys / Bearer / `sk-` material forbidden in tree, CI logs, evidence digests | **Held** (live=DISABLED; oob key only; **no Mesh live calls**) |
| secret_handle only | Versioned handles; I5 sees handle ids / digests, never raw secrets | **DESIGN_SEALED** (discuss/eval) — `GATE4_LIVE_DATA_POLICY.md` + `GATE4_DESIGN_SEALED.md`; handle `mesh://secrets/judge/gemini-free@v1`; path `/home/box/.config/neural-mesh/gemini.env` oob; CP-0058 / D1 §7.2 |
| Data classes | What may leave the box (prompts, digests, redacted envelopes) vs forbidden (operational Mesh SoT, plaintext secrets, unverified continuity) | **DESIGN_SEALED** (allowed vs forbidden classes); Mesh live egress still **N** until enable chain |
| Provider bounds | Free-tier Gemini (if ever) stays evaluation evidence; Vertex paid needs separate approval | Google fences; dry-run flag-gated (`30fe593`/`1e502c6`); Mesh live = RefuseTransport |
| Seal dependency | Serial gates: Gate 4 enable-ready when handle + canary data schedule ACK’d under ENABLE | **ENABLE_READY** — `GATE4_ENABLE_READY.md`; oob handle held; Gate5 canary **EXECUTED** (CP-0075) |

**Exit (design/discuss):** Written data-handling schedule + secret_handle lifecycle for DISCUSS_ONLY/eval; eval handle oob; still no keys committed.  
**Today:** Gate4 **ENABLE_READY**; secrets oob only; Gate5 canary done under CP-0075; LiveHttpTransport v0 under CP-0078 (default-off).

### Gate 5 — Adapter: RefuseTransport → live flag

| Item | Rule | Today |
|------|------|-------|
| Default binding | Every live peer slot defaults to `RefuseTransport` → `ENGINE_DISABLED` / `PEER_LIVE_DISABLED` | **In force** (CP-0058; Google spike T-gemini-c) |
| Flag transition | `live_adapter.enabled` / `LIVE_API_ENABLED` remain **false** until Gate 1–4 enable-ready + ENABLE ACK + this gate’s acceptance tests | **false** (held); **LIVE_API_ENABLED=False** — step (6) **not** flipped |
| Flip procedure (design) | (1)–(7) ordered walk | Steps (1)–(4) ENABLE_READY · (5) health **PASS** · (6)–(7) **EXECUTED** — CP-0075; `GATE5_CANARY_EVIDENCE.md`; dry-run ≠ canary |
| Fail-closed | Any missing gate → refuse network; no partial enable; abort→RefuseTransport; never partial enable | Binding (NT-1..NT-10 in runbook) |

**Exit (design/discuss):** Documented flip runbook + negative tests still prove refuse-default; enable remains operator-gated; canary marked NOT AUTHORIZED under DISCUSS_ONLY.  
**Today:** Gate5 procedure DESIGN_SEALED; step (5) PASS; step (6)–(7) **EXECUTED** (CP-0075); module LIVE_API=False. Gate6 metrics DESIGN_SEALED; sample measured (n=1 ≠ SLO). LiveHttpTransport v0 = **CP-0078 IMPL** (default-off; design was CP-0076).

### Gate 6 — Acceptance metrics (D4-E / D4-J / D4-K)

| Item | Rule | Today |
|------|------|-------|
| Beyond pytest | Correctness / safety / reliability / human-factors categories defined | Design (D1 §10.1) + live-path attachment in Gate6 bundle |
| Measurable pass intent | False-approval deny; containment success; missing/conflicting judges fail-closed; adversarial disagreement handled | **DESIGN_SEALED** (metrics) — refuse-default negatives, kill latency, no secret leakage, advisory-only judge, abort>accept, ledger evidence (`GATE6_LIVE_ACCEPTANCE_METRICS.md` + `GATE6_DESIGN_SEALED.md`) |
| Signoff-before-live-discussion | D4-K ten conditions (authority, consensus status explicit, oversight bounds, continuity limits, rollback+RV, evidence chain, metrics, claim hygiene, disagreement process, no hidden review→ops) | **DESIGN_SEALED** attachment; ENABLE discussion **not** opened; dry-run metrics evidence-only ≠ live RV |
| Evidence | Digests + policy version + audit completeness; no secrets in explain | Binding (M-LEDGER-* / M-SEC-*); live measurement **OPEN** |

**Exit (design/discuss):** Named metric bundle DESIGN_SEALED for DISCUSS_ONLY; pytest remains necessary but insufficient alone; live measurement marked OPEN.  
**Today:** Gate6 **DESIGN_SEALED**; **CP-0079** n=6 seal-candidate + **CP-0080** M-KILL-2 **PASS** / M-ABORT-3 **PASS**; permanent policy default False; F4 **DESIGN_SEALED** / product ACK **UNSIGNED**; **CP-0081** DESIGN + **CP-0082 R1 DONE** / **R2 OPEN**. Listo **bajo fences**; full-adapter RV OPEN (R1 compose done); product permanent blocked on F4 ACK.

### Gate 7 — Optional D3 (perf A/B)

| Item | Rule | Today |
|------|------|-------|
| ACK-gated | `MESH_PERF_EXPERIMENTAL` stays **OFF** until explicit operator ACK | **OFF** / **D3 NOT ACKed** |
| Order | D1→D2→D3 (F10); D3 does **not** unlock live or M1 | Binding |
| Role vs live | Optional mock bench / hotspot research; **orthogonal** to Gates 1–6 | May run later under separate ACK |
| Non-block | Skipping D3 does **not** unblock live; completing D3 does **not** imply live | Explicit |

**Exit (if chosen):** D3 ACK + flag discipline; results filed as research evidence only.

### Gate 8 — M1 N=2 posture does **not** block local judge API

| Item | Rule | Today |
|------|------|-------|
| M1 posture | **NO_CONSENSUS_YET** permanent under N=2 scope (CP-0074) | **In force** |
| Local / mock judge API | Mock multi-judge, RefuseTransport adapter, Google **mock** peer correlation — **allowed** under fences | **Allowed** (spikes present) |
| Not blocked by M1 | Permanent NO_CONSENSUS_YET ≠ freeze on local evaluation harnesses | Clarified here |
| Still blocked | Real network judge calls, live=ENABLED, Raft/N>2 unlock, claiming peer advisory = consensus | Binding |
| Dual advisory ≠ M1 | Gemini/mock dual agree ≠ ratified consensus; ≠ unlock | Google / M1 notes |

**Exit:** Operators may continue local judge API / mock work without waiting for M1 ratification; live network API still waits on Gates 1–6 (+ optional 7).

---

## 2. Compact status board

| # | Gate | Blocks live+API? | Status @ Gate6 DESIGN_SEALED (DISCUSS_ONLY / metrics) |
|---|------|------------------|------------------------------------------------------|
| 1 | Operator ACK | **Yes** (enable) | **SIGNED ENABLE_UNDER_FENCES** (`GATE1_ENABLE_UNDER_FENCES_ACK_SIGNED.md`); prior DISCUSS_ONLY retained |
| 2 | Safety evidence (+ live amendment) | **Yes** (enable) | **ENABLE_READY** (`GATE2_ENABLE_READY.md`); Mesh full-adapter live RV OPEN (R1 DONE CP-0082; R2 OPEN) |
| 3 | Authority Matrix in use | **Yes** (enable) | **ENABLE_READY** (`GATE3_ENABLE_READY.md`); runtime not live-enabled |
| 4 | Keys + data policy | **Yes** | **ENABLE_READY** (`GATE4_ENABLE_READY.md`); handle oob; secrets not in git |
| 5 | RefuseTransport → live flag | **Yes** | Step (5) **PASS**; step (6) **EXECUTED** (CP-0075 canary HTTP 200); module `LIVE_API_ENABLED=False` final |
| 6 | Acceptance metrics / D4-K | **Yes** | **DESIGN_SEALED**; **CP-0079** n=6 + **CP-0080** M-KILL-2/M-ABORT-3 **PASS**; policy default False; F4 design sealed / ACK **UNSIGNED**; **CP-0081** RV design |
| 7 | Optional D3 | No (orthogonal) | NOT ACKed / flag OFF |
| 8 | M1 N=2 vs local judge API | Clarifies non-block for **local/mock** | Local/mock OK; live still blocked by 1–6 |

**Bottom line:** Gate1 **SIGNED ENABLE_UNDER_FENCES**. Gates **2–4 ENABLE_READY**. **CP-0075..0082** under fences (canary + LHT + multi-canary + policy + kill budget + abort-3 + F4 design + full-adapter R0 + **R1 compose**). Tip base **`f30c4bb`**. Module **`LIVE_API_ENABLED=False`**. 「Listo」 **bajo fences YES**; full-adapter RV **R1 DONE / R2 OPEN**; product permanent needs **signed F4 product ACK** (draft unsigned). NO_HELD unchanged. See `GEMINI_FREE_NEXT_STEPS.md`.

---

## 3. Explicit non-goals (this doc)

- `live=ENABLED` / `LIVE_API_ENABLED=true` / `live_adapter.enabled=true`
- API keys in repo, env commits, or CI secrets files
- Real Gemini / Vertex / AI Studio production traffic
- Starting D3 or flipping `MESH_PERF_EXPERIMENTAL`
- Push, tags, pkg0190, v0.19, GIA, Raft/N>2, train-70B, SaaS
- Minting a feature CP solely for this checklist (docs-only unless operator opens a cycle)

---

## 4. Related

- `docs/planning/LIVE_100_OPERATOR_WALL.md` — DONE vs BLOCKED on operator; Mesh 0.18 local/mock vs live+API 100%
- `council/NOTE_LIVE_READINESS.md`
- `docs/planning/GATE1_LIVE_OPERATOR_ACK_DRAFT.md` · `GATE1_LIVE_OPERATOR_ACK_SIGNED.md` · `council/NOTE_GATE1_ACK_DRAFT.md` · `council/NOTE_LEAVE_HOLD_GATE1_DISCUSS_ONLY.md` · `docs/planning/GEMINI_FREE_NEXT_STEPS.md`
- `docs/planning/GATE2_LIVE_SAFETY_CASE_AMENDMENT.md` · `GATE2_DESIGN_SEALED.md` · `council/NOTE_GATE2_SAFETY_AMENDMENT.md` · `council/NOTE_GATE2_DESIGN_SEALED.md`
- `docs/planning/GATE3_AUTHORITY_MATRIX_BINDING.md` · `GATE3_DESIGN_SEALED.md` · `council/NOTE_GATE3_AUTHORITY_MATRIX.md` · `council/NOTE_GATE3_DESIGN_SEALED.md`
- `docs/planning/GATE4_LIVE_DATA_POLICY.md` · `GATE4_DESIGN_SEALED.md` · `council/NOTE_GATE4_DATA_POLICY.md` · `council/NOTE_GATE4_DESIGN_SEALED.md`
- `docs/planning/GATE5_LIVE_FLAG_FLIP_RUNBOOK.md` · `GATE5_DESIGN_SEALED.md` · `council/NOTE_GATE5_FLIP_RUNBOOK.md` · `council/NOTE_GATE5_DESIGN_SEALED.md`
- `docs/planning/GATE6_LIVE_ACCEPTANCE_METRICS.md` · `GATE6_DESIGN_SEALED.md` · `council/NOTE_GATE6_ACCEPTANCE_METRICS.md` · `council/NOTE_GATE6_DESIGN_SEALED.md`
- `docs/planning/GATE1_ENABLE_UNDER_FENCES_ACK_SIGNED.md` · `GATE1_ENABLE_UNDER_FENCES_ACK_DRAFT.md` (historical)
- `docs/planning/LIVE_HTTP_TRANSPORT_RESIDUAL_DESIGN.md` · `DESIGN_CP_0076_LIVE_HTTP_TRANSPORT_RESIDUAL.md` · `council/NOTE_DESIGN_CP_0076_LIVE_HTTP_TRANSPORT.md`
- `docs/planning/MESH_FULL_ADAPTER_R1_SOT_REFUSE_I5_COMPOSE_CHECKLIST.md` · `IMPL_CP_0082_FULL_ADAPTER_R1_COMPOSE.md` · `council/NOTE_CP_0082_FULL_ADAPTER_R1_COMPOSE.md`
- `MESH_FULL_ADAPTER_R4_STREAMING_DEFER_SEAL.md` · `IMPL_CP_0085_STREAMING_DEFER_SEAL.md` · `council/NOTE_CP_0085_STREAMING_DEFER_SEAL.md`
- `docs/planning/GATE6_METRIC_COMPLETION_DESIGN.md` · `DESIGN_CP_0077_GATE6_METRIC_COMPLETION.md` · `council/NOTE_DESIGN_CP_0077_GATE6_METRIC_COMPLETION.md`
- `council/REPLY_DEEPSEEK_CP0076_DESIGN_HYGIENE_ACK.md` · `council/NOTE_DEEPSEEK_ACK_GATE5_CANARY.md` · dual REPLY_*_GATE5_CANARY_HYGIENE_ACK.md
  - `docs/planning/GATE2_ENABLE_READY.md` · `GATE3_ENABLE_READY.md` · `GATE4_ENABLE_READY.md` · `GATE5_HEALTH_CHECK_EVIDENCE.md`
- `council/COUNCIL_AGREEMENT_D4.md` · `council/D4_CHATGPT_FINDINGS.md`
- `council/NOTE_GOOGLE_AI_TOOLS_FENCED.md` · `docs/planning/GOOGLE_L_JUDGE_PEER_SPIKE.md`
- `docs/planning/D1_L_JUDGE_SAFETY_CASE_MATURATION.md` (CP-0071)
- `docs/planning/M1_NO_CONSENSUS_N2_SCOPE.md` (CP-0074)
- `council/NOTE_OPERATOR_HOLD_POST_D2.md` · `council/NOTE_OPERATOR_HOLD_POST_WALL.md` · `council/NOTE_M1_NO_CONSENSUS_N2_SCOPE.md`
- `docs/planning/HOLD_MOCK_NEXT.md` — mock-only cycles under Hold
- `src/neural_mesh/packaging/l_judge_live_adapter_safety.py` (`RefuseTransport`)

---

*End LIVE_READINESS_CHECKLIST — tip f30c4bb→CP-0082; CP-0075..0082; R1 DONE / R2 OPEN; not an unlock; LIVE_API_ENABLED=False.*
