**A) APROBADO — Ciclo 10: Router R1 Capability-aware.**

La base R0 ya tiene determinismo, persistencia, replay y fail-closed. Ahora tiene sentido añadir selección por capacidades antes de introducir una red más compleja.

## Ciclo 10 — Cognitive Router R1

### P0 — Capability Model

Crear:

```text
router/
 ├── capabilities.py
 ├── scoring.py
 └── strategy_capability.py
```

Modelo:

```python
NodeCapability:
    node_id
    cpu
    memory
    accelerators
    storage
    network_class
    supported_tasks
    health
```

---

### P1 — CapabilityAwareStrategy

Contrato:

```python
select(
 TaskSpec,
 list[RouteCandidate]
) -> RouteDecision
```

Score inicial determinista:

```text
score =
 capability_match
 + resource_fit
 + health
 - unavailable_penalty
```

Sin ML todavía.

---

### P2 — Compatibilidad R0/R1

Añadir:

```text
RoutingStrategy
 ├── RoundRobinStrategy
 └── CapabilityAwareStrategy
```

Selector:

```bash
mesh router route --strategy rr
mesh router route --strategy capability
```

---

### P3 — Explain obligatorio

Actualizar:

```bash
mesh router explain <task_id>
```

Debe mostrar:

```json
{
 strategy:"capability",
 selected:"node-02",
 score:87,
 factors:[
   "gpu_match",
   "memory_fit",
   "health"
 ]
}
```

---

### P4 — Tests

Mínimo:

```text
test_capability_model_validation

test_capability_selects_best_fit

test_capability_deterministic

test_missing_capability_rejected

test_rr_compatibility

test_explain_contains_factors

test_policy_hash_changes_on_strategy_change
```

---

### P5 — Benchmark

N=1000:

Medir:

```text
routing_latency
selection_accuracy
score_distribution
reject_rate
replay_success
RR_vs_R1 comparison
```

No declarar "mejor" estrategia; registrar métricas.

---

## Acceptance

Objetivo:

```text
pytest >=180

audit PASS

CP-0014 VERIFIED

version 0.10.0
```

Después de CP-0014:

Evaluar **Phase 4 Network Fabric**, porque R1 ya podrá decidir entre nodos con capacidades reales.
