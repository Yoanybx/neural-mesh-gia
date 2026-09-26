# Mesh OBS Telemetry Contract

**Capability:** `MESH_OBS_TELEMETRY`  
**Cycle / Checkpoint:** 37 / CP-0041  
**Version:** 0.18.0  
**Theme:** `0.18_H4_obs_telemetry` (blueprint L2 H4 / schema/obs track)  
**Depends on:** `MESH_OBSERVABILITY_STATUS_SNAPSHOT` (CP-0023), `MESH_OBS_PEERS` (CP-0034)

## Purpose

Ship a **versioned OBS telemetry contract** (`mesh.obs/v1`) that extends existing
status snapshot + richer OBS peers into council/M2M signals, cadence tiers,
invariant assertions, and **ABORT→block CP mint** on breach — without Raft,
without N>2, without SLO chase, and without reinventing peer probe.

## What shipped

| Surface | Location |
|---------|----------|
| Library | `src/neural_mesh/obs/` — models, emit/validate, CLI helpers |
| Schema | `mesh.obs/v1` — `docs/schema/obs/v1.md` |
| CLI | `mesh obs telemetry \| validate \| schema` |
| Tests | `tests/test_obs_telemetry_cycle37.py` (marker `obs_telemetry_cycle37`) |
| Seal | `snapshots/CP-0041/` |

### Operator flows

1. **`mesh obs telemetry [--repo DIR] [--cadence 10s] [--m2m|--json]`**  
   Emit contract from local status snapshot (peers optional via existing inject).
2. **`mesh obs validate --file PATH`** (or stdin)  
   Fail-closed schema + invariant check; breach → non-zero + `abort_block_cp`.
3. **`mesh obs schema`**  
   Print active schema id + required signals.

### Signals (DeepSeek C36 NEXT)

Contract signals: `recovery_p99`, `ckpt_durable`, `ckpt_parity`, `conflict_full`,
`conflict_classify`, `minority_writes`, `dual_primary`, `cp_lag`.  
Adversary: `replay_attempts`, `auth_fails`, `tier_changes`.  
Cadence tiers: `1s` / `10s` / `60s`.  
CP-cites-OBS-window linkage via `window.window_id`.

### Fence / ABORT path

```
emit(snapshot) → TelemetryDocument (mesh.obs/v1)
validate(doc)
  schema mismatch → ObsSchemaMismatch → ABORT→block CP mint
  invariant breach (dual_primary≠0, plaintext, minority_writes≠0, …)
    → ObsAbortBlockCp → abort_block_cp=true; never mint CP
```

## Bounds (NO_HELD)

| Held | Meaning here |
|------|----------------|
| No Raft / N>2 / multi-primary | Contract N≤2; refuse Raft claims |
| No silent plaintext | `plaintext_fallback` hard 0; mode=plaintext refused |
| No Vault/ACME required | Filesystem / snapshot emit only |
| No GIA / SLO chase | `recovery_p99` documented only — not re-benchmarked |
| No H5..H8 | Packaging / minority_write / clock_skew / manifest deferred |
| dual_primary | **Hard 0** |

## Explicit non-claims

- Not Raft / quorum consensus telemetry.
- Not N>2 cluster collector.
- Not GIA / AGI.
- Does not reopen 0.16.3 / 0.17.0 tags.
- Does not implement H5..H8 this cycle.
- Does not replace `mesh.status.snapshot/v1` (coexists; emit consumes it).

## Exit criteria

- [x] Capability + schema docs
- [x] Library emit/validate fail-closed
- [x] CLI `mesh obs telemetry|validate|schema`
- [x] ≥14 pytest (`obs_telemetry_cycle37`)
- [x] CP-0041 sealed; ver **0.18.0**
- [x] PREFERRED_NEXT=`0.18_H5_packaging_distribution`
