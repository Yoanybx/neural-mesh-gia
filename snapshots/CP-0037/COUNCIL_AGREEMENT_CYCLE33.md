# Council Agreement — Cycle 33 / CP-0037

**Capability:** DeepSeek NEXT (Cycle 32 VERDICT)  
**Title:** 0.18 bootstrap; GOV.7 schema-debt entry waive; scope freeze H1..H8  
**Scope:** version + docs + tests only; no full H1..H8 implementation  
**Version:** package **0.18.0** (bootstrap); 0.17.0 themes + 0.16.3 CLOSED/FROZEN  
**Checkpoint:** `CP-0037`

## Semver note

Open the **0.18.x** development line at **0.18.0**. Do **not** reopen 0.17.0
theme-set archives or 0.16.3 RC. Do **not** move/delete tags `v0.17.0` /
`v0.16.3`. `RELEASE_VERSION` stays **0.16.3** (closed single-node release id).

## Scope and deliverables

- **0.18_bootstrap:** bump package to **0.18.0**; planning BOOTSTRAP / SCOPE /
  SCOPE_FROZEN / NON_GOALS; council SCOPE_0.18_FROZEN; capability
  MESH_0.18_BOOTSTRAP.
- **GOV.7 entry gate:** `docs/debt/SCHEMA_GATE_0.18_ENTRY.md` with
  **WAIVE_VIA_ACCEPT_AND_CARRY** (council note); carry
  `SCHEMA_GATE_RESOLUTION_0.17.md`. Docs only — no floor chase / no unlock invent.
- **Frozen themes:** H1..H8 from blueprint L2 NERVOUS_HARDENING (ordered).
- **PREFERRED_NEXT:** `0.18_H1_identity` (deferred; not implemented here).

## Explicit exclusions and bounds

**NO_HELD:** Raft, N>2, multi-primary, ML, R2, R3, plaintext, Vault-ACME-req, GIA, SLO_chase, tag_schema, EVERY_fsync.

This agreement authorizes 0.18.0 bootstrap + GOV.7 entry waiver docs only.
