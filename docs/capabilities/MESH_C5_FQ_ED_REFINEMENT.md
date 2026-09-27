# Mesh C5 FQ-ED Refinement

**Capability:** `MESH_C5_FQ_ED_REFINEMENT`  
**Cycle / Checkpoint:** 69 / CP-0073  
**Version:** package **0.18.0** held (0.19.0 / pkg0190 NOT_OPENED)  
**Status:** DESIGN ONLY — C5 refine to numeric 80; **M1=NO_CONSENSUS_YET**; not runtime  
**Scope:** Honest +2 (fence_compat +1, adversary +1); fence-probe matrix DESIGN_DRAFTED; ED acceptance criteria; unlock gaps documented

## Gates

| Gate | Meaning |
|------|---------|
| `planning_doc_present` | `docs/planning/C5_FQ_ED_REFINEMENT.md` |
| `hold_note_present` | Resume after Hold post-D2 |
| `axes_threshold_held` | ≥80 threshold unchanged; axes sum 100 |
| `scores_filled` | C0..C5; C5=80; safety stays 23 |
| `honest_delta_documented` | +2 justification without fudge |
| `fence_probe_matrix` | FP-* rows; status DESIGN_DRAFTED |
| `evidence_diversity_criteria` | kinds + correlation + ≥2/≥2 |
| `no_consensus_yet` | Unlock still NO_CONSENSUS_YET |
| `remaining_gaps` | design-review green / GOV.2 / N>2 evidence |
| `no_raft_default` | C1 no_raft=0 |
| `live_disabled` | live=DISABLED |
| `d3_not_acked` | D3 ACK-gated, not started |
| `mesh_perf_experimental_off` | OFF |
| `pkg0190_not_opened` | v0.19 absent |

## Helpers

- `neural_mesh.packaging.c5_fq_ed_refinement` — C69 / CP-0073

## Preferred next

`await_deepseek` (C5 numeric 80; M1 still NO_CONSENSUS_YET; D3 ACK-gated — do not flip experimental without ACK)

## NO_HELD

**NO_HELD:** Raft,N>2,multi-primary,ML,R2,R3,plaintext,Vault-ACME-req,GIA,SLO_chase,tag_schema,EVERY_fsync
