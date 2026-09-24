# Quickstart Stub — Neural Mesh 0.17.x (development line)

**Status:** STUB — forward-looking pointer only  
**Package line:** **0.17.0** (open for development; **not** a signed-off external release)  
**Single-node release path:** use `docs/quickstart/QUICKSTART_0.16.3.md`  
**Capability:** `MESH_EXTERNAL_QUICKSTART` (Cycle 31 / CP-0035)  
**Scope source:** `docs/planning/0.17_SCOPE_FROZEN.md`

## Purpose

Point operators and council at **what 0.17 actually shipped** under the frozen
themes, without claiming unfinished features as done, and without reopening the
closed **0.16.3** single-node packaging channel.

This stub is **not** an install guide for a 0.17 release tarball. Prefer the
signed-off **0.16.3** external quickstart for production-shaped single-node use.

## What 0.17 shipped (themes 1–4)

| # | Theme | Capability / evidence | Operator surface |
|---|-------|----------------------|------------------|
| 1 | N=2 multi-node packaging | `MESH_PACKAGING_N2_MULTI_NODE` (CP-0031..0032) | Optional N=2 bundle schema `mesh.bundle.manifest/v1-n2`; freeze channel `0.17.x-n2` |
| 2 | Fabric ops UX | `MESH_FABRIC_OPS_UX` (CP-0033) | `mesh fabric status \| diagnose \| reconnect` (TLS fail-closed) |
| 3 | Richer OBS peers | `MESH_OBS_PEERS` (CP-0034) | `mesh status --snapshot` peer inject / optional RO probe ≤2 |
| 4 | External quickstart | `MESH_EXTERNAL_QUICKSTART` (CP-0035) | This stub + public 0.16.3 quickstart |

Bootstrap / freeze docs (not feature claims):

- `docs/planning/0.17_SCOPE_FROZEN.md`
- `docs/planning/0.17_BOOTSTRAP.md`
- `docs/planning/0.17_NON_GOALS.md`

## Still EXPERIMENTAL / not an external release claim

Treat the following as **in-tree / RC-adjacent development**, not as a second
signed-off external product:

- N=2 multi-node packaging artifacts under the `0.17.x-n2` freeze (optional;
  dual_primary must remain **0**; majority = fenced primary / heal — **NOT Raft**)
- Fabric ops UX and OBS peer probe helpers (operator ergonomics on existing TLS)
- Package version **0.17.0** held on the development line until council **0.17
  signoff**

**Do not** tell external users that “0.17 is released” until signoff seals that
window. Until then, the external single-node path remains **0.16.3**.

## Explicit non-claims (NO_HELD)

This stub does **not** claim any of the following as shipped or available:

- Raft / quorum consensus
- N>2 topology
- Multi-primary / dual_primary ≠ 0
- GIA / AGI runtime
- Silent plaintext transport fallback
- Vault or ACME as a hard requirement
- SLO chase / tag_schema expansion / EVERY_fsync optimization
- ML / R2 / R3 cognitive-router expansions

**NO_HELD:** Raft,N>2,multi-primary,ML,R2,R3,plaintext,Vault-ACME-req,GIA,SLO_chase,tag_schema,EVERY_fsync

## Where to go next

1. **External single-node install:** `docs/quickstart/QUICKSTART_0.16.3.md`
2. **Capability index for shipped 0.17 themes:**  
   - `docs/capabilities/MESH_PACKAGING_N2_MULTI_NODE.md`  
   - `docs/capabilities/MESH_FABRIC_OPS_UX.md`  
   - `docs/capabilities/MESH_OBS_PEERS.md`  
   - `docs/capabilities/MESH_EXTERNAL_QUICKSTART.md`
3. **Council next (after CP-0035):** `0.17_signoff` → then 0.18.x H1..H8

## Related

- Closed release archive: `dist/releases/0.16.3/`
- Debt carry: `docs/debt/CHECKPOINT_EVERY_FLOOR.md` (SCHEMA-GATED ACCEPT_AND_CARRY)
