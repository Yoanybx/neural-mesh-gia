# EXPLICIT DEBT — checkpoint_every_floor (CP-0020 / Cycle 16 → CP-0021 schema)

**Date:** 2026-09-23 America/New_York (EDT)
**Status:** SCHEMA-GATED (CP-0021) — tag invariant enforced; SLO GAP remains honest (no chase)
**Owner:** durability / Phase 5C / tags
**Checkpoint:** CP-0021 / version 0.14.3 (schema); CP-0020 / 0.14.2 (EVERY opt GAP)

## Tag schema (CP-0021)

Canonical floor checkpoint tag::

    CHECKPOINT@floor:<n>

- `<n>` — non-negative integer floor id
- Floor **0** — primary EVERY overlay floor (this box `/workspace`)
- Additional floors may be declared for isolation notes (e.g. tmpfs) but are
  never substituted for the primary claim

**Invariant:** for each declared floor `n`, exactly **one** tag
`CHECKPOINT@floor:<n>` must be present (no missing, no duplicates).

**Validator:** `neural_mesh.tags.validate_one_checkpoint_tag_per_floor`
**Helpers:** `make_floor_checkpoint_tag`, `parse_floor_checkpoint_tag`,
`is_floor_checkpoint_tag`
**Tests:** `pytest -q tests/test_tags.py -k checkpoint_every_floor`

Example floor fixture tags::

    CHECKPOINT@floor:0
    CHECKPOINT@floor:1

## Claim (SLO — still GAP)

`checkpoint_every_floor` p99 ≤ **0.1 ms** under true EVERY-mode durable
checkpoint (content fdatasync/fsync per op + dir fsync policy) is **not MET**
on this box's primary bench filesystem (`/workspace` overlay).

Cycle 17 does **not** chase this SLO. Debt tracking is **SCHEMA-GATED**: the
tag invariant above is enforced; the performance GAP remains documented.

## Measured (Cycle 16 primary run)

Source: `experiments/phase5c-every-opt-c16/baseline.json` (same method as C15; n=200).

| Variant | p99 ms | vs 0.1 | Notes |
|---------|--------|--------|-------|
| EVERY full (primary) | **1.325** | GAP | os.write+fdatasync+dir fsync on `/workspace` overlay |
| EVERY + dir coalesce | 0.272 | GAP | content durable per-op; dir flush amortized |
| EVERY + compact payload | 0.435 | GAP | smaller seal bytes |
| EVERY on tmpfs isolation | 0.051 | MET* | *isolation note only — not primary claim |
| BATCH hot-path (held) | 0.072 | MET | P7 still MET |
| recovery (held) | 1.464 | MET ≤2 | P8 still MET |

## Evidence (Cycle 16)

Attempts (see `docs/phase5c_durability.md` §11):

1. Smaller seal payload — `compact_checkpoint_bytes`
2. Avoid double-fsync — `os.write` + single `fdatasync|fsync` (no Python buffered flush+fsync)
3. Dir fsync coalesce — `DURABLE_DIR_FSYNC=coalesce` + `DirFsyncCoalescer.flush()`
4. Reduce Python overhead — no `fdopen` on EVERY hot path
5. tmpfs isolation note — `/dev/shm` can show ≤0.1 ms; **not** the primary claim

Primary measurement method matches C15 (n=200, hash+`atomic_write_bytes` inside timer).
See `experiments/phase5c-every-opt-c16/baseline.json`.

**Floor cause:** per-op `fdatasync`/`fsync` latency on overlay create+replace dominates;
microbench of fsync alone on a warm fd can be <0.1 ms, but durable *new-file*
checkpoint (mkstemp → write → fdatasync → replace → dir fsync) remains ~0.2–0.8 ms p99.

## Mitigations already shipped

- **BATCH** mode (`DURABLE_SYNC=batch` + `GroupFsyncSeal`) meets checkpoint_durable ≤0.1 ms (P7 / CP-0019 MET).
- EVERY remains available for callers that need sync-every-write; floor reported honestly.
- Crash invariants for EVERY still hold (mid-write tmp-only).
- **CP-0021:** `CHECKPOINT@floor:<n>` schema + one-tag-per-floor validator (tags scope).

## Exit criteria

- **Schema gate (MET / CP-0021):** schema documented; validator requires one
  checkpoint tag per floor; `tests/test_tags.py -k checkpoint_every_floor` green.
- **SLO gate (OPEN):** close only when primary-FS EVERY p99 ≤0.1 ms is **honestly**
  measured (same method), or council redefines the SLO to BATCH-primary with
  EVERY as best-effort. **No SLO chase** unless council orders it.

## Non-claims

No Raft/Paxos, N>2, multi-primary, ML, fabricated p99, or silent plaintext.
No broad checkpoint rewrite outside the tag invariant.
