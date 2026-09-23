# C-RAM Replica N=2 — Consistency Model (FROZEN Cycle 6 / P0)

**Status:** FROZEN merge gate (DeepSeek P0 + council COUNCIL_AGREEMENT_CYCLE6).
**Date:** 2026-09-23 America/New_York (EDT).
**Scope:** Controlled N=2 replication. Cycle 6 = in-process (test-only). Cycle 7 = out-of-process Unix socket (see `docs/cram_replica_oop_transport.md`). NOT real multi-machine WAN / TLS.

This document is the authoritative consistency contract for Cycle 6. Code must not
diverge from these rules without a new council ADR.

---

## 1. Replication model

| Parameter | Value | Notes |
|-----------|-------|-------|
| Mode | **async replication** | Primary acknowledges write; replica sync follows |
| Write quorum | **W=1** | Primary-ack only |
| Read quorum | **R=1** | Any live verified copy |
| Topology | **N=2** | Exactly one primary + one secondary when ≥2 live nodes |
| Bound | **T_conv = 5.0 s** | Eventual consistency convergence bound (in-process twin/sandbox; measured in P8) |

Writes succeed when the primary has durably stored the object and recorded the
op. Secondary sync is best-effort async; clients must not assume linearizability
across nodes.

---

## 2. Explicit non-goals

Cycle 6 does **not** provide or attempt:

- Linearizability / strict serializability
- Majority quorum (impossible for N=2 without sacrificing availability)
- Raft / Paxos / any consensus protocol
- N>2 replicas
- Geographic / WAN replication
- ML-based or learned placement
- Phase 3 Cognitive Router
- Automatic background promote without fencing (prefer fail-closed)
- Real multi-machine network I/O (sandbox topology + node-scoped stores only)

---

## 3. Epoch fencing

- Every object key has a monotonic integer **`epoch`** (starts at 0).
- Every mutating apply is `apply(op_id, epoch, ...)`.
- If `epoch < current_epoch` for that key → **reject silently** (idempotent stale
  write) and append a log record `REJECTED_STALE_EPOCH`.
- Promote / fencing: surviving replica increments epoch and becomes the sole
  writable primary for that key. Old primary with lower epoch cannot write.

---

## 4. Tie-breaker (split-brain guard)

Chosen combination (council freeze):

1. **Static lexicographic `node_id` priority** — higher `node_id` wins when two
   nodes both claim writable primary under a simulated partition.
2. **Local `.cram/witness`** — on promote, the promoting node writes
   `.cram/witness` (JSON: `epoch`, `node_id`, `object_hash`, `promoted_at`).
   Witness timestamp breaks residual ties and provides audit evidence.

**Invariant:** under any simulated partition, **≤1 writable primary** for a given
object key. The minority / lower-priority side is read-only or rejected.

---

## 5. op_id idempotency

- Every `put` / sync / promote that mutates replica state **requires** an `op_id`
  (opaque string, caller-supplied or generated UUID hex).
- Duplicate `op_id` → **single effect** (second apply is a no-op success).
- Acceptance: 100 retries with the same `op_id` → 0 duplicate side effects.

---

## 6. Anti-entropy on rejoin

- When a partitioned or divergent secondary rejoins, run **Merkle-diff per object**
  (minimal: content hash + epoch leaf; not a full store scan).
- Primary is source of truth for the current epoch.
- Divergent secondary is repaired by copying authoritative bytes + metadata.
- Measured wall-clock converge time must be **&lt; T_conv (5.0 s)** in-process.

---

## 7. Replica lifecycle states

```
CREATED → SYNCING → SYNCED
                 ↘ FAILED
```

| State | Meaning |
|-------|---------|
| CREATED | Placement chosen; secondary slot reserved; bytes not yet verified on secondary |
| SYNCING | Copy in progress |
| SYNCED | Secondary hash + version + integrity verified |
| FAILED | Sync or verify failed (hash mismatch, I/O, etc.) |

Failover status (separate from sync state):

| Status | Meaning |
|--------|---------|
| FAILOVER_AVAILABLE | Primary lost/unavailable AND replica passes hash+version+integrity |
| FAILOVER_BLOCKED | Primary lost but replica corrupt / unverified / missing |
| PRIMARY_HEALTHY | Primary live — no failover |

---

## 8. CLI exit codes (preserved from Cycle 5)

| Code | Meaning |
|------|---------|
| 0 | PASS |
| 1 | Generic CLI error |
| 2 | Integrity failure (corrupt) |
| 3 | Missing / unavailable |

Replica subcommands must not invent new exit codes.

---

## 9. SLO carry-forward

- Existing single-node / Cycle 5 **recovery_time p99 must remain &lt; 150 ms** when
  re-measured.
- Replication overhead p99 must be **&lt; 5×** single-node put latency (honest
  measurement; document if box variance is high).

---

## 10. Acceptance checklist (Cycle 6)

- [ ] Consistency doc frozen (this file) before / with implementation
- [ ] ≤1 writable primary in all partition sims
- [ ] T_conv measured &lt; 5.0 s
- [ ] Repl overhead p99 &lt; 5× single-node AND recovery p99 &lt; 150 ms
- [ ] op_id: 0 duplicates in 100 retries
- [ ] pytest ≥ 90; audit PASS; **CP-0010 VERIFIED**
- [ ] Historical CP-0001..0009 still verify


---

## 11. Cycle 7 amendment — out-of-process transport

- Socket frontier / framing / backpressure / timeouts: **frozen** in
  `docs/cram_replica_oop_transport.md`.
- In-process mode remains available as **test-only**.
- OOP overhead SLO: p99 **&lt; 10×** single-node (honest).
- TLS / auth: **EXPLICIT DEBT** (not silent).
- Consistency rules §§1–10 unchanged (W=1 R=1, T_conv, fencing, op_id, ≤1 writer).
