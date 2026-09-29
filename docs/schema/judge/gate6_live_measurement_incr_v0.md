# Schema — Gate6 live-measurement incremental v0

**Status:** descriptors + seal-attempt contract under **CP-0086**  
**Phase:** **G6-INCR**  
**Does NOT** authorize R5 · permanent LIVE · F4 invent · product seal claim  
**Date:** 2026-09-28 ~23:19 EDT  
**Author:** Grok Bot `<grok-bot@local>`

---

## Surfaces

| Surface | Role |
|---------|------|
| Gate6 pack (CP-0079) | seal_candidate + prior real #1 |
| CP-0084 R3 incremental | prior real #2 |
| LiveHttpTransport (CP-0078) | This CP incremental unary HAPPY |
| Gemini free canary (CP-0075) | Session / I5 / ENABLE_UNDER_FENCES |
| RefuseTransport | Default binding; restore after |
| F4 product ACK draft | UNSIGNED — blocks product seal |

---

## Constants

| Key | Value |
|-----|-------|
| `impl_cp` | CP-0086 |
| `policy_cp` | CP-0084 |
| `design_cp` | CP-0081 |
| `prior_cp` | CP-0085 |
| `phase` | G6-INCR |
| `LIVE_API_ENABLED` | false (permanent) |
| `seal_candidate` | true |
| `product_seal` | false |
| `N_min` | 5 |
| `n_real_http_pack_baseline` | 1 |
| `n_real_http_r3_incremental_prior` | 1 |
| `n_real_http_min_live_measurement_seal` | 3 |
| `r5_authorized` | false |

---

## Descriptor IDs

| ID | Intent | Expected |
|----|--------|----------|
| **T-g6-incr-a** | prior accounting + bar | pack+R3 priors; bar=3 |
| **T-g6-incr-b** | incremental HAPPY | optional real under fences; LIVE False after; quota honest |
| **T-g6-incr-c** | variance honesty | min/median/max; no single-point live-ready |
| **T-g6-incr-d** | seal levels | live-measurement iff n≥3+variance; product False |
| **T-g6-incr-e** | module fence | LIVE False; R5/F4 invent not authorized |

---

## Policy verdicts

| Verdict | Meaning |
|---------|---------|
| `INCREMENTAL_RECORDED_BAR_OPEN` | Sample recorded or mock; bar still <3 or incomplete |
| `BAR_MET_VARIANCE_INCOMPLETE` | n≥3 but variance honesty missing |
| `LIVE_MEASUREMENT_SEALED_PRODUCT_OPEN` | live-measurement sealed; product stays OPEN (F4) |

---

## Suite shape (`mesh.judge.gate6_live_measurement_incr_suite/v0`)

```
ok: bool
seal: SealAttempt dict
variance: VarianceReport dict
incremental: IncrementalHappyResult | null
n_real_http_gate6_total: int
verdict: string
live_measurement_seal: bool
product_seal: false
LIVE_API_ENABLED_module_final: false
r5_authorized: false
binding_final: RefuseTransport
```

---

*End gate6_live_measurement_incr_v0 — measurement only; product seal OPEN.*
