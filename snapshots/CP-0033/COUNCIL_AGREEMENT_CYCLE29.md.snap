# Council Agreement — Cycle 29 / CP-0033

**Capability:** DeepSeek NEXT (Cycle 28 VERDICT) — fabric_ops_UX  
**Title:** Fabric ops UX (status / diagnose / reconnect)  
**Scope:** Operator UX around existing TLS fabric; no Vault/ACME-req; no plaintext  
**Version:** package **0.17.0** (hold)  
**Checkpoint:** `CP-0033`

## Semver note

Hold **0.17.0**. Do **not** reopen 0.16.3 / single-node freeze. Do **not** move/delete tag `v0.16.3`.

## Scope and deliverables

- Capability doc `MESH_FABRIC_OPS_UX`
- `FabricOps` library wrapping network/tls/session/fabric
- CLI `mesh fabric status|diagnose|reconnect`
- ≥10 tests (shipped 16): fail-closed TLS, no plaintext fallback, diagnose fields, reconnect on tmp roots

## Acceptance gates

- fabric_ops_cycle29 tests green; full pytest green (504+16=520)
- `CP-0033=VERIFIED`
- dual_primary=0; plaintext_fallback=0
- Version==0.17.0; `v0.16.3` tag untouched

## Explicit exclusions and bounds

**NO_HELD:** Raft, N>2, multi-primary, ML, R2, R3, plaintext, Vault-ACME-req, GIA, SLO_chase, tag_schema, EVERY_fsync.

Debt: SCHEMA-GATED ACCEPT_AND_CARRY (unchanged).
