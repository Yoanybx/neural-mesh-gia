# Mesh 0.18 Bootstrap

**Capability:** `MESH_0.18_BOOTSTRAP`  
**Cycle / Checkpoint:** 33 / CP-0037  
**Version:** 0.18.0 (development line OPEN; H1..H8 not implemented)  
**Scope:** version bump + planning freeze + GOV.7 entry waiver docs + tests

## Purpose

Open the **0.18.x** line after 0.17 theme-set closeout (CP-0036) without
shipping nervous-hardening features. Mirrors Cycle 26 / CP-0030 `0.17`
bootstrap pattern.

## Gates

| Gate | Meaning |
|------|---------|
| `version_0180` | pyproject + `__init__` == 0.18.0 |
| `scope_frozen_h1_h8` | `0.18_SCOPE_FROZEN` lists H1..H8 ordered |
| `no_held_documented` | NO_HELD unchanged (incl. GIA) |
| `gov7_entry_waiver` | `SCHEMA_GATE_0.18_ENTRY.md` WAIVE_VIA_ACCEPT_AND_CARRY |
| `prior_017_resolution` | `SCHEMA_GATE_RESOLUTION_0.17.md` still present |
| `release_0170_archive` | `dist/releases/0.17.0/` still present |
| `tag_v0170` | local tag `v0.17.0` exists (untouched) |
| `no_gia_claims` | bootstrap docs do not claim GIA |
| `h1_deferred` | no full H1 identity implementation this cycle |

## Artifacts

- `docs/planning/0.18_BOOTSTRAP.md`
- `docs/planning/0.18_SCOPE.md` / `0.18_SCOPE_FROZEN.md` / `0.18_NON_GOALS.md`
- `council/SCOPE_0.18_FROZEN.md`
- `docs/debt/SCHEMA_GATE_0.18_ENTRY.md`
- `tests/test_018_bootstrap_cycle33.py`
- `snapshots/CP-0037/`

## Preferred next

`0.18_H1_identity` (then H2..H8 per frozen scope).

## NO_HELD

**NO_HELD:** Raft,N>2,multi-primary,ML,R2,R3,plaintext,Vault-ACME-req,GIA,SLO_chase,tag_schema,EVERY_fsync

## Explicit non-goals (this cycle)

- Do not implement H1..H8 fully.
- Do not reopen/retag 0.17.0 or 0.16.3.
- Do not chase EVERY floor / edit tag_schema / claim GIA.
