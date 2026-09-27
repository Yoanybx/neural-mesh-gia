# Mesh M1 Scorecard Maturation

**Capability:** `MESH_M1_SCORECARD_MATURATION`  
**Cycle / Checkpoint:** 50 / CP-0054  
**Version:** 0.18.0 HELD  
**Scope:** design-only provisional scores + NO_CONSENSUS_YET; **no** consensus runtime

## Gates

| Gate | Meaning |
|------|---------|
| `scorecard_axes` | 100-pt axes + ≥80 unlock threshold |
| `provisional_scores` | C0..C4 filled; C1 Raft not default |
| `no_consensus_yet` | written justification; N stays 2 |
| `runtime_no_held` | Raft/N>2 documented NO_HELD |
| `version_held` | 0.18.0 |

## Preferred next

`0.19_design_set_signoff` (A–D design residues; still no train / no GIA / no Raft runtime)

## NO_HELD

**NO_HELD:** Raft,N>2,multi-primary,ML,R2,R3,plaintext,Vault-ACME-req,GIA,SLO_chase,tag_schema,EVERY_fsync
