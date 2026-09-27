# Schema: mesh.orchestrator.routing*/v0 (STUB)

**Status:** STUB (Cycle 60 / CP-0064) — design alignment only; no runtime codec  
**Schemas:** `mesh.orchestrator.routing_envelope/v0` · `mesh.orchestrator.routing_receipt/v0` · `mesh.judge.capability/v0`  
**Design:** `docs/design/ORCHESTRATOR_JUDGE_ROUTING_DESIGN.md`  
**Composes:** `mesh.judge.*/v0` · `mesh.membership/v0` · `mesh.wan.model/v0` · `mesh.goal/v0` · `mesh.continuity/v0`  
**Non-goals:** no live multi-engine; no train; no GIA; no M1 consensus via dual-judge; live=DISABLED

## RoutingEnvelope (`mesh.orchestrator.routing_envelope/v0`)

| Field | Type | Notes |
|-------|------|-------|
| `schema` | string | `mesh.orchestrator.routing_envelope/v0` |
| `request_id` | string | uuid |
| `goal_id` | string | `goal:<hash16>` required |
| `continuity_id` | string\|null | required for CONTINUITY_RESUME |
| `workload_class` | string | see design §3.1 |
| `action_class` | string | `A0`..`A4` |
| `member_state` | string | M2 state |
| `trust_tier` | string | `T0`..`T3` |
| `latency_band` | string | `RTT_lo`\|`RTT_mid`\|`RTT_hi`\|`RTT_x` |
| `prefer_dual` | bool | hint for critique |
| `oversight` | object | approved / deny / deadman_ok |
| `dual_primary` | int | **must be 0** |
| `n_members` | int | **must be ≤2** |
| `live_api_enabled` | bool | **must be false** |

## JudgeCapability (`mesh.judge.capability/v0`)

| Field | Type | Notes |
|-------|------|-------|
| `engine_id` | string | `judge:<id>` |
| `provider` | string | opaque; mock only this CP |
| `model_hint` | string | non-secret |
| `supports` | string[] | workload classes |
| `max_latency_band` | string | highest tolerable band |
| `trust_floor` | string | min tier to invoke |
| `live` | bool | **must be false** this CP |

## RoutingReceipt (`mesh.orchestrator.routing_receipt/v0`)

| Field | Type | Notes |
|-------|------|-------|
| `receipt_id` | string | `rcpt:<hash16>` |
| `decision` | string | `ALLOW`\|`ABORT` |
| `policy` | string | SINGLE_JUDGE\|DUAL_JUDGE_ADVISORY\|FALLBACK_CHAIN\|MESH_LOCAL |
| `target` | string | L_JUDGE\|AGENT_SHELL\|MESH_LOCAL\|NONE |
| `engine_ids` | string[] | selected engines |
| `reason` | string | short why |
| `prompt_hash` | string\|null | sha256 |
| `response_hash` | string\|null | sha256 |
| `goal_id` / `continuity_id` | string | durable hooks |
| `abort` | object\|null | code/reason |
| `dual_primary` | int | **0** |
| `live_api` | bool | **false** |
| `advisory_only` | bool | **true** for dual |
| `prev_receipt_hash` | string\|null | hash chain |

## ABORT codes

ROUTE_LIVE_DISABLED · ROUTE_MEMBER_NOT_ACTIVE · ROUTE_MEMBER_DRAINING ·
ROUTE_OVERSIGHT_REQUIRED · ROUTE_OVERSIGHT_DENIED · ROUTE_DEADMAN_REQUIRED ·
ROUTE_NO_CAPABLE_ENGINE · ROUTE_DUAL_UNDERPROVISIONED · ROUTE_JUDGE_MISMATCH ·
ROUTE_FALLBACK_EXHAUSTED · ROUTE_N_GT2_REFUSED · ROUTE_POLICY_UNKNOWN ·
ROUTE_SCHEMA_INVALID · FENCE

**NO_HELD:** Raft,N>2,multi-primary,ML,R2,R3,plaintext,Vault-ACME-req,GIA,SLO_chase,tag_schema,EVERY_fsync
