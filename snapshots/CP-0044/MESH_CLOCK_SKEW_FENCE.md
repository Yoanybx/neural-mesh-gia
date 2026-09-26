# Mesh Clock-Skew Join Fence

**Capability:** `MESH_CLOCK_SKEW_FENCE`  
**Cycle / Checkpoint:** 40 / CP-0044  
**Version:** 0.18.0  
**Theme:** `0.18_H7_clock_skew` (blueprint L2 H7 / clock_skew@N2; P-02)  
**Depends on:** H6 minority-write fence (`mesh.minority/v1`)

## Purpose

Ship **clock-skew detection @N=2**, **ABORT→refuse join**, and the
**wall_clock_as_authority=0** invariant (blueprint P-02: HLC + monotonic
counters; wall-clock non-authoritative) so a skewed peer never silently
joins — without Raft, without N>2 / multi-primary architecture, without
plaintext, and without Vault/ACME or GIA claims.

## What shipped

| Surface | Location |
|---------|----------|
| Library | `src/neural_mesh/clock/` — models, HLC/mono helpers, store, `ClockService`, CLI helpers |
| Schema | `mesh.clock/v1` — `docs/schema/clock_skew/v1.md` |
| CLI | `mesh clock status \| probe \| join-check` |
| Tests | `tests/test_clock_skew_cycle40.py` (marker `clock_skew_cycle40`) — T-H7a(+neg) |
| Seal | `snapshots/CP-0044/` |

### Operator flows

1. **`mesh clock status --data-root DIR`** — pair, skew_ms / threshold, refuse/abort flags; `wall_clock_as_authority` hard 0 in report.
2. **`mesh clock probe --data-root DIR [--no-auto-refuse]`** — detect pending skew; with auto-refuse (default) run ABORT→refuse join; with `--no-auto-refuse` enter abort and fail closed.
3. **`mesh clock join-check --data-root DIR --node-id ID [--peer-wall-ms N] [--local-wall-ms N]`** — accept join within threshold; on excess skew ABORT→refuse join.

### Library flows

```
bootstrap_pair(n-a, n-b, skew_threshold_ms=5000)
tick() / receive_hlc(remote) → HLC advance (wall advisory only)
mono_next() → monotonic counter
record_sample(node, wall_ms=…) → diagnostic walls + HLC merge
join_check(peer, peer_wall_ms, local_wall_ms) within threshold → accepted
join_check(peer, …) with |Δwall| > threshold → refused_skew; ABORT→refuse join
join_check(any) while refused → refused_abort
probe(auto_refuse=true) → ABORT→refuse join when pending skew
probe(--no-auto-refuse) → enter abort_refuse_join; never silent continue
```

### P-02 / wall_clock_as_authority = 0

Every status / probe / join-check / sample forces `wall_clock_as_authority=0`
in serialized reports. Wall deltas are **diagnostic fence inputs only**.
Causal / ordering authority is **HLC (logical, counter)** plus local
**monotonic counters**. Wall clock alone never accepts a join or orders events.

## Bounds (NO_HELD)

| Held | Meaning here |
|------|----------------|
| No Raft / N>2 / multi-primary | Exactly N=2 pair; `ClockN2Only` on N>2 |
| No silent plaintext | `mode=plaintext` refused (`CLOCK_PLAINTEXT_FORBIDDEN`) |
| No Vault/ACME required | Filesystem clock state only |
| No GIA / SLO chase | No clock P99 chase; no GIA claims |
| No H8 | manifest parity deferred |
| dual_primary | **Hard 0** (unchanged) |
| minority_writes | **Hard 0** (unchanged) |
| wall_clock_as_authority | **Permanent NO_HELD** — always 0 |

## Explicit non-claims

- Not Raft / quorum consensus / HLC-total-order ratification (M1 still held).
- Not NTP sync / time authority service.
- Not multi-primary heal / N>2 cluster.
- Not GIA / AGI.
- Does not reopen 0.16.3 / 0.17.0 tags.
- Does not implement H8 this cycle.
