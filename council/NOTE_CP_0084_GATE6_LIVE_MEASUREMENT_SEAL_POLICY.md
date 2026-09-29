# NOTE — CP-0084 Phase R3 Gate6 live-measurement seal policy

- **Date:** 2026-09-28 ~23:14 EDT (America/New_York)
- **Author:** Grok Bot `<grok-bot@local>`
- **Tip base:** `56cdaa0` (CP-0083 R2 DONE)
- **CP:** **CP-0084** — measurement/policy authorizing **R3 only**
- **Authority:** CP-0081 §4 Phase R3 · operator R3 authorize · Gate1 ENABLE_UNDER_FENCES

## What landed

| Item | Path |
|------|------|
| R3 policy | `docs/planning/MESH_FULL_ADAPTER_R3_GATE6_SEAL_POLICY.md` |
| CP seal | `docs/planning/IMPL_CP_0084_GATE6_LIVE_MEASUREMENT_SEAL_POLICY.md` |
| Schema | `docs/schema/judge/full_adapter_r3_gate6_seal_policy_v0.md` |
| Packaging | `src/neural_mesh/packaging/l_judge_full_adapter_r3_gate6_seal_policy.py` |
| Tests | `tests/test_full_adapter_r3_gate6_seal_policy_cycle80.py` |
| Evidence | `docs/planning/EVIDENCE_CP_0084_GATE6_LIVE_MEASUREMENT_SEAL_POLICY.md` |
| Ledger | `snapshots/CP-0084/r3_gate6_seal_policy_suite_ledger.json` |

## Policy (español-friendly)

- **seal_candidate** = SÍ (pack n=6: 1 real + 5 mock)
- **Gate6 live-measurement seal** = NO / OPEN (necesita n_real_http ≥ 3; hoy **2**)
- **Product seal** = NO (F4 UNSIGNED + live-measurement)
- R3 sella la **política** + 1 HAPPY real incremental; LIVE queda **False**
- R4 OPEN (streaming); R5 OPEN (F4 operador)

## Fences held

- Does **not** permanently enable live · `LIVE_API_ENABLED=False` final  
- Does **not** authorize **R4–R5** · no Gate6 final / product seal claim  
- Does **not** invent F4 · ACK stays **UNSIGNED**  
- No secrets · no push/tags · **NO_HELD unchanged**

## Honest 「listo」 remainder

| Track | Status |
|-------|--------|
| Bajo fences | **YES** |
| Full-adapter RV | **OPEN** — R0–R3 done; **R4 OPEN** |
| Product permanent | **NO** — F4 ACK unsigned; prefer leave False |

**Next:** R4 streaming DEFER/RV — **not** authorized here. Prefer leave LIVE False.
