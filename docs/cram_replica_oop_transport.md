# C-RAM Replica N=2 — Out-of-Process Transport (FROZEN Cycle 7 / P0)

**Status:** FROZEN merge gate (DeepSeek Cycle 7 + COUNCIL_AGREEMENT_CYCLE7).
**Date:** 2026-09-23 America/New_York (EDT).
**Scope:** Unix-domain socket transport between two processes. Extends Cycle 6
consistency (`docs/cram_replica_n2_consistency.md`) without changing W=1/R=1,
T_conv=5.0s, epoch fencing, op_id, or ≤1 writable primary.

This document is the authoritative **socket frontier** contract for Cycle 7.
Code must not diverge without a new council ADR.

---

## 1. Process / socket frontier

| Role | Process | Store root | Writable? |
|------|---------|------------|-----------|
| Primary | client / CLI caller | local `nodes/<primary>/` | yes (designated) |
| Secondary | `mesh cram replica serve` | local `nodes/<secondary>/` under `--root` | no (apply only) |

- Boundary = **OS process + Unix domain socket** (not in-memory calls).
- In-process `ReplicaManager(mode="inprocess")` remains **test-only** (Cycle 6 sims).
- Production / acceptance path for Cycle 7 = `mode="oop"` + `--socket`.

Communication is strictly **request/response stop-and-wait** (one in-flight
frame pair). No pipelining in Cycle 7.

---

## 2. Framing

```
+------------------+---------------------------+
| u32 BE length N  | N bytes payload (UTF-8 JSON) |
+------------------+---------------------------+
```

| Parameter | Value |
|-----------|-------|
| Length encoding | 4-byte big-endian unsigned |
| Payload | JSON object (message envelope) |
| Binary content | Base64 in `data_b64` field |
| **MAX_FRAME_BYTES** | **16_777_216** (16 MiB) including JSON overhead |
| Oversized frame | Reject: close socket; no partial apply |

Partial reads must buffer until a full frame is assembled. A mid-frame close
(EOF / RST) yields a transport error; receiver must **not** apply a truncated
payload.

---

## 3. Message types

| type | Direction | Purpose |
|------|-----------|---------|
| `HELLO` | C→S | `{node_id, role}` handshake |
| `HELLO_ACK` | S→C | `{node_id, ready: true}` |
| `PUT` | C→S | Apply bytes: `{op_id, epoch, content_hash, metadata, data_b64}` |
| `ACK` | S→C | `{op_id, ok, error?, content_hash?}` — **after durable fsync** |
| `GET` | C→S | `{content_hash}` |
| `GET_RESP` | S→C | `{ok, content_hash, data_b64?, epoch?, error?}` |
| `PING` / `PONG` | either | Liveness |
| `STATUS` / `STATUS_RESP` | C→S | `{node_id, keys_sample?, ready}` |
| `ERROR` | either | `{error}` non-recoverable protocol fault |

Secondary **must** `fsync` object (+ best-effort dir) **before** sending `ACK`
with `ok=true` (durability-before-ack).

---

## 4. Backpressure

- **Stop-and-wait:** sender may not emit another `PUT` until matching `ACK`
  (or transport error).
- Server accepts **one** client connection at a time in Cycle 7 (extra connect
  refused or queued briefly then refused).
- If peer send buffer fills, write blocks until `WRITE_TIMEOUT` then fails closed.
- No unbounded in-memory queues of pending PUTs.

---

## 5. Timeouts

| Timer | Default | Notes |
|-------|---------|-------|
| `CONNECT_TIMEOUT` | 2.0 s | socket connect |
| `READ_TIMEOUT` | 5.0 s | aligned with T_conv |
| `WRITE_TIMEOUT` | 5.0 s | send frame |
| `IDLE_TIMEOUT` | 30.0 s | optional server idle (serve loop) |

On timeout: close socket; treat as partition/crash for failover logic.
Rejoin + anti-entropy must still converge in **&lt; T_conv (5.0 s)** wall clock
once the peer is reachable again.

---

## 6. Explicit debt — TLS / auth

**NOT implemented in Cycle 7.** Unix sockets are intentional local-only IPC.

| Debt | Status |
|------|--------|
| TLS / mTLS on transport | **EXPLICIT DEBT** — document only; no silent TODO in code paths that claim security |
| AuthN / AuthZ of peer | **EXPLICIT DEBT** |
| Abstract AF_UNIX → TCP/WAN | Out of scope (would require TLS debt closed first) |

Do not ship Cycle 7 claiming network-safe replication.

---

## 7. Consistency carry-forward (unchanged)

From Cycle 6 freeze:

- async W=1 R=1, T_conv=5.0 s
- epoch fencing + op_id idempotency
- ≤1 writable primary (lex node_id + `.cram/witness`)
- anti-entropy Merkle-diff on rejoin

OOP overhead SLO (Cycle 7): **p99 &lt; 10×** single-node (relaxed vs in-process &lt;5×).

---

## 8. Non-goals (Cycle 7)

- Phase 3 Cognitive Router
- N&gt;2, Raft/Paxos/quorum
- ML placement
- TLS/auth (see §6)
- Multi-client concurrent writers over one socket

---

## 9. Acceptance checklist (Cycle 7)

- [ ] This transport doc frozen
- [ ] `mesh cram replica serve|connect --socket` works
- [ ] Real kill -9 + mid-frame cut: **0** scenarios with 2 writable primaries
- [ ] Rejoin mid-frame crash converges &lt; T_conv; op_id dups still 0/100
- [ ] OOP overhead p99 &lt; 10× (honest)
- [ ] pytest ≥ 110; audit PASS; **CP-0011 VERIFIED**
- [ ] CP-0001..0010 still verify
