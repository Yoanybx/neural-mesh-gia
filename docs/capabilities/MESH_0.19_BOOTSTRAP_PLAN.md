# Mesh 0.19 Bootstrap Plan

**Capability:** `MESH_0.19_BOOTSTRAP_PLAN`  
**Cycle / Checkpoint:** 43 / CP-0047  
**Version:** 0.18.0 HELD (0.19.0 line not opened)  
**Scope:** docs/design DRAFT + minimal scaffold tests; no feature runtime

## Purpose

Execute authorized post-0.18 work per `COUNCIL_AGREEMENT_HYPERBRAIN_ASTRA.md`:
bootstrap **plan** (not version open), L_judge MIX design, durable goal/memory
continuity design, agent-shell spike plan + M1..M3 design-only pointers.

## Gates

| Gate | Meaning |
|------|---------|
| `version_held_0180` | pyproject + `__init__` remain 0.18.0 |
| `scope_draft_abcd` | `0.19_SCOPE_DRAFT` lists themes (A)..(D) |
| `not_frozen_yet` | No `0.19_SCOPE_FROZEN` claimed this cycle |
| `no_held_documented` | NO_HELD unchanged (incl. GIA) |
| `design_l_judge` | `docs/design/L_JUDGE_MIX_DESIGN.md` present |
| `design_durable_goals` | `docs/design/DURABLE_GOALS_CONTINUITY_DESIGN.md` present |
| `tag_v0180_untouched` | local tag `v0.18.0` exists; not retagged |
| `no_gia_claims` | plan docs do not claim GIA/hyperbrain achieved |
| `impl_deferred` | no L_judge/goal runtime modules this cycle |

## Artifacts

- `docs/planning/0.19_BOOTSTRAP.md`
- `docs/planning/0.19_SCOPE_DRAFT.md` / `0.19_NON_GOALS.md`
- `docs/design/L_JUDGE_MIX_DESIGN.md`
- `docs/design/DURABLE_GOALS_CONTINUITY_DESIGN.md`
- `council/SCOPE_0.19_DRAFT.md`
- `tests/test_019_bootstrap_plan_cycle43.py`
- `snapshots/CP-0047/`

## Preferred next

`0.19_scope_freeze` (council freeze gate) — still docs; then design ratification /
adapter spike planning without NO_HELD.

## NO_HELD

**NO_HELD:** Raft,N>2,multi-primary,ML,R2,R3,plaintext,Vault-ACME-req,GIA,SLO_chase,tag_schema,EVERY_fsync

## Explicit non-goals (this cycle)

- Do not open package 0.19.0 / retag v0.18.0.
- Do not freeze scope prematurely.
- Do not implement MIX runtime, goal registry code, Raft/N>2, GIA, train, SaaS, economy.
