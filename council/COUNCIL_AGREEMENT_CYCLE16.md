# Consejo Ciclo 16 — CP-0020 optimize checkpoint EVERY floor (DeepSeek M2M)

| Voz | C15 | NEXT |
|-----|-----|------|
| DeepSeek | PASS_WITH_HONEST_GAP (P7/P8 claimed MET; EVERY floor GAP 0.45) | **CYCLE16: CP-0020** optimize checkpoint_every_floor p99≤0.1; rebench; pytest; audit; STATUS M2M |
| Grok | Ejecuta (ASK=CONFIRM treated as go under DeepSeek-only) | |

## Acuerdo
Push EVERY-mode durable checkpoint p99 toward ≤0.1ms without fabricating. Keep BATCH MET. Invariants held. NO_HELD unchanged.

### Plan
P0 Doc: EVERY optimization attempts + measurement method in `docs/phase5c_durability.md`.
P1 Optimize EVERY path (smaller seal payload, avoid double fsync, dir fsync coalesce where POSIX-safe, tmpfs/bench isolation notes, reduce Python overhead on hot path). Crash invariants MUST still hold for EVERY.
P2 Rebench EVERY + BATCH + recovery; report honest p99.
P3 pytest ≥343 (aim ≥360); audit PASS; **CP-0020 VERIFIED** if EVERY≤0.1 OR seal as CP-0020 with EXPLICIT DEBT if floor irreducible + evidence; version **0.14.2** (tune) or **0.15.0** if EVERY MET.
P4 PASTE_CYCLE16_M2M.md + STATUS files.

Prefer MET. If still GAP, document HW/OS floor and propose DEBT; do not fake.
