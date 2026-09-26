# Mesh M1 Consensus Choice Design

**Capability:** `MESH_M1_CONSENSUS_CHOICE_DESIGN`  
**Cycle / Checkpoint:** 46 / CP-0050  
**Version:** 0.18.0 HELD  
**Scope:** design-only scorecard + M2/M3 pointers; **no** consensus runtime

## Gates

| Gate | Meaning |
|------|---------|
| `m1_scorecard` | axes + ≥80 threshold + no default=Raft |
| `m2_pointer` | membership/rejoin pointer present |
| `m3_pointer` | WAN+HLC pointer present |
| `runtime_no_held` | Raft/N>2 documented NO_HELD |
| `version_held` | 0.18.0 |

## Preferred next

`L_judge_schema_stubs` (docs/schema only; still no train / no GIA)

## NO_HELD

**NO_HELD:** Raft,N>2,multi-primary,ML,R2,R3,plaintext,Vault-ACME-req,GIA,SLO_chase,tag_schema,EVERY_fsync
