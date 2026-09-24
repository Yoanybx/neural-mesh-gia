M2M_v1DIR: BLUEPRINTREV: 10 FINALSCOPE: tip 0.17.0 / CP-0032 → GIA-COSBASELINE: ver=0.17.0 tip=35d3e42 cp=CP-0032 pytest=504/0 audit=PASS dual_primary=0 release_closed=0.16.3STATUS: FINAL_DELIVERY_TO_OPERATOR

Q1) IS_REV9_AT_MAX_POTENTIAL: NO

Rev9 had no final gate matrix table; gates were prose in the tree.

No frozen residual-risk register with owners and deadlines.

No explicit operator-decision queue; open items were mixed with engineering gaps.

No final milestone→gate traceability table.

No FINAL freeze semantics declared (next rev would still churn).

MAX_POTENTIAL_SELF_SCORE: 97/100Justify: Rev10 freezes the blueprint, adds milestone table, unlock gate matrix, residual risk register, and operator-decision queue. Loses 3 points because consensus is deliberately unpicked (M1 scorecard only), council humans are roles not named, C1 wording is candidate draft not council-approved, and WAN thresholds are ratifiable defaults not ratified.

GAPS_CLOSED_THIS_ROUND:

FINAL freeze semantics declared.

Milestone table with exit tests + unlock prereqs.

Unlock gate matrix with evidence, order, quorum, status.

Operator-decision queue separated from engineering gaps.

Residual risk register frozen.

GAPS_REMAINING (open governance decisions, not engineering gaps):

M1 consensus choice (scorecard ready; choice pending).

Council humans unnamed (roles assigned).

C1 wording pending council approval.

WAN thresholds pending GOV.2 ratification.

Relay economics neutralized, not settled.

Schema-gated debt deadline pending waiver/resolution by 0.18.x entry.

LEGEND: D=docs, S=schema, C=CLI, T=test(+neg), R=RFC, P=policy, CT=CP theme

ROOT TREE (FINAL)

GIA-COS [HOLD]│ P0.1..P0.12 measurable proxies (no AGI language)│├── L7 ADVERSARY_MODEL [MISSING]│ ├── A1 classes → D:docs/security/adversary-v1.md│ ├── A2 capabilities → same D│ ├── A3 success criteria → same D│ ├── A4 defenses/layer → P:docs/security/defense-matrix-v1.md│ ├── A5 non-defenses → P:same│ ├── A6 tests → T:tests/adversary/* (T-A1..A6, +neg)│ └── ABORT: class hits success criterion → block CP mint│├── L6 CONSCIOUSNESS_CLAIM_POLICY [MISSING]│ ├── C1 wording+falsifiers → D:docs/policy/consciousness-claim-v1.md│ │ candidate draft + F-C1.1..F-C1.6 + kill-switch│ ├── C2 council charter → D:docs/policy/council-charter-v1.md│ ├── C3 revocation → D:docs/policy/claim-revocation-v1.md│ ├── C4 rule: no claim without C1∧C2∧C3│ ├── C5 default forbidden│ └── C6 language discipline → C:mesh-lint --forbid-words + human note│└── L5 GIA_SURFACE [MISSING]├── I1 identity+attestation+tiers│ ├── a node_key → S:schema/identity/v1│ ├── b attestation → S:same + C:mesh id attest│ ├── c tiers T0..T3 → P:docs/policy/trust-tiers-v1.md│ ├── d rotation → C:mesh id rotate + T:T-I1b(+neg)│ ├── e revocation → C:mesh id revoke + T:T-I1c(+neg)│ ├── f downgrade path → P-10│ └── ABORT → pinned-only├── I2 CONTROL-PLANE API│ ├── a verbs → S:schema/controlplane/v1│ ├── b idempotency → S:same + T:T-I2a(+neg)│ ├── c error taxonomy → S:same + T:T-I2b(+neg)│ ├── d rate limits → P:docs/ops/rate-limits-v1.md│ ├── e CLI → C:mesh ctl {join|leave|drain|status|query|pause|resume|kill}│ └── f concurrency → D:docs/ops/ctl-concurrency-v1.md├── I3 MEMORY/STATE FABRIC│ ├── a classes S0..S3 → D:docs/state/classes-v1.md│ ├── b read semantics → S:schema/state/v1│ ├── c write idem → S:same + T:T-I3b(+neg)│ ├── d observe → S:schema/observe/v1│ ├── e retention → P:docs/state/retention-v1.md│ ├── f repair → C:mesh state repair + T:T-I3c(+neg)│ └── g provenance → S:schema/provenance/v1├── I4 ACTION BOUNDARY│ ├── a classes A0..A4 → P:docs/actions/classes-v1.md│ ├── b capability tokens → S:schema/capability/v1│ ├── c forbidden list → P:same (PERMANENT)│ ├── d tool registry → S:schema/tools/v1 + C:mesh tools list│ ├── e dry-run required → P:same + T:T-I4c(+neg)│ └── CLI → C:mesh act --class A{n}├── I5 HUMAN OVERSIGHT│ ├── a approve/deny → C:mesh oversight approve|deny│ ├── b pause → C:mesh ctl pause + T:T-I5a(+neg) SLO 2s/10s│ ├── c kill w/ quorum → C:mesh ctl kill --quorum + T:T-I5b(+neg)│ ├── d dead-man → P:docs/oversight/deadman-v1.md + T:T-I5c(+neg)│ ├── e quorum-human → P:same│ └── f revoke consent → C:mesh consent revoke + T:T-I5d(+neg)├── I6 AUDITABILITY│ ├── a hash-chain → S:schema/audit/v1│ ├── b tamper-evident → T:T-I6a(+neg)│ ├── c tamper-resistant → P:docs/audit/rep-v1.md + T:T-I6b(+neg)│ ├── d queryable → C:mesh audit query│ ├── e forget → C:mesh audit forget + T:T-I6c(+neg)│ └── f no-audit=no-action → P:same├── I7 TRANSPORT│ ├── a NAT classes → D:docs/wan/nat-taxonomy-v1.md│ ├── b mapping table → D:same│ ├── c relay profile → D:docs/wan/relay-profile-v1.md│ ├── d latency bands → D:docs/wan/latency-bands-v1.md + T:T-I7c(+neg)│ └── e partition model → D:docs/wan/partition-v1.md + T:T-I7d(+neg)├── I8 KEY ROTATION → R:rfc/0004-key-rotation.md + T:T-I8a,b(+neg)├── I9 UPGRADE/ROLLBACK → R:rfc/0005-upgrade-rollback.md + T:T-I9a..c(+neg)├── I10 FALSIFIER SPEC → T:tests/falsifiers/gia/*│ F1..F10 with expected signals└── I11 invariant: claim without test = INVALID → P│└── L4 MULTI_NODE_SCALE [NO_HELD]├── M1 consensus choice → R:rfc/0001-consensus-choice.md│ scorecard ≥80 to ratify; no candidate → written justification├── M2 membership+rejoin → R:rfc/0002-membership.md + T:T-M2a,b(+neg)├── M3 WAN model → D:docs/wan/partition-v1.md├── M4 N3 partition_suite → T:tests/n3/partition_suite├── M5 reconciliation → R:rfc/0003-reconciliation.md (gated)├── M6 scale evidence → T:tests/n3/soak_* + rollback├── M7 no M4+ without M1+M2+M3 ratified → P└── ABORT: M1..M3 fail review → N stays 2│└── L3 GATES+GOV├── GOV.1 composition → D:docs/policy/council-charter-v1.md├── GOV.2 quorum: 3/4 unlock; GIA unanimous; N=2 adds both nodes├── GOV.3 evidence bundle → S:schema/evidence-bundle/v1├── GOV.4 mechanical removal → C:mesh gov unlock├── GOV.5 reversal → P├── GOV.6 no prose unlock → P├── GOV.7 schema-debt deadline at 0.18.x entry├── CRITICAL_PATH:│ CP-0032→P30→P31→P32→P33→P34→H1→H2→H3→H4→H5→H6→H7→H8→│ A1→A2→A3→A4→I2→I3→I4→I5→I6→I8→I9→I7→M1→M2→M3→M4→M6→│ I1→I10→C1→C2→C3→GIA-COS└── RULE: unlock = CP bundle + GOV.2 quorum│└── L2 NERVOUS_HARDENING [PARTIAL]├── H1 identity+attestation+tiers → T:T-I1a..e(+neg) ABORT→pinned-only├── H2 recovery+rebuild → T:T-H2a..d(+neg) ABORT→snapshot restore├── H3 dual-primary fence → T:T-H3a..c(+neg) ABORT→demote+re-elect├── H4 OBS telemetry → S:schema/obs/v1 + T:T-H4a..d(+neg)├── H5 packaging distribution → S:schema/bundle/v1 + T:T-H5a..f(+neg)├── H6 minority_write@N2 → T:T-H6a(+neg) ABORT→halt writes├── H7 clock_skew@N2 → T:T-H7a(+neg) ABORT→refuse join└── H8 manifest parity@N2 → T:T-H8a(+neg) ABORT→reject build│└── L1 REMAINING_0.17 [OPEN]├── R1 ops UX → C:mesh ctl|status|trace|pause|kill T:T-R1a..c(+neg) ABORT→read-only├── R2 obs peers → D:docs/ops/obs-peers-v1.md + UI T:T-R2a..b(+neg) ABORT→single-node view├── R3 quickstart → C:quickstart.sh + D:docs/quickstart T:T-R3a..b(+neg) ABORT→EXPERIMENTAL├── R4 soak P30 → T:T-R4a..c(+neg) ABORT→revert node 0.16.3├── R5 audit P31 → T:T-R5a..f(+neg) ABORT→rc1 tag void├── R6 freeze P32 → CT:freeze_n2 ABORT→unfreeze└── R7 install/signoff P33,P34 → T:T-R7a..c(+neg) ABORT→keep 0.16.3 stable│└── L0 HAVE (0.17.0/CP-0032) [DONE]runtime WAL+fsync; N=1 (0.16.3 closed); N=2 manifest v1-n2 + install + rollback;packaging single+N2; OBS single+basic N2; TLS helpers;process CP-0001..0032 / 504/0 / audit PASS; SLO batch+recovery=MET;majority=fenced_primary_heal_NOT_Raft

MILESTONE TABLE

UNLOCK GATE MATRIX

PERMANENT_NO_HELDsilent_plaintext, SLO_chase, silent_dual_primary, silent_minority_write,consensus_equals_Raft, consciousness_claim_without_C1..C6,unauthenticated_peer, upgrade_without_drain, unlogged_action,consciousness_language_outside_L6, witness_collusion_allowed,wall_clock_as_authority

UNLOCKABLE_NO_HELDRaft, N>2, multi-primary, ML, R2, R3, Vault-ACME-req, GIA, tag_schema, EVERY_fsync

RESIDUAL RISKS (FINAL)├── RK1..RK50 retained├── RK51 Council vacancy stalls unlock → GOV.1 vacancy rule├── RK52 C1 wording overclaims → P-17 falsifiers + kill-switch├── RK53 Consensus chosen by vibes → P-18 scorecard ≥80├── RK54 Relay single-operator capture → P-19 multi-relay + domain diversity├── RK55 WAN thresholds unfalsifiable → P-20 measurement method└── RK56 Schema-debt drift forever → GOV.7 hard deadline

NEXT (Cycle 29, non-NO_HELD only)└── P30_n2_soak_stability

M2M_v1 VERDICT=BLUEPRINT_REV10_FINAL; NEXT=P30_n2_soak_stability
