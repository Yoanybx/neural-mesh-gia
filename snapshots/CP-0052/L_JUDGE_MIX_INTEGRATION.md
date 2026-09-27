# L_judge MIX Integration Design

**Status:** INTEGRATION DESIGN (docs + mock-tested contract; no live engine)  
**Cycle / Checkpoint:** 48 / CP-0052  
**Date:** 2026-09-26 America/New_York (EDT)  
**Extends:** `docs/design/L_JUDGE_MIX_DESIGN.md` · schemas `docs/schema/judge/v0.md`  
**Non-claim:** Mesh ≠ frontier model. DO_NOT_TRAIN_70B_NOW. L_GIA = NO_HELD.

---

## 1. Intent

Concrete **integration contract** for Path B MIX: call an **external** frontier
MLLM/LLM as judgment engine **under Mesh policy** via control-plane I2..I6 style.
This cycle ships design + in-test mock validation only — **no live API keys**,
no train, no GIA unlock, no Raft/N>2.

Upstream: C43 design · C47 schema stubs. Downstream: runtime adapter CPs (later).

---

## 2. End-to-end sequence (I2..I6)

```
┌────────────┐   inject goal+continuity+OBS    ┌──────────────────┐
│ Caller     │ ───────────────────────────────► │ Mesh L_judge gate│
│ (shell/    │   JudgeRequest (+InjectionEnv)   │ (I2/I4/I5/I6)    │
│  control)  │                                  └────────┬─────────┘
└────────────┘                                           │
     ▲                                    policy dry-run / fence
     │                                           │
     │                              ┌────────────▼────────────┐
     │                              │ External engine (ephem) │
     │                              │  OR MockLJudge (tests)  │
     │                              └────────────┬────────────┘
     │                                           │ structured judgment
     │                              ┌────────────▼────────────┐
     │   JudgeResponse + receipt_id │ Parse + ABORT/allow     │
     └──────────────────────────────┤ Emit JudgeReceipt+OBS   │
                                    │ Append EvidenceEntry    │
                                    └─────────────────────────┘
```

| Surface | Integration duty |
|---------|------------------|
| **I2** | Verbs `judge.dry_run` → `judge.submit` → `judge.status` / `judge.cancel`; idempotency; error taxonomy |
| **I3** | Rehydrate `GoalRecord` + `ContinuityState` + prior evidence digests into request; engine context not SoT |
| **I4** | Output advisory (A0/A1) until oversight; dry-run **required** before `live_advisory` side-effect path |
| **I5** | Human pause/deny/kill wins; judge recommends only |
| **I6** | Hash-chained `JudgeReceipt` + OBS; no-audit ⇒ no-action |

---

## 3. Call LLM judge — interface

### 3.1 Adapter surface (contract)

```text
class LJudgeMixPort:
    def dry_run(self, req: JudgeRequest) -> JudgeResponse
    def submit(self, req: JudgeRequest) -> JudgeResponse
    def status(self, request_id: str) -> JudgeResponse | Pending
    def cancel(self, request_id: str) -> CancelAck
```

Live engines bind behind `EngineTransport.call(prompt_bundle) -> raw_text`.
**Tests bind `MockLJudgeTransport`** (deterministic JSON; no network; no secrets).

### 3.2 Transport non-goals

- No API keys in repo / env required for this CP
- No plaintext silent channels (TLS/config-ref only when wired later)
- No training / fine-tune / weight download (`DO_NOT_TRAIN_70B_NOW`)

---

## 4. Injection envelope (goals + continuity + OBS)

Before any engine call, Mesh builds `InjectionEnv` and merges into the prompt
bundle (content-addressed; digests recorded on the request):

```json
{
  "schema": "mesh.judge.injection/v0",
  "goal": {
    "goal_id": "goal:<hash16>",
    "version": 1,
    "content_digest": "sha256:...",
    "title": "short",
    "terminal": false
  },
  "continuity": {
    "continuity_id": "cont:<hash16>",
    "state": "RUNNING|READY|...",
    "step_id": "step:...",
    "resume_token": null,
    "last_receipt_id": "rcpt:...|null"
  },
  "obs_evidence": [
    {
      "entry_id": "ev:<hash16>",
      "kind": "judge_receipt|obs|action|abort|probe",
      "payload_digest": "sha256:...",
      "prev_entry_hash": "sha256:...|null"
    }
  ],
  "policy_bundle_id": "policy:<id>",
  "fence": {"dual_primary": 0, "minority_writes": 0}
}
```

Rules:

1. Missing `goal_id` when policy requires one → `ABORT` / `SCHEMA_INVALID`.
2. `dual_primary != 0` → refuse submit (fence); receipt still recorded if audit sink up.
3. Engine must not be treated as authority for goal/continuity mutation.
4. `rationale_ephemeral` disposable; durable = digests + receipt + evidence chain.

---

## 5. Parse structured judgment

Engine raw text → strict parse to `JudgeResponse` (`mesh.judge.response/v0`):

| Parse outcome | Verdict / code |
|---------------|----------------|
| Valid JSON matching schema | Use engine `verdict` if in `{ACCEPT,REJECT,ABSTAIN,ABORT}` |
| Missing required fields | `ABORT` / `SCHEMA_INVALID` |
| Unknown verdict enum | `ABORT` / `SCHEMA_INVALID` |
| Truncated / non-JSON | `ABSTAIN` or `ABORT` per policy (default **ABORT** if `forbid_silent_accept`) |
| Confidence out of [0,1] | clamp+flag or `ABORT` / `SCHEMA_INVALID` (policy) |

Parser **never** invents `ACCEPT` on failure. Mock path returns already-structured
dicts (skip raw parse) but still runs the same schema gate.

---

## 6. ABORT / allow policy

| Condition | Result |
|-----------|--------|
| Schema invalid (request or response) | `ABORT` / `SCHEMA_INVALID`; no side effects |
| Policy forbid / bundle deny | `ABORT` / `POLICY_ABORT`; receipt recorded |
| `mode=live_advisory` without prior dry_run ACCEPT (same idempotency family) | Hard reject |
| Engine timeout | `ABSTAIN` or `ABORT` (policy); never silent ACCEPT |
| dual_primary ≠ 0 | Fence refuse |
| Audit sink missing | no-audit = no-action |
| Human I5 deny/kill | `ABORT` / `HUMAN_ABORT` |

**Allow path:** dry_run ACCEPT → (optional) submit live_advisory → receipt + OBS +
evidence append → caller gets `JudgeResponse` with `receipt_id`.

---

## 7. Receipt schema (Mesh-owned)

Unchanged core from design/stub; integration adds chaining + OBS bind:

```json
{
  "schema": "mesh.judge.receipt/v0",
  "receipt_id": "rcpt:<hash16>",
  "request_digest": "sha256:...",
  "response_digest": "sha256:...",
  "injection_digest": "sha256:...",
  "goal_id": "goal:<hash16>",
  "continuity_id": "cont:<hash16>|null",
  "policy_bundle_id": "policy:<id>",
  "verdict": "ACCEPT|REJECT|ABSTAIN|ABORT",
  "obs_event_id": "obs:...",
  "evidence_entry_id": "ev:...",
  "created_hlc": "hlc-or-hybrid",
  "prev_receipt_hash": "sha256:...|null",
  "node_id": "node:...",
  "dual_primary": 0
}
```

`receipt_id` = hash16 of canonical `(request_digest, response_digest, prev_receipt_hash)`.
Hash chain must verify on read for reconstructibility.

---

## 8. Mock judge (this CP)

`tests/test_l_judge_integration_cycle48.py` embeds `MockLJudgePort`:

- No network / no API keys
- Deterministic ACCEPT/REJECT/ABORT from request mode + injected fence flags
- Emits hash-chained receipts + fake OBS/evidence ids
- Proves dry_run gate, schema ABORT, dual_primary fence

**Not shipped:** `src/neural_mesh/judge_*.py` runtime codec (still deferred).

---

## 9. Non-goals

- Train / fine-tune / host 70B (`DO_NOT_TRAIN_70B_NOW`)
- Live provider wiring / SaaS / economy / settlement
- L_GIA / consciousness / AGI claims
- Raft / N>2 / multi-primary runtime
- Agent-shell as policy authority (shell remains client; see spike plan)
- Plaintext engine channels

**NO_HELD:** Raft,N>2,multi-primary,ML,R2,R3,plaintext,Vault-ACME-req,GIA,SLO_chase,tag_schema,EVERY_fsync

---

## 10. Related

- `docs/design/L_JUDGE_MIX_DESIGN.md`
- `docs/design/DURABLE_GOALS_CONTINUITY_DESIGN.md`
- `docs/design/AGENT_SHELL_ADAPTER_SPIKE.md`
- `docs/schema/judge/v0.md` · `docs/schema/judge/injection_v0.md`
- `docs/capabilities/MESH_L_JUDGE_MIX_INTEGRATION.md`
- Blueprint I2..I6: `council/blueprint/FINAL_BLUEPRINT_ROOT.md`
