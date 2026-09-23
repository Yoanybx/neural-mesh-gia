# C-RAM Replica N=2 — Interface (Cycle 6 Implemented)

**Status:** Active controlled sandbox implementation (Cycle 6). See also
`docs/cram_replica_n2_consistency.md` (FROZEN consistency model).
**Unlocks:** CP-0010 after tests + bench + audit.

## Purpose

Two-copy mirror of selected C-RAM keys so that `NODE_LOSS` of the primary can
still resolve to a live secondary and complete real recovery proof (`get` from
the surviving replica), under the frozen async W=1 / R=1 model.

## Implemented API

```python
from neural_mesh.cram.replication import ReplicaManager, ReplicaPlacement

mgr = ReplicaManager(root, topology, seed=42)
key = mgr.put_replicated(b"...", op_id="...")
mgr.create_replica(key)          # CREATED
mgr.sync_object(key, op_id="...")  # SYNCING → SYNCED | FAILED
mgr.verify_replica(key)
mgr.replica_status(key)
mgr.remove_replica(key)
mgr.check_failover(key)          # FAILOVER_AVAILABLE | FAILOVER_BLOCKED | PRIMARY_HEALTHY
mgr.promote(key, node_id=..., op_id="...")  # epoch++ + witness
mgr.anti_entropy_rejoin(key)     # Merkle-diff; returns seconds
```

## Types

- `ReplicaPlan` / `ReplicaPlacement`: deterministic primary ≠ secondary.
- `ReplicaStore` semantics via `ReplicaManager` (node-scoped `CRAMStore` roots).
- Object descriptor fields: `primary_node`, `replica_nodes[]`, `version`/`epoch`,
  `content_hash`, sync `status`.

## Recovery contract

1. `NODE_LOSS(primary)` → filter live topology.
2. If secondary verified (hash+version+integrity) ⇒ `FAILOVER_AVAILABLE`.
3. Corrupt / missing secondary ⇒ `FAILOVER_BLOCKED` (never optimistic recoverable).
4. Promote requires fencing (`epoch` increment + `.cram/witness`); fail-closed
   without fencing.

## Explicit non-goals

See consistency doc §2. No Raft/Paxos/quorum, no N>2, no geo, no ML placement,
no Phase 3 Router, no real multi-machine network.


## Consistency (Cycle 6 freeze)

See `docs/cram_replica_n2_consistency.md` (authoritative):

- async W=1 R=1, T_conv=5.0s
- epoch fencing + op_id idempotency
- tie-breaker: lex node_id + `.cram/witness` on promote
- anti-entropy Merkle-diff on rejoin
- non-goals: Raft/Paxos/quorum/N>2/geo/ML/Router


## Cycle 7 — OOP CLI

```bash
mesh cram replica serve --socket /tmp/cram.sock --root ./data --node-id node-02
mesh cram replica connect --socket /tmp/cram.sock --root ./data --put 'hello' --ping
```

Python:

```python
mgr = ReplicaManager(root, topology, mode="oop", socket_path="/tmp/cram.sock")
```

TLS is **EXPLICIT_DEBT**. In-process `mode="inprocess"` is test-only.
