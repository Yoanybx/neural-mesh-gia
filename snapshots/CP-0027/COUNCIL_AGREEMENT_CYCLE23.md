# Council Agreement — Cycle 23 / CP-0027

**Capability:** DeepSeek NEXT (Cycle 22 VERDICT)  
**Title:** RC soak stability; final release audit; post-RC watch  
**Scope:** `capability_not_tags_not_SLO` (single-node RC packaging)  
**Version next:** `0.16.3` (patch — see semver note)  
**Checkpoint next:** `CP-0027`

## Semver note

DeepSeek Cycle 22 VERDICT did **not** give a hard next semver (`VER_NEXT: CYCLE_23_STATUS_AFTER_P15_P17`). Council chose **0.16.3** (patch): final soak/audit/watch on the RC track atop **0.16.2**. No minor bump because `mesh.bundle.manifest/v1` remains frozen/compatible for `0.16.x`.

## Scope and deliverables

- **P15 — rc_soak_stability:** `scripts/rc_soak.py` + `neural_mesh.packaging.rc_soak`; N iterations (default 5) install-or-reuse → status snapshot → verify_bundle → optional clean_node smoke; latency p50/p99; variance bound; JSON soak report.
- **P16 — final_release_audit:** `scripts/final_release_audit.py` + `docs/capabilities/MESH_PACKAGING_FINAL_RELEASE_AUDIT.md`; aggregate release_checklist / repro / freeze / CP tip / version==0.16.3 / packaging tests / dual_primary=0 / NO_HELD; JSON M2M; nonzero exit on fail.
- **P17 — post_rc_watch:** `scripts/post_rc_watch.py` + `docs/capabilities/MESH_PACKAGING_POST_RC_WATCH.md`; watch checklist (freeze, SCHEMA-GATED debt, no tag drift, OBS fields); `--once` JSON report; scheduled routine **document only** (no Grok Bot routines).

## Acceptance gates

- ≥10 new packaging tests (P15–P17); `-k packaging` green.
- Full pytest ≥424+N (expect ≥439).
- `AUDIT=PASS`.
- `CP-0027=VERIFIED`.
- RC soak PASS; final release audit PASS; post-RC watch `--once` PASS.
- Version **0.16.3**; freeze channel `0.16.x` unchanged; peers=0.

## Explicit exclusions and bounds

**NO_HELD:** Raft, N>2, multi-primary, ML, R2, R3, plaintext, Vault-ACME-req, GIA, SLO_chase, tag_schema, EVERY_fsync.

**BOUNDS:** `no_consensus_change`, `no_SLO_change`, `no_tag_schema`, `no_Raft`, `no_N>2`, `no_ML`, `no_plaintext`, `no_GIA`, `no_EVERY_fsync`.

This agreement authorizes single-node RC packaging soak/audit/watch only.
