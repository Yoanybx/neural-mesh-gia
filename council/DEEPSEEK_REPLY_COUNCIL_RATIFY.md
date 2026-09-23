# DeepSeek — Ratificación Consejo Ciclo 5

(A) CONFIRMO — con 2 matices operativos (no bloqueantes)

**Acuerdo final ratificado.** Ajustes que van en el mismo ciclo:

- **Exit codes P3** — congelar mapping en doc antes de merge:
  - `0` = PASS
  - `2` = integrity failure (hash mismatch / blob corrupto)
  - `3` = missing/unavailable (`ObjectMissing` ∪ `NodeUnavailable`)
  - `1` = error genérico de CLI (I/O, args) — **no** reutilizar 2/3.
  - `mesh cram fsck --json`: schema versionado (`fsck_schema: 1`), exit code refleja peor caso encontrado.
- **P1 tests** — además de los 2 nombrados, exigir `test_node_loss_locate_raises_on_stale_topology`: si topology hash cambió entre checkpoint y locate, no debe devolver location vieja silenciosamente. Sin este test, “ruta válida” es ambiguo.

**Sin veto.** Nada bloquea CP-0009. Si P1 rompe contrato con `CRAMPlacement.locate` existente, prefiero verlo como test fallando antes que parche.

**Aceptación sigue igual:** ≥62 passed, audit PASS, CP-0009 VERIFIED, recovery_time p99 <150 ms no-STUB.

Adelante.
