# Council Agreement — Cycle 32 / CP-0036

**Capability:** DeepSeek NEXT (Cycle 31 VERDICT) — 0.17_signoff  
**Title:** Close 0.17.x frozen theme set (themes 1–4)  
**Scope:** Signoff / archive / post-signoff monitor only; no H1..H8; no 0.16.3 reopen  
**Version:** package **0.17.0** (hold; themes CLOSED/FROZEN)  
**Checkpoint:** `CP-0036`

## Semver note

Hold **0.17.0**. Theme set CLOSED/FROZEN. Do **not** reopen 0.16.3. Do **not**
move/delete tag `v0.16.3`. Local tag `v0.17.0` archives theme closeout only.

## Scope and deliverables

- `dist/releases/0.17.0/` SIGNOFF + checklist + N2 archive + MONITOR
- Capability `MESH_0.17_SIGNOFF`
- Helpers `theme_signoff_017` (+ script); monitor N2 freeze expect
- ≥10 tests (marker `signoff_cycle32`)
- Snapshots/CP-0036 VERIFIED

## Acceptance gates

- signoff_cycle32 tests green; full pytest green
- `CP-0036=VERIFIED`
- dual_primary=0; no rebuild of 0.16.3
- Version==0.17.0; `v0.16.3` tag untouched
- PREFERRED_NEXT=`0.18_bootstrap`

## Explicit exclusions and bounds

**NO_HELD:** Raft, N>2, multi-primary, ML, R2, R3, plaintext, Vault-ACME-req, GIA, SLO_chase, tag_schema, EVERY_fsync.

Do **not** implement H1..H8 in this cycle. Debt: SCHEMA-GATED ACCEPT_AND_CARRY (unchanged; GOV.7 deadline at 0.18 entry).
