# CHANGELOG

## 0.5.0
Bootstrap continuity system (shipped source).

## 0.5.1 — Cycle 1 (2026-09-23)
- Fixed CheckpointManager integrity verify (canonical hash; frozen snapshot state).
- Fixed checkpoint ID allocation over `snapshots/CP-*`.
- Expanded Phase 0 tests (historical preserve, content corruption).
- Added Phase 1 Digital Twin deterministic simulator + `mesh twin run` + tests.
- CLI: checkpoint evidence/tests/status flags; resume shows NEXT_ACTION.
