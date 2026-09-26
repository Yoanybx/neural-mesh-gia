# Durable Goals + Continuity — Design (substrate memory)

**Status:** DESIGN DRAFT (authorized invention — HYPERBRAIN_ASTRA)  
**Cycle / Checkpoint:** 43 / CP-0047  
**Date:** 2026-09-26 America/New_York (EDT)  
**Explicit non-claims:** NOT infinite-context transformer memory; NOT consciousness;
NOT L_GIA unlock. This is **substrate memory** under Mesh control.

---

## 1. Problem

LLM / MLLM sessions are amnesiac: context windows truncate; process restarts wipe
chat state; rented engines do not own long-horizon goals. Operators still need
systems that **do not lose long-term goals or reconstructible reasoning trails**
and can resume assigned work after restart — without inventing NO_HELD layers.

## 2. Authorized invention (three durable pieces)

1. **Durable goal registry** — assigned goals survive sessions; hashed + versioned;
   restart-safe.
2. **Evidence / audit ledger** — actions, judgments, ABORT reasons via Mesh OBS +
   receipts; reconstructible trail.
3. **Continuity state machine** — multi-step progress, blockers, resume-after-restart;
   explicit terminal states.

Plus: **Ephemeral L_judge, persistent Mesh memory** — engine calls are disposable;
Mesh holds goals + evidence so the chain is reconstructible across sessions.

---

## 3. Data shapes

### 3.1 `GoalRecord`

```json
{
  "schema": "mesh.goal/v0",
  "goal_id": "goal:<hash16>",
  "version": 1,
  "content_digest": "sha256:...",
  "title": "short",
  "assignee": "human:|agent:|mesh:",
  "priority": 0,
  "created_hlc": "...",
  "updated_hlc": "...",
  "parent_goal_id": null,
  "tags": [],
  "terminal": false,
  "continuity_id": "cont:<hash16>"
}
```

Registry invariants:

- `goal_id` = hash of canonical content at v1; version bumps on mutation with
  prior digests retained in ledger.
- Restart-safe store (same durability class as Mesh recovery/WAL path conceptually;
  exact backend TBD — design only).
- Deletion is soft + audited (`forget` requires I6-style policy).

### 3.2 `EvidenceEntry` (ledger)

```json
{
  "schema": "mesh.evidence/v0",
  "entry_id": "ev:<hash16>",
  "goal_id": "goal:<hash16>",
  "kind": "judge_receipt|obs|action|abort|human_note|probe",
  "payload_digest": "sha256:...",
  "receipt_id": "rcpt:...|null",
  "prev_entry_hash": "sha256:...|null",
  "created_hlc": "...",
  "node_id": "node:...",
  "dual_primary": 0
}
```

Ledger is append-oriented + hash-chained. Reconstructibility = walk chain by
`goal_id` / `continuity_id`.

### 3.3 `ContinuityState` (state machine)

```json
{
  "schema": "mesh.continuity/v0",
  "continuity_id": "cont:<hash16>",
  "goal_id": "goal:<hash16>",
  "state": "PENDING|READY|RUNNING|BLOCKED|PAUSED|RESUMING|SUCCEEDED|FAILED|ABORTED|CANCELLED",
  "step_id": "step:...",
  "steps_done": [],
  "blocker": {"code": null, "detail_digest": null},
  "resume_token": "opaque-or-null",
  "last_receipt_id": "rcpt:...|null",
  "updated_hlc": "..."
}
```

#### Transition table (design)

| From | Event | To |
|------|-------|----|
| PENDING | assign/validate | READY |
| READY | start / resume | RUNNING |
| RUNNING | probe fail / wait | BLOCKED |
| BLOCKED | unblock | RESUMING → RUNNING |
| RUNNING | human pause | PAUSED |
| PAUSED | resume | RESUMING → RUNNING |
| RUNNING | success criteria | SUCCEEDED (terminal) |
| * | policy ABORT | ABORTED (terminal) |
| * | operator cancel | CANCELLED (terminal) |
| RUNNING | unrecoverable | FAILED (terminal) |

Terminal states are immutable except via audited supersede (new goal version).

---

## 4. Interfaces (pseudocode)

```text
class GoalRegistry:
    def put(self, goal: GoalRecord) -> GoalRecord
    def get(self, goal_id: str) -> GoalRecord
    def list_open(self) -> list[GoalRecord]
    def supersede(self, goal_id: str, new_content) -> GoalRecord

class EvidenceLedger:
    def append(self, entry: EvidenceEntry) -> EvidenceEntry
    def chain(self, goal_id: str) -> list[EvidenceEntry]
    def verify(self, goal_id: str) -> bool

class ContinuityMachine:
    def load(self, continuity_id: str) -> ContinuityState
    def transition(self, continuity_id: str, event: str, **kw) -> ContinuityState
    def resume_after_restart(self, continuity_id: str) -> ContinuityState
        """Rehydrate from registry+ledger; never from engine chat logs."""
```

Integration with L_judge MIX:

- Each `JudgeRequest` carries `goal_id` + `continuity_hint`.
- Each `JudgeReceipt` appends an `EvidenceEntry`.
- Verdicts may drive continuity events (`BLOCKED`, `SUCCEEDED`, …) only through
  Mesh policy — engine cannot directly mutate registry.

---

## 5. Compensating LLM session amnesia

| Lost in LLM session | Recovered from Mesh |
|---------------------|---------------------|
| Chat tokens | Not recovered (ephemeral by design) |
| Assigned goals | GoalRegistry |
| Why we ABORTed | EvidenceLedger + receipts |
| Which step we were on | ContinuityState |
| Prior accept/reject | receipt digests re-injected into next JudgeRequest |
| Operator intent across days | goal content_digest + human_note evidence |

**Reconstructible reasoning** means: an auditor can replay digests + receipts +
state transitions and understand *what was decided and why under policy* —
not that the original token stream is immortal.

---

## 6. Non-goals

- Infinite / lossless transformer context
- Consciousness, episodic autobiographical “self”, AGI memory claims
- L_GIA unlock
- Cross-site federated ledger runtime (world-scale = later design notes only)
- Economy / settlement ledgers
- Raft-backed multi-primary goal authority
- Treating agent-shell local diaries as Mesh source-of-truth

**NO_HELD:** Raft,N>2,multi-primary,ML,R2,R3,plaintext,Vault-ACME-req,GIA,SLO_chase,tag_schema,EVERY_fsync

---

## 7. Deferral

CP-0047 = design only. No registry runtime, no SQLite/WAL choice lock, no schema
mint under `schema/goal/` required until after freeze + subsequent implementation
CPs. Prefer reuse of existing OBS/receipt patterns where possible.

## Related

- `docs/design/L_JUDGE_MIX_DESIGN.md`
- `docs/planning/0.19_SCOPE_DRAFT.md`
- `council/COUNCIL_AGREEMENT_HYPERBRAIN_ASTRA.md`
