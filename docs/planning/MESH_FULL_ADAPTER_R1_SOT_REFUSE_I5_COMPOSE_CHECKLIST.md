# Mesh full-adapter R1 — SoT + RefuseTransport + I5 compose checklist

**Status:** **R1 DONE** under **CP-0082** (thin IMPL) — docs/tests descriptors + unit compose  
**Does NOT** authorize R2–R5 · **does NOT** flip `LIVE_API_ENABLED` · **does NOT** invent F4 · **does NOT** raise n_real_http  
**Cycle / Checkpoint:** 78 / **CP-0082**  
**Date:** 2026-09-28 ~23:06 EDT (America/New_York)  
**Author:** Grok Bot `<grok-bot@local>`  
**Tip at mint base:** `f30c4bb` (CP-0081 DESIGN_ONLY)  
**Authority:** CP-0081 §4 Phase **R1** · operator authorize R1 only  
**Package:** **0.18.0 HELD** · **`LIVE_API_ENABLED=False`** · RefuseTransport default ON · **NO_HELD unchanged**

**Design parent:** `MESH_FULL_ADAPTER_LIVE_RV_DESIGN.md`  
**CP seal:** `IMPL_CP_0082_FULL_ADAPTER_R1_COMPOSE.md`  
**Schema / descriptors:** `docs/schema/judge/full_adapter_r1_compose_v0.md`  
**Packaging:** `src/neural_mesh/packaging/l_judge_full_adapter_r1_compose.py`  
**Tests:** `tests/test_full_adapter_r1_compose_cycle78.py`

---

## 0. What R1 is / is not

| Is | Is not |
|----|--------|
| Full-adapter **SoT + RefuseTransport + I5** compose checklist | Multi-judge live RV (R2) |
| Negative-test **descriptors** + unit tests on packaging LiveHttpTransport + canary path | Gate6 live-measurement seal / more real HTTP (R3) |
| Proof: refuse when live off · I5 kill compose · advisory≠SoT / `mesh_accept=false` | Streaming DEFER/RV (R4) · F4 product ACK (R5) |
| Leaves module **False** | Permanent LIVE enable |

**Surface:** packaging `LiveHttpTransport` v0 + Gemini free canary path (CP-0075/0078) — **not** a new live product adapter.

---

## 1. SoT boundaries (must hold on compose)

| ID | Boundary | Prove |
|----|----------|-------|
| **SOT-1** | Mesh = SoT for goals / evidence / continuity / ABORT | Compose receipt keeps `mesh_accept=false` on advisory |
| **SOT-2** | Judge = propose-only; I5/Operator own kill + live-enable | I5 kill → ABORT; no post-kill execute |
| **SOT-3** | Advisory digests / Gemini text **never** Mesh ACCEPT / continuity SoT | Happy mock advisory → `advisory_only=true`, `mesh_accept=false` |
| **SOT-4** | Continuity resume from Mesh registry+ledger only | Cited; no LLM-chat resume claim |
| **SOT-5** | Claim hygiene: canary 200 ≠ live ready · ADVISORY ≠ SoT · seal_candidate ≠ F4 · ENABLE ≠ product | Binding in checklist + auth record |

---

## 2. RefuseTransport compose

| ID | Rule | Descriptor | Status |
|----|------|------------|--------|
| **REF-1** | `enabled=false` / live off → `ENGINE_DISABLED`; **zero** network | **T-fa-r1-a** | **PASS** (unit) |
| **REF-2** | After session, runtime LIVE **False** + Refuse binding | **T-fa-r1-d** | **PASS** (unit) |
| **REF-3** | Bare `RefuseTransport` still default when module False | covered by T-fa-r1-a | **PASS** |

---

## 3. I5 compose

| ID | Rule | Descriptor | Status |
|----|------|------------|--------|
| **I5-1** | Kill-armed: kill → Refuse + ABORT; no resume without re-ACK | **T-fa-r1-b** | **PASS** (unit) |
| **I5-2** | Module `LIVE_API_ENABLED` stays False on canary + LHT + R1 surfaces | **T-fa-r1-e** | **PASS** (unit) |
| **I5-3** | M-KILL-2 process-local budget remains prior (CP-0080); R1 does not widen to network RTT | cited | Held |

---

## 4. Negative-test descriptors (R1)

| ID | Intent | Exit |
|----|--------|------|
| **T-fa-r1-a** | Refuse when live off | `ENGINE_DISABLED`; zero network; `mesh_accept=false` |
| **T-fa-r1-b** | I5 kill compose | ABORT (`ENGINE_DISABLED`\|`HUMAN_ABORT`); subsequent Refuse; zero post-kill network |
| **T-fa-r1-c** | Advisory ≠ SoT | Mock HTTP-ok → `ADVISORY` / `advisory_only` / `mesh_accept=false` |
| **T-fa-r1-d** | Session restore | Runtime LIVE False after compose |
| **T-fa-r1-e** | Module fence | Canary + LHT + R1 constants all False |

---

## 5. Explicit non-authorization (R1)

This checklist / CP-0082 **must not** be cited as authority for:

1. **R2** multi-judge live/mock-bound RV  
2. **R3** Gate6 live-measurement seal or raising `n_real_http`  
3. **R4** streaming DEFER seal or streaming RV  
4. **R5** F4 product ACK / permanent module True  
5. Setting module `LIVE_API_ENABLED=True`  
6. Inventing F4 signature · unlock NO_HELD · push/tags/secrets · D3  

---

## 6. Phase board after R1

| Phase | Status |
|-------|--------|
| **R0** | **DONE** — CP-0081 DESIGN_ONLY |
| **R1** | **DONE** — this checklist + CP-0082 + descriptors + unit compose |
| **R2** | **DONE** — CP-0083 multi-judge live/mock-bound |
| **R3** | **DONE** — CP-0084 Gate6 seal policy (candidate remains) |
| **R4** | **OPEN** — streaming DEFER or RV (optional) |
| **R5** | **OPEN** — operator F4 product ACK only |

**Hard:** `LIVE_API_ENABLED=False` · Prefer leave False · NO_HELD unchanged.

---

*End MESH_FULL_ADAPTER_R1 checklist — R1 DONE; R2 DONE (CP-0083); R3 DONE (CP-0084); R4 DONE (CP-0085 DEFER); R5 OPEN (operator); LIVE False; F4 unsigned.*
