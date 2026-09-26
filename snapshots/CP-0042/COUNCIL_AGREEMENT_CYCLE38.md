# Council Agreement — Cycle 38 / CP-0042

**Capability:** Frozen scope NEXT after H4 (CP-0041)  
**Title:** 0.18_H5_packaging_distribution — mesh.bundle/v1 distribution primitive; ABORT→pin prior  
**Scope:** H5 only (schema/bundle/v1; distribute/verify/pin-prior; T-H5a..f(+neg); P-09 toolchain pin)  
**Version:** package **0.18.0** (unchanged line)  
**Checkpoint:** `CP-0042`

## Scope and deliverables

- Capability `MESH_PACKAGING_DISTRIBUTION` + schema `mesh.bundle/v1`
- Library `src/neural_mesh/packaging/distribution/` (distribute/verify/pin-prior)
- CLI `mesh dist distribute|verify|pin-prior|schema`
- Tests ≥14; seal `snapshots/CP-0042/`
- PREFERRED_NEXT: `0.18_H6_minority_write`

## Explicit exclusions and bounds

**NO_HELD:** Raft, N>2, multi-primary, ML, R2, R3, plaintext, Vault-ACME-req, GIA, SLO_chase, tag_schema, EVERY_fsync.

Do **not** implement H6..H8 this cycle. Do **not** claim GIA. Do **not** retag
v0.17.0 / v0.16.3. Do **not** reopen 0.16.3 RC. dual_primary=0. No silent continue
on schema/signature/replay breach. No plaintext. No Raft. No N>2. No Vault/ACME req.

## Authorization

This agreement authorizes CP-0042 H5 packaging distribution only, per frozen
0.18 scope ordering (H5 then H6..H8). Dual Joan briefing is separate and
non-blocking.
