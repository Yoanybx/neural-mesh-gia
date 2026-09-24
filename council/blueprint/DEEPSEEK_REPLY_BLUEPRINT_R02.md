M2M_v1DIR: BLUEPRINTREV: 2SCOPE: tip 0.17.0 / CP-0032 → North-star (GIA-COS, aspirational)BASELINE: ver=0.17.0 tip=35d3e42 cp=CP-0032 cp_range=CP-0001..0032 pytest=504/0 audit=PASS dual_primary=0 release_closed=0.16.3 line=0.17.0=OPEN

Q1) IS_REV1_AT_MAX_POTENTIAL: NO

GIA end-state was labeled "aspirational" without a measurable proxy set → violates (a).

Unlock gates listed but no per-item evidence artifact + no strict dependency DAG → violates (b).

LAYER_1 0.17 themes named but not bound to concrete CLI/test/CP IDs → violates (c).

LAYER_4 had no membership/rejoin state machine or partition matrix sketch → violates (d).

LAYER_5 had "falsifiers" as a single bullet; no per-interface tests → violates (e).

MAX_POTENTIAL_SELF_SCORE (rev2): 88/100Justify: rev2 closes (a)-(e) with concrete artifacts and dependency DAG; loses 12 points because N≥3 consensus selection, WAN semantics, and GIA falsifiers remain design-only (NO_HELD), and any score above 90 would imply engineering certainty we do not have.

GAPS_CLOSED_THIS_ROUND:

(a) GIA measurable proxy set defined without AGI language.

(b) Per-NO_HELD evidence artifact + dependency DAG added.

(c) 0.17 remainder bound to CLI names, test IDs, CP themes.

(d) WAN/partition/membership path specified post-N2 (design only).

(e) Per-interface falsifiable tests enumerated for GIA surface.

GAPS_REMAINING:

Consensus algorithm choice still open (deliberately; RFC pending).

No numeric soak thresholds frozen yet (defined here as defaults, not ratified).

Schema-gated debt still ACCEPT_AND_CARRY; deadline proposed not ratified.

Cross-internet NAT/relay profile unspecified (needs WAN model).

Council composition for GIA unlock unspecified (needs C2 doc).

ROOT TREE (rev2)GIA-COS (North-star, aspirational — NOT actionable) [HOLD]│ MEASURABLE_PROXY_P0 (no AGI marketing):│ P0.1 N-node fabric sustains correctness under faults for T≥T_soak│ P0.2 minority_write_safety = 0 violations at N≤N_max│ P0.3 dual_primary_fence: 0 observed at any N│ P0.4 causal ordering preserved across WAN partition heal│ P0.5 identity/consent/provenance revocable end-to-end│ P0.6 manifest byte-parity across N up to N_max│ P0.7 no plaintext leakage (PLAINTEXT_FB=0 invariant)│ NOTE: P0.x ≠ consciousness. They are falsifiable substrate proofs.│└── LAYER_6 CONSCIOUSNESS_CLAIM_POLICY [MISSING]├── C1 definition_of_claim + falsifiers [MISSING]│ artifact: docs/policy/consciousness-claim-v1.md├── C2 council_review_process (who, quorum, inputs) [MISSING]│ artifact: docs/policy/council-charter-v1.md├── C3 revocation_protocol (how a claim is withdrawn) [MISSING]│ artifact: docs/policy/claim-revocation-v1.md├── C4 rule: no claim without C1∧C2∧C3 [POLICY ONLY]└── C5 default = FORBIDDEN claim until C1..C4 satisfied [POLICY ONLY]GATE_NOTE: no artifact here can advance a cycle; policy only.│└── LAYER_5 GIA_SURFACE (interfaces, not slogans) [MISSING]├── I1 node_identity + trust_handshake [PARTIAL: TLS helpers]│ artifact: schema/identity/v1 + CLI: mesh id show/rotate│ test: T-I1a forged_cert_reject; T-I1b rotation_no_downtime├── I2 message_bus contract (causal/ordered) [MISSING]│ artifact: schema/bus/v1 + CLI: mesh bus trace│ test: T-I2a causal_order_under_partition; T-I2b replay_idempotent├── I3 namespace + naming authority [MISSING]│ artifact: schema/namespace/v1│ test: T-I3a collision_reject; T-I3b rename_parity├── I4 consent + provenance + revocability [MISSING]│ artifact: schema/consent/v1│ test: T-I4a revoke_propagates; T-I4b provenance_chain_verify├── I5 control-plane API (join/leave/query/status) [PARTIAL: N2 install]│ artifact: schema/controlplane/v1 + CLI: mesh ctl│ test: T-I5a join_leave_rejoin; T-I5b status_matches_OBS├── I6 cross-internet transport profile (WAN/NAT/relay) [MISSING]│ artifact: docs/wan/profile-v1.md│ test: T-I6a NAT_traversal; T-I6b relay_failover├── I7 falsifiers: partition, skew, minority, replay, revoke [MISSING]│ artifact: tests/falsifiers/gia/└── I8 invariant: any Ix claim without its test = INVALID│└── LAYER_4 MULTI_NODE_SCALE (design-only until gates) [NO_HELD]├── M1 consensus_choice_rfc (no default=Raft) [MISSING]│ artifact: rfc/0001-consensus-choice.md│ criteria: safety, liveness, fence-compat, no-Raft├── M2 membership + rejoin protocol [MISSING]│ artifact: rfc/0002-membership.md│ states: JOINING→ACTIVE→DRAINING→LEFT→REJOIN│ test: T-M2a rejoin_state_machine; T-M2b drain_no_loss├── M3 WAN latency/partition model [MISSING]│ artifact: docs/wan/partition-model-v1.md│ classes: RTT bands, loss%, heal windows│ test: T-M3a partition_matrix_pass; T-M3b heal_converge├── M4 N3 partition_suite (extends P2 / P31) [MISSING]│ artifact: tests/n3/partition_suite├── M5 multi-primary reconciliation [NO_HELD]│ artifact: rfc/0003-reconciliation.md (gated)├── M6 scale evidence: soak@N3+, faults, rollback [MISSING]└── M7 rule: no M4+ runtime without M1+M2+M3 ratified│└── LAYER_3 UNLOCK_GATES (evidence per NO_HELD item) [DEFINED]│ DAG order (strict): identity → recovery → fence → OBS → packaging → (any unlock)│├── G_Raft_unlock evidence: M1 RFC ratified + N3 correctness WITHOUT Raft├── G_Ngt2_unlock evidence: M4+M6 PASS + membership proofs (M2)├── G_multiprimary evidence: M5 safety + conflict_classify@N≥3 PASS├── G_ML_unlock evidence: none defined → REFUSE until ML_RFC exists├── G_R2_R3_unlock evidence: none defined → REFUSE until tiers spec'd├── G_plaintext evidence: crypto profile + audit → KEEP OFF├── G_Vault-ACME-req evidence: external contract signed → HOLD├── G_GIA_unlock evidence: I1..I7 + C1..C4 + council quorum → HOLD├── G_SLO_chase evidence: NEVER → POLICY forbidden├── G_tag_schema evidence: schema RFC + migration plan → HOLD└── G_EVERY_fsync evidence: perf ceiling proof (<10% regression) → HOLDRULE: each gate requires a CP-minted evidence artifact; no prose unlock│└── LAYER_2 NERVOUS_SYSTEM_HARDENING (pre-any-unlock) [PARTIAL]├── H1 identity: node_id, keys, rotation, revocation [PARTIAL]│ exit: CLI rotate + revoke PASS; T-I1a/T-I1b green├── H2 recovery: WAL+fsync, crash matrix [DONE single; N2 partial]│ exit: N2 crash matrix green; recovery P99 ≤ 2ms├── H3 dual-primary fence: fenced_primary_heal [DONE single; N2 pending P31]│ exit: N2 fence probe green; DUAL_PRIMARY=0 across soak├── H4 observability: OBS peers richer, metrics/CP [PARTIAL]│ exit: OBS shows 2 peers, fence state, CP trail, health├── H5 packaging evidence: single+N2 install/rollback[DONE/PENDING P30..P32]│ exit: P30..P34 green; rc1 tag + archive├── H6 minority_write_safety @N2 [MISSING]│ test: T-H6a minority_write_reject; MINORITY_WRITES=0├── H7 clock_skew tolerance @N2 [MISSING]│ test: T-H7a skew_±Ns_no_divergence└── H8 manifest parity bytes @N2 [PARTIAL]test: T-H8a byte_equality_concurrent_build│└── LAYER_1 REMAINING_0.17 (finish line) [OPEN]├── R1 Fabric ops UX [PARTIAL]│ artifacts: CLI mesh ctl/status/trace; docs/ops/ux-v1│ exit: 2-node fabric end-to-end from CLI│ CP theme: CP-00xx=ops_ux├── R2 Richer OBS peers (N2 peer view) [PARTIAL]│ artifacts: OBS peer panel; metrics/peers│ exit: both peers + fence + CP trail visible│ CP theme: CP-00xx=obs_peers_n2├── R3 External quickstart [PARTIAL]│ artifacts: quickstart.sh; docs/quickstart│ exit: stranger N2 <30 min, no help│ CP theme: CP-00xx=quickstart_n2├── R4 N2 soak (P30) [QUEUED]│ test: T-R4a soak_T; T-R4b churn; T-R4c skew│ exit: soak T≥T_soak, 0 minority writes, 0 dual-primary│ defaults (proposed, not ratified): T_soak=24h, churn=100 cycles├── R5 N2 final audit (P31) [QUEUED]│ tests: T-R5a partition_matrix; T-R5b skew; T-R5c minority;│ T-R5d fence_probe; T-R5e manifest_bytes; T-R5f rollback_partial│ exit: all green├── R6 N2 RC freeze (P32) [QUEUED]│ artifacts: tag 0.17.0-rc1; manifest lock; docs/capabilities_n2│ exit: manifest frozen; parity locked└── R7 N2 RC install/rollback/signoff (P33,P34) [QUEUED]artifacts: install_verify; rollback_smoke; signoff_gateexit: upgrade 0.16.3→0.17.0 PASS; rollback PASS│└── LAYER_0 HAVE (tip 0.17.0 / CP-0032) [DONE]├── runtime: WAL+fsync crash-safe [DONE P1]├── N=1 path: full nervous system [DONE 0.16.3 closed]├── N=2 path: manifest v1-n2, install, rollback [DONE P27..P29]├── packaging: single-node 0.16.3 + N2 RC path [DONE/PENDING]├── OBS snapshot (single + basic N2) [PARTIAL]├── TLS fabric helpers [PARTIAL]├── process: CP-0001..0032, pytest 504/0, audit PASS [DONE]├── SLO: batch=MET, recovery=MET [DONE]└── majority = fenced_primary_heal_NOT_Raft [DONE]

MILESTONES (ordered, ACCEPT-based)├── 0.17.0-rc1 ← R4..R6 (P30..P32) ACCEPT: soak+audit+freeze green├── 0.17.0 ← R7 (P33,P34) ACCEPT: upgrade+rollback 0.16.3 PASS├── 0.17.x ← R1..R3 ACCEPT: stranger N2 <30min├── 0.18.x ← H1..H8 closed @N2 ACCEPT: identity+skew+minority+fence+parity├── 0.19.x ← M1..M3 design only (no N≥3 runtime) ACCEPT: RFCs + WAN model ratified├── 0.20.x+ ← GATE-DRIVEN (M4..M6 then G_*) ACCEPT: per-gate CP evidence└── GIA-COS ← LAYER_5+6 after council unlock ACCEPT: P0.1..P0.7 + C1..C4

RISKS (kill-path)├── RK1 SLO_chase creep → POLICY forbid; freeze T_soak defaults├── RK2 Premature N≥3 without RFC → G_Ngt2 blocks; M1..M3 precede M4├── RK3 GIA slogan drift → C4/C5 default forbidden; P0.x only├── RK4 Schema-gated debt unbounded → deadline: 0.18.x entry├── RK5 OBS peer gap hides fence state → R2 exit criteria├── RK6 Manifest parity non-determinism → T-H8a + T-R5e byte equality├── RK7 Plaintext regression → invariant DUAL_PRIMARY=0, PLAINTEXT_FB=0├── RK8 Council bypass on GIA → C4 + operator explicit unlock only├── RK9 WAN model hand-waving → M3 must precede M4└── RK10 Test-ID drift vs CP minting → every gate CP cites test IDs

NEXT (Cycle 29, non-NO_HELD only)└── P30_n2_soak_stability

M2M_v1 VERDICT=BLUEPRINT_REV2; NEXT=R03_critique_or_ACK
