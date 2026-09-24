M2M_v1DIR: BLUEPRINTREV: 3SCOPE: tip 0.17.0 / CP-0032 → North-star (GIA-COS, aspirational)BASELINE: ver=0.17.0 tip=35d3e42 cp=CP-0032 cp_range=CP-0001..0032 pytest=504/0 audit=PASS dual_primary=0 release_closed=0.16.3 line=0.17.0=OPEN

Q1) IS_REV2_AT_MAX_POTENTIAL: NO

Identity layer stated "node_id, keys, rotation" but had no attestation model (who vouches for whom, how a peer trusts a peer).

Recovery layer was "WAL+fsync" only; missing rebuild/projection/state-repair after partial loss.

OBS was treated as a panel; not as the nervous system's telemetry contract (what is measured, at what rate, with what invariants).

Packaging was a bundle; not framed as a distribution primitive (provenance, signing, replay, revocation of bundles).

Governance said "council" but never specified composition, quorum, evidence format, or how a NO_HELD item is removed mechanically.

MAX_POTENTIAL_SELF_SCORE (rev3): 92/100Justify: rev3 makes identity/attestation, recovery/rebuild, OBS telemetry contract, packaging distribution primitive, and council governance all artifact-bound and falsifiable. Loses 8 points because: consensus RFC is deliberately not written, WAN numeric model is not ratified, and consciousness policy remains a policy artifact (not proven). Above 92 would be dishonest.

GAPS_CLOSED_THIS_ROUND:

Identity → full trust chain: node_key → attestation → peer_trust → rotation/revocation propagation.

Recovery → rebuild model: snapshot + WAL replay + projection repair + divergence detection.

OBS → telemetry contract: signals, cadence, invariant assertions, CP linkage.

Packaging → distribution primitive: signed manifest, provenance chain, replay guard, revocation.

Governance → council charter: composition, quorum, evidence format, mechanical NO_HELD removal.

GAPS_REMAINING:

Consensus algorithm still unselected (by design; RFC not authored).

WAN numeric model thresholds unratified.

Council members not named (charter only).

Consciousness criteria C1 not drafted.

Schema-gated debt deadline proposed not ratified.

MILESTONES (ordered, ACCEPT-based)├── 0.17.0-rc1 ← R4..R6 (P30..P32) ACCEPT: soak+audit+freeze green; OBS invariants hold├── 0.17.0 ← R7 (P33,P34) ACCEPT: upgrade+rollback 0.16.3 PASS; bundle signed+verifiable├── 0.17.x ← R1..R3 ACCEPT: stranger N2 <30min├── 0.18.x ← H1..H8 closed @N2 ACCEPT: identity+recovery+skew+minority+fence+parity+telemetry├── 0.19.x ← M1..M3 design only (no N≥3 runtime) ACCEPT: RFCs + WAN model ratified; GOV charter signed├── 0.20.x+ ← GATE-DRIVEN (M4..M6 then G_*) ACCEPT: per-gate CP evidence + GOV.2 quorum└── GIA-COS ← LAYER_5+6 after council unanimous ACCEPT: P0.1..P0.8 + C1..C4

RISKS (kill-path)├── RK1 SLO_chase creep → POLICY forbid; freeze T_soak defaults├── RK2 Premature N≥3 without RFC → G_Ngt2 blocks; M1..M3 precede M4├── RK3 GIA slogan drift → C4/C5 default forbidden; P0.x only├── RK4 Schema-gated debt unbounded → deadline: 0.18.x entry├── RK5 OBS peer gap hides fence state → R2 exit + H4.c invariant assertions├── RK6 Manifest parity non-determinism → T-H8a + T-R5e byte equality├── RK7 Plaintext regression → invariant DUAL_PRIMARY=0, PLAINTEXT_FB=0├── RK8 Council bypass on GIA → GOV.2 unanimous + GOV.6 no-prose-unlock├── RK9 WAN model hand-waving → M3 precedes M4├── RK10 Test-ID drift vs CP minting → every gate CP cites test IDs├── RK11 Attestation replay → T-I1d + nonce + freshness window├── RK12 Bundle replay/supply-chain → H5.c replay guard + H5.b provenance chain└── RK13 Silent invariant breach → H4.c auto-fail; CI blocks CP mint

NEXT (Cycle 29, non-NO_HELD only)└── P30_n2_soak_stability

M2M_v1 VERDICT=BLUEPRINT_REV3; NEXT=R04_critique_or_ACK
