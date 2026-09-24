# Mesh Recovery + Rebuild

**Capability:** `MESH_RECOVERY_REBUILD`  
**Cycle / Checkpoint:** 35 / CP-0039  
**Version:** 0.18.0  
**Theme:** `0.18_H2_recovery` (blueprint L2 H2 / T-H2a..d)  
**Depends on:** `src/neural_mesh/checkpoint.py` (CheckpointManager / integrity hashing patterns), H1 identity store (fail-closed abort patterns)

## Purpose

Ship **recovery snapshot create/list/verify**, **restore from snapshot**,
**rebuild from last-good snapshot + WAL**, and **ABORT→snapshot restore**
without Raft, without N>2 / multi-primary, without silent continue on
tamper/missing snapshot, and without plaintext or Vault/ACME requirements.

## What shipped

| Surface | Location |
|---------|----------|
| Library | `src/neural_mesh/recovery/` — models, store, `RecoveryService` |
| Schema | `mesh.recovery/v1` — `docs/schema/recovery/v1.md` |
| CLI | `mesh recover status | snapshot | restore | rebuild` |
| Tests | `tests/test_recovery_cycle35.py` (marker `recovery_cycle35`) |
| Seal | `snapshots/CP-0039/` |

### Operator flows

1. **`mesh recover status --data-root DIR`** — durable seq/epoch, last_good, WAL length, abort_restore flag.
2. **`mesh recover snapshot --data-root DIR [--reason …]`** — create content-hashed snapshot; updates last_good.
3. **`mesh recover snapshot --data-root DIR --list`** — list snapshots.
4. **`mesh recover snapshot --data-root DIR --verify SNAP-id`** — integrity verify (fail-closed on tamper).
5. **`mesh recover restore --data-root DIR [--snapshot SNAP-id]`** — restore durable state from verified snapshot; truncates divergent WAL tail.
6. **`mesh recover rebuild --data-root DIR [--snapshot SNAP-id]`** — restore base from last good + replay WAL; on failure **ABORT→snapshot restore**.

### Recover / rebuild paths

```
apply(patch) → WAL append + durable update
create_snapshot → content-hash seal (state + wal_offset)
restore(SNAP) → verify → load state → truncate WAL after offset
rebuild → verify last_good → load state → replay WAL(after offset)
  on failure → ABORT→snapshot restore (alternate last_good / other verified)
```

### ABORT→snapshot restore

On recovery failure (tamper, missing snapshot, rebuild crash / unknown WAL op):

- Enter `abort_restore=true` in `recovery_state.json` (not silent continue).
- Attempt restore from last_good or another verified snapshot.
- Never invent a dual-primary / plaintext fallback.
- Operator clears abort via successful restore path / acknowledge.

## Bounds (NO_HELD)

| Held | Meaning here |
|------|----------------|
| No Raft / N>2 / multi-primary | Local data-root recovery only; dual_primary hard 0 |
| No silent plaintext | `mode=plaintext` refused (`RECOVERY_PLAINTEXT_FORBIDDEN`) |
| No Vault/ACME required | Filesystem snapshots + WAL only |
| No GIA / SLO chase | No recovery P99 chase; no GIA claims |
| No H3..H8 | Dual-primary fence and later themes deferred |

## Explicit non-claims

- Not Raft / consensus recovery.
- Not multi-primary heal.
- Not GIA / AGI.
- Does not reopen 0.16.3 / 0.17.0 tags.
