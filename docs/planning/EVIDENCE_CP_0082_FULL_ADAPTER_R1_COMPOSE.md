# Evidence — CP-0082 Phase R1 SoT + Refuse + I5 compose

**Status:** **MEASURED** (mock/unit under fences) · module LIVE False  
**Date:** 2026-09-28 ~23:06 EDT (America/New_York)  
**Author:** Grok Bot `<grok-bot@local>`  
**Tip at base:** `f30c4bb`  
**Tests:** `tests/test_full_adapter_r1_compose_cycle78.py` (**7 passed**)

**Does not** flip permanent LIVE · **does not** authorize R2–R5 · **does not** invent F4 · **does not** unlock NO_HELD.

---

## 1. Descriptor results

| Descriptor | Result |
|------------|--------|
| **T-fa-r1-a** refuse when live off | **PASS** — `ENGINE_DISABLED`; zero network; `mesh_accept=false` |
| **T-fa-r1-b** I5 kill compose | **PASS** — ABORT; Refuse binding; zero post-kill network; restore False |
| **T-fa-r1-c** advisory ≠ SoT | **PASS** — `ADVISORY` / `advisory_only` / `mesh_accept=false` |
| **T-fa-r1-d** session restore | **PASS** — runtime LIVE False |
| **T-fa-r1-e** module fence | **PASS** — canary + LHT + R1 constants False |

---

## 2. Suite summary

| Field | Value |
|-------|-------|
| Phase | **R1** |
| impl_cp | CP-0082 |
| Suite ok | **true** (**7 passed**) |
| Module LIVE final | **False** |
| r2_r5_authorized | **false** |
| Binding default | RefuseTransport |

---

## 3. Phase board

| Phase | Status |
|-------|--------|
| R0 | DONE (CP-0081) |
| R1 | **DONE** (this CP) |
| R2–R5 | **OPEN** / not authorized |

---

*End EVIDENCE_CP_0082 — R1 unit compose green; LIVE False.*
