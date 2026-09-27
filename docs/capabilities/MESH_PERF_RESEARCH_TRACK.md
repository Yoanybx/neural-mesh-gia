# Mesh Performance Research Track

**Capability:** `MESH_PERF_RESEARCH_TRACK`  
**Cycle / Checkpoint:** 62 / CP-0066  
**Version:** package **0.18.0** held  
**Status:** RESEARCH + local microbench harness  
**Scope:** Honest baselines for fence / OBS snapshot / membership SM / receipt
hash-chain / packaging verify; literature pointers to etcd/Raft/CRDT as
NON-default; M1=NO_CONSENSUS_YET; no false "fastest" claims

## Gates

| Gate | Meaning |
|------|---------|
| Design | `docs/design/MESH_PERF_RESEARCH_TRACK.md` |
| Literature pointers | `docs/design/MESH_PERF_LITERATURE_POINTERS_NONDEFAULT.md` |
| Helpers | packaging `mesh_perf_research` |
| Benches | fence_path · obs_snapshot · membership_sm · receipt_hash_chain · packaging_verify |
| Honesty | `ranking_claim=null`; forbidden-phrase tests |
| M1 | NO_CONSENSUS_YET |
| live | DISABLED |
| NO_HELD held | No Raft/N>2/GIA/train unlock |

## Preferred next

Superseded by CP-0067 `perf_hotspot_and_improvement_design` (then `await_deepseek`).

## NO_HELD

**NO_HELD:** Raft,N>2,multi-primary,ML,R2,R3,plaintext,Vault-ACME-req,GIA,SLO_chase,tag_schema,EVERY_fsync
