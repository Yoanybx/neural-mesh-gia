# Council STATUS — Cycle 14 / CP-0018

**Mode:** DeepSeek-only (ChatGPT catch-up via STATUS_FOR_CHATGPT_CYCLE14.md).
**Date:** 2026-09-23 America/New_York (EDT).

| Gate | Result |
|------|--------|
| pytest | **328 passed** (≥320) |
| CP-0018 | **VERIFIED** |
| CP-0001..0017 | **VERIFIED** |
| version | **0.14.0** |
| dual-primary | **0** |
| minority writes | **0** |
| stale reject | **100%** |
| duplicate idempotent | **100%** |
| partition suite | PASS (first gate) |
| audit | PASS (project state + pytest + checkpoint latest) |

**Phase 5C delivered:** WAL/fsync policy, crash invariants, N=2 adversarial partition suite, safe compaction, CLI, bench.

**Bounds:** recovery/checkpoint(durable)/conflict(full) show honest **gaps** vs stretch SLOs; C13-parity checkpoint + classify-only conflict **MET**.

**Clarification:** N=2 “majority” = fenced primary / heal path only — **NOT Raft**.

**Artifacts:** `docs/phase5c_durability.md`, `STATUS_FOR_CHATGPT_CYCLE14.md`, `council/STATUS_DEEPSEEK_CYCLE14.md`, `experiments/phase5c-durability-c14/baseline.json`, `snapshots/CP-0018/`.

**Hard NO held:** Raft/Paxos, N>2, multi-primary, ML/R2/R3, silent plaintext, Vault/ACME required, GIA/AGI claims.
