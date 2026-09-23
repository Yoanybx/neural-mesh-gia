# Council STATUS — Cycle 17 / CP-0021

**Mode:** DeepSeek-only M2M (`PASTE_CYCLE17_M2M.md`).
**Date:** 2026-09-23 America/New_York (EDT).

| Gate | Result |
|------|--------|
| pytest | **369 passed** (≥359) |
| pytest_min tags | **10 passed** (`-k checkpoint_every_floor`) |
| CP-0021 | **VERIFIED** (tag invariant + SCHEMA-GATED debt) |
| CP-0001..0020 | **VERIFIED** |
| version | **0.14.3** |
| schema | `CHECKPOINT@floor:<n>` documented |
| validator | one checkpoint tag per floor |
| debt CHECKPOINT_EVERY_FLOOR | **SCHEMA-GATED** (SLO GAP held) |
| BATCH durable / recovery | **MET** (held; no chase) |
| dual-primary | **0** |
| minority writes | **0** |
| stale reject | **100%** |
| duplicate idempotent | **100%** |
| audit | **PASS** |

**Clarification:** N=2 “majority” = fenced primary / heal path only — **NOT Raft**.

**Artifacts:** `src/neural_mesh/tags.py`, `docs/debt/CHECKPOINT_EVERY_FLOOR.md`, `tests/test_tags.py`, `STATUS_FOR_CHATGPT_CYCLE17.md`, `snapshots/CP-0021/`.

**Hard NO held:** Raft/Paxos, N>2, multi-primary, ML/R2/R3, silent plaintext, Vault/ACME required, GIA/AGI claims, SLO chase, refactor outside tags.
