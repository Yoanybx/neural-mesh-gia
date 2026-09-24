# Mesh Identity + Attestation + Trust Tiers

**Capability:** `MESH_IDENTITY_ATTESTATION`  
**Cycle / Checkpoint:** 34 / CP-0038  
**Version:** 0.18.0  
**Theme:** `0.18_H1_identity` (blueprint L2 H1 / I1 subset)  
**Depends on:** Phase 4 Network Fabric mTLS (`docs/network_fabric_tls.md`) — LocalCA leafs, CN/SAN = `node_id`

## Purpose

Ship **node identity records**, **local-CA attestation**, **trust tiers T0..T3**,
**rotation / revocation**, and **ABORT→pinned-only** without requiring Vault/ACME
and without silent identity downgrade or plaintext trust claims.

## What shipped

| Surface | Location |
|---------|----------|
| Library | `src/neural_mesh/identity/` — models, store, `IdentityService` |
| Schema | `mesh.identity/v1` — `docs/schema/identity/v1.md` |
| Policy | `docs/policy/trust-tiers-v1.md` (T0..T3 + P-10 downgrade) |
| CLI | `mesh id status \| attest \| tier \| rotate \| revoke` |
| Tests | `tests/test_identity_cycle34.py` (marker `identity_cycle34`) |
| Seal | `snapshots/CP-0038/` |

### Operator flows

1. **`mesh id status --fabric-root DIR --node-id ID`** — record + pinned-only flag.
2. **`mesh id attest ...`** — verify leaf under local CA; CN/SAN must match; fail-closed; mismatch enters pinned-only.
3. **`mesh id tier ... [--set T{n}] [--pin] [--downgrade]`** — bounds T0..T3; T3 needs `--pin`.
4. **`mesh id rotate ...`** — LocalCA leaf rotate; prior fingerprint retained; **no silent tier downgrade**.
5. **`mesh id revoke ...`** — force T0, record fingerprint, enter pinned-only abort.

## Bounds (NO_HELD)

| Held | Meaning here |
|------|----------------|
| No Raft / N>2 / multi-primary | Identity is local + N≤2 fabric leafs only |
| No silent plaintext | `mode=plaintext` refused (`IDENTITY_PLAINTEXT_FORBIDDEN`) |
| No Vault/ACME required | Local CA only; external PKI remains optional debt |
| No GIA / AGI claims | Substrate identity only |
| No H2..H8 | Deferred per frozen 0.18 scope |
| dual_primary | **Hard 0** on every record / result |

## Exit criteria

- [x] Capability + policy + schema docs
- [x] Library: record, attest, tier, rotate, revoke, pinned-only
- [x] CLI wired
- [x] ≥14 pytest cases (mismatch reject, tier bounds, pinned-only, no plaintext, dual_primary=0, no Vault)
- [x] ver **0.18.0**; CP-0038 sealed
- [x] PREFERRED_NEXT → `0.18_H2_recovery`

## Non-goals

- H2 recovery / H3 fence / H4 OBS / H5 packaging / H6..H8
- Raft, N>2, multi-primary, GIA claims
- Requiring Vault or ACME
- Quiet plaintext fallback or silent identity downgrade

## Related

- `docs/planning/0.18_SCOPE_FROZEN.md` theme H1
- `docs/network_fabric_tls.md`
- `council/DEEPSEEK_REPLY_CYCLE33.md` NEXT=`0.18_H1_identity`
