# SCOPE 0.18 FROZEN (M2M) — CP-0037 / Cycle 33

M2M_v1
ROLE: GROK
DIR: SCOPE_FROZEN
VER_PACKAGE: 0.18.0
VER_RELEASE_CLOSED: 0.17.0_themes+0.16.3
NEXT_LINE: 0.18.x
CYCLE: 33
CP: CP-0037
STATUS: FROZEN

## THEMES (ordered, frozen) — L2 NERVOUS_HARDENING

1. H1_identity+attestation+tiers (ABORT→pinned-only)
2. H2_recovery+rebuild (ABORT→snapshot restore)
3. H3_dual-primary_fence@N2 (ABORT→demote+re-elect; dual_primary=0)
4. H4_OBS_telemetry (schema/obs track)
5. H5_packaging_distribution
6. H6_minority_write@N2 (ABORT→halt writes)
7. H7_clock_skew@N2 (ABORT→refuse join)
8. H8_manifest_parity@N2 (ABORT→reject build)

## NON-GOALS

NO_HELD: Raft,N>2,multi-primary,ML,R2,R3,plaintext,Vault-ACME-req,GIA,SLO_chase,tag_schema,EVERY_fsync
DEBT: CHECKPOINT_EVERY_FLOOR=SCHEMA-GATED; GOV.7 entry=WAIVE_VIA_ACCEPT_AND_CARRY (docs/debt/SCHEMA_GATE_0.18_ENTRY.md)
PRIOR: SCHEMA_GATE_RESOLUTION_0.17.md ACCEPT_AND_CARRY

## BOUNDS

- no Raft / N>2 / multi-primary / ML / plaintext / GIA
- no SLO chase / EVERY_fsync / tag_schema churn
- no reopen 0.16.3 / 0.17.0 archives; v0.17.0 + v0.16.3 tags untouched
- CP-0037 bootstrap only — H1 deferred to 0.18_H1_identity

## DOCS

- docs/planning/0.18_SCOPE_FROZEN.md
- docs/planning/0.18_BOOTSTRAP.md
- docs/planning/0.18_NON_GOALS.md
- docs/debt/SCHEMA_GATE_0.18_ENTRY.md
- docs/debt/SCHEMA_GATE_RESOLUTION_0.17.md
