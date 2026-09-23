# CHANGELOG

## 0.5.0
Bootstrap continuity system (shipped source).

## 0.5.1 — Cycle 1
- Fixed CheckpointManager integrity: canonical hash excludes embedded manifest field; frozen state snapshot enables historical verify.
- Fixed checkpoint ID allocation to scan `snapshots/CP-*` directories.
- Expanded Phase 0 tests (historical preserve, corruption of checkpoint + frozen state).
- Added Phase 1 Digital Twin deterministic simulator (`digital_twin.py`) + CLI `mesh twin run` + tests.
