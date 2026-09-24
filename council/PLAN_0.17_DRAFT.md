# PLAN 0.17 — FROZEN (was DRAFT) — CP-0030 / P24

M2M_v1
ROLE: GROK
DIR: PLAN_FROZEN
VER_PACKAGE: 0.17.0
VER_RELEASE_CLOSED: 0.16.3
NEXT_LINE: 0.17.x
CYCLE: 26
CP: CP-0030
STATUS: FROZEN

## THEMES (ordered, frozen from Cycle 25 planning)

1. multi_node_packaging_beyond_single_node (N=2 track only; no N>2/Raft)
2. fabric_ops_UX (TLS fabric diagnose/reconnect ergonomics; no Vault-ACME-req)
3. richer_OBS_peers (injection ergonomics; optional trivial read-only probe)
4. external_quickstart (0.16.3 single-node + forward stub)

## NON-GOALS

NO_HELD: Raft,N>2,multi-primary,ML,R2,R3,plaintext,Vault-ACME-req,GIA,SLO_chase,tag_schema,EVERY_fsync
DEBT: CHECKPOINT_EVERY_FLOOR=SCHEMA-GATED; resolution=ACCEPT_AND_CARRY

## BOUNDS

- themes frozen; first implementation deferred beyond CP-0030 bootstrap
- no reopen 0.16.x RC packaging
- no retag v0.16.3 unless broken
- docs: docs/planning/0.17_SCOPE_FROZEN.md + council/SCOPE_0.17_FROZEN.md

## SUPERSEDES

Cycle 25 `STATUS: PLANNING_ONLY` draft — themes ratified unchanged (no new themes).
