# Schema: mesh.membership.m1_reresearch/v0 (STUB)

**Status:** STUB (Cycle 68 / CP-0072) — design alignment only; no consensus runtime  
**Schemas:** `mesh.membership.m1_reresearch/v0`  
**Design:** `docs/planning/D2_M1_CONSENSUS_CANDIDATE_RERESEARCH.md`  
**Non-goals:** no Raft runtime; no N>2; no live API; no GIA; no train-70B

## M1ReresearchGate (`mesh.membership.m1_reresearch/v0`)

| Field | Type | Notes |
|-------|------|-------|
| `schema` | string | `mesh.membership.m1_reresearch/v0` |
| `m1_status` | string | `NO_CONSENSUS_YET` |
| `ratify_threshold` | int | `80` |
| `axes` | object | safety30,liveness15,fence15,no_raft10,wan15,adversary10,complexity5 |
| `candidate_totals` | object | C0..C5 integer totals |
| `closest_candidate` | string | `C5` (FQ-ED) when status is NO_CONSENSUS_YET |
| `closest_score` | int | `78` |
| `raft_is_default` | bool | **must be false** |
| `live_enabled` | bool | **must be false** |
| `mesh_perf_experimental` | string | `OFF` |
| `composed_cps` | string[] | CP-0050, CP-0054, CP-0071 |
| `d1_exit_seal` | string | `PASS` |
| `d1_exit_live_discussion` | string | `NOT_PASS` |

## Candidate IDs

`C0` (baseline) · `C1` Raft · `C2` Paxos · `C3` Flex/EPaxos · `C4` Mesh-native · `C5` FQ-ED

**NO_HELD:** Raft,N>2,multi-primary,ML,R2,R3,plaintext,Vault-ACME-req,GIA,SLO_chase,tag_schema,EVERY_fsync
