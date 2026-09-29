# Schema — full-adapter R2 multi-judge v0 (descriptors)

**Status:** descriptors + live/mock-bound compose contract under **CP-0083**  
**Phase:** **R2** only  
**Does NOT** authorize R3–R5 · permanent LIVE · F4 invent · M1 consensus under N=2  
**Date:** 2026-09-28 ~23:10 EDT  
**Author:** Grok Bot `<grok-bot@local>`

---

## Surfaces

| Surface | Role |
|---------|------|
| `LiveHttpTransport` (CP-0078) | Gemini free advisory path (unary v0) |
| Gemini free canary (CP-0075) | Session / I5 arm / restore / ENABLE_UNDER_FENCES |
| Deterministic mock/local advisory | Second judge under Authority Matrix |
| `RefuseTransport` (CP-0058) | Default binding when live off / killed |
| `I5KillArm` | Kill authority; cannot execute |
| Authority Matrix (D1) | L_judge propose-only; Mesh ABORT > judge ACCEPT |

---

## Constants

| Key | Value |
|-----|-------|
| `impl_cp` | CP-0083 |
| `design_cp` | CP-0081 |
| `prior_cp` | CP-0082 |
| `phase` | R2 |
| `LIVE_API_ENABLED` | false (permanent) |
| `m1_status` | NO_CONSENSUS_YET |
| `n_judges` | 2 |
| `abort_gt_accept` | ABORT_GT_ACCEPT |
| `mesh_accept` on advisory / dual | false (permanent) |
| `r3_r5_authorized` | false |

---

## Judge ids

| Id | Mode |
|----|------|
| `judge:gemini-free` | real_http (gated) or mock_local |
| `judge:mock-local` | mock_local (deterministic) |

---

## Negative / RV descriptor IDs

| ID | Intent | Expected |
|----|--------|----------|
| **T-fa-r2-a** | refuse default / live off | `ENGINE_DISABLED`; zero network; `mesh_accept=false` |
| **T-fa-r2-b** | I5 armed compose | ABORT; Refuse binding; zero post-kill network; restore False |
| **T-fa-r2-c** | ABORT > ACCEPT | Mesh `POLICY_ABORT` even when judges claim ACCEPT |
| **T-fa-r2-d** | conflict | `JUDGE_CONFLICT` ABORT; escalate I5; no auto-majority |
| **T-fa-r2-e** | missing judge | `JUDGE_MISSING` ABORT; never invent ACCEPT |
| **T-fa-r2-f** | agree ≠ M1 | `ADVISORY`; `m1_status=NO_CONSENSUS_YET`; `mesh_accept=false` |
| **T-fa-r2-g** | live+mock-bound | Both judges bound; real HTTP only if gates; honest quota doc |
| **T-fa-r2-h** | module fence | Canary + LHT + R2 module constants False; RefuseTransport final |

---

## Auth record shape (`mesh.judge.full_adapter_r2_multi_judge_auth/v0`)

```
authorized: true
phase: R2
authorizes: [R2 multi-judge live/mock-bound RV, optional one real HTTP under fences]
does_not_authorize: [R3, R4, R5, permanent LIVE, F4 invent, M1 claim N=2, NO_HELD, push/tags/secrets]
permanent_live_enable: false
m1_status: NO_CONSENSUS_YET
n_judges: 2
```

---

## Suite shape (`mesh.judge.full_adapter_r2_multi_judge_suite/v0`)

```
ok: bool
descriptors: [ComposeResult…]
checklist: [MJ/REF/I5/FENCE rows]
authorization: auth record
gates: runbook gate check (no secrets)
LIVE_API_ENABLED_module_final: false
m1_status: NO_CONSENSUS_YET
real_http_used: bool
r3_r5_authorized: false
binding_final: RefuseTransport
```

---

*End full_adapter_r2_multi_judge_v0 — R2 descriptors only.*
