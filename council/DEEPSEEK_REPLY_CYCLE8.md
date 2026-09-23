Veredicto Ciclo 8

APROBADO. Determinismo congelado, persistencia C-RAM con op_id+epoch+trace_id, p99 2.60ms < 5ms, CP-0012 verde, 142 passed. Deltas aplicados correctamente.

NEXT → (C) Ciclo 9 corto de endurecimiento R0↔C-RAM, luego R1

Razón única y técnica: R0 escribe cada decisión en C-RAM, pero la suite no prueba qué pasa cuando C-RAM (OOP, socket) cae a mitad de routing. En R0 actual, fail-closed es una afirmación, no un test con fallo real. Saltar a R1 o Phase 4 apila features sobre una frontera no verificada. Es el mismo patrón que Ciclo 7 resolvió para réplica; ahora toca resolverlo para Router→C-RAM.

Además hay 2 decisiones abiertas que conviene cerrar ya: TLS debt (¿aceptable hasta Phase 4 o se arrastra?) y rejected 100/1000 (¿es saturación esperada o fuga de capacidad?).

Cambios exigidos
- Frontera R0↔C-RAM probada con fallo real: kill -9 al proceso C-RAM mid-decision ⇒ Router falla cerrado con código tipado, no decisión fantasma sin persistir.
- Durabilidad de decisión: crash del Router tras DecisionStore.put y antes de responder ⇒ al restart, op_id reaparece idempotente.
- Explicar 100/1000 rejected: clasificar (saturación legítima vs bug). Documentar bound de cola y política de rechazo.
- TLS: decidir formalmente — (a) aceptar deuda hasta Phase 4 con timestamp de vencimiento, o (b) cerrar en este ciclo. No dejar indefinido.

Plan P0–P5 (Ciclo 9, corto)
- P0 — Doc freeze: fallo C-RAM mid-route, semántica de decisión fantasma, bound de cola, decisión TLS.
- P1 — Guard: RouteDecision solo se emite tras ack persistente de C-RAM. Sin ack ⇒ ERROR tipado.
- P2 — Crash tests: kill -9 C-RAM mid-decision, restart Router, idempotencia.
- P3 — Clasificar y arreglar rejected 100/1000 (o documentar como política).
- P4 — Bench con C-RAM sano + C-RAM caído (fail-closed latency p99).
- P5 — Audit + CP-0013.

Criterio de aceptación
- 0 decisiones fantasma en 100 kill -9 mid-decision (pass/fail binario).
- Idempotencia: 100 reintentos mismo op_id ⇒ 1 decisión persistida, incluso tras restart.
- Rejected 100/1000 clasificado: 100% justificado por bound declarado o reducido a 0 con fix.
- Fail-closed p99 < 10 ms cuando C-RAM caído.
- Suite ≥160 passed; audit PASS; CP-0013 VERIFIED.

Qué NO hacer en Ciclo 9
- No R1, no Phase 4, no ML, no adaptive routing.
- No N>2, no Raft.
- No cambiar contrato de determinismo de R0.
- No implementar TLS sin decisión P0 (evitar trabajo silencioso).

Después (Ciclo 10): R1 capability-aware o Phase 4, con CP-0013 verde.
