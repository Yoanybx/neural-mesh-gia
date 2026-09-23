# Consejo acordado — Ciclo 6 C-RAM Replica N=2 (Controlled)

**Fecha:** 2026-09-23 America/New_York (EDT)

## Veredictos Ciclo 5
| Voz | Ciclo 5 | Ciclo 6 |
|-----|---------|---------|
| ChatGPT | OK prerreqs | **B) APROBADO CON CAMBIOS** — réplica controlada v0 |
| DeepSeek | **APROBADO** | **B) APROBADO CON CAMBIOS** — fijar consistencia antes de código |
| Grok Bot | Acepta | Integra ambos: **P0 doc freeze (DeepSeek) luego impl (ChatGPT)** |

## Modelo de consistencia CONGELADO (P0 — merge gate)
- **async replication**, primary-ack **W=1**, read **R=1**
- Eventual consistency with bound **T_conv = 5.0s** (in-process twin/sandbox; measured in P8)
- **Non-goals:** linearizability, majority quorum, Raft/Paxos, N>2, geo, ML placement
- **Fencing:** monotonic `epoch` per object key; `apply(op_id, epoch)` rejects `epoch < current` (idempotent log)
- **Tie-breaker:** static `node_id` lexicographic priority + local `.cram/witness` timestamp on promote
- **op_id** required on put; duplicate op_id → single effect
- **Anti-entropy on rejoin:** Merkle-diff per object (minimal), converge < T_conv

## Plan implementación (tras P0)
P1 ReplicaPlacement primary≠secondary deterministic  
P2 ReplicaManager sync CREATED→SYNCING→SYNCED|FAILED + ReplicationLog  
P3 Failover: primary NODE_LOSS + verified replica → FAILOVER_AVAILABLE (hash+version+integrity)  
P4 Split-brain guard (epoch + tie-breaker); ≤1 writable primary under partition sim  
P5 Anti-entropy rejoin  
P6 Tests ChatGPT+DeepSeek suite  
P7 CLI: create/status/verify/repair + promote/verify-consistency; exit 0/1/2/3  
P8 Bench overhead + T_conv; recovery_time p99 still <150ms; audit; **CP-0010**

## Acceptance
- ≤1 writable primary in partition sims  
- T_conv measured < 5.0s  
- Repl overhead p99 < 5× single-node AND recovery p99 <150ms  
- op_id: 0 duplicates in 100 retries  
- pytest ≥90; audit PASS; CP-0010 VERIFIED  

## NO hacer
N>2, Raft/Paxos, Phase 3 Router, ML, auto-promote without fencing, checkpoint schema break without migration.
