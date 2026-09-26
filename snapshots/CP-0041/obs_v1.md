# Schema: mesh.obs/v1

**Status:** ACTIVE (Cycle 37 / CP-0041)  
**Schema id:** `mesh.obs/v1`  
**Signals schema:** `mesh.obs.signals/v1`  
**Adversary schema:** `mesh.obs.adversary/v1`  
**Window schema:** `mesh.obs.window/v1`  
**Theme:** `0.18_H4_obs_telemetry`

## Deprecation / coexistence

| Schema | Role |
|--------|------|
| `mesh.status.snapshot/v1` | Local operator status snapshot (CP-0023 / C19; peers C30). **Still ACTIVE** — emit path consumes it. |
| `mesh.obs/v1` | Versioned **OBS telemetry contract** for council M2M, CP mint gates, and invariant assertions. |

Do **not** invent a parallel peer probe or Raft/N>2 collector. Extend
`status_snapshot` / `obs_peers` into this contract; fail-closed on schema mismatch.

## TelemetryDocument

| Field | Type | Notes |
|-------|------|-------|
| `schema` | string | always `mesh.obs/v1` |
| `node_id` | string | emitter node |
| `cycle` | int | council cycle |
| `ver` | string | package version |
| `tip` | string\|null | git short tip |
| `cp_tip` | string | tip checkpoint id |
| `cp_range` | string | e.g. `CP-0001..0041` |
| `pytest` | object | `{passed, failed}` |
| `slo_state` | object | documented states only (no re-benchmark) |
| `debt_gates` | array | from status snapshot |
| `peers` | array | injected / RO-probed peer rows (≤2 live probe) |
| `signals` | object | `mesh.obs.signals/v1` (see below) |
| `adversary` | object | `mesh.obs.adversary/v1` |
| `cadence` | string | `1s` \| `10s` \| `60s` |
| `window` | object | `mesh.obs.window/v1` — CP-cites-OBS-window |
| `dual_primary` | int | **hard 0** |
| `vault_acme_required` | int | **hard 0** |
| `plaintext_fallback` | int | **hard 0** |
| `invariants_ok` | bool | all contract invariants held |
| `abort_block_cp` | bool | ABORT→block CP mint when breach |
| `source_schema` | string | usually `mesh.status.snapshot/v1` |

## Signals (`mesh.obs.signals/v1`)

| Signal | Type | Notes |
|--------|------|-------|
| `recovery_p99` | string | documented / SCHEMA-GATED — **no SLO chase** |
| `ckpt_durable` | string | e.g. `MET` |
| `ckpt_parity` | string | e.g. `MET` / `UNKNOWN` |
| `conflict_full` | int | count (≥0) |
| `conflict_classify` | int | count (≥0) |
| `minority_writes` | int | **hard 0** intent at N=2 fence |
| `dual_primary` | int | **hard 0** |
| `cp_lag` | int | checkpoint lag (≥0) |

## Adversary (`mesh.obs.adversary/v1`)

| Signal | Type | Notes |
|--------|------|-------|
| `replay_attempts` | int | ≥0 |
| `auth_fails` | int | ≥0 |
| `tier_changes` | int | ≥0 |

## Window (`mesh.obs.window/v1`)

| Field | Type | Notes |
|-------|------|-------|
| `window_id` | string | stable id for CP citation |
| `started_at` | string\|null | UTC |
| `ended_at` | string\|null | UTC |
| `cadence` | string | echo of document cadence |

## Cadence tiers

| Tier | Use |
|------|-----|
| `1s` | hot path / local operator poll (optional) |
| `10s` | default emit / validate |
| `60s` | council M2M / CP mint window |

## Invariants (auto-fail → ABORT→block CP mint)

1. `schema == mesh.obs/v1`
2. `dual_primary == 0`
3. `plaintext_fallback == 0`
4. `vault_acme_required == 0`
5. `signals.dual_primary == 0`
6. `signals.minority_writes == 0`
7. required fields present and typed
8. unknown / wrong schema → **fail-closed** (`OBS_SCHEMA_MISMATCH`)

Breach sets `abort_block_cp=true` and raises `ObsAbortBlockCp` — **never** mint CP on breach.

## Error codes

| Code | Meaning |
|------|---------|
| `OBS_SCHEMA_MISMATCH` | wrong/missing schema id or required field |
| `OBS_INVARIANT_BREACH` | dual_primary / plaintext / minority_writes / etc. |
| `OBS_ABORT_BLOCK_CP` | ABORT→block CP mint |
| `OBS_PLAINTEXT_FORBIDDEN` | plaintext mode refused |
| `OBS_N2_ONLY` | N>2 / Raft refused |
| `OBS_CADENCE_INVALID` | cadence not in {1s,10s,60s} |

## Explicit non-claims

- Not Raft / N>2 collector.
- Not SLO re-benchmark (`recovery_p99` is documented state, not chased).
- Not GIA.
- Does not replace `mesh.status.snapshot/v1`.
