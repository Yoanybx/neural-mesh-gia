# Schema: mesh.manifest.parity/v1

**Status:** ACTIVE (Cycle 41 / CP-0045)  
**Schema id:** `mesh.manifest.parity/v1`  
**Store schema:** `mesh.manifest.parity.store/v1`  
**Report schema:** `mesh.manifest.parity.report/v1`  
**Build schema:** `mesh.manifest.parity.build/v1`  
**Toolchain schema:** `mesh.manifest.parity.toolchain/v1`  
**Theme:** `0.18_H8_manifest_parity`  
**Source manifests:** `mesh.bundle.manifest/v1-n2` (extend; do not mutate frozen v1)

## ParityStatus

| Field | Type | Notes |
|-------|------|-------|
| `schema` | string | always `mesh.manifest.parity/v1` |
| `ok` | bool | |
| `pair` | string[] | exactly 0..2 build side ids |
| `parity_ok` | bool | last check matched |
| `mismatch_detected` | bool | live pending mismatch |
| `build_rejected` | bool | ABORT→reject build engaged |
| `abort_reject_build` | bool | ABORT mode engaged |
| `dual_primary` | int | **hard 0** |
| `minority_writes` | int | **hard 0** |
| `vault_acme_required` | int | **hard 0** |
| `plaintext_fallback` | int | **hard 0** |
| `toolchain` | object | P-09 pin |
| `last_digest_a` / `last_digest_b` | string | sha256 of canonical bytes |
| `mismatch_paths` | string[] | e.g. `canonical_manifest`, path keys |
| `action` | string | (report) `none` \| `reject_build` \| `abort_reject_build` |

## BuildArtifact

| Field | Type | Notes |
|-------|------|-------|
| `schema` | string | `mesh.manifest.parity.build/v1` |
| `side` | string | pair id or `a`/`b` |
| `digest_sha256` | string | canonical manifest digest |
| `checksums` | object | path → sha256 |
| `bundle_sha256` | string\|null | optional archive digest |
| `toolchain_pin_hash` | string\|null | P-09 |
| `dual_primary` | int | **hard 0** |

## ParityCheckResult / ConcurrentBuildResult

| Field | Type | Notes |
|-------|------|-------|
| `outcome` | string | `matched` \| `mismatch` \| `rejected_abort` \| `pending` \| `incomplete` |
| `byte_equal` | bool | concurrent result only |
| `parity_ok` | bool | |
| `build_rejected` | bool | |
| `abort_reject_build` | bool | |

## ToolchainPin (P-09)

| Field | Type | Notes |
|-------|------|-------|
| `compiler` | string | e.g. `cpython-3.13` |
| `libc` | string | host libc / OS |
| `locale` | string | default `C.UTF-8` |
| `pin_hash` | string | sha256(`compiler\|libc\|locale`) |

## Error codes

| Code | Meaning |
|------|---------|
| `PARITY_MISMATCH` | byte / checksum / pin inequality |
| `PARITY_ABORT_REJECT_BUILD` | ABORT→reject build engaged |
| `PARITY_N2_ONLY` | N>2 / duplicate pair / workers≠2 refused |
| `PARITY_PLAINTEXT_FORBIDDEN` | plaintext mode refused |
| `PARITY_TOOLCHAIN_MISMATCH` | P-09 pin mismatch |
| `PARITY_FROZEN_CHANNEL` | refuse reopen 0.16.3 / 0.17.0 |
| `PARITY_INCOMPLETE` | both build sides required |

## Layout

```
<data-root>/
  parity/
    parity_state.json   # pair, digests, abort flags, toolchain
    builds.jsonl        # recorded BuildArtifact lines
```

## Invariants

- `dual_primary` hard 0
- `minority_writes` hard 0
- `vault_acme_required` hard 0
- `plaintext_fallback` hard 0
- Exactly N=2; no Raft
- Frozen channels `0.16.3` / `0.17.0` / `0.17.x-n2` not reopened
- Mismatch never silently accepted → ABORT→reject build
