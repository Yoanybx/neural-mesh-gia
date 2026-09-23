# Phase 5B — C-RAM Consistency & Recovery Hardening (FROZEN Cycle 13 / P0)

**Status:** FROZEN merge gate (council `COUNCIL_AGREEMENT_CYCLE13.md`).
**Date:** 2026-09-23 America/New_York (EDT).
**Checkpoint target:** CP-0017 / version 0.13.0.
**Builds on:** Cycle 12 Phase 5A N=2 active-passive + Fabric mTLS; Cycle 6/7 epoch/fencing.

This document freezes the Phase 5B consistency contract. Code must not diverge without a new council ADR.

---

## 1. Goal

Convert the C12 N=2 replica into a **robust consistent state layer**:

- Explicit version model per object
- Deterministic conflict detection (no silent last-write-wins)
- Formal recovery FSM with evidence
- Idempotency by `operation_id` that survives restart
- N=2 partition fail-closed (no silent minority writes)
- **dual-primary = 0** always

**Out of scope (HARD NO):** Raft/Paxos, N>2, multi-primary, ML/R2/R3, silent plaintext fallback, Vault/ACME required, GIA/AGI claims.

---

## 2. Version model (`CRAMVersion`)

```
CRAMVersion(
  object_id,   # logical object key (content hash or stable id)
  epoch,       # fencing epoch; monotonic; never decreases for an object
  sequence,    # per-object write sequence within epoch
  hash,        # content hash of the versioned payload
  timestamp,   # ISO-8601 UTC
  origin_node  # node that authored this version
)
```

### Rules (fail-closed)

| Condition | Outcome |
|-----------|---------|
| same `object_id` + same `hash` | **IDEMPOTENT** — no state change; return prior version |
| same `object_id` + different `hash` | **CONFLICT** — explicit `ConflictRecord`; no silent LWW |
| incoming `epoch` < current `epoch` | **REJECT** (`REJECTED_STALE_EPOCH`) — 100% |
| incoming `epoch` == current, sequence ≤ current | reject or treat as duplicate per `operation_id` |
| incoming `epoch` > current (after fenced promote) | accept only from fenced writable primary |

Modules: `cram/version.py`, `cram/consistency.py`, `cram/conflict.py`.

---

## 3. Conflict policy

- Conflicts are **recorded** (audit JSONL) with both candidate versions.
- Resolution is **deterministic and explicit** — never silent last-write-wins without an audit record.
- Default policy for Phase 5B: **reject conflicting write** (`CONFLICT_REJECT`) and require operator/recovery path.
- Alternate deterministic resolve (higher epoch wins; if equal, higher sequence; if equal, lexicographically greater hash) is available as `CONFLICT_RESOLVE_DETERMINISTIC` for heal/reconcile after partition — always emits a `ConflictRecord`.

---

## 4. Idempotency

- Dedup key: **`operation_id`** (alias `op_id`).
- Durable map: `consistency/idempotency.jsonl` under the consistency root.
- Replay of the same `operation_id` after process restart returns the **same result** (100% duplicate suppression).
- Survives crash/restart by replaying the JSONL on load.

---

## 5. Recovery FSM

Messages (Phase 5B — extend Fabric `MessageType`):

| Type | Purpose |
|------|---------|
| `RECOVERY_REQUEST` | Detected failure; request recovery for object |
| `RECOVERY_RESPONSE` | Candidate replica location + epoch/hash |
| `RECOVERY_VERIFY` | Hash/epoch verification challenge |
| `RECOVERY_COMMIT` | Fenced promote + checkpoint commit notice |

### Flow

```
DETECT → LOCATE → VERIFY (hash) → PROMOTE (fenced) → CHECKPOINT → RESUME_WRITES
```

States (`RecoveryState`):

1. **DETECT** — primary unavailable / corrupt metadata / mid-append crash
2. **LOCATE** — find verified standby holding the object
3. **VERIFY** — re-hash bytes; compare epoch+hash
4. **PROMOTE** — fence: bump epoch, set sole `writable_primary`, write witness
5. **CHECKPOINT** — durable checkpoint evidence (notice hash)
6. **RESUME** — accept writes only on fenced primary

Invariant: under any failure path, **dual-primary = 0**.

---

## 6. N=2 partition (fail-closed)

- Topology remains exactly **N=2** (PRIMARY + STANDBY).
- Under partition: only the **fenced** writable primary may accept writes.
- Minority / non-fenced side: **read-only or reject** — **no silent minority writes**.
- On heal: reconcile via epoch + hash verify; explicit conflict if hashes diverge.
- `dual-primary` count must remain **0** under partition, promote-under-partition, and kill mid-handshake.

---

## 7. Fault matrix (acceptance)

| Fault | Expected |
|-------|----------|
| Replica crash mid-append | Primary retains authority; standby unfinished apply discarded/retry; dual-primary=0 |
| Primary crash after ACK before checkpoint | Standby holds ACK'd bytes; recovery VERIFY→PROMOTE→CHECKPOINT; resume on new primary |
| Stale epoch write | **100% rejected** (`REJECTED_STALE_EPOCH`) |
| Duplicate `operation_id` replay | **100% idempotent** |
| Network partition | Fail-closed; no silent minority writes; dual-primary=0 |
| Corrupt replica metadata | Failover blocked until repair/verify; promote refused if unverified |
| Dual-primary attempts | Always **0** |

---

## 8. CLI (P3)

```
mesh cram consistency check <object>
mesh cram recovery test
mesh cram history <object>
mesh cram trace <operation_id>   # preserved from C12
```

Exit codes remain frozen (Cycle 5): 0 PASS / 1 generic / 2 corrupt / 3 missing|unavailable.

---

## 9. Observability

Every consistency/recovery op records: `operation_id`, `trace_id`, epoch, sequence, hash, origin_node, result (`APPLIED|DUPLICATE|REJECTED_STALE_EPOCH|CONFLICT|RECOVERED`).

Trace path: Task → Router → Network → C-RAM → Consistency → Checkpoint.

---

## 10. Acceptance (CP-0017)

- pytest ≥ 280; audit PASS; **CP-0017 VERIFIED**; version **0.13.0**
- CP-0001..0016 still VERIFIED
- dual-primary = 0; stale rejects 100%; duplicates idempotent 100%
- Bench: 10k small / 1k medium / 100 large → `experiments/phase5b-consistency-c13/`

---

## 11. Explicit non-claims

Not claimed: Raft, N>2, multi-primary, ML/adaptive routing, R2/R3, GIA/AGI, physical/industrial deploy, Vault/ACME requirement.
