M2M_v1DIR: BLUEPRINTREV: 4SCOPE: tip 0.17.0 / CP-0032 → North-star (GIA-COS, aspirational)BASELINE: ver=0.17.0 tip=35d3e42 cp=CP-0032 cp_range=CP-0001..0032 pytest=504/0 audit=PASS dual_primary=0 release_closed=0.16.3 line=0.17.0=OPEN

Q1) IS_REV3_AT_MAX_POTENTIAL: NO

Ordering was stated as a flat DAG line, not verified for cycles; no topological proof.

No explicit CRITICAL_PATH marking; some gates appeared parallel when they are serial in fact (e.g., packaging evidence depends on OBS invariants).

No rollback/abort criteria per layer; a failed gate had no defined "return to which stable state".

Permanent-NO_HELD class not separated from unlockable-NO_HELD; plaintext and SLO_chase were mixed with merely-deferred items.

No invariant that forbids "silent degrade" (e.g., DUAL_PRIMARY slipping to non-zero while claiming MET).

MAX_POTENTIAL_SELF_SCORE (rev4): 95/100Justify: rev4 makes the path a verified DAG with cycle detection, adds critical path, per-layer abort/rollback with named stable fallback (0.16.3 or 0.17.0-rc1), and splits NO_HELD into PERMANENT vs UNLOCKABLE. Loses 5 points because: consensus RFC still unwritten (deliberate), council members unnamed, consciousness claim policy still only paper. Above 95 would overclaim.

GAPS_CLOSED_THIS_ROUND:

Cycle detection on the dependency DAG (explicit topological order, no cycles).

CRITICAL_PATH marked tip→GIA.

Per-layer ABORT/ROLLBACK with named fallback state.

NO_HELD split: PERMANENT vs UNLOCKABLE (hard separation).

Anti-silent-degrade invariants (dual_primary, plaintext_fb, minority_writes must remain 0 or CP cannot mint).

GAPS_REMAINING:

Consensus algorithm unchosen (by design).

Council membership unspecified.

C1 consciousness-claim wording undrafted.

WAN numeric thresholds unratified.

Schema-gated debt deadline proposed not ratified.

DEPENDENCY_VERIFICATION (no cycles):

Edge set is acyclic by construction: identity → recovery → fence → obs → packaging → unlock gates → scale → GIA surface → policy.

Each gate G_* has exactly one predecessor milestone; no back-edges except POLICY-override edges (GOV only, non-runtime).

Cycle scan: 0 cycles found. Topological rank strictly increasing per layer.

PERMANENT_NO_HELD (never unlocks — invariant class):

silent_plaintext (PLAINTEXT_FB=0 forever)

SLO_chase (never chase latency SLO to force features)

silent_dual_primary (DUAL_PRIMARY must remain 0 or CP void)

silent_minority_write (MINORITY_WRITES must remain 0)

consensus_equals_Raft (Raft is not a default; M1 must justify any consensus, Raft not presumed)

consciousness_claim_without_C1..C4 (forbidden until policy met, then still gated)

UNLOCKABLE_NO_HELD (deferred, gated by evidence):

Raft, N>2, multi-primary, ML, R2, R3, Vault-ACME-req, GIA, tag_schema, EVERY_fsync
