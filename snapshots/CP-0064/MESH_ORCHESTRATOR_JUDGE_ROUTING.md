# Mesh Orchestrator Judge Routing

**Capability:** `MESH_ORCHESTRATOR_JUDGE_ROUTING`  
**Cycle / Checkpoint:** 60 / CP-0064  
**Version:** package **0.18.0** held  
**Status:** DESIGN ONLY  
**Scope:** Route workloads to L_judge MIX / agent_shell under policy, M2/M3 gates,
oversight (A3/A4), dual-advisory (≠ M1 consensus), fallback, ABORT-on-mismatch,
durable goals continuity hooks; mock router only; live=DISABLED; no train

## Gates

| Gate | Meaning |
|------|---------|
| Design present | `docs/design/ORCHESTRATOR_JUDGE_ROUTING_DESIGN.md` |
| Schema stub | `docs/schema/judge/routing_v0.md` |
| Policies | SINGLE / DUAL_ADVISORY / FALLBACK / ABORT_ON_MISMATCH |
| Targets | L_judge · agent_shell · MESH_LOCAL |
| M2/M3 compose | ACTIVE T2\|T3; latency band preference |
| Oversight I5 | A3/A4 approve/deny; A4 deadman |
| Continuity | goal_id + continuity hooks on receipts |
| Helpers + neg | packaging `orchestrator_judge_routing`; T-route-a/b/c |
| Operator intent | Mesh = reasoning orchestrator (not frontier LLM) |
| M1 orthogonal | NO_CONSENSUS_YET; dual ≠ consensus |
| NO_HELD held | No Raft/N>2/multi-primary/GIA/train/live |

## Preferred next

`await_deepseek` (C60 routing design sealed; ranked follow-on = multi-judge agent_shell spike per C59 Option3)

## NO_HELD

**NO_HELD:** Raft,N>2,multi-primary,ML,R2,R3,plaintext,Vault-ACME-req,GIA,SLO_chase,tag_schema,EVERY_fsync
