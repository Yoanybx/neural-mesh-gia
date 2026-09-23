# Consejo Ciclo 9 — R0 Hardening + Observability

| Voz | NEXT |
|-----|------|
| ChatGPT | **C)** R0 Hardening + Observability → CP-0013; luego R1 luego Network |
| DeepSeek | **C)** R0↔C-RAM crash frontier → CP-0013; luego R1/Phase4 |
| Grok | **Unir ambos** |

## TLS (P0 decision)
**Aceptar deuda hasta Phase 4** con vencimiento documentado **2026-12-31**; no implementar TLS en C9.

## Plan unificado
P0 Doc: mid-route C-RAM failure, phantom decision semantics, queue bound, TLS expiry  
P1 Guard: emit RouteDecision only after C-RAM persist ack; else typed ERROR  
P2 Crash: kill -9 C-RAM mid-decision; Router restart; op_id idempotent; 0 phantoms/100  
P3 Audit trail + `mesh router replay <trace_id>` byte-identical  
P4 Classify/document rejected 100/1000 (bound policy)  
P5 Metrics + bench healthy + C-RAM-down fail-closed p99 <10ms  
P6 RoutingStrategy interface; RoundRobin ✅; CapabilityAware **STUB only**  
P7 ≥160 tests; audit; **CP-0013 VERIFIED**

NO: R1 active, Phase 4, ML, Raft, N>2, change R0 determinism contract, silent TLS.
