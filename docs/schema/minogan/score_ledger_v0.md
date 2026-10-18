# Score ledger v0 — `mesh.minogan.ledger/v0` (CP-0088 P0.6)

Per-tenant hash chain recording **every** scoring, so any past score can be re-derived byte-for-byte and any
alteration — of the ledger or of the agent memory it relied on — is detected.

Code: `src/neural_mesh/minogan/ledger.py` · CLI: `mesh minogan replay <id> --root R`,
`mesh minogan verify --root R [--tenant T] [--replay]` · Tests: `tests/test_minogan_score_ledger_cp0088.py`.

## Layout (same root and C-RAM CAS as AgentMemory)

```
<root>/.cram/…                                  EVIDENCE objects: entry, canonical input, canonical output
<root>/minogan_ledger/<T>/head.json             {tenant_id, seq, hash, pending?}
<root>/minogan_ledger/<T>/seq/NNNNNNNN.jsonl    index, 1000 entries per chunk → O(1) lookup by seq
<root>/minogan_ledger/<T>/.lock                 flock (append / recovery)
```

`T = sha256("minogan.ledger/v0\0" + tenant_id)[:32]`. Entry id: **`msl_<T[:16]>_<seq>`** (no raw tenant id).
Index line: `{seq, id, key, hash, prev_hash, agent_id, mem_to}` (`mem_to` = memory seq covered after the entry).

## Entry (`kind: "score"`)

| field | meaning |
|-------|---------|
| `schema`, `id`, `seq` | `mesh.minogan.ledger/v0`, id, 1-based position in the tenant chain |
| `tenant_id`, `agent_id`, `ts` | tenant (= token tenant = `org_id`), agent, input `now` |
| `contract` | `minogan.scorer/v1` |
| `input_key`, `input_digest` | C-RAM key of `canonical_json(ScorerInput.canonical_dict())`; `sha256:` digest (= output `components.input_digest`). Metadata-only by construction: the contract refuses content keys (prompts/completions/tool args/results) |
| `memory` | `null` (scored without memory) or `{before:{seq,hash,ts}, used:{n,first_seq,last_seq,digest}, appended:{seq,hash,ts}}` |
| `model_version`, `methodology` | scorer version that produced the output |
| `output_key`, `output_digest` | C-RAM key and `sha256:` of the canonical ScorerOutput bytes |
| `score`, `uw_outcome` | convenience copies (covered by the hash) |
| `prev_hash`, `hash` | chain link; `hash = sha256(canonical_json(entry − hash))`; genesis `0×64` |

`memory.before` is the agent's memory head **before** this scoring (snapshot reference); `used` digests the
`[seq, hash]` list of the records the scorer actually read (`MemoryView`); `appended` is the memory record this
scoring wrote (its `input_digest` must equal the entry's).

### `kind: "memory_unledgered"`

`memory: {from_seq, to_seq, to_hash, to_ts}` + `reason`. Written automatically before an agent's next scoring
when its memory holds records no entry covers (a crash between memory and ledger commit, or pre-ledger history).
Not replayable; `verify` lists it as a warning so the hole stays visible.

## Scoring order (service and `MeshScorer(memory, ledger)` / `record_scoring`)

Under the per-(tenant, agent) lock: `head = memory.head` → reconcile (above) → `view = memory.view(max_seq =
head.seq)` → `score(inp, memory=view)` → deadline check (nothing persisted after it) → `memory.append_score` →
`ledger.append_scoring`. Live scoring and replay both read memory through `MemoryView`, so they run the same code.

## Append protocol / crash safety (same as AgentMemory)

1. C-RAM put of input, output, entry (fsync) — crash after: orphan CAS objects, invisible
2. `head.pending = {seq, key, hash}` (atomic replace + fsync) — entry durable
3. index line append (fsync)
4. head commit

Recovery on open (under flock): torn index tail truncated; a pending entry is verified (CAS bytes, entry hash,
`prev_hash == head.hash`, `seq == head.seq + 1`) and rolled forward. kill -9 tests cover every step of both
protocols and a mid-stream SIGKILL. The only cross-structure window (memory committed, ledger not) makes
`verify` fail — it is indistinguishable from a deleted ledger tail — until the next scoring of that agent records
it as `memory_unledgered`.

## Replay (`mesh minogan replay <id>`)

Load entry (CAS + hash) → refuse if `model_version` ≠ running scorer (`model_version_mismatch`) → load input
(CAS + `input_digest`, tenant/agent/ts match) → check memory refs (`before` record hash, `appended` record hash +
input_digest) → `score(inp, memory = memory.view(max_seq = before.seq))` → output bytes must equal the stored
output object and `output_digest`, and `view.used_ref()` must equal `memory.used`. Exit 0 iff all hold.

## Verify (`mesh minogan verify`)

For every tenant in the ledger **or** in AgentMemory: index/entry seq, `prev_hash` links, entry hash, index line
== derived line, id format, input/output CAS bytes + digests, output cites the input digest, memory refs,
per-agent coverage continuity (`before.seq` == previous coverage, unledgered ranges contiguous), head == tail,
`AgentMemory.verify_chain` for each agent, and memory head == coverage (memory records without entries fail).
`--replay` additionally replays every scoring entry. Exit 0 iff no errors.

Detected (tests): flipped bytes in entry / input / output objects; internally consistent re-hashed entries
(score, uw_outcome, output_digest, memory, agent_id); altered index line or head; deleted ledger tail; flipped
memory record bytes; a **consistently rewritten memory chain** (memory's own verify passes; ledger refs fail).

## Limits (v0)

- No external anchoring of the ledger head: an attacker rewriting ledger **and** memory **and** CAS consistently
  from genesis is not detectable locally (P1: anchor head hashes externally / sign).
- One writer process per root (thread-safe within a process; flock keeps chains valid across processes, but the
  per-tenant coverage cache is per process).
- Replay needs the same `model_version`; older entries need the matching scorer build.
- Stored inputs dedupe in CAS but are retained indefinitely (no retention policy yet).
