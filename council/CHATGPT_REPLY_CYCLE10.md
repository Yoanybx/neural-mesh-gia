A) APROBADO — Ciclo 11: Phase 4 Network Fabric + cierre de TLS debt.

R1 ya tiene selección basada en capacidades, TTL y replay. El siguiente cuello de botella lógico es crear una capa de comunicación real entre nodos antes de añadir más inteligencia.

Ciclo 11 — Network Fabric v0

P0 — Transporte seguro base
Implementar:
network/
├── transport.py
├── tls.py
├── protocol.py
└── session.py

Objetivos:
- TLS habilitado.
- Identidad de nodo.
- Handshake verificable.
- Rechazo fail-closed.

Tests:
test_tls_handshake test_invalid_certificate_rejected test_node_identity_verified

P1 — Node Communication Layer
Contrato:
NodeSession: connect(node) send(message) receive() close()

Mensajes iniciales:
TASK_REQUEST STATE_QUERY STATE_RESPONSE HEARTBEAT CAPABILITY_UPDATE CHECKPOINT_NOTICE

P2 — Integración Router + Network
Flujo:
TaskSpec ↓ Router R1 ↓ selected node ↓ Network Fabric ↓ execution endpoint ↓ C-RAM checkpoint

Test:
test_router_dispatches_over_network test_network_failure_returns_error test_checkpoint_after_remote_task

P3 — Fault testing de red
Añadir:
NETWORK_TIMEOUT CONNECTION_DROP INVALID_SESSION MESSAGE_CORRUPTION

Esperado:
- sin estados fantasmas.
- sin ACK falso.
- recuperación mediante checkpoint.

P4 — Bench
N=1000 mensajes:
Medir:
latency p50/p99 TLS overhead throughput connection recovery message integrity

Comparar contra transporte local, reportando métricas.

P5 — Cierre deuda TLS
Actualizar:
docs/debt/TLS.md status: RESOLVED

Tests / Acceptance
Target:
pytest >=210 audit PASS CP-0015 VERIFIED version 0.11.0

No implementar todavía:
- Raft.
- N>2 replication.
- aprendizaje de routing.
- mesh global abierto.

Primero: red segura, medible y recuperable.
