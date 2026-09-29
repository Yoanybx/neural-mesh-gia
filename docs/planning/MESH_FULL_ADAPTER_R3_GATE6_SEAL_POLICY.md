# Mesh full-adapter R3 — Gate6 live-measurement seal policy

**Status:** **R3 DONE** (policy sealed) — Gate6 **live-measurement seal** later **SEALED** by **CP-0086** (n=3); **product seal** remains **OPEN**  
**Does NOT** flip `LIVE_API_ENABLED` · **does NOT** invent F4 · **does NOT** authorize R4/R5 · **does NOT** claim Gate6 product sealed  
**Cycle / Checkpoint:** 80 / **CP-0084**  
**Date:** 2026-09-28 ~23:13 EDT (America/New_York)  
**Author:** Grok Bot `<grok-bot@local>`  
**Parent:** CP-0081 `MESH_FULL_ADAPTER_LIVE_RV_DESIGN.md` §4 Phase **R3**  
**Package:** **0.18.0 HELD** · **`LIVE_API_ENABLED=False`** · **NO_HELD unchanged** · M1=NO_CONSENSUS_YET

---

## 0. What this is / is not

| Is | Is not |
|----|--------|
| Honest policy: **seal_candidate** vs **Gate6 live-measurement seal** vs **product seal** | Permission to claim live-measurement / product sealed |
| Limited incremental real HAPPY under free-tier when quota allows | Permanent LIVE / five-live claim |
| Design bar `N_real_http_min=3` for future live-measurement seal attempt | Auto-seal when bar met numerically |
| Prefer leave module **False** | R4 streaming / R5 F4 invent |

---

## 1. Three-level Gate6 bar (binding)

| Level | Requirement | Status @ CP-0084 |
|-------|-------------|------------------|
| **seal_candidate** | n ≥ N_min=5 total attempts + edge mix (CP-0077); may be **1 real + mocks** | **MET** — pack n=6 (1 real, 5 mock) CP-0079 |
| **Gate6 live-measurement seal** | seal_candidate **plus** `n_real_http ≥ N_real_http_min=3` independent real HAPPY (free-tier, kill-armed) + variance/ledger honesty; **not** mock substitution for the real count | **SEALED @ CP-0086** — `n_real_http_gate6_total=3` (pack 1 + R3 incr 1 + CP-0086 incr 1) |
| **Gate6 product seal / permanent** | live-measurement seal **plus** **signed** F4 product ACK + P7 walk | **NOT MET** — F4 ACK **UNSIGNED** |

**Invariant:** seal_candidate ≠ live-measurement seal ≠ product permanent 「listo」.  
**Claim hygiene:** Prefer 「pack n=6 (1 real, 5 mock)」 + honest `n_real_http_gate6_total` — never “5 live sealed.”

---

## 2. Why R3 does **not** raise the bar as met

| Factor | Decision |
|--------|----------|
| Free-tier quota | Space real HTTP; do not burn quota chasing a false seal |
| Current real count | Pack baseline **1** + R3 incremental **1** → **total 2** |
| Design bar | **N_real_http_min=3** — justified for minimal distribution beyond 1–2 samples; **not** met |
| F4 | UNSIGNED — product seal blocked regardless of HTTP count |
| Preference | Seal **policy** that candidate remains until F4/operator fills real-HTTP bar via future authorized measurement CP |

Raising `N_real_http_min` above pack’s single real sample is **justified** as the live-measurement bar (honest variance). Claiming that bar **met** this CP is **not** justified.

---

## 3. Checklist rows

| ID | Topic | Rule | Status |
|----|-------|------|--------|
| G6-POL-1 | seal_candidate | N_min=5 as pack n=6 | **DONE** |
| G6-POL-2 | live-measurement bar | n_real_http ≥ 3 | **SEALED @ CP-0086** (3≥3) |
| G6-POL-3 | product seal | F4 signed + live-measurement | **OPEN** |
| G6-POL-4 | incremental | Limited real HAPPY under fences | **DONE** (+1 HTTP 200) |
| G6-POL-5 | fences | LIVE False; R4/R5 off | **DONE** |

---

## 4. Explicit non-authorization

1. **R4** streaming DEFER / streaming RV  
2. **R5** F4 product ACK / permanent module True  
3. Declaring Gate6 live-measurement **final sealed**  
4. Declaring Gate6 **product seal**  
5. Inventing F4 · unlock NO_HELD · push/tags/secrets  

---

## 5. Related

- `IMPL_CP_0084_GATE6_LIVE_MEASUREMENT_SEAL_POLICY.md` · `EVIDENCE_CP_0084_…`  
- `GATE6_MULTI_CANARY_MEASUREMENT.md` · `GATE6_METRIC_COMPLETION_DESIGN.md`  
- `F4_PRODUCT_ENABLE_ACK_DRAFT.md` (**UNSIGNED**)  
- `MESH_FULL_ADAPTER_LIVE_RV_DESIGN.md` · wall / next / checklist  

---

*End MESH_FULL_ADAPTER_R3_GATE6_SEAL_POLICY — R3 policy DONE; live-measurement later SEALED @ CP-0086; product OPEN; LIVE False.*
