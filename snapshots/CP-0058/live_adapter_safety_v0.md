# Schema: mesh.judge.live_adapter_safety/v0 (STUB)

**Status:** STUB (Cycle 54 / CP-0058) — design alignment only; no runtime live codec  
**Schemas:** `mesh.judge.live_adapter_safety/v0` · ties to `mesh.judge.live_adapter_config/v0`  
**Design:** `docs/design/L_JUDGE_LIVE_ADAPTER_SAFETY_CASE.md`  
**Non-goals:** no live API; no keys; no train-70B; no GIA; no silent plaintext

## LiveAdapterSafetyGate (`mesh.judge.live_adapter_safety/v0`)

| Field | Type | Notes |
|-------|------|-------|
| `schema` | string | `mesh.judge.live_adapter_safety/v0` |
| `enabled` | bool | **must be false** until evidence (§8 safety case) |
| `secret_handle` | string\|null | `mesh://secrets/...@vN` ref only |
| `refuse_transport_default` | bool | **true** |
| `tls_required` | bool | **true** |
| `forbid_plaintext` | bool | **true** |
| `require_prior_dry_run` | bool | **true** |
| `require_audit_sink` | bool | **true** (no-audit=no-action) |
| `max_calls_per_minute` | int | floor default 10 |
| `max_calls_per_hour` | int | floor default 120 |
| `max_retries` | int | floor default 1 |
| `timeout_s` | number | floor default 30 |
| `max_raw_bytes` | int | floor default 65536 |
| `max_concurrent` | int | floor default 1 |
| `must_stay_false` | object | see below |

### must_stay_false (until evidence)

| Key | Value until evidence |
|-----|----------------------|
| `live_adapter.enabled` | false |
| `live_api_in_ci` | false |
| `src_live_codec_shipped` | false |
| `mesh_is_frontier_model` | false (permanent) |
| `train_70b` | false (permanent) |
| `gia_unlocked` | false (NO_HELD) |
| `raft_runtime` | false (NO_HELD) |
| `n_gt_2` | false (NO_HELD) |
| `saas_settlement` | false |
| `engine_is_goal_sot` | false (permanent) |
| `silent_accept_on_error` | false (permanent) |

## secret_handle

Pattern (design): `mesh://secrets/<scope>/<name>@<version>`  
Invalid: raw `sk-…`, `api_key=…`, `Authorization: Bearer …` material in repo.

## ABORT codes (live safety)

`ENGINE_DISABLED` · `ENGINE_AUTH` · `ENGINE_TLS` · `PLAINTEXT_FORBIDDEN` ·
`ENGINE_HTTP` · `ENGINE_TIMEOUT` · `ENGINE_RATE_LIMIT` · `SCHEMA_INVALID` ·
`NO_AUDIT` · `FENCE` · `POLICY_ABORT` · `HUMAN_ABORT`

**NO_HELD:** Raft,N>2,multi-primary,ML,R2,R3,plaintext,Vault-ACME-req,GIA,SLO_chase,tag_schema,EVERY_fsync
