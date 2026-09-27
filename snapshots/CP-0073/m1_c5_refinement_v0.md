# Schema: mesh.membership.m1_c5_refinement/v0 (STUB)

**Status:** STUB (Cycle 69 / CP-0073) — design alignment only; no consensus runtime  
**Schemas:** `mesh.membership.m1_c5_refinement/v0`  
**Design:** `docs/planning/C5_FQ_ED_REFINEMENT.md`  
**Non-goals:** no Raft runtime; no N>2; no live API; no GIA; no train-70B; no D3 without ACK

## M1C5RefinementGate (`mesh.membership.m1_c5_refinement/v0`)

| Field | Type | Notes |
|-------|------|-------|
| `schema` | string | `mesh.membership.m1_c5_refinement/v0` |
| `m1_status` | string | `NO_CONSENSUS_YET` |
| `ratify_threshold` | int | `80` (unchanged) |
| `closest_candidate` | string | `C5` |
| `closest_score` | int | `80` |
| `prior_closest_score` | int | `78` |
| `score_delta` | int | `2` |
| `fence_probe_status` | string | `DESIGN_DRAFTED` (not DESIGN_REVIEW_GREEN) |
| `c5_numeric_threshold_met` | bool | `true` |
| `remaining_unlock_gaps` | string[] | fence green, GOV.2, N>2 evidence, runtime NO_HELD |
| `raft_is_default` | bool | **must be false** |
| `live_enabled` | bool | **must be false** |
| `mesh_perf_experimental` | string | `OFF` |
| `composed_cps` | string[] | CP-0050, CP-0054, CP-0071, CP-0072 |

## Candidate totals (design)

C0=85† · C1=54 · C2=53 · C3=60 · C4=73 · **C5=80**

† Not unlock-eligible.

**NO_HELD:** Raft,N>2,multi-primary,ML,R2,R3,plaintext,Vault-ACME-req,GIA,SLO_chase,tag_schema,EVERY_fsync
