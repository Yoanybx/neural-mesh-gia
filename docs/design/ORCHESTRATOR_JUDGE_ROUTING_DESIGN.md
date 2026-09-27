# Orchestrator Judge Routing — Design

**Status:** DESIGN ONLY (mock router + schema; **no live API**, no train, no src codec)  
**Cycle / Checkpoint:** 60 / CP-0064  
**Date:** 2026-09-26 America/New_York (EDT)  
**Theme:** `Orchestrator_judge_routing_DESIGN`  
**Authority:** DeepSeek C59 NEXT Option 1 (ranked) after 0.19 design-set signoff v2  
**Operator intent:** Mesh = ultra-advanced **reasoning orchestrator** (control plane over
judgment engines) — **not** a frontier LLM itself. Aspirational labels stay out of L6.  
**Extends:** `L_JUDGE_MIX_DESIGN.md` · `L_JUDGE_LIVE_ADAPTER_DESIGN.md` ·
`DURABLE_GOALS_CONTINUITY_DESIGN.md` · `AGENT_SHELL_EXTENDED_SCENARIOS.md` ·
`fabric/M2_MEMBERSHIP_REJOIN_DESIGN.md` · `fabric/M3_WAN_MODEL_DESIGN.md`  
**Non-claim:** Mesh ≠ frontier model. DO_NOT_TRAIN_70B_NOW. L_GIA = NO_HELD.
M1 = NO_CONSENSUS_YET (dual-judge **advisory** ≠ consensus protocol).

---

## 1. Intent

Design how Mesh **routes goals/workloads** to:

| Target | Role |
|--------|------|
| **L_judge MIX** | External judgment engine(s) under Mesh policy (dry_run mock path) |
| **agent_shell** | Bounded tool workloads (CP-0053/0062 mock pipeline) |

Mesh remains the verifiable nervous system (H1..H8 + I2/I4/I5/I6 conceptual).
Engines are rented/ephemeral; Mesh owns goals, evidence, continuity, receipts, ABORT.

| This CP ships | Explicitly deferred |
|---------------|---------------------|
| Routing policy design + schema stub | Live multi-engine HTTPS/SDK |
| Mock `OrchestratorRouter` + registry | Runtime codec in `src/neural_mesh/judge_*.py` |
| Neg tests T-route-a/b/c | Dual-judge as M1 consensus |
| Continuity / oversight hooks (design) | GIA / train / SaaS / settlement |

---

## 2. Ownership boundary (hard)

```
┌──────────────────────────────────────────────────────────────┐
│ Mesh Orchestrator (this design)                              │
│  • classify workload + action class                          │
│  • read M2 member state + M3 latency band                    │
│  • consult JudgeCapabilitiesRegistry                         │
│  • select policy: SINGLE | DUAL_ADVISORY | FALLBACK | ABORT  │
│  • gate A3/A4 via I5 oversight                               │
│  • emit RoutingReceipt (hash-chained) + continuity hooks     │
└───────────────────┬───────────────────┬──────────────────────┘
                    │                   │
                    ▼                   ▼
           L_judge MIX (mock)    agent_shell (mock)
```

| Concern | Owner | Must NOT |
|---------|-------|----------|
| Engine selection / fallback | Mesh orchestrator | Engine self-elect |
| Policy / ABORT / fence | Mesh | Adapter override |
| Dual-judge “agreement” | **Advisory** only | Claim M1 consensus / Raft |
| Goal / continuity SoT | Mesh substrate | Engine chat as SoT |
| Credentials / live transport | RefuseTransport default | Keys in repo; live=ENABLED |
| Training / fine-tune | **FORBIDDEN** | Either side |

---

## 3. Inputs (routing envelope)

### 3.1 WorkloadClass

| Class | Typical target | Notes |
|-------|----------------|-------|
| `JUDGE_ADVISORY` | L_judge | A0/A1 semantic judgment |
| `JUDGE_CRITIQUE` | L_judge (prefer dual advisory) | Ranking / critique |
| `SHELL_BOUNDED` | agent_shell | Single-shot allowlisted tools |
| `SHELL_MULTI_TURN` | agent_shell | Bounded multi-turn (CP-0062) |
| `SAFETY_PROBE` | Mesh-local probes | May skip engine |
| `CONTINUITY_RESUME` | prior target + continuity | Resume via ContinuityState |

### 3.2 ActionClass (I4 safety tier)

| Class | Meaning | Orchestrator gate |
|-------|---------|-------------------|
| **A0** | Observe / classify | Auto allow under dry_run |
| **A1** | Advisory recommend | Auto allow under dry_run |
| **A2** | Soft side-effect (reversible, local) | dry_run required; optional oversight |
| **A3** | Hard side-effect / external act | **Human approve/deny required** (I5) |
| **A4** | Irreversible / high-blast | **Human approve + deadman** (I5) |

### 3.3 Environment inputs (composed, not reinvented)

| Input | Source | Effect on route |
|-------|--------|-----------------|
| `member_state` | M2 MembershipSM | Only `ACTIVE` (T2\|T3) may invoke judge/shell |
| `latency_band` | M3 WanModel | Prefer low-latency judge; RTT_x ⇒ FALLBACK or ABORT |
| `dual_primary` | H3 fence | Must be **0** else `FENCE` |
| `live_api_enabled` | safety constant | Hard **False**; live path → `ROUTE_LIVE_DISABLED` |
| `goal_id` / `continuity_id` | durable goals | Attached to every receipt; resume hooks |

### 3.4 JudgeCapabilitiesRegistry (mock)

Each registered engine advertises **non-secret** capability:

```json
{
  "schema": "mesh.judge.capability/v0",
  "engine_id": "judge:mock-a",
  "provider": "mock",
  "model_hint": "mock-judge-a",
  "supports": ["JUDGE_ADVISORY", "JUDGE_CRITIQUE"],
  "max_latency_band": "RTT_mid",
  "trust_floor": "T2",
  "live": false
}
```

Registry is Mesh-owned config; no API keys; mock engines only this CP.

---

## 4. Routing policies

| Policy | Behavior |
|--------|----------|
| **SINGLE_JUDGE** | Pick one capable engine; emit one invocation plan |
| **DUAL_JUDGE_ADVISORY** | Invoke two engines; compare digests; **advisory** agreement only — **not** M1 consensus / Raft / quorum |
| **FALLBACK_CHAIN** | Ordered list; on `ENGINE_*` / timeout / capability miss → next; exhaust → ABORT |
| **ABORT_ON_MISMATCH** | Dual advisory: verdict or response-digest mismatch → `ROUTE_JUDGE_MISMATCH` ABORT (fail closed) |

Default policy by class (design):

| WorkloadClass | Default policy |
|---------------|----------------|
| JUDGE_ADVISORY | SINGLE_JUDGE |
| JUDGE_CRITIQUE | DUAL_JUDGE_ADVISORY (+ ABORT_ON_MISMATCH) |
| SHELL_* | SINGLE path → agent_shell (not an LLM judge) |
| SAFETY_PROBE | Mesh-local (no engine) |
| CONTINUITY_RESUME | Restore prior policy from ContinuityState / last RoutingReceipt |

Latency band influence (design):

| Band | Preference |
|------|------------|
| RTT_lo / RTT_mid | Prefer registry engines with `max_latency_band ≥ band` |
| RTT_hi | Prefer SINGLE; dual only if both engines tolerate hi |
| RTT_x | No dual; FALLBACK to Mesh-local ABORT/refuse unless stress-flag |

---

## 5. Decision algorithm (pseudocode)

```text
def route(env: RoutingEnvelope) -> RoutingDecision:
    if env.live_api_enabled: abort ROUTE_LIVE_DISABLED
    if env.dual_primary != 0: abort FENCE
    if env.n_members > 2: abort ROUTE_N_GT2_REFUSED
    if env.member_state != ACTIVE or env.trust_tier not in {T2,T3}:
        abort ROUTE_MEMBER_NOT_ACTIVE
    if env.action_class in {A3, A4} and not env.oversight.approved:
        abort ROUTE_OVERSIGHT_REQUIRED   # I5 approve/deny(/deadman for A4)
    if env.action_class == A4 and not env.oversight.deadman_ok:
        abort ROUTE_DEADMAN_REQUIRED

    engines = registry.capable(env.workload_class, env.latency_band)
    policy = select_policy(env.workload_class, env.latency_band, env.prefer_dual)

    if env.workload_class.startswith("SHELL"):
        return Decision(target=AGENT_SHELL, policy=SINGLE, engines=[])
    if env.workload_class == SAFETY_PROBE:
        return Decision(target=MESH_LOCAL, policy=SINGLE, engines=[])

    if policy == SINGLE_JUDGE:
        if not engines: abort ROUTE_NO_CAPABLE_ENGINE
        return Decision(target=L_JUDGE, policy=SINGLE, engines=[engines[0]])
    if policy == DUAL_JUDGE_ADVISORY:
        if len(engines) < 2: abort ROUTE_DUAL_UNDERPROVISIONED
        return Decision(target=L_JUDGE, policy=DUAL, engines=engines[:2],
                        abort_on_mismatch=True)
    if policy == FALLBACK_CHAIN:
        if not engines: abort ROUTE_NO_CAPABLE_ENGINE
        return Decision(target=L_JUDGE, policy=FALLBACK, engines=engines)

    abort ROUTE_POLICY_UNKNOWN
```

**M1 fence:** Dual-judge agreement **never** upgrades to “cluster consensus.”
`M1=NO_CONSENSUS_YET` unchanged. Label dual results `advisory_agreement` only.

---

## 6. Receipts

Every decision (ALLOW or ABORT) emits `mesh.orchestrator.routing_receipt/v0`:

```json
{
  "schema": "mesh.orchestrator.routing_receipt/v0",
  "receipt_id": "rcpt:<hash16>",
  "decision": "ALLOW|ABORT",
  "policy": "SINGLE_JUDGE|DUAL_JUDGE_ADVISORY|FALLBACK_CHAIN|MESH_LOCAL",
  "target": "L_JUDGE|AGENT_SHELL|MESH_LOCAL|NONE",
  "workload_class": "JUDGE_ADVISORY",
  "action_class": "A1",
  "engine_ids": ["judge:mock-a"],
  "reason": "capable+ACTIVE+RTT_mid",
  "prompt_hash": "sha256:...|null",
  "response_hash": "sha256:...|null",
  "goal_id": "goal:<hash16>",
  "continuity_id": "cont:<hash16>|null",
  "member_state": "ACTIVE",
  "latency_band": "RTT_mid",
  "oversight": {"required": false, "approved": null, "deadman_ok": null},
  "abort": {"code": null, "reason": null},
  "dual_primary": 0,
  "live_api": false,
  "advisory_only": true,
  "prev_receipt_hash": "sha256:...|null",
  "created_hlc": "..."
}
```

Invariants: `dual_primary==0`, `live_api==false`, hash chain via `prev_receipt_hash`.
For dual advisory, both engines’ prompt/response digests recorded; mismatch → ABORT
with code `ROUTE_JUDGE_MISMATCH` (no silent ACCEPT).

---

## 7. Oversight hooks (I5 compose)

| Hook | When | Effect |
|------|------|--------|
| `approve` | A3/A4 before ALLOW | Sets `oversight.approved=true` |
| `deny` | Operator deny | ABORT `ROUTE_OVERSIGHT_DENIED` |
| `pause` | Mid-flight | Continuity → PAUSED; no new routes |
| `kill` | Emergency | Continuity → ABORTED; refuse further |
| `deadman` | A4 only | Must refresh within TTL else ABORT `ROUTE_DEADMAN_REQUIRED` |
| `consent_revoke` | Any | Drops approval; subsequent routes re-gate |

Design-only: mock `OversightGate` records decisions; no UI; no live kill channel.

---

## 8. Durable goals / continuity hooks

| Hook | Behavior |
|------|----------|
| `attach_goal(goal_id)` | Required on every RoutingEnvelope |
| `attach_continuity(continuity_id)` | Optional; required for CONTINUITY_RESUME |
| `on_allow` | Append EvidenceEntry kind=`routing_receipt`; advance ContinuityState step |
| `on_abort` | EvidenceEntry + ContinuityState → BLOCKED or ABORTED per code |
| `resume` | Load last RoutingReceipt; re-validate member/band/oversight; re-route |

Engine context windows are **not** continuity SoT (see `DURABLE_GOALS_CONTINUITY_DESIGN.md`).

---

## 9. ABORT codes (orchestrator)

| Code | Trigger |
|------|---------|
| `ROUTE_LIVE_DISABLED` | live path while live=DISABLED |
| `ROUTE_MEMBER_NOT_ACTIVE` | member ≠ ACTIVE or tier ∉ {T2,T3} |
| `ROUTE_MEMBER_DRAINING` | DRAINING mid-route |
| `ROUTE_OVERSIGHT_REQUIRED` | A3/A4 without approve |
| `ROUTE_OVERSIGHT_DENIED` | human deny |
| `ROUTE_DEADMAN_REQUIRED` | A4 without deadman |
| `ROUTE_NO_CAPABLE_ENGINE` | registry miss |
| `ROUTE_DUAL_UNDERPROVISIONED` | dual policy but <2 engines |
| `ROUTE_JUDGE_MISMATCH` | dual advisory digest/verdict mismatch |
| `ROUTE_FALLBACK_EXHAUSTED` | fallback chain empty |
| `ROUTE_N_GT2_REFUSED` | N>2 claim |
| `ROUTE_POLICY_UNKNOWN` | unknown policy id |
| `ROUTE_SCHEMA_INVALID` | envelope schema fail |
| `FENCE` | dual_primary ≠ 0 |

Negative tests:

| ID | Trigger | Expect |
|----|---------|--------|
| **T-route-a** | route while JOINING/LEFT/REJOIN/ATTESTING/DRAINING | `ROUTE_MEMBER_NOT_ACTIVE` / `ROUTE_MEMBER_DRAINING` |
| **T-route-b** | A3/A4 without approve (A4 also without deadman) | `ROUTE_OVERSIGHT_REQUIRED` / `ROUTE_DEADMAN_REQUIRED` |
| **T-route-c** | dual mismatch; N>2; live=True; dual_primary≠0; no capable engine | matching ABORT / `FENCE` |

---

## 10. Explicit non-goals (held)

- live=ENABLED / API keys / frontier Mesh / train-70B / GIA  
- Raft / N>2 / multi-primary / pkg0190 / v0.19.0 tag  
- Dual-judge as M1 consensus protocol  
- Settlement / IOU / SaaS multi-tenant orchestrator product  
- Consciousness vocabulary outside L6  

**NO_HELD:** Raft,N>2,multi-primary,ML,R2,R3,plaintext,Vault-ACME-req,GIA,SLO_chase,tag_schema,EVERY_fsync

---

## 11. Related

- `docs/schema/judge/routing_v0.md`
- `docs/capabilities/MESH_ORCHESTRATOR_JUDGE_ROUTING.md`
- `src/neural_mesh/packaging/orchestrator_judge_routing.py`
- `tests/test_orchestrator_judge_routing_cycle60.py`
