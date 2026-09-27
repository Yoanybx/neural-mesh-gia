## Cycle 49 — 2026-09-26 — CP-0053 agent_shell_spike_execution
- docs/design/AGENT_SHELL_SPIKE_EXECUTION.md; MESH_AGENT_SHELL_SPIKE_EXECUTION.
- MockAgentShellAdapter pipeline (workload→normalize→probes→receipts→reports).
- Hash-chained receipts; ABORT schema/fence/tool/policy/audit; tests=14; pytest 816.
- No settlement/API keys/src runtime; package 0.18.0 held; NEXT=M1_scorecard_maturation.

## Cycle 48 — 2026-09-26 — CP-0052 L_judge MIX integration design
- docs/design/L_JUDGE_MIX_INTEGRATION.md (I2..I6 call/inject/parse/ABORT/receipt).
- docs/schema/judge/injection_v0.md; MESH_L_JUDGE_MIX_INTEGRATION.
- tests l_judge_integration_cycle48 (MockLJudgePort; no API keys); CP-0052 VERIFIED.
- No src codec / live engine; package 0.18.0 held; NEXT=agent_shell_spike_execution.

## Cycle 47 — 2026-09-26 — CP-0051 L_judge schema stubs
- docs/schema/{judge,goal,continuity,shell}/v0.md stubs; MESH_L_JUDGE_SCHEMA_STUBS.
- tests schema_stubs_cycle47 (10); pytest 789; CP-0051 VERIFIED.
- No runtime codecs; package 0.18.0 held; NEXT=await_deepseek_c43_c47.

## Cycle 46 — 2026-09-26 — CP-0050 M1 consensus choice design + M2/M3 pointers
- docs/design/fabric/M1_CONSENSUS_CHOICE_DESIGN.md (scorecard ≥80; no default=Raft).
- M2 membership + M3 WAN/HLC pointer docs; MESH_M1_CONSENSUS_CHOICE_DESIGN.
- tests m1_design_cycle46 (10); pytest 779; CP-0050 VERIFIED.
- Runtime Raft/N>2 still NO_HELD; package 0.18.0 held; NEXT=L_judge_schema_stubs.

## Cycle 45 — 2026-09-26 — CP-0049 agent_shell_adapter_spike_plan
- docs/design/AGENT_SHELL_ADAPTER_SPIKE.md + MESH_AGENT_SHELL_SPIKE_PLAN.
- tests shell_spike_cycle45 (10); pytest 769; CP-0049 VERIFIED.
- No shell runtime/settlement; package 0.18.0 held; NEXT=M1_consensus_choice_design.

## Cycle 44 — 2026-09-26 — CP-0048 0.19 scope freeze A–D
- docs/planning/0.19_SCOPE_FROZEN.md + council/SCOPE_0.19_FROZEN.md; DRAFT SUPERSEDED.
- MESH_0.19_SCOPE_FREEZE; tests scope_freeze_cycle44 (10); pytest 759; CP-0048 VERIFIED.
- Package 0.18.0 held; NO_HELD unchanged; PREFERRED_NEXT=agent_shell_adapter_spike_plan.

## Cycle 43 — 2026-09-26 — CP-0047 0.19 bootstrap plan / L_judge MIX + durable goals design
- docs/planning/0.19_{BOOTSTRAP,SCOPE_DRAFT,NON_GOALS}.md (DRAFT; version 0.18.0 held).
- docs/design/L_JUDGE_MIX_DESIGN.md + DURABLE_GOALS_CONTINUITY_DESIGN.md.
- MESH_0.19_BOOTSTRAP_PLAN; council SCOPE_0.19_DRAFT; HYPERBRAIN_ASTRA authority.
- tests/test_019_bootstrap_plan_cycle43.py (13); pytest 749; CP-0047 VERIFIED.
- v0.18.0 / 0.17.0 / 0.16.3 untouched; no GIA/Raft/N>2/train/SaaS/economy; NO_HELD held.

## Cycle 33 — 2026-09-23 — CP-0037 0.18 bootstrap / GOV.7 entry
- Package version 0.18.0; docs/planning/0.18_{BOOTSTRAP,SCOPE,SCOPE_FROZEN,NON_GOALS}.md.
- council/SCOPE_0.18_FROZEN.md; MESH_0.18_BOOTSTRAP capability.
- docs/debt/SCHEMA_GATE_0.18_ENTRY.md WAIVE_VIA_ACCEPT_AND_CARRY (GOV.7); links 0.17 resolution.
- tests/test_018_bootstrap_cycle33.py (12); pytest 579; CP-0037 VERIFIED.
- v0.17.0 + dist/releases/0.17.0 + v0.16.3 untouched; no H1..H8 impl; NO_HELD unchanged.

## Cycle 27 — 2026-09-23 — CP-0031 N=2 multi-node packaging
- P27: docs/capabilities/MESH_PACKAGING_N2_MULTI_NODE.md (schema v1-n2; fenced heal NOT Raft; dual_primary=0).
- P28: manifest_n2 + bundle_n2; build_n2_bundle/verify_n2_bundle; core parity vs single-node; N2 stubs/scripts.
- P29: n2_install_dual + n2_install_rollback_smoke (node-a/node-b prefixes; replica mock OOB).
- tests/test_packaging_n2_cycle27.py (14); packaging_n2 14; packaging ~105; pytest 491; CP-0031 VERIFIED.
- Version 0.17.0 held; 0.16.3 CLOSED; single-node v1 frozen untouched.
- No Raft/N>2/multi-primary; no SLO chase; no tag-schema; no EVERY_fsync.

## Cycle 26 — 2026-09-23 — CP-0030 0.17 scope freeze / schema gate / bootstrap
- P24: docs/planning/0.17_SCOPE_FROZEN.md + council/SCOPE_0.17_FROZEN.md; PLAN marked FROZEN.
- P25: docs/debt/SCHEMA_GATE_RESOLUTION_0.17.md resolution=ACCEPT_AND_CARRY; debt_gate_status helper.
- P26: package version 0.17.0; docs/planning/0.17_BOOTSTRAP.md; NEXT_ACTION → N=2 multi-node (deferred).
- tests/test_packaging_rc_cycle26.py (13); packaging 91; pytest 477; CP-0030 VERIFIED.
- Release 0.16.3 CLOSED/FROZEN; tag v0.16.3 untouched; freeze channel 0.16.x still closed for RC.
- No SLO chase; no tag-schema; no Raft/N>2/consensus changes; no full theme impl.

## Cycle 25 — 2026-09-23 — CP-0029 Post-release ops + 0.17 planning
- P21: scripts/post_release_monitor.py --continue; monitor_history.jsonl append/roll; fail if signoff/archive missing.
- P22: docs/planning/0.17_SCOPE.md + 0.17_NON_GOALS.md + council/PLAN_0.17_DRAFT.md (planning only; no 0.17 features).
- P23: scripts/debt_gate_review.py + docs/debt/DEBT_GATE_REVIEW_CP0029.md; SCHEMA-GATED consistency; JSON M2M; no rebenchmark.
- tests/test_packaging_rc_cycle25.py (12); packaging 78; pytest 464; CP-0029 VERIFIED.
- Version 0.16.3 held (signed-off); next_line=0.17.x note only.
- No SLO chase; no tag-schema; no Raft/N>2/consensus changes.

## Cycle 24 — 2026-09-23 — CP-0028 Packaging RC (signoff / tag archive / monitor)
- P18: scripts/release_signoff.py + packaging.release_signoff; SIGNOFF.json (signer=council:DeepSeek+Grok).
- P19: scripts/release_tag_archive.py + packaging.release_tag_archive; local tag + dist/releases/0.16.3/ archive.
- P20: scripts/post_release_monitor.py + MESH_PACKAGING_POST_RELEASE_MONITOR.md; --once MONITOR.json (no Grok Bot routine).
- tests/test_packaging_rc_cycle24.py (13); packaging 66; pytest 452; CP-0028 VERIFIED.
- Version 0.16.3 kept as signed-off release (Cycle 24 = release closeout of 0.16.3).
- No SLO chase; no tag-schema; no Raft/N>2/consensus changes.

## Cycle 23 — 2026-09-23 — CP-0027 Packaging RC (soak / final audit / watch)
- P15: scripts/rc_soak.py + packaging.rc_soak (N-iter install/status/verify[/smoke]; p50/p99; variance bound).
- P16: scripts/final_release_audit.py + MESH_PACKAGING_FINAL_RELEASE_AUDIT.md; JSON M2M release-ready gate.
- P17: scripts/post_rc_watch.py + MESH_PACKAGING_POST_RC_WATCH.md; --once watch report (no Grok Bot routine).
- tests/test_packaging_rc_cycle23.py (15); packaging 53; pytest 439; CP-0027 VERIFIED.
- Version 0.16.3 (DeepSeek gave no hard VER; final soak/audit on RC track).
- No SLO chase; no tag-schema; no Raft/N>2/consensus changes.

## Cycle 22 — 2026-09-23 — CP-0026 Packaging RC (install / rollback / checklist)
- P12: scripts/rc_install_verify.py + packaging.rc_install (clean prefix PYTHONPATH install).
- P13: scripts/rollback_smoke.py + packaging.rollback (B→A filesystem rollback).
- P14: scripts/release_checklist.py + MESH_PACKAGING_RELEASE_CHECKLIST.md; JSON M2M.
- tests/test_packaging_rc_cycle22.py (13); packaging 38; pytest 424; CP-0026 VERIFIED.
- Version 0.16.2 (DeepSeek gave no hard VER; RC packaging track on 0.16.1).
- No SLO chase; no tag-schema; no Raft/N>2/consensus changes.

## Cycle 21 — 2026-09-23 — CP-0025 Packaging RC (clean-node / repro / freeze)
- P9: scripts/clean_node_smoke.py + packaging.clean_node_smoke (isolated extract smoke).
- P10: scripts/repro_check.py + build_bundle --repro-check; name-based modes; hash-lock.
- P11: freeze{channel:0.16.x,schema:v1}; docs RC freeze; version 0.16.1 (DeepSeek gave no hard VER).
- tests/test_packaging_rc_cycle21.py (13); packaging 25; pytest 411; CP-0025 VERIFIED.
- No SLO chase; no tag-schema; no Raft/N>2/consensus changes.

## Cycle 20 — 2026-09-23 — CP-0024 Mesh Packaging Single-Node Bundle
- schema mesh.bundle.manifest/v1 (name, ver, tip, cp_range, pytest, entrypoint, checksums).
- scripts/build_bundle.py + scripts/verify_bundle.py; neural_mesh.packaging (deterministic tar).
- tests/test_packaging_single_node_bundle.py (≥10; 12 passed); docs/capabilities/MESH_PACKAGING_SINGLE_NODE_BUNDLE.md.
- pytest 398; audit PASS; version 0.16.0; CP-0024 VERIFIED.
- No SLO chase; no tag-schema; no Raft/N>2/consensus changes.

# Changelog

## Cycle 19 — 2026-09-23 — CP-0023 Mesh Observability Status Snapshot
- schema mesh.status.snapshot/v1 (node_id, cycle, ver, cp_range, pytest, slo_state, debt_gates, peers, local).
- API neural_mesh.status.snapshot / status_snapshot; CLI mesh status --snapshot/--m2m; format_obs_m2m.
- tests/test_observability_status_snapshot.py (≥12; 14 passed); docs/capabilities/MESH_OBSERVABILITY_STATUS_SNAPSHOT.md.
- pytest 386; audit PASS; version 0.15.0; CP-0023 VERIFIED.
- No SLO chase; no tag-schema; no Raft/N>2/consensus writes; peers injected/mock only.

## Cycle 18 — 2026-09-23 — CP-0022 tag schema gate
- schema_gate_checkpoint_every_floor in neural_mesh.tags (SCHEMA-GATED debt gate).
- Strengthened tests/test_tags.py -k checkpoint_every_floor (schema gate presence + one-per-floor).
- docs/debt/CHECKPOINT_EVERY_FLOOR.md: SCHEMA-GATED ref, SLO gap ~1.32ms, No SLO chase.
- pytest 372; audit PASS; version 0.14.4; CP-0022 VERIFIED.
- No SLO chase; no refactor outside tags; no Raft/N>2/ML.


## Cycle 17 — 2026-09-23 — CP-0021 floor checkpoint tag invariant
- Schema CHECKPOINT@floor:<n> in docs/debt/CHECKPOINT_EVERY_FLOOR.md.
- Validator neural_mesh.tags.validate_one_checkpoint_tag_per_floor (one tag per floor).
- tests/test_tags.py -k checkpoint_every_floor; debt SCHEMA-GATED; pytest 369; 0.14.3.
- No SLO chase; no refactor outside tags; no Raft/N>2/ML.

## Cycle 16 — 2026-09-23 — CP-0020 EVERY floor opt (GAP-with-debt)
- EVERY hot-path: os.write + fdatasync|fsync; DirFsyncCoalescer; compact_checkpoint_bytes.
- Rebench phase5c-every-opt-c16; EVERY primary GAP; BATCH+recovery MET; EXPLICIT DEBT.
- pytest 359; audit PASS; version 0.14.2; CP-0020 VERIFIED.

- P7: DURABLE_SYNC=batch + GroupFsyncSeal; checkpoint_durable p99 MET ≤0.1ms; EVERY floor reported honestly.
- P8: recovery VERIFY tune; FSM recovery_time_ms; p99 MET ≤2ms.
- Rebench experiments/phase5c-slo-close-c15/; pytest 343; version 0.14.1; CP-0019 VERIFIED.
- Docs: durable vs parity; sync modes; no fabricated p99.


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
## Cycle 28 — 2026-09-23 — CP-0032 N2 RC packaging hardening
- P30: n2_rc_soak (N-iter dual-prefix install smoke; p50/p99; variance fail).
- P31: n2_final_release_audit + MESH_PACKAGING_N2_FINAL_RELEASE_AUDIT.md (M2M JSON).
- P32: N2 freeze always-on channel 0.17.x-n2; verify rejects wrong/missing; schema FROZEN for N2 RC; 0.16.3 untouched.
- tests/test_packaging_n2_cycle28.py (13); packaging_n2 27; pytest 504; CP-0032 VERIFIED; ver 0.17.0 held.

## Cycle 29 — 2026-09-23 — CP-0033 Fabric ops UX
- docs/capabilities/MESH_FABRIC_OPS_UX.md
- src/neural_mesh/network/ops.py (status/diagnose/reconnect)
- CLI mesh fabric status|diagnose|reconnect
- tests/test_fabric_ops_cycle29.py (16); pytest 520; CP-0033 VERIFIED; ver 0.17.0 held.
