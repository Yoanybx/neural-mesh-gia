# Senior Engineering Review — D4 External Review Pause

**Scope:** sealed orchestrator contract only  
**Constraint respected:** no implementation unlock, no live enable recommendation, no execution plan beyond design review.

## Executive assessment

The sealed contract appears to have reached a maturity level where the primary risks are no longer “can the system route tasks?” but rather:

- **authority boundaries**
- **judge arbitration semantics**
- **failure containment**
- **human oversight guarantees**
- **evidence quality**
- **operational reversibility**

The current state (`live=DISABLED`, `0.18.0 HELD`, `M1=NO_CONSENSUS_YET`) is appropriate because several claims require stronger contract-level definitions before any transition decision.

---

## 1. Remaining risks and missing pieces before any `live=ENABLED`

### A. Authority ambiguity risk (highest)

The contract needs an unambiguous answer to:

**Who has final authority when components disagree?**

**Open questions:**

- Does L_judge recommend, vote, veto, or authorize?
- Can a judge override another judge?
- Can a continuity mechanism preserve a bad state?
- Can oversight stop a decision after consensus?
- Is human approval required for specific classes of actions?

**Missing contract artifact: Authority Matrix**

| Component | Can propose | Can approve | Can veto | Can execute |
|---|---:|---:|---:|---:|
| L_judge | ? | ? | ? | ? |
| Oversight I5 | ? | ? | ? | ? |
| Continuity layer | ? | ? | ? | ? |
| Operator | ? | ? | ? | ? |

Without this, “safe orchestration” remains underspecified.

### B. Consensus semantics are incomplete

`M1=NO_CONSENSUS_YET` is a critical unresolved area.

**Need definitions for:**

- what counts as consensus
- minimum evidence threshold
- disagreement handling
- timeout behavior
- contradictory judge outputs
- stale judge state
- unavailable judge behavior

**Potential failure mode:**

> Multiple judges agree because they share the same blind spot.

A multi-judge design does not automatically create independence.

**Needed:**

- independence assumptions
- correlation analysis
- adversarial disagreement tests
- evidence diversity requirements

### C. Continuity risk

CP-0068 continuity introduces a key question:

**What exactly is preserved during continuity?**

**Possible unsafe interpretations:**

- preserving state that should have been invalidated
- restoring authority after a compromised decision
- carrying forward incorrect assumptions

**Contract needs:**

- continuity scope
- continuity limits
- invalidation rules
- recovery authority
- maximum persistence window

Continuity should preserve **verified state**, not merely previous state.

### D. Oversight I5 needs stronger boundaries

CP-0069 is important, but oversight requires explicit guarantees.

**Missing:**

- oversight independence
- observation scope
- intervention authority
- audit retention
- conflict-of-interest handling
- emergency stop semantics

A monitoring-only oversight layer may detect problems but fail to prevent them.  
A controlling oversight layer may become an unsafe single point of authority.  
The contract needs to define the balance.

### E. Evaluation gap

Current metrics such as pytest count are useful engineering indicators but insufficient for orchestrator safety.

**Missing evaluation categories:**

#### Correctness

- deterministic routing behavior
- policy compliance
- disagreement handling

#### Safety

- unsafe proposal rejection
- escalation correctness
- containment success

#### Reliability

- degraded operation behavior
- recovery correctness
- state integrity

#### Human factors

- explainability quality
- operator decision burden
- audit usability

---

## 2. Recommended D-order

Without seeing the exact D1/D2/D3 definitions, the ordering should follow dependency risk.

**Recommended review order:**

### 1. D1 — Contract authority and decision semantics

First priority.

**Reason:** Everything depends on knowing:

- who decides
- who can block
- who can override
- what evidence is required

A performance review before authority semantics are frozen risks optimizing an undefined system.

### 2. D2 — Safety, oversight, and containment contract

Second.

Once authority is defined, verify:

- boundaries
- intervention
- rollback
- failure modes

### 3. D3 — Evaluation and operational readiness criteria

Third.

Only after semantics and safety boundaries exist should evaluation criteria finalize.

**Suggested dependency:**

```text
D1 Authority model ↓ D2 Safety/oversight model ↓ D3 Validation/readiness model ↓ D4 external review
```

---

## 3. Claims that appear overstated or unsupported

Based only on the stated contract themes:

### “Hyperbrain Astra agreement LOCKED”

**Potential issue:**

Agreement between design agents/reviewers is not equivalent to:

- correctness proof
- safety proof
- operational validation
- independent verification

**Better wording:**

> “Design alignment achieved among participating reviewers.”

### “Neural Mesh = verifiable nervous system”

**Potential issue:**

“Verifiable” requires defined verification mechanisms.

**Need evidence for:**

- what properties are verified
- verification frequency
- verifier independence
- failure handling

### “Consensus”

**Potential issue:**

Consensus can mean:

- identical output
- majority agreement
- evidence convergence
- protocol-level agreement

The contract must define which.

### “Oversight”

**Potential issue:**

Oversight is not automatically control.

A watcher, auditor, governor, and emergency controller are different roles.

### “Continuity”

**Potential issue:**

Continuity is often treated positively, but unsafe continuity can preserve bad state.

Need bounded continuity.

---

## 4. Contract ambiguities and required additions

### A. Ambiguities

#### Decision lifecycle

Need explicit states:

```text
proposal → evaluation → judge review → approval/rejection → execution authorization → audit closure
```

#### Identity and trust

Need:

- component identity rules
- trust boundaries
- credential lifecycle
- compromise response

#### Policy versioning

Need:

- active policy identifier
- policy migration rules
- rollback rules
- incompatible policy handling

#### Failure classification

Need categories:

- transient failure
- degraded mode
- unsafe state
- compromise suspected
- unknown state

## Safety / oversight gaps

**Required contract additions:**

### Safety invariants

Examples:

- no unauthorized authority escalation
- no hidden execution path
- no bypass of oversight requirements
- no irreversible action without required evidence

### Containment requirements

Define:

- maximum blast radius
- isolation procedure
- emergency disable semantics
- state quarantine
- forensic capture requirements

### Rollback requirements

Need:

- rollback trigger
- rollback authority
- rollback scope
- rollback verification

A rollback that cannot prove restored correctness is incomplete.

## Observability gaps

Need contract-level observability requirements.

### Required records

Every decision should have:

- request identity
- policy version
- judge inputs
- judge outputs
- evidence references
- final authority decision
- timestamp/order information
- operator visibility status

### Explainability requirement

The system should answer:

> “Why was this decision accepted or rejected?”

Not just:

> “Which component produced the output?”

## Evaluation holes

**Missing acceptance criteria:**

### Decision quality

Measure:

- false approvals
- false rejections
- disagreement resolution quality

### Safety behavior

Measure:

- containment success rate
- escalation correctness
- unsafe-path prevention

### Robustness

Test:

- missing judges
- conflicting judges
- corrupted evidence
- stale state
- partial observability

### Human oversight

Measure:

- time to understand a decision
- time to intervene
- audit completeness

## Required signoff conditions before reconsidering live state

A contract-level signoff should require:

- **Authority model frozen**
- **Consensus definition frozen**
- **Oversight powers explicitly bounded**
- **Continuity limits documented**
- **Rollback/containment contract complete**
- **Observable evidence chain defined**
- **Acceptance criteria measurable**
- **Unsupported claims removed or reframed**
- **Independent review disagreement process defined**
- **No hidden transition from review mode to operational mode**

---

## Final D4 review verdict

**Status: Continue external review pause.**

The architecture themes are coherent, but the remaining risk is not primarily engineering complexity; it is **governance precision**. The sealed contract needs stronger definitions around authority, evidence, disagreement, and containment before any discussion of `live=ENABLED`.

**Recommended next review focus:**

**D1 → D2 → D3**, with D1 treated as the gating design artifact because safety, oversight, and evaluation all depend on a clear authority model.
