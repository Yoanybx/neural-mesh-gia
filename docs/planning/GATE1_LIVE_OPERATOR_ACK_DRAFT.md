# Gate 1 — Live operator ACK (DRAFT)

**Status:** **DRAFT — NOT SIGNED**  
**Effect:** This artifact is a **fillable / signable draft** for the operator (Joan / Yoan).  
**It does NOT** enable live · **does NOT** flip `live_adapter.enabled` / `LIVE_API_ENABLED` · **does NOT** mint keys · **does NOT** authorize real provider calls · **does NOT** start D3 · **does NOT** push/tag · **does NOT** mint a CP.

**Date drafted:** 2026-09-27 America/New_York (EDT)  
**Author (draft only):** Grok Bot (Staff Eng — docs only)  
**Tip at draft:** `8c771a7` (Design-only: live readiness checklist) atop Google fenced spike / CP-0074  
**Package posture:** **0.18.0 HELD** · **live=DISABLED** · **M1=NO_CONSENSUS_YET** · **D3 NOT ACKed** · **MESH_PERF_EXPERIMENTAL=OFF** · pkg0190 **NOT_OPENED**

**Checklist / Gate 1 exit:** `docs/planning/LIVE_READINESS_CHECKLIST.md` § Gate 1 — Operator ACK  
**Council note:** `council/NOTE_GATE1_ACK_DRAFT.md`

---

## 0. What this is / is not

| Is | Is not |
|----|--------|
| Fillable Gate 1 draft the operator may edit and later **ACK** | A signed ACK today |
| Record of intent to *discuss* or (later) *enable under fences* | An automatic `enabled=true` flip |
| Scope string the operator must fill before any signature has force | Permission to ship keys, network transports, or real Gemini traffic |
| Compatible with continuing local mock / RefuseTransport work | A claim that D1/D2 sealed or Google tools APPROVE_WITH_FENCES = live-ready |

**Invariant (D4 F3/F4):** flipping live requires a **separate cycle** + **this ACK (signed)** + **safety-case amendment** + Gates **2–5** (and 6 acceptance bundle). This draft alone does **not** pre-authorize that flip.

---

## 1. Explicit non-implication (binding)

The following **do NOT count** as this Gate 1 ACK and **must not** be cited as substitute:

| Prior artifact | Why it is not this ACK |
|----------------|------------------------|
| Google free AI tools **APPROVE_WITH_FENCES** (`council/NOTE_GOOGLE_AI_TOOLS_FENCED.md` §10) | Tool approval ≠ live discussion/enable ACK |
| D4 lock (`council/COUNCIL_AGREEMENT_D4.md` F3/F4) | Governance bookkeeping; F3 design-only; F4 requires separate ACK |
| D1 seal / safety-case maturation (`docs/planning/D1_L_JUDGE_SAFETY_CASE_MATURATION.md`) | Design sealed; not live proof; not live-enable ACK |
| Google / L_judge **mock** peer spike | Mock / RefuseTransport only; no keys; no live |
| Live readiness checklist itself | Ordered gates design; not an unlock |
| Any council cycle ACK / DeepSeek PASS / ChatGPT verdict | Governance alignment ≠ live operator ACK (CG1 / CG3) |

**Operator checkbox (required when signing):**  
- [ ] I confirm none of the above substitute for this Gate 1 ACK.

---

## 2. Scope string (operator must fill / confirm)

Leave blanks until the operator fills them. Unsigned blanks = **no force**.

### 2.1 Provider(s)

| Field | Operator fill |
|-------|---------------|
| Provider class | `[ ] Gemini free-tier eval only` · `[ ] none (discuss fences only)` · `[ ] other: _______________` |
| Paid / Vertex | **Default OUT** — requires separate approval beyond this ACK: `[ ] still OUT` · `[ ] separate approval filed: _______________` |
| Role of provider output | Evidence / evaluation input only — **not** Mesh SoT, consensus, or execution authority: `[ ] confirmed` |

### 2.2 Environment

| Field | Operator fill |
|-------|---------------|
| Environment | `[ ] local box / mock only` · `[ ] other (name): _______________` |
| Network egress for live peer | `[ ] none (discuss only)` · `[ ] canary under kill-armed I5 (after Gates 2–5)` · `[ ] forbidden until filled` |
| Config flags today | `live_adapter.enabled=false` · `LIVE_API_ENABLED=false` · RefuseTransport default **ON** — `[ ] confirmed held` |

### 2.3 Data classes allowed to leave the box

| Class | Allowed? (operator) | Notes |
|-------|---------------------|-------|
| Redacted / synthetic prompts for eval | `[ ] Y / [ ] N` | |
| Digests / evidence refs (no secrets) | `[ ] Y / [ ] N` | |
| Operational Mesh SoT / continuity plaintext | **Default N** — `[ ] N held` | Forbidden unless separate schedule |
| Raw secrets / API keys / Bearer / `sk-` | **Default N** — `[ ] N held` | Never in repo; secret_handle only |
| Unverified continuity / orphan state | **Default N** — `[ ] N held` | |

**Live data schedule:** `[ ] not yet` · `[ ] attached at: _______________` (Gate 4 still required before any real call)

### 2.4 Kill authority (I5)

| Field | Operator fill / confirm |
|-------|-------------------------|
| Kill path | I5 kill → RefuseTransport + continuity **ABORT** + emergency `enabled=false` |
| Kill armed before any canary | `[ ] confirmed` (required for any ENABLE_UNDER_FENCES intent) |
| Authority cite | D1 §3 Authority Matrix · D1 §6 Oversight I5 · D4-A / D4-D |

### 2.5 Rollback owner

| Field | Operator fill |
|-------|---------------|
| Rollback owner | `[ ] Operator (Yoan / Joan)` · `[ ] I5 + Operator quorum (A4)` · `[ ] name: _______________` |
| Verification | RV-1..RV-7 required post-rollback (D1 §8.4) — `[ ] confirmed` |
| Scope | Policy/goal version supersede; in-flight ABORT; audit history append-only — `[ ] confirmed` |

### 2.6 Explicitly OUT of scope (this ACK)

Signing this ACK (when signed) **does not** authorize any of the following. Operator must leave these **OUT**:

| Out of scope | Status |
|--------------|--------|
| pkg0190 / package 0.19.0 open | **OUT** |
| Raft / N>2 topology unlock | **OUT** |
| GIA unlock | **OUT** |
| train 70B / 128B now | **OUT** |
| SaaS migration | **OUT** |
| D3 / `MESH_PERF_EXPERIMENTAL` without **separate** D3 ACK | **OUT** |
| `live=ENABLED` / mesh live adapter flip **without Gates 2–5** (+ Gate 6 bundle) | **OUT** |
| Keys in repo / CI / evidence digests | **OUT** |
| Claiming Gemini/mock dual agree = M1 consensus | **OUT** |

**Operator checkbox:**  
- [ ] I confirm all rows above remain OUT under this ACK.

---

## 3. Authority Matrix summary (cite — do not amend here)

From `docs/planning/D1_L_JUDGE_SAFETY_CASE_MATURATION.md` §3 (D4-A):

| Role | Live-relevant bound |
|------|---------------------|
| **L_judge** | Propose-only (advisory); cannot approve/veto/execute live |
| **Oversight I5** | Approve/deny/pause/**kill**; does not run side-effects alone |
| **RefuseTransport** | Fail-closed veto default until controlled flip |
| **Operator** | **Sole live-enable ACK authority** (F4); final for A3/A4 |

Disagreement: Mesh ABORT > judge ACCEPT; I5 may stop post-advisory; no judge-over-judge override.

---

## 4. Intent (pick one when signing)

| Intent code | Meaning | Still requires Gates 2–5 before any flag flip? |
|-------------|---------|--------------------------------------------------|
| **DISCUSS_ONLY** | Open live *discussion* under named fences; no enable | **Yes** (discussion ≠ enable) |
| **ENABLE_UNDER_FENCES** | Intent to enable later under this scope + Gates 2–5 + safety amendment | **Yes** — this ACK alone never flips flags |

**Selected intent (operator):** `[ ] DISCUSS_ONLY` · `[ ] ENABLE_UNDER_FENCES` · `[ ] unsigned / none`

---

## 5. Gates 2–5 still required (checkbox)

Before any `live_adapter.enabled` / `LIVE_API_ENABLED` flip:

- [ ] **Gate 2** — Live safety-case **amendment** reviewed; mock RV drills green  
- [ ] **Gate 3** — Authority Matrix **in use** (config/policy cites matrix IDs)  
- [ ] **Gate 4** — Keys via secret_handle outside repo + written live data schedule  
- [ ] **Gate 5** — RefuseTransport → live flag runbook + negative tests; canary under kill-armed I5  
- [ ] **Gate 6** (acceptance bundle) attached to the live cycle  

**Operator checkbox (required on signature):**  
- [ ] I understand Gates **2–5** (and Gate 6 bundle) remain required; signing this draft does **not** flip live.

---

## 6. Signature block (UNSIGNED until operator fills)

| Field | Value |
|-------|-------|
| **Operator name** | _________________________________ (Joan / Yoan) |
| **Date** | _______________ America/New_York |
| **Intent** | `[ ] DISCUSS_ONLY` · `[ ] ENABLE_UNDER_FENCES` |
| **Scope string complete** | `[ ] Yes — §§2.1–2.6 filled` |
| **Non-implication confirmed** | `[ ] §1 checkbox` |
| **OUT-of-scope confirmed** | `[ ] §2.6 checkbox` |
| **Gates 2–5 still required** | `[ ] §5 checkbox` |
| **Signature / ACK mark** | _________________________________ |

**Until this block is filled and marked ACK by the operator, status remains: DRAFT — NOT SIGNED.**  
**Posture held:** **live=DISABLED**.

---

## 7. Related

- `docs/planning/LIVE_READINESS_CHECKLIST.md` (Gate 1 exit)
- `council/NOTE_GATE1_ACK_DRAFT.md`
- `council/NOTE_LIVE_READINESS.md`
- `council/COUNCIL_AGREEMENT_D4.md` (F3/F4)
- `docs/planning/D1_L_JUDGE_SAFETY_CASE_MATURATION.md` (Authority Matrix §3)
- `council/NOTE_GOOGLE_AI_TOOLS_FENCED.md` (§10 non-implication)
- `docs/planning/GOOGLE_L_JUDGE_PEER_SPIKE.md`
- `src/neural_mesh/packaging/l_judge_live_adapter_safety.py` (`RefuseTransport`)

---

*End GATE1_LIVE_OPERATOR_ACK_DRAFT — DRAFT NOT SIGNED; not an unlock; live=DISABLED.*
