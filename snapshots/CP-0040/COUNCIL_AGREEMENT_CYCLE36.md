# Council Agreement — Cycle 36 / CP-0040

**Capability:** DeepSeek NEXT (Cycle 35 VERDICT PASS / HIGH)  
**Title:** 0.18_H3_dual_primary_fence — detect dual-primary @N2; demote+re-elect; ABORT→demote+re-elect  
**Scope:** H3 only (fence epoch + durable token, N2 fence probe, dual_primary intent=0, ABORT=demote+re-elect)  
**Version:** package **0.18.0** (unchanged line)  
**Checkpoint:** `CP-0040`

## Scope and deliverables

- Capability `MESH_DUAL_PRIMARY_FENCE` + schema `mesh.fence/v1`
- Library `src/neural_mesh/fence/` (roles, epoch, durable token, PrimaryWitness sync)
- CLI `mesh fence status|probe|demote|reelect`
- Tests ≥14; seal `snapshots/CP-0040/`
- PREFERRED_NEXT: `0.18_H4_obs_telemetry`

## Explicit exclusions and bounds

**NO_HELD:** Raft, N>2, multi-primary, ML, R2, R3, plaintext, Vault-ACME-req, GIA, SLO_chase, tag_schema, EVERY_fsync.

Do **not** implement H4..H8 this cycle. Do **not** claim GIA. Do **not** retag
v0.17.0 / v0.16.3. dual_primary=0. No silent continue on dual-primary. No plaintext.
No Raft. No N>2.

## Authorization

This agreement authorizes CP-0040 H3 dual-primary fence only, per
DeepSeek Cycle 35 ordered NEXT (H3 then H4..H8).
