# Schema: mesh.judge.live_http_transport/v0 (STUB)

**Status:** STUB (Cycle 72 / **CP-0076 DESIGN_ONLY**) — alignment only; **no runtime live codec**  
**Schemas:** `mesh.judge.live_http_transport/v0` · ties to `mesh.judge.live_adapter_config/v0` · `mesh.judge.live_adapter_safety/v0`  
**Design:** `docs/planning/LIVE_HTTP_TRANSPORT_RESIDUAL_DESIGN.md`  
**Compose:** CP-0058 safety · CP-0068 continuity · CP-0069 oversight · CP-0075 canary = separate minimum  
**Non-goals:** no codec impl · no live enable · no keys · no push/tags · NO_HELD unchanged

## LiveHttpTransportPolicy (`mesh.judge.live_http_transport/v0`)

| Field | Type | Notes |
|-------|------|-------|
| `schema` | string | `mesh.judge.live_http_transport/v0` |
| `enabled` | bool | **must be false** as product default (runtime LIVE window only under fences) |
| `mode` | string | `unary` \| `streaming` \| `stream_unary_fallback` — default design `unary` |
| `streaming_allowed` | bool | **false** (v0 unary only; streaming residual) |
| `secret_handle` | string\|null | `mesh://secrets/...@vN` ref only |
| `tls_required` | bool | **true** |
| `forbid_plaintext` | bool | **true** |
| `idempotency_required` | bool | **true** (Mesh Continuity key) |
| `max_retries` | int | floor default **1** (must not loosen without evidence) |
| `backoff` | object | `{ strategy: "exponential_full_jitter", bound_by_timeout: true }` |
| `timeout_s` | number | floor default **30** |
| `soft_timeout_s` | number\|null | ≤ `timeout_s` |
| `max_raw_bytes` | int | floor default **65536** |
| `max_calls_per_minute` | int | floor default **10** |
| `max_calls_per_hour` | int | floor default **120** |
| `max_concurrent` | int | floor default **1** |
| `audit_required` | bool | **true** (no-audit=no-action) |
| `compose_continuity` | bool | **true** — InFlightTracker / orphan / resume |
| `compose_oversight` | bool | **true** — I5 kill/pause/deadman |
| `refuse_transport_default` | bool | **true** |
| `must_stay_false` | object | see below |

### must_stay_false / status (under CP-0078)

| Key | Value |
|-----|-------|
| `live_adapter.enabled` | false (product default) |
| `LIVE_API_ENABLED` | false (module default) |
| `live_api_in_ci` | false |
| `src_live_codec_shipped` | **true** (packaging v0 under CP-0078) |
| `codec_impl_authorized_by_cp_0078` | **true** |
| `mesh_is_frontier_model` | false (permanent) |
| `train_70b` | false (permanent) |
| `gia_unlocked` | false (NO_HELD) |
| `raft_runtime` | false (NO_HELD) |
| `n_gt_2` | false (NO_HELD) |
| `saas_settlement` | false |
| `engine_is_goal_sot` | false (permanent) |
| `silent_accept_on_error` | false (permanent) |
| `advisory_is_sot` | false (permanent) |
| `n1_is_slo` | false (permanent) |

## ABORT codes (transport residual)

Inherits CP-0058 live safety codes, plus continuity compose:

`ENGINE_DISABLED` · `ENGINE_AUTH` · `ENGINE_TLS` · `PLAINTEXT_FORBIDDEN` ·
`ENGINE_HTTP` · `ENGINE_TIMEOUT` · `ENGINE_RATE_LIMIT` · `SCHEMA_INVALID` ·
`NO_AUDIT` · `FENCE` · `POLICY_ABORT` · `HUMAN_ABORT` ·
`CONT_IDEMPOTENCY_CONFLICT` · `CONT_LIVE_DISABLED`

## Negative-test descriptor IDs

`T-lht-a` … `T-lht-l` — see design doc §5. Descriptors only; not a shipped suite claim.

## Fence

**CP-0076 does NOT authorize codec implementation and does NOT enable live.**  
CP-0075 free canary path remains the separate minimum.

**NO_HELD:** Raft,N>2,multi-primary,ML,R2,R3,plaintext,Vault-ACME-req,GIA,SLO_chase,tag_schema,EVERY_fsync
