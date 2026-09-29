# IMPL CP-0084 — Phase R3 Gate6 live-measurement seal policy

**Status:** **AUTHORIZED measurement/policy** under fences — **R3 only**  
**Cycle / Checkpoint:** 80 / **CP-0084**  
**Date:** 2026-09-28 ~23:13 EDT (America/New_York)  
**Author:** Grok Bot `<grok-bot@local>`  
**Tip at mint base:** `56cdaa0` (CP-0083 R2 DONE)  
**Package:** **0.18.0 HELD** · **LIVE_API_ENABLED=False** · **NO_HELD unchanged** · D3 NOT ACKed · M1=**NO_CONSENSUS_YET**  
**Parent design:** CP-0081 `MESH_FULL_ADAPTER_LIVE_RV_DESIGN.md` §4 Phase **R3**

---

## 0. What this is / is not

| Is | Is not |
|----|--------|
| Thin measurement/policy authorizing **R3 only**: Gate6 seal bar vs seal_candidate | Authorization for **R4–R5** |
| Design bar `N_real_http_min=3`; incremental real HAPPY if quota allows | Gate6 live-measurement / product **final seal** |
| Honest `n_real_http` accounting; leave LIVE **False** | F4 invent · NO_HELD · push/tags/secrets · “5 live” |
| Policy: candidate remains until F4 + more real HTTP later | Permanent `LIVE_API_ENABLED=True` |

---

## 1. Artifacts

| Artifact | Path |
|----------|------|
| R3 policy | `docs/planning/MESH_FULL_ADAPTER_R3_GATE6_SEAL_POLICY.md` |
| CP seal (this) | `docs/planning/IMPL_CP_0084_GATE6_LIVE_MEASUREMENT_SEAL_POLICY.md` |
| Schema / descriptors | `docs/schema/judge/full_adapter_r3_gate6_seal_policy_v0.md` |
| Packaging | `src/neural_mesh/packaging/l_judge_full_adapter_r3_gate6_seal_policy.py` |
| Tests | `tests/test_full_adapter_r3_gate6_seal_policy_cycle80.py` |
| Council note | `council/NOTE_CP_0084_GATE6_LIVE_MEASUREMENT_SEAL_POLICY.md` |
| Evidence | `docs/planning/EVIDENCE_CP_0084_GATE6_LIVE_MEASUREMENT_SEAL_POLICY.md` |

---

## 2. Outcomes

| Item | Result |
|------|--------|
| seal_candidate | **MET** (unchanged) |
| Gate6 live-measurement seal | **NOT MET** / **OPEN** |
| Gate6 product seal | **NOT MET** / **OPEN** (F4 UNSIGNED) |
| `n_real_http_pack_baseline` | **1** |
| `n_real_http_r3_incremental` | **1** (HTTP 200 ADVISORY) |
| `n_real_http_gate6_total` | **2** (&lt; bar 3) |
| Verdict | **POLICY_SEALED_CANDIDATE_REMAINS** |
| Module LIVE | **False** |
| R4–R5 | **NOT authorized** (R4 **OPEN**) |

---

## 3. Explicit non-authorization

This CP **must not** be cited as authority for:

1. **R4** streaming DEFER or streaming RV  
2. **R5** F4 product ACK / permanent module True  
3. Claiming Gate6 live-measurement **final sealed**  
4. Claiming Gate6 **product seal** / “5 live”  
5. Flipping permanent `LIVE_API_ENABLED` / inventing F4 / unlock NO_HELD / push/tags/secrets  

**does NOT authorize R4** · R5.

---

## 4. Honest 「listo」 after this CP

| Track | Status |
|-------|--------|
| Listo bajo fences | **YES** (unchanged) |
| Full Mesh adapter live RV | **OPEN** — R0–R3 done; **R4 OPEN** |
| Gate6 live-measurement seal | **OPEN** (candidate remains; need ≥3 real HTTP later) |
| Product permanent LIVE | **NO** — F4 ACK **UNSIGNED**; prefer leave False |

---

*End IMPL_CP_0084 — R3 DONE; R4 OPEN; LIVE False; F4 unsigned; n_real_http_gate6_total=2; NO_HELD unchanged.*
