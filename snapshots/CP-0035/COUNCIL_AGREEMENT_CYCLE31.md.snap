# Council Agreement — Cycle 31 / CP-0035

**Capability:** DeepSeek NEXT (Cycle 30 VERDICT) — external_quickstart  
**Title:** External quickstart (public 0.16.3 path + 0.17 stub)  
**Scope:** Docs + dry-run helper only; no packaging reopen; no unfinished feature claims  
**Version:** package **0.17.0** (hold)  
**Checkpoint:** `CP-0035`

## Semver note

Hold **0.17.0**. Do **not** reopen 0.16.3 / single-node freeze. Do **not** move/delete tag `v0.16.3`.

## Scope and deliverables

- `QUICKSTART_0.16.3.md` — external single-node install/verify/smoke
- `QUICKSTART_0.17_STUB.md` — shipped themes vs EXPERIMENTAL
- `scripts/quickstart_0.16.3.sh` — dry-run default; `--execute` verify only
- Capability `MESH_EXTERNAL_QUICKSTART`
- ≥10 tests (marker `quickstart_cycle31`)

## Acceptance gates

- quickstart_cycle31 tests green; full pytest green
- `CP-0035=VERIFIED`
- dual_primary=0; no rebuild of 0.16.3
- Version==0.17.0; `v0.16.3` tag untouched
- PREFERRED_NEXT=`0.17_signoff`

## Explicit exclusions and bounds

**NO_HELD:** Raft, N>2, multi-primary, ML, R2, R3, plaintext, Vault-ACME-req, GIA, SLO_chase, tag_schema, EVERY_fsync.

Debt: SCHEMA-GATED ACCEPT_AND_CARRY (unchanged).
