# Gate 2 — DESIGN_SEALED (DISCUSS_ONLY / Gemini free-tier eval path)

**Status:** **DESIGN_SEALED** for Gate1 **DISCUSS_ONLY** / Gemini **free-tier eval** safety amendment  
**Not:** operator-SIGNed ENABLE seal · **not** `live=ENABLED` · **not** Mesh live adapter on · **not** Gate5 canary  
**Date sealed (design):** 2026-09-28 ~18:43 EDT (America/New_York)  
**Author (docs):** Grok Bot `<grok-bot@local>` — design seal only; **did not invent operator signature**  
**Tip at seal base:** `30fe593` (Gemini peer dry-run wire) atop evidence `1e502c6` / leave-Hold `fc4ef9e`  
**Package posture:** **0.18.0 HELD** · **live=DISABLED** · **LIVE_API_ENABLED=False** · **RefuseTransport default ON** · **M1=NO_CONSENSUS_YET** · **D3 NOT ACKed** · **NO_HELD** (Raft/N>2/GIA/train/SaaS) stays NO_HELD · Gate1 **SIGNED DISCUSS_ONLY**

**Amendment:** `docs/planning/GATE2_LIVE_SAFETY_CASE_AMENDMENT.md`  
**Checklist:** `docs/planning/LIVE_READINESS_CHECKLIST.md` § Gate 2  
**Council:** `council/NOTE_GATE2_SAFETY_AMENDMENT.md` · `council/NOTE_GATE2_DESIGN_SEALED.md`

---

## 0. Honest split — sealed vs still needs operator ACK

| Layer | Status | Meaning |
|-------|--------|---------|
| **DESIGN_SEALED** (this artifact) | **YES** | Live-safety **amendment text** for Gemini free-tier **eval / DISCUSS_ONLY** path is complete, bound to dry-run evidence, Authority Matrix, RefuseTransport, and secret_handle — **design/docs seal only** |
| **ENABLE seal / operator SIGN** | **NO — OPEN** | Requires explicit signed operator ACK intent **ENABLE_UNDER_FENCES** (user-written). Gate1 today is **DISCUSS_ONLY** only. **Do not invent signature.** |
| **Live proof (RV under Mesh live transport)** | **NO — OPEN** | Dry-run eval ≠ Gate5 canary ≠ live RV-1..RV-7 under Mesh live adapter |
| **Flag flip** | **FORBIDDEN now** | `LIVE_API_ENABLED` / `live_adapter.enabled` stay **false** |

**Claim hygiene (D4-F):** DESIGN_SEALED ≠ ENABLE seal ≠ live-ready ≠ Gate5 canary.

---

## 1. What is DESIGN_SEALED (DISCUSS_ONLY / eval)

| Item | Bound evidence / cite | Sealed? |
|------|----------------------|---------|
| D1 safety maturation (CP-0071) + D4-A..K | `docs/planning/D1_L_JUDGE_SAFETY_CASE_MATURATION.md` · `council/D4_CHATGPT_FINDINGS.md` | Design yes |
| Live amendment §§2–5 (blast radius, key compromise, kill→Refuse+ABORT, continuity under peer failure) | `GATE2_LIVE_SAFETY_CASE_AMENDMENT.md` | Design yes |
| Authority Matrix cite (D4-A / Gate3 IDs) | `GATE3_AUTHORITY_MATRIX_BINDING.md` AM-* IDs; L_judge propose-only; Operator sole live-enable ACK; `AM-REFUSE` | Design cite yes |
| RefuseTransport fail-closed default | `src/neural_mesh/packaging/l_judge_live_adapter_safety.py` · CP-0058 | In force |
| secret_handle hygiene (eval) | Handle id `mesh://secrets/judge/gemini-free@v1`; path `/home/box/.config/neural-mesh/gemini.env` **outside repo**; `.gitignore` covers | Eval provisioned; raw key never in git |
| Gemini free dry-run evidence | `GEMINI_DRY_RUN_EVIDENCE.md` @ tip context `fc4ef9e`→`1e502c6` — HTTP 200, marker `MESH_DRY_RUN_OK`, model `gemini-flash-latest` | Eval evidence yes |
| Peer dry-run wire (flag-gated) | `30fe593` · `NOTE_GEMINI_PEER_DRY_RUN_WIRE.md` — `GeminiFreeDryRunTransport`; default mock/no-network; Mesh live slot still Refuse | Eval wire yes |
| Gate1 intent | **SIGNED DISCUSS_ONLY** — `GATE1_LIVE_OPERATOR_ACK_SIGNED.md` | Intent locked discuss |
| mock RV-1..RV-7 | Still mock-green (D1); **not** live-transport RV | Design/mock yes |

---

## 2. What still needs operator ACK / later cycles (NOT sealed)

| Gap | Owner | Blocked until |
|-----|-------|---------------|
| Intent upgrade **ENABLE_UNDER_FENCES** | **Operator (user-written signature)** | Explicit ACK artifact the operator writes — bots must **not** invent |
| Gate2 **ENABLE** seal (live proof claim) | Operator + council | After ENABLE intent + live-path RV evidence |
| Gate3 seal (matrix **in use** on live-armed config) | Serial after Gate2 enable path | Design binding exists; live ops not armed |
| Gate4 seal for enable (handle + schedule ACK’d for Mesh live) | Serial | Eval handle done; Mesh live schedule seal OPEN |
| Gate5 canary under kill-armed I5 | Serial Gates 2–4 enable-sealed | Runbook drafted; **NOT executed** |
| Gate6 acceptance bundle on canary | Serial after Gate5 evidence | Bundle drafted; canary not run |
| Live RV-1..RV-7 under real Mesh transport | Gate5+rollback cycle | Mock-only today |

---

## 3. Fences held at DESIGN_SEAL

| Fence | Value |
|-------|-------|
| `LIVE_API_ENABLED` | **False** (untouched) |
| `live_adapter.enabled` | **false** |
| Mesh live L_judge adapter | **NOT_ENABLED** |
| Push / tags / secrets in git | **NONE** |
| Gate1 intent | **DISCUSS_ONLY** (no upgrade) |
| NO_HELD | Raft, N>2, GIA, train, SaaS, pkg0190 — **stay NO_HELD** |
| D3 / `MESH_PERF_EXPERIMENTAL` | **OFF** / NOT ACKed |

---

## 4. Exit rules (restated)

| Exit | Met? |
|------|------|
| Gate2 **design** exit for DISCUSS_ONLY / eval amendment reviewed + mock RV green + Gate1 discuss signed | **YES — DESIGN_SEALED** |
| Gate2 **enable** exit (live amendment reviewed under ENABLE ACK + live proof) | **NO** |
| Checklist “Missing live proof” for enable | Still true for enable path |

---

## 5. Next serial blueprint step (no ask)

**Next:** **Gate 3** — advance Authority Matrix binding toward **DESIGN_SEALED** (DISCUSS_ONLY / config cite), still live=DISABLED.  
**Later (enable path):** Gate4 enable seal → **Gate 5** canary only after ENABLE_UNDER_FENCES + Gates 2–4 enable-ready.

---

## 6. Related

- `docs/planning/GATE2_LIVE_SAFETY_CASE_AMENDMENT.md`
- `docs/planning/LIVE_READINESS_CHECKLIST.md`
- `docs/planning/GATE1_LIVE_OPERATOR_ACK_SIGNED.md`
- `docs/planning/GEMINI_FREE_NEXT_STEPS.md` · `GEMINI_DRY_RUN_EVIDENCE.md`
- `council/NOTE_GEMINI_PEER_DRY_RUN_WIRE.md` · `council/NOTE_LEAVE_HOLD_GATE1_DISCUSS_ONLY.md`
- `docs/planning/GATE3_AUTHORITY_MATRIX_BINDING.md`
- `docs/planning/GATE4_LIVE_DATA_POLICY.md` · `GATE5_LIVE_FLAG_FLIP_RUNBOOK.md`

---

*End GATE2_DESIGN_SEALED — design/docs seal for DISCUSS_ONLY eval path; live=DISABLED; ENABLE still needs operator ACK.*
