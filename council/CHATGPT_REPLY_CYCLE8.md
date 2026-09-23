C) Otro NEXT concreto: endurecer la base antes de R1/Phase 4.

R0 está suficientemente validado, pero antes de añadir inteligencia de routing o red real haría un Ciclo 9 — Router R0 Hardening + Observability, corto y cerrado.

P0 — Decision audit trail completo
Implementar:
router/ ├── audit.py ├── trace.py

Cada RouteDecision debe guardar:
- task_id
- op_id
- epoch
- trace_id
- policy_hash
- candidates_fingerprint
- selected_node
- rejection_reasons
- timestamp lógico

Test:
test_route_audit_replay test_trace_id_consistency test_decision_hash_reproducible

P1 — Replay determinista
Nuevo comando:
mesh router replay <trace_id>

Debe reconstruir:
TaskSpec + candidate set + policy version + seed = misma RouteDecision

Test:
test_replay_byte_identical

P2 — Métricas Router → Benchmark
Añadir:
decision_latency queue_time reject_rate node_distribution policy_changes replay_success_rate

Integrar con el benchmark existente.

P3 — Preparar R1 sin implementarlo
Crear solamente interfaces:
class RoutingStrategy: def select(self, task, candidates): pass

Implementaciones:
RoundRobinStrategy ✅ CapabilityAwareStrategy STUB

No activar R1 todavía.

P4 — Tests + checkpoint
Objetivo:
pytest >=155 audit PASS CP-0013 VERIFIED

Después de CP-0013, la siguiente decisión sería:
- R1 Capability-aware si se quiere mejorar selección interna.
- Phase 4 Network Fabric si se quiere pasar a nodos/red.

Mi recomendación de orden técnico:
R0 Hardening ↓ R1 Capability-aware ↓ Network Fabric
porque el router será la capa que decidirá cómo usar esa red.
