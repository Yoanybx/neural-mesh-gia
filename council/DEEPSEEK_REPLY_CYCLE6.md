# DeepSeek — respuesta Ciclo 6

## Veredicto Ciclo 6
**APROBADO.** Todos los criterios cumplidos con margen (T_conv 0.00425s, p99 4.18× < 5×, 0/100 dups, CP-0010 VERIFIED).

## NEXT → (B) APROBADO CON CAMBIOS — 1 ciclo corto de endurecimiento, luego Phase 3

Razón única y técnica: la réplica es **in-process**. Los tests de partición/split-brain simulan pero **no cruzan un boundary real** (proceso, socket, FS). Pasar a Phase 3 Cognitive Router sobre una réplica que nunca ha visto un EOF de socket es deuda estructural. Pero no merece un ciclo completo — merece un ciclo de 1 semana para cerrar el gap, y después Phase 3 sin excusas.

## Cambios exigidos (Ciclo 7, corto)
- **Out-of-process replica:** 2 procesos `mesh cram replica serve` comunicándose por Unix socket + framing con límite de tamaño. In-process queda como modo test-only.
- **Partición adversarial real:** `kill -9` al secundario mid-write, cortar socket en medio de un frame, rejoin. Test binario: **≤1 primary writable** sobrevive.
- **Durabilidad cruzando proceso:** `fsync` antes de ack en primario; test de crash-restart con op_id reapareciendo.

## Plan P0–P4 (Ciclo 7, deliberadamente corto)
- **P0** — Doc freeze: frontera socket, framing, backpressure, timeouts. Sin código.
- **P1** — `replica serve` proceso + socket transport + framing con límite.
- **P2** — Crash tests: kill -9, socket cut mid-frame, rejoin converge < T_conv.
- **P3** — CLI `mesh cram replica serve|connect` + `--socket` path.
- **P4** — Benchmark out-of-process overhead; audit; **CP-0011**.

## Criterio de aceptación (Ciclo 7)
- Partición real (kill -9 + socket cut): **0 escenarios con 2 primaries writable** (pass/fail binario).
- Rejoin desde crash mid-frame converge sin corrupción; op_id duplicados siguen 0/100.
- Overhead p99 out-of-process < **10×** (relajado por IPC real; in-process <5× se mantiene en modo test).
- Suite ≥ **110 passed**; audit PASS; **CP-0011 VERIFIED**.

## Qué NO hacer en Ciclo 7
- No N>2, no Raft, no quórum real, no Byzantine.
- No Phase 3 todavía.
- No ML / embeddings.
- No TLS/auth en socket aún (documentar como deuda explícita, no silenciosa).

## Después (Ciclo 8, no ahora)
Phase 3 Cognitive Router R0, asumiendo CP-0011 verde. Si P0 del Ciclo 7 revela que el boundary real invalida el modelo de consistencia congelado en Ciclo 6, entonces sí paramos y re-discutimos — pero no antes.

Adelante con P0.
