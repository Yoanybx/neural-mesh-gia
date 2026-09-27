# Orchestrator Oversight Hooks — Design Refinement (I5 human oversight)

**Status:** DESIGN ONLY (mock oversight plane + schema; **live=DISABLED**; no live API, no train, no src codec)  
**Cycle / Checkpoint:** 65 / CP-0069  
**Version:** package **0.18.0** held  
**Date:** 2026-09-26 America/New_York (EDT)  
**Theme:** `oversight_hooks_design_refinement`  
**Authority:** DeepSeek C64 NEXT Option 1 (ranked) after orchestrator continuity CP-0068  
**Extends:** blueprint L5 I5 · `ORCHESTRATOR_JUDGE_ROUTING_DESIGN.md` §7 ·
`ORCHESTRATOR_CONTINUITY_DESIGN.md` · `L_JUDGE_LIVE_ADAPTER_SAFETY_CASE.md` (RefuseTransport / HUMAN_ABORT) ·
`DURABLE_GOALS_CONTINUITY_DESIGN.md`  
**Non-claim:** Human-in-the-loop control surface for Mesh orchestrator decisions —
NOT GIA unlock, NOT consciousness, NOT live kill-channel UI, NOT Quorum-Raft.

---

## 1. Intent

Formalize the **I5 human oversight contract** that CP-0064 hooked and CP-0068 left queued:

| Concern | This CP formalizes |
|---------|-------------------|
| approve / deny | A3/A4 gate before ALLOW |
| pause / resume | Mid-flight continuity PAUSED; no new routes; resume restores |
| kill (w/ quorum) | Continuity ABORTED; RefuseTransport; refuse further |
| dead-man | T_dead default; no human ack → auto-DRAIN; override logged |
| consent-revoke | Drops approval + deadman_ok; subsequent routes re-gate |
| A0..A4 boundary | Enforced at orchestrator (I4 compose) |
| Compose continuity | Acts on in-flight ContinuityState / InFlightTracker |
| Compose routing | Oversight decision binds selected judge(s) / RoutingReceipt |
| Safety case | HUMAN_ABORT + RefuseTransport (CP-0058) |

| This CP ships | Explicitly deferred |
|---------------|---------------------|
| Oversight policy design + schema stubs | Live multi-engine HTTPS/SDK |
| Mock OversightPlane + OversightOrchestrator | Runtime codec in `src/neural_mesh/judge_*.py` |
| Neg tests T-ovs-a/b/c | Production UI / mesh CLI surface (I2) |
| Dead-man + quorum-human (design) | Raft / N>2 / GIA / train / SaaS |
| Compose continuity + routing | MESH_PERF_EXPERIMENTAL flip |

---

## 2. Ownership boundary (hard)

```
┌──────────────────────────────────────────────────────────────┐
│ Mesh Oversight Plane (this design — I5)                      │
│  • OversightPlane (approve/deny/pause/resume/kill/deadman)   │
│  • OversightDecision ledger (hash-chained)                   │
│  • DeadmanWatch (T_dead + auto-DRAIN)                        │
│  • QuorumHuman (A4 ≥2 named humans — design mock)            │
│  • wraps ContinuityOrchestrator (CP-0068)                    │
│  • binds OrchestratorRouter (CP-0064) judge selection        │
└───────────────┬──────────────────┬───────────────────────────┘
                │                  │
                ▼                  ▼
       Continuity plane      Routing + RefuseTransport
       (in-flight SoT)       (which judges bind / kill-switch)
```

| Concern | Owner | Must NOT |
|---------|-------|----------|
| Human approve/deny/pause/kill | Mesh OversightPlane | Engine self-approve; silent ALLOW on A3/A4 |
| Dead-man TTL / auto-DRAIN | Mesh DeadmanWatch | Wall-clock-as-authority for Mesh HLC (H7) |
| Continuity PAUSED/ABORTED | ContinuityMachine | Engine chat as pause SoT |
| Which judges a decision binds | RoutingReceipt.engine_ids | Dual-judge as M1 consensus |
| Live transport on kill | RefuseTransport | Keep calling live after kill |
| Consciousness / self | **FORBIDDEN claim** | Any L6 vocabulary as product claim |

---

## 3. Action-class boundary (I4 compose)

| Class | Meaning | Oversight requirement |
|-------|---------|----------------------|
| **A0** | Observe / classify | Auto allow under dry_run; no human gate |
| **A1** | Advisory judgment | Auto allow (advisory_only); no human gate |
| **A2** | Soft side-effect / dry-run tool | Dry-run required; human optional |
| **A3** | Hard side-effect / external act / tool invocation | **Human approve or deny required** |
| **A4** | Irreversible / high-blast | **Human approve + deadman + quorum-human (≥2)** |

Enforced at orchestrator path before ContinuityOrchestrator delegates to
OrchestratorRouter.ALLOW. Bypass attempt → ABORT `OVS_CLASS_BYPASS` /
`ROUTE_OVERSIGHT_REQUIRED`.

---

## 4. Hook verbs (I5)

| Hook | CLI (design) | Effect on continuity | Effect on routing | Ledger kind |
|------|--------------|----------------------|-------------------|-------------|
| `approve` | `mesh oversight approve` | Clears BLOCKED-for-oversight; may proceed | Sets `oversight.approved=true` on bound engines | `oversight` |
| `deny` | `mesh oversight deny` | → ABORTED | ABORT `ROUTE_OVERSIGHT_DENIED` / `OVS_DENIED` | `oversight` + `abort` |
| `pause` | `mesh ctl pause` | → PAUSED; open in-flight stay OPEN (no seal ALLOW) | No new routes (`OVS_PAUSED`) | `oversight` |
| `resume` | `mesh ctl resume` | PAUSED → RUNNING (if member ACTIVE) | Clears paused; re-gate A3/A4 | `oversight` |
| `kill` | `mesh ctl kill --quorum` | → ABORTED; open in-flight ABORTED | Refuse further; RefuseTransport | `oversight` + `abort` |
| `deadman_refresh` | (operator heartbeat) | Keeps A4 window open | Sets `deadman_ok=true` until TTL | `oversight` |
| `consent_revoke` | `mesh consent revoke` | Re-gate subsequent; may BLOCKED | Drops approved + deadman_ok | `oversight` |

**SLO_pause (design):** target ≤2 mock units, hard ≤10 mock units from pause
command to no-new-ALLOW. Measured with injected HLC/counters (not wall-clock authority).

**Kill quorum (design, N=2):** both human seats in QuorumHuman **or** single
operator + fence_epoch attest (P-01 compose). Mock records `quorum_ok`.

---

## 5. Dead-man switch (P-11)

| Parameter | Default (design mock) | Notes |
|-----------|----------------------|-------|
| `T_dead` | **86400** mock units (≈24h logical) | P-11; override logged |
| `T_dead_override` | operator-set; must log `deadman_override` | Evidence kind `oversight` |
| On expiry | auto-**DRAIN** membership path + continuity BLOCKED | ABORT codes `OVS_DEADMAN_EXPIRED` / compose `ROUTE_DEADMAN_REQUIRED` |
| A4 without fresh deadman | refuse ALLOW | `ROUTE_DEADMAN_REQUIRED` / `OVS_DEADMAN_REQUIRED` |

Algorithm (mock):

```text
def tick_deadman(now_hlc):
    if not watching_a4: return
    if now_hlc - last_refresh > T_dead:
        append Evidence(kind=oversight, code=OVS_DEADMAN_EXPIRED)
        continuity → BLOCKED (or DRAIN path)
        membership notify DRAINING (design stub)
        deadman_ok = False
```

Wall clock is **not** Mesh authority (H7); mock uses logical counters / injected HLC.

---

## 6. Quorum-human (A4)

| Rule | Design |
|------|--------|
| Minimum | ≥2 named human seats for A4 approve/kill |
| Mock seats | `human:operator`, `human:reviewer` (placeholders; not live IdP) |
| Approve A4 | both must `approve` (or recorded `quorum_ok=true` after dual ack) |
| Kill | same quorum rule |
| Single-seat attempt | ABORT `OVS_QUORUM_REQUIRED` |

A0–A3 do not require dual seats (A3 needs one approve/deny).

---

## 7. Compose with continuity (CP-0068) + routing (CP-0064)

`OversightOrchestrator.decide_and_invoke(envelope, idempotency_key)`:

1. Apply OversightPlane pre-gate (kill/pause/deny/class/deadman/quorum).
2. If pre-gate ABORT → ledger `oversight` + continuity ABORT/BLOCKED; **no** router ALLOW.
3. Else ContinuityOrchestrator.invoke → OrchestratorRouter.route (existing path).
4. Oversight decisions bind `RoutingReceipt.engine_ids` (which judges the human
   decision covers); recorded on OversightDecision.bound_engine_ids.
5. Mid-flight `pause`/`kill` via OversightPlane acts on ContinuityMachine +
   InFlightTracker (seal ABORT / leave OPEN blocked).
6. Safety: kill or live attempt → RefuseTransport semantics (`HUMAN_ABORT` /
   `CONT_LIVE_DISABLED` / `OVS_KILLED`); live stays DISABLED.

Perf note (CP-0067): oversight receipts join the same hash-chain budget as
routing/continuity; prefer batched seal of oversight+abort where policy allows.

---

## 8. OversightDecision record

```json
{
  "schema": "mesh.orchestrator.oversight_decision/v0",
  "decision_id": "ovs:<hash16>",
  "verb": "approve|deny|pause|resume|kill|deadman_refresh|consent_revoke|tick_deadman",
  "actor": "human:operator",
  "goal_id": "goal:<hash16>",
  "continuity_id": "cont:<hash16>",
  "action_class": "A3",
  "bound_engine_ids": ["judge:mock-a"],
  "quorum_ok": true,
  "deadman_ok": true,
  "t_dead": 86400,
  "t_dead_override_logged": false,
  "result": "ALLOW|ABORT|BLOCKED|PAUSED|DRAIN",
  "abort_code": null,
  "refuse_transport": false,
  "dual_primary": 0,
  "live_api": false,
  "created_hlc": "hlc:N",
  "prev_decision_hash": "sha256:...|null"
}
```

---

## 9. ABORT codes (oversight — additive)

| Code | Trigger |
|------|---------|
| `OVS_REQUIRED` | A3/A4 without approve (alias compose `ROUTE_OVERSIGHT_REQUIRED`) |
| `OVS_DENIED` | human deny (alias `ROUTE_OVERSIGHT_DENIED`) |
| `OVS_PAUSED` | pause engaged; no new routes |
| `OVS_KILLED` | kill switch; RefuseTransport |
| `OVS_DEADMAN_REQUIRED` | A4 without fresh deadman |
| `OVS_DEADMAN_EXPIRED` | T_dead elapsed → auto-DRAIN |
| `OVS_QUORUM_REQUIRED` | A4/kill without quorum-human |
| `OVS_CLASS_BYPASS` | attempted A3/A4 bypass of gate |
| `OVS_CONSENT_REVOKED` | post-revoke attempt without re-approve |
| `OVS_LIVE_DISABLED` | live path while live=DISABLED |
| `OVS_N_GT2_REFUSED` | N>2 |
| `OVS_SCHEMA_INVALID` | missing actor/goal/continuity |
| `FENCE` | dual_primary ≠ 0 |

(Plus CP-0064 `ROUTE_*` and CP-0068 `CONT_*` when delegated.)

---

## 10. Negative tests

| ID | Trigger | Expect |
|----|---------|--------|
| **T-ovs-a** | A3 without approve; A3 approve→ALLOW; A3 deny | `OVS_REQUIRED` / ALLOW / `OVS_DENIED`; ledger `oversight` |
| **T-ovs-b** | pause mid-flight; resume; kill | PAUSED no new ALLOW; resume re-gates; kill→ABORTED + `refuse_transport` |
| **T-ovs-c** | A4 without deadman/quorum; deadman expire; consent-revoke; live; N>2; dual_primary | `OVS_DEADMAN_*` / `OVS_QUORUM_*` / auto-DRAIN / re-gate / `OVS_LIVE_DISABLED` / `OVS_N_GT2_REFUSED` / `FENCE` |

Happy path (design): A1 advisory → ALLOW without human; A3 with approve → ALLOW +
bound engines recorded; A4 with dual approve + deadman_refresh → ALLOW; chain verifies.

---

## 11. Explicit non-goals (held)

- Enabling live (must stay live=DISABLED) / API keys / frontier Mesh / train-70B / GIA  
- Raft / N>2 / multi-primary / pkg0190 / v0.19.0 tag  
- Consciousness / episodic autobiographical “self” / AGI claims  
- Production mesh CLI UI; real IdP quorum; settlement / SaaS product  
- MESH_PERF_EXPERIMENTAL flip without operator ACK  
- Treating LLM self-approval as human oversight  

**NO_HELD:** Raft,N>2,multi-primary,ML,R2,R3,plaintext,Vault-ACME-req,GIA,SLO_chase,tag_schema,EVERY_fsync

---

## 12. Related

- `docs/oversight/deadman-v1.md`
- `docs/schema/oversight/orchestrator_v0.md`
- `docs/capabilities/MESH_ORCHESTRATOR_OVERSIGHT.md`
- `src/neural_mesh/packaging/orchestrator_oversight.py`
- `tests/test_orchestrator_oversight_cycle65.py`
- `docs/design/ORCHESTRATOR_CONTINUITY_DESIGN.md` · `ORCHESTRATOR_JUDGE_ROUTING_DESIGN.md`
- `docs/design/L_JUDGE_LIVE_ADAPTER_SAFETY_CASE.md`
