# Schema: mesh.minogan.memory/v0 — AgentMemory (CP-0088 P0.4)

**Status:** IMPL v0 (single box, single writer per agent) · code `src/neural_mesh/minogan/memory.py` · tests `tests/test_minogan_agent_memory_cp0088.py`  
Substrate persistence, **not cognition**. Metadata only.

## 1. Record (one C-RAM `MEMORY` object each, immutable)

| Field | Notes |
|-------|-------|
| `schema` | `mesh.minogan.memory/v0` |
| `tenant_id`, `agent_id` | = ScorerInput `org_id`, `agent.id`; checked on **every** read |
| `seq` | 1, 2, 3 … per (tenant, agent), contiguous |
| `prev_hash` | previous record `hash` (genesis = 64×`0`) |
| `hash` | sha256 of canonical JSON of the record without `hash` |
| `ts` | epoch ms (= ScorerInput `now`); non-decreasing per agent (`MemoryOrderError` otherwise) |
| `kind=score` payload | `input_digest`, `model_version`, `score`, `exposure`, `behavior`, `driftPct`, `driftStatus`, `window`, `features` (13 counters), `signals[{id,type,rule,severity,ts,pattern,trace_ids≤10}]` |

Never stored: prompts, completions, tool arguments/results, signal titles. Any content key (contract `CONTENT_KEYS`) at any depth → `MemoryContentError`.

## 2. Time-bucketed index

```
<root>/.cram/…                                        CAS objects (C-RAM CRAMStore.put_object, type MEMORY)
<root>/minogan_memory/<T>/<A>/head.json               {seq, hash, ts, first_day, last_day, pending}
<root>/minogan_memory/<T>/<A>/days/YYYY-MM-DD.jsonl   {seq, ts, key, hash, prev_hash} per line (UTC day of ts)
T = sha256("minogan.memory/v0\0"+tenant_id)[:32]      A = sha256(tenant_id+"\0"+agent_id)[:32]
```

- `history(since, until)` opens only the day files between `max(day(since), first_day)` and `min(day(until), last_day)`:
  a 90-day query costs ≤ 91 bucket reads + 1 CAS read per matching record, independent of total history length
  (test: 301 days stored → 91 bucket / 91 record reads; `CRAMStore.list_keys` / `fsck` patched to fail).
- `baseline(since, until)` → `{n, mean_score, min_score, max_score, from, to}`.
- `recurrence(rule, days, now)` → distinct UTC days / occurrences of `rule` by **signal** ts in `(now−days, now]`, dedup by signal id.
- `verify_chain()` is the audit path (reads all of one agent's buckets): seq contiguity, prev_hash links, record re-hash,
  CAS byte hash, day placement, head == tail.

## 3. Append protocol and crash recovery

1. CAS put of the record (temp + fsync + rename + dir fsync) — crash ⇒ orphan object, invisible.
2. `head.pending = {seq, day, key, hash}` (atomic replace, `SyncMode.EVERY`) — from here the record is durable.
3. Bucket append + fsync (+ dir fsync when the day file is new).
4. Head commit (`pending` cleared).

On open (under `flock`): torn bucket tail truncated; a `pending` record is re-verified (CAS hash, record hash,
`prev_hash == head.hash`, `seq == head.seq+1`) and rolled forward; anything else ⇒ `MemoryCorrupt` (refuse, never guess).
Tests: real `SIGKILL` of a writer subprocess mid-stream, plus a kill at each of steps 1–3 (env hook
`MESH_MINOGAN_MEMORY_CRASH_AT`, test-only); a 25-kill stress run on one store stayed valid.

## 4. Isolation

Paths are derived from hashes (hostile ids like `../../x` cannot escape `minogan_memory/`), and every record read checks
`tenant_id`/`agent_id` — a forged index line pointing at another tenant's record raises `MemoryTenantError`.
The CAS directory is shared per root; hard multi-tenancy (separate roots/keys per tenant, deletion) is P1.

## 5. Scorer use (`score(input, memory=…)`)

Without memory: output unchanged byte-for-byte (parity path). With memory (read-only, records `ts ≤ now`):
- `components.drift_long`: scores in `[now−90d, window.from)` → `{n, baseline_mean, drift_pct, status, memory_from}`. Does **not** change `driftPct`.
- `components.recurrence[]`: per rule in the current signals, 30-day `occurrences`, `distinct_days`, `high_distinct_days` (current signals included, dedup by id).
- `decline` (uw_v0 §3 rule 4): `score ≥ 85` ∧ `confidence ≥ 0.6` ∧ a current high `data exfil pattern` / `prompt injection attempt`
  rule with `high_distinct_days ≥ 2` in 30 days ⇒ `components.uw.outcome = decline` + `components.decline_basis`. The number never changes.
- Re-scoring after appending the input's own record yields identical bytes.

## 6. Not in v0

Multi-writer concurrency across hosts; N=2 replication of memory (C-RAM replica not used here; no Raft, no N>2); retention /
verifiable deletion; compaction of day files; per-tenant encryption; `fcntl` ⇒ POSIX only.
