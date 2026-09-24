# Council Agreement — Cycle 26 / CP-0030

**Capability:** DeepSeek NEXT (Cycle 25 VERDICT)  
**Title:** 0.17 scope freeze; schema-gate resolution; 0.17 bootstrap  
**Scope:** `capability_not_tags_not_SLO` (freeze + resolution + version open; no full theme impl)  
**Version:** package **0.17.0** (bootstrap); release **0.16.3** remains CLOSED/FROZEN  
**Checkpoint:** `CP-0030`

## Semver note

Open the **0.17.x** development line at **0.17.0**. Do **not** reopen 0.16.x packaging RC. Do **not** move/delete tag `v0.16.3`. `RELEASE_VERSION` packaging constant stays **0.16.3** (closed release id).

## Scope and deliverables

- **P24 — 0.17_scope_freeze:** `docs/planning/0.17_SCOPE_FROZEN.md` (status=FROZEN) + `council/SCOPE_0.17_FROZEN.md`; mark `council/PLAN_0.17_DRAFT.md` FROZEN. Ordered themes from Cycle 25 planning only — no invented themes.
- **P25 — schema_gate_resolution:** `docs/debt/SCHEMA_GATE_RESOLUTION_0.17.md` with **resolution=ACCEPT_AND_CARRY**; extend `debt_gate_review` / `debt_gate_status()` (read-only). No EVERY fsync; no tag_schema churn; gate tests remain green.
- **P26 — 0.17_bootstrap:** bump package to **0.17.0**; `docs/planning/0.17_BOOTSTRAP.md`; NEXT_ACTION → first frozen theme (N=2 multi-node packaging) as future work — **not** implemented fully here.

## Acceptance gates

- ≥10 new tests (P24–P26); packaging green; full pytest ≥464+N.
- `AUDIT=PASS` (held).
- `CP-0030=VERIFIED`.
- Frozen scope present; ACCEPT_AND_CARRY in resolution doc + review report; version==0.17.0; `v0.16.3` tag exists; freeze channel docs still say 0.16.x closed for RC.
- dual_primary=0; peers=0.

## Explicit exclusions and bounds

**NO_HELD:** Raft, N>2, multi-primary, ML, R2, R3, plaintext, Vault-ACME-req, GIA, SLO_chase, tag_schema, EVERY_fsync.

**BOUNDS:** `no_consensus_change`, `no_SLO_change`, `no_tag_schema`, `no_Raft`, `no_N>2`, `no_ML`, `no_plaintext`, `no_GIA`, `no_EVERY_fsync`, `no_reopen_0.16.3_RC`, `no_full_theme_impl_in_bootstrap`.

This agreement authorizes scope freeze, schema-gate ACCEPT_AND_CARRY resolution, and 0.17.0 bootstrap only.
