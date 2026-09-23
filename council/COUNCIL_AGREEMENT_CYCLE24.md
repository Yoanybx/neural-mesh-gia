# Council Agreement — Cycle 24 / CP-0028

**Capability:** DeepSeek NEXT (Cycle 23 VERDICT)  
**Title:** Release signoff; release tag archive; post-release monitor  
**Scope:** `capability_not_tags_not_SLO` (single-node RC packaging)  
**Version:** `0.16.3` (signed-off release — do **not** bump; Cycle 24 = release closeout of 0.16.3)  
**Checkpoint next:** `CP-0028`

## Semver note

Keep package version at **0.16.3** as the signed-off release. Do **not** bump to 0.16.4 unless a conflict forces it. Cycle 24 is the release closeout of 0.16.3 (P18–P20).

## Scope and deliverables

- **P18 — release_signoff:** `scripts/release_signoff.py` + `neural_mesh.packaging.release_signoff`; requires final_release_audit PASS (or re-run), freeze 0.16.x, CP-0027 verified (seals CP-0028), packaging pytest green (injectable); writes `dist/releases/0.16.3/SIGNOFF.json` (+ `.project_state/RELEASE_SIGNOFF_0.16.3.json`); signer=`council:DeepSeek+Grok`; docs `MESH_PACKAGING_RELEASE_SIGNOFF.md`.
- **P19 — release_tag_archive:** `scripts/release_tag_archive.py` + `neural_mesh.packaging.release_tag_archive`; local annotated tag `v0.16.3` (or `release-0.16.3`) via one-shot `-c user.name/email` only; never edit git config; never push; archive under `dist/releases/0.16.3/` (bundle + manifest + SIGNOFF + SHA256SUMS + audit copy + release tar).
- **P20 — post_release_monitor:** `scripts/post_release_monitor.py` + `MESH_PACKAGING_POST_RELEASE_MONITOR.md`; `--once` checks (signoff, tag/marker, freeze, SCHEMA-GATED debt, OBS fields, no forbidden drift); writes `MONITOR.json`; schedule stub only (no Grok Bot routines).

## Acceptance gates

- ≥10 new packaging tests (P18–P20); `-k packaging` green.
- Full pytest ≥439+N.
- `AUDIT=PASS`.
- `CP-0028=VERIFIED`.
- Signoff PASS; tag/archive PASS; post-release monitor `--once` PASS.
- Version **0.16.3**; freeze channel `0.16.x` unchanged; peers=0.

## Explicit exclusions and bounds

**NO_HELD:** Raft, N>2, multi-primary, ML, R2, R3, plaintext, Vault-ACME-req, GIA, SLO_chase, tag_schema, EVERY_fsync.

**BOUNDS:** `no_consensus_change`, `no_SLO_change`, `no_tag_schema`, `no_Raft`, `no_N>2`, `no_ML`, `no_plaintext`, `no_GIA`, `no_EVERY_fsync`.

This agreement authorizes single-node RC release signoff/archive/monitor only.
