# Schema: mesh.clock/v1

**Status:** ACTIVE (Cycle 40 / CP-0044)  
**Schema id:** `mesh.clock/v1`  
**Store schema:** `mesh.clock.store/v1`  
**Sample schema:** `mesh.clock.sample/v1`  
**Join schema:** `mesh.clock.join/v1`  
**HLC schema:** `mesh.clock.hlc/v1`  
**Theme:** `0.18_H7_clock_skew`

## ClockStatus / ProbeResult

| Field | Type | Notes |
|-------|------|-------|
| `schema` | string | always `mesh.clock/v1` |
| `ok` | bool | |
| `pair` | string[] | exactly 0..2 node ids |
| `skew_ms` | int | absolute diagnostic wall delta |
| `skew_threshold_ms` | int | join-fence threshold (default 5000) |
| `skew_detected` | bool | live diagnostic (pending excess skew) |
| `wall_clock_as_authority` | int | **hard 0** (P-02) |
| `join_refused` | bool | ABORT→refuse join engaged |
| `abort_refuse_join` | bool | ABORT mode engaged |
| `dual_primary` | int | **hard 0** |
| `minority_writes` | int | **hard 0** |
| `vault_acme_required` | int | **hard 0** |
| `plaintext_fallback` | int | **hard 0** |
| `local_hlc` | object | HLC tuple (ordering authority) |
| `local_mono` | int | monotonic counter |
| `action` | string | probe: `none` \| `refuse_join` \| `abort_refuse_join` |

## HLC

| Field | Type | Notes |
|-------|------|-------|
| `schema` | string | `mesh.clock.hlc/v1` |
| `logical` | int | hybrid logical component |
| `counter` | int | tie-break counter |
| `wall_ms` | int | advisory snapshot only |
| `wall_clock_as_authority` | int | **hard 0** |

## ClockSample

| Field | Type | Notes |
|-------|------|-------|
| `schema` | string | `mesh.clock.sample/v1` |
| `node_id` | string | sample source |
| `wall_ms` | int | diagnostic wall |
| `hlc` | object | authoritative HLC at sample |
| `mono` | int | local mono at sample |
| `wall_clock_as_authority` | int | **hard 0** |

## JoinCheckResult

| Field | Type | Notes |
|-------|------|-------|
| `schema` | string | `mesh.clock.join/v1` |
| `outcome` | string | `accepted` \| `refused_skew` \| `refused_abort` \| `refused_unknown` |
| `skew_ms` | int | |
| `join_refused` | bool | |
| `wall_clock_as_authority` | int | **hard 0** |

## Error codes

| Code | Meaning |
|------|---------|
| `CLOCK_SKEW_DETECTED` | wall delta exceeds threshold / join refused |
| `CLOCK_ABORT_REFUSE_JOIN` | ABORT→refuse join engaged |
| `CLOCK_JOIN_REFUSED` | join refused while abort engaged |
| `CLOCK_N2_ONLY` | N>2 / duplicate pair refused |
| `CLOCK_NODE_UNKNOWN` | node_id not in pair |
| `CLOCK_PLAINTEXT_FORBIDDEN` | plaintext mode refused |

## Layout

```
<data-root>/
  clock/
    clock_state.json   # pair, threshold, walls, HLC/mono, abort flags
    samples.jsonl      # diagnostic clock samples
```
