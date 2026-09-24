# Council Agreement — Cycle 34 / CP-0038

**Capability:** DeepSeek NEXT (Cycle 33 VERDICT PASS / HIGH)  
**Title:** 0.18_H1_identity — identity + attestation + trust tiers  
**Scope:** H1 only (node_key, attest, T0..T3, rotate/revoke, ABORT→pinned-only)  
**Version:** package **0.18.0** (unchanged line)  
**Checkpoint:** `CP-0038`

## Scope and deliverables

- Capability `MESH_IDENTITY_ATTESTATION` + policy `trust-tiers-v1` + schema `mesh.identity/v1`
- Library `src/neural_mesh/identity/` on LocalCA / existing TLS helpers (no Vault/ACME)
- CLI `mesh id status|attest|tier|rotate|revoke`
- Tests ≥14; seal `snapshots/CP-0038/`
- PREFERRED_NEXT: `0.18_H2_recovery`

## Explicit exclusions and bounds

**NO_HELD:** Raft, N>2, multi-primary, ML, R2, R3, plaintext, Vault-ACME-req, GIA, SLO_chase, tag_schema, EVERY_fsync.

Do **not** implement H2..H8 this cycle. Do **not** claim GIA. Do **not** retag
v0.17.0 / v0.16.3. dual_primary=0. No silent identity downgrade. No plaintext trust.

## Authorization

This agreement authorizes CP-0038 H1 identity/attestation/tiers only, per
DeepSeek Cycle 33 ordered NEXT (H1 then H2..H8).
