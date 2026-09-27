# Mesh Performance Research Track

**Status:** RESEARCH PROGRAM + local microbench harness (honest baselines only)  
**Cycle / Checkpoint:** 62 / CP-0066  
**Date:** 2026-09-26 America/New_York (EDT)  
**Theme:** `MESH_PERF_RESEARCH_TRACK`  
**Authority:** Continuous-loop authorization after CP-0065 (multi_judge spike)  
**Version:** package **0.18.0** held  
**Non-claim:** **No** "fastest in the world" · no cross-system ranking without a shared
harness · no GIA · no Raft/N>2 runtime unlock · M1 = **NO_CONSENSUS_YET**.

---

## 1. Intent

Stand up a **competitive systems research plan** for Mesh packaging/ops paths with
**experimental microbenches** that produce **local, reproducible baselines**.

This track exists to measure Mesh honestly — not to market slogans. Any future
comparison to other systems requires a **shared harness**, identical workload
definitions, and published methodology. Until then, ranks and superlatives are
**forbidden**.

| This CP ships | Explicitly deferred |
|---------------|---------------------|
| Research program design (what / why / how) | Cross-system bakeoff vs etcd/Raft/CRDT |
| timeit / perf_counter microbench harness | pytest-benchmark plugin dependency (optional later) |
| Five named local benches | Live WAN / multi-host benches |
| Literature pointer note (NON-default refs) | GIA / Raft / N>2 unlock |
| Neg tests on claim honesty | Settlement / SaaS / train |

---

## 2. What to measure

| Target | Path | Why |
|--------|------|-----|
| **fence_path** | H3 `FenceService` bootstrap → force dual → `probe(auto_fence=True)` | Safety-critical ABORT→demote+re-elect latency (local) |
| **obs_snapshot** | `status_snapshot.snapshot()` | OPS observability tax on project_state reads |
| **membership_sm** | M2 `MembershipSM` JOIN→…→REJOIN churn | In-memory membership gate cost |
| **receipt_hash_chain** | Orchestrator routing receipts + `verify_receipt_chain` | Evidence integrity cost under chain growth |
| **packaging_verify** | Synthetic manifest sha256 verify | Packaging integrity micro-cost (local) |

Implementation: `src/neural_mesh/packaging/mesh_perf_research.py`  
Tests: `tests/test_mesh_perf_research_cycle62.py`

---

## 3. Claim policy (fail-closed)

Emitted reports always set `ranking_claim=null` and carry:

- `LOCAL_BASELINE_ONLY`
- `NO_FASTEST_IN_WORLD`
- `NO_CROSS_SYSTEM_RANKING_WITHOUT_SHARED_HARNESS`
- `NONDEFAULT_LITERATURE_REFS`

Forbidden phrases (tests assert absence): "fastest in the world", "beat etcd",
"beat raft", "faster than all", etc.

Median / p95 numbers from this harness are **box-local** and **not** portable
marketing metrics.

---

## 4. Literature / pointer note (NON-default)

See `docs/design/MESH_PERF_LITERATURE_POINTERS_NONDEFAULT.md`.

| System | Role vs Mesh |
|--------|----------------|
| **etcd** | NON_DEFAULT_REFERENCE — KV/Raft latency literature |
| **Raft** | NON_DEFAULT_REFERENCE — consensus family; **NO_HELD** for Mesh runtime |
| **CRDT** | NON_DEFAULT_REFERENCE — orthogonal research pointer |

**M1 remains NO_CONSENSUS_YET.** Dual-judge advisory (CP-0064/0065) is **not** a
consensus protocol and does **not** adopt Raft/etcd/CRDT as defaults.

---

## 5. Harness notes

- Default runner: `time.perf_counter` loops with small iteration counts (CI-safe).
- Optional future: `pytest-benchmark` — **not** required this CP (avoid new dep).
- `run_all_microbenches()` returns a `BenchReport` with per-target median/p95 ms.
- N_CAP=2 held; `dual_primary=0`; `live_api=False` on all samples.

---

## 6. Explicit non-goals (held)

- Unlocking Raft / N>2 / multi-primary  
- GIA / train-70B / live LLM / SaaS / settlement  
- Claiming Mesh is fastest / beating etcd without shared harness  
- Collapsing advisory dual-judge into M1 consensus  

**NO_HELD:** Raft,N>2,multi-primary,ML,R2,R3,plaintext,Vault-ACME-req,GIA,SLO_chase,tag_schema,EVERY_fsync

---

## 7. Related

- `docs/design/MESH_PERF_LITERATURE_POINTERS_NONDEFAULT.md`
- `docs/capabilities/MESH_PERF_RESEARCH_TRACK.md`
- `docs/design/ORCHESTRATOR_JUDGE_ROUTING_DESIGN.md` (receipt chain)
- `docs/capabilities/MESH_DUAL_PRIMARY_FENCE.md` (fence path)
