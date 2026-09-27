# Schema: mesh.judge.injection/v0 (STUB)

**Status:** STUB (Cycle 48 / CP-0052) — integration injection envelope; no runtime codec  
**Design:** `docs/design/L_JUDGE_MIX_INTEGRATION.md`  
**Parent schemas:** `mesh.judge.request/v0` · `mesh.goal/v0` · `mesh.continuity/v0` · `mesh.evidence/v0`

## InjectionEnv (`mesh.judge.injection/v0`)

| Field | Type | Notes |
|-------|------|-------|
| `schema` | string | `mesh.judge.injection/v0` |
| `goal` | object | subset GoalRecord (goal_id, version, content_digest, title, terminal) |
| `continuity` | object | subset ContinuityState |
| `obs_evidence` | array | EvidenceEntry digests (hash-chained) |
| `policy_bundle_id` | string | |
| `fence` | object | `dual_primary` must be **0**; `minority_writes` must be **0** |

## Gate sequence

1. Validate JudgeRequest schema  
2. Build InjectionEnv; refuse if fence broken  
3. dry_run / submit per I2  
4. Parse JudgeResponse; ABORT on schema failure (never silent ACCEPT)  
5. Emit JudgeReceipt + OBS + EvidenceEntry  

## Non-goals

No live API keys · no train-70B · no GIA · no src codec this cycle

**NO_HELD:** Raft,N>2,multi-primary,ML,R2,R3,plaintext,Vault-ACME-req,GIA,SLO_chase,tag_schema,EVERY_fsync
