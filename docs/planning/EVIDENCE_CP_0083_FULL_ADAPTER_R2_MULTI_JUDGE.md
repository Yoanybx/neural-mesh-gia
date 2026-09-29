# Evidence — CP-0083 Phase R2 multi-judge live/mock-bound RV

**Status:** **MEASURED** (mock-bound + **1 real HTTP** under fences) · module LIVE False  
**Date:** 2026-09-28 ~23:12 EDT (America/New_York)  
**Author:** Grok Bot `<grok-bot@local>`  
**Tip at base:** `4023d65`  
**Tests:** `tests/test_full_adapter_r2_multi_judge_cycle79.py` (**11 passed**, 1 skipped default; real opt-in PASS)

**Does not** flip permanent LIVE · **does not** authorize R3–R5 · **does not** invent F4 · **does not** unlock NO_HELD · **does not** claim M1 consensus.

---

## 1. Descriptor results

| Descriptor | Result |
|------------|--------|
| **T-fa-r2-a** refuse default | **PASS** — `ENGINE_DISABLED`; zero network; L_judge !execute |
| **T-fa-r2-b** I5 armed | **PASS** — ABORT; Refuse binding; zero post-kill network; restore False |
| **T-fa-r2-c** ABORT > ACCEPT | **PASS** — Mesh `POLICY_ABORT` despite dual judge ACCEPT claims |
| **T-fa-r2-d** conflict | **PASS** — `JUDGE_CONFLICT`; escalate I5; no auto-majority |
| **T-fa-r2-e** missing judge | **PASS** — `JUDGE_MISSING`; never invent ACCEPT |
| **T-fa-r2-f** agree ≠ M1 | **PASS** — `ADVISORY`; `m1_status=NO_CONSENSUS_YET`; `mesh_accept=false` |
| **T-fa-r2-g** live+mock-bound | **PASS** — Gemini **real_http HTTP 200** + mock-local; mesh ADVISORY; `mesh_accept=false` |
| **T-fa-r2-h** module fence | **PASS** — canary + LHT + R2 constants False; RefuseTransport final |

---

## 2. Real HTTP (T-fa-r2-g)

| Field | Value |
|-------|-------|
| Gates | Gate1 ENABLE_UNDER_FENCES SIGNED · CP-0075/0078 `may_enable` · oob key present · I5 armed |
| Gemini judge | `judge:gemini-free` · mode **real_http** · HTTP **200** · verdict **ADVISORY** |
| Marker | `MESH_R2_MULTI_JUDGE_OK` |
| Mock judge | `judge:mock-local` · mode **mock_local** · digest aligned |
| Mesh | verdict **ADVISORY** · `mesh_accept=false` · `m1_status=NO_CONSENSUS_YET` · `auto_majority_execute=false` |
| Quota | **none** (HTTP 200) |
| Module LIVE final | **False** |
| Runtime LIVE final | **False** |
| Binding final | **RefuseTransport** |
| Secrets | handle id only · no raw key / no `AI`+`za` / no Bearer in evidence |

**Claim hygiene:** N=2 dual advisory (1 real + 1 mock) **≠** M1 consensus · canary/advisory 200 **≠** product permanent LIVE · R2 **≠** Gate6 final seal.

---

## 3. Suite summary

| Field | Value |
|-------|-------|
| Phase | **R2** |
| impl_cp | CP-0083 |
| Suite ok | **true** (**11 passed** mock default; real+suite **ok=true**) |
| Module LIVE final | **False** |
| M1 status | **NO_CONSENSUS_YET** |
| n_judges | **2** |
| real_http_used | **true** (one fenced call) |
| r3_r5_authorized | **false** |
| Binding default | RefuseTransport |

---

## 4. Phase board

| Phase | Status |
|-------|--------|
| R0 | DONE (CP-0081) |
| R1 | DONE (CP-0082) |
| R2 | **DONE** (this CP) |
| R3–R5 | **OPEN** / not authorized |

---

*End EVIDENCE_CP_0083 — R2 multi-judge green; 1 real HTTP 200 + mock; LIVE False; M1=NO_CONSENSUS_YET; R3 OPEN.*
