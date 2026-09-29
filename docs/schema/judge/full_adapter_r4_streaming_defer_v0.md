# Schema — full-adapter R4 streaming DEFER v0

**Status:** descriptors + DEFER-policy contract under **CP-0085**  
**Phase:** **R4** only  
**Does NOT** authorize R5 · permanent LIVE · F4 invent · streaming codec ship  
**Date:** 2026-09-28 ~23:16 EDT  
**Author:** Grok Bot `<grok-bot@local>`

---

## Surfaces

| Surface | Role |
|---------|------|
| LiveHttpTransport (CP-0078) | Unary v0 product path; streaming_allowed=False |
| LIVE_HTTP_TRANSPORT residual (CP-0076) | T-lht-j design residual deferred |
| F4 product ACK draft | UNSIGNED; Streaming OUT unless named |
| RefuseTransport | Default binding |

---

## Constants

| Key | Value |
|-----|-------|
| `impl_cp` | CP-0085 |
| `design_cp` | CP-0081 |
| `prior_cp` | CP-0084 |
| `phase` | R4 |
| `LIVE_API_ENABLED` | false (permanent) |
| `streaming_posture` | DEFERRED |
| `streaming_f4_scope` | OUT_OF_SCOPE_FOR_F4 |
| `streaming_allowed` | false |
| `streaming_shipped` | false |
| `product_codec_mode` | unary |
| `r5_authorized` | false |

---

## Descriptor IDs

| ID | Intent | Expected |
|----|--------|----------|
| **T-fa-r4-a** | unary product path | product_codec_mode=unary; CP-0078 binding |
| **T-fa-r4-b** | F4 scope | streaming OUT_OF_SCOPE_FOR_F4 |
| **T-fa-r4-c** | flags | streaming_allowed=False; streaming_shipped=False |
| **T-fa-r4-d** | T-lht-j deferred | design residual cited; no streaming RV executed |
| **T-fa-r4-e** | module fence | LIVE False; R5 not authorized |

---

## Policy verdicts

| Verdict | Meaning |
|---------|---------|
| `STREAMING_DEFERRED_OUT_OF_F4` | R4 DEFER sealed; streaming out of F4; unary-only product |

---

## Suite shape (`mesh.judge.full_adapter_r4_streaming_defer_suite/v0`)

```
ok: bool
policy: StreamingDeferPolicy dict
verdict: STREAMING_DEFERRED_OUT_OF_F4
streaming_posture: DEFERRED
streaming_f4_scope: OUT_OF_SCOPE_FOR_F4
LIVE_API_ENABLED_module_final: false
r5_authorized: false
binding_final: RefuseTransport
```

---

*End full_adapter_r4_streaming_defer_v0 — R4 DEFER only.*
