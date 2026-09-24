# Schema Gate Resolution — 0.17 line (CP-0030 / P25)

**Date:** 2026-09-23 America/New_York (EDT)  
**Cycle / Checkpoint:** 26 / CP-0030  
**Package version:** 0.17.0 (bootstrap)  
**Release closed:** 0.16.3  

## Resolution

**resolution = ACCEPT_AND_CARRY**

The 0.17 development line **carries forward** `CHECKPOINT_EVERY_FLOOR`
**SCHEMA-GATED** debt as accepted **non-blocking** debt unless the schema
gate fails.

## What this is NOT

- **NOT** SLO chase (`SLO_chase` remains in NO_HELD).
- **NOT** EVERY fsync optimization (`EVERY_fsync` remains in NO_HELD).
- **NOT** deleting / rewriting `neural_mesh.tags` schema gates (`tag_schema`
  remains in NO_HELD).
- **NOT** changing documented EVERY floor GAP (~1.32 ms).

## Policy

| Item | Policy for 0.17.x |
|------|-------------------|
| `CHECKPOINT_EVERY_FLOOR` status | SCHEMA-GATED (held) |
| Schema gate `schema_gate_checkpoint_every_floor` | Must remain present and green |
| Gate tests (`tests/test_tags.py -k checkpoint_every_floor`) | Remain green |
| Debt docs | Carry forward; no churn beyond this resolution note |
| Production hot-path | No changes for this resolution |
| Blocking? | Non-blocking unless schema gate fails |

## Review helper

`neural_mesh.packaging.debt_gate_review.debt_gate_status()` and
`run_debt_gate_review(...)` emit `resolution=ACCEPT_AND_CARRY` for the
0.17 line (read-only; no rebenchmark).

## NO_HELD (unchanged)

**NO_HELD:** Raft,N>2,multi-primary,ML,R2,R3,plaintext,Vault-ACME-req,GIA,SLO_chase,tag_schema,EVERY_fsync

## Related

- `docs/debt/CHECKPOINT_EVERY_FLOOR.md`
- `docs/debt/DEBT_GATE_REVIEW_CP0029.md`
- `docs/planning/0.17_SCOPE_FROZEN.md`
- `scripts/debt_gate_review.py`

- `docs/debt/SCHEMA_GATE_0.18_ENTRY.md` (GOV.7 0.18.x entry waive/carry)
