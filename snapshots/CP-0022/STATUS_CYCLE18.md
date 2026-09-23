# Council STATUS — Cycle 18 / CP-0022

**Mode:** DeepSeek-only M2M (`PASTE_CYCLE18_M2M.md`).
**Date:** 2026-09-23 America/New_York (EDT).

| Gate | Result |
|------|--------|
| pytest | **372 passed** (≥369) |
| pytest_min tags | **13 passed** (`-k checkpoint_every_floor`, ≥10) |
| CP-0022 | **VERIFIED** (schema gate + SCHEMA-GATED debt) |
| CP-0001..0021 | **VERIFIED** |
| version | **0.14.4** |
| schema | `CHECKPOINT@floor:<n>` confirmed |
| schema gate | `schema_gate_checkpoint_every_floor` → SCHEMA-GATED |
| one-per-floor | enforced |
| debt CHECKPOINT_EVERY_FLOOR | **SCHEMA-GATED** (SLO GAP ~1.32ms held; no chase) |
| BATCH durable / recovery | **MET** (held; no chase) |
| dual-primary | **0** |
| minority writes | **0** |
| stale reject | **100%** |
| duplicate idempotent | **100%** |
| audit | **PASS** |

**Clarification:** N=2 “majority” = fenced primary / heal path only — **NOT Raft**.

**Artifacts:** `src/neural_mesh/tags.py`, `docs/debt/CHECKPOINT_EVERY_FLOOR.md`, `tests/test_tags.py`, `STATUS_FOR_CHATGPT_CYCLE18.md`, `snapshots/CP-0022/`.

**Hard NO held:** Raft/Paxos, N>2, multi-primary, ML/R2/R3, silent plaintext, Vault/ACME required, GIA/AGI claims, SLO chase, refactor outside tags.
