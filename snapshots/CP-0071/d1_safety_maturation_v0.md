# Schema: mesh.judge.d1_safety_maturation/v0 (STUB)

**Status:** STUB (Cycle 67 / CP-0071) — design alignment only; no runtime live codec  
**Schemas:** `mesh.judge.d1_safety_maturation/v0`  
**Design:** `docs/planning/D1_L_JUDGE_SAFETY_CASE_MATURATION.md`  
**Non-goals:** no live API; no keys; no M1 default; no train-70B; no GIA

## D1SafetyMaturationGate (`mesh.judge.d1_safety_maturation/v0`)

| Field | Type | Notes |
|-------|------|-------|
| `schema` | string | `mesh.judge.d1_safety_maturation/v0` |
| `live_enabled` | bool | **must be false** |
| `m1_status` | string | `NO_CONSENSUS_YET` |
| `d4_debt_ids` | string[] | must include D4-A..K |
| `authority_matrix_frozen` | bool | D4-A |
| `continuity_verified_state_only` | bool | D4-C |
| `oversight_bounds_documented` | bool | D4-D |
| `rollback_verification_ids` | string[] | RV-1..RV-7 (D4-H) |
| `policy_version_required` | bool | D4-I provenance |
| `audit_completeness_required` | bool | D4-I |
| `d1_exit_ready_for_live` | bool | **must be false** (F4 separate) |
| `mesh_perf_experimental` | string | `OFF` |
| `composed_cps` | string[] | CP-0058, CP-0068, CP-0069 |

## Authority roles (summary)

| Component | propose | approve | veto | execute |
|-----------|---------|---------|------|---------|
| L_judge | Y | N | N | N |
| Oversight I5 | Y | Y | Y | N |
| Continuity | N | N | Y | N |
| Operator | Y | Y | Y | Y (gated) |

## Rollback verification IDs

`RV-1` .. `RV-7` — see planning doc §8.4.

**NO_HELD:** Raft,N>2,multi-primary,ML,R2,R3,plaintext,Vault-ACME-req,GIA,SLO_chase,tag_schema,EVERY_fsync
