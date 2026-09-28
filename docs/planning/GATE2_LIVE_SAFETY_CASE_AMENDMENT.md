# Gate 2 — Live safety-case amendment (**DESIGN_SEALED** / DISCUSS_ONLY)

**Status:** **DESIGN_SEALED** for Gate1 **DISCUSS_ONLY** / Gemini free-tier **eval** path — does **not** enable live · **does not** mint keys into git · **does not** authorize Mesh live adapter · **does not** start D3 · **does not** push/tag · **does not** mint a CP · **does not** execute RV drills under Mesh live transport · **is not ENABLE seal** · **is not live proof for flag flip**.  
**Date drafted:** 2026-09-28 America/New_York (EDT)  
**Date design-sealed:** 2026-09-28 ~18:43 EDT  
**Author (docs):** Grok Bot `<grok-bot@local>` — design seal only; **did not invent operator ENABLE signature**  
**Tip at design seal:** `30fe593` (peer dry-run wire) atop evidence `1e502c6` / leave-Hold `fc4ef9e` / prior draft stack Gate5 `45ccc16`  
**Package posture:** **0.18.0 HELD** · **live=DISABLED** · **LIVE_API_ENABLED=False** · **M1=NO_CONSENSUS_YET** · **D3 NOT ACKed** · **MESH_PERF_EXPERIMENTAL=OFF** · pkg0190 **NOT_OPENED** · **Gate1 SIGNED DISCUSS_ONLY** · Gate2 **DESIGN_SEALED (discuss/eval)** · Gates **3–6 not sealed for enable** · **NO_HELD** stays NO_HELD

**Design-seal artifact:** `docs/planning/GATE2_DESIGN_SEALED.md`  
**Checklist / Gate 2 exit:** `docs/planning/LIVE_READINESS_CHECKLIST.md` § Gate 2 — Safety evidence (D1 / D4-H)  
**Council note:** `council/NOTE_GATE2_SAFETY_AMENDMENT.md` · `council/NOTE_GATE2_DESIGN_SEALED.md`  
**Upstream:** D4 F4 (`council/COUNCIL_AGREEMENT_D4.md`) · `council/D4_CHATGPT_FINDINGS.md` (D4-A..K) · `docs/planning/D1_L_JUDGE_SAFETY_CASE_MATURATION.md` (CP-0071) · CP-0058 RefuseTransport · Gate1 **SIGNED** DISCUSS_ONLY · Gate3 Authority Matrix · Gate4 secret_handle · Gate5 flip runbook · Gemini dry-run evidence + peer wire

---

## 0. What this is / is not

| Is | Is not |
|----|--------|
| **Design amendment** to the D1 safety case for a *future* real-transport path (blast radius, keys, kill, continuity, evidence gaps) | Permission to ship keys, network transports, or real Gemini traffic |
| Answer to Gate 2 “Live amendment” row + D4 F4 “safety-case amendment” | An **ENABLE** seal or Mesh **live proof** / flag flip |
| Compatible with mock / RefuseTransport / Google free-tier **eval dry-run** (bound) | An unlock, ENABLE ACK substitute, or `live=ENABLED` flip |
| **DESIGN_SEALED** for DISCUSS_ONLY / eval path (`GATE2_DESIGN_SEALED.md`) | A claim that design seal = ENABLE_UNDER_FENCES or Gate5 canary |

**Invariant (D4 F4):** `live=ENABLED` requires a **separate cycle** + **separate operator ACK** (intent **ENABLE_UNDER_FENCES**, user-written) + **this amendment reviewed** + Gates **1–6** satisfaction for enable. Gate1 is **SIGNED DISCUSS_ONLY** → Gate2 **DESIGN_SEALED** for discuss/eval is honest. **ENABLE seal** still requires operator ENABLE ACK + live-path evidence this amendment only *names* (not claims). **Do not invent operator signature.**

**Today (2026-09-28 ~18:43 EDT):** live=DISABLED · RefuseTransport default ON · `LIVE_API_ENABLED=false` · `live_adapter.enabled=false` · secret_handle **out-of-band** (eval) · Gemini **eval dry-run** done (not Mesh live) · **this amendment NOT executed as Mesh live proof** · RV drills remain **mock-green** for Mesh live · Gate2 **DESIGN_SEALED** (discuss/eval only).

---

## 1. Authority citations (must hold)

| ID / fence | Role in this amendment |
|------------|------------------------|
| **D4-A** | Authority Matrix unchanged: L_judge propose-only; I5 approve/veto/kill; Operator sole live-enable ACK; RefuseTransport veto |
| **D4-B** | Consensus still **NO_CONSENSUS_YET**; live peer advisory ≠ protocol consensus; dual agree ≠ unlock |
| **D4-C** | Continuity preserves **verified** Mesh state only; live peer failure must not launder unverified state |
| **D4-D** | I5 kill / emergency stop → RefuseTransport + continuity ABORT; watch ≠ control |
| **D4-E / J / K** | Acceptance / signoff before live *discussion* stay governance checklists — not live enable |
| **D4-F** | Claim hygiene: design amendment ≠ live readiness proof |
| **D4-G** | Compromise response / failure classes apply to real-transport path |
| **D4-H** | Containment + rollback + **RV-1..RV-7** remain binding; live path needs amended blast radius |
| **D4-I** | Evidence chain / explainability: no secrets in explain; digests + handle ids only |
| **F3 / F4** | Design-only; live=ENABLED = separate cycle + ACK + amendment |
| **RefuseTransport** | Fail-closed default until controlled Gate 5 flip under kill-armed I5 |
| **I5 kill** | Quorum for A4; RefuseTransport; continuity ABORTED; emergency `enabled=false` |

---

## 1b. Bound eval evidence (DISCUSS_ONLY — not Mesh live)

| Artifact | Tip / path | Role under Gate2 design seal |
|----------|------------|------------------------------|
| Gate1 SIGNED DISCUSS_ONLY | `GATE1_LIVE_OPERATOR_ACK_SIGNED.md` | Serial prerequisite met for **discuss/eval** design seal |
| Gemini free dry-run evidence | `GEMINI_DRY_RUN_EVIDENCE.md` (base ~`fc4ef9e`→`1e502c6`) | HTTP 200; marker `MESH_DRY_RUN_OK`; model `gemini-flash-latest`; **no secrets in evidence** |
| Peer dry-run wire | tip `30fe593` · `council/NOTE_GEMINI_PEER_DRY_RUN_WIRE.md` | `GeminiFreeDryRunTransport` flag-gated; default mock/no-network; Mesh live slot → RefuseTransport |
| Authority Matrix | `GATE3_AUTHORITY_MATRIX_BINDING.md` AM-* | Cite-only; L_judge propose-only; Operator sole live-enable ACK; `AM-REFUSE` |
| RefuseTransport | `l_judge_live_adapter_safety.py` / CP-0058 | Fail-closed default **in force**; `live_adapter.enabled` must stay false |
| secret_handle (eval) | `mesh://secrets/judge/gemini-free@v1` @ `/home/box/.config/neural-mesh/gemini.env` | Outside repo; `.gitignore` covers; revoke path in Gate4 § / amendment §3 |

**Not claimed:** dry-run or peer wire = Gate5 canary, Mesh live adapter enable, or RV live-green.

## 2. Real transport blast radius (design amendment)

D1 §8.2 containment assumed mock / RefuseTransport. For any *future* real transport, blast radius is amended as follows (**design only**):

| Bound | Design rule under live path | Rationale |
|-------|-----------------------------|-----------|
| **Default slot** | Every live peer slot defaults to `RefuseTransport` → `ENGINE_DISABLED` / `PEER_LIVE_DISABLED` until Gate 5 step (6) | CP-0058; Gate5 NT-1 |
| **Canary scope** | **One** canary call only; rate floors; redacted/synthetic prompt only | Gate5 step (6); no fan-out |
| **Continuity slice** | Single `continuity_id` / `goal_id`; no cross-goal fan-out by default | D1 §8.2 |
| **Egress classes** | Only Gate4 **allowed** classes; Mesh SoT / raw secrets / unverified continuity **forbidden** | Gate4 §1 |
| **Provider bounds** | Free-tier Gemini (if ever) = evaluation evidence only; Vertex paid needs **separate** approval | Google fences; Gate4 |
| **Partial enable** | **Forbidden** — one slot live + others unset → abort → full RefuseTransport | Gate5 NT-9 |
| **Advisory ≠ SoT** | Live peer digests are evaluation evidence only — never Mesh SoT, M1 consensus, or execute authority | D4-A / D4-B / Gate1 |
| **Network on miss** | Any missing Gate 1–4 / failed Gate 2 review / anomaly → **zero** network | Gate5 NT-5; fail-closed |

**Not claimed today:** that these bounds have been exercised under real transport. They are **design fences** for a future canary cycle.

---

## 3. Key compromise response (design amendment)

Composes D1 §7.2 / §7.4 / §8 + Gate4 secret_handle revoke. Under suspected key/handle compromise (**design path — not executed**):

| Step | Actor | Action | Evidence |
|------|-------|--------|----------|
| 1 | I5 / Operator | **kill** (A4 quorum if required) | `oversight` + `abort` ledger kinds |
| 2 | Safety gate | Bind peer slots to **RefuseTransport**; force `live_adapter.enabled=false` / `LIVE_API_ENABLED=false` | Health `{binding: "RefuseTransport", live: False}` |
| 3 | Gate4 | **revoke** secret_handle → unresolved → any enabled path ABORT `ENGINE_AUTH` | Revoke record; handle id only (never raw) |
| 4 | Continuity | Quarantine continuity slice; forbid resume-as-verified until operator clear | D1 §5.3 / §8.2 |
| 5 | Forensics | Freeze evidence-chain digests; **no** secret material in capture | D1 §8.2; D4-I |
| 6 | Rollback | Operator/I5 rollback if policy/goal version tainted; then **RV-1..RV-7** | D1 §8.3–§8.4 |

**Never:** leave a half-enabled transport after compromise indicators; re-use revoked handle; put raw keys in repo/CI/explain.

---

## 4. Kill → RefuseTransport + ABORT (binding; live-amended wording)

I5 kill path remains the default emergency control. For live-path *discussion*, the binding chain is:

```text
I5 kill (A4 quorum if required)
  → RefuseTransport on all live peer slots
  → continuity ABORT / QUARANTINED (no silent ACTIVE)
  → emergency enabled=false / LIVE_API_ENABLED=false
  → refuse further routes / canaries
  → ledger: oversight + abort (+ forensic digests, no secrets)
```

| Property | Rule |
|----------|------|
| Mesh ABORT beats judge ACCEPT | Unchanged (D1 §3) |
| Kill mid-canary | Immediate RefuseTransport + ABORT + `enabled=false` (Gate5 NT-6) |
| Post-kill resume | Re-gate A3/A4; re-walk Gate5 (1)–(7) if live re-enable ever considered |
| Operator force-disable | Always allowed; matrix does not pre-authorize re-enable |

**Today:** kill path is **binding in design**; **not** live-armed (no live transport to kill).

---

## 5. Continuity under live peer failure (design amendment)

Extends D1 §5 (D4-C) for real-transport peer failure modes (**mock posture holds today**):

| Failure | Continuity action | Must not |
|---------|-------------------|----------|
| Live peer timeout / unavailable | Prefer ABORT / BLOCKED / FALLBACK per policy; **never invent ACCEPT** | Count missing peer as silent agree |
| Live peer returns contradictory advisory | Record both digests; ABORT `ABORT_MISMATCH` or escalate I5 | Auto-pick-winner / majority as execute auth |
| Live path attempted while live=DISABLED | ABORT `CONT_LIVE_DISABLED` | Treat as soft success |
| Peer LEFT / dual_primary ≠ 0 mid-flight | Orphan ABORT / FENCE; dual_primary must return 0 | Resume as ACTIVE |
| Provider error / auth fail (`ENGINE_AUTH`) | Fail-closed; keep RefuseTransport if flags false | Retry with raw key in logs |
| Kill / deny during live canary | Continuity ABORTED; quarantine slice | Preserve unverified “almost-APPROVE” as SoT |
| Provenance gap after peer reply | Refuse resume-as-verified; refuse EXEC_AUTHORIZED | Close audit with missing kinds |

**Recovery authority:** Continuity rehydrates from Mesh registry+ledger only after re-validation. L_judge / live peer **never** recovers authority (D1 §5.4).

---

## 6. What D1 design proves vs what live still needs

### 6.1 What D1 (CP-0071) design proves / seals

| Artifact | Status |
|----------|--------|
| D4-A..K cited in evidence-bundle outline | Design sealed |
| Authority Matrix frozen (propose/approve/veto/execute) | Design |
| Consensus status explicit: **NO_CONSENSUS_YET** | Design |
| Continuity = verified state only + invalidation rules | Design |
| I5 bounds + kill → RefuseTransport + ABORT | Design |
| Containment + rollback contract + **RV-1..RV-7 specified** | Design |
| Evidence / explainability / claim hygiene | Design |
| D1-exit acceptance categories (mock) | Design |
| live=DISABLED / must-stay-false held through D1 | Binding posture |

### 6.2 What live still needs as evidence (OPEN — not claimed by this amendment)

| Gap | Needed before any live *enable* claim | Notes |
|-----|----------------------------------------|-------|
| **Gate 1 ENABLE ACK** | Intent **ENABLE_UNDER_FENCES** (user-written) with provider/env/data/kill/rollback | Gate1 is **DISCUSS_ONLY** only — ENABLE **OPEN** |
| **This amendment ENABLE-sealed** | Operator review of §§2–5 under ENABLE ACK + live proof | **DESIGN_SEALED** for discuss/eval; ENABLE seal **OPEN** |
| **Live-path RV cycle** | RV-1..RV-7 under real transport + rollback drill with live flags momentarily considered then forced false | Today mock-only |
| **Matrix-bound live config** | Gate 3: runtime cites matrix IDs + policy_version | Design OK; live binding OPEN |
| **Keys/data schedule sealed** | Gate 4 for ACK’d env; handles outside repo; no raw keys | Schedule drafted; cannot seal |
| **Controlled canary evidence** | Gate 5 steps (5)–(7) under kill-armed I5 + ledger digests | Runbook drafted; **NOT executed** |
| **Acceptance bundle** | Gate 6 metrics attached to ACK cycle | Design OK; live bundle OPEN |
| **No silent codec / no partial enable** | Negative tests still green under refuse-default | Binding; prove again before flip |

**Claim hygiene (D4-F):** “DESIGN_SEALED (discuss/eval)” ≠ “ENABLE seal” ≠ “live ready” ≠ “RV live-green”.

---

## 7. RV drills — mock-green until live cycle

| Check ID | Verification (D1 §8.4) | Today | Live cycle still needs |
|----------|------------------------|-------|------------------------|
| **RV-1** | Evidence chain hash-verifies after compensating entries | Mock-green (design/tests) | Re-prove after live canary / rollback with real transport digests |
| **RV-2** | Active `policy_version` matches rollback target | Mock-green | Same under ACK’d live policy id |
| **RV-3** | Continuity state ∈ allowed post-rollback set | Mock-green | Incl. live-peer orphan / quarantine cases (§5) |
| **RV-4** | dual_primary == 0; **live flags still false** | Mock-green; flags **false** | Post-canary must restore flags false + dual_primary 0 |
| **RV-5** | Oversight gates re-armed | Mock-green | Re-arm after kill/canary; revoke stale APPROVE |
| **RV-6** | Idempotency store consistent | Mock-green | No double-invoke of rolled-back live act |
| **RV-7** | Operator-visible explain: why rolled back / what restored | Mock-green | Explain must cover transport/kill/compromise without secrets |

**Exit rule — DESIGN_SEALED (met):** amendment reviewed for DISCUSS_ONLY/eval **and** mock RV-1..RV-7 still green **and** Gate1 SIGNED DISCUSS_ONLY **and** dry-run + peer wire + RefuseTransport + secret_handle + Authority Matrix **bound** — still **not** Mesh live proof.  

**Exit rule — ENABLE seal (future):** requires ENABLE_UNDER_FENCES operator ACK + live RV under Gate 5 canary + rollback — **not** this design seal.

---

## 8. Explicit NOT executed / not live proof

| Claim | Status today |
|-------|--------------|
| This file enables live / flips flags | **FALSE** — must stay false |
| This file is Gate 2 **ENABLE** seal | **FALSE** — DESIGN_SEALED for discuss/eval only; ENABLE needs operator ACK |
| This file is Gate 2 **design** seal (DISCUSS_ONLY) | **TRUE** — see `GATE2_DESIGN_SEALED.md` |
| RV-1..RV-7 proven under Mesh live transport | **FALSE** — mock-green only; eval dry-run ≠ live RV |
| Keys in git / D3 started / Mesh live on | **FALSE** — not done |
| Gemini free eval dry-run / peer wire | **DONE (eval)** — tips `1e502c6` / `30fe593`; not Mesh live |
| Push / tags / CP mint for this amendment | **FALSE** — docs-only |
| D1 design = live readiness | **FALSE** — F3/F4; §6.2 enable gaps remain |
| Partial enable of peer slots | **FORBIDDEN** |

**Bottom line:** Gate 2 live safety-case amendment is **DESIGN_SEALED** for DISCUSS_ONLY / Gemini free-tier eval. Mesh live proof, ENABLE seal, and flag flip remain **OPEN**. Posture: **live=DISABLED**.

---

## 9. Related

- `docs/planning/LIVE_READINESS_CHECKLIST.md` (Gate 2)
- `docs/planning/LIVE_100_OPERATOR_WALL.md` — operator wall; live track **FROZEN** under HOLD (A)
- `docs/planning/HOLD_MOCK_NEXT.md` · `council/NOTE_OPERATOR_HOLD_POST_WALL.md` · `council/NOTE_HOLD_MOCK_ROADMAP_COMPLETE.md`
- `council/NOTE_GATE2_SAFETY_AMENDMENT.md`
- `docs/planning/D1_L_JUDGE_SAFETY_CASE_MATURATION.md` (CP-0071; D4-A..K; RV-1..RV-7; I5 kill)
- `council/COUNCIL_AGREEMENT_D4.md` (F4)
- `council/D4_CHATGPT_FINDINGS.md`
- `docs/design/L_JUDGE_LIVE_ADAPTER_SAFETY_CASE.md` (CP-0058 RefuseTransport)
- `docs/planning/GATE2_DESIGN_SEALED.md` · `council/NOTE_GATE2_DESIGN_SEALED.md`
- `docs/planning/GATE1_LIVE_OPERATOR_ACK_SIGNED.md` · `GATE1_LIVE_OPERATOR_ACK_DRAFT.md` · `council/NOTE_LEAVE_HOLD_GATE1_DISCUSS_ONLY.md`
- `docs/planning/GEMINI_FREE_NEXT_STEPS.md` · `GEMINI_DRY_RUN_EVIDENCE.md` · `council/NOTE_GEMINI_PEER_DRY_RUN_WIRE.md`
- `docs/planning/GATE3_AUTHORITY_MATRIX_BINDING.md` · `council/NOTE_GATE3_AUTHORITY_MATRIX.md`
- `docs/planning/GATE4_LIVE_DATA_POLICY.md` · `council/NOTE_GATE4_DATA_POLICY.md`
- `docs/planning/GATE5_LIVE_FLAG_FLIP_RUNBOOK.md` · `council/NOTE_GATE5_FLIP_RUNBOOK.md`
- `docs/planning/GOOGLE_L_JUDGE_PEER_SPIKE.md`
- `src/neural_mesh/packaging/l_judge_live_adapter_safety.py` (`RefuseTransport`)

---

*End GATE2_LIVE_SAFETY_CASE_AMENDMENT — DESIGN_SEALED for DISCUSS_ONLY/eval; NOT Mesh live proof; ENABLE seal OPEN; live=DISABLED.*
