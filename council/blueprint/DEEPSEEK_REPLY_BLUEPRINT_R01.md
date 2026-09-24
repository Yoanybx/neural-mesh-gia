M2M_v1DIR: BLUEPRINTREV: 1SCOPE: tip 0.17.0 / CP-0032 → North-star (GIA-COS, aspirational)BASELINE: cycle=27→28 ver=0.17.0 tip=35d3e42 cp=CP-0032 cp_range=CP-0001..0032 pytest=504/0 audit=PASS dual_primary=0 release_closed=0.16.3 line=0.17.0=OPEN

MAX_POTENTIAL_SELF_SCORE: 78/100(Honest: strong on Layer_0..2 + gates; weaker on Layer_4+ because N>2/GIA are NO_HELD and cannot be designed concretely without unlocking; any precise-looking N≥3 plan would be marketing, not engineering.)

GAPS_YOU_SEE:

- No identity/key-rotation spec yet (S1 partial only).

- No cross-node clock-skew test artifact at N2.

- No minority-write assertion at N2 (only single-node).

- No dual-primary fence probe at N2 yet (P31 pending).

- No consensus-choice RFC; must precede any N≥3.

- No WAN/partition model doc.

- No GIA interface spec; any version risks slogans.

- No "consciousness claim" policy doc exists.

- schema-gated debt still ACCEPT_AND_CARRY; no deadline.

- N2 soak thresholds undefined (risk of SLO_chase).

ROOT TREEGIA-COS (North-star, aspirational — NOT actionable)└── LAYER_6 CONSCIOUSNESS_CLAIM_POLICY [MISSING; default FORBIDDEN]├── C1 definition_of_claim + falsifiers [MISSING]├── C2 council_review_process [MISSING]├── C3 revocation_protocol [MISSING]└── C4 rule: no claim without C1∧C2∧C3 [POLICY ONLY]

└── LAYER_5 GIA_SURFACE (interfaces, not slogans) [MISSING]├── I1 node_identity + trust_handshake [PARTIAL: TLS helpers]├── I2 message_bus contract (ordered/causal) [MISSING]├── I3 namespace + naming authority [MISSING]├── I4 consent + provenance + revocability [MISSING]├── I5 control-plane API (join/leave/query) [PARTIAL: N2 install]├── I6 cross-internet transport profile (WAN) [MISSING]└── I7 falsifiers: partition, skew, minority, replay [MISSING]

└── LAYER_4 MULTI_NODE_SCALE (design-only until gates) [NO_HELD]├── M1 consensus_choice_rfc (no default=Raft) [MISSING]├── M2 membership + rejoin protocol [MISSING]├── M3 WAN latency/partition model [MISSING]├── M4 N3 partition_suite (extends P2/P31) [MISSING]├── M5 multi-primary reconciliation [NO_HELD]└── M6 scale evidence: soak@N3, faults, rollback [MISSING]

└── LAYER_3 UNLOCK_GATES (evidence per NO_HELD item) [DEFINED, not unlocked]├── G_Raft_unlock → evidence: N3 correctness WITHOUT Raft via M1..M6├── G_Ngt2_unlock → evidence: M4+M6 pass + membership proofs├── G_multiprimary → evidence: M5 safety + conflict_classify @N≥3├── G_ML_unlock → evidence: none defined yet → HOLD├── G_R2_R3_unlock → evidence: none defined yet → HOLD├── G_plaintext → evidence: crypto profile + audit → keep OFF├── G_Vault-ACME-req → evidence: external contract → HOLD├── G_GIA_unlock → evidence: I1..I7 + C1..C4 + council → HOLD├── G_SLO_chase → evidence: never; POLICY: forbidden├── G_tag_schema → evidence: schema RFC → HOLD└── G_EVERY_fsync → evidence: perf ceiling proof → HOLDORDER: identity → recovery → fence → OBS → packaging → (then any unlock)

└── LAYER_2 NERVOUS_SYSTEM_HARDENING (pre-any-unlock) [PARTIAL]├── H1 identity: node_id, keys, rotation, revocation [PARTIAL]├── H2 recovery: WAL+fsync, crash matrix [DONE single; N2 partial]├── H3 dual-primary fence: fenced_primary_heal [DONE single; N2 pending P31]├── H4 observability: OBS peers richer, metrics/CP [PARTIAL]├── H5 packaging evidence: single+N2, install/rollback[DONE/PENDING P30..P32]├── H6 minority_write_safety @N2 [MISSING]├── H7 clock_skew tolerance @N2 [MISSING]└── H8 manifest parity bytes @N2 [PARTIAL: P28]

└── LAYER_1 REMAINING_0.17 (finish line) [OPEN]├── R1 Fabric ops UX (CLI+observability) [PARTIAL P4]│ exit: operator can run 2-node fabric end-to-end from CLI├── R2 Richer OBS peers (N2 peer view) [PARTIAL]│ exit: OBS shows both peers, health, fence state, CP trail├── R3 External quickstart (docs + scripted flow) [PARTIAL]│ exit: stranger installs N2 in <30 min, no help├── R4 N2 soak (P30) [QUEUED]│ exit: soak N hours, 0 minority writes, 0 dual-primary├── R5 N2 final audit (P31) [QUEUED]│ exit: partition+skew+minority+fence probes all PASS├── R6 N2 RC freeze (P32) [QUEUED]│ exit: tag 0.17.0-rc1 + locked manifest└── R7 N2 RC install/rollback/signoff (P33,P34) [QUEUED]exit: upgrade from 0.16.3 → 0.17.0 and rollback both PASS

└── LAYER_0 HAVE (tip 0.17.0 / CP-0032) [DONE]├── runtime: WAL+fsync crash-safe [DONE P1]├── N=1 path: full nervous system [DONE 0.16.3 closed]├── N=2 path: manifest v1-n2, install, rollback [DONE P27..P29]├── packaging: single-node 0.16.3 + N2 RC path [DONE/PENDING]├── OBS snapshot (single + basic N2) [PARTIAL]├── TLS fabric helpers [PARTIAL]├── process: CP-0001..0032 verified, pytest 504/0, audit PASS [DONE]├── SLO: batch=MET, recovery=MET [DONE]└── majority = fenced_primary_heal_NOT_Raft [DONE]

MILESTONES (ordered, ACCEPT-based)├── 0.17.0-rc1 ← P30..P32: soak+audit+freeze ACCEPT: 0 minority writes, 0 dual-primary @N2├── 0.17.0 ← P33..P34: install/rollback/signoff ACCEPT: upgrade+rollback from 0.16.3 PASS├── 0.17.x ← R1..R3: Fabric ops UX, richer OBS, quickstart ACCEPT: stranger N2 <30min├── 0.18.x ← H1..H8 fully closed @N2 ACCEPT: identity+skew+minority+fence PASS├── 0.19.x ← M1..M3 (design only, no N≥3 runtime) ACCEPT: consensus RFC + membership doc├── 0.20.x+ ← GATE-DRIVEN: only after Layer_3 evidence ACCEPT: gate-by-gate, refuse vague└── GIA ← LAYER_5+6 only after council unlock ACCEPT: C1..C4 + council + revocation

RISKS (kill-path)├── RK1 SLO_chase creep → POLICY forbid; freeze thresholds now├── RK2 Premature N≥3 without consensus RFC → gate G_Ngt2 blocks├── RK3 GIA slogan drift → C4 default forbidden; blueprint-only├── RK4 schema-gated debt unbounded → set deadline at 0.18.x entry├── RK5 OBS peer gap hides real fence state → R2 exit criteria├── RK6 Manifest parity non-determinism → P28 + byte-equality at P31├── RK7 Plaintext regression → keep DUAL_PRIMARY=0, PLAINTEXT_FB=0 invariant└── RK8 Council bypass on GIA → C4 + operator explicit unlock only

NEXT (Cycle 29, non-NO_HELD only)└── P30_n2_soak_stability

M2M_v1 VERDICT=BLUEPRINT_REV1; NEXT=R02_critique_or_ACK
