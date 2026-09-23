**A) Confirmo el NEXT_ACTION propuesto, con una pequeña reordenación de prioridades para mantener la arquitectura limpia.**

El Ciclo 1 cumplió correctamente la función de crear la base de continuidad. Antes de pasar a C-RAM, conviene cerrar el Digital Twin como plataforma experimental reproducible. El objetivo del Ciclo 2 debe ser que cualquier agente pueda repetir un experimento de red/fallos y obtener el mismo resultado desde un checkpoint.

## CICLO 2 — Digital Twin Experimental Hardening

### Prioridad P0 — Fault Injection determinista

Implementar:

```
src/neural_mesh/twin/
    faults.py
    events.py
    simulator.py
```

Interfaces:

```python
class FaultEvent:
    event_id: str
    fault_type: str
    target_id: str
    tick: int
    seed: int
    parameters: dict
```

Tipos iniciales:

```python
NODE_LOSS
PACKET_DROP
PACKET_DELAY
```

Ejemplo:

```json
{
  "event_id": "fault-0001",
  "fault_type": "NODE_LOSS",
  "target_id": "node-03",
  "tick": 100,
  "seed": 42
}
```

Requisito:

* Misma topología.
* Mismo workload.
* Mismo seed.
* Mismo resultado.

Debe existir:

```
mesh twin run \
 --topology topology.json \
 --workload workload.json \
 --faults faults.json \
 --seed 42
```

Salida:

```
experiment_id
seed
events_executed
nodes_alive
packets_sent
packets_dropped
latency_avg
checkpoint_id
```

---

# Prioridad P1 — JSON Topology Persistence

Crear:

```
src/neural_mesh/twin/schema.py
src/neural_mesh/twin/storage.py
```

Formato mínimo:

```json
{
 "network_id":"test-net-001",
 "seed":42,
 "nodes":[
   {
    "id":"node-01",
    "cpu":8,
    "memory":32000,
    "capabilities":["compute"]
   }
 ],
 "links":[
   {
    "source":"node-01",
    "target":"node-02",
    "latency_ms":5,
    "bandwidth_mbps":1000
   }
 ]
}
```

Interfaces:

```python
Topology.load(path)
Topology.save(path)
Topology.hash()
```

Requisito:

El hash de la topología debe entrar en el checkpoint.

Ejemplo:

```
CP-0004

topology_hash:
8af923...

workload_hash:
92bd11...

seed:
42
```

---

# Prioridad P2 — Benchmark Harness

Crear:

```
src/neural_mesh/benchmark/
    runner.py
    metrics.py
```

Interface:

```python
class ExperimentResult:
    experiment_id:str
    duration_ms:int
    metrics:dict
    artifacts:list
```

Métricas iniciales:

```
simulation_time
events_processed
node_failures
packet_loss
latency
throughput
recovery_time
checkpoint_overhead
```

Comando:

```
mesh benchmark run twin-basic
```

Debe generar:

```
experiments/
 └── EXP-0001/
      ├── result.json
      ├── topology.json
      ├── workload.json
      ├── faults.json
      └── checkpoint.json
```

---

# Prioridad P3 — Cerrar Acceptance Part X

Antes de Phase 2:

Añadir:

## Dirty tree gate

Nuevo comando:

```
mesh audit git
```

Debe detectar:

```
modified files
untracked files
branch
commit hash
```

Salida:

```
GIT STATUS:
PASS/FAIL
```

---

## Safety gate inicial

Crear:

```
.project_state/SAFETY_POLICY.json
```

Ejemplo:

```json
{
 "allow_network_actions":false,
 "allow_physical_actions":false,
 "require_human_approval":true
}
```

CLI:

```
mesh safety status
```

---

# Tests obligatorios antes de CP-0004

Agregar mínimo:

```
tests/test_fault_injection.py
tests/test_topology_serialization.py
tests/test_benchmark.py
tests/test_reproducibility.py
tests/test_git_gate.py
tests/test_safety_gate.py
```

Acceptance:

```
pytest
>=15 tests
0 failures

audit.sh PASS

CP-0004 VERIFIED
```

---

## Después de CP-0004

Entonces sí:

# Phase 2 — C-RAM

No empezaría C-RAM antes de esto, porque C-RAM necesitará un entorno donde podamos probar:

* pérdida de nodos,
* recuperación de estado,
* snapshots,
* migración,
* consistencia,
* rollback.

El orden recomendado queda:

```
Phase 0  Continuidad        ✅
Phase 1  Digital Twin       ✅ parcial
Cycle 2   Twin Hardening    ← ahora
Phase 2  C-RAM              después
```

Estado aceptado:

**NEXT_ACTION = Ciclo 2 Digital Twin Hardening con Fault Injection + JSON Persistence + Benchmark Harness + cierre Acceptance Part X.**
