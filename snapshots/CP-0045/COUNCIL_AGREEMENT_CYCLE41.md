# Council Agreement — Cycle 41 / CP-0045

**Capability:** Frozen scope NEXT after H7 (CP-0044)  
**Title:** 0.18_H8_manifest_parity — manifest parity@N2; ABORT→reject build; byte-equality under concurrent build  
**Scope:** H8 only (parity check @N2; reject build on abort; toolchain pin; T-H8a(+neg); extend manifest_n2)  
**Version:** package **0.18.0** (unchanged line)  
**Checkpoint:** `CP-0045`

## Scope and deliverables

- Capability `MESH_MANIFEST_PARITY` + schema `mesh.manifest.parity/v1`
- Library `src/neural_mesh/packaging/parity/` (check/concurrent-build/core-parity/ABORT)
- CLI `mesh parity status|check|build-check`
- Tests ≥14; seal `snapshots/CP-0045/`
- PREFERRED_NEXT: `0.18_signoff` (H1..H8 complete; do not invent GIA/N>2)

## Explicit exclusions and bounds

**NO_HELD:** Raft, N>2, multi-primary, ML, R2, R3, plaintext, Vault-ACME-req, GIA, SLO_chase, tag_schema, EVERY_fsync.

Do **not** invent GIA / N>2 after H8. Do **not** claim GIA. Do **not** retag
v0.17.0 / v0.16.3. Do **not** reopen 0.16.3 RC. dual_primary=0. minority_writes=0.
No silent accept on mismatch. No plaintext. No Raft. No N>2.
No Vault/ACME req. Economy PARKED.

## Authorization

This agreement authorizes CP-0045 H8 manifest_parity only, per frozen
0.18 scope ordering (last H theme → then 0.18_signoff). Economy remains PARKED.
