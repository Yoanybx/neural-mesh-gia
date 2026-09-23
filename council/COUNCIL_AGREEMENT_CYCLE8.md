# Consejo Ciclo 8 — Cognitive Router R0

| Voz | Veredicto |
|-----|-----------|
| ChatGPT | **A) APROBADO** R0 → CP-0012 |
| DeepSeek | **B) APROBADO CON CAMBIOS** (determinismo falsable + C-RAM audit) |
| Grok / Usuario | Arrancar C8; aplicar cambios DeepSeek |

## Extras DeepSeek (obligatorios)
- Doc: Decision = f(policy_hash, seed, TaskSpec) byte-identical
- Safety fail-closed; saturación definida
- Persist RouteDecision en C-RAM (op_id/epoch/trace_id); idempotencia
- ≥130 tests; routing p99 <5ms; CP-0012
