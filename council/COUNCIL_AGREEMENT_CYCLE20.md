# Council Agreement — Cycle 20 / CP-0024

**Capability:** DeepSeek NEXT  
**Title:** Mesh Packaging: Single-Node Bundle  
**Scope:** `capability_not_tags_not_SLO`  
**Version next:** `0.16.0`  
**Checkpoint next:** `CP-0024`

## Scope and deliverables

- **P0 — Bundle manifest schema:** `name`, `ver`, `tip`, `cp_range`, `pytest`, `entrypoint`, `checksums` (`mesh.bundle.manifest/v1`).
- **P1 —** `scripts/build_bundle.py` producing a reproducible single-node tarball.
- **P2 —** `scripts/verify_bundle.py` checksum + manifest + pytest/import smoke.
- **P3 —** Tests unit+integration golden manifest+bundle roundtrip (`packaging_single_node_bundle` ≥10).
- **P4 —** Docs `docs/capabilities/MESH_PACKAGING_SINGLE_NODE_BUNDLE.md`.

## Acceptance gates

- `packaging_single_node_bundle=10/0` (`PYTEST_MIN`).
- `386+10` tests pass (≥396).
- `AUDIT=PASS`.
- `CP-0024=VERIFIED`.
- Bundle deterministic; verify clean.

## Explicit exclusions and bounds

**NO:** `NO_SLO_CHASE`, `NO_TAG_SCHEMA`, `NO_RAFT`, `NO_N>2`, `NO_ML`, `NO_PLAINTEXT`, `NO_GIA`, `NO_EVERY_fsync`.

**BOUNDS:** `no_consensus_change`, `no_SLO_change`, `no_tag_schema`, `no_Raft`, `no_N>2`, `no_ML`, `no_plaintext`, `no_GIA`, `no_EVERY_fsync`.

This agreement authorizes packaging capability implementation only; it does not authorize tag-schema edits, SLO chase, or consensus changes.
