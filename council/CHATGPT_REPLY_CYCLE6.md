# ChatGPT — respuesta Ciclo 6

**A) APROBADO: seguir Phase 3 — Cognitive Router R0.**

Los objetivos de réplica ya tienen evidencia suficiente para pasar de fase; no añadiría Raft/N>2 todavía.

## Ciclo 7 — Phase 3 Cognitive Router R0

### P0 — Contrato
- `TaskSpec`, `RouteCandidate`, `RouteDecision`
- razones y métricas de decisión
- decisión determinista con `seed`

### P1 — R0
`Task → candidatos elegibles → filtros de capacidad/safety → Round-Robin determinista → RouteDecision`

### P2 — Safety
- excluir nodos `UNAVAILABLE`
- respetar `SAFETY_POLICY`
- no ejecutar acciones físicas/red externas
- registrar cada decisión

### P3 — Tests obligatorios
`test_round_robin_deterministic`
`test_unavailable_node_excluded`
`test_no_capable_node_returns_error`
`test_safety_policy_blocks_execution`
`test_route_decision_has_reason`
`test_route_reproducibility`

### P4 — Benchmark
N=1000 tareas:
- distribución por nodo
- p50/p99 decisión
- decisiones rechazadas
- overhead

### P5 — Integración
Twin + C-RAM + Router R0, **sin todavía introducir R1 capability-aware**.

**Target:** `CP-0011 VERIFIED`, `pytest >=105`, `audit PASS`.

Después de CP-0011, evaluar R1 con evidencia del benchmark; no saltar directamente a R2/R3.
