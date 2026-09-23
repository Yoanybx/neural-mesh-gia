# Consejo Ciclo 12 — Phase 5A Distributed C-RAM over Fabric (N=2)

| Voz | Veredicto C11 | NEXT C12 |
|-----|---------------|----------|
| ChatGPT | APROBADO | Phase 5 Distributed State Ops (remote C-RAM + consistency + faults + obs + bench) → CP-0016 ≥250 |
| DeepSeek | APROBADO | **Phase 5A** N=2 activo-pasivo sobre Fabric mTLS, sin Raft, promoción controlada, feature flag → CP-0016 |
| Grok | Síntesis **5A** | Unifica remote API ChatGPT + réplica N=2 DeepSeek |

## Acuerdo unificado (Grok)

**Phase 5A — Replicación N=2 activo-pasivo + remote C-RAM API sobre Network Fabric mTLS → CP-0016.**

### Alcance
- Exactamente N=2: 1 primary + 1 standby (standby read-only / rejects writes).
- Transporte: Fabric mTLS obligatorio para path remoto; AF_UNIX coexistente para local/test.
- Feature flag: OFF = single-node C11 intacto.
- Promoción **manual/controlada** con epoch/fencing; dual-primary = 0 siempre.
- NO Raft / N>2 / multi-primary / ML / plaintext fallback / Vault-ACME required / auto-failover sin fencing.

### Plan P0–P5
**P0** Doc freeze `docs/phase5_replication_n2.md` (roles, epoch, fencing, promote, fail-closed).
**P1** Remote C-RAM API: `cram/remote_*.py` — put_remote / get_remote / verify_remote / checkpoint_remote; TLS required for remote path.
**P2** Replica protocol over Fabric: REPLICA_APPEND, REPLICA_ACK, ROLE_STATUS, PROMOTE_REQUEST + epoch/fencing; version/epoch/object_hash/node_id; stale epoch + hash mismatch reject.
**P3** Faults: NETWORK_DROP mid-replica, kill -9 mid-handshake/mid-frame, cert invalid, promote under partition → dual-primary 0; no phantom state; checkpoint after recovery.
**P4** Light observability: trace_id / operation_id / node_path / latency / result; CLI `mesh cram trace <operation_id>` reconstructing Task→Router→Network→C-RAM→Checkpoint (minimal viable).
**P5** Bench N=1000: remote put/get p50/p99; replica overhead p99 <1.0 ms OR <2× C11; recovery p99 <250 ms; thruput ≥50% C11 (≥3300 msg/s); integrity 1.0; dual-primary 0; plaintext 0. Persist experiments/ + snapshot.
**P6** pytest ≥250; audit PASS; **CP-0016 VERIFIED**; version **0.12.0**; CP-0001..0015 still VERIFIED.

### NO
Raft, Paxos, N>2, quorum, dynamic membership, multi-primary, CRDT, ML, plaintext fallback, Vault/ACME mandatory, Phase 6.
