# ARCHITECTURAL DECISIONS

Use ADR files for major decisions.

## ADR-0001 — Checkpoint integrity (Cycle 1)
- Store `manifest_sha256` inside `checkpoint.json` for humans/agents.
- Hash canonical JSON with `manifest_sha256` nulled to avoid circular digest.
- Freeze `.project_state/CHECKPOINT.json` into each snapshot folder so historical `verify` is independent of later global state.

## ADR-0002 — Digital Twin Phase 1 slice
- Pure Python + networkx public API; no Ray/torch required.
- Deterministic discrete-time scheduler; digest mixes seed + schedule for replay identity.

## ADR-0003 — Phase 1 fault injection + topology I/O + bench (Cycle 2)
- Faults: only `NODE_LOSS` and `PACKET_DROP` in Phase 1 (other codebook faults deferred to Phase 6).
- NODE_LOSS: node ineligible from `at_tick`; mid-flight tasks → `FAILED`.
- PACKET_DROP: seeded SHA256 Bernoulli on placement-path hops (up to 3 retries/hop); total loss → task stays pending → `UNSCHEDULED`.
- Topology JSON includes seed, nodes, links, tasks, faults; round-trip preserves digest.
- BenchmarkMetrics: makespan, mean_wait, mean_latency, utilization, packet drop stats.

## ADR-0004 — Twin package layout + ChatGPT interfaces (Cycle 3)
- Prefer `src/neural_mesh/twin/{faults,events,schema,storage,simulator}.py`; `digital_twin.py` is a compatibility shim.
- Canonical FaultEvent: event_id, fault_type, target_id, tick, seed, parameters (+ PACKET_DELAY).
- Topology ChatGPT schema (network_id, nodes.id/cpu/memory, links.source/target); hash into report + experiment checkpoint.json.
- Benchmark writes experiment-local checkpoint.json (does not auto-create snapshots/CP-*).
- Git gate PASS iff clean working tree; Safety SAFE iff network+physical actions denied.

## ADR-0005 — C-RAM v0 core (Cycle 4)
- Content identity = SHA-256 of raw bytes; metadata is sidecar and does not affect key.
- On-disk: `.cram/<first2>/<remainder>`; atomic writes.
- Object types limited to STATE/MEMORY/TASK/PLAN/EVIDENCE/CHECKPOINT; no free-text private thoughts.
- Placement: `int(key_hex[:16], 16) % len(sorted_nodes)` — deterministic, no consensus.
- Checkpoint fields `cram_root_hash` / `cram_objects` are optional with defaults so CP-0001..0007 remain verifiable.
- NODE_LOSS recovery: node-local view may fail; durable CAS + checkpoint refs ⇒ RECOVERABLE. No replication/consensus yet.

## ADR-0006 — C-RAM hardening Cycle 5 (recovery SLO + typed errors)
- `recovery_time` measured around locate+get; never STUB when C-RAM path runs.
- NODE_LOSS placement recovery: locate on declared topology; valid live route + successful get ⇒ RECOVERABLE with proof; otherwise ERROR. No optimistic RECOVERABLE.
- Do not re-hash over filtered live node sets (silent remap = stale location).
- If `expect_topology_hash` mismatches current `topology.hash()` ⇒ ERROR `CRAM_STALE_TOPOLOGY`, `located_node=None`.
- CLI exit codes frozen: 0 PASS, 1 generic, 2 integrity/corrupt, 3 missing/unavailable. `fsck_schema: 1`.
- Replica N=2 is interface/docs only until Cycle 6.
