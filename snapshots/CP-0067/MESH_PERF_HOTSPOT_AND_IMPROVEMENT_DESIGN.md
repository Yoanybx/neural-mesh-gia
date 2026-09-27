# Mesh Perf — Hotspot Analysis & Improvement Design

**Status:** DESIGN + hotspot analysis + optional experimental A/B (flag OFF by default)  
**Cycle / Checkpoint:** 63 / CP-0067  
**Date:** 2026-09-26 America/New_York (EDT)  
**Theme:** `perf_hotspot_and_improvement_design`  
**Prior:** CP-0066 `MESH_PERF_RESEARCH_TRACK` (tip `0778d32`, pytest 1023)  
**Version:** package **0.18.0** held  
**Non-claim:** **No** "fastest in the world" · no cross-system ranking ·
`ranking_claim=null` · no GIA · no Raft/N>2 runtime · M1=**NO_CONSENSUS_YET**.

---

## 1. Intent

Convert CP-0066 local microbench baselines into:

1. A **hotspot report** (box-local median/p95 share — not a competitive rank).
2. **Ranked improvement designs** that are experimental and measurable.
3. Optional **A/B microbenches** behind `MESH_PERF_EXPERIMENTAL` (default OFF).

No improvement is claimed as shipped speedup until re-measured under the same
harness. Continuity design remains **queued** (DeepSeek C61-62 Option 2) —
not dropped.

| This CP ships | Explicitly deferred |
|---------------|---------------------|
| Hotspot analysis from CP-0066 benches | Production default behavior changes |
| Ranked I1..I7 improvement designs | Cross-system bakeoff vs etcd/Raft/CRDT |
| Experimental A/B helpers (flag OFF) | Fence store coalesce production patch |
| Measurement plan per candidate | GIA / Raft / N>2 / train / live LLM |
| Neg tests on claim honesty | Continuity design (queued next structural) |

---

## 2. Local hotspot results (box-local)

Harness: `run_all_microbenches` / `analyze_hotspots` in
`src/neural_mesh/packaging/mesh_perf_hotspot.py`.  
Numbers below are **illustrative local samples** from Cycle 63 on this box;
re-run the harness for a fresh baseline. They are **not** portable marketing
metrics.

| Rank (local median) | Bench | Example median | Example share | Dominant cost (profile) |
|---------------------|-------|----------------|---------------|-------------------------|
| 1 | `fence_path` | ~2.6 ms | ~44% | tmpdir + bootstrap + dual/probe JSON IO |
| 2 | `obs_snapshot` | ~2.2 ms | ~37% | `_git_tip7` subprocess (~1.0 ms) + cp list + pyproject |
| 3 | `receipt_hash_chain` | ~0.9 ms | ~15% | route×32 + `content_hash` json+sha256 |
| 4 | `packaging_verify` | ~0.25 ms | ~4% | small synthetic sha256 IO |
| 5 | `membership_sm` | ~0.002 ms | ~0% | in-memory SM (noise floor) |

Sub-profile (same box, research-only):

- `snapshot()` ~2.05 ms vs `snapshot(tip=…)` ~0.93 ms → git tip ≈ half of OBS.
- fence full TemporaryDirectory ~2.56 ms vs dual+probe reuse-root ~1.18 ms.
- receipt verify_only chain32 ~0.30 ms; build+verify ~1.02 ms.

**Interpretation rule:** share_% ranks **this harness's** local costs only.
It does **not** mean Mesh is faster/slower than etcd/Raft/CRDT.

---

## 3. Ranked improvement designs (experimental)

| ID | Target | Status | Hypothesis (local) | Measure |
|----|--------|--------|--------------------|---------|
| **I1** obs tip inject/cache | obs_snapshot | EXPERIMENTAL_MEASURABLE | tip inject ~55% relative OBS cut when git dominates | A/B tip inject vs default |
| **I2** fence harness split | fence_path | EXPERIMENTAL_MEASURABLE | ~half of fence_path is setup artifact | A/B reuse-root vs full |
| **I3** receipt hash memo | receipt_hash_chain | EXPERIMENTAL_MEASURABLE | memo helps verify re-pass; build still dominates | A/B memo verify |
| **I4** OBS cp index cache | obs_snapshot | DESIGN_ONLY | `_list_cp_ids` ~0.37 ms grows with CP count | cold vs warm list |
| **I5** fence read coalesce | fence_path | DESIGN_ONLY | coalesce state/epoch/role reads in one probe | read-count + latency A/B |
| **I6** packaging batch hash | packaging_verify | DESIGN_ONLY | low priority (~0.25 ms) | larger fixture A/B |
| **I7** membership noop | membership_sm | DEFER | already noise floor | canary only |

Full machine-readable payloads: `IMPROVEMENT_DESIGNS` in
`mesh_perf_hotspot.py`.

### Continuity note (queued)

DeepSeek C61-62 flagged `orchestrator_continuity_design` as the next structural
must after the perf loop. Hotspot knowledge relevant to continuity:

- If LEFT/REJOIN paths emit many routing receipts, budget for
  `receipt_hash_chain` (~0.9 ms / 32) in continuity resume designs.
- OBS tip inject (I1) helps status cadence during continuity without touching
  consensus (M1 still NO_CONSENSUS_YET).

---

## 4. Optional experimental flag

```text
MESH_PERF_EXPERIMENTAL=0|1|all|obs_tip_inject,fence_reuse_root,receipt_hash_memo
```

- Default: **OFF** (no A/B benches run; designs still documented).
- `run_experimental_ab(force=True)` for explicit research runs in tests.
- Experimental paths **do not** change production defaults of `snapshot()`,
  `FenceService`, or `verify_receipt_chain`.
- I3 memo lives only in `_verify_receipt_chain_memo` (research wrapper).

---

## 5. Claim policy (fail-closed)

Inherited from CP-0066 + enforced here:

- `LOCAL_BASELINE_ONLY`
- `NO_FASTEST_IN_WORLD`
- `NO_CROSS_SYSTEM_RANKING_WITHOUT_SHARED_HARNESS`
- `NONDEFAULT_LITERATURE_REFS`
- `ranking_claim=null`
- `achieved_speedup_claimed=false` on experimental A/B payloads

Forbidden affirmative phrases remain those checked by `assert_honest_claims`.

---

## 6. Explicit non-goals (held)

- Unlocking Raft / N>2 / multi-primary / GIA / train / live LLM / SaaS / settlement
- No claims that Mesh beats etcd/Raft (forbidden without a shared harness)
- Promoting literature refs from NON_DEFAULT to default
- Opening pkg0190 / minting v0.19.0 tag / mutating v0.18.0 tag
- Collapsing dual-judge advisory into M1 consensus

**NO_HELD:** Raft,N>2,multi-primary,ML,R2,R3,plaintext,Vault-ACME-req,GIA,SLO_chase,tag_schema,EVERY_fsync

---

## 7. Related

- `docs/design/MESH_PERF_RESEARCH_TRACK.md` (CP-0066)
- `docs/design/MESH_PERF_LITERATURE_POINTERS_NONDEFAULT.md`
- `docs/capabilities/MESH_PERF_HOTSPOT_AND_IMPROVEMENT.md`
- `src/neural_mesh/packaging/mesh_perf_hotspot.py`
- `tests/test_mesh_perf_hotspot_cycle63.py`
- Queued: `orchestrator_continuity_design` (DeepSeek Option 2)
