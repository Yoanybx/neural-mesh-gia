# Trust Tiers v1 (T0..T3)

**Status:** ACTIVE (Cycle 34 / CP-0038 / H1)  
**Policy id:** `trust-tiers-v1`  
**Schema:** `mesh.identity/v1`  
**ABORT:** pinned-only

## Definitions

| Tier | Name | Meaning | How reached |
|------|------|---------|-------------|
| **T0** | Untrusted | Unknown, revoked, or explicitly untrusted. No write / join authority under identity policy. | Default; revoke; downgrade terminus |
| **T1** | Provisional | TOFU / first-seen fingerprint recorded, not yet CA-attested. Limited trust. | First observation without full attest; explicit assign ≤T1 |
| **T2** | Attested | Leaf cert verified under **local CA**; CN/SAN = `node_id`. | Successful `mesh id attest` |
| **T3** | Pinned | Operator-confirmed pin of fingerprint. Survives ABORT→pinned-only. | `mesh id tier --set T3 --pin` after attest |

## Escalation (upgrade)

- T0/T1 → T2: requires successful local-CA attestation (fail-closed).
- → T3: requires **explicit operator pin** (`--pin`). No silent escalate.
- Vault / ACME **not** required (NO_HELD: Vault-ACME-req).

## Downgrade path (P-10)

Explicit one-step path: **T3 → T2 → T1 → T0**.

- Downgrade is always recorded on the identity record (`notes`, `updated_at`).
- Revocation forces **T0** and appends fingerprint to `revoked_fingerprints`.
- **No silent identity downgrade** on rotate: prior fingerprint retained in
  `prior_fingerprints`; tier preserved unless operator downgrades.

## ABORT → pinned-only

On attestation mismatch / CA verify failure / revoke:

1. Enter **pinned-only** abort mode on the identity store.
2. Subsequent accepts require fingerprint ∈ pin set (T3 pinned).
3. Unpinned / unknown identities are rejected (`IDENTITY_PINNED_ONLY`).

Clearing pinned-only is an explicit operator action (not automatic).

## Invariants

- `dual_primary = 0`
- `plaintext_fallback = 0` (plaintext mode forbidden for identity ops)
- `vault_acme_required = 0`
- Tier bounds strictly **T0..T3**

## Related

- `docs/capabilities/MESH_IDENTITY_ATTESTATION.md`
- `docs/schema/identity/v1.md`
- `docs/network_fabric_tls.md` (CN/SAN = node_id)
