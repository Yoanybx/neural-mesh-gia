# Mesh Orchestrator Continuity

**Capability:** `MESH_ORCHESTRATOR_CONTINUITY`  
**Cycle / Checkpoint:** 64 / CP-0068  
**Version:** package **0.18.0** held  
**Status:** DESIGN ONLY  
**Scope:** Durable goals + evidence/audit ledger + continuity state machine +
in-flight/orphan policy across LEFT/REJOIN + invocation idempotency + resume
after restart + timeout bounds + ABORT propagation; compose with CP-0064 judge
routing; substrate memory NOT consciousness; mock ContinuityOrchestrator only;
live=DISABLED; no train

## Gates

| Gate | Meaning |
|------|---------|
| Design present | `docs/design/ORCHESTRATOR_CONTINUITY_DESIGN.md` |
| Prior durable goals | `docs/design/DURABLE_GOALS_CONTINUITY_DESIGN.md` |
| Schema stub | `docs/schema/continuity/orchestrator_v0.md` |
| Compose routing | wraps OrchestratorRouter (CP-0064) |
| Orphan policy | LEFT/REJOIN/DRAIN in-flight → audited ABORT/BLOCKED |
| Idempotency | no double-invoke; conflict ABORT |
| Resume | registry+ledger only (not engine chat) |
| Perf note | budget receipt_hash_chain at transition edges (CP-0067) |
| Helpers + neg | packaging `orchestrator_continuity`; T-cont-a/b/c |
| Substrate memory | NOT consciousness / NOT L_GIA |
| M1 orthogonal | NO_CONSENSUS_YET |
| NO_HELD held | No Raft/N>2/multi-primary/GIA/train/live |

## Preferred next

`await_deepseek` (C64 continuity sealed; ranked follow-on = oversight_hooks refinement per C63 Option3, or hold)

## NO_HELD

**NO_HELD:** Raft,N>2,multi-primary,ML,R2,R3,plaintext,Vault-ACME-req,GIA,SLO_chase,tag_schema,EVERY_fsync
