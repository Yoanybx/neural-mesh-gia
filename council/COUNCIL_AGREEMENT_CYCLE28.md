# Council Agreement — Cycle 28 / CP-0032

**Capability:** DeepSeek NEXT (Cycle 27 VERDICT)  
**Title:** N2 multi-node packaging RC hardening (soak / final audit / freeze)  
**Scope:** N2 packaging RC only; majority=fenced_primary_heal NOT Raft  
**Version:** package **0.17.0** (hold)  
**Checkpoint:** `CP-0032`

## Semver note

Hold **0.17.0**. Do **not** reopen 0.16.3 / single-node freeze. Do **not** move/delete tag `v0.16.3`.

## Scope and deliverables

- **P30 — N2_soak_stability:** `scripts/n2_rc_soak.py` + `n2_rc_soak` helper; N iterations (default 5) of N2 install smoke on node-a/node-b; JSON report with p50/p99; fail on iteration failure / high variance.
- **P31 — N2_final_release_audit:** `scripts/n2_final_release_audit.py` + `docs/capabilities/MESH_PACKAGING_N2_FINAL_RELEASE_AUDIT.md`; aggregate N2 verify, soak PASS (injectable), dual_primary=0, schema v1-n2, freeze, packaging_n2 tests (injectable), NO_HELD; JSON for M2M.
- **P32 — N2_rc_freeze:** embed `freeze: {channel:"0.17.x-n2", schema:"mesh.bundle.manifest/v1-n2"}` always in `build_n2_bundle`; verify rejects wrong/missing channel when expected; document schema **FROZEN** for N2 RC. Do not alter 0.16.3 single-node freeze.

## Acceptance gates

- ≥10–12 new tests (`packaging_n2` / `packaging_n2_cycle28`); full pytest green (491+N).
- `AUDIT=PASS` (held).
- `CP-0032=VERIFIED`.
- dual_primary=0; majority=fenced_primary_heal.
- Version==0.17.0; `v0.16.3` tag exists untouched.

## Explicit exclusions and bounds

**NO_HELD:** Raft, N>2, multi-primary, ML, R2, R3, plaintext, Vault-ACME-req, GIA, SLO_chase, tag_schema, EVERY_fsync.

**BOUNDS:** `no_consensus_change`, `no_SLO_change`, `no_tag_schema`, `no_Raft`, `no_N>2`, `no_ML`, `no_plaintext`, `no_GIA`, `no_EVERY_fsync`, `no_reopen_0.16.3_RC`, `no_multi_primary`.

Debt: SCHEMA-GATED ACCEPT_AND_CARRY (unchanged).
