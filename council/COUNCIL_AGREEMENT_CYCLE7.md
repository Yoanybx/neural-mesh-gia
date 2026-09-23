# Consejo — Ciclo 7 (resolución de divergencia)

**Fecha:** 2026-09-23 America/New_York (EDT)

## Divergencia
| Voz | NEXT |
|-----|------|
| ChatGPT | **A)** Ciclo 7 = Phase 3 Cognitive Router R0 → CP-0011 |
| DeepSeek | **B)** Ciclo 7 corto = réplica out-of-process + crash/socket → CP-0011; Phase 3 = Ciclo 8 |
| Grok Bot | **Adopta B luego A:** DeepSeek tiene razón en la deuda de boundary; ChatGPT tiene razón en no alargar réplica infinitamente |

## Acuerdo Ciclo 7 (corto, DeepSeek)
Out-of-process replica transport; NO Phase 3 aún; NO Raft/N>2/ML/TLS.

P0 Doc: socket frontier, framing, backpressure, timeouts; TLS=deuda explícita  
P1 `mesh cram replica serve` + Unix socket + size-limited framing; in-process = test-only mode  
P2 Crash: kill -9, mid-frame cut, rejoin < T_conv; ≤1 writable primary  
P3 CLI serve|connect --socket  
P4 Bench OOP overhead p99 <10×; audit; **CP-0011 VERIFIED**; pytest ≥110

## Ciclo 8 (reservado, plan ChatGPT)
Phase 3 Cognitive Router R0 (TaskSpec/RouteDecision, RR determinista, safety, bench N=1000, Twin+C-RAM+R0) → **CP-0012**, pytest ≥105+delta.

Si P0/C7 invalida el modelo de consistencia C6, parar y re-discutir antes de Router.
