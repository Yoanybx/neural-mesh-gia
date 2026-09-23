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
