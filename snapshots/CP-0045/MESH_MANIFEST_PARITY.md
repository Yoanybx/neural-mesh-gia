# Mesh Manifest Parity @N2

**Capability:** `MESH_MANIFEST_PARITY`  
**Cycle / Checkpoint:** 41 / CP-0045  
**Version:** 0.18.0  
**Theme:** `0.18_H8_manifest_parity` (blueprint L2 H8 / manifest_parity@N2)  
**Depends on:** H5 packaging distribution (`mesh.bundle/v1`), H7 clock fence,
N2 packaging (`mesh.bundle.manifest/v1-n2`)

## Purpose

Ship **manifest parity @N=2**, **byte-equality under concurrent build**,
**toolchain pin (P-09)**, and **ABORT→reject build** so a mismatched N2
manifest never silently ships — without Raft, without N>2 / multi-primary,
without plaintext, without Vault/ACME or GIA claims, and **without reopening**
frozen `0.16.3` / `0.17.0` tags.

This is the **last** H1..H8 theme. Extends existing
`packaging/manifest_n2` + `core_parity_checksums`; does **not** mutate frozen
single-node `mesh.bundle.manifest/v1`.

## What shipped

| Surface | Location |
|---------|----------|
| Library | `src/neural_mesh/packaging/parity/` — models, store, `ParityService`, CLI helpers |
| Schema | `mesh.manifest.parity/v1` — `docs/schema/manifest_parity/v1.md` |
| CLI | `mesh parity status \| check \| build-check` |
| Tests | `tests/test_manifest_parity_cycle41.py` (marker `manifest_parity_cycle41`) — T-H8a..(+neg) |
| Seal | `snapshots/CP-0045/` |

### Operator flows

1. **`mesh parity status --data-root DIR`** — pair, digests, mismatch/reject flags.
2. **`mesh parity check --data-root DIR [--no-auto-reject]`** — compare recorded
   N2 builds; with auto-reject (default) run ABORT→reject build on mismatch.
3. **`mesh parity build-check --data-root DIR [--manifest-a A --manifest-b B]`** —
   concurrent deterministic build byte-equality, or compare two manifest files.

### Library flows

```
bootstrap_pair(build-a, build-b, pin_toolchain=true)
record_build(side, manifest) → BuildArtifact (canonical digest)
check(auto_reject=true) → matched | mismatch→ABORT→reject build
concurrent_build_check(builder) → two threads; byte-equal or reject
core_parity_vs_single(n2_cs, single_cs) → extend manifest_n2 core_parity + ABORT
```

### Byte-equality under concurrent build

Two builders run concurrently (exactly workers=2 @N2). Canonical JSON strips
non-deterministic fields (`created_utc`) and forces `dual_primary=0`. Digests,
path checksums, and optional `bundle_sha256` must match. Toolchain pin hashes
must agree when present (P-09).

### ABORT→reject build

```
check / concurrent_build_check / core_parity_vs_single
  mismatch → mark_pending → ABORT→reject build
  further record_build / concurrent_build while rejected → fail-closed
```

## Bounds (NO_HELD)

| Held | Meaning here |
|------|----------------|
| No Raft / N>2 / multi-primary | Exactly N=2 pair; `ParityN2Only` on N>2 |
| No silent plaintext | `mode=plaintext` refused (`PARITY_PLAINTEXT_FORBIDDEN`) |
| No Vault/ACME required | Filesystem parity state + local toolchain pin only |
| No GIA / SLO chase | Packaging parity primitive only |
| No reopen 0.16.3 / 0.17.0 | Frozen channels + tags untouched |
| No invent GIA / N>2 after H8 | PREFERRED_NEXT=`0.18_signoff` |
| dual_primary | **Hard 0** |
| minority_writes | **Hard 0** |
| Economy | **PARKED** |

## Explicit non-claims

- Not Raft / quorum package fabric.
- Not N>2 cluster distribution / multi-primary heal.
- Not GIA / AGI.
- Does not reopen 0.16.3 RC or retag v0.17.0.
- Does not invent post-H8 GIA themes; next is `0.18_signoff`.
- Does not replace `mesh.bundle.manifest/v1-n2` (extends + fences it).

## Exit criteria

- [x] Capability + schema docs
- [x] Library check/concurrent-build/core-parity fail-closed
- [x] CLI `mesh parity status|check|build-check`
- [x] ≥14 pytest (`manifest_parity_cycle41`) covering T-H8(+neg)
- [x] CP-0045 sealed; ver **0.18.0**
- [x] PREFERRED_NEXT=`0.18_signoff`
