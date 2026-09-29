# Schema — full-adapter R1 compose v0 (descriptors)

**Status:** descriptors + unit-compose contract under **CP-0082**  
**Phase:** **R1** only  
**Does NOT** authorize R2–R5 · permanent LIVE · F4 invent  
**Date:** 2026-09-28 ~23:06 EDT  
**Author:** Grok Bot `<grok-bot@local>`

---

## Surfaces

| Surface | Role |
|---------|------|
| `LiveHttpTransport` (CP-0078 packaging) | Full-adapter compose subject (unary v0) |
| Gemini free canary path (CP-0075) | Session / I5 arm / restore |
| `RefuseTransport` (CP-0058) | Default binding when live off / killed |
| `I5KillArm` | Kill authority; cannot execute |

---

## Constants

| Key | Value |
|-----|-------|
| `impl_cp` | CP-0082 |
| `design_cp` | CP-0081 |
| `phase` | R1 |
| `LIVE_API_ENABLED` | false (permanent) |
| `advisory_is_sot` | false (permanent) |
| `mesh_accept` on advisory | false (permanent) |
| `r2_r5_authorized` | false |

---

## Negative-test descriptor IDs

| ID | Intent | Expected |
|----|--------|----------|
| **T-fa-r1-a** | live off / Refuse default | `ENGINE_DISABLED`; zero network; `mesh_accept=false` |
| **T-fa-r1-b** | I5 kill compose | ABORT (`ENGINE_DISABLED`\|`HUMAN_ABORT`); Refuse binding; zero post-kill network; no resume without re-ACK |
| **T-fa-r1-c** | advisory ≠ SoT | Mock happy → `verdict=ADVISORY`, `advisory_only=true`, `mesh_accept=false` |
| **T-fa-r1-d** | session restore | Runtime LIVE False after compose session |
| **T-fa-r1-e** | module fence | Canary + LHT + R1 module constants all False |

---

## Auth record shape (`mesh.judge.full_adapter_r1_compose_auth/v0`)

```
authorized: true
phase: R1
authorizes: [R1 checklist, descriptors, unit compose]
does_not_authorize: [R2, R3, R4, R5, permanent LIVE, F4 invent, NO_HELD, push/tags/secrets]
permanent_live_enable: false
```

---

## Suite shape (`mesh.judge.full_adapter_r1_compose_suite/v0`)

```
ok: bool
descriptors: [ComposeResult…]
checklist: [SOT/REF/I5 rows]
authorization: auth record
LIVE_API_ENABLED_module_final: false
r2_r5_authorized: false
```

---

*End full_adapter_r1_compose_v0 — R1 descriptors only.*
