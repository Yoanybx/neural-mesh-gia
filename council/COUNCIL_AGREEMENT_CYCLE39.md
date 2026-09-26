# Council Agreement — Cycle 39 / CP-0043

**Capability:** Frozen scope NEXT after H5 (CP-0042)  
**Title:** 0.18_H6_minority_write — minority_write@N2; ABORT→halt writes; MINORITY_WRITES=0  
**Scope:** H6 only (detect minority write @N2; halt writes on abort; T-H6a(+neg))  
**Version:** package **0.18.0** (unchanged line)  
**Checkpoint:** `CP-0043`

## Scope and deliverables

- Capability `MESH_MINORITY_WRITE_FENCE` + schema `mesh.minority/v1`
- Library `src/neural_mesh/minority/` (detect/probe/halt/try_write)
- CLI `mesh minority status|probe|halt`
- Tests ≥14; seal `snapshots/CP-0043/`
- PREFERRED_NEXT: `0.18_H7_clock_skew`

## Explicit exclusions and bounds

**NO_HELD:** Raft, N>2, multi-primary, ML, R2, R3, plaintext, Vault-ACME-req, GIA, SLO_chase, tag_schema, EVERY_fsync.

Do **not** implement H7..H8 this cycle. Do **not** claim GIA. Do **not** retag
v0.17.0 / v0.16.3. Do **not** reopen 0.16.3 RC. dual_primary=0. minority_writes=0.
No silent continue on minority write. No plaintext. No Raft. No N>2. No Vault/ACME req.

## Authorization

This agreement authorizes CP-0043 H6 minority_write only, per frozen
0.18 scope ordering (H6 then H7..H8). Economy remains PARKED.
