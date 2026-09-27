# Mesh Perf — Literature Pointers (NON-DEFAULT)

**Status:** POINTER NOTE ONLY  
**Cycle / Checkpoint:** 62 / CP-0066  
**Purpose:** Name widely studied systems as **references for methodology and
latency literature** — **not** as Mesh defaults, and **not** as unlocked runtimes.

## Hard framing

| Mesh stance | Value |
|-------------|-------|
| M1 | **NO_CONSENSUS_YET** |
| Raft | **NO_HELD** (not a Mesh runtime choice this window) |
| N>2 | **NO_HELD** |
| Dual-judge advisory | ≠ consensus (CP-0064/0065) |
| Ranking vs these systems | **Forbidden** without shared harness |

## Pointers

### etcd
- Distributed key-value store commonly backed by Raft.
- Useful public literature on lease/watch/write latency and quorum costs.
- **NON_DEFAULT_REFERENCE** for Mesh. Do not imply Mesh embeds or replaces etcd.

### Raft
- Consensus algorithm (leader election + log replication).
- Classic papers and production war stories inform *how to measure* consensus paths.
- Mesh keeps Raft in **NO_HELD**. Pointing at Raft ≠ enabling Raft.

### CRDT
- Conflict-free replicated data types; strong literature on concurrent updates without
  global consensus.
- Orthogonal research pointer for future comparison methodology.
- **NON_DEFAULT_REFERENCE** — not Mesh substrate default.

## How to use these pointers later

1. Define a **shared harness** (workload, durability class, failure model).
2. Publish methodology before numbers.
3. Report Mesh **local baselines** beside peer numbers only under that harness.
4. Never emit "fastest in the world" or "beats X" from Mesh-only microbenches.

## Related

- `docs/design/MESH_PERF_RESEARCH_TRACK.md`
- M1 scorecard / design (NO_CONSENSUS_YET)
