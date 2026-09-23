# Cognitive Router R1 — Capability-aware (Cycle 10)

**CP-0014.** Extends R0 (`docs/cognitive_router_r0.md`, hardening C9). Activates
`CapabilityAwareStrategy` (replaces Cycle 9 STUB). Does **not** start Phase 4,
ML, Raft, or N>2. (TLS local mTLS closed Cycle 11.)

## P0 — Doc freeze

### Capability schema (versioned)

`CAPABILITY_SCHEMA_VERSION = 1`.

```
NodeCapability:
  node_id, cpu, memory, accelerators[], storage, network_class,
  supported_tasks[], health ∈ [0,1], advertised_at_ms, ttl_ms,
  schema_version
```

Unknown `schema_version` ⇒ reject advertisement (fail-closed).

### Advertisement / TTL / staleness

- Nodes advertise into `CapabilityRegistry` (persisted in C-RAM with
  `op_id + epoch + trace_id`).
- A capability is **fresh** iff `now_ms <= advertised_at_ms + ttl_ms`.
- **Stale** capabilities are rejected: never used for routing
  (exclude reason `STALE_CAPABILITY`). Bound: **0 routes to expired caps**.
- Default TTL: **5000 ms**. Capability update propagation bound
  **T_conv = 5.0 s** (same numeric bound as C-RAM eventual consistency).

### Determinism contract (R0 + cap_state_fp)

```
RouteDecision_canonical = f(policy_hash, seed, TaskSpec, candidates_fp, cap_state_fp)
```

- `cap_state_fp` = SHA-256 of sorted fresh `NodeCapability.to_dict()` list.
- Volatile excluded: `timestamp`, `metrics.decision_latency_ms`.
- Same inputs ⇒ **1000× byte-identical** canonical bytes (0 divergences).

### policy_hash and strategy

- R0 Round-Robin (default): `policy_hash` remains SHA-256 of normalized
  SAFETY_POLICY only (Cycle 8/9 back-compat).
- Capability-aware: effective policy includes
  `routing_strategy: "capability"` ⇒ **policy_hash changes** vs RR.
- Allowed policy keys schema v1 extended with optional `routing_strategy`
  (`rr` | `capability`).

### No-match policy (fail-closed)

If zero nodes match required capabilities / all stale / all score as
unavailable ⇒ `REJECTED` with reason **`CAPABILITY_NO_MATCH`**
(typed code `ROUTER_CAPABILITY_NO_MATCH`).

**Never** silent fallback to Round-Robin on capability mismatch.

### Scoring (deterministic, no ML)

```
score = capability_match + resource_fit + health - unavailable_penalty
```

Tie-break: higher score, then lexicographic `node_id`.

### Latency SLO (R1)

Routing decision p99 **< 8 ms** (relaxed vs R0 5 ms for capability lookup).

## Out of scope

ML/adaptive, Raft, N>2, silent RR fallback. (Phase 4 Network Fabric + local mTLS closed in Cycle 11 / CP-0015.)
