# Council Agreement — Cycle 43 / CP-0047

**Capability:** Post-0.18 authorized work per HYPERBRAIN_ASTRA  
**Title:** 0.19 bootstrap plan + L_judge MIX design + durable goals/continuity  
**Scope:** Docs/design DRAFT only; no GIA; no Raft/N>2 runtime; no train 70B; no SaaS; no economy  
**Version:** package **0.18.0** HELD  
**Checkpoint:** `CP-0047`

## Semver note

Hold **0.18.0**. Do **not** open 0.19.0 this cycle. Do **not** retag `v0.18.0` /
`v0.17.0` / `v0.16.3`. Scope remains **DRAFT** (freeze gate = later CP).

## Scope and deliverables

- `docs/planning/0.19_{BOOTSTRAP,SCOPE_DRAFT,NON_GOALS}.md`
- `docs/design/L_JUDGE_MIX_DESIGN.md`
- `docs/design/DURABLE_GOALS_CONTINUITY_DESIGN.md`
- Capability `MESH_0.19_BOOTSTRAP_PLAN`
- Council `SCOPE_0.19_DRAFT` + PASTE/STATUS Cycle 43
- ≥10 tests (marker `bootstrap_plan_cycle43`)
- Snapshots/CP-0047 VERIFIED
- PREFERRED_NEXT=`0.19_scope_freeze`

## Acceptance gates

- bootstrap_plan_cycle43 tests green; full pytest green
- `CP-0047=VERIFIED`
- dual_primary=0; version==0.18.0; prior tags untouched
- NO_HELD marked; no GIA / hyperbrain / train / SaaS / economy claims
- Scope status == DRAFT (not FROZEN)

## Explicit exclusions

**NO_HELD:** Raft, N>2, multi-primary, ML, R2, R3, plaintext, Vault-ACME-req, GIA, SLO_chase, tag_schema, EVERY_fsync.

Authority: `council/COUNCIL_AGREEMENT_HYPERBRAIN_ASTRA.md` (LOCKED).
