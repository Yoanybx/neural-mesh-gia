# Gate 6 — DESIGN_SEALED (DISCUSS_ONLY / Gemini free-tier eval path — metrics only)

**Status:** **DESIGN_SEALED** for Gate1 **DISCUSS_ONLY** / Gemini **free-tier eval** — acceptance **metrics bundle** (docs only)  
**Not:** live **measurement** · **not** canary evidence · **not** `live=ENABLED` · **not** Mesh live adapter on · **not** flag flip · **not** ENABLE seal · **not** invent ENABLE_UNDER_FENCES signature  
**Date sealed (design):** 2026-09-28 ~18:55 EDT (America/New_York)  
**Author (docs):** Grok Bot `<grok-bot@local>` — design seal only; **did not invent operator signature**  
**Tip at seal base:** `d2c16d8` (Gate5 DESIGN_SEALED) atop Gate4 `5879321` / Gate3 `ce53e7c` / Gate2 `7c436f8` / peer wire `30fe593` / evidence `1e502c6` / leave-Hold `fc4ef9e`  
**Package posture:** **0.18.0 HELD** · **live=DISABLED** · **LIVE_API_ENABLED=False** · **RefuseTransport default ON** · **M1=NO_CONSENSUS_YET** · **D3 NOT ACKed** · **NO_HELD** (Raft/N>2/GIA/train/SaaS) stays NO_HELD · Gate1 **SIGNED DISCUSS_ONLY** · Gates 2–5 **DESIGN_SEALED** (discuss/eval; Gate5 = procedure only)

**Binding:** `docs/planning/GATE6_LIVE_ACCEPTANCE_METRICS.md`  
**Checklist:** `docs/planning/LIVE_READINESS_CHECKLIST.md` § Gate 6  
**Council:** `council/NOTE_GATE6_ACCEPTANCE_METRICS.md` · `council/NOTE_GATE6_DESIGN_SEALED.md`

---

## 0. Honest split — sealed vs still OPEN

| Layer | Status | Meaning |
|-------|--------|---------|
| **DESIGN_SEALED** (this artifact) | **YES** | Named **metric bundle** for future canary/acceptance under kill-armed I5 is complete as **docs**: M-REFUSE / M-KILL / M-SEC / M-ADV / M-ABORT / M-LEDGER + D4-E categories + D4-K attachment — **metrics sealed**; **live measurement OPEN** |
| **Live measurement / canary evidence** | **NO — OPEN** | Under **DISCUSS_ONLY** — do **not** run canary; do **not** claim live RV; dry-run eval metrics = **evidence-only ≠ live RV** |
| **ENABLE seal / Mesh live flip** | **NO — OPEN** | Requires **ENABLE_UNDER_FENCES** (operator user-written) + Gates **2–5 enable**-ready + Gate5 canary execute — **Do not invent signature.** |
| **Flag flip** | **FORBIDDEN now** | `LIVE_API_ENABLED` / `live_adapter.enabled` stay **false** |
| **Dry-run peer `30fe593` / evidence `1e502c6`** | **≠ live RV** | Flag-gated Gemini free eval only; metrics observed there are **evidence-only** under DISCUSS_ONLY — **not** Gate6 live acceptance |

**Claim hygiene (D4-F):** DESIGN_SEALED (metrics) ≠ live measurement ≠ canary started ≠ ENABLE seal ≠ live-ready ≠ authorization to flip flags.

---

## 1. What is DESIGN_SEALED (metrics / DISCUSS_ONLY)

| Item | Bound evidence / cite | Sealed? |
|------|----------------------|---------|
| D4-E categories (correctness / safety / reliability / human factors) | `GATE6_LIVE_ACCEPTANCE_METRICS.md` §1 | Design yes |
| M-REFUSE-1..3 refuse-default negatives | §2.1 — zero network while flags false; NT-* green; no partial enable | Design yes |
| M-KILL-1..3 kill latency / resume | §2.2 — kill→RefuseTransport+ABORT; budget ops-defined; no auto-resume | Design yes (not live-armed; latency # filled only on future ACK’d canary) |
| M-SEC-1..3 no secret leakage | §2.3 — no raw secrets in digests/explain/CI; handle ids only; forbidden egress held | Design yes |
| M-ADV-1..3 advisory-only judge | §2.4 — peer = eval evidence; L_judge propose-only; dual agree ≠ M1 unlock | Design yes |
| M-ABORT-1..3 abort > accept | §2.5 — Mesh ABORT > judge ACCEPT; anomaly→RefuseTransport; fail-closed | Design yes |
| M-LEDGER-1..3 ledger evidence | §2.6 — required kinds; oversight/abort; claim hygiene | Design yes |
| D4-K ten-condition attachment | §3 | Design yes |
| Attach path to future canary | §4 — pre-flip / step(6) / step(7) / seal attempt | Design yes |
| Gate1–5 serial (discuss/eval) | Gate1 **SIGNED DISCUSS_ONLY**; Gates 2–5 **DESIGN_SEALED** discuss/eval (Gate5=procedure) | Serial yes |
| Dry-run ≠ live RV | Peer wire `30fe593` / evidence `1e502c6` = eval dry-run only; metrics there **evidence-only** | Explicit |

---

## 2. What still needs operator ACK / later cycles (NOT sealed / NOT authorized)

| Gap | Owner | Blocked until |
|-----|-------|---------------|
| Intent upgrade **ENABLE_UNDER_FENCES** | **Operator (user-written signature)** | Explicit ACK artifact — bots must **not** invent — draft at `docs/planning/GATE1_ENABLE_UNDER_FENCES_ACK_DRAFT.md` (**UNSIGNED**) |
| Gates 2–5 **ENABLE** seals | Operator + council | After ENABLE intent + live proof path |
| **Gate5 canary execution** | Serial Gates 1–4 **enable**-ready + ENABLE ACK | Runbook **DESIGN_SEALED**; flip **NOT executed** / **NOT AUTHORIZED** under DISCUSS_ONLY |
| Gate6 **live measurement** on canary evidence | After canary (if ever authorized) | Metrics **DESIGN_SEALED**; measurement **OPEN** |
| Live RV-1..RV-7 under real Mesh transport | Gate5+rollback cycle | Mock / dry-run only today — dry-run ≠ live RV |

---

## 3. Fences held at DESIGN_SEAL

| Fence | Value |
|-------|-------|
| `LIVE_API_ENABLED` | **False** (untouched) |
| `live_adapter.enabled` | **false** |
| Mesh live L_judge adapter | **NOT_ENABLED** (RefuseTransport) |
| Canary | **NOT STARTED / NOT AUTHORIZED** |
| Live measurement of this bundle | **OPEN** (not claimed) |
| Keys in repo / CI / digests | **NONE** — oob path only |
| Push / tags / secrets in git | **NONE** |
| Gate1 intent | **DISCUSS_ONLY** (no upgrade; no invented ENABLE_UNDER_FENCES) |
| NO_HELD | Raft, N>2, GIA, train, SaaS, pkg0190 — **stay NO_HELD** |
| D3 / `MESH_PERF_EXPERIMENTAL` | **OFF** / NOT ACKed |
| Dry-run peer `30fe593` | Flag-gated eval only; **not** Mesh live / **not** Gate5 canary / **not** live RV |

---

## 4. Exit rules (restated)

| Exit | Met? |
|------|------|
| Gate6 **design** exit for DISCUSS_ONLY — named metric bundle + D4-E/J/K attachment; pytest necessary/insufficient alone; canary evidence marked OPEN | **YES — DESIGN_SEALED (metrics)** |
| Gate6 **live measurement** exit (metrics on canary evidence under kill-armed I5) | **NO — OPEN / FORBIDDEN under DISCUSS_ONLY** |
| Checklist “metrics measured on canary / live proof” | Still **OPEN** |
| Flag flip | **FORBIDDEN now** |

---

## 5. Honest status after Gate6 (wall)

| Track | Status |
|-------|--------|
| Design chain Gates **2–6** | **DESIGN_SEALED** under **DISCUSS_ONLY** (Gate5=procedure; Gate6=metrics) |
| Live+API **100%** | **Still blocked** — needs operator **ENABLE_UNDER_FENCES** ACK + Gates 2–5 **enable** seals + Gate5 **canary execute** + Gate6 **live measurement** |
| Mesh 0.18 local/mock | Usable under fences; **≠** live+API 100% |

---

## 6. Next serial blueprint step (no ask)

**Next (enable path — docs only):** write / hold **ENABLE_UNDER_FENCES** operator ACK **draft** (`docs/planning/GATE1_ENABLE_UNDER_FENCES_ACK_DRAFT.md`) for **user signature later** — **UNSIGNED**; bots must **not** invent signature. Optional: council PASTE DeepSeek ACK of design-seal pack 2–6.  
**Later (execute path):** ENABLE signed → Gates 2–5 enable seals → Gate5 **canary execution** under kill-armed I5 → Gate6 metrics **measured** on canary evidence.

---

## 7. Related

- `docs/planning/GATE6_LIVE_ACCEPTANCE_METRICS.md`
- `docs/planning/LIVE_READINESS_CHECKLIST.md`
- `docs/planning/GATE1_LIVE_OPERATOR_ACK_SIGNED.md`
- `docs/planning/GATE1_ENABLE_UNDER_FENCES_ACK_DRAFT.md` (**UNSIGNED**)
- `docs/planning/GATE2_DESIGN_SEALED.md` · `GATE3_DESIGN_SEALED.md` · `GATE4_DESIGN_SEALED.md` · `GATE5_DESIGN_SEALED.md`
- `docs/planning/GEMINI_FREE_NEXT_STEPS.md` · `GEMINI_DRY_RUN_EVIDENCE.md` · `LIVE_100_OPERATOR_WALL.md`
- `council/NOTE_GEMINI_PEER_DRY_RUN_WIRE.md` · `council/NOTE_GEMINI_DRY_RUN.md`
- `docs/planning/GATE5_LIVE_FLAG_FLIP_RUNBOOK.md`
- `docs/planning/D1_L_JUDGE_SAFETY_CASE_MATURATION.md` (§10 · §4.4)
- `council/COUNCIL_AGREEMENT_D4.md` (D4-E/J/K)
- `src/neural_mesh/packaging/l_judge_live_adapter_safety.py`
- `src/neural_mesh/packaging/google_l_judge_peer_spike.py` (`LIVE_API_ENABLED=False`)

---

*End GATE6_DESIGN_SEALED — metrics sealed for DISCUSS_ONLY; live measurement OPEN; canary NOT STARTED / NOT AUTHORIZED; live=DISABLED; LIVE_API_ENABLED=False; ENABLE still needs operator ACK; next=ENABLE_UNDER_FENCES draft (UNSIGNED) for operator signature.*
