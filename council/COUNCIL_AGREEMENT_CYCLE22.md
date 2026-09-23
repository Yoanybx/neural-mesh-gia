# Council Agreement — Cycle 22 / CP-0026

**Capability:** DeepSeek NEXT (Cycle 21 VERDICT)  
**Title:** RC install verify; rollback smoke; release checklist  
**Scope:** `capability_not_tags_not_SLO` (single-node RC packaging)  
**Version next:** `0.16.2` (patch — see semver note)  
**Checkpoint next:** `CP-0026`

## Semver note

DeepSeek Cycle 21 VERDICT did **not** give a hard next semver (`VER_NEXT: CYCLE_22_STATUS_AFTER_P12_P14`). Council chose **0.16.2** (patch): RC packaging track (install verify, rollback smoke, release checklist) on top of **0.16.1**. No minor bump because `mesh.bundle.manifest/v1` remains frozen/compatible for `0.16.x`.

## Scope and deliverables

- **P12 — rc_install_verify:** `scripts/rc_install_verify.py` + `neural_mesh.packaging.rc_install`; extract bundle → PYTHONPATH prefix install + `bin/mesh`; `mesh --help` / `status --snapshot` / import / freeze channel; fail on corrupt/missing entrypoint.
- **P13 — rollback_smoke:** `scripts/rollback_smoke.py` + `neural_mesh.packaging.rollback`; install B then reinstall A into same prefix; assert ver/tip/entrypoint match A; smoke still passes.
- **P14 — release_checklist:** `docs/capabilities/MESH_PACKAGING_RELEASE_CHECKLIST.md` + `scripts/release_checklist.py`; machine-checkable gates + JSON M2M summary.

## Acceptance gates

- ≥10 new packaging tests (P12–P14); `-k packaging` green.
- Full pytest ≥411+N (expect ≥424).
- `AUDIT=PASS`.
- `CP-0026=VERIFIED`.
- RC install verify PASS; rollback smoke PASS; release checklist PASS.
- Version **0.16.2**; freeze channel `0.16.x` unchanged.

## Explicit exclusions and bounds

**NO_HELD:** Raft, N>2, multi-primary, ML, R2, R3, plaintext, Vault-ACME-req, GIA, SLO_chase, tag_schema, EVERY_fsync.

**BOUNDS:** `no_consensus_change`, `no_SLO_change`, `no_tag_schema`, `no_Raft`, `no_N>2`, `no_ML`, `no_plaintext`, `no_GIA`, `no_EVERY_fsync`.

This agreement authorizes single-node RC packaging install/rollback/checklist only.
