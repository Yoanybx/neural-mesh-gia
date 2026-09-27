# Schema: mesh.membership.m1_n2_scope_posture/v0 (STUB)

**Status:** STUB (Cycle 70 / CP-0074) — design alignment only; no consensus runtime  
**Schemas:** `mesh.membership.m1_n2_scope_posture/v0`  
**Design:** `docs/planning/M1_NO_CONSENSUS_N2_SCOPE.md`  
**Non-goals:** no Raft runtime; no N>2; no live API; no GIA; no train-70B; no D3 without ACK

## M1N2ScopePostureGate (`mesh.membership.m1_n2_scope_posture/v0`)

| Field | Type | Notes |
|-------|------|-------|
| `schema` | string | `mesh.membership.m1_n2_scope_posture/v0` |
| `m1_status` | string | `NO_CONSENSUS_YET` |
| `posture` | string | `PERMANENT_UNDER_N2_SCOPE` |
| `pending_reresearch` | bool | **must be false** |
| `ratify_threshold` | int | `80` (unchanged) |
| `closest_candidate` | string | `C5` |
| `closest_score` | int | `80` |
| `c5_numeric_threshold_met` | bool | `true` |
| `unlocked` | bool | **must be false** |
| `fence_probe_status` | string | `DESIGN_DRAFTED` |
| `remaining_unlock_gaps` | string[] | fence_green, GOV.2, n_gt2_safety |
| `structural_circularity` | string | `n_gt2_safety_blocked_while_n_gt2_no_held` |
| `raft_is_default` | bool | **must be false** |
| `n_gt2_status` | string | `NO_HELD` |
| `live_enabled` | bool | **must be false** |
| `mesh_perf_experimental` | string | `OFF` |
| `d3_acked` | bool | **must be false** |
| `hold_active` | bool | **must be true** |
| `composed_cps` | string[] | CP-0050, CP-0054, CP-0071, CP-0072, CP-0073 |

## Candidate totals (unchanged from CP-0073)

C0=85† · C1=54 · C2=53 · C3=60 · C4=73 · **C5=80**

† Not unlock-eligible.

**NO_HELD:** Raft,N>2,multi-primary,ML,R2,R3,plaintext,Vault-ACME-req,GIA,SLO_chase,tag_schema,EVERY_fsync
