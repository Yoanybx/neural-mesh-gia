# Schema: mesh.fence/v1

**Status:** ACTIVE (Cycle 36 / CP-0040)  
**Schema id:** `mesh.fence/v1`  
**Store schema:** `mesh.fence.store/v1`  
**Epoch schema:** `mesh.fence.epoch/v1`  
**Role schema:** `mesh.fence.role/v1`

## NodeRole

| Field | Type | Notes |
|-------|------|-------|
| `schema` | string | always `mesh.fence.role/v1` |
| `node_id` | string | member of N=2 pair |
| `role` | string | `primary` \| `secondary` \| `demoted` \| `none` |
| `fence_epoch` | int | last epoch this role was written |
| `durable_token` | string | bound token when primary |
| `dual_primary` | int | **hard 0** |
| `vault_acme_required` | int | **hard 0** |
| `plaintext_fallback` | int | **hard 0** |

## FenceEpoch

| Field | Type | Notes |
|-------|------|-------|
| `schema` | string | `mesh.fence.epoch/v1` |
| `epoch` | int | monotonic fence epoch |
| `writable_primary` | string\|null | sole elected primary |
| `durable_token` | string | content-ish token (not Raft term) |
| `pair` | string[] | exactly 0..2 node ids |
| `updated_at` | string | UTC |
| `dual_primary` | int | **hard 0** |

## FenceStatus / ProbeResult

| Field | Type | Notes |
|-------|------|-------|
| `ok` | bool | |
| `dual_primary_detected` | bool | live diagnostic (claimants > 1) |
| `dual_primary` | int | **hard 0** (intent; never success metric) |
| `abort_demote_reelect` | bool | ABORT mode engaged |
| `fence_epoch` | int | |
| `writable_primary` | string\|null | |
| `primary_claimants` | string[] | probe only |
| `action` | string | `none` \| `demote_reelect` \| `abort_demote_reelect` |

## Error codes

| Code | Meaning |
|------|---------|
| `FENCE_DUAL_PRIMARY` | dual-primary detected / refused claim |
| `FENCE_ABORT_DEMOTE_REELECT` | ABORT→demote+re-elect engaged / exhausted |
| `FENCE_UNRESOLVED` | dual-primary still live after fence attempt |
| `FENCE_N2_ONLY` | N>2 / duplicate pair refused |
| `FENCE_NODE_UNKNOWN` | node_id not in pair |
| `FENCE_PLAINTEXT_FORBIDDEN` | plaintext mode refused |

## Layout

```
<data-root>/
  fence/
    fence_state.json      # pair, abort_demote_reelect, abort_reason
    epoch.json            # FenceEpoch
    roles/<node_id>.json  # NodeRole
    witness.json          # PrimaryWitness sole writable primary
```
