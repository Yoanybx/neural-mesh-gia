# M2 Membership + Rejoin — Design-Only State Machine

**Status:** DESIGN MATURED (no membership runtime; no N>2 topology)  
**Cycle / Checkpoint:** 55 / CP-0059  
**Date:** 2026-09-26 America/New_York (EDT)  
**Theme:** `M2_membership_rejoin_DESIGN` (0.19_SCOPE_FROZEN theme D / blueprint L4 M2)  
**Authority:** DeepSeek C54 NEXT Option1 (ranked)  
**Prior pointer:** `M2_MEMBERSHIP_REJOIN_POINTER.md` (CP-0050) — superseded for design content; kept as historical stub  
**Target RFC (later):** `rfc/0002-membership.md`  
**ABORT rule:** M1..M3 fail review → N stays 2  
**Runtime:** Raft / N>2 / multi-primary / M4+ remain **NO_HELD**

---

## 1. Intent

Produce a **ratifiable membership + rejoin state machine** that:

1. Defines who may join, attest, serve, drain, leave, and rejoin under **N≤2**.
2. **Composes with H1** identity + attestation + trust tiers T0..T3 (already shipped CP-0038).
3. Remains **orthogonal to M1** consensus choice (`NO_CONSENSUS_YET`): membership does not pick Raft or unlock N>2.
4. Gives M3 a clear actor set for partition modeling (design-only prerequisite).

This CP does **not** implement a membership service, does **not** open N>2, and does **not** claim Raft/quorum membership.

---

## 2. State machine (canonical)

```
JOINING → ATTESTING → ACTIVE → DRAINING → LEFT → REJOIN
                                              └──────────────┘
                         (REJOIN is a labeled re-entry into JOINING)
```

| State | Meaning | Write authority | Peer visibility |
|-------|---------|-----------------|-----------------|
| **JOINING** | Node declared intent; identity record may be T0/T1; no fabric write authority | none | probe-only / OBS join intent |
| **ATTESTING** | Local-CA attestation in progress (H1 `mesh id attest`); CN/SAN must match `node_id` | none | probe + attest exchange |
| **ACTIVE** | Attested (≥T2); participating in N≤2 fabric under existing fence semantics | per role (primary/secondary) under H3/H6 | full peer |
| **DRAINING** | Operator-initiated graceful leave; no new writes accepted; finish in-flight | drain-only / read-ok | peer marked draining |
| **LEFT** | Cleanly departed; fingerprint retained; no join authority until REJOIN | none | historical |
| **REJOIN** | Labeled re-entry: same as JOINING with prior fingerprint/history attached | none | same as JOINING |

**Label note:** `REJOIN` is a **transition label / entry mode**, not a long-lived hold state. Implementations MAY model it as `JOINING` with `rejoin=true` on the membership record. Design diagrams keep the six-name sequence DeepSeek specified for clarity.

### Happy-path transitions

| From | Event | To | Guards |
|------|-------|----|--------|
| (none) | `join_intent` | JOINING | `dual_primary=0`; N≤2; plaintext forbidden |
| JOINING | `begin_attest` | ATTESTING | identity record exists; not revoked |
| ATTESTING | `attest_ok` (≥T2) | ACTIVE | local-CA verify; CN/SAN=`node_id`; not pinned-only unless pin∈set |
| ACTIVE | `drain` | DRAINING | operator or policy; fence not already dual-primary abort |
| DRAINING | `drain_complete` | LEFT | no in-flight writes; receipts sealed |
| LEFT | `rejoin_intent` | REJOIN→JOINING | prior fingerprint retained; revoke list clear for this fp or new leaf |
| REJOIN/JOINING | (same as JOINING) | ATTESTING… | full re-attest required (no silent resume as ACTIVE) |

### Negative / ABORT transitions

| From | Event | Effect | Code |
|------|-------|--------|------|
| JOINING / ATTESTING | attest mismatch / CA fail | ABORT→pinned-only (H1); stay out of ACTIVE | `MEMBER_ATTEST_FAIL` |
| any | plaintext trust claim | refuse | `MEMBER_PLAINTEXT_FORBIDDEN` |
| JOINING | N would exceed 2 | refuse join | `MEMBER_N_GT2_REFUSED` |
| ACTIVE | dual_primary detected | H3 demote+re-elect path; membership stays ACTIVE only if fence clears | `FENCE` (H3) |
| ACTIVE | minority primary under partition | H6 halt writes | `MINORITY_WRITE_HALT` (H6) |
| JOINING / ATTESTING | clock skew beyond policy | H7 refuse join | `CLOCK_SKEW_REFUSE` (H7) |
| any → ACTIVE | manifest parity fail | H8 reject build / refuse activate | `MANIFEST_PARITY_REJECT` (H8) |
| DRAINING | drain timeout with loss risk | ABORT drain; remain DRAINING or force LEFT with audit flag | `MEMBER_DRAIN_ABORT` |
| LEFT | rejoin while revoked | refuse | `MEMBER_REVOKED` |
| ACTIVE | silent tier downgrade on rotate | forbidden (H1 P-10); membership unchanged until explicit | `IDENTITY_NO_SILENT_DOWNGRADE` |

---

## 3. Composition with H1 tiers (T0..T3)

Membership **does not redefine** trust tiers. It **consumes** them:

| Membership state | Allowed tiers | Notes |
|------------------|---------------|-------|
| JOINING | T0, T1 | T0 = unknown/untrusted; T1 = provisional TOFU |
| ATTESTING | T0→T2 path | Success lifts to ≥T2; failure → pinned-only |
| ACTIVE | **T2 or T3 only** | T3 preferred for operator-pinned peers |
| DRAINING | T2 or T3 | Tier retained; no silent drop |
| LEFT | any (historical) | Revoke forces T0 + refuse REJOIN until cleared |
| REJOIN | start at recorded prior; must re-attest to ≥T2 | No shortcut ACTIVE |

**Invariant:** `ACTIVE ⇒ tier ∈ {T2, T3}`. Violating this is a design bug / ABORT.

---

## 4. Invariants (design-time)

1. **`dual_primary = 0`** on every membership record and transition receipt.
2. **`n_members_active ≤ 2`** (runtime N>2 remains NO_HELD; join that would exceed is refused).
3. **No silent ACTIVE resume** after LEFT — REJOIN must pass ATTESTING again.
4. **No Raft / quorum membership protocol** — N=2 fenced_primary_heal remains the operational majority story.
5. **Orthogonal to M1** — membership SM does not select C1..C5; `NO_CONSENSUS_YET` unchanged.
6. **Plaintext forbidden** for membership trust claims (`MEMBER_PLAINTEXT_FORBIDDEN`).
7. **Audit:** every transition emits a hash-chained receipt field set (design; runtime later).
8. **Drain no-loss (design goal T-M2b):** DRAINING MUST NOT acknowledge leave while unreplicated durable writes remain (ties to existing N=2 CRAM / anti-entropy rejoin notes — no new runtime here).

---

## 5. Record sketch (design schema)

See `docs/schema/membership/v0.md` (`mesh.membership/v0`).

Minimal fields:

| Field | Type | Notes |
|-------|------|-------|
| `schema` | string | `mesh.membership/v0` |
| `node_id` | string | = cert CN/SAN |
| `state` | enum | JOINING\|ATTESTING\|ACTIVE\|DRAINING\|LEFT\|REJOIN |
| `tier` | enum | T0..T3 (from H1) |
| `rejoin` | bool | true when entered via REJOIN label |
| `fingerprint` | string | leaf fp |
| `prior_fingerprints` | list | retained on rotate/rejoin |
| `dual_primary` | int | **always 0** |
| `n_cap` | int | **always 2** (hard design cap while NO_HELD) |
| `receipt_prev` / `receipt_hash` | string | audit chain placeholders |

---

## 6. Test plan (mock / design-only — this CP)

| ID | Case | Expect |
|----|------|--------|
| T-M2a | `rejoin_state_machine` happy path | JOINING→…→LEFT→REJOIN→JOINING→…→ACTIVE |
| T-M2a-neg-1 | attest fail | never ACTIVE; ABORT code set |
| T-M2a-neg-2 | N>2 join attempt | `MEMBER_N_GT2_REFUSED` |
| T-M2a-neg-3 | plaintext claim | `MEMBER_PLAINTEXT_FORBIDDEN` |
| T-M2a-neg-4 | ACTIVE with T0/T1 | rejected by invariant |
| T-M2a-neg-5 | LEFT→ACTIVE shortcut | rejected; must REJOIN |
| T-M2b | `drain_no_loss` (mock) | drain_complete refused while `pending_writes>0` |
| T-M2b-neg | drain timeout | `MEMBER_DRAIN_ABORT` |

Runtime fabric membership service remains **out of scope**. Helpers in
`neural_mesh.packaging.m2_membership_rejoin` are **pattern mocks** only.

---

## 7. Relation to M1 / M3 / blueprint

| Item | Status after this CP |
|------|----------------------|
| M1 scorecard | unchanged; **NO_CONSENSUS_YET**; checklist "M2 SM draft exists" → **yes** |
| M2 pointer | design matured here; pointer retained as stub |
| M3 WAN+HLC | design matured CP-0060 (`M3_WAN_MODEL_DESIGN.md`); pointer retained as stub |
| M4+ | NO_HELD until M1+M2+M3 ratified |
| Blueprint L4 M2 | design artifact toward future `rfc/0002-membership.md` |

---

## 8. Non-goals

- Implementing membership runtime / ctl join|leave service
- Opening N>2 topology or Raft/Paxos membership
- Multi-primary reconciliation (M5 NO_HELD)
- GIA / train / SaaS / economy
- Changing H1 tier semantics
- Claiming world-scale cluster membership

**NO_HELD:** Raft,N>2,multi-primary,ML,R2,R3,plaintext,Vault-ACME-req,GIA,SLO_chase,tag_schema,EVERY_fsync

---

## Related

- `docs/design/fabric/M2_MEMBERSHIP_REJOIN_POINTER.md` (historical stub)
- `docs/design/fabric/M1_CONSENSUS_CHOICE_DESIGN.md` / `M1_SCORECARD_MATURATION.md`
- `docs/design/fabric/M3_WAN_PARTITION_HLC_POINTER.md`
- `docs/capabilities/MESH_IDENTITY_ATTESTATION.md` (H1)
- `docs/policy/trust-tiers-v1.md`
- `docs/planning/0.19_SCOPE_FROZEN.md`
- `council/DEEPSEEK_REPLY_CYCLE54.md` (Option1)
