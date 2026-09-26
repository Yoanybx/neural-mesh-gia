# Mesh Dual-Primary Fence

**Capability:** `MESH_DUAL_PRIMARY_FENCE`  
**Cycle / Checkpoint:** 36 / CP-0040  
**Version:** 0.18.0  
**Theme:** `0.18_H3_dual_primary_fence` (blueprint L2 H3 / fence epoch + durable token)  
**Depends on:** `src/neural_mesh/network/witness.py` (`PrimaryWitness`), H2 recovery fail-closed abort patterns

## Purpose

Ship **dual-primary detection @N=2**, **demote + re-elect**, and
**ABORT→demote+re-elect** so a partition / split-brain never leaves
`dual_primary>0` as a successful operator status — without Raft, without
N>2 / multi-primary architecture, without plaintext, and without Vault/ACME
requirements.

## What shipped

| Surface | Location |
|---------|----------|
| Library | `src/neural_mesh/fence/` — models, store, `FenceService`, CLI helpers |
| Schema | `mesh.fence/v1` — `docs/schema/fence/v1.md` |
| CLI | `mesh fence status \| probe \| demote \| reelect` |
| Tests | `tests/test_fence_cycle36.py` (marker `fence_cycle36`) |
| Seal | `snapshots/CP-0040/` |

### Operator flows

1. **`mesh fence status --data-root DIR`** — pair, roles, fence epoch, writable primary, abort flag; `dual_primary` hard 0 in report.
2. **`mesh fence probe --data-root DIR [--preferred NODE] [--no-auto-fence]`** — detect dual-primary claimants; with auto-fence (default) run ABORT→demote+re-elect; with `--no-auto-fence` enter abort and fail closed.
3. **`mesh fence demote --data-root DIR --node-id NODE`** — demote a primary contender; bump fence epoch; keep sole remaining primary if any.
4. **`mesh fence reelect --data-root DIR [--preferred NODE]`** — elect exactly one writable primary (lexicographic default); demote other primaries.

### Fence / ABORT path

```
detect_dual_primary → claimants (>1)
probe(auto_fence=true) → ABORT→demote+re-elect
  demote contenders → elect sole primary → durable token + witness sync
  clear abort when dual_primary live count == 0
probe(--no-auto-fence) → enter abort_demote_reelect; never silent continue
reports always dual_primary=0 (intent); dual_primary_detected is diagnostic only
```

### dual_primary intent = 0

Every status / probe / demote / reelect / action result forces `dual_primary=0`
in serialized reports. Live detection uses `dual_primary_detected` / claimant
lists; success never means "dual primary is OK".

## Bounds (NO_HELD)

| Held | Meaning here |
|------|----------------|
| No Raft / N>2 / multi-primary | Exactly N=2 pair; `FenceN2Only` on N>2 |
| No silent plaintext | `mode=plaintext` refused (`FENCE_PLAINTEXT_FORBIDDEN`) |
| No Vault/ACME required | Filesystem fence state + PrimaryWitness only |
| No GIA / SLO chase | No fence P99 chase; no GIA claims |
| No H4..H8 | OBS telemetry and later themes deferred |

## Explicit non-claims

- Not Raft / quorum consensus.
- Not multi-primary heal / N>2 cluster.
- Not GIA / AGI.
- Does not reopen 0.16.3 / 0.17.0 tags.
- Does not implement H4..H8 this cycle.
