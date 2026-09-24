# Council Agreement — Cycle 27 / CP-0031

**Capability:** DeepSeek NEXT (Cycle 26 VERDICT)  
**Title:** N=2 multi-node packaging design + manifest parity + install/rollback smoke  
**Scope:** N=2 packaging only; no Raft / N>2 / multi-primary  
**Version:** package **0.17.0** (stay; open 0.17.x line)  
**Checkpoint:** `CP-0031`

## Semver note

Stay on **0.17.0**. Prefer 0.17.0 unless forced by conflict. Do **not** reopen 0.16.x packaging RC. Do **not** move/delete tag `v0.16.3`. Single-node `mesh.bundle.manifest/v1` remains FROZEN for closed `0.16.x`.

## Scope and deliverables

- **P27 — N2_multi_node_packaging_design:** `docs/capabilities/MESH_PACKAGING_N2_MULTI_NODE.md` — two-node bundle product; schema `mesh.bundle.manifest/v1-n2` / product `neural-mesh-gia-n2`; topology=n2; roles=[primary,secondary]; majority=fenced_primary_heal **NOT Raft**; dual_primary=0.
- **P28 — N2_manifest_parity:** `manifest_n2` + `bundle_n2`; `build_n2_bundle` / `verify_n2_bundle`; scripts; core parity vs single-node; N2-only extras listed; distinct schema id.
- **P29 — N2_install_rollback_smoke:** dual prefix extract (node-a / node-b); import/mesh help smoke; replica status mock (full serve out-of-band); filesystem rollback of one node.

## Acceptance gates

- ≥12 new tests (`packaging_n2`); packaging green; full pytest ≥477+N.
- `AUDIT=PASS` (held).
- `CP-0031=VERIFIED`.
- dual_primary=0; peers=0.
- Version==0.17.0; `v0.16.3` tag exists untouched.

## Explicit exclusions and bounds

**NO_HELD:** Raft, N>2, multi-primary, ML, R2, R3, plaintext, Vault-ACME-req, GIA, SLO_chase, tag_schema, EVERY_fsync.

**BOUNDS:** `no_consensus_change`, `no_SLO_change`, `no_tag_schema`, `no_Raft`, `no_N>2`, `no_ML`, `no_plaintext`, `no_GIA`, `no_EVERY_fsync`, `no_reopen_0.16.3_RC`, `no_multi_primary`.

This agreement authorizes N=2 packaging (design + manifest parity + install/rollback smoke) only.
