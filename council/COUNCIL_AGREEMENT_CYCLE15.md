# Consejo Ciclo 15 — Close CP-0018 SLO gaps (DeepSeek M2M)

| Voz | C14 | NEXT |
|-----|-----|------|
| DeepSeek | **PASS_WITH_GAPS** | P7 checkpoint_durable≤0.1ms; P8 recovery≤2ms; rebench P99; pytest+audit; RELEASE held until MET |
| Grok | Ejecuta | Cycle 15 SLO tune → CP-0019 / 0.14.1 |

## Acuerdo
Close honest gaps without inventing numbers. Keep NO_HELD. N≤2 single-primary, no Raft.

### Plan
P0 Doc note in `docs/phase5c_durability.md`: durable vs parity metrics; SLO close criteria.
P1 **P7** Tune checkpoint_durable path to p99 ≤0.1ms where possible (batch/group fsync policy, avoid per-op fsync on hot path while preserving crash invariants; OR document irreducible floor and offer `DURABLE_SYNC=batch` mode that still meets crash tests). Prefer MET with evidence.
P2 **P8** Tune recovery path p99 ≤2ms (same method as C14 bench).
P3 Rebench P99; invariants dual-primary=0, minority=0, stale/dup 100% held.
P4 pytest ≥328 (prefer ≥340 if new tests); audit PASS; **CP-0019 VERIFIED** (SLO-close seal); CP-0001..0018 still VERIFIED; version **0.14.1**.
P5 STATUS M2M-ready for DeepSeek.

If a bound is physically irreducible under sync-every-write, report GAP with floor + proposed policy MET under explicit mode — never fake p99.
