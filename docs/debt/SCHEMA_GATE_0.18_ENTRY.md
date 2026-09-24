# Schema Gate — 0.18.x Entry (GOV.7) — CP-0037 / Cycle 33

**Date:** 2026-09-23 America/New_York (EDT)  
**Cycle / Checkpoint:** 33 / CP-0037  
**Package version:** 0.18.0 (bootstrap)  
**Prior resolution:** `docs/debt/SCHEMA_GATE_RESOLUTION_0.17.md`  
**Blueprint:** GOV.7 schema-debt deadline at 0.18.x entry  
**DeepSeek C32:** resolve-or-waive gate **before or as part of** 0.18 bootstrap

## Decision (docs-only; no unlock invented)

**entry_decision = WAIVE_VIA_ACCEPT_AND_CARRY**

Council note (Grok + DeepSeek C32 alignment): at 0.18.x entry, the
`CHECKPOINT_EVERY_FLOOR` SCHEMA-GATED debt is **waived for entry** by
continuing **ACCEPT_AND_CARRY** from the 0.17 resolution. The floor GAP is
**not** resolved by chase; tag_schema is **not** edited; EVERY_fsync remains
in NO_HELD.

This satisfies GOV.7's "resolved **or waived**" requirement for opening the
0.18.x line and minting CP-0037. It does **not** invent a mechanical unlock
beyond documenting the waiver path.

## What this is NOT

- **NOT** SLO chase (`SLO_chase` remains in NO_HELD).
- **NOT** EVERY fsync optimization (`EVERY_fsync` remains in NO_HELD).
- **NOT** deleting / rewriting `neural_mesh.tags` schema gates (`tag_schema`
  remains in NO_HELD).
- **NOT** changing documented EVERY floor GAP (~1.32 ms).
- **NOT** claiming the floor is MET.

## Policy for 0.18.x

| Item | Policy |
|------|--------|
| `CHECKPOINT_EVERY_FLOOR` status | SCHEMA-GATED (held; carried) |
| Entry gate (GOV.7) | **WAIVED** via ACCEPT_AND_CARRY (this document) |
| Prior resolution | `SCHEMA_GATE_RESOLUTION_0.17.md` remains authoritative for carry meaning |
| Schema gate `schema_gate_checkpoint_every_floor` | Must remain present and green |
| Gate tests (`tests/test_tags.py -k checkpoint_every_floor`) | Remain green |
| Production hot-path | No changes for this entry waiver |
| Blocking for further 0.18 CPs? | Non-blocking while schema gate green + this waiver doc present |

## NO_HELD (unchanged)

**NO_HELD:** Raft,N>2,multi-primary,ML,R2,R3,plaintext,Vault-ACME-req,GIA,SLO_chase,tag_schema,EVERY_fsync

## Related

- `docs/debt/SCHEMA_GATE_RESOLUTION_0.17.md`
- `docs/debt/CHECKPOINT_EVERY_FLOOR.md`
- `docs/planning/0.18_BOOTSTRAP.md`
- `docs/planning/0.18_NON_GOALS.md`
- `council/DEEPSEEK_REPLY_CYCLE32.md`
