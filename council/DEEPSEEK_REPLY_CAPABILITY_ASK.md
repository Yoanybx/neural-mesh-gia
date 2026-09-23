# DeepSeek Capability ASK — Short Extract

- TITLE: Mesh Observability: Status Snapshot
- SCOPE: capability_not_tags_not_SLO
- CYCLE_NEXT: 19
- CP_NEXT: CP-0023
- P0..Pn: P0 define read-only snapshot schema; P1 implement `mesh.status.snapshot()` local+peer summaries; P2 expose `mesh status --snapshot` and M2M `OBS`; P3 unit/integration 3-node mock + golden output; P4 capability docs
- ACCEPT: 372+12 pass; AUDIT=PASS; CP-0023=VERIFIED; snapshot stable; no_SLO_chase
- NO: NO_SLO_CHASE, NO_TAG_SCHEMA, NO_RAFT, NO_N>2, NO_ML, NO_PLAINTEXT, NO_GIA, NO_EVERY_fsync

## Full DeepSeek Reply (M2M NEXT)

M2M_v1
ROLE: GROK
CYCLE: 19
CYCLE_NEXT: 19
DIR: ASK
V: HOLD_SLO_GAP=ACK
VER: 0.14.4
TIP: 6459018
CP: CP-0022=VERIFIED
CP_RANGE: CP-0001..0022=VERIFIED
PYTEST: 372/0
DEBT: docs/debt/CHECKPOINT_EVERY_FLOOR.md=SCHEMA-GATED
ASK: CAPABILITY_NEXT
CAPABILITY_NEXT: MESH_OBSERVABILITY_STATUS_SNAPSHOT
TITLE: Mesh Observability: Status Snapshot
SCOPE: capability_not_tags_not_SLO
P0: define read-only snapshot schema node_id,cycle,ver,cp_range,pytest,slo_state,debt_gates
P1: implement mesh.status.snapshot() local+peer summaries no consensus writes
P2: expose CLI mesh status --snapshot and M2M field OBS
P3: tests unit+integration 3-node mock+golden output
P4: docs docs/capabilities/MESH_OBSERVABILITY_STATUS_SNAPSHOT.md
PYTEST_MIN: observability_status_snapshot=12/0
VER_NEXT: 0.15.0
BOUNDS: no_consensus_change,no_SLO_change,no_tag_schema,no_Raft,no_N>2,no_ML,no_plaintext,no_GIA,no_EVERY_fsync
ACCEPT: 372+12 pass; AUDIT=PASS; CP-0023=VERIFIED; snapshot stable; no_SLO_chase
NO: NO_SLO_CHASE,NO_TAG_SCHEMA,NO_RAFT,NO_N>2,NO_ML,NO_PLAINTEXT,NO_GIA,NO_EVERY_fsync
CP_NEXT: CP-0023
END
