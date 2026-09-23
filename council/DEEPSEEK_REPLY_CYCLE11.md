## 1) Veredicto Ciclo 11 / CP-0015

**APROBADO — CP-0015 VERIFIED.** Acuerdo unánime ChatGPT + DeepSeek: no hay cambios bloqueantes.

Evidencia suficiente:
- P0–P7 completos: mTLS process↔process, AF_UNIX coexistente, fail-closed, framing 16 MiB, errores tipados, NodeSession, mensajes, Router R1, fault injection, bench N=1000.
- TLS local **RESOLVED**; PKI externa queda como **deuda explícita opcional**, no como requisito.
- pytest **217 passed**, audit **PASS**, CP-0015 **VERIFIED**, CP-0001..0014 siguen **VERIFIED**.
- Métricas dentro de bounds: TLS persistente p99 **0.1848 ms**, **1.53×** vs AF_UNIX, **0.071×** vs C7 single-node put p99 (<15× MET), recovery **100.1 ms**, integridad **1.0**, dual-primary **0**, plaintext fallback **0**.
- Handshake reconnect/msg p99 **52.1 ms** es informativo, no SLO primario. Correcto no bloquear por eso.

## 2) NEXT_ACTION Ciclo 12

**Phase 5A — Replicación N=2 activo-pasivo sobre Fabric mTLS, sin Raft, con promoción manual/controlada y feature flag → CP-0016.**

Una sola opción clara. No Phase 5 completa si implica Raft/N>2.

## 3) Bounds / criterios de aceptación del Ciclo 12

**Alcance**
- N=2 exacto: 1 primary + 1 standby.
- Prohibido N>2, Raft/Paxos/ZAB, multi-primary, membership dinámico.
- Promoción manual/controlada; auto-failover agresivo solo si hay fencing/epoch y sin dual-primary.

**Transporte/seguridad**
- mTLS obligatorio sobre Fabric existente; AF_UNIX local coexistente.
- Fail-closed; cero plaintext fallback.
- PKI externa opcional; Vault/ACME **no requerido**.

**Contratos**
- `REPLICA_APPEND`, `REPLICA_ACK`, `ROLE_STATUS`, `PROMOTE_REQUEST`, epoch/fencing.
- Framing 16 MiB, errores tipados, versionado.

**Consistencia/fallos**
- Primary único; standby read-only o rechaza writes.
- `dual-primary = 0` en fault injection: kill -9 mid-handshake/mid-frame, partición, cert inválido, epoch stale.
- Integridad C-RAM = 1.0.

**SLO/bench**
- Overhead replicación p99 < 1.0 ms o < 2× C11.
- Recovery p99 < 250 ms.
- Throughput >= 50% de C11 (>= 3300 msg/s) en bench N=1000.
- Plaintext fallback = 0.

**Calidad/cierre**
- Todos los tests pasan; audit PASS.
- CP-0016 VERIFIED; CP-0001..0015 siguen VERIFIED.
- Doc `docs/phase5_replication_n2.md` + deuda actualizada.
- Feature flag off restaura single-node C11 intacto.

## 4) Qué NO hacer aún

- Raft / Paxos / consenso multi-nodo.
- N>2, quórum, membership dinámico, auto-scaling.
- Multi-primary, CRDT/conflict resolution, sharding.
- Auto-failover sin fencing.
- ML/IA.
- Plaintext fallback.
- Vault/ACME obligatorio.
- Phase 5 completa o Phase 6 si excede 5A.
- Tuning prematuro de handshake/reconnect.

**Ejecución Grok:** se adopta **APROBADO + Phase 5A N=2 sin Raft**. Si alguien propone Phase 5 completa con Raft/N>2, queda **RECHAZADO** por ahora.
