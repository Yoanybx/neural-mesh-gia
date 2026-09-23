# Consejo Ciclo 14 — CP-0018 Durability & Adversarial Partition (DeepSeek-only)

| Voz | C13 | NEXT C14 |
|-----|-----|----------|
| DeepSeek | **APROBADO** CP-0017 | **CP-0018** Durability & Adversarial Partition Hardening → ≥320 tests, v0.14.0 |
| ChatGPT | (dormido) | — |
| Grok | Ejecuta DeepSeek | N≤2, single-primary, sin Raft |

## Acuerdo

**Phase 5C — Durability & Adversarial Partition Hardening → CP-0018 / 0.14.0 / pytest ≥320.**

### Nota DeepSeek (no bloqueante C13)
Si la fault matrix C13 no cubría partición de red real de punta a punta, **primer gate de CP-0018** = partition suite explícita.

### Plan
P0 Tag/baseline C13; doc `docs/phase5c_durability.md` (WAL/fsync policy, crash invariants, N=2 partition fail-closed).
P1 WAL/fsync policy explícita + crash-recovery invariants formales (post-kill -9).
P2 Partition suite: isolated minority accepts **0** writes; stale-epoch under partition; dual-primary=0; deterministic reconcile on heal (fenced promote + epoch/hash — NOT Raft quorum; for N=2 “majority” = fenced primary side / heal path only).
P3 Snapshot compaction seguro (no corrupt / no lose verified state).
P4 CLI: `mesh cram durability check | partition test | recovery trace`.
P5 Bench: crash + partition + reconnect; 10k/1k/100; experiments/phase5c-durability-c14/ + snapshot.
P6 pytest ≥320; audit PASS; **CP-0018 VERIFIED**; CP-0001..0017 still VERIFIED; version 0.14.0.

### SLO targets (honest; measure same method as C13 where possible)
- Recovery p99 ≤ 2 ms (stretch vs prior path)
- Checkpoint ≤ 0.1 ms
- Conflict detect ≤ 0.1 ms
- Dup suppress 100%; stale reject 100%; dual-primary 0; minority writes accepted 0

### NO
Raft, N>2, multi-primary, ML/R2/R3, plaintext, Vault-ACME required, GIA/AGI, physical/industrial claims.
