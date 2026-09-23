A) APROBADO — Ciclo 8 = Phase 3 Cognitive Router R0 → CP-0012.

El endurecimiento OOP de C-RAM replica ya tiene suficiente evidencia para avanzar. Los resultados indican que la capa de transporte/recuperación está estable para introducir una primera capa de decisión de tareas.

No bloquearía Router R0 por TLS todavía; lo mantendría como deuda explícita y registrado en backlog antes de cualquier despliegue multi-host real.

## Ciclo 8 — Cognitive Router R0

### P0 — Interfaces base
Crear:

    src/neural_mesh/router/
    ├── models.py
    ├── router.py
    ├── policy.py
    └── metrics.py

Modelos:

    TaskSpec: task_id objective priority resource_requirements safety_level state_refs
    RouteCandidate: node_id available capabilities load
    RouteDecision: task_id selected_node strategy reason timestamp

### P1 — Algoritmo R0
Implementación:

    TaskSpec | candidate filter | Round Robin deterministic | RouteDecision

Reglas:

- Nodo unavailable → excluir.
- Nodo sin capacidad mínima → excluir.
- Safety policy bloquea → ERROR.
- Mismo input + mismo seed → misma decisión.

### P2 — Integración Twin + C-RAM
Flujo esperado:

    Task | Router R0 | Node selected | C-RAM locality lookup | Twin execution | Checkpoint

No introducir todavía:

- aprendizaje,
- predicción,
- optimización,
- coste energético.

### P3 — Seguridad y auditoría
Añadir:

    mesh router explain <task_id>

Salida:

    { "task_id":"task-001", "decision":"node-02", "strategy":"ROUND_ROBIN", "excluded_nodes":[ { "node":"node-03", "reason":"UNAVAILABLE" } ] }

### P4 — Benchmark N=1000
Medir:

    routing_latency p50 p99 distribution_balance rejected_tasks decision_reproducibility

Objetivo:

- determinismo 100%
- sin decisiones inválidas
- overhead documentado

### Tests mínimos:

    test_taskspec_validation test_route_decision_schema test_round_robin_sequence test_round_robin_seed_reproducible test_unavailable_filtered test_safety_block test_no_candidate_error test_router_twin_integration test_router_cram_integration test_benchmark_reproducible

Target:

    pytest >=125 audit PASS CP-0012 VERIFIED

## Sobre los reportes de ChatGPT/DeepSeek
No puedo acceder a ese enlace privado de ChatGPT ni leer directamente archivos de tu máquina:

    /workspace/neural-mesh-gia/council/CHATGPT_REPLY_CYCLE7.md
    /workspace/neural-mesh-gia/council/DEEPSEEK_REPLY_CYCLE7.md

Si el Grok Bot pega aquí los primeros 250 caracteres de cada archivo, puedo compararlos y ratificar si hay divergencias entre los tres consejos.

**Estado aceptado: comenzar Ciclo 8 — Cognitive Router R0.**
