# Schema: mesh.minority/v1

**Status:** ACTIVE (Cycle 39 / CP-0043)  
**Schema id:** `mesh.minority/v1`  
**Store schema:** `mesh.minority.store/v1`  
**Attempt schema:** `mesh.minority.attempt/v1`  
**Halt schema:** `mesh.minority.halt/v1`  
**Theme:** `0.18_H6_minority_write`

## MinorityStatus / ProbeResult

| Field | Type | Notes |
|-------|------|-------|
| `schema` | string | always `mesh.minority/v1` |
| `ok` | bool | |
| `pair` | string[] | exactly 0..2 node ids |
| `writable_primary` | string\|null | sole elected primary (fence-compatible) |
| `minority_write_detected` | bool | live diagnostic (pending minority attempt) |
| `minority_writes` | int | **hard 0** (intent; never success metric) |
| `writes_halted` | bool | ABORT→halt writes engaged |
| `abort_halt_writes` | bool | ABORT mode engaged |
| `dual_primary` | int | **hard 0** |
| `vault_acme_required` | int | **hard 0** |
| `plaintext_fallback` | int | **hard 0** |
| `action` | string | probe: `none` \| `halt_writes` \| `abort_halt_writes` |

## WriteAttempt

| Field | Type | Notes |
|-------|------|-------|
| `schema` | string | `mesh.minority.attempt/v1` |
| `node_id` | string | writer claimant |
| `key` | string | logical object key |
| `outcome` | string | `accepted` \| `rejected_minority` \| `rejected_halted` \| `rejected_unknown` |
| `is_minority` | bool | true when node ≠ writable_primary |
| `minority_writes` | int | **hard 0** |

## Error codes

| Code | Meaning |
|------|---------|
| `MINORITY_WRITE_DETECTED` | minority write attempted / refused |
| `MINORITY_ABORT_HALT_WRITES` | ABORT→halt writes engaged |
| `MINORITY_WRITES_HALTED` | writes refused while halt engaged |
| `MINORITY_N2_ONLY` | N>2 / duplicate pair refused |
| `MINORITY_NODE_UNKNOWN` | node_id not in pair |
| `MINORITY_PLAINTEXT_FORBIDDEN` | plaintext mode refused |

## Layout

```
<data-root>/
  minority/
    minority_state.json   # pair, primary, halt/abort flags
    attempts.jsonl        # diagnostic write attempts (no committed minority)
```
