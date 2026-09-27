# Schema: mesh.wan.model/v0 (STUB)

**Status:** STUB (Cycle 56 / CP-0060) — design alignment only; no WAN runtime  
**Schema:** `mesh.wan.model/v0`  
**Design:** `docs/design/fabric/M3_WAN_MODEL_DESIGN.md`  
**Composes:** `mesh.clock.hlc/v1` (H7); `mesh.membership/v0` (M2 actors)  
**Non-goals:** no N>2; no Raft; no multi-primary; no GIA; wall_clock_as_authority=0

## WanModelRecord (`mesh.wan.model/v0`)

| Field | Type | Notes |
|-------|------|-------|
| `schema` | string | `mesh.wan.model/v0` |
| `rtt_ms` | number | measured/scenario RTT |
| `band` | string | `RTT_lo` \| `RTT_mid` \| `RTT_hi` \| `RTT_x` |
| `jitter_ms` | number | p95 \|ΔRTT\| scenario |
| `loss_pct` | number | loss percent 0..100 |
| `p_partition` | number | scenario ∈ [0,1] |
| `p_label` | string | `P_rare` \| `P_occasional` \| `P_elevated` \| `P_hostile` |
| `partition_class` | string | `STABLE` \| `SPLIT` \| `HEAL` \| `FLIP_FLOP` \| `CASCADE` |
| `hlc` | object | `mesh.clock.hlc/v1` stamp |
| `dual_primary` | int | **must be 0** |
| `n_cap` | int | **must be 2** while N>2 NO_HELD |
| `wall_clock_as_authority` | int | **must be 0** |
| `abort_code` | string\|null | last ABORT if any |

## Latency bands

| Band | RTT (ms) |
|------|----------|
| `RTT_lo` | `[0, 50)` |
| `RTT_mid` | `[50, 200)` |
| `RTT_hi` | `[200, 1000)` |
| `RTT_x` | `≥ 1000` |

## Partition classes

`STABLE → SPLIT → HEAL → STABLE`; also `FLIP_FLOP`, `CASCADE` (see design).

## Invariants (schema-level)

- `dual_primary == 0`
- `n_cap == 2`
- `wall_clock_as_authority == 0`
- `0 ≤ p_partition ≤ 1`
- HLC `(logical, counter)` is ordering authority; `wall_ms` advisory only

## ABORT codes (WAN model)

| Code | Meaning |
|------|---------|
| `WAN_BAND_EXTREME_DEFAULT` | RTT_x used as production default |
| `WAN_LOSS_ENVELOPE_EXCEEDED` | loss above band envelope |
| `WAN_JITTER_ENVELOPE_EXCEEDED` | jitter above band envelope |
| `WAN_WALL_CLOCK_AS_AUTHORITY` | wall claimed as order authority |
| `WAN_N_GT2_REFUSED` | N>2 runtime claim |
| `WAN_P_PARTITION_INVALID` | P_partition outside [0,1] |
| `WAN_CLASS_UNKNOWN` | unknown partition class |
| `WAN_HLC_ORDER_VIOLATION` | non-HLC event order claim |
