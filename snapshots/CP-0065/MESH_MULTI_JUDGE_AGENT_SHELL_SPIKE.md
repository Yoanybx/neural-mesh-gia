# Mesh Multi-Judge + Agent-Shell Spike

**Capability:** `MESH_MULTI_JUDGE_AGENT_SHELL_SPIKE`  
**Cycle / Checkpoint:** 61 / CP-0065  
**Version:** package **0.18.0** held  
**Status:** SPIKE EXECUTED (mock-only; live=DISABLED)  
**Scope:** Two mock judges + agent_shell + orchestrator routing under M2 churn;
DUAL_ADVISORY / FALLBACK / ABORT_MISMATCH; receipt hash-chain; no double-invoke;
attribution; M1=NO_CONSENSUS_YET

## Gates

| Gate | Meaning |
|------|---------|
| Design note | `docs/design/MULTI_JUDGE_AGENT_SHELL_SPIKE.md` |
| Spike helpers | packaging `multi_judge_agent_shell_spike` |
| Policies stressed | DUAL_ADVISORY · FALLBACK · ABORT_MISMATCH · shell path |
| Churn | DRAINING→LEFT→REJOIN ABORT new routes |
| Receipts | hash-chained spike receipts; attribution complete |
| Neg tests | T-route-spike-a / T-route-spike-b / T-route-spike-c |
| M1 orthogonal | NO_CONSENSUS_YET; dual ≠ consensus |
| live | DISABLED (no keys, no WAN, no frontier) |
| NO_HELD held | No Raft/N>2/multi-primary/GIA/train/SaaS |

## Preferred next

`await_deepseek` (C60 Option1 sealed; ranked follow-on Option3 continuity or Option2 oversight — or authorized MESH_PERF_RESEARCH_TRACK)

## NO_HELD

**NO_HELD:** Raft,N>2,multi-primary,ML,R2,R3,plaintext,Vault-ACME-req,GIA,SLO_chase,tag_schema,EVERY_fsync
