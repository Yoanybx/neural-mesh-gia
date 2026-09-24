# Council Agreement — Cycle 35 / CP-0039

**Capability:** DeepSeek NEXT (Cycle 34 VERDICT PASS / HIGH)  
**Title:** 0.18_H2_recovery — recovery + rebuild; ABORT→snapshot restore  
**Scope:** H2 only (snapshot create/list/verify, restore, rebuild+WAL, ABORT→snapshot restore)  
**Version:** package **0.18.0** (unchanged line)  
**Checkpoint:** `CP-0039`

## Scope and deliverables

- Capability `MESH_RECOVERY_REBUILD` + schema `mesh.recovery/v1`
- Library `src/neural_mesh/recovery/` (durable + WAL + content-hash snapshots)
- CLI `mesh recover status|snapshot|restore|rebuild`
- Tests ≥14; seal `snapshots/CP-0039/`
- PREFERRED_NEXT: `0.18_H3_dual_primary_fence`

## Explicit exclusions and bounds

**NO_HELD:** Raft, N>2, multi-primary, ML, R2, R3, plaintext, Vault-ACME-req, GIA, SLO_chase, tag_schema, EVERY_fsync.

Do **not** implement H3..H8 this cycle. Do **not** claim GIA. Do **not** retag
v0.17.0 / v0.16.3. dual_primary=0. No silent continue on tamper. No plaintext.

## Authorization

This agreement authorizes CP-0039 H2 recovery/rebuild only, per
DeepSeek Cycle 34 ordered NEXT (H2 then H3..H8).
