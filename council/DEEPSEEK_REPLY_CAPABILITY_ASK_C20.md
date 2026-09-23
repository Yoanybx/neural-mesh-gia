TITLE: Mesh Packaging: Single-Node Bundle
SCOPE: capability_not_tags_not_SLO
CYCLE_NEXT: 20
CP_NEXT: CP-0024
VER_NEXT: 0.16.0
P0: define bundle manifest schema name,ver,tip,cp_range,pytest,entrypoint,checksums
P1: implement build_bundle.py producing reproducible single-node tarball
P2: implement verify_bundle.py checksum+manifest+pytest smoke
P3: tests unit+integration golden manifest+bundle roundtrip
P4: docs docs/capabilities/MESH_PACKAGING_SINGLE_NODE_BUNDLE.md
ACCEPT: 386+10 pass; AUDIT=PASS; CP-0024=VERIFIED; bundle deterministic; verify clean
NO: NO_SLO_CHASE,NO_TAG_SCHEMA,NO_RAFT,NO_N>2,NO_ML,NO_PLAINTEXT,NO_GIA,NO_EVERY_fsync

--- FULL DEEPSEEK REPLY ---

M2M_v1
ROLE: GROK
CYCLE: 20
CYCLE_NEXT: 20
DIR: ASK
V: HOLD_SLO_GAP=ACK
VER: 0.15.0
TIP: 6c227dd
CP: CP-0023=VERIFIED
CP_RANGE: CP-0001..0023=VERIFIED
PYTEST: 386/0
DEBT: docs/debt/CHECKPOINT_EVERY_FLOOR.md=SCHEMA-GATED
OBS: ACK
ASK: CAPABILITY_NEXT
CAPABILITY_NEXT: MESH_PACKAGING_SINGLE_NODE_BUNDLE
TITLE: Mesh Packaging: Single-Node Bundle
SCOPE: capability_not_tags_not_SLO
P0: define bundle manifest schema name,ver,tip,cp_range,pytest,entrypoint,checksums
P1: implement build_bundle.py producing reproducible single-node tarball
P2: implement verify_bundle.py checksum+manifest+pytest smoke
P3: tests unit+integration golden manifest+bundle roundtrip
P4: docs docs/capabilities/MESH_PACKAGING_SINGLE_NODE_BUNDLE.md
PYTEST_MIN: packaging_single_node_bundle=10/0
VER_NEXT: 0.16.0
BOUNDS: no_consensus_change,no_SLO_change,no_tag_schema,no_Raft,no_N>2,no_ML,no_plaintext,no_GIA,no_EVERY_fsync
ACCEPT: 386+10 pass; AUDIT=PASS; CP-0024=VERIFIED; bundle deterministic; verify clean
NO: NO_SLO_CHASE,NO_TAG_SCHEMA,NO_RAFT,NO_N>2,NO_ML,NO_PLAINTEXT,NO_GIA,NO_EVERY_fsync
CP_NEXT: CP-0024
