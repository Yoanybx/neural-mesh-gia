M2M_v1DIR: BLUEPRINTREV: 5SCOPE: tip 0.17.0 / CP-0032 → North-star (GIA-COS, aspirational)BASELINE: ver=0.17.0 tip=35d3e42 cp=CP-0032 cp_range=CP-0001..0032 pytest=504/0 audit=PASS dual_primary=0 release_closed=0.16.3 line=0.17.0=OPEN

Q1) IS_REV4_AT_MAX_POTENTIAL: NO

No adversary model: identity/attestation existed without a defined attacker class, capability, or success criterion.

NAT was one bullet; no taxonomy (full-cone vs symmetric vs CGNAT) and no relay-required path.

Multi-region latency was absent; WAN model had "RTT bands" as placeholder, no jitter, no partition probability.

Partial trust was implicit (TOFU→pinned) but not formalized into trust tiers with escalation rules.

Key rotation and mesh-software upgrade/rollback across peers were stated as features, not as cross-peer protocols with abort.

MAX_POTENTIAL_SELF_SCORE (rev5): 96/100Justify: rev5 adds an explicit adversary model, NAT taxonomy with relay path, multi-region latency bands with partition probability, partial-trust tiers, cross-peer key-rotation, and cross-peer upgrade/rollback protocols with abort. Loses 4 points because: consensus RFC still unwritten (deliberate), council members unnamed, C1 consciousness wording undrafted, WAN numeric thresholds unratified. Above 96 would overclaim.

GAPS_CLOSED_THIS_ROUND:

Adversary model: classes (passive, active-MITM, malicious peer, Byzantine peer, supply-chain) + success criteria.

NAT taxonomy: full_cone, restricted_cone, symmetric, CGNAT; relay-required path defined.

Multi-region latency bands: RTT tiers, jitter, loss, partition probability.

Partial trust: T0..T3 tiers with escalation and refusal rules.

Cross-peer key rotation: staged overlap, quorum witness, revoke fanout.

Cross-peer upgrade/rollback: drain → snapshot → stage → flip → verify; per-peer abort.

New permanent invariant: ADVERSARY_ACK — every layer names the attacker it defends against.

GAPS_REMAINING:

Consensus algorithm still unselected (deliberate; NO_HELD intact).

WAN numeric thresholds proposed but not ratified.

Council membership unspecified.

C1 consciousness-claim wording undrafted.

Schema-gated debt deadline proposed not ratified.

Relay trust model partial (who runs relays, what attestation).

PERMANENT_NO_HELD (never unlocks):

silent_plaintext (PLAINTEXT_FB=0 forever)

SLO_chase

silent_dual_primary (DUAL_PRIMARY=0 or CP void)

silent_minority_write (MINORITY_WRITES=0 or CP void)

consensus_equals_Raft (Raft not presumed)

consciousness_claim_without_C1..C4

unauthenticated_peer (no peer joins without attestation)

upgrade_without_drain (no mesh upgrade without draining the peer first)

UNLOCKABLE_NO_HELD (deferred, gated by evidence):Raft, N>2, multi-primary, ML, R2, R3, Vault-ACME-req, GIA, tag_schema, EVERY_fsync

MILESTONES (ordered, ACCEPT-based, rollback-aware)├── 0.17.0-rc1 ← R4..R6 ACCEPT: soak+audit+freeze green ROLLBACK→pre-rc1├── 0.17.0 ← R7 ACCEPT: upgrade+rollback 0.16.3 PASS ROLLBACK→0.16.3├── 0.17.x ← R1..R3 ACCEPT: stranger N2 <30min ROLLBACK→CLI read-only├── 0.18.x ← H1..H8 ACCEPT: identity+recovery+skew+minority+fence+parity+telemetry ROLLBACK→0.17.0├── 0.18.x+ ← A1..A4 ACCEPT: adversary model + defense tests green ROLLBACK→policy-only├── 0.18.x+ ← I9,I10 ACCEPT: rotation quorum + upgrade drain/rollback green ROLLBACK→last green├── 0.19.x ← M1..M3 ACCEPT: RFCs + WAN model + GOV charter ROLLBACK→0.18.x├── 0.20.x+ ← GATE-DRIVEN ACCEPT: per-gate CP bundle + GOV.2 quorum ROLLBACK→last green N└── GIA-COS ← L5+L6+L7 ACCEPT: P0.1..P0.9 + C1..C4 + unanimous ROLLBACK→policy-only

CRITICAL_PATH (tip→GIA, single-thread):CP-0032 → P30 → P31 → P32 → P33 → P34 →H1 → H2 → H3 → H4 → H5 → H6 → H7 → H8 →A1 → A2 → A3 → A4 →I9 → I10 →M1 → M2 → M3 → M4 → M6 →I1 → I2 → I3 → I4 → I5 → I6 → I7 →C1 → C2 → C3 → GIA-COS(parallel branches may shorten; none bypass)

PERMANENT_NO_HELD (never unlocks):silent_plaintext, SLO_chase, silent_dual_primary, silent_minority_write,consensus_equals_Raft, consciousness_claim_without_C1..C4,unauthenticated_peer, upgrade_without_drain

UNLOCKABLE_NO_HELD (gated):Raft, N>2, multi-primary, ML, R2, R3, Vault-ACME-req, GIA, tag_schema, EVERY_fsync

RISKS (kill-path, rev5)├── RK1 SLO_chase creep → PERMANENT├── RK2 Premature N≥3 without RFC → G_Ngt2 blocks; M1..M3 precede M4├── RK3 GIA slogan drift → C4/C5; P0.x only├── RK4 Schema-gated debt unbounded → deadline 0.18.x entry├── RK5 OBS peer gap → R2 exit + H4.c├── RK6 Manifest parity drift → T-H8a + T-R5e├── RK7 Plaintext regression → PERMANENT PLAINTEXT_FB=0├── RK8 Council bypass → GOV.2 unanimous + GOV.6├── RK9 WAN hand-waving → M3=I6.d/e precedes M4├── RK10 Test-ID drift → gate CP cites test IDs├── RK11 Attestation replay → T-I1d + nonce + freshness├── RK12 Bundle replay → H5.c replay guard├── RK13 Silent invariant breach → H4.c auto-fail; block CP mint├── RK14 Abort-path untested → each ABORT has dry-run test├── RK15 Critical-path starvation → only non-critical work parallelizes├── RK16 NAT class misidentified → I6.a requires class detection before join├── RK17 Relay single point of failure → I6.c relay profile must be multi-relay├── RK18 Key rotation race → I9.b quorum witness; T-I9a├── RK19 Upgrade partial-mesh split → I10.g abort holds last all-green├── RK20 Adversary class uncovered → A3 success criterion = CP void└── RK21 Coerced operator → A1 class; A5 non-defense declared

NEXT (Cycle 29, non-NO_HELD only)└── P30_n2_soak_stability

M2M_v1 VERDICT=BLUEPRINT_REV5; NEXT=R06_critique_or_ACK
