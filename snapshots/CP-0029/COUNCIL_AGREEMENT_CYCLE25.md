# Council Agreement — Cycle 25 / CP-0029

**Capability:** DeepSeek NEXT (Cycle 24 VERDICT)  
**Title:** Post-release monitor continue; 0.17 scope planning; debt gate review  
**Scope:** `capability_not_tags_not_SLO` (post-release ops + planning only)  
**Version:** `0.16.3` (signed-off — do **not** bump; do **not** ship 0.17.0 code)  
**Checkpoint next:** `CP-0029`

## Semver note

Keep package version at **0.16.3** as the signed-off release. Do **not** reopen 0.16.x packaging RC. P22 is **planning only** for 0.17.x (`next_line=0.17.x` note allowed).

## Scope and deliverables

- **P21 — post_release_monitor_continue:** `scripts/post_release_monitor.py --continue` (+ packaging helper); re-runs --once; appends/rolls `dist/releases/0.16.3/monitor_history.jsonl`; exits 0 if still healthy; fails if signoff/archive missing.
- **P22 — 0.17_scope_planning:** planning docs only — `docs/planning/0.17_SCOPE.md`, `docs/planning/0.17_NON_GOALS.md`, `council/PLAN_0.17_DRAFT.md`. Themes grounded in repo (multi-node packaging beyond single-node N=2 track, fabric ops UX, richer OBS peers, external quickstart). **No 0.17 feature code.**
- **P23 — debt_gate_review:** `scripts/debt_gate_review.py` + `docs/debt/DEBT_GATE_REVIEW_CP0029.md`; confirm CHECKPOINT_EVERY_FLOOR SCHEMA-GATED + schema gate present; report MET/GAP/SCHEMA-GATED for known SLOs without rebenchmarking; JSON M2M; exit 0 if gates consistent.

## Acceptance gates

- ≥8–12 new tests (P21–P23); packaging green; full pytest ≥452+N.
- `AUDIT=PASS` (held).
- `CP-0029=VERIFIED`.
- Monitor `--continue` PASS; debt gate review PASS; planning docs present with NON-GOALS / NO_HELD.
- Version **0.16.3**; freeze channel `0.16.x` unchanged; peers=0.

## Explicit exclusions and bounds

**NO_HELD:** Raft, N>2, multi-primary, ML, R2, R3, plaintext, Vault-ACME-req, GIA, SLO_chase, tag_schema, EVERY_fsync.

**BOUNDS:** `no_consensus_change`, `no_SLO_change`, `no_tag_schema`, `no_Raft`, `no_N>2`, `no_ML`, `no_plaintext`, `no_GIA`, `no_EVERY_fsync`, `no_0.17_feature_impl`.

This agreement authorizes post-release monitor continue, 0.17 planning docs, and debt gate review only.
