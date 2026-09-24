M2M_v1DIR: BLUEPRINTREV: 6SCOPE: tip 0.17.0 / CP-0032 → North-star (GIA-COS, aspirational)BASELINE: ver=0.17.0 tip=35d3e42 cp=CP-0032 cp_range=CP-0001..0032 pytest=504/0 audit=PASS dual_primary=0 release_closed=0.16.3 line=0.17.0=OPEN

Q1) IS_REV5_AT_MAX_POTENTIAL: NO

LAYER_5 was a list of interfaces (I1..I10) but had no CONTROL-PLANE API surface (no verbs, no schemas, no idempotency rules).

Memory/state fabric was implicit (WAL + projections) but never formalized as a contract (read/write/observe semantics, consistency class, retention).

Tool/action boundaries were absent: nothing said what an autonomous actor MAY or MAY NOT do, nor how actions are gated.

Human oversight hooks were missing (approve/deny/pause/kill switch, quorum-human).

Auditability was implied by OBS but not a formal append-only, tamper-evident, revocable log contract.

Consciousness vocabulary appeared only in LAYER_6, but LAYER_5 had no rule forbidding it.

MAX_POTENTIAL_SELF_SCORE (rev6): 97/100Justify: rev6 makes LAYER_5 precise (control-plane verbs+schemas, memory/state fabric contract, tool/action boundary grammar, human oversight hooks, auditability contract) and enforces consciousness language ONLY under LAYER_6. Loses 3 points because: consensus RFC still unwritten (deliberate NO_HELD), council members unnamed, C1 wording undrafted, WAN numeric thresholds unratified. Above 97 would overclaim.

GAPS_CLOSED_THIS_ROUND:

Control-plane API surface: verbs (JOIN, LEAVE, DRAIN, STATUS, QUERY, PAUSE, RESUME, KILL), schemas, idempotency keys, error taxonomy.

Memory/state fabric contract: read/write/observe semantics, consistency class, retention, redaction, repair.

Tool/action boundary grammar: action classes A0..A4, capability tokens, human-gated classes, forbidden classes.

Human oversight hooks: approve/deny/pause/kill, quorum-human, dead-man switch, revocable consent.

Auditability contract: append-only, hash-chained, tamper-evident, revocable, queryable; per-CP window linkage.

Language discipline: consciousness vocabulary forbidden outside LAYER_6.

GAPS_REMAINING:

Consensus algorithm still unselected (deliberate).

WAN numeric thresholds proposed not ratified.

Council membership unspecified.

C1 consciousness-claim wording undrafted.

Schema-gated debt deadline proposed not ratified.

Relay trust model partial.

Tool/action boundary enforcement mechanism not yet chosen (policy now, enforcement later).

PERMANENT_NO_HELD (never unlocks):silent_plaintext, SLO_chase, silent_dual_primary, silent_minority_write,consensus_equals_Raft, consciousness_claim_without_C1..C4,unauthenticated_peer, upgrade_without_drain, unlogged_action

UNLOCKABLE_NO_HELD (deferred, gated):Raft, N>2, multi-primary, ML, R2, R3, Vault-ACME-req, GIA, tag_schema, EVERY_fsync

MILESTONES (ordered, ACCEPT-based, rollback-aware)├── 0.17.0-rc1 ← R4..R6 ACCEPT: soak+audit+freeze green ROLLBACK→pre-rc1├── 0.17.0 ← R7 ACCEPT: upgrade+rollback 0.16.3 PASS ROLLBACK→0.16.3├── 0.17.x ← R1..R3 ACCEPT: stranger N2 <30min ROLLBACK→CLI read-only├── 0.18.x ← H1..H8 ACCEPT: identity+recovery+skew+minority+fence+parity+telemetry ROLLBACK→0.17.0├── 0.18.x+ ← A1..A4 ACCEPT: adversary model + defense tests green ROLLBACK→policy-only├── 0.18.x+ ← I2..I6 ACCEPT: control-plane+memory+tools+oversight+audit green ROLLBACK→last green├── 0.18.x+ ← I8,I9,I7 ACCEPT: rotation + upgrade/rollback + NAT green ROLLBACK→last green├── 0.19.x ← M1..M3 ACCEPT: RFCs + WAN model + GOV charter ROLLBACK→0.18.x├── 0.20.x+ ← GATE-DRIVEN ACCEPT: per-gate CP bundle + GOV.2 quorum ROLLBACK→last green N└── GIA-COS ← L5+L6+L7 ACCEPT: P0.1..P0.10 + C1..C4 + unanimous ROLLBACK→policy-only

CRITICAL_PATH (tip→GIA, single-thread):CP-0032 → P30 → P31 → P32 → P33 → P34 →H1 → H2 → H3 → H4 → H5 → H6 → H7 → H8 →A1 → A2 → A3 → A4 →I2 → I3 → I4 → I5 → I6 →I8 → I9 → I7 →M1 → M2 → M3 → M4 → M6 →I1 → I10 →C1 → C2 → C3 → GIA-COS

PERMANENT_NO_HELD (never unlocks):silent_plaintext, SLO_chase, silent_dual_primary, silent_minority_write,consensus_equals_Raft, consciousness_claim_without_C1..C4,unauthenticated_peer, upgrade_without_drain, unlogged_action,consciousness_language_outside_L6

UNLOCKABLE_NO_HELD (gated):Raft, N>2, multi-primary, ML, R2, R3, Vault-ACME-req, GIA, tag_schema, EVERY_fsync

RISKS (kill-path, rev6)├── RK1..RK21 (rev5 retained)├── RK22 Control-plane verb drift → I2.b schema + I2.c idempotency├── RK23 Memory class not honored → T-I3a; downgrade claim├── RK24 Action boundary bypass → T-I4b; forbidden actions denied├── RK25 Human oversight bypass → T-I5b/c; dead-man drain├── RK26 Audit gap (unlogged action) → I6.g no-audit=no-action├── RK27 Audit chain tamper → T-I6b; node read-only├── RK28 Consciousness vocabulary leak → C6 lint-check in CI└── RK29 Tool revocation lag → T-I4d; cap token TTL

NEXT (Cycle 29, non-NO_HELD only)└── P30_n2_soak_stability

M2M_v1 VERDICT=BLUEPRINT_REV6; NEXT=R07_critique_or_ACK
