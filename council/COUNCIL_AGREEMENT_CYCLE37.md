# Council Agreement — Cycle 37 / CP-0041

**Capability:** DeepSeek NEXT (Cycle 36 VERDICT PASS / HIGH)  
**Title:** 0.18_H4_obs_telemetry — versioned OBS telemetry contract; ABORT→block CP mint  
**Scope:** H4 only (schema/obs/v1; signals+adversary+cadence; invariant auto-fail → block CP)  
**Version:** package **0.18.0** (unchanged line)  
**Checkpoint:** `CP-0041`

## Scope and deliverables

- Capability `MESH_OBS_TELEMETRY` + schema `mesh.obs/v1`
- Library `src/neural_mesh/obs/` (emit/validate; extends status_snapshot)
- CLI `mesh obs telemetry|validate|schema`
- Tests ≥14; seal `snapshots/CP-0041/`
- PREFERRED_NEXT: `0.18_H5_packaging_distribution`

## Explicit exclusions and bounds

**NO_HELD:** Raft, N>2, multi-primary, ML, R2, R3, plaintext, Vault-ACME-req, GIA, SLO_chase, tag_schema, EVERY_fsync.

Do **not** implement H5..H8 this cycle. Do **not** claim GIA. Do **not** retag
v0.17.0 / v0.16.3. dual_primary=0. No silent continue on schema breach. No plaintext.
No Raft. No N>2. No SLO chase on recovery_p99.

## Authorization

This agreement authorizes CP-0041 H4 OBS telemetry only, per
DeepSeek Cycle 36 ordered NEXT (H4 then H5..H8).
