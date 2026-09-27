# Schema: mesh.membership/v0 (STUB)

**Status:** STUB (Cycle 55 / CP-0059) — design alignment only; no membership runtime  
**Schema:** `mesh.membership/v0`  
**Design:** `docs/design/fabric/M2_MEMBERSHIP_REJOIN_DESIGN.md`  
**Composes:** `mesh.identity/v1` (H1 tiers T0..T3)  
**Non-goals:** no N>2; no Raft; no multi-primary; no GIA

## MembershipRecord (`mesh.membership/v0`)

| Field | Type | Notes |
|-------|------|-------|
| `schema` | string | `mesh.membership/v0` |
| `node_id` | string | Must equal cert CN/SAN |
| `state` | string | `JOINING` \| `ATTESTING` \| `ACTIVE` \| `DRAINING` \| `LEFT` \| `REJOIN` |
| `tier` | string | `T0`..`T3` from H1 |
| `rejoin` | bool | true when entered via REJOIN label |
| `fingerprint` | string | current leaf fingerprint |
| `prior_fingerprints` | string[] | retained on rotate / rejoin |
| `dual_primary` | int | **must be 0** |
| `n_cap` | int | **must be 2** while N>2 NO_HELD |
| `pending_writes` | int | drain guard (design) |
| `receipt_prev` | string\|null | audit chain |
| `receipt_hash` | string\|null | audit chain |
| `abort_code` | string\|null | last ABORT if any |

## State enum

`JOINING → ATTESTING → ACTIVE → DRAINING → LEFT → REJOIN` (REJOIN re-enters JOINING)

## Invariants (schema-level)

- `dual_primary == 0`
- `n_cap == 2`
- `state == ACTIVE` ⇒ `tier ∈ {T2, T3}`
- plaintext trust claims forbidden

## ABORT codes (membership)

| Code | Meaning |
|------|---------|
| `MEMBER_ATTEST_FAIL` | attestation mismatch / CA fail |
| `MEMBER_PLAINTEXT_FORBIDDEN` | plaintext trust claim |
| `MEMBER_N_GT2_REFUSED` | join would exceed N=2 |
| `MEMBER_DRAIN_ABORT` | drain timeout / loss risk |
| `MEMBER_REVOKED` | rejoin while revoked |
| `MEMBER_INVALID_TRANSITION` | illegal state edge |
| `MEMBER_TIER_INVARIANT` | ACTIVE without ≥T2 |
