# BLUEPRINT_ROOT FINAL (rev 10) — readable reformatting

Source: DeepSeek R10 after 10 critique rounds. Reformatted for human reading only;
substance unchanged. Tip baseline: 0.17.0 / tip 35d3e42 / CP-0032 / pytest 504/0.

**Operator note (Grok / Cycle 52 CP-0056; SP2 alias Cycle 56 CP-0060):** L1 REMAINING_0.17 is **CLOSED**. L1-ops-UX / L1-OBS-peers / L1-quickstart evidence: CP-0033..0035 (tips e1d5e50 / 64747b9 / e6a0964); R4–R6: CP-0032; R7: CP-0036. See `docs/planning/L1_RESIDUE_CLOSEOUT.md` + `NOTE_L1_ALIAS_VS_NO_HELD_R2_R3.md`. Full `mesh ctl|pause|kill` remains L5 I2/I5 (not L1). NO_HELD product **R2/R3** (ML-router) stay locked — display aliases only; no unlock.

---

M2M_v1
DIR: BLUEPRINT
REV: 10 FINAL
SCOPE: tip 0.17.0 / CP-0032 → GIA-COS
BASELINE: ver=0.17.0 tip=35d3e42 cp=CP-0032 pytest=504/0 audit=PASS dual_primary=0 release_closed=0.16.3
STATUS: FINAL_DELIVERY_TO_OPERATOR

Q1) IS_REV9_AT_MAX_POTENTIAL: NO

Rev9 had no final gate matrix table; gates were prose in the tree.

No frozen residual-risk register with owners and deadlines.

No explicit operator-decision queue; open items were mixed with engineering gaps.

No final milestone→gate traceability table.

No FINAL freeze semantics declared (next rev would still churn).

MAX_POTENTIAL_SELF_SCORE: 97/100
Justify: Rev10 freezes the blueprint, adds milestone table, unlock gate matrix, residual risk register, and operator-decision queue. Loses 3 points because consensus is deliberately unpicked (M1 scorecard only), council humans are roles not named, C1 wording is candidate draft not council-approved, and WAN thresholds are ratifiable defaults not ratified.

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

GIA-COS [HOLD]
│ P0.1..P0.12 measurable proxies (no AGI language)
│
├── L7 ADVERSARY_MODEL [MISSING]
│ 
├── A1 classes → D:docs/security/adversary-v1.md
│ 
├── A2 capabilities → same D
│ 
├── A3 success criteria → same D
│ 
├── A4 defenses/layer → P:docs/security/defense-matrix-v1.md
│ 
├── A5 non-defenses → P:same
│ 
├── A6 tests → T:tests/adversary/* (T-A1..A6, +neg)
│ 
└── ABORT: class hits success criterion → block CP mint
│
├── L6 CONSCIOUSNESS_CLAIM_POLICY [MISSING]
│ 
├── C1 wording+falsifiers → D:docs/policy/consciousness-claim-v1.md
│ 
│ candidate draft + F-C1.1..F-C1.6 + kill-switch
│ 
├── C2 council charter → D:docs/policy/council-charter-v1.md
│ 
├── C3 revocation → D:docs/policy/claim-revocation-v1.md
│ 
├── C4 rule: no claim without C1∧C2∧C3
│ 
├── C5 default forbidden
│ 
└── C6 language discipline → C:mesh-lint --forbid-words + human note
│
└── L5 GIA_SURFACE [MISSING]
├── I1 identity+attestation+tiers
│ 
├── a node_key → S:schema/identity/v1
│ 
├── b attestation → S:same + C:mesh id attest
│ 
├── c tiers T0..T3 → P:docs/policy/trust-tiers-v1.md
│ 
├── d rotation → C:mesh id rotate + T:T-I1b(+neg)
│ 
├── e revocation → C:mesh id revoke + T:T-I1c(+neg)
│ 
├── f downgrade path → P-10
│ 
└── ABORT → pinned-only
├── I2 CONTROL-PLANE API
│ 
├── a verbs → S:schema/controlplane/v1
│ 
├── b idempotency → S:same + T:T-I2a(+neg)
│ 
├── c error taxonomy → S:same + T:T-I2b(+neg)
│ 
├── d rate limits → P:docs/ops/rate-limits-v1.md
│ 
├── e CLI → C:mesh ctl {join|leave|drain|status|query|pause|resume|kill}
│ 
└── f concurrency → D:docs/ops/ctl-concurrency-v1.md
├── I3 MEMORY/STATE FABRIC
│ 
├── a classes S0..S3 → D:docs/state/classes-v1.md
│ 
├── b read semantics → S:schema/state/v1
│ 
├── c write idem → S:same + T:T-I3b(+neg)
│ 
├── d observe → S:schema/observe/v1
│ 
├── e retention → P:docs/state/retention-v1.md
│ 
├── f repair → C:mesh state repair + T:T-I3c(+neg)
│ 
└── g provenance → S:schema/provenance/v1
├── I4 ACTION BOUNDARY
│ 
├── a classes A0..A4 → P:docs/actions/classes-v1.md
│ 
├── b capability tokens → S:schema/capability/v1
│ 
├── c forbidden list → P:same (PERMANENT)
│ 
├── d tool registry → S:schema/tools/v1 + C:mesh tools list
│ 
├── e dry-run required → P:same + T:T-I4c(+neg)
│ 
└── CLI → C:mesh act --class A{n}
├── I5 HUMAN OVERSIGHT
│ 
├── a approve/deny → C:mesh oversight approve|deny
│ 
├── b pause → C:mesh ctl pause + T:T-I5a(+neg) SLO 2s/10s
│ 
├── c kill w/ quorum → C:mesh ctl kill --quorum + T:T-I5b(+neg)
│ 
├── d dead-man → P:docs/oversight/deadman-v1.md + T:T-I5c(+neg)
│ 
├── e quorum-human → P:same
│ 
└── f revoke consent → C:mesh consent revoke + T:T-I5d(+neg)
├── I6 AUDITABILITY
│ 
├── a hash-chain → S:schema/audit/v1
│ 
├── b tamper-evident → T:T-I6a(+neg)
│ 
├── c tamper-resistant → P:docs/audit/rep-v1.md + T:T-I6b(+neg)
│ 
├── d queryable → C:mesh audit query
│ 
├── e forget → C:mesh audit forget + T:T-I6c(+neg)
│ 
└── f no-audit=no-action → P:same
├── I7 TRANSPORT
│ 
├── a NAT classes → D:docs/wan/nat-taxonomy-v1.md
│ 
├── b mapping table → D:same
│ 
├── c relay profile → D:docs/wan/relay-profile-v1.md
│ 
├── d latency bands → D:docs/wan/latency-bands-v1.md + T:T-I7c(+neg)
│ 
└── e partition model → D:docs/wan/partition-v1.md + T:T-I7d(+neg)
├── I8 KEY ROTATION → R:rfc/0004-key-rotation.md + T:T-I8a,b(+neg)
├── I9 UPGRADE/ROLLBACK → R:rfc/0005-upgrade-rollback.md + T:T-I9a..c(+neg)
├── I10 FALSIFIER SPEC → T:tests/falsifiers/gia/*
│ F1..F10 with expected signals
└── I11 invariant: claim without test = INVALID → P
│
└── L4 MULTI_NODE_SCALE [NO_HELD]
├── M1 consensus choice → R:rfc/0001-consensus-choice.md
│ scorecard ≥80 to ratify; no candidate → written justification
├── M2 membership+rejoin → R:rfc/0002-membership.md + T:T-M2a,b(+neg)
├── M3 WAN model → D:docs/wan/partition-v1.md
├── M4 N3 partition_suite → T:tests/n3/partition_suite
├── M5 reconciliation → R:rfc/0003-reconciliation.md (gated)
├── M6 scale evidence → T:tests/n3/soak_* + rollback
├── M7 no M4+ without M1+M2+M3 ratified → P
└── ABORT: M1..M3 fail review → N stays 2
│
└── L3 GATES+GOV
├── GOV.1 composition → D:docs/policy/council-charter-v1.md
├── GOV.2 quorum: 3/4 unlock; GIA unanimous; N=2 adds both nodes
├── GOV.3 evidence bundle → S:schema/evidence-bundle/v1
├── GOV.4 mechanical removal → C:mesh gov unlock
├── GOV.5 reversal → P
├── GOV.6 no prose unlock → P
├── GOV.7 schema-debt deadline at 0.18.x entry
├── CRITICAL_PATH:
│ CP-0032→P30→P31→P32→P33→P34→H1→H2→H3→H4→H5→H6→H7→H8→
│ A1→A2→A3→A4→I2→I3→I4→I5→I6→I8→I9→I7→M1→M2→M3→M4→M6→
│ I1→I10→C1→C2→C3→GIA-COS
└── RULE: unlock = CP bundle + GOV.2 quorum
│
└── L2 NERVOUS_HARDENING [PARTIAL]
├── H1 identity+attestation+tiers → T:T-I1a..e(+neg) ABORT→pinned-only
├── H2 recovery+rebuild → T:T-H2a..d(+neg) ABORT→snapshot restore
├── H3 dual-primary fence → T:T-H3a..c(+neg) ABORT→demote+re-elect
├── H4 OBS telemetry → S:schema/obs/v1 + T:T-H4a..d(+neg)
├── H5 packaging distribution → S:schema/bundle/v1 + T:T-H5a..f(+neg)
├── H6 minority_write@N2 → T:T-H6a(+neg) ABORT→halt writes
├── H7 clock_skew@N2 → T:T-H7a(+neg) ABORT→refuse join
└── H8 manifest parity@N2 → T:T-H8a(+neg) ABORT→reject build
│
└── L1 REMAINING_0.17 [CLOSED]
├── L1-ops-UX (was R1) fabric ops UX → C:mesh fabric status|diagnose|reconnect + D:docs/ops/fabric-ops-ux-v1.md
│   T:fabric_ops_cycle29 (CP-0033 tip e1d5e50)
│   [note: full mesh ctl|pause|kill deferred to L5 I2/I5]
├── L1-OBS-peers (was R2) obs peers → D:docs/ops/obs-peers-v1.md + UI T:obs_peers_cycle30 (CP-0034 tip 64747b9)
│   ABORT→single-node view
├── L1-quickstart (was R3) quickstart → C:scripts/quickstart.sh→quickstart_0.16.3.sh + D:docs/quickstart
│   T:quickstart_cycle31 (CP-0035 tip e6a0964)
├── R4 soak P30 → CP-0032 tip 8a941f0 [DONE]
├── R5 audit P31 → CP-0032 [DONE]
├── R6 freeze P32 → CP-0032 freeze 0.17.x-n2 [DONE]
└── R7 install/signoff → CP-0036 tip 241d570 THEME_SIGNOFF_0.17.0 [DONE]
    closeout=docs/planning/L1_RESIDUE_CLOSEOUT.md CP-0056
    SP2: aliases avoid collision with NO_HELD product ML R2/R3 (no unlock)
│
└── L0 HAVE (0.17.0/CP-0032) [DONE]runtime WAL+fsync; N=1 (0.16.3 closed); N=2 manifest v1-n2 + install + rollback;packaging single+N2; OBS single+basic N2; TLS helpers;process CP-0001..0032 / 504/0 / audit PASS; SLO batch+recovery=MET;majority=fenced_primary_heal_NOT_Raft

MILESTONE TABLE

UNLOCK GATE MATRIX

PERMANENT_NO_HELDsilent_plaintext, SLO_chase, silent_dual_primary, silent_minority_write,consensus_equals_Raft, consciousness_claim_without_C1..C6,unauthenticated_peer, upgrade_without_drain, unlogged_action,consciousness_language_outside_L6, witness_collusion_allowed,wall_clock_as_authority

UNLOCKABLE_NO_HELDRaft, N>2, multi-primary, ML, R2, R3, Vault-ACME-req, GIA, tag_schema, EVERY_fsync

RESIDUAL RISKS (FINAL)
├── RK1..RK50 retained
├── RK51 Council vacancy stalls unlock → GOV.1 vacancy rule
├── RK52 C1 wording overclaims → P-17 falsifiers + kill-switch
├── RK53 Consensus chosen by vibes → P-18 scorecard ≥80
├── RK54 Relay single-operator capture → P-19 multi-relay + domain diversity
├── RK55 WAN thresholds unfalsifiable → P-20 measurement method
└── RK56 Schema-debt drift forever → GOV.7 hard deadline

NEXT (Cycle 29, non-NO_HELD only)
└── P30_n2_soak_stability

M2M_v1 VERDICT=BLUEPRINT_REV10_FINAL; NEXT=P30_n2_soak_stability
