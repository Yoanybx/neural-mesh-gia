## Veredicto Ciclo 13 / CP-0017

**APROBADO.**

CP-0017 cumple lo comprometido: versionado, epochs, conflictos, recovery formal, idempotencia, stale-write rejection, fault matrix, benchmarks y cierre.

Evidencia: 283 tests passed, audit PASS, CP-0017 VERIFIED, CP-0001..0016 siguen VERIFIED.

Métricas honestas y compatibles con lo declarado. No hay violación de directiva: sin Raft, sin N>2, sin multi-primary, sin ML/R2/R3, sin plaintext, sin GIA claims.

**Nota no bloqueante:** si la fault matrix no incluye explícitamente partición de red real, debe añadirse como primer gate de CP-0018. No invalida CP-0017, pero cierra el único hueco semántico posible.

## NEXT_ACTION Ciclo 14 — UNA opción clara

**CP-0018 — Durability & Adversarial Partition Hardening**

**Objetivo:** endurecer durabilidad post-crash y comportamiento bajo partición de red, manteniendo single-primary, N≤2 y sin Raft.

**Alcance:**

- WAL/fsync policy explícita.
- Crash-recovery invariants formales.
- Partición de red: minoría rechaza escrituras, mayoría recupera.
- Stale-epoch bajo partición.
- Snapshot compaction seguro.
- CLI: `mesh cram durability check | partition test | recovery trace`.
- Bench: crash + partición + reconexión.

**Bounds:**

- N≤2.
- Single-primary.
- Sin Raft.
- Sin multi-primary.
- Sin ML/R2/R3.
- mTLS obligatorio, sin plaintext.
- Sin Vault-ACME required.
- Sin GIA/AGI claims.

**Criterios de aceptación:**

- Recovery p99 ≤ 2 ms.
- Checkpoint ≤ 0.1 ms.
- Conflict detect ≤ 0.1 ms.
- Dup suppress 100%.
- Stale reject 100%.
- Dual-primary = 0.
- Partición minoría: 0 escrituras aceptadas.
- Reconciliación determinista post-participación.
- CP-0001..0017 sin regresión.

**Qué NO hacer:**

- No Raft.
- No N>2.
- No multi-primary.
- No R2/R3.
- No aprendizaje adaptativo.
- No memoria cognitiva completa.
- No World Model.
- No razonamiento multiagente avanzado.
- No auto-mejora.
- No autonomía física.
- No despliegue industrial.
- No afirmar GIA/AGI.

## Targets sugeridos

| Elemento | Target |
|---|---|
| Pytest | **320 passed** |
| CP | **CP-0018** |
| Versión | **v0.14.0** |
| Tag previo | `v0.13.0-cp0017-verified` |
| Bench | `experiments/phase5c-durability-c14/` |
| Audit | PASS |
| CP-0017 | Mantener VERIFIED |

**Orden de ejecución:**

1. Tag `v0.13.0-cp0017-verified`.
2. Abrir CP-0018 con `docs/phase5c_durability.md`.
3. Implementar WAL/fsync + partition tests.
4. Añadir crash-recovery invariants.
5. Bench 10k/1k/100 + partición.
6. Pytest target 320.
7. Audit y cierre CP-0018.

Grok puede ejecutar esto sin esperar a ChatGPT.
