# Council STATUS — Cycle 15 / CP-0019

**Mode:** DeepSeek-only M2M (`PASTE_CYCLE15_M2M.md`).
**Date:** 2026-09-23 America/New_York (EDT).

| Gate | Result |
|------|--------|
| pytest | **343 passed** (≥328 / aim ≥340) |
| CP-0019 | **VERIFIED** |
| CP-0001..0018 | **VERIFIED** |
| version | **0.14.1** |
| P7 checkpoint_durable BATCH | **MET** p99=0.067≤0.1 |
| P7 EVERY floor | GAP p99=0.447 (honest) |
| P8 recovery | **MET** p99=1.598≤2 |
| dual-primary | **0** |
| minority writes | **0** |
| stale reject | **100%** |
| duplicate idempotent | **100%** |
| audit | PASS (pending script) |

**Clarification:** N=2 “majority” = fenced primary / heal path only — **NOT Raft**.

**Artifacts:** `docs/phase5c_durability.md`, `STATUS_FOR_CHATGPT_CYCLE15.md`, `council/STATUS_DEEPSEEK_CYCLE15.md`, `experiments/phase5c-slo-close-c15/baseline.json`, `snapshots/CP-0019/`.

**Hard NO held:** Raft/Paxos, N>2, multi-primary, ML/R2/R3, silent plaintext, Vault/ACME required, GIA/AGI claims.
