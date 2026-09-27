# Mesh M2 Membership + Rejoin Design

**Capability:** `MESH_M2_MEMBERSHIP_REJOIN_DESIGN`  
**Cycle / Checkpoint:** 55 / CP-0059  
**Version:** package **0.18.0** held  
**Status:** DESIGN ONLY  
**Scope:** Membership/rejoin state machine + H1 tier composition; no N>2 runtime; no Raft

## Gates

| Gate | Meaning |
|------|---------|
| Design present | `docs/design/fabric/M2_MEMBERSHIP_REJOIN_DESIGN.md` |
| States | JOINING→ATTESTING→ACTIVE→DRAINING→LEFT→REJOIN |
| H1 compose | ACTIVE ⇒ T2\|T3; attest path mandatory |
| Helpers + neg tests | packaging `m2_membership_rejoin` mocks |
| M1 orthogonal | NO_CONSENSUS_YET unchanged |
| NO_HELD held | No Raft/N>2/multi-primary/GIA |

## Preferred next

`await_deepseek` (C55 M2 design + SENIOR_PROPOSALS verdict)

## NO_HELD

**NO_HELD:** Raft,N>2,multi-primary,ML,R2,R3,plaintext,Vault-ACME-req,GIA,SLO_chase,tag_schema,EVERY_fsync
