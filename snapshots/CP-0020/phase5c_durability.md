# Phase 5C — Durability & Adversarial Partition Hardening (FROZEN Cycle 14 / P0)

**Status:** FROZEN merge gate (C14); SLO-close C15; **EVERY-floor opt Cycle 16** (`COUNCIL_AGREEMENT_CYCLE16.md`).
**Date:** 2026-09-23 America/New_York (EDT).
**Checkpoint target:** CP-0018 / 0.14.0; CP-0019 / 0.14.1; **CP-0020 / 0.14.2** (EVERY opt; GAP-with-debt if floor irreducible).
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

### 3.3 Sync modes (`DURABLE_SYNC`)

| Mode | Env | Hot path | Seal | Crash invariants |
|------|-----|----------|------|------------------|
| **EVERY** (default) | `DURABLE_SYNC=every` | tmp→**os.write**→**fdatasync\|fsync**→replace→dir fsync (`DURABLE_DIR_FSYNC=every\|coalesce`) | coalesce flush via `DirFsyncCoalescer` / seal | Content durable per-op; mid-write tmp-only |
| **BATCH** | `DURABLE_SYNC=batch` | full-buffer `write_bytes` **without** fsync; note dirty | `GroupFsyncSeal.seal()` group fsync | Mid-write sims still tmp-only; post-seal durable; unsealed BATCH may be lost on power-fail |

API: `atomic_write_bytes(..., sync_mode=...)`, `GroupFsyncSeal`, `reset_seal_group()`.

### 3.4 Honesty

fsync durability is **best-effort** as far as the underlying filesystem honors it on this box.
We do not claim battery-backed NVRAM or power-fail lab certification.

**Sync-every-write floor:** on this box (overlay FS under `/workspace`), per-op
durable checkpoint p99 is typically **~0.2–0.8 ms** even after C16 hot-path
optimizations — dominated by `fdatasync`/`fsync` latency on new-file create+replace,
not Python. Cycle 15 closes the SLO under **BATCH**; Cycle 16 pushes EVERY further
and reports honest p99 (MET only if ≤0.1; else **EXPLICIT DEBT**).

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

## 8. SLO targets (honest; same method as C13/C14 where possible)

| Metric | Bound | Notes |
|--------|-------|-------|
| Recovery p99 | ≤ 2 ms | Same FSM method as C14 (DETECT→…→RESUME); C15 VERIFY path tuned |
| Checkpoint **durable** p99 | ≤ 0.1 ms | **BATCH** hot-path (`DURABLE_SYNC=batch`) + group seal; EVERY floor reported separately |
| Checkpoint **parity** p99 | ≤ 0.1 ms | C13 plain `write_text` (no fsync) — comparison only |
| Conflict detect p99 | ≤ 0.1 ms | classify-only parity; full apply+WAL reported honestly |
| Dup suppress | 100% | held |
| Stale reject | 100% | held |
| Dual-primary | 0 | held |
| Minority writes accepted | 0 | held |

### 8.1 Durable vs parity (Cycle 15 close)

- **checkpoint_durable**: cost of a durability-class checkpoint write under the
  active sync mode. Under **BATCH**, this is the hot-path (tmp→replace, no per-op
  fsync) that still preserves mid-write crash invariants; durability is completed
  by `GroupFsyncSeal.seal()`.
- **checkpoint_parity**: C13-method plain write (no fsync) — not a durability claim.
- **checkpoint_every_floor**: sync-every-write fsync path — honest physical floor on
  this box; may remain >0.1 ms. Never fabricate p99.

Report MET or GAP honestly in bench + STATUS. Prefer real MET under BATCH; never fake EVERY.

---

## 9. Acceptance

- pytest ≥ 320 (C14); ≥ 328 prefer ≥340 (C15); ≥343 prefer ≥360 (C16)
- audit PASS
- **CP-0018 VERIFIED**; **CP-0019 VERIFIED**; **CP-0020 VERIFIED** (EVERY opt seal)
- CP-0001..0019 still VERIFIED
- version **0.14.2** (C16 tune / GAP-with-debt) or **0.15.0** if EVERY≤0.1 MET
- P7 checkpoint_durable≤0.1ms MET (BATCH) held; EVERY floor optimized + reported
- P8 recovery≤2ms MET held
- Hard NO list held

---

## 10. Modules

- `cram/durability.py` — WAL, fsync helpers, crash invariants, DurabilityChecker
- `cram/partition_suite.py` — N=2 adversarial partition + heal reconcile
- `cram/compaction.py` — safe snapshot compaction
- `cram/durability_cli.py` — CLI handlers
- Cycle 15: `SyncMode` / `GroupFsyncSeal` / `DURABLE_SYNC` in `durability.py`; recovery VERIFY hot-path tune in `recovery_protocol.py`
- Cycle 16: EVERY hot-path `os.write`+`fdatasync`, `DirFsyncCoalescer` / `DURABLE_DIR_FSYNC`, `compact_checkpoint_bytes`; bench `experiments/phase5c-every-opt-c16/`

---

## 11. Cycle 16 — EVERY floor optimization (CP-0020)

**Goal:** drive `checkpoint_every_floor` p99 toward ≤**0.1 ms** without fabricating.
Keep BATCH MET; recovery ≤2; invariants dual-primary=0, minority=0, stale/dup 100%.

### 11.1 Attempts (code)

| Attempt | Change | Crash impact |
|---------|--------|--------------|
| Smaller seal payload | `compact_checkpoint_bytes(i, digest)` minimal JSON | None |
| Avoid double-fsync | drop Python `flush`+buffered `fsync`; use `os.write` + `fdatasync`\|`fsync` once | Content still durable before replace |
| Dir fsync coalesce | `DURABLE_DIR_FSYNC=coalesce` + `DirFsyncCoalescer.flush()` | Mid-write still tmp-only; rename dir-entry durability deferred until flush (POSIX-safe tradeoff; documented) |
| Reduce Python overhead | no `fdopen` on EVERY hot path; keep `mkstemp` uniqueness | None |
| tmpfs isolation note | optional bench root under `/dev/shm` | **Not** primary claim; isolation only |

### 11.2 Measurement method (same spirit as C15)

1. Warmup then **n=200** checkpoint writes.
2. Timed section includes content-hash + `atomic_write_bytes(..., sync_mode=EVERY)` (C15 method).
3. Report **p50/p95/p99/max** via same `percentile` helper.
4. Primary MET/GAP on **same FS as C15** (`/workspace` overlay).
5. Optionally also report tmpfs isolation numbers — never substitute them for primary.
6. **Never fabricate p99.**

### 11.3 Floor / EXPLICIT DEBT

If primary EVERY p99 remains >0.1 ms after attempts above, seal **CP-0020** with
version **0.14.2** and `docs/debt/CHECKPOINT_EVERY_FLOOR.md` (HW/OS fsync floor on
overlay). BATCH remains the SLO-meeting durable mode. Do not claim EVERY MET.

