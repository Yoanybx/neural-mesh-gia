# Mesh Perf — Hotspot & Improvement Design

**Capability:** `perf_hotspot_and_improvement_design`  
**Cycle / Checkpoint:** 63 / CP-0067  
**Version:** package **0.18.0** held  
**Status:** DESIGN + local hotspot analysis + optional experimental A/B (flag OFF)  
**Scope:** Rank CP-0066 microbench hotspots (box-local); propose measurable
improvement designs I1..I7; no false ranking / world-fastest claims;
M1=NO_CONSENSUS_YET; live=DISABLED

## Gates

| Gate | Meaning |
|------|---------|
| Design | `docs/design/MESH_PERF_HOTSPOT_AND_IMPROVEMENT_DESIGN.md` |
| Helpers | packaging `mesh_perf_hotspot` |
| Hotspots | fence_path · obs_snapshot · receipt_hash_chain · packaging_verify · membership_sm |
| Experimental flag | `MESH_PERF_EXPERIMENTAL` default OFF |
| Honesty | `ranking_claim=null`; `achieved_speedup_claimed=false` |
| M1 | NO_CONSENSUS_YET |
| live | DISABLED |
| NO_HELD held | No Raft/N>2/GIA/train unlock |

## Preferred next

`await_deepseek` (continuity design still queued)

## NO_HELD

**NO_HELD:** Raft,N>2,multi-primary,ML,R2,R3,plaintext,Vault-ACME-req,GIA,SLO_chase,tag_schema,EVERY_fsync
