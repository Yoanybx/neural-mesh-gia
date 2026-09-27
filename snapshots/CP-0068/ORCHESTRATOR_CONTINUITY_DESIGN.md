# Orchestrator Continuity — Design (durable goals + audit + resume)

**Status:** DESIGN ONLY (mock continuity plane + schema; **live=DISABLED**; no live API, no train, no src codec)  
**Cycle / Checkpoint:** 64 / CP-0068  
**Version:** package **0.18.0** held  
**Date:** 2026-09-26 America/New_York (EDT)  
**Theme:** `orchestrator_continuity_design`  
**Authority:** DeepSeek C63 NEXT Option 1 (ranked) after perf hotspot CP-0067  
**Extends:** `DURABLE_GOALS_CONTINUITY_DESIGN.md` · `ORCHESTRATOR_JUDGE_ROUTING_DESIGN.md` ·
`L_JUDGE_M2_E2E_SPIKE.md` · `MULTI_JUDGE_AGENT_SHELL_SPIKE.md` ·
`MESH_PERF_HOTSPOT_AND_IMPROVEMENT_DESIGN.md` · `fabric/M2_MEMBERSHIP_REJOIN_DESIGN.md`  
**Non-claim:** This is **substrate memory under Mesh control** — NOT consciousness,
NOT infinite-context transformer memory, NOT L_GIA unlock. Engines stay ephemeral;
Mesh owns goals, evidence, continuity, receipts, ABORT.

---

## 1. Intent

Formalize the **orchestrator continuity contract** that CP-0064 only hooked:

| Concern | This CP formalizes |
|---------|-------------------|
| In-flight judge calls across LEFT/REJOIN | Orphan policy + audit |
| Orphaned-request policy | Explicit ABORT / rebind rules |
| Invocation idempotency | Keyed; no double-invoke |
| Resume after restart | Rehydrate from Mesh registry+ledger only |
| Timeout bounds | Soft / hard / deadman compose |
| ABORT propagation | Continuity + routing + membership |
| Compose with judge routing | ContinuityOrchestrator wraps OrchestratorRouter |
| Perf budget note | receipt_hash_chain cost at transition edges (CP-0067) |

| This CP ships | Explicitly deferred |
|---------------|---------------------|
| Continuity policy design + schema stubs | Live multi-engine HTTPS/SDK |
| Mock ContinuityOrchestrator + registry/ledger | Runtime codec in `src/neural_mesh/judge_*.py` |
| Neg tests T-cont-a/b/c | Oversight-hooks refinement (queued after) |
| Resume-after-restart mock | WAL/SQLite backend lock; Raft/N>2 |
| Continuity × routing compose | GIA / train / SaaS / settlement |

---

## 2. Ownership boundary (hard)

```
┌──────────────────────────────────────────────────────────────┐
│ Mesh Continuity Plane (this design)                          │
│  • GoalRegistry (durable assigned goals)                     │
│  • EvidenceLedger (hash-chained audit)                       │
│  • ContinuityMachine (state + resume token)                  │
│  • InFlightTracker (invocation idempotency + orphan policy)  │
│  • wraps OrchestratorRouter (CP-0064) for ALLOW/ABORT        │
└───────────────┬──────────────────┬───────────────────────────┘
                │                  │
                ▼                  ▼
       L_judge MIX (mock)   agent_shell (mock)
         (ephemeral)           (ephemeral)
```

| Concern | Owner | Must NOT |
|---------|-------|----------|
| Goals / evidence / continuity SoT | Mesh substrate | Engine chat / agent diary as SoT |
| In-flight orphan on LEFT/REJOIN | Mesh continuity | Silent drop without ledger entry |
| Idempotent invoke | Mesh InFlightTracker | Engine-side “retry invents new goal” |
| Resume after process restart | Mesh registry+ledger | Reconstruct from LLM context window |
| Consciousness / self / autobiographical memory | **FORBIDDEN claim** | Any L6 vocabulary as product claim |
| Credentials / live transport | RefuseTransport default | Keys in repo; flipping live away from DISABLED |
| Dual-judge agreement | Advisory only | Claim M1 consensus / Raft |

---

## 3. Durable pieces (compose CP-0047)

### 3.1 GoalRegistry (restart-safe)

`GoalRecord` (`mesh.goal/v0`) — assigned goals survive sessions; hashed + versioned.
Deletion is soft + audited. See `DURABLE_GOALS_CONTINUITY_DESIGN.md` §3.1.

### 3.2 EvidenceLedger (audit)

`EvidenceEntry` (`mesh.evidence/v0`) — append-oriented hash chain. Kinds used here:

| kind | When |
|------|------|
| `routing_receipt` | OrchestratorRouter ALLOW/ABORT |
| `judge_receipt` | Mock judge return |
| `invoke_start` | In-flight open |
| `invoke_end` | In-flight close (success/abort) |
| `orphan` | LEFT/REJOIN orphan policy fired |
| `resume` | resume_after_restart / CONTINUITY_RESUME |
| `timeout` | soft/hard timeout |
| `abort` | policy ABORT |
| `human_note` | operator annotate |

### 3.3 ContinuityMachine

States (unchanged from CP-0047):  
`PENDING|READY|RUNNING|BLOCKED|PAUSED|RESUMING|SUCCEEDED|FAILED|ABORTED|CANCELLED`

Terminal immutable except audited supersede (new goal version).

---

## 4. In-flight + orphan policy (LEFT/REJOIN)

### 4.1 InFlightRecord

```json
{
  "schema": "mesh.orchestrator.inflight/v0",
  "invoke_id": "inv:<hash16>",
  "idempotency_key": "idem:<opaque>",
  "goal_id": "goal:<hash16>",
  "continuity_id": "cont:<hash16>",
  "request_id": "uuid",
  "engine_ids": ["judge:mock-a"],
  "member_state_at_start": "ACTIVE",
  "status": "OPEN|SEALED|ORPHANED|TIMED_OUT|ABORTED",
  "opened_hlc": "...",
  "deadline_hlc": "...",
  "last_routing_receipt_id": "rcpt:...|null",
  "prev_entry_hash": "sha256:...|null"
}
```

### 4.2 Orphan policy (design)

When membership leaves ACTIVE mid-flight (DRAINING / LEFT / REJOIN / JOINING / ATTESTING):

| Event | Continuity action | Ledger | Routing |
|-------|-------------------|--------|---------|
| DRAINING mid-flight | BLOCKED (`MEMBER_DRAINING`) | `orphan` + reason | no new ALLOW; finish seal if drain-only |
| LEFT mid-flight | ABORT `CONT_ORPHAN_LEFT` | `orphan` + `abort` | refuse further until REJOIN→ACTIVE |
| REJOIN label (not yet ACTIVE) | stay BLOCKED / ORPHANED | `orphan` | no silent resume as ACTIVE |
| Process crash / restart | RESUMING via `resume_after_restart` | `resume` | re-validate member/band/oversight; re-route |

**Invariant:** no silent ACTIVE resume after LEFT (M2 rule). Continuity may hold
goals; membership must re-attest to ACTIVE T2|T3 before new invokes.

### 4.3 Orphaned-request outcomes

| Outcome code | Meaning |
|--------------|---------|
| `CONT_ORPHAN_LEFT` | In-flight sealed ABORT because member LEFT |
| `CONT_ORPHAN_REJOIN_PENDING` | Rejoin in progress; wait for ACTIVE |
| `CONT_ORPHAN_DRAIN` | Drain interrupted in-flight; BLOCKED |
| `CONT_REBIND_AFTER_ACTIVE` | After ACTIVE restored, idempotent rebind allowed if key fresh / within TTL |
| `CONT_ORPHAN_DROP_FORBIDDEN` | Attempted silent drop without ledger → refused |

---

## 5. Invocation idempotency

- Every invoke carries `idempotency_key` (required).
- `InFlightTracker.open(key)` → if key already SEALED with same digest → return prior receipt (**no double-invoke**).
- If key OPEN → return same `invoke_id` (at-most-once start).
- If key SEALED with **different** payload digest → ABORT `CONT_IDEMPOTENCY_CONFLICT`.
- Keys expire only after terminal continuity + soft TTL (design: mock clock; no wall-clock-as-authority for Mesh HLC — HLC remains authority).

---

## 6. Resume semantics (after restart)

```text
def resume_after_restart(continuity_id) -> ContinuityState:
    goal = registry.get(by continuity)
    chain = ledger.chain(goal_id)
    state = machine.load(continuity_id)
    assert not from_engine_chat_logs
    if state in TERMINAL: return state  # immutable
    # Re-validate environment before re-route
    if member_state != ACTIVE or trust not in {T2,T3}: BLOCKED
    if dual_primary != 0: ABORT FENCE
    if live_api_enabled: ABORT CONT_LIVE_DISABLED
    if n_members > 2: ABORT CONT_N_GT2_REFUSED
    machine.transition(RESUMING)
    decision = router.route(envelope with WorkloadClass.CONTINUITY_RESUME)
    append EvidenceEntry(kind=resume)
    return machine.transition(RUNNING|BLOCKED|ABORTED per decision)
```

**Reconstructible reasoning** = digests + receipts + transitions under policy —
not immortal token streams. Substrate memory ≠ consciousness.

---

## 7. Timeout bounds

| Bound | Default (design mock) | Effect |
|-------|----------------------|--------|
| `soft_timeout` | 30s mock units | Evidence `timeout` soft; continuity → BLOCKED; may retry idempotent |
| `hard_timeout` | 120s mock units | In-flight → TIMED_OUT; continuity → FAILED or ABORTED per policy |
| `deadman` (A4) | compose I5 | ABORT `ROUTE_DEADMAN_REQUIRED` / `CONT_DEADMAN` |
| `orphan_grace` | 5s mock units | After LEFT detected, grace then `CONT_ORPHAN_LEFT` |

Wall clock is **not** Mesh authority (H7); mock uses logical counters / injected HLC.

---

## 8. ABORT propagation

ABORT sources fan into ContinuityMachine:

| Source | Continuity target | Ledger kind |
|--------|-------------------|-------------|
| Routing ABORT (CP-0064 codes) | BLOCKED or ABORTED | `routing_receipt` + `abort` |
| Orphan LEFT | ABORTED (`CONT_ORPHAN_LEFT`) | `orphan` |
| Hard timeout | FAILED/ABORTED | `timeout` |
| Oversight kill / deny | ABORTED | `abort` |
| Idempotency conflict | ABORTED | `abort` |
| FENCE / N>2 / live | ABORTED | `abort` |

Propagation is **fail-closed**: no ALLOW after terminal ABORT without supersede.

New continuity ABORT codes (additive to routing):

| Code | Trigger |
|------|---------|
| `CONT_ORPHAN_LEFT` | in-flight + member LEFT |
| `CONT_ORPHAN_REJOIN_PENDING` | rejoin not yet ACTIVE |
| `CONT_ORPHAN_DRAIN` | drain mid-flight |
| `CONT_ORPHAN_DROP_FORBIDDEN` | silent drop attempted |
| `CONT_IDEMPOTENCY_CONFLICT` | same key, different payload |
| `CONT_TIMEOUT_SOFT` | soft timeout (BLOCKED) |
| `CONT_TIMEOUT_HARD` | hard timeout |
| `CONT_LIVE_DISABLED` | live path while live=DISABLED |
| `CONT_N_GT2_REFUSED` | N>2 |
| `CONT_SCHEMA_INVALID` | missing goal/continuity/idempotency |
| `CONT_RESUME_FORBIDDEN_TERMINAL` | resume on terminal state |
| `FENCE` | dual_primary ≠ 0 |

---

## 9. Compose with judge routing (CP-0064)

`ContinuityOrchestrator.invoke(envelope)`:

1. Validate goal_id + continuity_id + idempotency_key.
2. Registry put-if-absent; machine ensure READY/RUNNING.
3. InFlightTracker.open (idempotent).
4. Delegate `OrchestratorRouter.route(envelope)`.
5. On ALLOW → ledger `routing_receipt` + `invoke_end` SEALED; continuity RUNNING/step++.
6. On ABORT → ledger + continuity BLOCKED/ABORTED; in-flight ABORTED.
7. On member churn mid-flight → orphan policy (§4).

CONTINUITY_RESUME workload restores prior policy from ContinuityState / last RoutingReceipt
(already sketched in CP-0064 §8).

---

## 10. Perf budget note (CP-0067)

Local hotspot knowledge (honest, box-local, `ranking_claim=null`):

- `receipt_hash_chain` ~0.9 ms / 32 locally — LEFT/REJOIN paths that emit many
  routing + orphan + resume receipts must **budget** chain append/verify cost.
- Continuity designs prefer **batched seal** of orphan+abort as one ledger append
  where policy allows (still hash-chained; no EVERY_fsync invention).
- OBS tip inject (I1) remains experimental/OFF — may help status cadence during
  resume without touching M1 (still NO_CONSENSUS_YET).
- No achieved-speedup claim from this CP.

---

## 11. Negative tests

| ID | Trigger | Expect |
|----|---------|--------|
| **T-cont-a** | in-flight invoke then DRAINING→LEFT→REJOIN (not ACTIVE) | orphan ABORT / BLOCKED; ledger `orphan`; no silent ACTIVE; no drop without audit |
| **T-cont-b** | duplicate idempotency_key (same payload) / conflict (different payload) | same receipt / `CONT_IDEMPOTENCY_CONFLICT`; **no double-invoke** |
| **T-cont-c** | hard timeout; resume on terminal; live=True; dual_primary≠0; N>2; missing idempotency | matching CONT_* / `FENCE` / `CONT_LIVE_DISABLED` |

Happy path (design): ACTIVE T2 + soft path → ALLOW + ledger chain verifies + resume_after_restart restores RUNNING.

---

## 12. Explicit non-goals (held)

- Enabling live (must stay live=DISABLED) / API keys / frontier Mesh / train-70B / GIA  
- Raft / N>2 / multi-primary / pkg0190 / v0.19.0 tag  
- Consciousness / episodic autobiographical “self” / AGI memory claims  
- Dual-judge as M1 consensus · settlement / SaaS multi-tenant product  
- Treating agent-shell local diaries or LLM chat as Mesh source-of-truth  
- Production perf patches; MESH_PERF_EXPERIMENTAL stays OFF unless operator flips  

**NO_HELD:** Raft,N>2,multi-primary,ML,R2,R3,plaintext,Vault-ACME-req,GIA,SLO_chase,tag_schema,EVERY_fsync

---

## 13. Related

- `docs/design/DURABLE_GOALS_CONTINUITY_DESIGN.md` (CP-0047 substrate memory)
- `docs/schema/continuity/orchestrator_v0.md`
- `docs/capabilities/MESH_ORCHESTRATOR_CONTINUITY.md`
- `src/neural_mesh/packaging/orchestrator_continuity.py`
- `tests/test_orchestrator_continuity_cycle64.py`
