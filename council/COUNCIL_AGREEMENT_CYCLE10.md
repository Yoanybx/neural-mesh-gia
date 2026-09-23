# Consejo Ciclo 10 — Router R1 Capability-aware

| Voz | NEXT |
|-----|------|
| ChatGPT | **A)** R1 Capability-aware → CP-0014 → then Phase 4 |
| DeepSeek | **A)** R1 (finish STUB) → CP-0014 → then Phase 4 + TLS |
| Grok | **A** unificado |

## Plan
P0 Doc: capability schema versioned; TTL/staleness; determinism extends with cap_state_fp; no-match = ERROR never silent RR fallback
P1 CapabilityRegistry in C-RAM (op_id+epoch+trace_id)
P2 CapabilityAwareStrategy real (replace STUB); score = match+resource_fit+health−unavailable; deterministic
P3 CLI `--strategy rr|capability`; explain with factors/scores
P4 Staleness TTL reject; fail-closed
P5 Keep R0 safety+persist-ack+audit; policy_hash changes with strategy
P6 Bench N=1000 RR vs R1 metrics (no declare winner); 1000× determinism; update prop < T_conv; p99 <8ms
P7 ≥185 tests (ChatGPT ≥180); audit; **CP-0014**; version 0.10.0

NO: Phase 4, TLS, ML, Raft, N>2, silent RR fallback on mismatch.
