# Phase 5A — N=2 Active-Passive Replication over Fabric mTLS (FROZEN Cycle 12 / P0)

**Status:** FROZEN merge gate (council `COUNCIL_AGREEMENT_CYCLE12.md`).
**Date:** 2026-09-23 America/New_York (EDT).
**Checkpoint target:** CP-0016 / version 0.12.0.
**Builds on:** Cycle 6/7 replica (epoch/fencing/promote) + Cycle 11 Network Fabric mTLS.

This document freezes the Phase 5A contract. Code must not diverge without a new council ADR.

---

## 1. Roles (exactly N=2)

| Role | Count | Writes | Reads | Notes |
|------|-------|--------|-------|-------|
| **PRIMARY** | 1 | accepted | accepted | Sole writable authority for the object epoch |
| **STANDBY** | 1 | **rejected** | accepted (verified copies) | Apply replica appends only; never dual-primary |

- Topology is fixed **N=2**. No dynamic membership, no N>2, no multi-primary.
- Feature flag **`NEURAL_MESH_PHASE5A_REPLICATION`** (default **OFF**):
  - **OFF** → single-node C11 path intact (local C-RAM / Fabric TASK path only).
  - **ON** → remote C-RAM API + active-passive replica over Fabric mTLS.

---

## 2. Epoch and fencing

- Every object key carries a monotonic integer **`epoch`** (starts at 0) and **`version`** (aligned with epoch on promote).
- Mutating remote/replica ops carry: `version`, `epoch`, `object_hash`, `node_id`, `op_id`.
- Rules (fail-closed):
  - `epoch < current_epoch` → **reject** (`REJECTED_STALE_EPOCH`).
  - `object_hash` mismatch vs expected content → **reject** (`HASH_MISMATCH`).
  - Unknown / unverified state → explicit typed error (never silent invent).
- On controlled **promote**: surviving standby increments epoch, becomes sole `writable_primary`, old primary with lower epoch cannot write.

---

## 3. Promote (manual / controlled)

Messages:

| Type | Direction | Purpose |
|------|-----------|---------|
| `ROLE_STATUS` | either | Advertise role, epoch, writable_primary |
| `PROMOTE_REQUEST` | standby→authority / operator | Request fencing promote |
| `REPLICA_APPEND` | primary→standby | Ship object bytes + meta |
| `REPLICA_ACK` | standby→primary | Ack apply / reject reason |

Promote is **manual/controlled** (CLI / API call). Aggressive auto-failover without fencing is **out of scope**.

**Invariant:** under partition, kill -9 mid-handshake/mid-frame, invalid cert, or promote under partition → **`dual-primary = 0`**. Minority / non-fenced side is read-only or rejected.

---

## 4. Transport and fail-closed

- **Remote path:** Fabric **mTLS required**. No silent plaintext fallback.
- **AF_UNIX** remains for local/test when TLS is not required (C11 coexistence).
- Framing: 16 MiB max (Cycle 7/11).
- Invalid cert → `FABRIC_TLS_ERROR`; plaintext attempt when TLS required → `FABRIC_PLAINTEXT_FORBIDDEN`.
- Vault / ACME / public PKI: **not required** (optional EXPLICIT DEBT).

---

## 5. Remote C-RAM API

```
put_remote(node, object) → content_hash
get_remote(node, hash) → bytes
verify_remote(node, hash) → bool
checkpoint_remote(...) → notice hash / metadata
```

Modules: `cram/remote_protocol.py`, `remote_client.py`, `remote_store.py`.

---

## 6. Observability (light)

Each remote/replica op records:

- `trace_id`, `operation_id`, `node_path`, `latency_ms`, `result`

CLI: `mesh cram trace <operation_id>` reconstructs minimally:

`Task → Router → Network → C-RAM → Checkpoint`

---

## 7. Explicit non-goals (Hard NO)

- Raft / Paxos / ZAB / quorum consensus
- N>2, multi-primary, CRDT, dynamic membership
- ML / adaptive routing
- Silent plaintext fallback
- Vault/ACME mandatory
- Aggressive auto-failover without fencing
- Phase 6

---

## 8. Acceptance (CP-0016)

- pytest ≥250; audit PASS; version **0.12.0**
- integrity = 1.0; dual-primary = 0; plaintext fallback = 0
- Bench N=1000: remote put/get p50/p99; replica overhead p99 &lt;1.0 ms **OR** &lt;2× C11 persistent; recovery p99 &lt;250 ms; thruput ≥50% C11 (≥3300 msg/s)
- Feature flag OFF restores C11 single-node behavior
- Historical CP-0001..0015 remain VERIFIED

