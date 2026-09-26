# Schema: mesh.bundle/v1

**Status:** ACTIVE (Cycle 38 / CP-0042)  
**Schema id:** `mesh.bundle/v1`  
**Toolchain schema:** `mesh.bundle.toolchain/v1`  
**Provenance schema:** `mesh.bundle.provenance/v1`  
**Signature schema:** `mesh.bundle.signature/v1`  
**Prior-pin schema:** `mesh.bundle.prior_pin/v1`  
**Theme:** `0.18_H5_packaging_distribution`

## Deprecation / coexistence

| Schema | Role |
|--------|------|
| `mesh.bundle.manifest/v1` | Single-node archive manifest (CP-0024..). **Still ACTIVE**. |
| `mesh.bundle.manifest/v1-n2` | N=2 archive manifest (CP-0031..). **Still ACTIVE**. |
| `mesh.bundle/v1` | **Distribution primitive** — signed manifest, provenance chain, replay guard, toolchain pin (P-09), revocation / ABORT→pin prior. |

Do **not** reopen frozen `0.16.3` / `0.17.0` release archives or retag `v0.16.3` / `v0.17.0`.  
Distribution channel for this schema is **`0.18.x`**.

## DistributionDocument

| Field | Type | Notes |
|-------|------|-------|
| `schema` | string | always `mesh.bundle/v1` |
| `bundle_id` | string | stable id for this distribution |
| `ver` | string | package version (`0.18.x` only for mint) |
| `channel` | string | `0.18.x` (frozen channels refused for distribute) |
| `name` | string | distribution name |
| `tip` | string\|null | git short tip |
| `cp_tip` | string | tip checkpoint id |
| `cp_range` | string | e.g. `CP-0001..0042` |
| `entrypoint` | string | usually `mesh` |
| `checksums` | object | path → sha256 |
| `bundle_sha256` | string | content digest |
| `signature` | object | `mesh.bundle.signature/v1` |
| `provenance` | array | `mesh.bundle.provenance/v1` steps (H5.b) |
| `replay_nonce` | string | unique nonce (H5.c replay guard) |
| `replay_seen` | bool | consumed flag |
| `toolchain` | object | `mesh.bundle.toolchain/v1` (P-09) |
| `revoked` | bool | revocation flag |
| `prior_pin` | object\|null | `mesh.bundle.prior_pin/v1` |
| `dual_primary` | int | **hard 0** |
| `vault_acme_required` | int | **hard 0** |
| `plaintext_fallback` | int | **hard 0** |
| `invariants_ok` | bool | all contract invariants held |
| `abort_pin_prior` | bool | ABORT→pin prior when breach |
| `source_manifest_schema` | string | usually `mesh.bundle.manifest/v1` |
| `cycle` | int | council cycle |
| `created_utc` | string\|null | UTC |
| `files` | array | included path list |

## Signature (`mesh.bundle.signature/v1`)

| Field | Type | Notes |
|-------|------|-------|
| `alg` | string | `hmac-sha256-local` (no Vault/ACME required) |
| `key_id` | string | `mesh-dist-local-v1` |
| `value` | string | HMAC hex over canonical JSON (signature.value blanked) |

## Provenance (`mesh.bundle.provenance/v1`)

| Field | Type | Notes |
|-------|------|-------|
| `parent_bundle_id` | string\|null | prior bundle (null on mint) |
| `parent_sha256` | string\|null | prior digest |
| `step` | string | `mint` \| `derive` \| … |
| `at` | string\|null | UTC |

## Toolchain (`mesh.bundle.toolchain/v1`) — P-09

| Field | Type | Notes |
|-------|------|-------|
| `compiler` | string | e.g. `cpython-3.12` |
| `libc` | string | host libc id |
| `locale` | string | e.g. `C.UTF-8` |
| `pin_hash` | string | sha256(`compiler\|libc\|locale\|mesh.bundle/v1`) |

## Prior pin (`mesh.bundle.prior_pin/v1`)

| Field | Type | Notes |
|-------|------|-------|
| `ver` | string | default `0.17.0` |
| `bundle_id` | string | prior id |
| `sha256` | string | prior digest |
| `label` | string | e.g. `dist/releases/0.17.0` |

## Tests (T-H5a..f + neg)

| Id | Coverage |
|----|----------|
| T-H5a | `distribute` mints `mesh.bundle/v1` under `dist/releases/0.18.x` |
| T-H5b | provenance chain (`mint` / `derive` parent links) |
| T-H5c | replay guard (nonce registry; second consume → ABORT) |
| T-H5d | signed-manifest verify (HMAC fail-closed) |
| T-H5e | toolchain pin present + mismatch path (P-09) |
| T-H5f | ABORT→pin prior; tags `v0.16.3`/`v0.17.0` untouched |

## Invariants (auto-fail → ABORT→pin prior)

1. `schema == mesh.bundle/v1`
2. `dual_primary == 0`
3. `plaintext_fallback == 0`
4. `vault_acme_required == 0`
5. channel not in frozen `{0.16.3, 0.16.x, 0.17.0, 0.17.x-n2}` for distribute
6. signature verifies
7. provenance non-empty; replay_nonce non-empty; toolchain.pin_hash non-empty
8. `revoked == false` for accept path
9. unknown / wrong schema → **fail-closed** (`DIST_SCHEMA_MISMATCH`)

Breach sets `abort_pin_prior=true` and raises `DistAbortPinPrior` — operator runs
`mesh dist pin-prior` to record prior known-good; **never** retag frozen releases.

## Error codes

| Code | Meaning |
|------|---------|
| `DIST_SCHEMA_MISMATCH` | wrong/missing schema or required field |
| `DIST_INVARIANT_BREACH` | dual_primary / plaintext / revoked / empty chain |
| `DIST_ABORT_PIN_PRIOR` | ABORT→pin prior |
| `DIST_REPLAY_DETECTED` | H5.c replay guard fired |
| `DIST_SIGNATURE_INVALID` | HMAC / key_id / alg failure |
| `DIST_TOOLCHAIN_MISMATCH` | P-09 pin mismatch |
| `DIST_FROZEN_CHANNEL` | refuse reopen 0.16.3 / 0.17.0 |
| `DIST_PLAINTEXT_FORBIDDEN` | plaintext mode refused |
| `DIST_N2_ONLY` | N>2 / Raft refused |

## Explicit non-claims

- Not a reopen of 0.16.3 RC or retag of v0.17.0.
- Not Vault/ACME-required signing.
- Not Raft / N>2 distribution fabric.
- Not GIA / SLO chase / tag_schema churn.
- Does not replace `mesh.bundle.manifest/v1` (coexists).
