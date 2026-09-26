# Schema: mesh.continuity/v0 + mesh.evidence/v0 (STUB)

**Status:** STUB (Cycle 47 / CP-0051)  
**Design:** `docs/design/DURABLE_GOALS_CONTINUITY_DESIGN.md`

## ContinuityState (`mesh.continuity/v0`)

States: `PENDING|READY|RUNNING|BLOCKED|PAUSED|RESUMING|SUCCEEDED|FAILED|ABORTED|CANCELLED`

Terminal: SUCCEEDED, FAILED, ABORTED, CANCELLED (immutable except audited supersede).

## EvidenceEntry (`mesh.evidence/v0`)

Append-only hash-chained ledger entries (`kind`: judge_receipt|obs|action|abort|human_note|probe).

**NO_HELD** unchanged. No federated multi-site ledger runtime.
