# Gate 1 — ENABLE_UNDER_FENCES operator ACK — **SIGNED**

**Status:** **SIGNED — ENABLE_UNDER_FENCES**  
**Effect:** Records operator intent to *enable under fences* (Gemini free-tier eval → live canary path under fences after Gates 2–5 enable-ready).  
**It does NOT alone:** flip flags · mint keys into git · authorize Mesh live without Gate5 walk · start D3 · push/tag · mint CP · unlock NO_HELD · claim dry-run = canary / live RV.  
**Prior Gate1:** `docs/planning/GATE1_LIVE_OPERATOR_ACK_SIGNED.md` — **DISCUSS_ONLY** (superseded *for intent* by this ENABLE ACK; DISCUSS_ONLY record retained).  
**Unsigned draft (historical):** `docs/planning/GATE1_ENABLE_UNDER_FENCES_ACK_DRAFT.md`

**Date drafted:** 2026-09-28 ~18:55 EDT (America/New_York)  
**Date signed:** 2026-09-28 ~19:41 EDT (America/New_York)  
**Author (docs):** Grok Bot `<grok-bot@local>` — recorded operator signature; did not invent claims beyond operator mark  
**Operator ACK:** Joan / Yoan V (repo owner) — chat message **「Aprobado」** 2026-09-28 ~19:41 ET in context of honest wall = approve signing ENABLE_UNDER_FENCES  
**Tip at sign base:** `a816c34` (dual Gate2–6 hygiene ACK PASS; live was DISABLED pending this signature)  
**Package posture:** **0.18.0 HELD** · **Hold A LEFT** · Gate1 intent **ENABLE_UNDER_FENCES** · **LIVE_API_ENABLED=False** until Gate5 walk + authorized impl posture · RefuseTransport default **ON** · **M1=NO_CONSENSUS_YET** · **D3 NOT ACKed** · **NO_HELD** stays NO_HELD

**Checklist:** `docs/planning/LIVE_READINESS_CHECKLIST.md` · wall `docs/planning/LIVE_100_OPERATOR_WALL.md`  
**Runbook:** `docs/planning/GATE5_LIVE_FLAG_FLIP_RUNBOOK.md` · `GATE5_DESIGN_SEALED.md`

---

## 0. What this is / is not

| Is | Is not |
|----|--------|
| **Signed** ACK for intent **ENABLE_UNDER_FENCES** | Automatic `LIVE_API_ENABLED=true` / `live_adapter.enabled=true` |
| Intent upgrade from DISCUSS_ONLY → enable *under named fences* for Gemini free-tier canary path | Permission to skip Gates 2–5 enable-ready / Gate5 walk / I5 kill-armed canary |
| Compatible with RefuseTransport defaults, oob keys, rollback, NO_HELD held | A claim that design seals alone = live proof / consciousness / unlocks |
| Explicit: this ACK alone never flips flags | A substitute for Gate5 canary ledger or Gate6 live measurement |

**Invariant (D4 F3/F4):** flipping live requires **this ACK (signed)** + Gates **2–5 enable**-ready + safety-case live path + Gate5 canary under kill-armed I5 + Gate6 metrics measured. Design seals under prior DISCUSS_ONLY did **not** authorize that flip; this ACK opens the enable chain.

---

## 1. Explicit non-implication (binding)

The following **do NOT count** as substitutes for this ENABLE ACK:

| Prior artifact | Why it is not this ACK |
|----------------|------------------------|
| Gate1 **SIGNED DISCUSS_ONLY** | Discussion ≠ enable intent (now upgraded by *this* artifact) |
| Gates **2–6 DESIGN_SEALED** (discuss/eval) | Design seals ≠ ENABLE seals / live proof |
| Dual council hygiene ACK PASS (`a816c34`) | Hygiene ≠ operator ENABLE signature |
| Dry-run peer `30fe593` / evidence `1e502c6` | Eval dry-run = evidence-only ≠ live RV / ≠ canary |
| Google free AI tools APPROVE_WITH_FENCES | Tool approval ≠ ENABLE ACK |
| D4 lock / D1 seal / council PASS | Governance ≠ operator ENABLE ACK |
| Unsigned ENABLE draft | Draft ≠ signature |

**Operator checkbox (recorded on signature via 「Aprobado」):**  
- [x] I confirm none of the above substitute for this ENABLE_UNDER_FENCES ACK.

---

## 2. Scope string (operator confirmed)

### 2.1 Provider(s)

| Field | Operator fill |
|-------|---------------|
| Provider class | `[x] Gemini free-tier canary only` · `[ ] other: _______________` |
| Paid / Vertex | **OUT** unless separate approval — `[x] still OUT` · `[ ] separate approval filed: _______________` |
| Role of provider output | Evidence / evaluation input only — **not** Mesh SoT, consensus, or execution authority: `[x] confirmed` |

### 2.2 Environment

| Field | Operator fill |
|-------|---------------|
| Environment | `[x] local box / canary` · `[ ] other (name): _______________` |
| Network egress for live peer | `[x] single canary under kill-armed I5 (after Gates 2–5 enable-ready)` · `[ ] forbidden until filled` |
| Config flags before canary | `live_adapter.enabled=false` · `LIVE_API_ENABLED=false` · RefuseTransport default **ON** until Gate5 walk — `[x] confirmed held until walk` |

### 2.3 Data classes allowed to leave the box (canary)

| Class | Allowed? (operator) | Notes |
|-------|---------------------|-------|
| Redacted / synthetic prompts for canary | `[x] Y` · `[ ] N` | Per Gate4 schedule |
| Digests / evidence refs (no secrets) | `[x] Y` · `[ ] N` | |
| Operational Mesh SoT / continuity plaintext | **N held** — `[x] N held` | |
| Raw secrets / API keys / Bearer / `sk-` | **N held** — secret_handle oob only — `[x] N held` | Key remains `/home/box/.config/neural-mesh/gemini.env` only |
| Unverified continuity / orphan state | **N held** — `[x] N held` | |

**Live data schedule cite:** `[x] Gate4 ENABLE path ACK’d via ENABLE-ready seal docs (serial with this ACK)`

### 2.4 Kill authority (I5)

| Field | Operator fill / confirm |
|-------|-------------------------|
| Kill path | I5 kill → RefuseTransport + continuity **ABORT** + emergency `enabled=false` |
| Kill armed before any canary | `[x] confirmed` |
| Authority cite | D1 §3 Authority Matrix · D1 §6 Oversight I5 · Gate5 runbook · Gate3 binding |

### 2.5 Rollback owner

| Field | Operator fill |
|-------|---------------|
| Rollback owner | `[x] Operator (Yoan / Joan)` · `[ ] I5 + Operator quorum (A4)` · `[ ] name: _______________` |
| Verification | RV-1..RV-7 required post-rollback (D1 §8.4) — `[x] confirmed` |
| Scope | Revert `enabled=false` + RefuseTransport; re-enable requires re-walk Gate5 (1)–(7) — `[x] confirmed` |

### 2.6 Explicitly OUT of scope (this ACK)

| Out of scope | Status |
|--------------|--------|
| pkg0190 / package 0.19.0 open | **OUT** |
| Raft / N>2 topology unlock | **OUT** |
| GIA unlock | **OUT** |
| train 70B / 128B now | **OUT** |
| SaaS migration | **OUT** |
| D3 / `MESH_PERF_EXPERIMENTAL` without **separate** D3 ACK | **OUT** |
| Keys in repo / CI / evidence digests | **OUT** |
| Claiming Gemini/mock dual agree = M1 consensus | **OUT** |
| Auto-flip without Gate5 walk / without kill-armed I5 | **OUT** |
| Treating dry-run as canary / live RV | **OUT** |
| Invented unlocks / consciousness claims | **OUT** |

**Operator checkbox:**  
- [x] I confirm all rows above remain OUT under this ACK.

---

## 3. Authority Matrix summary (cite — do not amend here)

From `docs/planning/D1_L_JUDGE_SAFETY_CASE_MATURATION.md` §3 + Gate3 DESIGN_SEALED:

| Role | Live-relevant bound |
|------|---------------------|
| **L_judge** | Propose-only (advisory); cannot approve/veto/execute live |
| **Oversight I5** | Approve/deny/pause/**kill**; does not run side-effects alone |
| **RefuseTransport** | Fail-closed veto default until controlled Gate5 walk |
| **Operator** | **Sole live-enable ACK authority** (F4); final for A3/A4 |

Disagreement: Mesh ABORT > judge ACCEPT; I5 may stop post-advisory; no judge-over-judge override.

---

## 4. Intent (selected)

| Intent code | Meaning | Still requires Gates 2–5 enable-ready before any flag flip? |
|-------------|---------|--------------------------------------------------------------|
| **DISCUSS_ONLY** | (prior Gate1) Open discussion; no enable | Yes — retained as prior record |
| **ENABLE_UNDER_FENCES** | Intent to enable under this scope + Gates 2–5 enable + safety live path + canary | **Yes** — this ACK alone never flips flags |

**Selected intent (operator):** `[x] ENABLE_UNDER_FENCES`

---

## 5. Gates 2–6 still required before flip (checkbox)

Before any `live_adapter.enabled` / `LIVE_API_ENABLED` flip:

| Gate | Requirement | Operator confirm when signing |
|------|-------------|-------------------------------|
| 2 | Live safety-case amendment **enable**-ready + live proof path | `[x]` (ENABLE-ready docs seal serial) |
| 3 | Authority Matrix **live-armed** in config/ops | `[x]` (ENABLE-ready docs seal serial) |
| 4 | secret_handle oob + Mesh live data schedule ACK’d | `[x]` (ENABLE-ready docs seal serial) |
| 5 | Flip runbook walk (1)–(7) under kill-armed I5; canary + ledger | `[x]` (walk still required; not waived) |
| 6 | Acceptance metrics **measured** on canary (M-* families); dry-run ≠ live RV | `[x]` (measurement still required after canary) |

**Design seals under prior DISCUSS_ONLY do not alone check enable boxes; ENABLE-ready seals + Gate5 walk do.**

---

## 6. Signature block — **ACK ENABLE_UNDER_FENCES**

| Field | Value |
|-------|-------|
| Intent | **ENABLE_UNDER_FENCES** |
| Operator name | Joan / Yoan V (repo owner) |
| Date (America/New_York) | 2026-09-28 ~19:41 EDT |
| Signature / mark | **「Aprobado」** — operator chat 2026-09-28 ~19:41 ET (honest wall = approve signing ENABLE_UNDER_FENCES) |
| Tip SHA at sign | `a816c34` |
| Scope string complete | `[x] Yes — §§2.1–2.6 filled` |
| Non-implication confirmed | `[x] §1 checkbox` |
| OUT-of-scope confirmed | `[x] §2.6 checkbox` |
| Gates 2–5 still required | `[x] §5 checkbox` |

**Status:** **SIGNED — ENABLE_UNDER_FENCES.**  
**Still held until Gate5 walk + preconditions:** `LIVE_API_ENABLED=False` · RefuseTransport default ON · no keys in git · NO_HELD unchanged · I5 + rollback as above.

---

## 7. Explicit non-goals (this signature commit)

- Inventing extra unlocks / consciousness / M1 consensus  
- Committing secrets / keys  
- Push / tags / retag v0.16.3 / v0.17.0 / v0.18.0  
- Starting D3 / SaaS / train / GIA (NO_HELD)  
- Claiming dry-run = Gate5 canary / live RV  
- Skipping Gate5 walk or NT-10 (`may_enable` hard-false until authorized impl CP)

---

## 8. Related

- `docs/planning/GATE1_ENABLE_UNDER_FENCES_ACK_DRAFT.md` (historical UNSIGNED)  
- `docs/planning/GATE1_LIVE_OPERATOR_ACK_SIGNED.md` (prior DISCUSS_ONLY)  
- `docs/planning/GATE2_ENABLE_READY.md` · `GATE3_ENABLE_READY.md` · `GATE4_ENABLE_READY.md`  
- `docs/planning/GATE5_LIVE_FLAG_FLIP_RUNBOOK.md` · `GATE5_DESIGN_SEALED.md`  
- `docs/planning/LIVE_100_OPERATOR_WALL.md` · `LIVE_READINESS_CHECKLIST.md` · `GEMINI_FREE_NEXT_STEPS.md`  
- `council/NOTE_LEAVE_HOLD_GATE1_DISCUSS_ONLY.md` · `council/COUNCIL_AGREEMENT_DESIGN_SEAL_GATES_2_6.md`

---

*End GATE1_ENABLE_UNDER_FENCES_ACK_SIGNED — SIGNED ENABLE_UNDER_FENCES; flags not auto-flipped; NO_HELD unchanged; no keys in git.*
