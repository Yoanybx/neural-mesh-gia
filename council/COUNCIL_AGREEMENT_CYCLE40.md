# Council Agreement — Cycle 40 / CP-0044

**Capability:** Frozen scope NEXT after H6 (CP-0043)  
**Title:** 0.18_H7_clock_skew — clock_skew@N2; ABORT→refuse join; wall_clock_as_authority=0  
**Scope:** H7 only (detect skew @N2; refuse join on abort; HLC+mono; T-H7a(+neg); P-02)  
**Version:** package **0.18.0** (unchanged line)  
**Checkpoint:** `CP-0044`

## Scope and deliverables

- Capability `MESH_CLOCK_SKEW_FENCE` + schema `mesh.clock/v1`
- Library `src/neural_mesh/clock/` (detect/probe/join-check/HLC/mono)
- CLI `mesh clock status|probe|join-check`
- Tests ≥14; seal `snapshots/CP-0044/`
- PREFERRED_NEXT: `0.18_H8_manifest_parity`

## Explicit exclusions and bounds

**NO_HELD:** Raft, N>2, multi-primary, ML, R2, R3, plaintext, Vault-ACME-req, GIA, SLO_chase, tag_schema, EVERY_fsync.

Do **not** implement H8 this cycle. Do **not** claim GIA. Do **not** retag
v0.17.0 / v0.16.3. Do **not** reopen 0.16.3 RC. dual_primary=0. minority_writes=0.
wall_clock_as_authority=0 (P-02). No silent join on skew. No plaintext. No Raft. No N>2.
No Vault/ACME req. Economy PARKED.

## Authorization

This agreement authorizes CP-0044 H7 clock_skew only, per frozen
0.18 scope ordering (H7 then H8). Economy remains PARKED.
