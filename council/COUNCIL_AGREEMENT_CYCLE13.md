# Consejo Ciclo 13 — Phase 5B Consistency & Recovery Hardening (DeepSeek-only mode)

| Voz | C12 | NEXT C13 |
|-----|-----|----------|
| ChatGPT | APROBADO CP-0016 | Phase 5B Consistency & Recovery → CP-0017 ≥280 |
| DeepSeek | Congelar C12; abrir CP-0017 (9 WS) | Versionado, epochs, conflictos, recovery, idempotencia, stale reject, partición, bench, docs |
| Grok | Síntesis 5B | Ejecutar ahora (ChatGPT dormido ~24h; DeepSeek-only) |

## Acuerdo unificado

**Phase 5B — C-RAM Consistency & Recovery Hardening → CP-0017, v0.13.0, pytest ≥280.**

Build on C12 N=2 + Fabric. Keep dual-primary=0. No Raft / N>2 / multi-primary / ML.

### Plan
**P0** Doc freeze `docs/phase5b_consistency.md` (version model, conflict policy, recovery FSM, fail-closed partition for N=2).
**P1** Versioning: `cram/version.py`, `consistency.py`, `conflict.py` — CRAMVersion(object_id, epoch, sequence, hash, timestamp, origin_node). Same id+hash = idempotent; same id+diff hash = explicit conflict; lesser epoch = reject.
**P2** Recovery protocol: RECOVERY_REQUEST/RESPONSE/VERIFY/COMMIT — detect → locate replica → verify hash → promote (fenced) → checkpoint → resume writes.
**P3** CLI: `mesh cram consistency check`, `mesh cram recovery test`, `mesh cram history <object>` (+ keep `mesh cram trace`).
**P4** Fault matrix: replica crash mid-append; primary crash after ACK before checkpoint; stale epoch write; duplicate replay; network partition (N=2 fail-closed, no silent minority writes); corrupt replica metadata. dual-primary=0; stale rejects 100%; duplicates idempotent 100%.
**P5** Bench: 10k small / 1k medium / 100 large — conflict latency, recovery, duplicate suppression, checkpoint cost, consistency verify. Persist experiments/ + snapshot.
**P6** pytest ≥280; audit PASS; **CP-0017 VERIFIED**; CP-0001..0016 still VERIFIED; version 0.13.0.

### Conflict/partition policy (N=2, no Raft)
- Explicit conflict record + deterministic reject/resolve for hash mismatch (no silent last-write-wins without audit).
- Partition: only fenced primary writes; dual-primary=0; reconcile on heal via epoch+hash verify.
- Idempotency by operation_id survives restart.

### NO
Raft/Paxos, N>2, multi-primary, ML/R2/R3, plaintext fallback, Vault/ACME required, physical/industrial deploy claims, GIA/AGI claims.
