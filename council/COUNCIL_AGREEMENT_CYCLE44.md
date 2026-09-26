# Council Agreement — Cycle 44 / CP-0048

**Capability:** Freeze 0.19 plan scope from CP-0047 DRAFT  
**Title:** 0.19_scope_freeze (themes A–D)  
**Scope:** Docs only; promote DRAFT→FROZEN; no runtime; no GIA/Raft/N>2/train/SaaS/economy  
**Version:** package **0.18.0** HELD  
**Checkpoint:** `CP-0048`

## Semver note

Hold **0.18.0**. Do **not** open 0.19.0 / retag `v0.18.0`. Themes A–D FROZEN for plan ordering only.

## Deliverables

- `docs/planning/0.19_SCOPE_FROZEN.md` + `council/SCOPE_0.19_FROZEN.md`
- Mark `0.19_SCOPE_DRAFT` SUPERSEDED
- ≥8 tests (marker `scope_freeze_cycle44`)
- Snapshots/CP-0048 VERIFIED
- PREFERRED_NEXT=`agent_shell_adapter_spike_plan`

## Exclusions

**NO_HELD:** Raft,N>2,multi-primary,ML,R2,R3,plaintext,Vault-ACME-req,GIA,SLO_chase,tag_schema,EVERY_fsync
