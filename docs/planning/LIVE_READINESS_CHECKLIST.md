# Live readiness checklist (design-only)

**Status:** DESIGN ONLY — ordered gates for any future **live+API discussion**.  
**Does not** enable live · **does not** mint keys · **does not** call Gemini/providers · **does not** start D3 · **does not** push/tag.  
**Date:** 2026-09-28 America/New_York (EDT) — Gate1 SIGNED DISCUSS_ONLY (leave Hold)  
**Operator decision:** Hold A **LEFT** 2026-09-28 — Gate1 **SIGNED DISCUSS_ONLY** (Gemini free-tier eval only); live still **DISABLED**; see `council/NOTE_LEAVE_HOLD_GATE1_DISCUSS_ONLY.md` · `docs/planning/GEMINI_FREE_NEXT_STEPS.md`  
**Tip context:** Gate2 DESIGN_SEALED atop peer wire `30fe593` / dry-run `1e502c6` / leave-Hold `fc4ef9e` / HOLD_STAY ~`9348651` / Gate1 **SIGNED DISCUSS_ONLY** / **CP-0074**  
**Wall:** `docs/planning/LIVE_100_OPERATOR_WALL.md` — Gate1 **SIGNED DISCUSS_ONLY**; Gate2 **DESIGN_SEALED** (discuss/eval); Gates 3–6 **cannot seal for enable** yet  
**Authority base:** `council/COUNCIL_AGREEMENT_D4.md` (F3/F4) · `docs/planning/D1_L_JUDGE_SAFETY_CASE_MATURATION.md` · `docs/planning/M1_NO_CONSENSUS_N2_SCOPE.md` · `docs/planning/GOOGLE_L_JUDGE_PEER_SPIKE.md`  
**Council note:** `council/NOTE_LIVE_READINESS.md` · Gate1 draft: `council/NOTE_GATE1_ACK_DRAFT.md` / `docs/planning/GATE1_LIVE_OPERATOR_ACK_DRAFT.md` · Gate2: `council/NOTE_GATE2_DESIGN_SEALED.md` / `docs/planning/GATE2_DESIGN_SEALED.md` · Gate4: `council/NOTE_GATE4_DATA_POLICY.md` / `docs/planning/GATE4_LIVE_DATA_POLICY.md` · Gate5: `council/NOTE_GATE5_FLIP_RUNBOOK.md` / `docs/planning/GATE5_LIVE_FLAG_FLIP_RUNBOOK.md` · Gate6: `council/NOTE_GATE6_ACCEPTANCE_METRICS.md` / `docs/planning/GATE6_LIVE_ACCEPTANCE_METRICS.md`

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

Gates are **serial**. A later gate may be drafted in parallel as design text, but **cannot seal for enable** until earlier gates are satisfied. Checkbox state today reflects Gate1 **SIGNED DISCUSS_ONLY** + Gate2 **DESIGN_SEALED** (discuss/eval) + Gates **3–6 design drafts** (none sealed for enable) + dry-run peer wire + CP-0074 posture. **live=DISABLED.**

### Gate 1 — Operator ACK (live discussion / enable)

| Item | Rule | Today |
|------|------|-------|
| Separate ACK | Live *discussion* ≠ D4 lock ≠ Google tools APPROVE_WITH_FENCES ≠ D1 seal | **SIGNED — DISCUSS_ONLY** — `docs/planning/GATE1_LIVE_OPERATOR_ACK_DRAFT.md` / `GATE1_LIVE_OPERATOR_ACK_SIGNED.md` |
| Scope string | ACK must name provider(s), env, data classes, kill authority, rollback owner | **Filled** — Gemini free-tier eval only; Vertex OUT; local box/discuss; egress none until Gates 2–5 |
| Non-implication | Tool approvals, mock spikes, Colab placeholders do **not** count as this ACK | Binding (Google fence §10); confirmed on signature |

**Exit:** Written operator ACK artifact recording intent to *discuss* or *enable* live under named fences. Still not an automatic `enabled=true`.  
**Today:** Gate1 exit **met for DISCUSS_ONLY**; enable still requires Gates 2–5 (+ Gate 6) and (if desired) ENABLE_UNDER_FENCES intent.

### Gate 2 — Safety evidence (D1 / D4-H)

| Item | Rule | Today |
|------|------|-------|
| Safety-case maturation | D1 artifacts cite D4-A..K; fail-closed RefuseTransport; containment + rollback **verification** (RV-*) | **Design sealed** (CP-0071) — evidence exists as *design*, not as live proof |
| Live amendment | Any live path needs safety-case **amendment** for real transport, keys, blast radius, compromise response | **DESIGN_SEALED** (DISCUSS_ONLY/eval) — `GATE2_LIVE_SAFETY_CASE_AMENDMENT.md` + `GATE2_DESIGN_SEALED.md`; bound to `30fe593`/`1e502c6`, Authority Matrix, RefuseTransport, secret_handle; **Missing Mesh live proof**; ENABLE seal **OPEN** |
| Kill path | I5 kill → RefuseTransport + continuity ABORT remains default until amended | Binding (amended wording in Gate2 doc §4; **not** live-armed) |

**Exit (design/discuss):** Live-safety amendment reviewed; mock RV drills still green; no silent codec; Gate1 DISCUSS_ONLY signed.  
**Today:** Gate2 **DESIGN_SEALED** for DISCUSS_ONLY/eval; ENABLE seal still needs operator **ENABLE_UNDER_FENCES** ACK + live proof; RV drills mock-green only; **live=DISABLED**.

### Gate 3 — Authority Matrix in use (D4-A)

| Item | Rule | Today |
|------|------|-------|
| Frozen matrix | L_judge propose-only; I5 approve/veto; Operator sole live-enable ACK; RefuseTransport veto | **Design present** (D1 §3) — cited by binding doc |
| In use | Runtime / adapter config and ops runbooks **reference** the matrix (propose/approve/veto/execute) — not prose-only | **Binding drafted as design** — `docs/planning/GATE3_AUTHORITY_MATRIX_BINDING.md` (matrix IDs + config/ops cite); runtime still Refuse default; **cannot seal** |
| Disagreement | Mesh ABORT > judge ACCEPT; I5 may stop post-advisory; no judge-over-judge override | Binding in design (+ Gate3 AM-NT-* intent) |

**Exit:** Live cycle cites matrix IDs in config/policy version; no role invents execute authority.  
**Today:** binding **drafted as design**; live ops **not** armed; Gate2 design-sealed (discuss) → Gate 3 is **next** design seal; enable seal still **OPEN / cannot seal**.

### Gate 4 — Keys + data policy

| Item | Rule | Today |
|------|------|-------|
| No keys in repo | Raw API keys / Bearer / `sk-` material forbidden in tree, CI logs, evidence digests | **Held** (live=DISABLED; spike uses no keys; **no real calls**) |
| secret_handle only | Versioned handles; I5 sees handle ids / digests, never raw secrets | **Design schedule drafted** — `docs/planning/GATE4_LIVE_DATA_POLICY.md` (create/rotate/revoke; handles outside repo); CP-0058 / D1 §7.2 |
| Data classes | What may leave the box (prompts, digests, redacted envelopes) vs forbidden (operational Mesh SoT, plaintext secrets, unverified continuity) | **Design schedule drafted** (allowed vs forbidden classes); still **no real calls** |
| Provider bounds | Free-tier Gemini (if ever) stays evaluation evidence; Vertex paid needs separate approval | Google fences; dry-run schedule design-only in Gate4 doc |
| Seal dependency | Serial gates: Gate 4 **cannot seal** until handle provisioned + data schedule ACK’d for enable path | **Cannot seal** — secret_handle not provisioned; no real calls |

**Exit:** Written data-handling schedule + secret_handle lifecycle for the ACK’d env; still no keys committed.  
**Today:** schedule **drafted**; Gate1 DISCUSS_ONLY; handle **not** provisioned → Gate 4 **OPEN / cannot seal**; no keys / no real calls.

### Gate 5 — Adapter: RefuseTransport → live flag

| Item | Rule | Today |
|------|------|-------|
| Default binding | Every live peer slot defaults to `RefuseTransport` → `ENGINE_DISABLED` / `PEER_LIVE_DISABLED` | **In force** (CP-0058; Google spike T-gemini-c) |
| Flag transition | `live_adapter.enabled` / `LIVE_API_ENABLED` remain **false** until Gate 1–4 + this gate’s acceptance tests | **false** (held) |
| Flip procedure (design) | (1) ACK present (2) safety amendment (3) matrix-bound config (4) keys via handle outside repo (5) health check (6) single canary call under kill-armed I5 (7) ledger evidence | **Runbook drafted** — `docs/planning/GATE5_LIVE_FLAG_FLIP_RUNBOOK.md`; flip **not executed**; Gates **2–4 not sealed** (Gate1 discuss-only) |
| Fail-closed | Any missing gate → refuse network; no partial enable; abort→RefuseTransport; never partial enable | Binding (negative tests in runbook) |

**Exit:** Documented flip runbook + negative tests still prove refuse-default; enable remains operator-gated.  
**Today:** runbook **drafted**; flip **not** executed; Gates **2–4 not sealed** for enable → Gate 5 **OPEN / cannot seal**.

### Gate 6 — Acceptance metrics (D4-E / D4-J / D4-K)

| Item | Rule | Today |
|------|------|-------|
| Beyond pytest | Correctness / safety / reliability / human-factors categories defined | Design (D1 §10.1) + live-path attachment in Gate6 bundle |
| Measurable pass intent | False-approval deny; containment success; missing/conflicting judges fail-closed; adversarial disagreement handled | **Bundle drafted** — refuse-default negatives, kill latency, no secret leakage, advisory-only judge, abort>accept, ledger evidence (`GATE6_LIVE_ACCEPTANCE_METRICS.md`) |
| Signoff-before-live-discussion | D4-K ten conditions (authority, consensus status explicit, oversight bounds, continuity limits, rollback+RV, evidence chain, metrics, claim hygiene, disagreement process, no hidden review→ops) | **Checklist usable** + Gate6 §3 attachment; live discussion **not** opened |
| Evidence | Digests + policy version + audit completeness; no secrets in explain | Binding (M-LEDGER-* / M-SEC-*) |

**Exit:** Named metric bundle attached to the live ACK cycle; pytest remains necessary but insufficient alone.  
**Today:** bundle **drafted as design**; attached for discuss context only; canary **NOT executed**; Gate1 DISCUSS_ONLY → Gate 6 **OPEN / cannot seal**.

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

| # | Gate | Blocks live+API? | Status @ Gate2 DESIGN_SEALED (DISCUSS_ONLY/eval) |
|---|------|------------------|--------------------------------------------------|
| 1 | Operator ACK | **Yes** (enable) | **SIGNED DISCUSS_ONLY** — Gemini free eval (`GATE1_LIVE_OPERATOR_ACK_SIGNED.md`) |
| 2 | Safety evidence (+ live amendment) | **Yes** (enable) | **DESIGN_SEALED** discuss/eval (`GATE2_DESIGN_SEALED.md`); ENABLE seal **OPEN**; Missing Mesh live proof |
| 3 | Authority Matrix in use | **Yes** | Binding **drafted as design** (`GATE3_AUTHORITY_MATRIX_BINDING.md`); live ops not armed; **next design seal**; **cannot seal for enable** |
| 4 | Keys + data policy | **Yes** | Schedule **drafted** (`GATE4_LIVE_DATA_POLICY.md`); no-keys / no-calls held; **cannot seal** |
| 5 | RefuseTransport → live flag | **Yes** | Runbook **drafted** (`GATE5_LIVE_FLAG_FLIP_RUNBOOK.md`); flip **not executed**; Refuse default ON; **cannot seal** |
| 6 | Acceptance metrics / D4-K | **Yes** | Bundle **drafted as design** (`GATE6_LIVE_ACCEPTANCE_METRICS.md`); canary not executed; **cannot seal** |
| 7 | Optional D3 | No (orthogonal) | NOT ACKed / flag OFF |
| 8 | M1 N=2 vs local judge API | Clarifies non-block for **local/mock** | Local/mock OK; live still blocked by 1–6 |

**Bottom line:** Gate1 **SIGNED DISCUSS_ONLY**. Gate2 **DESIGN_SEALED** (discuss/eval). Missing for live+API **enable** = ENABLE_UNDER_FENCES operator ACK + Gates **2(enable)–6** with live proof + Gate5 canary. **Next design step: Gate 3.** See `docs/planning/GEMINI_FREE_NEXT_STEPS.md`. Mesh **0.18 local/mock** ≠ live+API **100%**. **live=DISABLED**. D3 optional. M1 permanent NO_CONSENSUS_YET does **not** freeze local mock judge work.

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
- `docs/planning/GATE3_AUTHORITY_MATRIX_BINDING.md` · `council/NOTE_GATE3_AUTHORITY_MATRIX.md`
- `docs/planning/GATE4_LIVE_DATA_POLICY.md` · `council/NOTE_GATE4_DATA_POLICY.md`
- `docs/planning/GATE5_LIVE_FLAG_FLIP_RUNBOOK.md` · `council/NOTE_GATE5_FLIP_RUNBOOK.md`
- `docs/planning/GATE6_LIVE_ACCEPTANCE_METRICS.md` · `council/NOTE_GATE6_ACCEPTANCE_METRICS.md`
- `council/COUNCIL_AGREEMENT_D4.md` · `council/D4_CHATGPT_FINDINGS.md`
- `council/NOTE_GOOGLE_AI_TOOLS_FENCED.md` · `docs/planning/GOOGLE_L_JUDGE_PEER_SPIKE.md`
- `docs/planning/D1_L_JUDGE_SAFETY_CASE_MATURATION.md` (CP-0071)
- `docs/planning/M1_NO_CONSENSUS_N2_SCOPE.md` (CP-0074)
- `council/NOTE_OPERATOR_HOLD_POST_D2.md` · `council/NOTE_OPERATOR_HOLD_POST_WALL.md` · `council/NOTE_M1_NO_CONSENSUS_N2_SCOPE.md`
- `docs/planning/HOLD_MOCK_NEXT.md` — mock-only cycles under Hold
- `src/neural_mesh/packaging/l_judge_live_adapter_safety.py` (`RefuseTransport`)

---

*End LIVE_READINESS_CHECKLIST — design-only; not an unlock.*
