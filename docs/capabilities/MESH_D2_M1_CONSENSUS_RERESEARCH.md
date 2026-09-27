# Mesh D2 M1 Consensus Candidate Re-Research

**Capability:** `MESH_D2_M1_CONSENSUS_RERESEARCH`  
**Cycle / Checkpoint:** 68 / CP-0072  
**Version:** package **0.18.0** held (0.19.0 / pkg0190 NOT_OPENED)  
**Status:** DESIGN ONLY — re-score + C5 FQ-ED sketch; **M1=NO_CONSENSUS_YET**; not runtime  
**Scope:** Re-score C0..C5 under C67 axes (safety 30 / liveness 15 / fence-compat 15 / no-Raft 10 / WAN 15 / adversary 10 / complexity 5); compose D1 consensus draft; document NO_CONSENSUS_YET

## Gates

| Gate | Meaning |
|------|---------|
| `planning_doc_present` | `docs/planning/D2_M1_CONSENSUS_CANDIDATE_RERESEARCH.md` |
| `f2_d4_findings_present` | `council/D4_CHATGPT_FINDINGS.md` (fence F2) |
| `d1_exit_noted` | D1 seal PASS / live-discussion NOT PASS recorded in D2 opening |
| `axes_c67_weights` | Updated axes sum 100; ≥80 threshold |
| `scores_filled` | C0..C5 provisional scores present |
| `c5_sketch` | FQ-ED custom sketch documented |
| `no_consensus_yet` | Written justification; no Raft default |
| `composes_d1` | D1 §4 vocabulary / CG4 independence+adversarial cited |
| `live_disabled` | live=DISABLED unchanged |
| `pkg0190_not_opened` | pkg0190 NOT_OPENED; v0.19 absent |
| `mesh_perf_experimental_off` | MESH_PERF_EXPERIMENTAL=OFF |
| `prior_m1_cps` | CP-0050 + CP-0054 still VERIFIED |

## Helpers

- `neural_mesh.packaging.d2_m1_consensus_reresearch` — C68 / CP-0072

## Preferred next

`await_deepseek` (D2 sealed; D3 ACK-gated next per F10 — do not flip experimental without ACK)

## NO_HELD

**NO_HELD:** Raft,N>2,multi-primary,ML,R2,R3,plaintext,Vault-ACME-req,GIA,SLO_chase,tag_schema,EVERY_fsync
