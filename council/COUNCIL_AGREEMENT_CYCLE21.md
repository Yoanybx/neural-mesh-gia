# Council Agreement — Cycle 21 / CP-0025

**Capability:** DeepSeek NEXT (Cycle 20 VERDICT)  
**Title:** Clean-node bundle smoke; manifest reproducibility; RC freeze  
**Scope:** `capability_not_tags_not_SLO` (single-node packaging harden)  
**Version next:** `0.16.1` (patch — see semver note)  
**Checkpoint next:** `CP-0025`

## Semver note

DeepSeek Cycle 20 VERDICT did **not** give a hard next semver. Council chose **0.16.1** (patch): packaging RC hardening on top of **0.16.0** (clean-node smoke, manifest repro, RC freeze). No minor bump because `mesh.bundle.manifest/v1` remains compatible (additive `freeze` only).

## Scope and deliverables

- **P9 — clean_node_bundle_smoke:** `scripts/clean_node_smoke.py` + `neural_mesh.packaging.clean_node_smoke`; extract to empty temp; isolated import; `mesh status --snapshot` equivalent; isolation assertions.
- **P10 — manifest_repro:** strengthen determinism (name-based modes, no `os.access`); `scripts/repro_check.py` + `build_bundle --repro-check`; hash-lock tests.
- **P11 — rc_freeze:** freeze `mesh.bundle.manifest/v1` for `0.16.x`; embed `freeze: {channel, schema}`; docs RC freeze section; version **0.16.1**.

## Acceptance gates

- ≥8 new packaging tests (P9–P11); `-k packaging` green.
- Full pytest ≥398+N (expect ≥411).
- `AUDIT=PASS`.
- `CP-0025=VERIFIED`.
- Clean-node smoke PASS; repro PASS; freeze embedded.

## Explicit exclusions and bounds

**NO_HELD:** Raft, N>2, multi-primary, ML, R2, R3, plaintext, Vault-ACME-req, GIA, SLO_chase, tag_schema, EVERY_fsync.

**BOUNDS:** `no_consensus_change`, `no_SLO_change`, `no_tag_schema`, `no_Raft`, `no_N>2`, `no_ML`, `no_plaintext`, `no_GIA`, `no_EVERY_fsync`.

This agreement authorizes packaging RC hardening only.
