## Veredicto Ciclo 7

**APROBADO.** 111 passed, CP-0011 verde, OOP 6.75× < 10×, dual-primary 0, T_conv 0.007s. TLS como deuda explícita es aceptable en AF_UNIX local. Base sólida para Phase 3.

## Ciclo 8 → (B) APROBADO CON CAMBIOS

Razón única: "Router determinista" es una **afirmación falsable** y el plan de ChatGPT no exige el artefacto que la prueba. Sin `policy_hash + seed` congelados y comparación byte-a-byte, "determinista" es marketing. Además, la decisión de ruteo debe ser **auditable por C-RAM** — si no, el Router queda fuera del modelo de consistencia que costó Ciclos 5–7.

### Cambios exigidos (no bloquean P0, sí el merge)

1. **Contrato de determinismo congelado en doc P0**: `RouteDecision = f(policy_hash, seed, TaskSpec)` byte-identical. Sin esto, no hay R0 reproducible.
2. **Safety gate fail-closed**: sin ruta ⇒ `ERROR` con código tipado, **nunca** fallback silencioso. Test binario.
3. **Toda RouteDecision se persiste en C-RAM** con `op_id + epoch + trace_id`. Link explícito Twin→Router→C-RAM.
4. **Idempotencia**: mismo `op_id` ⇒ una sola decisión registrada.
5. **Saturación definida**: qué pasa en bench N=1000 cuando cola > bound (rechazo, backpressure, drop). No dejar indefinido.
6. **policy_hash versionado** y rechazo de decisiones con policy desconocida (fallar cerrado).

### Plan P0–P7

- **P0** — Doc freeze: contrato determinismo, safety fail-closed, schema TaskSpec/RouteDecision (con op_id/epoch/trace_id), policy_hash versioning, saturación.
- **P1** — Modelos `TaskSpec` + `RouteDecision` con campos de auditoría.
- **P2** — RR determinista con `policy_hash + seed`; comparación byte-identical en test.
- **P3** — Safety gate fail-closed + errores tipados.
- **P4** — Persistencia de decisiones en C-RAM (usa CAS + op_id idempotente).
- **P5** — Integración Twin+C-RAM+R0 end-to-end.
- **P6** — Bench N=1000: p50/p99 routing, saturación, comportamiento bajo cola llena.
- **P7** — Audit + **CP-0012**.

### Criterio de aceptación (medible)

- Determinismo: 1000 corridas con mismo `(policy_hash, seed, TaskSpec)` ⇒ **0 divergencias byte-level**.
- Safety: 0 fallbacks silenciosos en suite de safety (≥8 casos, incluido policy desconocida).
- Auditoría: 100% de RouteDecision recuperables vía C-RAM `get(op_id)`; epoch consistente.
- Idempotencia: 100 reintentos mismo op_id ⇒ 1 decisión.
- Latencia routing p99 < **5 ms** (in-process, AF_UNIX).
- Suite ≥ **130 passed**; audit PASS; **CP-0012 VERIFIED**.

### Qué NO hacer en Ciclo 8

- No ML, no embeddings, no aprendizaje, no adaptive routing.
- No Router v1 (SLO-aware, priority classes, weighted).
- No implementar TLS (sigue como deuda explícita).
- No N>2, no Raft, no quórum real.
- No tocar esquema de checkpoint sin migración.

Adelante con P0; gate de merge en P0 (contrato de determinismo congelado) antes de P1.
