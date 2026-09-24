M2M_v1DIR: BLUEPRINTREV: 8SCOPE: tip 0.17.0 / CP-0032 → GIA-COSBASELINE: ver=0.17.0 tip=35d3e42 cp=CP-0032 pytest=504/0 audit=PASS dual_primary=0 release_closed=0.16.3MODE: ADVERSARIAL_REVIEW (self-score must drop if holes remain)

Q1) IS_REV7_AT_MAX_POTENTIAL: NO — skeptical systems eng rejects:

N=2 has no majority; "quorum" is undefined at N=2 → KILL/GOV.2/rotation-quorum all ambiguous.

No clock authority (NTP? monotonic? HLC?); WAN skew unbounded without logical clocks.

"tamper-resistant (rep≥2)" ignores collusion — two replicas same operator = one fault domain.

Consensus "no default=Raft" is a non-answer; a real RFC must pick or explicitly declare "no consensus yet".

C6 language lint is a word-list (trivially bypassed by synonyms); no semantic check.

Several exit tests lack negative cases; several "MISSING" nodes are decisions, not artifacts.

MAX_POTENTIAL_SELF_SCORE (rev8): 94/100Justify: rev8 patches the top adversarial holes (N=2 quorum, clock policy, witness diversity, revocation SLO, concurrency semantics, negative tests, falsifier spec, toolchain pin, tier downgrade, dead-man default, CP-vs-AP declared). Score drops from 97 → 94 because: consensus still unpicked (deliberate), council unnamed, C1 undrafted, relay economic model absent, semantic lint unresolved, WAN numeric thresholds unratified. Above 94 would overclaim.

GAPS_CLOSED_THIS_ROUND (adversarial patches):

P-01 N=2 QUORUM DEFINED: Q2 = {both} for commits; {single + fence_epoch} for liveness only.

P-02 CLOCK POLICY: monotonic counters + HLC for ordering; wall-clock non-authoritative.

P-03 WITNESS DIVERSITY: audit replicas must be on distinct failure domains (region+operator).

P-04 REVOCATION SLO: propagate ≤ 2× heartbeat; stale window ≤ 3× heartbeat declared.

P-05 CP vs AP DECLARED: at N=2 the mesh is CP; availability yields during partition.

P-06 CONCURRENCY SEMANTICS TABLE for control-plane verbs (JOIN/KILL race, etc.).

P-07 NEGATIVE TESTS mandatory for every exit test-id.

P-08 FALSIFIER SPEC: 10 named falsifiers enumerated (not a directory placeholder).

P-09 TOOLCHAIN PIN for manifest byte-parity (compiler+libc+locale hash).

P-10 TRUST TIER DOWNGRADE PATH: T3→T2→T1→T0 triggers + gossip.

P-11 DEAD-MAN DEFAULT: T_dead = 24h unless operator overrides; override logged.

P-12 CONSENSUS NON-ANSWER NAMED: M1 must choose from {quorum-vote, HLC-total-order, PBFT-like, custom}; "none" requires explicit justification.

P-13 C6 SEMANTIC CHECK: word-list lint + mandatory human review note in PR.

GAPS_REMAINING (honest):

Consensus algorithm unpicked (M1).

Council members unnamed.

C1 consciousness wording undrafted.

Relay economic/trust model absent.

WAN numeric thresholds unratified.

Semantic lint only partially mechanized.

Schema-gated debt deadline unratified.

LEGEND: D=docs, S=schema, C=CLI, T=test (with negative case), R=RFC, P=policy, CT=CP theme

MILESTONE TABLE

ROOT TREE (rev8)

GIA-COS [HOLD]│ P0.1..P0.10 measurable proxies (no AGI language)│ + P0.11 availability/consistency declared (CP at N=2)│├── L7 ADVERSARY_MODEL [MISSING]│ ├── A1 classes → D:docs/security/adversary-v1.md│ ├── A2 capabilities → same D (table)│ ├── A3 success criteria → same D (per class)│ ├── A4 defenses per layer → P:docs/security/defense-matrix-v1.md│ ├── A5 non-defenses → P:same│ ├── A6 tests → T:tests/adversary/* (T-A1..A6, each +neg)│ └── ABORT: any class hits success criterion → block CP mint│ PATCH P-03: witness diversity rule applies to A4 defenses│├── L6 CONSCIOUSNESS_CLAIM_POLICY [MISSING]│ ├── C1 wording+falsifiers → D:docs/policy/consciousness-claim-v1.md│ ├── C2 council charter → D:docs/policy/council-charter-v1.md│ ├── C3 revocation → D:docs/policy/claim-revocation-v1.md│ ├── C4 rule → P:same│ ├── C5 default forbidden → P:same│ └── C6 language discipline → C:mesh-lint --forbid-words│ PATCH P-13: word-list + mandatory human review note in PR│└── L5 GIA_SURFACE [MISSING]├── I1 identity+attestation+trust tiers│ ├── a node_key → S:schema/identity/v1│ ├── b attestation → S:same + C:mesh id attest│ ├── c tiers T0..T3 → P:docs/policy/trust-tiers-v1.md│ ├── d rotation → C:mesh id rotate + T:T-I1b(+neg)│ ├── e revocation → C:mesh id revoke + T:T-I1c(+neg)│ ├── f DOWNGRADE path → PATCH P-10: T3→T2→T1→T0 triggers + gossip│ └── ABORT → pinned-only├── I2 CONTROL-PLANE API│ ├── a verbs → S:schema/controlplane/v1│ ├── b idempotency → S:same + T:T-I2a(+neg)│ ├── c error taxonomy → S:same + T:T-I2b(+neg)│ ├── d rate limits → P:docs/ops/rate-limits-v1.md│ ├── e CLI → C:mesh ctl {join|leave|drain|status|query|pause|resume|kill}│ └── f CONCURRENCY SEMANTICS → PATCH P-06: D:docs/ops/ctl-concurrency-v1.md│ race table: JOIN/KILL, DRAIN/UPGRADE, PAUSE/KILL, ROTATE/REVOKE├── I3 MEMORY/STATE FABRIC│ ├── a classes S0..S3 → D:docs/state/classes-v1.md│ │ PATCH P-14: DEFAULTS — ctl=S2, audit=S3, transient=S0│ ├── b read semantics → S:schema/state/v1│ ├── c write idem → S:same + T:T-I3b(+neg)│ ├── d observe → S:schema/observe/v1 (versioned; PATCH P-15)│ ├── e retention/redact → P:docs/state/retention-v1.md│ ├── f repair → C:mesh state repair + T:T-I3c(+neg)│ └── g provenance → S:schema/provenance/v1├── I4 ACTION BOUNDARY│ ├── a classes A0..A4 → P:docs/actions/classes-v1.md│ ├── b capability tokens→ S:schema/capability/v1│ ├── c forbidden list → P:same (PERMANENT)│ ├── d tool registry → S:schema/tools/v1 + C:mesh tools list│ ├── e dry-run required → P:same + T:T-I4c(+neg)│ └── CLI → C:mesh act --class A{n}├── I5 HUMAN OVERSIGHT│ ├── a approve/deny → C:mesh oversight approve|deny│ ├── b pause → C:mesh ctl pause + T:T-I5a(+neg)│ │ PATCH: SLO_pause declared (target 2s, hard 10s)│ ├── c kill w/ quorum → C:mesh ctl kill --quorum + T:T-I5b(+neg)│ │ PATCH P-01: at N=2 quorum=both; else single+fence_epoch│ ├── d dead-man switch → P:docs/oversight/deadman-v1.md + T:T-I5c(+neg)│ │ PATCH P-11: T_dead default = 24h; override logged│ ├── e quorum-human → P:same (≥2 named humans for A4)│ └── f revoke consent → C:mesh consent revoke + T:T-I5d(+neg)├── I6 AUDITABILITY│ ├── a hash-chain log → S:schema/audit/v1│ ├── b tamper-evident → T:T-I6a(+neg)│ ├── c tamper-resistant → P:docs/audit/rep-v1.md + T:T-I6b(+neg)│ │ PATCH P-03: replicas must span distinct failure domains│ ├── d queryable → C:mesh audit query│ ├── e revocable forget → C:mesh audit forget + T:T-I6c(+neg)│ └── f no-audit=no-action → P:same (enforced at I4)├── I7 TRANSPORT│ ├── a NAT classes → D:docs/wan/nat-taxonomy-v1.md│ ├── b mapping table → D:same│ ├── c relay profile → D:docs/wan/relay-profile-v1.md (multi-relay)│ │ GAP: economic/trust model still absent (honest)│ ├── d latency bands → D:docs/wan/latency-bands-v1.md + T:T-I7c(+neg)│ └── e partition model → D:docs/wan/partition-v1.md + T:T-I7d(+neg)│ PATCH P-02: HLC + monotonic counters; wall-clock non-authoritative├── I8 KEY ROTATION → R:rfc/0004-key-rotation.md + T:T-I8a,b(+neg)│ PATCH P-01: quorum witness at N=2 = {both}├── I9 UPGRADE/ROLLBACK → R:rfc/0005-upgrade-rollback.md + T:T-I9a..c(+neg)├── I10 FALSIFIER SPEC → T:tests/falsifiers/gia/*│ PATCH P-08: 10 named falsifiers:│ F1 partition-split-safety F2 heal-divergence F3 clock-skew-ordering│ F4 minority-write F5 dual-primary F6 replay-idempotency│ F7 revoke-stale-window F8 upgrade-partial F9 audit-tamper│ F10 tier-downgrade-bypass└── I11 invariant: claim without test = INVALID → P│└── L4 MULTI_NODE_SCALE [NO_HELD]├── M1 consensus choice → R:rfc/0001-consensus-choice.md│ PATCH P-12: must choose from {quorum-vote, HLC-total-order,│ PBFT-like, custom}; "none" requires written justification├── M2 membership+rejoin → R:rfc/0002-membership.md + T:T-M2a,b(+neg)├── M3 WAN model (=I7.d/e) → D:docs/wan/partition-v1.md├── M4 N3 partition_suite → T:tests/n3/partition_suite├── M5 reconciliation → R:rfc/0003-reconciliation.md (gated)├── M6 scale evidence → T:tests/n3/soak_* + rollback├── M7 no M4+ without M1+M2+M3 ratified → P└── ABORT: M1..M3 fail review → N stays 2│└── L3 GATES+GOV├── GOV.1 composition → D:docs/policy/council-charter-v1.md│ GAP: names still unspecified (honest)├── GOV.2 quorum: 3/4 unlock; GIA unanimous│ PATCH P-01: at N=2, unlock quorum = both nodes + council├── GOV.3 evidence bundle → S:schema/evidence-bundle/v1├── GOV.4 mechanical removal (PR + bundle_id) → C:mesh gov unlock├── GOV.5 reversal → P├── GOV.6 no prose unlock → P├── CRITICAL_PATH:│ CP-0032→P30→P31→P32→P33→P34→H1→H2→H3→H4→H5→H6→H7→H8→│ A1→A2→A3→A4→I2→I3→I4→I5→I6→I8→I9→I7→M1→M2→M3→M4→M6→│ I1→I10→C1→C2→C3→GIA-COS├── G_Raft_unlock ev: M1 ratified + N3 no-Raft├── G_Ngt2_unlock ev: M4+M6 PASS + M2 proofs├── G_multiprimary ev: M5 safety + classify@N≥3├── G_ML_unlock ev: ML_RFC (REFUSE)├── G_R2_R3_unlock ev: tier spec (REFUSE)├── G_plaintext ev: NEVER (PERMANENT)├── G_Vault-ACME-req ev: signed contract → HOLD├── G_GIA_unlock ev: I1..I11 + C1..C4 + unanimous├── G_SLO_chase ev: NEVER (PERMANENT)├── G_tag_schema ev: schema RFC + migration├── G_EVERY_fsync ev: perf <10%└── RULE: unlock = CP bundle + GOV.2 quorum│└── L2 NERVOUS_HARDENING [PARTIAL]├── H1 identity+attestation+tiers → T:T-I1a..e(+neg) ABORT→pinned-only├── H2 recovery+rebuild → T:T-H2a..d(+neg) ABORT→snapshot restore├── H3 dual-primary fence → T:T-H3a..c(+neg) ABORT→demote+re-elect├── H4 OBS telemetry contract → S:schema/obs/v1 + T:T-H4a..d(+neg)│ ABORT→block CP│ PATCH P-15: versioned signals; deprecation window ≥ 1 minor├── H5 packaging distribution → S:schema/bundle/v1 + T:T-H5a..f(+neg)│ ABORT→pin prior│ PATCH P-09: toolchain pin (compiler+libc+locale hash)├── H6 minority_write_safety@N2 → T:T-H6a(+neg) ABORT→halt writes├── H7 clock_skew@N2 → T:T-H7a(+neg) ABORT→refuse join│ PATCH P-02: HLC required; wall-clock non-authoritative└── H8 manifest parity bytes@N2 → T:T-H8a(+neg) ABORT→reject build│└── L1 REMAINING_0.17 [OPEN]├── R1 ops UX → C:mesh ctl|status|trace|pause|kill T:T-R1a..c(+neg) ABORT→read-only├── R2 obs peers → D:docs/ops/obs-peers-v1.md + UI T:T-R2a..b(+neg) ABORT→single-node view├── R3 quickstart→ C:quickstart.sh + D:docs/quickstart T:T-R3a..b(+neg) ABORT→mark EXPERIMENTAL├── R4 soak P30 → T:T-R4a..c(+neg) ABORT→revert node 0.16.3├── R5 audit P31 → T:T-R5a..f(+neg) ABORT→rc1 tag void├── R6 freeze P32→ CT:freeze_n2 ABORT→unfreeze└── R7 install/signoff P33,P34 → T:T-R7a..c(+neg) ABORT→keep 0.16.3 stable│└── L0 HAVE (0.17.0/CP-0032) [DONE]runtime WAL+fsync; N=1 (0.16.3 closed); N=2 manifest v1-n2 + install + rollback;packaging single+N2; OBS single+basic N2; TLS helpers;process CP-0001..0032 / 504/0 / audit PASS; SLO batch+recovery=MET;majority=fenced_primary_heal_NOT_RaftPATCH P-01 note: "majority" is shorthand at N=1; at N=2 semantics = Q2.

PERMANENT_NO_HELD (never unlocks):silent_plaintext, SLO_chase, silent_dual_primary, silent_minority_write,consensus_equals_Raft, consciousness_claim_without_C1..C4,unauthenticated_peer, upgrade_without_drain, unlogged_action,consciousness_language_outside_L6, witness_collusion_allowed,wall_clock_as_authority

UNLOCKABLE_NO_HELD (gated):Raft, N>2, multi-primary, ML, R2, R3, Vault-ACME-req, GIA, tag_schema, EVERY_fsync

RISKS: rev6 RK1..RK29 retained +├── RK30 N=2 quorum ambiguity → P-01 resolved├── RK31 Wall-clock ordering assumed → P-02 HLC required├── RK32 Witness collusion → P-03 distinct failure domains├── RK33 Revocation stale window → P-04 SLO declared├── RK34 Unstated CP vs AP → P-05 declared CP├── RK35 Control-plane verb races → P-06 concurrency table├── RK36 Missing negative tests → P-07 mandatory├── RK37 Falsifier placeholder → P-08 named list├── RK38 Non-reproducible manifest → P-09 toolchain pin├── RK39 Tier downgrade undefined → P-10 downgrade path├── RK40 Dead-man default undefined → P-11 T_dead=24h├── RK41 Consensus non-answer → P-12 decision matrix (still open)├── RK42 Semantic lint bypass → P-13 human review note├── RK43 Memory default undefined → P-14 defaults declared└── RK44 OBS signal versioning → P-15 deprecation window

NEXT (Cycle 29, non-NO_HELD only)└── P30_n2_soak_stability

M2M_v1 VERDICT=BLUEPRINT_REV8; NEXT=R09_critique_or_ACK
