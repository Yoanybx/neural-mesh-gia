# Dead-man Switch Policy v1 (I5.d)

**Status:** POLICY STUB (Cycle 65 / CP-0069) — design alignment only  
**Design:** `docs/design/ORCHESTRATOR_OVERSIGHT_HOOKS_DESIGN.md`  
**Blueprint:** L5 I5.d + P-11 (`T_dead` default = 24h; override logged)  
**Non-goals:** live kill channel; wall-clock-as-authority; GIA unlock

## Defaults

| Parameter | Value | Notes |
|-----------|-------|-------|
| `T_dead` | 86400 mock units (≈24h logical) | P-11 default |
| Override | allowed | **must** append ledger `deadman_override` |
| On expiry | auto-DRAIN + continuity BLOCKED | `OVS_DEADMAN_EXPIRED` |
| A4 gate | fresh `deadman_ok` required | else `OVS_DEADMAN_REQUIRED` / `ROUTE_DEADMAN_REQUIRED` |

## Rules

1. Dead-man applies to **A4** irreversible actions (and optional operator-wide watch).
2. `deadman_refresh` by a named human seat resets the window.
3. Expiry does **not** silent-ALLOW; fail-closed DRAIN/BLOCKED.
4. HLC / logical counters are Mesh authority; wall clock is not (H7).
5. live=DISABLED remains; expiry never opens a live path.

## Tests

- T-I5c / **T-ovs-c** (neg): expire → DRAIN; missing refresh on A4 → ABORT.

**NO_HELD:** Raft,N>2,multi-primary,ML,R2,R3,plaintext,Vault-ACME-req,GIA,SLO_chase,tag_schema,EVERY_fsync
