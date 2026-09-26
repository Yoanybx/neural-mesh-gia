# Mesh Packaging Distribution

**Capability:** `MESH_PACKAGING_DISTRIBUTION`  
**Cycle / Checkpoint:** 38 / CP-0042  
**Version:** 0.18.0  
**Theme:** `0.18_H5_packaging_distribution` (blueprint L2 H5 / schema/bundle/v1)  
**Depends on:** single-node + N2 packaging (CP-0024..CP-0032), H4 OBS telemetry (CP-0041)

## Purpose

Elevate packaging from archive-only manifests into a **distribution primitive**
(`mesh.bundle/v1`): signed manifest, provenance chain, replay guard, toolchain
pin (P-09), and **ABORT→pin prior** — without reopening 0.16.3 RC, without
retaging v0.17.0, without Vault/ACME, without Raft/N>2, without GIA.

## What shipped

| Surface | Location |
|---------|----------|
| Library | `src/neural_mesh/packaging/distribution/` — models, distribute/verify/pin-prior, CLI helpers |
| Schema | `mesh.bundle/v1` — `docs/schema/bundle/v1.md` |
| CLI | `mesh dist distribute \| verify \| pin-prior \| schema` |
| Tests | `tests/test_packaging_dist_cycle38.py` (marker `packaging_dist_cycle38`) — T-H5a..f(+neg) |
| Seal | `snapshots/CP-0042/` |
| Artifacts | `dist/releases/0.18.0/` (frozen `0.16.3` / `0.17.0` dirs untouched) |

### Operator flows

1. **`mesh dist distribute [--repo DIR] [--out-dir DIR]`**  
   Mint `mesh.bundle/v1` under `dist/releases/0.18.x` with sign + provenance +
   replay nonce + toolchain pin.
2. **`mesh dist verify --file PATH`** (or stdin)  
   Fail-closed schema + signature + invariant check; breach → non-zero +
   `abort_pin_prior`.
3. **`mesh dist pin-prior [--repo DIR] [--reason TEXT]`**  
   ABORT path: record prior known-good (`0.17.0` default); **never** retag
   `v0.16.3` / `v0.17.0`.
4. **`mesh dist schema`**  
   Print active schema id + ops + T-H5a..f list.

### Tests mapped (DeepSeek blueprint T-H5a..f)

| Id | Behavior |
|----|----------|
| T-H5a | distribute mints schema-valid doc on `0.18.x` channel |
| T-H5b | provenance chain (`mint` / parent `derive`) |
| T-H5c | replay guard (nonce registry; second consume aborts) |
| T-H5d | signed-manifest verify (HMAC fail-closed) |
| T-H5e | toolchain pin (compiler+libc+locale → pin_hash) |
| T-H5f | ABORT→pin prior; frozen tags untouched |

### Fence / ABORT path

```
distribute(repo) → DistributionDocument (mesh.bundle/v1)
verify(doc)
  schema / signature / replay / toolchain / invariant breach
    → DistAbortPinPrior → abort_pin_prior=true
pin-prior(repo) → DIST_PRIOR_PIN.json (prior=0.17.0); retag=false
```

## Bounds (NO_HELD)

| Held | Meaning here |
|------|----------------|
| No Raft / N>2 / multi-primary | Distribution N≤2; refuse Raft claims |
| No silent plaintext | `plaintext_fallback` hard 0 |
| No Vault/ACME required | Local HMAC only (`hmac-sha256-local`) |
| No GIA / SLO chase | Packaging primitive only |
| No reopen 0.16.3 / 0.17.0 | Frozen channels + tags untouched |
| No H6..H8 | minority_write / clock_skew / manifest deferred |
| dual_primary | **Hard 0** |

## Explicit non-claims

- Not Raft / quorum package fabric.
- Not N>2 cluster distribution.
- Not GIA / AGI.
- Does not reopen 0.16.3 RC or retag v0.17.0.
- Does not implement H6..H8 this cycle.
- Does not replace `mesh.bundle.manifest/v1` (coexists; distribution wraps it).

## Exit criteria

- [x] Capability + schema docs
- [x] Library distribute/verify/pin-prior fail-closed
- [x] CLI `mesh dist distribute|verify|pin-prior|schema`
- [x] ≥14 pytest (`packaging_dist_cycle38`) covering T-H5a..f(+neg)
- [x] CP-0042 sealed; ver **0.18.0**
- [x] PREFERRED_NEXT=`0.18_H6_minority_write`
