# IMPL CP-0082 — Phase R1 full-adapter SoT + RefuseTransport + I5 compose

**Status:** **AUTHORIZED thin IMPL** under fences — **R1 only**  
**Cycle / Checkpoint:** 78 / **CP-0082**  
**Date:** 2026-09-28 ~23:06 EDT (America/New_York)  
**Author:** Grok Bot `<grok-bot@local>`  
**Tip at mint base:** `f30c4bb` (CP-0081 DESIGN_ONLY)  
**Package:** **0.18.0 HELD** · **LIVE_API_ENABLED=False** · **NO_HELD unchanged** · D3 NOT ACKed · M1=NO_CONSENSUS_YET  
**Parent design:** CP-0081 `MESH_FULL_ADAPTER_LIVE_RV_DESIGN.md` §4 Phase **R1**

---

## 0. What this is / is not

| Is | Is not |
|----|--------|
| Thin IMPL authorizing **R1 only**: checklist + negative-test descriptors + unit compose | Authorization for **R2–R5** |
| Compose SoT boundaries + RefuseTransport + I5 on packaging LiveHttpTransport + canary path | Permanent LIVE enable / new live HTTP canaries |
| Leaves module LIVE **False** | F4 invent · NO_HELD · push/tags/secrets · codec beyond CP-0078 v0 |

---

## 1. Artifacts

| Artifact | Path |
|----------|------|
| R1 checklist | `docs/planning/MESH_FULL_ADAPTER_R1_SOT_REFUSE_I5_COMPOSE_CHECKLIST.md` |
| CP seal (this) | `docs/planning/IMPL_CP_0082_FULL_ADAPTER_R1_COMPOSE.md` |
| Schema / descriptors | `docs/schema/judge/full_adapter_r1_compose_v0.md` |
| Packaging compose | `src/neural_mesh/packaging/l_judge_full_adapter_r1_compose.py` |
| Tests | `tests/test_full_adapter_r1_compose_cycle78.py` |
| Council note | `council/NOTE_CP_0082_FULL_ADAPTER_R1_COMPOSE.md` |
| Evidence | `docs/planning/EVIDENCE_CP_0082_FULL_ADAPTER_R1_COMPOSE.md` |

---

## 2. Outcomes

| Item | Result |
|------|--------|
| R1 checklist | **DONE** |
| Descriptors T-fa-r1-a..e | **DONE** (unit) |
| Refuse when live off | **PASS** |
| I5 kill compose | **PASS** |
| Advisory ≠ SoT / `mesh_accept=false` | **PASS** |
| Module LIVE | **False** |
| R2–R5 | **NOT authorized** (R2 **OPEN**) |

---

## 3. Explicit non-authorization

This CP **must not** be cited as authority for:

1. **R2** multi-judge live/mock-bound RV  
2. **R3** Gate6 live-measurement seal / raise `n_real_http`  
3. **R4** streaming DEFER or streaming RV  
4. **R5** F4 product ACK / permanent module True  
5. Flipping `LIVE_API_ENABLED` / inventing F4 / unlock NO_HELD / push/tags/secrets  

**does NOT authorize R2** · R3 · R4 · R5.

---

## 4. Honest 「listo」 after this CP

| Track | Status |
|-------|--------|
| Listo bajo fences | **YES** (unchanged) |
| Full Mesh adapter live RV | **OPEN** — R0+R1 done; **R2 OPEN** |
| Product permanent LIVE | **NO** — F4 ACK **UNSIGNED**; prefer leave False |

---

*End IMPL_CP_0082 — R1 DONE; R2 OPEN; LIVE False; F4 unsigned; NO_HELD unchanged.*
