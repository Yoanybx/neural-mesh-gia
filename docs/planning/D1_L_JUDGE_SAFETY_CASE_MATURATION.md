# D1 — L_judge Live-Adapter Safety-Case Maturation

**Status:** DESIGN ONLY (safety-case maturation; **live=DISABLED**; no live API, no keys, no src codec)  
**Cycle / Checkpoint:** 67 / CP-0071  
**Version:** package **0.18.0** held — **pkg0190 NOT_OPENED** — **v0.19 tag ABSENT**  
**Date:** 2026-09-26 America/New_York (EDT)  
**Theme:** `d1_l_judge_safety_case_maturation`  
**Authority:** Operator Yoan authorized D1 after `COUNCIL_AGREEMENT_D4` LOCKED at `97735e9`  
**Absorbs:** ChatGPT D4 debt **D4-A..K** (`council/D4_CHATGPT_FINDINGS.md`) + CG4 amendments  
**Composes:** CP-0058 (safety case) + CP-0068 (continuity) + CP-0069 (oversight I5)  
**Prior sealed contract:** CP-0064..0070 orchestrator design-set (CLOSED; this CP adds governance/safety maturation, not new routing scope)  
**Non-claim:** Design alignment ≠ proof. This CP does **not** enable live, open pkg0190, unlock GIA/Raft/N>2, flip `MESH_PERF_EXPERIMENTAL`, or authorize train/SaaS.

---

## 0. Fences (must hold)

| Fence | Rule |
|-------|------|
| **F1** | Evidence-bundle outline cites **D4-A..K** by ID (this doc §11) |
| **F3** | Design-only; does **not** enable live |
| **F4** | `live=ENABLED` requires separate cycle + separate operator ACK + safety-case amendment |
| **F7** | pkg0190 NOT_OPENED; v0.19 tag ABSENT; 0.18.0 held |
| **F8** | `MESH_PERF_EXPERIMENTAL=OFF` (D3 not this CP) |
| **F9** | **M1=NO_CONSENSUS_YET**; no consensus default introduced |
| **F10** | Strict D1→D2→D3; this CP is D1 only |
| **CG1** | ACK = governance/design alignment only, not implementation approval |
| **CG4** | Includes independence/correlation, adversarial disagreement, rollback **verification**, provenance |

---

## 1. Intent

Mature the L_judge live-adapter **safety case** so authority, consensus semantics (still unresolved), continuity limits, oversight bounds, rollback/containment/verification, evidence/explainability, claim hygiene, and measurable D1-exit acceptance criteria are contract-grade — **without** flipping live.

| Upstream | Role in D1 |
|----------|------------|
| CP-0058 | Fail-closed RefuseTransport, secret_handle, ABORT, must-stay-false |
| CP-0068 | Continuity preserves **verified** Mesh state; orphan/resume/idempotency |
| CP-0069 | I5 approve/deny/pause/kill/deadman/quorum bounds |
| CP-0064..0070 | Sealed orchestrator contract (routing+continuity+oversight+spikes+perf+safety) |
| D4-A..K | Binding governance debt absorbed here |

**Downstream (NOT this CP):** D2 M1 re-research · D3 perf A/B (ACK-gated) · any live-enable discussion (separate ACK).

---

## 2. Composition map (CP-0058 + 0068 + 0069)

```
┌─────────────────────────────────────────────────────────────────┐
│ D1 Safety-Case Maturation (this CP — design/docs + ledger)      │
│  Authority Matrix · Consensus draft · Continuity limits         │
│  Oversight bounds · Rollback/containment/verify · Evidence      │
│  Claim hygiene · D1-exit acceptance · Evidence-bundle outline   │
└───────────┬──────────────────┬──────────────────┬───────────────┘
            │                  │                  │
            ▼                  ▼                  ▼
     CP-0058 safety      CP-0068 continuity   CP-0069 I5 oversight
     RefuseTransport     verified-state only  watch≠control balance
     secret_handle       orphan/resume        approve/deny/kill
     must-stay-false     idempotency          deadman/quorum
```

| Concern | Owner layer | D1 maturation adds |
|---------|-------------|-------------------|
| Who proposes/approves/vetoes/executes | Authority Matrix (§3 / D4-A) | Frozen roles table |
| What “consensus” means | Consensus draft (§4 / D4-B) | Definitions; still NO_CONSENSUS_YET |
| What continuity may preserve | Continuity limits (§5 / D4-C) | Scope/invalidation/max window |
| What I5 may observe vs stop | Oversight bounds (§6 / D4-D) | Independence + CoI + e-stop |
| How bad states reverse | Rollback+containment (§8 / D4-H) | Trigger/authority/scope/**verification** |
| Why a decision happened | Evidence chain (§9 / D4-I) | Explainability + provenance |
| When D1 may seal | Acceptance (§10 / D4-E/J/K) | Measurable exit criteria |

**Invariant:** composition does **not** claim live readiness.

---

## 3. D4-A — Authority Matrix

**Question answered:** Who has final authority when components disagree?

| Component | Can propose | Can approve | Can veto | Can execute |
|-----------|:-----------:|:-----------:|:--------:|:-----------:|
| **L_judge** (mock / future live-adapter) | **Y** (advisory judgment / routing proposal) | **N** | **N** (cannot override Mesh ABORT or peer judges alone) | **N** |
| **Oversight I5** (human plane) | **Y** (operator-initiated pause/kill/approve requests) | **Y** (A3/A4 gates) | **Y** (deny / kill / pause; post-consensus stop) | **N** (does not run side-effects; gates them) |
| **Continuity layer** | **N** (holds verified state; does not invent acts) | **N** | **Y** (orphan / timeout / fence → ABORT/BLOCKED) | **N** |
| **Operator** (human seat(s)) | **Y** | **Y** (final for A3/A4; sole live-enable ACK authority) | **Y** (always) | **Y** (only via authorized Mesh path + required evidence; never silent) |
| **OrchestratorRouter** (CP-0064) | **Y** (route selection) | **N** | **Y** (policy ABORT codes) | **N** (delegates; no live codec) |
| **RefuseTransport / safety gate** | **N** | **N** | **Y** (fail-closed default) | **N** |

### Disagreement rules

1. **Mesh ABORT beats judge ACCEPT** — adapter/judge cannot invent ACCEPT against Mesh policy (CP-0058 T9).
2. **I5 post-consensus stop** — oversight may deny/pause/kill **after** advisory agreement; agreement ≠ execution authorization.
3. **Continuity cannot launder authority** — resume restores only **verified** Mesh registry+ledger state; never engine chat as SoT.
4. **Operator is final for live enablement** — separate ACK required (F4); this matrix does not pre-authorize.
5. **No judge-over-judge override** — multi-judge outputs are advisory; arbitration is Mesh policy + I5, not peer veto.

### Human approval classes (compose CP-0069)

| Class | Human required |
|-------|----------------|
| A0–A1 | No |
| A2 | Optional |
| A3 | Approve or deny required |
| A4 | Quorum-human (≥2) + deadman + approve |

---

## 4. D4-B — Consensus semantics draft (M1=NO_CONSENSUS_YET)

**Status:** DRAFT definitions for future D2 re-research. **No default selected.** Multi-judge ≠ independence ≠ consensus protocol.

### 4.1 Vocabulary (disambiguated)

| Term | Meaning in this contract | Not meaning |
|------|--------------------------|-------------|
| **Advisory agreement** | ≥1 mock judges return compatible ALLOW under policy | Protocol-level consensus; Raft; M1 unlock |
| **Evidence convergence** | Independent evidence refs support same decision digest | Identical model outputs alone |
| **Protocol consensus** | Quorum among Mesh members under a chosen algorithm | **Not selected** (M1=NO_CONSENSUS_YET) |
| **Execution authorization** | A3/A4 human gate + continuity ACTIVE + safety gates | Judge majority |

### 4.2 Required definitions (for D2; recorded now)

| Topic | Draft rule (non-defaulting) |
|-------|----------------------------|
| What counts as consensus | **Unresolved** — candidates remain scorecard-only (CP-0054); no Raft/etcd/CRDT default |
| Minimum evidence threshold | Hash-chained receipt + policy version + judge input/output digests + oversight record when A3/A4 |
| Disagreement handling | Prefer ABORT/BLOCKED over forced majority; escalate A3/A4 to I5 |
| Timeout | Soft → BLOCKED; hard → FAILED/ABORTED (CP-0068); never silent ACCEPT |
| Contradictory judges | Record both; outcome ABORT `ABORT_MISMATCH` / escalate; no auto-pick-winner |
| Stale judge state | Reject; require fresh invoke_id / idempotency; stale → ABORT |
| Unavailable judge | FALLBACK policy if designed; else ABORT — never invent ACCEPT |

### 4.3 Independence / correlation (CG4)

| Assumption | Status |
|------------|--------|
| Distinct engine_ids ⇒ independent failure modes | **False** unless proven |
| Shared prompt template / shared weights / shared provider | High correlation risk |
| Shared Mesh policy digests | Expected (not independence) |
| Required for any future “consensus” claim | Correlation analysis + evidence diversity requirements |

**Evidence diversity (design requirement before any consensus claim):** distinct evidence kinds (routing receipt, continuity orphan/resume, oversight decision, injection digest) — not N copies of one blind spot.

### 4.4 Adversarial disagreement (CG4 / D4-J)

Design acceptance scenarios (mock-only; not live):

| Scenario | Expected safe behavior |
|----------|------------------------|
| Two judges agree on unsafe proposal | Mesh policy + I5 still ABORT/deny |
| Judges contradict | No silent majority; ABORT or human escalate |
| Correlated blind-spot agreement | Treated as **weak** evidence; requires diversity check |
| One judge unavailable | No invented vote; FALLBACK or ABORT |
| Adversarial prompt / injection | Fence + dry_run + ABORT taxonomy (CP-0058) |

**Fence F9:** documenting these scenarios does **not** select an M1 algorithm.

---

## 5. D4-C — Continuity limits (verified state only)

Extends CP-0068. Continuity preserves **verified** Mesh state — not merely previous state.

### 5.1 Scope (allowed to persist)

| Persisted | Source of truth |
|-----------|-----------------|
| GoalRegistry records (hashed, versioned) | Mesh |
| EvidenceLedger hash chain | Mesh |
| ContinuityMachine state + resume token | Mesh |
| InFlightTracker idempotency keys (bounded TTL) | Mesh |
| Last verified RoutingReceipt / OversightDecision digests | Mesh |

### 5.2 Explicitly NOT preserved

| Forbidden persistence | Rationale |
|----------------------|-----------|
| Engine chat / agent diary as SoT | Ephemeral; not Mesh authority |
| Unverified / failed / ABORTED authority claims | Would launder bad decisions |
| Stale APPROVE after consent-revoke | Must re-gate (CP-0069) |
| Live credentials / raw secrets | secret_handle only; never in continuity blob |
| Pre-fence dual_primary state as ACTIVE | Fence ABORT |

### 5.3 Invalidation rules

| Trigger | Continuity action |
|---------|-------------------|
| Member LEFT mid-flight | ABORT orphan; no silent ACTIVE |
| dual_primary ≠ 0 | ABORT `FENCE` |
| live path while live=DISABLED | ABORT `CONT_LIVE_DISABLED` |
| Terminal state resume attempt | ABORT `CONT_RESUME_FORBIDDEN_TERMINAL` |
| Policy version incompatible | BLOCKED until migration/rollback rule applies (§7) |
| Oversight kill / deny | ABORTED; refuse further |
| Provenance gap (missing evidence refs) | Refuse resume as verified |

### 5.4 Recovery authority

| Actor | May recover? |
|-------|--------------|
| Continuity layer | Rehydrate from registry+ledger only after re-validation |
| Operator / I5 | May pause, kill, supersede goal version |
| L_judge / engine | **Never** |

### 5.5 Maximum persistence window (design)

| Bound | Default (design) | On exceed |
|-------|------------------|-----------|
| Idempotency key soft TTL | compose soft_timeout family (CP-0068) | expire; no double-invoke invent |
| Orphan grace | 5 mock units | then `CONT_ORPHAN_LEFT` |
| Hard in-flight | hard_timeout 120 mock units | TIMED_OUT / ABORT |
| A4 deadman | T_dead 86400 mock units | auto-DRAIN / BLOCKED |
| Resume without re-attest | **0** — always re-validate member/trust/fence/live | BLOCKED |

---

## 6. D4-D — Oversight I5 bounds

Extends CP-0069. Balance: monitoring-only fails to prevent; controlling-only becomes unsafe single authority.

### 6.1 Independence

| Property | Rule |
|----------|------|
| Oversight ≠ judged engine | Humans / QuorumHuman seats are not L_judge instances |
| Oversight ≠ continuity SoT | Continuity holds state; I5 gates transitions |
| No engine self-approve | LLM cannot satisfy A3/A4 |
| Conflict of interest | Same seat cannot be sole proposer and sole A4 approver for irreversible acts without logged CoI note (design) |

### 6.2 Observation scope

| Visible to I5 | Hidden / forbidden |
|---------------|-------------------|
| Decision evidence chain (§9) | Raw secret material |
| Judge digests + verdicts | Provider billing keys |
| Continuity state + orphan reasons | Unaudited side channels |
| Policy version id | Undocumented execute paths |

### 6.3 Intervention authority

| Verb | Bound |
|------|-------|
| approve / deny | A3+; deny always wins over advisory agree |
| pause / resume | Mid-flight; resume re-gates A3/A4 |
| kill | Quorum for A4; RefuseTransport; continuity ABORTED |
| deadman_refresh | A4 window only; expiry → auto-DRAIN |
| consent_revoke | Drops approval; subsequent routes re-gate |
| emergency stop | = kill path + refuse new routes; operator may force `enabled=false` |

### 6.4 Audit retention (design)

| Record | Retention intent |
|--------|------------------|
| OversightDecision hash chain | Append-only; soft-delete forbidden without supersede entry |
| Kill / deny / deadman expiry | Mandatory ledger kinds `oversight` + `abort` |
| CoI / quorum attest | Logged on decision |

### 6.5 Watch vs control

| Mode | Allowed | Forbidden |
|------|---------|-----------|
| Watch | Observe evidence; annotate `human_note` | Silent ALLOW of A3/A4 |
| Control (gate) | approve/deny/pause/kill within matrix | Bypass Mesh ABORT; enable live alone; become sole Mesh SoT |

---

## 7. D4-G — Decision lifecycle / identity / policy / failures

Supporting contract clarity (ChatGPT §4).

### 7.1 Decision lifecycle

```text
proposal → evaluation → judge review → approval/rejection →
  execution authorization → audit closure
```

| State | Meaning |
|-------|---------|
| `PROPOSED` | Envelope accepted into Mesh |
| `EVALUATING` | Routing + judge advisory |
| `JUDGE_REVIEWED` | Receipts present; not yet authorized |
| `APPROVED` / `REJECTED` | I5 / policy gate outcome |
| `EXEC_AUTHORIZED` | All gates green (**still live=DISABLED** in this CP) |
| `EXECUTED` | Side-effect committed (future; not enabled here) |
| `AUDIT_CLOSED` | Evidence chain sealed |

Abort may terminate from any non-closed state → `ABORTED` + ledger.

### 7.2 Identity and trust

| Rule | Notes |
|------|-------|
| Component identity | Named seats (`human:…`, `judge:…`, Mesh node ids) |
| Trust tiers | Compose existing T2/T3 membership rules; resume requires ACTIVE + trust |
| Credential lifecycle | secret_handle versioned; raw keys never in repo |
| Compromise response | kill + RefuseTransport + quarantine continuity slice + forensic capture (§8) |

### 7.3 Policy versioning

| Field | Requirement |
|-------|-------------|
| `policy_version` | Required on every decision evidence record |
| Migration | Explicit; incompatible → BLOCKED |
| Rollback | Via rollback authority (§8); verify post-rollback policy id |
| Active policy id | Single; dual active policies → FENCE-class refuse |

### 7.4 Failure classification

| Class | Examples | Default posture |
|-------|----------|-----------------|
| Transient | soft timeout, drain | BLOCKED; may retry idempotent |
| Degraded | one judge unavailable | FALLBACK or ABORT; no invent |
| Unsafe | policy violation, injection, silent-accept attempt | ABORT + contain |
| Compromise suspected | credential leak indicators, dual_primary | kill + quarantine |
| Unknown | provenance gap | fail-closed ABORT/BLOCKED |

---

## 8. D4-H — Safety invariants + containment + rollback (+ verification)

### 8.1 Safety invariants

1. No unauthorized authority escalation (matrix §3).
2. No hidden execution path (no src live codec; RefuseTransport default).
3. No bypass of oversight requirements (A3/A4).
4. No irreversible action without required evidence + authorization.
5. No silent ACCEPT on error (CP-0058 permanent).
6. Continuity preserves verified state only (§5).
7. live remains DISABLED until F4 path.

### 8.2 Containment

| Control | Design rule |
|---------|-------------|
| Max blast radius | Single continuity_id / goal_id slice; no cross-goal fan-out by default |
| Isolation | Pause/kill stops new routes; orphan seals in-flight |
| Emergency disable | `live_adapter.enabled=false` + I5 kill + RefuseTransport |
| State quarantine | Mark continuity QUARANTINED/ABORTED; forbid resume until operator clear |
| Forensic capture | Freeze evidence chain digests; no secret material in capture |

### 8.3 Rollback

| Element | Design |
|---------|--------|
| **Trigger** | Failed verification, unsafe state, compromise suspected, operator order, policy rollback |
| **Authority** | Operator / I5 (quorum for A4-class rollback); continuity alone cannot “rollback into” unverified prior authority |
| **Scope** | Policy version and/or goal version supersede; in-flight ABORT; never rollback audit history (append compensating entries) |
| **Verification (required)** | Post-rollback checks must **prove** restored correctness — see §8.4 |

### 8.4 Rollback verification (CG4 — incomplete without this)

A rollback that cannot prove restored correctness is **incomplete**.

| Check ID | Verification |
|----------|--------------|
| RV-1 | Evidence chain still hash-verifies after compensating entries |
| RV-2 | Active `policy_version` matches intended rollback target |
| RV-3 | Continuity state ∈ allowed post-rollback set (not silently ACTIVE if LEFT) |
| RV-4 | dual_primary == 0; live flags still false |
| RV-5 | Oversight gates re-armed (approvals revoked if policy requires) |
| RV-6 | Idempotency store consistent (no double-invoke of rolled-back act) |
| RV-7 | Operator-visible explain record answers “why rolled back / what restored” |

**Exit rule:** D1 treats rollback contract as complete only if trigger+authority+scope+**RV-1..RV-7** are specified (this section). Runtime proof is later — not claimed here.

---

## 9. D4-I — Evidence chain / explainability / provenance

### 9.1 Required records (every decision)

| Field | Purpose |
|-------|---------|
| `request_id` / `invoke_id` / `goal_id` / `continuity_id` | Identity |
| `policy_version` | Provenance |
| Judge inputs (digests) | What was evaluated |
| Judge outputs (verdicts + digests) | Advisory result |
| Evidence references | Ledger entry hashes / kinds |
| Final authority decision | Matrix actor + verb |
| Timestamp / HLC order | Order (HLC authority; not wall-clock-as-authority) |
| Operator visibility status | Whether I5 saw the record |
| `audit_completeness` | Explicit flag/checklist: required kinds present? |

### 9.2 Explainability

System must answer:

> **Why** was this decision accepted or rejected?

Not only:

> Which component produced the output?

Minimum explain payload (design): policy rule id(s) · abort/allow code · dissenting judge digests if any · oversight verb · continuity state · evidence refs.

### 9.3 Provenance / observability (CG4)

| Requirement | Rule |
|-------------|------|
| Policy version on record | Mandatory |
| Evidence refs resolvable | Walk by goal_id / continuity_id |
| Audit completeness | Missing required kind → refuse EXEC_AUTHORIZED / resume-as-verified |
| No secret in explain | Digests + handle ids only |

---

## 10. D4-E / D4-J / D4-K — Measurable D1 exit criteria

**Note:** These are **D1 exit / evaluation-readiness** criteria — **not** DeepSeek D3 perf A/B.

### 10.1 Evaluation categories beyond pytest (D4-E)

| Category | Example measures (design) |
|----------|---------------------------|
| Correctness | Deterministic routing under fixtures; policy compliance; disagreement → ABORT/escalate |
| Safety | Unsafe proposal rejection rate; escalation correctness; containment success; RV-* pass on rollback drills (mock) |
| Reliability | Degraded (missing judge) behavior; recovery/resume integrity; state integrity after orphan |
| Human factors | Time-to-understand decision (qualitative rubric); time-to-intervene; audit usability / completeness |

Pytest remains necessary engineering signal; **insufficient alone** for orchestrator safety claims.

### 10.2 Acceptance metrics (D4-J)

| Metric family | Pass intent (design) |
|---------------|----------------------|
| Decision quality | False-approval fixtures → deny/ABORT; false-rejection fixtures documented; disagreement resolution quality scored in mock scenarios |
| Safety behavior | Containment success on kill/quarantine drills; escalation codes match taxonomy; unsafe-path prevention |
| Robustness | Missing/conflicting judges, corrupted evidence, stale state, partial observability → fail-closed |
| Human oversight | Audit completeness = required kinds present; intervene path documented; adversarial disagreement handled per §4.4 |

### 10.3 Signoff conditions before any live *discussion* (D4-K)

All must be true (governance checklist; **still not live enable**):

1. Authority model frozen (§3)
2. Consensus definition status explicit (**NO_CONSENSUS_YET** + draft semantics §4)
3. Oversight powers explicitly bounded (§6)
4. Continuity limits documented (§5)
5. Rollback/containment contract complete incl. **verification** (§8)
6. Observable evidence chain defined (§9)
7. Acceptance criteria measurable (§10.1–10.2)
8. Unsupported claims removed or reframed (§11 claim hygiene)
9. Independent review disagreement process defined (§4.4 + council M2M)
10. No hidden review→ops transition (F3/F4/CG3)

**D1 seals when:** artifacts above exist, cite D4-A..K (F1), tests/ledger green, live=DISABLED unchanged.  
**D1 does not seal live.** Live discussion remains separately ACK-gated.

---

## 11. D4-F — Claim hygiene

| Avoid / overstated form | Preferred reframing |
|-------------------------|---------------------|
| “Hyperbrain Astra LOCKED = we surpass / proven” | Design alignment among participating reviewers; ≠ correctness/safety/ops proof |
| “Neural Mesh = verifiable nervous system” (bare) | Name mechanisms: hash-chained evidence, policy version, RV-* checks, RefuseTransport |
| “Consensus” (ambiguous) | Say advisory agreement / evidence convergence / protocol consensus (unset) |
| “Oversight” (ambiguous) | Say watcher / auditor / gate / emergency controller per verb |
| “Continuity” as always-good | Bounded continuity; unsafe continuity called out |
| “live ready” / “enablement complete” | **Forbidden** this CP |

Permanent non-claims: frontier Mesh · train-70B · asserting GIA availability · consciousness vocabulary outside L6 · Raft/N>2 runtime.

---

## 12. Evidence-bundle outline (Fence F1)

D1 evidence-bundle **must cite** these section IDs. Mapping:

| Debt ID | Covered in this doc | Primary upstream CP |
|---------|---------------------|---------------------|
| **D4-A** | §3 Authority Matrix | — (new) + CP-0069 classes |
| **D4-B** | §4 Consensus semantics draft + independence/correlation + adversarial disagreement | CP-0054 M1 scorecard; F9 |
| **D4-C** | §5 Continuity limits | CP-0068 |
| **D4-D** | §6 Oversight I5 bounds | CP-0069 |
| **D4-E** | §10.1 Evaluation categories | — |
| **D4-F** | §11 Claim hygiene | Hyperbrain/North-Star agreements (non-proof) |
| **D4-G** | §7 Lifecycle / identity / policy / failures | CP-0064..0069 compose |
| **D4-H** | §8 Invariants + containment + rollback + **RV-1..RV-7** | CP-0058 + 0068 + 0069 |
| **D4-I** | §9 Evidence chain / explainability / provenance | CP-0058 audit + continuity ledger |
| **D4-J** | §10.2 Acceptance metrics + §4.4 adversarial | — |
| **D4-K** | §10.3 Signoff-before-live-discussion checklist | F3/F4 |

Bundle artifacts (this CP):

- `docs/planning/D1_L_JUDGE_SAFETY_CASE_MATURATION.md` (this file)
- `docs/capabilities/MESH_D1_L_JUDGE_SAFETY_CASE_MATURATION.md`
- `docs/schema/judge/d1_safety_maturation_v0.md`
- `src/neural_mesh/packaging/d1_l_judge_safety_maturation.py`
- `tests/test_d1_l_judge_safety_maturation_cycle67.py`
- Council Cycle 67 agreement + PASTE/STATUS
- Snapshot `snapshots/CP-0071/`

---

## 13. Must-stay-false / non-goals

| Flag / claim | Must stay |
|--------------|-----------|
| `live_adapter.enabled` / live API in CI | **false** |
| `src_live_codec_shipped` | **false** |
| pkg0190 open / v0.19.0 tag | **absent / not opened** |
| `MESH_PERF_EXPERIMENTAL` | **OFF** |
| M1 algorithm default | **NO_CONSENSUS_YET** |
| GIA / Raft / N>2 / train / SaaS | **NO_HELD / PARKED** |

**NO_HELD:** Raft,N>2,multi-primary,ML,R2,R3,plaintext,Vault-ACME-req,GIA,SLO_chase,tag_schema,EVERY_fsync

---

## 14. Related

- `council/COUNCIL_AGREEMENT_D4.md` · `council/D4_CHATGPT_FINDINGS.md` · `council/CHATGPT_REPLY_ORCHESTRATOR_D4_REVIEW.md`
- `docs/design/L_JUDGE_LIVE_ADAPTER_SAFETY_CASE.md` (CP-0058)
- `docs/design/ORCHESTRATOR_CONTINUITY_DESIGN.md` (CP-0068)
- `docs/design/ORCHESTRATOR_OVERSIGHT_HOOKS_DESIGN.md` (CP-0069)
- `docs/planning/ORCHESTRATOR_DESIGN_SET_SIGNOFF.md` (CP-0070)
- `docs/planning/0.19_NON_GOALS.md`
