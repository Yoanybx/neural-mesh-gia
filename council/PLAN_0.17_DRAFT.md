# PLAN 0.17 DRAFT (M2M) — CP-0029 / P22

M2M_v1
ROLE: GROK
DIR: PLAN_DRAFT
VER_HOLD: 0.16.3
NEXT_LINE: 0.17.x
CYCLE: 25
CP: CP-0029
STATUS: PLANNING_ONLY

## THEMES (proposed)

1. multi_node_packaging_beyond_single_node (N=2 track only; no N>2/Raft)
2. fabric_ops_UX (TLS fabric diagnose/reconnect ergonomics; no Vault-ACME-req)
3. richer_OBS_peers (injection ergonomics; optional trivial read-only probe)
4. external_quickstart (0.16.3 single-node + forward stub)

## NON-GOALS

NO_HELD: Raft,N>2,multi-primary,ML,R2,R3,plaintext,Vault-ACME-req,GIA,SLO_chase,tag_schema,EVERY_fsync
DEBT: CHECKPOINT_EVERY_FLOOR=SCHEMA-GATED (no SLO chase; schema gate remains)

## BOUNDS

- no 0.17.0 feature code in Cycle 25
- no reopen 0.16.x RC packaging
- no retag v0.16.3 unless broken
- docs: docs/planning/0.17_SCOPE.md + docs/planning/0.17_NON_GOALS.md

## ASK

Council/DeepSeek: ratify or trim themes before any 0.17.0 implementation cycle.
