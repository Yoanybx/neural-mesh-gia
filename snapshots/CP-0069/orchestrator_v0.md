# Schema: mesh.orchestrator.oversight*/v0 (STUB)

**Status:** STUB (Cycle 65 / CP-0069) — design alignment only; no runtime codec  
**Schemas:** `mesh.orchestrator.oversight_decision/v0` · `mesh.orchestrator.oversight_receipt/v0`  
**Design:** `docs/design/ORCHESTRATOR_OVERSIGHT_HOOKS_DESIGN.md`  
**Policy:** `docs/oversight/deadman-v1.md`  
**Composes:** `mesh.orchestrator.continuity_*/v0` · `mesh.orchestrator.routing_*/v0` · `mesh.evidence/v0`  
**Non-goals:** no live multi-engine; no train; no GIA; no consciousness SoT; live=DISABLED

## OversightDecision (`mesh.orchestrator.oversight_decision/v0`)

| Field | Type | Notes |
|-------|------|-------|
| `schema` | string | `mesh.orchestrator.oversight_decision/v0` |
| `decision_id` | string | `ovs:<hash16>` |
| `verb` | string | approve\|deny\|pause\|resume\|kill\|deadman_refresh\|consent_revoke\|tick_deadman |
| `actor` | string | `human:<seat>` |
| `goal_id` / `continuity_id` | string | durable hooks |
| `action_class` | string | `A0`..`A4` |
| `bound_engine_ids` | string[] | judges this decision binds (CP-0064) |
| `quorum_ok` | bool | A4/kill dual-seat |
| `deadman_ok` | bool | A4 freshness |
| `t_dead` | int | default 86400 |
| `t_dead_override_logged` | bool | P-11 |
| `result` | string | ALLOW\|ABORT\|BLOCKED\|PAUSED\|DRAIN |
| `abort` | object\|null | code/reason |
| `refuse_transport` | bool | kill / HUMAN_ABORT |
| `dual_primary` | int | **must be 0** |
| `live_api` | bool | **must be false** |
| `created_hlc` | string | HLC (not wall-clock authority) |
| `prev_decision_hash` | string\|null | hash chain |

## OversightReceipt (`mesh.orchestrator.oversight_receipt/v0`)

| Field | Type | Notes |
|-------|------|-------|
| `schema` | string | `mesh.orchestrator.oversight_receipt/v0` |
| `receipt_id` | string | `rcpt:<hash16>` |
| `decision_id` | string | links OversightDecision |
| `continuity_state` | string | ContinuityState enum |
| `continuity_receipt_id` | string\|null | compose CP-0068 |
| `routing_receipt_id` | string\|null | compose CP-0064 |
| `result` | string | ALLOW\|ABORT\|BLOCKED\|PAUSED\|DRAIN |
| `abort` | object\|null | |
| `dual_primary` | int | **0** |
| `live_api` | bool | **false** |
| `prev_receipt_hash` | string\|null | |

## Evidence kinds (additive)

`oversight` · `deadman_override` · (+ continuity/routing kinds)

## Oversight ABORT codes

OVS_REQUIRED · OVS_DENIED · OVS_PAUSED · OVS_KILLED · OVS_DEADMAN_REQUIRED ·
OVS_DEADMAN_EXPIRED · OVS_QUORUM_REQUIRED · OVS_CLASS_BYPASS · OVS_CONSENT_REVOKED ·
OVS_LIVE_DISABLED · OVS_N_GT2_REFUSED · OVS_SCHEMA_INVALID · FENCE

(Plus CP-0064 `ROUTE_*` and CP-0068 `CONT_*` when delegated.)

**NO_HELD:** Raft,N>2,multi-primary,ML,R2,R3,plaintext,Vault-ACME-req,GIA,SLO_chase,tag_schema,EVERY_fsync
