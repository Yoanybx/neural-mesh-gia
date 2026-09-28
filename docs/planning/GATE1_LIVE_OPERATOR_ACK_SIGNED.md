# Gate 1 — Live operator ACK — **SIGNED DISCUSS_ONLY**

**Status:** **SIGNED — DISCUSS_ONLY** (not enable)  
**Filename note:** Canonical signed copy. In-place draft path `docs/planning/GATE1_LIVE_OPERATOR_ACK_DRAFT.md` carries the same SIGNED DISCUSS_ONLY content for history.  
**Effect:** Opens live *discussion* under named fences (Gemini free-tier eval only).  
**It does NOT** enable live · **does NOT** flip `live_adapter.enabled` / `LIVE_API_ENABLED` · **does NOT** mint keys · **does NOT** authorize real provider calls · **does NOT** start D3 · **does NOT** push/tag · **does NOT** mint a CP.

**Date drafted:** 2026-09-27 America/New_York (EDT)  
**Date signed:** 2026-09-28 America/New_York (EDT)  
**Author (draft):** Grok Bot (Staff Eng — docs only)  
**Operator ACK:** Joan Alberto Barrios Cruz / Yoan V (operator ACK in chat 2026-09-28) — leave Hold; sign Gate1 **DISCUSS_ONLY**  
**Tip at sign:** ~`9348651` (HOLD_STAY locked)  
**Package posture:** **0.18.0 HELD** · **Hold A LEFT** (operator override 2026-09-28) · **live=DISABLED** (flags held false) · **Gate1 SIGNED DISCUSS_ONLY** · **M1=NO_CONSENSUS_YET** · **D3 NOT ACKed** · **MESH_PERF_EXPERIMENTAL=OFF** · pkg0190 **NOT_OPENED**  
**Hold hygiene:** wall `docs/planning/LIVE_100_OPERATOR_WALL.md` · checklist `docs/planning/LIVE_READINESS_CHECKLIST.md` · leave-Hold note `council/NOTE_LEAVE_HOLD_GATE1_DISCUSS_ONLY.md`

**Checklist / Gate 1 exit:** `docs/planning/LIVE_READINESS_CHECKLIST.md` § Gate 1 — Operator ACK  
**Council notes:** `council/NOTE_GATE1_ACK_DRAFT.md` · `council/NOTE_LEAVE_HOLD_GATE1_DISCUSS_ONLY.md`

---

## 0. What this is / is not

| Is | Is not |
|----|--------|
| **Signed** Gate 1 ACK with intent **DISCUSS_ONLY** | An enable / `enabled=true` flip |
| Record of intent to *discuss* Gemini free-tier eval under fences | Permission to ship keys, network transports, or real Gemini traffic |
| Scope string filled for Gemini free-tier eval only; Vertex paid **OUT** | Authorization for Gates 2–5 seal or Gate5 canary |
| Compatible with continuing local mock / RefuseTransport work | A claim that D1/D2 sealed or Google tools APPROVE_WITH_FENCES = live-ready |

**Invariant (D4 F3/F4):** flipping live requires a **separate cycle** + **this ACK (signed)** + **safety-case amendment** + Gates **2–5** (and 6 acceptance bundle). This ACK alone does **not** authorize that flip. Intent = **DISCUSS_ONLY**.

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
| Prior **HOLD_STAY** council consensus | Superseded for *discussion reopen* by this operator override; does **not** substitute for this ACK |

**Operator checkbox (required when signing):**  
- [x] I confirm none of the above substitute for this Gate 1 ACK.

---

## 2. Scope string (operator filled / confirmed)

### 2.1 Provider(s)

| Field | Operator fill |
|-------|---------------|
| Provider class | `[x] Gemini free-tier eval only` · `[ ] none (discuss fences only)` · `[ ] other: _______________` |
| Paid / Vertex | **OUT** — `[x] still OUT` · `[ ] separate approval filed: _______________` |
| Role of provider output | Evidence / evaluation input only — **not** Mesh SoT, consensus, or execution authority: `[x] confirmed` |

### 2.2 Environment

| Field | Operator fill |
|-------|---------------|
| Environment | `[x] local box / discuss` · `[ ] other (name): _______________` |
| Network egress for live peer | `[x] none (discuss only)` · `[ ] canary under kill-armed I5 (after Gates 2–5)` · `[ ] forbidden until filled` — **none until Gates 2–5** |
| Config flags today | `live_adapter.enabled=false` · `LIVE_API_ENABLED=false` · RefuseTransport default **ON** — `[x] confirmed held` |

### 2.3 Data classes allowed to leave the box

| Class | Allowed? (operator) | Notes |
|-------|---------------------|-------|
| Redacted / synthetic prompts for eval | `[x] Y` | Discuss/design only; no real call in this commit |
| Digests / evidence refs (no secrets) | `[x] Y` | |
| Operational Mesh SoT / continuity plaintext | **N held** — `[x] N held` | Forbidden unless separate schedule |
| Raw secrets / API keys / Bearer / `sk-` | **N held** — `[x] N held` | Never in repo; secret_handle only (Gate4, outside repo) |
| Unverified continuity / orphan state | **N held** — `[x] N held` | |

**Live data schedule:** `[x] not yet` · `[ ] attached at: _______________` (Gate 4 still required before any real call)

### 2.4 Kill authority (I5)

| Field | Operator fill / confirm |
|-------|-------------------------|
| Kill path | I5 kill → RefuseTransport + continuity **ABORT** + emergency `enabled=false` |
| Kill armed before any canary | `[x] confirmed` (I5 confirmed; canary still Gates 2–5 later — not this ACK) |
| Authority cite | D1 §3 Authority Matrix · D1 §6 Oversight I5 · D4-A / D4-D |

### 2.5 Rollback owner

| Field | Operator fill |
|-------|---------------|
| Rollback owner | `[x] Operator (Yoan / Joan)` · `[ ] I5 + Operator quorum (A4)` · `[ ] name: _______________` |
| Verification | RV-1..RV-7 required post-rollback (D1 §8.4) — `[x] confirmed` |
| Scope | Policy/goal version supersede; in-flight ABORT; audit history append-only — `[x] confirmed` |

### 2.6 Explicitly OUT of scope (this ACK)

Signing this ACK **does not** authorize any of the following. Operator leaves these **OUT**:

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
| Real API calls in this commit / until Gates 2–5 | **OUT** |

**Operator checkbox:**  
- [x] I confirm all rows above remain OUT under this ACK.

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

## 4. Intent (selected)

| Intent code | Meaning | Still requires Gates 2–5 before any flag flip? |
|-------------|---------|--------------------------------------------------|
| **DISCUSS_ONLY** | Open live *discussion* under named fences; no enable | **Yes** (discussion ≠ enable) |
| **ENABLE_UNDER_FENCES** | Intent to enable later under this scope + Gates 2–5 + safety amendment | **Yes** — this ACK alone never flips flags |

**Selected intent (operator):** `[x] DISCUSS_ONLY` · `[ ] ENABLE_UNDER_FENCES` · `[ ] unsigned / none`

---

## 5. Gates 2–5 still required (checkbox)

Before any `live_adapter.enabled` / `LIVE_API_ENABLED` flip:

- [ ] **Gate 2** — Live safety-case **amendment** reviewed; mock RV drills green  
- [ ] **Gate 3** — Authority Matrix **in use** (config/policy cites matrix IDs)  
- [ ] **Gate 4** — Keys via secret_handle outside repo + written live data schedule  
- [ ] **Gate 5** — RefuseTransport → live flag runbook + negative tests; canary under kill-armed I5  
- [ ] **Gate 6** (acceptance bundle) attached to the live cycle  

**Operator checkbox (required on signature):**  
- [x] I understand Gates **2–5** (and Gate 6 bundle) remain required; signing this draft does **not** flip live.

---

## 6. Signature block — **ACK DISCUSS_ONLY**

| Field | Value |
|-------|-------|
| **Operator name** | Joan Alberto Barrios Cruz / Yoan V |
| **Date** | 2026-09-28 America/New_York (EDT) |
| **Intent** | `[x] DISCUSS_ONLY` · `[ ] ENABLE_UNDER_FENCES` |
| **Scope string complete** | `[x] Yes — §§2.1–2.6 filled` |
| **Non-implication confirmed** | `[x] §1 checkbox` |
| **OUT-of-scope confirmed** | `[x] §2.6 checkbox` |
| **Gates 2–5 still required** | `[x] §5 checkbox` |
| **Signature / ACK mark** | **ACK DISCUSS_ONLY** — operator YES in chat 2026-09-28 (leave Hold; Gemini free-tier eval only; no live enable) |

**Status:** **SIGNED — DISCUSS_ONLY.**  
**Posture held:** **live=DISABLED** (flags `live=false` held; network egress none until Gates 2–5; no keys in repo; no real API calls in this commit).

---

## 7. Related

- `docs/planning/GATE1_LIVE_OPERATOR_ACK_SIGNED.md` (signed copy)
- `docs/planning/GEMINI_FREE_NEXT_STEPS.md`
- `council/NOTE_LEAVE_HOLD_GATE1_DISCUSS_ONLY.md`
- `docs/planning/LIVE_READINESS_CHECKLIST.md` (Gate 1 exit)
- `docs/planning/LIVE_100_OPERATOR_WALL.md`
- `council/HOLD_POSTURE_AND_REOPEN_CONDITIONS.md`
- `council/COUNCIL_AGREEMENT_HOLD_STAY.md` (prior; operator superseded for discussion reopen)
- `docs/planning/HOLD_MOCK_NEXT.md` · `council/NOTE_OPERATOR_HOLD_POST_WALL.md` · `council/NOTE_HOLD_MOCK_ROADMAP_COMPLETE.md`
- `council/NOTE_GATE1_ACK_DRAFT.md`
- `council/NOTE_LIVE_READINESS.md`
- `council/COUNCIL_AGREEMENT_D4.md` (F3/F4)
- `docs/planning/D1_L_JUDGE_SAFETY_CASE_MATURATION.md` (Authority Matrix §3)
- `council/NOTE_GOOGLE_AI_TOOLS_FENCED.md` (§10 non-implication)
- `docs/planning/GOOGLE_L_JUDGE_PEER_SPIKE.md`
- `src/neural_mesh/packaging/l_judge_live_adapter_safety.py` (`RefuseTransport`)

---

*End GATE1_LIVE_OPERATOR_ACK — SIGNED DISCUSS_ONLY; not an unlock; live=DISABLED.*
