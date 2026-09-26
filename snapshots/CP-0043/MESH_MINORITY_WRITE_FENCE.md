# Mesh Minority-Write Fence

**Capability:** `MESH_MINORITY_WRITE_FENCE`  
**Cycle / Checkpoint:** 39 / CP-0043  
**Version:** 0.18.0  
**Theme:** `0.18_H6_minority_write` (blueprint L2 H6 / minority_write@N2)  
**Depends on:** H3 dual-primary fence (`mesh.fence/v1`), C-RAM N2 consistency fail-closed minority reject

## Purpose

Ship **minority-write detection @N=2**, **ABORT→halt writes**, and the
**MINORITY_WRITES=0** invariant so a partition / non-primary side never silently
commits writes — without Raft, without N>2 / multi-primary architecture, without
plaintext, and without Vault/ACME or GIA claims.

## What shipped

| Surface | Location |
|---------|----------|
| Library | `src/neural_mesh/minority/` — models, store, `MinorityService`, CLI helpers |
| Schema | `mesh.minority/v1` — `docs/schema/minority_write/v1.md` |
| CLI | `mesh minority status \| probe \| halt` |
| Tests | `tests/test_minority_write_cycle39.py` (marker `minority_write_cycle39`) — T-H6a(+neg) |
| Seal | `snapshots/CP-0043/` |

### Operator flows

1. **`mesh minority status --data-root DIR`** — pair, writable primary, halt/abort flags; `minority_writes` hard 0 in report.
2. **`mesh minority probe --data-root DIR [--no-auto-halt]`** — detect pending minority-write; with auto-halt (default) run ABORT→halt writes; with `--no-auto-halt` enter abort and fail closed.
3. **`mesh minority halt --data-root DIR [--reason TEXT]`** — explicit ABORT→halt writes; all further writes refused.

### Library flows

```
bootstrap_pair(n-a, n-b, primary=n-a)
try_write(primary, key) → accepted
try_write(minority, key) → rejected_minority; ABORT→halt writes; minority_writes=0
try_write(any, key) while halted → rejected_halted
probe(auto_halt=true) → ABORT→halt writes when pending
probe(--no-auto-halt) → enter abort_halt_writes; never silent continue
```

### MINORITY_WRITES intent = 0

Every status / probe / halt / write result forces `minority_writes=0` in serialized
reports. Live detection uses `minority_write_detected` / claimant lists / rejected
attempt counters; success never means "a minority write committed". Rejected
attempts are logged for diagnostics only.

## Bounds (NO_HELD)

| Held | Meaning here |
|------|----------------|
| No Raft / N>2 / multi-primary | Exactly N=2 pair; `MinorityN2Only` on N>2 |
| No silent plaintext | `mode=plaintext` refused (`MINORITY_PLAINTEXT_FORBIDDEN`) |
| No Vault/ACME required | Filesystem minority state only |
| No GIA / SLO chase | No minority P99 chase; no GIA claims |
| No H7..H8 | clock_skew / manifest parity deferred |
| dual_primary | **Hard 0** (unchanged) |
| silent_minority_write | **Permanent NO_HELD** — MINORITY_WRITES must remain 0 |

## Explicit non-claims

- Not Raft / quorum consensus.
- Not multi-primary heal / N>2 cluster.
- Not GIA / AGI.
- Does not reopen 0.16.3 / 0.17.0 tags.
- Does not implement H7..H8 this cycle.
