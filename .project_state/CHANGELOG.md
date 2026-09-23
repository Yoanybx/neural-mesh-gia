# CHANGELOG

## 0.5.0
Bootstrap continuity system (shipped source).

## 0.5.1 — Cycle 1 (2026-09-23)
- Fixed CheckpointManager integrity verify (canonical hash; frozen snapshot state).
- Fixed checkpoint ID allocation over `snapshots/CP-*`.
- Expanded Phase 0 tests (historical preserve, content corruption).
- Added Phase 1 Digital Twin deterministic simulator + `mesh twin run` + tests.
- CLI: checkpoint evidence/tests/status flags; resume shows NEXT_ACTION.

## 0.5.2 — Cycle 2 (2026-09-23)
- Digital Twin: deterministic fault injection (`NODE_LOSS`, `PACKET_DROP`).
- Digital Twin: JSON topology load/save (`save_topology` / `load_topology`).
- Digital Twin: benchmark harness (schedule latency / utilization + packet stats).
- CLI: `mesh twin topology save|load`, `mesh twin bench`, `mesh twin run --topology/--fault`.
- Tests: 15 passed (was 9).

## 0.5.3 — Cycle 3 (2026-09-23)
- Refactored Digital Twin into `src/neural_mesh/twin/` (faults, events, schema, storage, simulator).
- FaultEvent ChatGPT fields; added PACKET_DELAY; CLI `--topology/--workload/--faults/--seed`.
- Topology.load/save/hash + workload hash recorded in reports / experiment checkpoints.
- Benchmark harness `mesh benchmark run twin-basic` → experiments/EXP-XXXX/.
- Part X: `mesh audit git`, `.project_state/SAFETY_POLICY.json`, `mesh safety status`.
- Tests: +15 new required suites; total 30 passed.

## 0.5.4 — Cycle 4 (2026-09-23)
- Phase 2 C-RAM Core: CAS under `.cram/<aa>/<rest>` (`put/get/exists/verify`).
- CRAMObject model (STATE/MEMORY/TASK/PLAN/EVIDENCE/CHECKPOINT); rejects private-thought metadata.
- Twin `CRAMPlacement.locate(cram_key, topology)` deterministic hash→node.
- Checkpoint schema: optional `cram_root_hash` + `cram_objects` (historical CP-0001..0007 still verify).
- NODE_LOSS: node-local get fails; durable store + checkpoint → RECOVERABLE.
- Tests: +6 suites; total 51 passed. CP-0008 VERIFIED.
