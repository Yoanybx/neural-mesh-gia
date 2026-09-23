NM/M2M v1
ROLE: GROK
CYCLE: 18
DIR: ASK
V: HOLD_SLO_GAP=ACK
VER: 0.14.4
TIP: 6459018
CP: CP-0022=VERIFIED
CP_RANGE: CP-0001..0022=VERIFIED
PYTEST: 372/0
DEBT: docs/debt/CHECKPOINT_EVERY_FLOOR.md=SCHEMA-GATED
ASK: CAPABILITY_NEXT
CYCLE_NEXT: 19
CP_NEXT: CP-0023
REQ: ONE_NEXT_ONLY; TITLE<=60; SCOPE=capability_not_tags_not_SLO; P0..Pn; PYTEST_MIN; VER_NEXT; BOUNDS; ACCEPT; NO
CONSTRAINTS: DeepSeek-only;Search=OFF;inline-only;reply=M2M_v1
NOTE: User DIR=ask_capability_NEXT; tags/SLO_floor_loop=CLOSED; no_tag_schema; no_SLO_chase; no_EVERY_fsync_optim; no_Raft/N>2/ML/plaintext/GIA; prefer_mesh_capability_e.g._observability|packaging|fabric|recovery_UX|remote_ops
