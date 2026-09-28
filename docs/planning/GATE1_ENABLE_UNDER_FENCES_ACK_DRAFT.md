# Gate 1 — ENABLE_UNDER_FENCES operator ACK — **UNSIGNED DRAFT (HISTORICAL)**

**Status:** **HISTORICAL UNSIGNED DRAFT** — superseded by **SIGNED** artifact  
**Signed copy:** `docs/planning/GATE1_ENABLE_UNDER_FENCES_ACK_SIGNED.md` — operator **「Aprobado」** 2026-09-28 ~19:41 ET  
**Effect (when signed):** Records intent to *enable under fences* (Gemini free-tier canary path after Gates 2–5 enable-ready).  
**This draft file alone does not authorize flips**; use the SIGNED copy as the ACK of record.

**Date drafted:** 2026-09-28 ~18:55 EDT (America/New_York)  
**Author (draft only):** Grok Bot `<grok-bot@local>` — docs only  
**Date signed:** 2026-09-28 ~19:41 EDT — see SIGNED artifact  
**Operator ACK:** Joan / Yoan V — **「Aprobado」** (recorded on SIGNED copy)  
**Tip at draft:** Gate6 DESIGN_SEALED atop `d2c16d8` (Gate5) / Gates 2–4 · peer wire `30fe593` · evidence `1e502c6`  
**Tip at sign:** `a816c34`  
**Package posture at draft:** **0.18.0 HELD** · **LIVE_API_ENABLED=False** · Gate1 was **SIGNED DISCUSS_ONLY** · Gates **2–6 DESIGN_SEALED** · **NO_HELD** stays NO_HELD

**Prior Gate1:** `docs/planning/GATE1_LIVE_OPERATOR_ACK_SIGNED.md` — **DISCUSS_ONLY** (does not substitute for this ENABLE ACK)  
**Checklist:** `docs/planning/LIVE_READINESS_CHECKLIST.md` · wall `docs/planning/LIVE_100_OPERATOR_WALL.md`  
**Metrics (design):** `docs/planning/GATE6_DESIGN_SEALED.md` · runbook `docs/planning/GATE5_DESIGN_SEALED.md`

---

## 0. What this is / is not

| Is | Is not |
|----|--------|
| **Unsigned** draft for intent **ENABLE_UNDER_FENCES** | A signed ACK today |
| Record of *future* enable intent under named fences (when operator signs) | Permission to flip flags, ship keys, or call Mesh live providers **now** |
| Compatible with continuing RefuseTransport / dry-run / design seals | A claim that Gates 2–6 DESIGN_SEALED = enable-ready |
| Explicit: this ACK alone never flips flags | A substitute for Gate5 canary execution or Gate6 live measurement |

**Invariant (D4 F3/F4):** flipping live requires **this ACK (signed by operator)** + Gates **2–5 enable**-ready + safety-case live path + Gate5 canary under kill-armed I5 + Gate6 metrics measured. Design seals under DISCUSS_ONLY do **not** authorize that flip.

---

## 1. Explicit non-implication (binding)

The following **do NOT count** as this ENABLE ACK and **must not** be cited as substitute:

| Prior artifact | Why it is not this ACK |
|----------------|------------------------|
| Gate1 **SIGNED DISCUSS_ONLY** | Discussion ≠ enable intent |
| Gates **2–6 DESIGN_SEALED** (discuss/eval) | Design seals ≠ ENABLE seals / live proof |
| Dry-run peer `30fe593` / evidence `1e502c6` | Eval dry-run = evidence-only ≠ live RV / ≠ canary |
| Google free AI tools APPROVE_WITH_FENCES | Tool approval ≠ ENABLE ACK |
| D4 lock / D1 seal / council PASS | Governance ≠ operator ENABLE ACK |
| This draft itself while **UNSIGNED** | Draft ≠ signature |

**Operator checkbox (required when signing):**  
- [ ] I confirm none of the above substitute for this ENABLE_UNDER_FENCES ACK.

---

## 2. Scope string (operator fills when signing)

### 2.1 Provider(s)

| Field | Operator fill |
|-------|---------------|
| Provider class | `[ ] Gemini free-tier canary only` · `[ ] other: _______________` |
| Paid / Vertex | **OUT** unless separate approval — `[ ] still OUT` · `[ ] separate approval filed: _______________` |
| Role of provider output | Evidence / evaluation input only — **not** Mesh SoT, consensus, or execution authority: `[ ] confirmed` |

### 2.2 Environment

| Field | Operator fill |
|-------|---------------|
| Environment | `[ ] local box / canary` · `[ ] other (name): _______________` |
| Network egress for live peer | `[ ] single canary under kill-armed I5 (after Gates 2–5 enable-ready)` · `[ ] forbidden until filled` |
| Config flags before canary | `live_adapter.enabled=false` · `LIVE_API_ENABLED=false` · RefuseTransport default **ON** until Gate5 walk — `[ ] confirmed held until walk` |

### 2.3 Data classes allowed to leave the box (canary)

| Class | Allowed? (operator) | Notes |
|-------|---------------------|-------|
| Redacted / synthetic prompts for canary | `[ ] Y` · `[ ] N` | Per Gate4 schedule |
| Digests / evidence refs (no secrets) | `[ ] Y` · `[ ] N` | |
| Operational Mesh SoT / continuity plaintext | **N held** unless separate schedule — `[ ] N held` | |
| Raw secrets / API keys / Bearer / `sk-` | **N held** — secret_handle oob only — `[ ] N held` | |
| Unverified continuity / orphan state | **N held** — `[ ] N held` | |

**Live data schedule cite:** `[ ] Gate4 ENABLE path ACK’d at: _______________`

### 2.4 Kill authority (I5)

| Field | Operator fill / confirm |
|-------|-------------------------|
| Kill path | I5 kill → RefuseTransport + continuity **ABORT** + emergency `enabled=false` |
| Kill armed before any canary | `[ ] confirmed` |
| Authority cite | D1 §3 Authority Matrix · D1 §6 Oversight I5 · Gate5 runbook · Gate3 binding |

### 2.5 Rollback owner

| Field | Operator fill |
|-------|---------------|
| Rollback owner | `[ ] Operator (Yoan / Joan)` · `[ ] I5 + Operator quorum (A4)` · `[ ] name: _______________` |
| Verification | RV-1..RV-7 required post-rollback (D1 §8.4) — `[ ] confirmed` |
| Scope | Revert `enabled=false` + RefuseTransport; re-enable requires re-walk Gate5 (1)–(7) — `[ ] confirmed` |

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

**Operator checkbox:**  
- [ ] I confirm all rows above remain OUT under this ACK.

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

## 4. Intent (selected when signing)

| Intent code | Meaning | Still requires Gates 2–5 enable-ready before any flag flip? |
|-------------|---------|--------------------------------------------------------------|
| **DISCUSS_ONLY** | (prior Gate1) Open discussion; no enable | Yes — already signed separately |
| **ENABLE_UNDER_FENCES** | Intent to enable later under this scope + Gates 2–5 enable + safety live path + canary | **Yes** — this ACK alone never flips flags |

**Selected intent (operator when signing):** `[ ] ENABLE_UNDER_FENCES` · `[ ] leave unsigned / none`

---

## 5. Gates 2–6 still required before flip (checkbox)

Before any `live_adapter.enabled` / `LIVE_API_ENABLED` flip:

| Gate | Requirement | Operator confirm when signing |
|------|-------------|-------------------------------|
| 2 | Live safety-case amendment **enable**-ready + live proof path | `[ ]` |
| 3 | Authority Matrix **live-armed** in config/ops | `[ ]` |
| 4 | secret_handle oob + Mesh live data schedule ACK’d | `[ ]` |
| 5 | Flip runbook walk (1)–(7) under kill-armed I5; canary + ledger | `[ ]` |
| 6 | Acceptance metrics **measured** on canary (M-* families); dry-run ≠ live RV | `[ ]` |

**Design seals today (DISCUSS_ONLY) do not check these boxes.**

---

## 6. Signature block (operator only — leave blank until ready)

| Field | Value |
|-------|-------|
| Intent | **ENABLE_UNDER_FENCES** |
| Operator name | _______________________________ |
| Date (America/New_York) | _______________________________ |
| Signature / mark | _______________________________ |
| Tip SHA at sign | _______________________________ |

**UNSIGNED.** Do not treat draft as signed. Do not invent signature.

---

## 7. Explicit non-goals (this draft)

- Inventing or backdating a signature  
- Flipping `LIVE_API_ENABLED` / `live_adapter.enabled`  
- Executing Gate5 canary in this docs cycle  
- Claiming Gates 2–6 DESIGN_SEALED = ENABLE seals  
- Claiming dry-run metrics as live RV  
- Push / tags / secrets / D3 / NO_HELD unlocks

---

## 8. Related

- `docs/planning/GATE1_LIVE_OPERATOR_ACK_SIGNED.md` (DISCUSS_ONLY prior)
- `docs/planning/GATE5_DESIGN_SEALED.md` · `GATE5_LIVE_FLAG_FLIP_RUNBOOK.md`
- `docs/planning/GATE6_DESIGN_SEALED.md` · `GATE6_LIVE_ACCEPTANCE_METRICS.md`
- `docs/planning/LIVE_100_OPERATOR_WALL.md` · `LIVE_READINESS_CHECKLIST.md` · `GEMINI_FREE_NEXT_STEPS.md`
- `council/NOTE_GATE6_DESIGN_SEALED.md` · `council/PASTE_DEEPSEEK_STATUS_GATE6_DESIGN_SEALED.md`

---

*End GATE1_ENABLE_UNDER_FENCES_ACK_DRAFT — HISTORICAL; see GATE1_ENABLE_UNDER_FENCES_ACK_SIGNED.md.*
