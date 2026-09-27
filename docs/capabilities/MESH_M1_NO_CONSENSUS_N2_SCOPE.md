# Mesh M1 NO_CONSENSUS_YET N=2 Scope Posture

**Capability:** `MESH_M1_NO_CONSENSUS_N2_SCOPE`  
**Cycle / Checkpoint:** 70 / CP-0074  
**Version:** package **0.18.0** held (0.19.0 / pkg0190 NOT_OPENED)  
**Status:** DESIGN ONLY — permanent M1=NO_CONSENSUS_YET under N=2 scope + HOLD; not runtime  
**Scope:** Formalize operator Path C posture; close re-research loop under this scope; do not unlock; do not start D3

## Gates

| Gate | Meaning |
|------|---------|
| `posture_note_present` | `council/NOTE_M1_NO_CONSENSUS_N2_SCOPE.md` |
| `planning_doc_present` | `docs/planning/M1_NO_CONSENSUS_N2_SCOPE.md` |
| `permanent_no_consensus` | M1 permanent under N=2 scope (not pending re-research) |
| `numeric_not_ratify` | C5≥80 ≠ unlocked / ratified |
| `no_raft_default` | Raft must not be default |
| `n_gt2_no_held` | N>2 remains NO_HELD |
| `live_disabled` | live=DISABLED |
| `d3_not_acked` | D3 ACK-gated, not started |
| `mesh_perf_experimental_off` | OFF |
| `pkg0190_not_opened` | v0.19 absent |
| `structural_circularity_documented` | n_gt2_safety circular boundary written |
| `hold_active` | HOLD; no D3; no unlock |

## Helpers

- `neural_mesh.packaging.m1_no_consensus_n2_scope` — C70 / CP-0074

## Preferred next

`await_deepseek` (posture sealed; HOLD; D3 remains ACK-gated — do not flip experimental without ACK)

## NO_HELD

**NO_HELD:** Raft,N>2,multi-primary,ML,R2,R3,plaintext,Vault-ACME-req,GIA,SLO_chase,tag_schema,EVERY_fsync
