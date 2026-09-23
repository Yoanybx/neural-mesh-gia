## Veredicto Ciclo 9
**APROBADO.** 160 passed, CP-0013 verde, 0 fantasmas/100, fail-closed 0.044ms, rejected clasificado. TLS con expiry 2026-12-31 queda como deuda trazable — aceptable.

## NEXT → **(A) Router R1 capability-aware**

Razón única: `CapabilityAware STUB only` es **trabajo inacabado de R0**, no una feature nueva. Ir a Phase 4 con router RR + stub de capability = fabric con cerebro simulado. Además, R1 es prerequisito real de Phase 4 (fabric sin enrutamiento por capacidad no tiene sentido). TLS se paga en Phase 4, como está pactado.

### Riesgos a cerrar en P0
- "Capability-aware" sin **schema versionado** = ad-hoc por nodo.
- Capabilities **stale** (nodo caído, lista vieja) ⇒ ruteo a fantasma.
- **Determinismo R0 roto**: capability state debe entrar al hash como `candidates_fp`, no como input mutable.
- **No-match silencioso**: si 0 nodos cumplen, ¿fallback RR o ERROR? Debe ser fail-closed explícito.

### Plan P0–P7
- **P0** — Doc freeze: capability schema versionado, advertisement protocol, TTL/staleness bound, extensión del contrato determinista (`f(policy_hash,seed,TaskSpec,candidates_fp,cap_state_fp)`), política no-match, decisión sobre fallback RR.
- **P1** — `CapabilityRegistry` persistido en C-RAM (op_id+epoch+trace_id, igual que DecisionStore).
- **P2** — `CapabilityAware` real (reemplaza STUB), determinista, byte-identical.
- **P3** — Staleness: TTL, rechazo de capabilities vencidas, fail-closed.
- **P4** — No-match: `ERROR` tipado, **nunca** RR silencioso.
- **P5** — Integración con pipeline R0 (safety + persist-ack + auditoría intactos).
- **P6** — Bench: capability filter, propagación de update < T_conv, no-match latency, determinismo 1000×.
- **P7** — Audit + **CP-0014**.

### Criterio de aceptación
- Determinismo: 1000 corridas mismo `(policy_hash,seed,TaskSpec,cap_state_fp)` ⇒ **0 divergencias**.
- Stale capability rechazada dentro de TTL; 0 ruteos a capability vencida.
- 0 fallback RR silencioso cuando capability mismatch (fail-closed binario).
- Propagación de capability update < T_conv (bound P0).
- Routing p99 < **8 ms** (relajado por lookup de capability).
- Suite ≥ **185 passed**; audit PASS; **CP-0014 VERIFIED**.

### Qué NO hacer en Ciclo 10
- No Phase 4 (espera CP-0014).
- No TLS (expiry 2026-12-31 sigue válido).
- No ML, no adaptive, no self-learning capabilities.
- No N>2, no Raft.
- No tocar contrato determinista de R0 más allá de añadir `cap_state_fp` al hash.

Después (Ciclo 11): **Phase 4 Network Fabric + pago de TLS** con CP-0014 verde.