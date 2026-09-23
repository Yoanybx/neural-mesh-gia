# Cognitive Router R0 — Contract (Cycle 8 / Phase 3)

**FROZEN for CP-0012** (ChatGPT A + DeepSeek B changes).  
**Cycle 9 hardening addendum:** `docs/cognitive_router_r0_hardening_c9.md` (persist-ack guard, phantom semantics, TLS expiry 2026-12-31). Determinism contract unchanged.
**No R1/R2/R3, Raft, N>2 expand, ML/adaptive, or TLS** in Cycle 8/9.

## P0 — Determinism contract (falsable)

```
RouteDecision_canonical = f(policy_hash, seed, TaskSpec, candidates_fingerprint)
```

Properties:

1. **Byte-identical**: same `(policy_hash, seed, TaskSpec, candidates)` ⇒ identical
   canonical JSON bytes (sorted keys, no volatile fields).
2. **Volatile excluded from canonical form**: `timestamp`, `metrics.decision_latency_ms`.
3. **policy_hash**: SHA-256 of canonical SAFETY_POLICY JSON (`policy_schema_version` +
   known keys only). See § Policy versioning.
4. **candidates_fingerprint**: SHA-256 of sorted `RouteCandidate.to_dict()` list.
5. **RR cursor**: initialized from `seed`; advances only on **new accepted** decisions
   (idempotent `op_id` replay does **not** advance the cursor).

Acceptance: **1000** identical runs → **0** byte divergences on canonical payload.

## Pipeline

```
TaskSpec (+ op_id, trace_id)
  → validate policy (fail-closed on unknown)
  → idempotent lookup by op_id in C-RAM (return prior decision if present)
  → saturation check (queue > bound → REJECT)
  → exclude UNAVAILABLE
  → capability filter
  → SAFETY_POLICY filter (network/physical)
  → deterministic Round-Robin
  → RouteDecision (reason + metrics + policy_hash + op_id + epoch + trace_id)
  → persist EVERY decision in C-RAM (CAS) keyed by op_id
  → decision log (JSONL mirror)
```

## Types

| Type | Fields (core) |
|------|----------------|
| `TaskSpec` | `task_id`, `required_capabilities`, `requires_network`, `requires_physical`, `op_id`, `trace_id`, (+ optional objective/priority/…) |
| `RouteCandidate` | `node_id`, `capabilities`, `status` (`AVAILABLE`\|`UNAVAILABLE`), `cpu`, `memory` |
| `RouteDecision` | `task_id`, `status`, `reason`, `selected_node_id`, `eligible`, `excluded`, `metrics`, `seed`, `policy_hash`, `op_id`, `epoch`, `trace_id`, `candidates_fingerprint` |

## Safety — fail-closed

- No silent fallbacks. No capable/safe route ⇒ `REJECTED` with typed reason/code.
- Exclude `UNAVAILABLE`.
- Respect SAFETY_POLICY (`allow_network_actions`, `allow_physical_actions`).
- Router **never** executes physical or external-network actions.
- **Unknown policy** (unknown key or `policy_schema_version`) ⇒ `REJECTED` /
  `ROUTER_UNKNOWN_POLICY` — never route under an unrecognized policy.
- Log + persist every decision (accept or reject).

## Policy versioning

- `policy_schema_version` must be `1` (missing ⇒ treated as `1` only for the
  built-in DEFAULT_POLICY keys).
- Allowed keys (schema v1): `policy_schema_version`, `allow_network_actions`,
  `allow_physical_actions`, `require_human_approval`.
- Any other key ⇒ unknown policy → fail-closed.
- `policy_hash = SHA256(canonical_json(normalized_policy))`.

## Saturation (queue > bound)

When `inflight_accepted >= queue_bound` and the next decision would be ACCEPTED:

- **Reject** with reason `SATURATION_QUEUE_FULL` (no silent drop, no adaptive ML).
- Bound default: `1000`. Configurable on router. Bench documents behavior.

## C-RAM audit persistence

- Every `RouteDecision` is stored as CAS bytes (canonical JSON) in C-RAM.
- Index: `op_id → content_hash`.
- Fields stamped: `op_id`, `epoch`, `trace_id`, `policy_hash`.
- **Idempotency**: same `op_id` ⇒ return the single stored decision (100 retries → 1 object).

## Latency SLO (R0 in-process)

- Routing decision p99 **< 5 ms** (in-process; no AF_UNIX required for pure route()).

## Out of scope (R0)

- R1 capability-aware / weighted / priority scoring
- R2/R3, ML, embeddings, adaptive routing
- Raft / consensus / N>2 mesh expand / TLS (TLS remains EXPLICIT DEBT)

## TLS debt (Cycle 9 formal)

Accepted until Phase 4. **Expiry: 2026-12-31.** See
`docs/cognitive_router_r0_hardening_c9.md`. No TLS implementation in R0 cycles.

## Persist-ack guard (Cycle 9)

When `DecisionStore` is configured, `RouteDecision` is returned only after C-RAM
persist ACK. Failure ⇒ `CramPersistError` — zero phantom decisions.

