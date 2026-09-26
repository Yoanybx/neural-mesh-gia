# Schema: mesh.judge.*/v0 (STUB)

**Status:** STUB (Cycle 47 / CP-0051) — design alignment only; no runtime codec  
**Schemas:** `mesh.judge.request/v0` · `mesh.judge.response/v0` · `mesh.judge.receipt/v0`  
**Design:** `docs/design/L_JUDGE_MIX_DESIGN.md`  
**Non-goals:** no train-70B; no GIA; no silent plaintext; engine ephemeral

## JudgeRequest (`mesh.judge.request/v0`)

| Field | Type | Notes |
|-------|------|-------|
| `schema` | string | `mesh.judge.request/v0` |
| `request_id` | string | uuid |
| `idempotency_key` | string | required |
| `goal_id` | string | `goal:<hash16>` |
| `mode` | string | `dry_run` \| `live_advisory` |
| `policy_bundle_id` | string | |
| `inputs` | object | prompt_ref, artifacts[], constraints |
| `engine` | object | provider/model_hint/endpoint_ref (no secrets) |
| `continuity_hint` | object | step_id, resume_token |

## JudgeResponse (`mesh.judge.response/v0`)

| Field | Type | Notes |
|-------|------|-------|
| `verdict` | string | `ACCEPT` \| `REJECT` \| `ABSTAIN` \| `ABORT` |
| `confidence` | number | 0..1 |
| `rationale_digest` | string | sha256 |
| `receipt_id` | string | |
| `abort` | object\|null | code/reason |

## JudgeReceipt (`mesh.judge.receipt/v0`)

Durable Mesh-owned hash-chained receipt; see design doc. `dual_primary` hard **0**.

## ABORT

schema_invalid · policy_abort · engine_timeout · no_audit · fence

**NO_HELD:** Raft,N>2,multi-primary,ML,R2,R3,plaintext,Vault-ACME-req,GIA,SLO_chase,tag_schema,EVERY_fsync
