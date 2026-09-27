# Schema: mesh.orchestrator.continuity*/v0 (STUB)

**Status:** STUB (Cycle 64 / CP-0068) — design alignment only; no runtime codec  
**Schemas:** `mesh.orchestrator.inflight/v0` · `mesh.orchestrator.continuity_receipt/v0` ·
extends `mesh.continuity/v0` · `mesh.evidence/v0` · `mesh.goal/v0`  
**Design:** `docs/design/ORCHESTRATOR_CONTINUITY_DESIGN.md`  
**Composes:** `mesh.orchestrator.routing_*/v0` · `mesh.membership/v0` · `mesh.wan.model/v0`  
**Non-goals:** no live multi-engine; no train; no GIA; no consciousness SoT; live=DISABLED

## InFlightRecord (`mesh.orchestrator.inflight/v0`)

| Field | Type | Notes |
|-------|------|-------|
| `schema` | string | `mesh.orchestrator.inflight/v0` |
| `invoke_id` | string | `inv:<hash16>` |
| `idempotency_key` | string | required; at-most-once |
| `goal_id` | string | `goal:<hash16>` |
| `continuity_id` | string | `cont:<hash16>` |
| `request_id` | string | uuid |
| `engine_ids` | string[] | selected engines |
| `member_state_at_start` | string | M2 state at open |
| `status` | string | `OPEN\|SEALED\|ORPHANED\|TIMED_OUT\|ABORTED` |
| `opened_hlc` / `deadline_hlc` | string | HLC (not wall-clock authority) |
| `last_routing_receipt_id` | string\|null | |
| `payload_digest` | string | sha256 of invoke payload |
| `prev_entry_hash` | string\|null | ledger chain |

## ContinuityReceipt (`mesh.orchestrator.continuity_receipt/v0`)

| Field | Type | Notes |
|-------|------|-------|
| `schema` | string | `mesh.orchestrator.continuity_receipt/v0` |
| `receipt_id` | string | `rcpt:<hash16>` |
| `decision` | string | `ALLOW\|ABORT\|BLOCKED\|RESUMED` |
| `continuity_state` | string | ContinuityState enum |
| `goal_id` / `continuity_id` | string | durable hooks |
| `invoke_id` | string\|null | |
| `idempotency_key` | string | |
| `orphan_code` | string\|null | CONT_ORPHAN_* |
| `abort` | object\|null | code/reason |
| `routing_receipt_id` | string\|null | compose CP-0064 |
| `dual_primary` | int | **must be 0** |
| `live_api` | bool | **must be false** |
| `prev_receipt_hash` | string\|null | hash chain |
| `created_hlc` | string | |

## Evidence kinds (additive)

`routing_receipt` · `judge_receipt` · `invoke_start` · `invoke_end` · `orphan` ·
`resume` · `timeout` · `abort` · `human_note` · `probe`

## Continuity ABORT codes

CONT_ORPHAN_LEFT · CONT_ORPHAN_REJOIN_PENDING · CONT_ORPHAN_DRAIN ·
CONT_ORPHAN_DROP_FORBIDDEN · CONT_IDEMPOTENCY_CONFLICT · CONT_TIMEOUT_SOFT ·
CONT_TIMEOUT_HARD · CONT_LIVE_DISABLED · CONT_N_GT2_REFUSED · CONT_SCHEMA_INVALID ·
CONT_RESUME_FORBIDDEN_TERMINAL · FENCE

(Plus all CP-0064 `ROUTE_*` codes when delegated.)

**NO_HELD:** Raft,N>2,multi-primary,ML,R2,R3,plaintext,Vault-ACME-req,GIA,SLO_chase,tag_schema,EVERY_fsync
