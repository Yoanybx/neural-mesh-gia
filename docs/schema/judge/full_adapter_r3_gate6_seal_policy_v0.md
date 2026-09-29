# Schema — full-adapter R3 Gate6 seal policy v0

**Status:** descriptors + seal-policy contract under **CP-0084**  
**Phase:** **R3** only  
**Does NOT** authorize R4–R5 · permanent LIVE · F4 invent · Gate6 live-measurement / product seal claim  
**Date:** 2026-09-28 ~23:13 EDT  
**Author:** Grok Bot `<grok-bot@local>`

---

## Surfaces

| Surface | Role |
|---------|------|
| Gate6 pack (CP-0079) | seal_candidate baseline — pack n=6 (1 real, 5 mock) |
| LiveHttpTransport (CP-0078) | Optional incremental unary HAPPY |
| Gemini free canary (CP-0075) | Session / I5 / ENABLE_UNDER_FENCES |
| RefuseTransport | Default binding; restore after |
| F4 product ACK draft | UNSIGNED — blocks product seal |

---

## Constants

| Key | Value |
|-----|-------|
| `impl_cp` | CP-0084 |
| `design_cp` | CP-0081 |
| `prior_cp` | CP-0083 |
| `phase` | R3 |
| `LIVE_API_ENABLED` | false (permanent) |
| `seal_candidate` | true |
| `live_measurement_seal` | false |
| `product_seal` | false |
| `N_min` | 5 |
| `n_real_http_pack_baseline` | 1 |
| `n_real_http_min_live_measurement_seal` | 3 |
| `r4_r5_authorized` | false |

---

## Descriptor IDs

| ID | Intent | Expected |
|----|--------|----------|
| **T-fa-r3-a** | candidate vs live-measurement seal split | candidate True; live-measurement seal False |
| **T-fa-r3-b** | real-HTTP bar documented | bar=3; not falsely claimed met when total&lt;3 |
| **T-fa-r3-c** | product seal needs F4 | product_seal False while F4 UNSIGNED |
| **T-fa-r3-d** | incremental HAPPY | optional real under fences; LIVE False after; quota honest |
| **T-fa-r3-e** | module fence | LIVE False; R4/R5 not authorized |

---

## Policy verdicts

| Verdict | Meaning |
|---------|---------|
| `POLICY_SEALED_CANDIDATE_REMAINS` | R3 policy sealed; Gate6 live-measurement / product seals stay OPEN |
| `BARS_NUMERIC_BUT_R3_DOES_NOT_PRODUCT_SEAL` | Numeric bar may be met; R3 still does not flip seals True |

---

## Suite shape (`mesh.judge.full_adapter_r3_gate6_seal_policy_suite/v0`)

```
ok: bool
policy: SealPolicy dict
incremental: IncrementalHappyResult | null
n_real_http_gate6_total: int
verdict: string
live_measurement_seal: false
product_seal: false
LIVE_API_ENABLED_module_final: false
r4_r5_authorized: false
binding_final: RefuseTransport
```

---

*End full_adapter_r3_gate6_seal_policy_v0 — R3 policy only.*
