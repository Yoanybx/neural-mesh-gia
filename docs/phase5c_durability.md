# Phase 5C — Durability & Adversarial Partition Hardening (FROZEN Cycle 14 / P0)

**Status:** FROZEN merge gate (council `COUNCIL_AGREEMENT_CYCLE14.md`).
**Date:** 2026-09-23 America/New_York (EDT).
**Checkpoint target:** CP-0018 / version 0.14.0.
**Builds on:** Cycle 13 Phase 5B consistency (CP-0017); Cycle 12 Phase 5A N=2 Fabric replica.

This document freezes the Phase 5C durability + adversarial partition contract.
Code must not diverge without a new council ADR.

---

## 1. Goal

Harden **post-crash durability** and **N=2 network partition** behaviour:

- Explicit **WAL + fsync** policy for consistency metadata and CAS objects
- Formal **crash-recovery invariants** (kill -9 mid-write / mid-append / mid-checkpoint)
- **Partition suite** as first gate (DeepSeek C13 non-blocking note): minority accepts **0** writes
- Safe **snapshot compaction** (no corruption; no loss of verified objects)
- CLI: `mesh cram durability check | partition test | recovery trace`
- Bench: crash + partition + reconnect (+ 10k/1k/100 if cheap)

**Out of scope (HARD NO):** Raft/Paxos, N>2, multi-primary, ML/R2/R3, silent plaintext
fallback, Vault/ACME required, GIA/AGI claims, physical/industrial deploy.

---

## 2. Clarification — “majority” is NOT Raft

For **N=2 single-primary**, the word **majority** in DeepSeek notes means **only**:

1. The **fenced writable primary** side under partition (the side holding the fence/witness), **or**
2. The **heal path** after partition ends (deterministic reconcile via epoch + hash + fenced promote).

It does **NOT** mean:

- Raft / Paxos / quorum consensus
- Vote counting across N>2 nodes
- Multi-primary acceptance
- Automatic aggressive failover without fencing

Invariant remains: **dual-primary = 0** always.

---

## 3. WAL / fsync policy

### 3.1 Layers

| Layer | Path | Durability |
|-------|------|------------|
| CAS objects | `.cram/<aa>/<rest>` | temp → write → **fsync** → `os.replace` → best-effort dir fsync (`CRAMStore._atomic_write`) |
| Consistency heads | `consistency/versions/heads.json` | same atomic fsync replace |
| Version history WAL | `consistency/versions/history.jsonl` | append → flush → **fsync** |
| Conflict audit WAL | `consistency/versions/conflicts.jsonl` | append → flush → **fsync** |
| Idempotency WAL | `consistency/idempotency.jsonl` | append → flush → **fsync** |
| Durability WAL | `consistency/durability/wal.jsonl` | append → flush → **fsync** before heads commit |
| Checkpoint evidence | recovery / compact notices | atomic fsync JSON |

### 3.2 Ordering (write path)

```
1. APPEND WAL record (BEGIN / APPLY) + fsync
2. Persist payload (CAS atomic write) if applicable
3. Update heads.json (atomic fsync replace)
4. APPEND WAL record (COMMIT) + fsync
```

Crash between (1) and (4): recovery replays WAL; incomplete COMMIT → discard or retry; never dual-apply.

### 3.3 Honesty

fsync durability is **best-effort** as far as the underlying filesystem honors it on this box.
We do not claim battery-backed NVRAM or power-fail lab certification.

---

## 4. Crash-recovery invariants

Simulated / enforced for:

| Fault | Invariant |
|-------|-----------|
| kill -9 **mid-write** (CAS tmp present, final missing) | No partial object visible; `verify` fails or object absent; retry safe |
| kill -9 **mid-append** (WAL line truncated / no COMMIT) | Replay ignores incomplete record; heads unchanged for that op |
| kill -9 **mid-checkpoint** (checkpoint tmp / incomplete notice) | Prior verified checkpoint remains; no corrupt CP accepted |
| Process restart after COMMIT | Idempotent: same `operation_id` → DUPLICATE; heads match WAL |

Formal checks: `DurabilityChecker` / `mesh cram durability check`.

---

## 5. N=2 partition suite (fail-closed) — FIRST GATE

Topology exactly **PRIMARY + STANDBY** (N=2). Single-primary. No Raft.

| Case | Expected |
|------|----------|
| Isolated **minority** (non-fenced) | Accepts **0** writes (`REJECTED_PARTITION`) |
| Stale-epoch write under partition | **100%** `REJECTED_STALE_EPOCH` |
| Dual-primary attempt | Count stays **0**; promote refuses split-brain |
| Heal | Deterministic reconcile: compare epoch + hash; fenced promote; explicit conflict if hashes diverge (audited) |

“Majority recovers” ≡ fenced primary keeps authority **or** heal promotes with fence — **not** quorum math.

---

## 6. Snapshot compaction (safe)

- Compact **only** after VERIFY of all retained object hashes
- Never delete the sole verified copy of an object
- Compaction is transactional: write new snapshot → fsync → flip pointer → then GC orphans
- Abort leaves prior snapshot intact (mid-compact crash invariant)

Module: `cram/compaction.py`.

---

## 7. CLI (Phase 5C)

| Command | Purpose |
|---------|---------|
| `mesh cram durability check` | WAL/fsync + crash-invariant report |
| `mesh cram partition test` | Run N=2 adversarial partition suite |
| `mesh cram recovery trace` | Trace DETECT→…→RESUME evidence / WAL |

Exit codes: Cycle 5 contract preserved (0 PASS / 1 generic / 2 corrupt / 3 missing).

---

## 8. SLO targets (honest; same method as C13 where possible)

| Metric | Bound |
|--------|-------|
| Recovery p99 | ≤ 2 ms (stretch) |
| Checkpoint p99 | ≤ 0.1 ms |
| Conflict detect p99 | ≤ 0.1 ms |
| Dup suppress | 100% |
| Stale reject | 100% |
| Dual-primary | 0 |
| Minority writes accepted | 0 |

Report MET or gap honestly in bench + STATUS.

---

## 9. Acceptance

- pytest ≥ 320
- audit PASS
- **CP-0018 VERIFIED**
- CP-0001..0017 still VERIFIED
- version **0.14.0**
- Hard NO list held

---

## 10. Modules

- `cram/durability.py` — WAL, fsync helpers, crash invariants, DurabilityChecker
- `cram/partition_suite.py` — N=2 adversarial partition + heal reconcile
- `cram/compaction.py` — safe snapshot compaction
- `cram/durability_cli.py` — CLI handlers
