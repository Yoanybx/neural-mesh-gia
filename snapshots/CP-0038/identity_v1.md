# Schema: mesh.identity/v1

**Status:** ACTIVE (Cycle 34 / CP-0038)  
**Schema id:** `mesh.identity/v1`  
**Store schema:** `mesh.identity.store/v1`

## NodeIdentityRecord

| Field | Type | Notes |
|-------|------|-------|
| `schema` | string | always `mesh.identity/v1` |
| `node_id` | string | CN/SAN identity |
| `cert_fingerprint` | string | SHA-256 hex of leaf PEM |
| `cert_path` / `key_path` / `ca_cert_path` | string | LocalCA paths |
| `tier` | int | 0..3 (T0..T3) |
| `tier_name` | string | `T0`..`T3` (derived on serialize) |
| `revoked` | bool | |
| `pinned` | bool | T3 operator pin |
| `pinned_fingerprint` | string | pin set member |
| `revoked_fingerprints` | string[] | |
| `prior_fingerprints` | string[] | rotation history |
| `attested_at` / `updated_at` | string | UTC ISO-ish |
| `notes` | string | |
| `dual_primary` | int | **hard 0** |
| `vault_acme_required` | int | **hard 0** |
| `plaintext_fallback` | int | **hard 0** |

## AttestationResult

| Field | Type | Notes |
|-------|------|-------|
| `ok` | bool | |
| `node_id` | string | |
| `cert_fingerprint` | string | |
| `identities` | string[] | CN + DNS SANs |
| `tier` / `tier_name` | int / string | |
| `ca_verified` | bool | |
| `error` / `error_code` | string? | fail-closed codes |
| `pinned_only` | bool | abort mode |

## Error codes

| Code | Meaning |
|------|---------|
| `IDENTITY_MISMATCH` | CN/SAN ≠ expected node_id |
| `IDENTITY_ATTESTATION_FAILED` | missing cert / CA verify fail |
| `IDENTITY_TIER_BOUNDS` | tier outside T0..T3 |
| `IDENTITY_TIER_ERROR` | illegal upgrade / pin rules |
| `IDENTITY_REVOKED` | revoked identity or fingerprint |
| `IDENTITY_PINNED_ONLY` | ABORT mode reject |
| `IDENTITY_PLAINTEXT_FORBIDDEN` | plaintext mode refused |

## Layout

```
<fabric-root>/
  ca.crt
  nodes/<node_id>/node.{crt,key}
  identity/
    identity_state.json    # pinned_only flag
    identities/<node_id>.json
```
