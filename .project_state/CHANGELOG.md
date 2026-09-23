# Changelog

## Cycle 14 — 2026-09-23 — CP-0018 Phase 5C Durability & Adversarial Partition
- WAL/fsync policy + DurabilityWAL (BEGIN/APPLY/COMMIT); crash invariants mid-write/append/checkpoint.
- N=2 partition suite first gate: minority=0, dual-primary=0, stale=100%, deterministic heal (NOT Raft).
- Safe snapshot compaction; CLI `mesh cram durability check|partition test|recovery trace`.
- Bench experiments/phase5c-durability-c14/; pytest 328; version 0.14.0; CP-0018 VERIFIED.
- Clarification: N=2 "majority" = fenced primary/heal only.

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

## 0.5.5 — Cycle 5 (2026-09-23)
- Real `recovery_time` instrumentation (t0/t1 locate+get); twin-basic MEASURED (no STUB).
- P1: NODE_LOSS → locate valid route OK; no route → ERROR (no optimistic RECOVERABLE).
- Stale topology hash guard (`CRAM_STALE_TOPOLOGY`); refuse silent stale location.
- Typed errors: `NodeUnavailable` vs `ObjectMissing` (+ `CRAMCorrupt`, `StaleTopology`).
- CLI: `mesh cram put|get|verify|fsck` — exit 0 PASS / 1 generic / 2 corrupt / 3 missing; `fsck --json` with `fsck_schema: 1`.
- Blob corruption + fsck orphans + fsync durability tests.
- Bench N=100 → p50/p99 persisted; p99 << 150ms on this box.
- Doc only: `docs/cram_replica_n2_interface.md` (no active replica). Exit codes frozen in `docs/cram_cli_exit_codes.md`.
- Tests: 74 passed. CP-0009 VERIFIED. No Phase 3 Router. No real replication.

## 0.7.0 — Cycle 7 (2026-09-23 EDT)
- Out-of-process C-RAM replica: Unix socket + size-limited framing
- `mesh cram replica serve|connect --socket`
- Real crash tests (kill -9, mid-frame cut); ≤1 writable primary
- OOP overhead p99 <10×; CP-0011 VERIFIED; pytest ≥110
- TLS/auth: EXPLICIT DEBT

## 0.8.0 — Cycle 8 (2026-09-23 EDT)
- Phase 3 Cognitive Router R0: TaskSpec / RouteCandidate / RouteDecision contract
- Deterministic Round-Robin with seed; UNAVAILABLE + capability + SAFETY_POLICY filters
- Decision log for every route; no physical/external-network execution
- Bench N=1000 → experiments/router-r0-bench-c8/; Twin+C-RAM+R0 integration
- Tests: 122 passed. CP-0012 VERIFIED. No R1/R2/R3, Raft, N>2 expand, ML, TLS.

### Cycle 8 DeepSeek deltas
- Frozen determinism contract (policy_hash + seed + TaskSpec)
- C-RAM DecisionStore persistence + op_id idempotency
- Safety fail-closed (≥8 cases) + saturation reject policy
- pytest ≥130; routing p99 <5ms

## 0.9.0 — Cycle 9 (2026-09-23)
- R0 Hardening + Observability (CP-0013): persist-ack guard, crash frontier, audit/replay, strategy stubs, TLS expiry 2026-12-31.

## 0.10.0 — Cycle 10 (2026-09-23 EDT)
- Cognitive Router R1 Capability-aware (CP-0014): versioned NodeCapability schema, TTL/staleness, CapabilityRegistry in C-RAM, real CapabilityAwareStrategy (replaces STUB).
- Determinism extends with `cap_state_fp`; no-match = CAPABILITY_NO_MATCH (never silent RR).
- CLI: `mesh router route --strategy rr|capability`; explain shows strategy/selected/score/factors.
- Bench N=1000 RR vs capability (metrics only); routing p99 <8ms; pytest ≥185.
- NO Phase 4 / TLS / ML / Raft / N>2.

## 0.11.0 — Cycle 11 (2026-09-23)
- Phase 4 Network Fabric v0 + local mTLS (trust model freeze).
- `src/neural_mesh/network/`: transport, tls, protocol, session, endpoint, fabric.
- Message types: TASK_REQUEST, STATE_QUERY/RESPONSE, HEARTBEAT, CAPABILITY_UPDATE, CHECKPOINT_NOTICE.
- Router R1 → Fabric → execution stub → C-RAM checkpoint integration.
- Faults: NETWORK_TIMEOUT, CONNECTION_DROP, INVALID_SESSION, MESSAGE_CORRUPTION; kill -9; dual-primary 0.
- Local mTLS debt RESOLVED (`docs/debt/TLS.md`); external PKI optional EXPLICIT DEBT.
- Bench N=1000 under experiments/network-fabric-tls-c11/.
- Tests: 217 passed. CP-0015 VERIFIED.
