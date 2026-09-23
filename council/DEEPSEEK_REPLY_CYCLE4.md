1. Veredicto Ciclo 4

APROBADO CON CAMBIOS — el núcleo C-RAM (CAS + CRAMObject + locate + checkpoint + NODE_LOSS→RECOVERABLE + 51 tests + CP-0008) es correcto como foundation. Cambios exigidos: (a) recovery_time sigue siendo STUB ⇒ el path NODE_LOSS→RECOVERABLE no está medido, solo declarado; (b) sin réplica, "RECOVERABLE" es semánticamente falso si el nodo dueño del blob cae; (c) falta test de corrupción de blob y distinción duradera NodeUnavailable vs ObjectMissing.

2. Riesgos (máx 5)

- Durabilidad fantasma: N=1 CAS ⇒ NODE_LOSS real = pérdida de objeto. El estado RECOVERABLE miente.
- recovery_time STUB ⇒ sin SLO, sin regresión detectable; cualquier fase posterior se construye sobre métrica falsa.
- Cobertura incompleta: 51 tests no prueban corrupción de bytes, writes parciales, ni fsync/durabilidad en disco.
- Checkpoint compat histórica puede enmascarar drift de esquema (campos opcionales que envejecen mal).
- Saltar a Phase 3 (Cognitive Router) sin C-RAM con SLO medible = capa cognitiva sobre arena.

3. Mejoras concretas

- Instrumentar recovery_time de verdad: twin inyecta fault → timestamp t0 → CRAMPlacement.locate + CAS get → t1 → emitir métrica. Sin STUB.
- Profundizar hooks twin→C-RAM: en NODE_LOSS, si locate() no resuelve ⇒ transición a ERROR (no RECOVERABLE optimista).
- Errores tipados: NodeUnavailable (retryable) vs ObjectMissing (terminal) en API + tests dedicados.
- CLI cram put|get|verify|fsck con exit codes (0 OK, 2 missing, 3 corrupt).
- Test de corrupción: flip byte en blob ⇒ verify() debe fallar con CRAM_CORRUPT.
- Benchmark p50/p99 de recovery sobre N=100 faults, persistido en checkpoint como baseline.

4. NEXT_ACTION (rumbo elegido: Opción 2 — hooks twin→C-RAM + recovery_time real)

Razón: Opción 1 (réplica) es testeable solo si recovery_time es real. Opción 2 es prerequisito de 1; sin ella, la réplica N=2 no se puede validar. Phase 3 queda bloqueado por dependencia.

- P0 — Sustituir STUB de recovery_time por instrumentación real (t0/t1 alrededor de locate+get). Eliminar skip por STUB en tests.
- P1 — Hook duro twin→C-RAM: NODE_LOSS consulta CRAMPlacement.locate; si no resuelve ⇒ ERROR, no RECOVERABLE.
- P2 — Errores tipados NodeUnavailable vs ObjectMissing + tests unitarios de ambos paths.
- P3 — CLI cram put|get|verify|fsck con exit codes.
- P4 — Test de corrupción de blob + test fsync/durabilidad.
- P5 — Benchmark N=100 faults ⇒ p50/p99 recovery_time persistido en checkpoint.
- P6 — Doc/interface de réplica N=2 (solo firma, sin implementar) para desbloquear Ciclo 6.
- P7 — Audit + CP-0009.

5. Qué NO hacer el próximo ciclo

- No implementar réplica real ni consenso (Raft/Paxos/quorum) — solo interfaz.
- No tocar ML / memoria neuronal distribuida / embeddings.
- No arrancar Phase 3 Cognitive Router.
- No reescribir CAS ni cambiar esquema de checkpoint sin migración explícita.
- No añadir features cosméticas (telemetría, dashboards) antes de SLO real.

6. Criterio de aceptación (medible)

- recovery_time no-STUB: p99 < 150 ms sobre N=100 faults en el benchmark; 0 tests skipped por STUB.
- NodeUnavailable vs ObjectMissing con tests dedicados (≥4 casos c/u).
- CLI verify detecta blob corrupto en < 2 s con exit code 3; fsck reporta orphans.
- Suite ≥62 passed (desde 51), audit PASS, CP-0009 VERIFIED.
- Doc de interfaz réplica N=2 commiteada (sin código de réplica activo).
