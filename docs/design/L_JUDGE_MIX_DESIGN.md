# L_judge MIX Adapter — Design (docs only)

**Status:** DESIGN DRAFT (authorized by `COUNCIL_AGREEMENT_HYPERBRAIN_ASTRA`)  
**Cycle / Checkpoint:** 43 / CP-0047  
**Date:** 2026-09-26 America/New_York (EDT)  
**Layer:** L_nervous (DONE @0.18) → **L_judge MIX** (this) → L_GIA (**NO_HELD**)  
**Non-claim:** Mesh ≠ frontier model. Completing 0.18 ≠ hyperbrain. DO_NOT_TRAIN_70B_NOW.

---

## 1. Intent

Attach an **external** frontier MLLM/LLM as a **judgment engine** under Mesh policy.
Mesh remains the verifiable nervous system (identity, fence, OBS, recovery, audit,
ABORT). The engine is **rented/ephemeral**; Mesh substrate holds durable goals and
evidence (see `DURABLE_GOALS_CONTINUITY_DESIGN.md`).

**Path B MIX only** — no train-own-70B, no ML-as-product-layer unlock.

---

## 2. Ownership boundary

| Concern | Owner |
|---------|-------|
| Identity / attestation / trust tiers | Mesh (H1) |
| Dual-primary / minority-write / clock-skew / parity fences | Mesh (H3/H6/H7/H8) |
| OBS telemetry + receipts | Mesh (H4 + packaging provenance) |
| Policy evaluate / ABORT / dry-run gate | Mesh control plane (I2/I4/I5/I6 conceptual) |
| Semantic judgment / ranking / critique text | External L_judge engine |
| Session chat context window | Engine (ephemeral) |
| Goals / evidence / continuity across restarts | Mesh substrate memory |

Shell/UI agents (OpenJarvis etc.) are **clients** of Mesh policy — never a second
policy brain (see theme C in `0.19_SCOPE_DRAFT.md`).

---

## 3. Conceptual control-plane mapping (I2..I6)

Design-only mapping to blueprint L5 surfaces — **no GIA unlock**, no runtime I*
implementation required this cycle:

| Surface | MIX role |
|---------|----------|
| **I2 control-plane** | Verbs: `judge.submit`, `judge.status`, `judge.cancel`, `judge.dry_run`; idempotency keys; error taxonomy (`POLICY_ABORT`, `ENGINE_TIMEOUT`, `SCHEMA_INVALID`, …) |
| **I3 memory/state** | Persist `GoalRecord` / `EvidenceEntry` / `ContinuityState` as Mesh state classes (S0..S3 TBD); engine context is **not** authoritative state |
| **I4 action boundary** | Judgment output is class A0/A1 (advisory) until human oversight promotes; dry-run **required** before any side-effecting act |
| **I5 human oversight** | Pause/deny/kill still Mesh; judge may recommend only |
| **I6 auditability** | Every judge call → hash-chained receipt; no-audit ⇒ no-action |

---

## 4. Interfaces (concrete shapes)

### 4.1 `JudgeRequest` (ingress)

```json
{
  "schema": "mesh.judge.request/v0",
  "request_id": "uuid",
  "idempotency_key": "string",
  "goal_id": "goal:<hash16>",
  "mode": "dry_run | live_advisory",
  "policy_bundle_id": "policy:<id>",
  "inputs": {
    "prompt_ref": "content-addressed-or-inline",
    "artifacts": [{"kind": "text|json|ref", "digest": "sha256:..."}],
    "constraints": {"max_tokens": 0, "timeout_ms": 0, "forbid_side_effects": true}
  },
  "engine": {
    "provider": "external_mllm",
    "model_hint": "deepseek-70b|peer",
    "endpoint_ref": "config-ref-not-secret"
  },
  "continuity_hint": {"step_id": "string", "resume_token": "opaque-or-null"}
}
```

### 4.2 `JudgeResponse` (egress)

```json
{
  "schema": "mesh.judge.response/v0",
  "request_id": "uuid",
  "verdict": "ACCEPT | REJECT | ABSTAIN | ABORT",
  "confidence": 0.0,
  "rationale_digest": "sha256:...",
  "rationale_ephemeral": "optional-plaintext-not-stored-long",
  "recommended_acts": [],
  "abort": {"code": null, "reason": null},
  "receipt_id": "rcpt:<hash16>",
  "engine_meta": {"latency_ms": 0, "model_hint": "string", "truncated": false}
}
```

### 4.3 `JudgeReceipt` (Mesh-owned, durable)

```json
{
  "schema": "mesh.judge.receipt/v0",
  "receipt_id": "rcpt:<hash16>",
  "request_digest": "sha256:...",
  "response_digest": "sha256:...",
  "goal_id": "goal:<hash16>",
  "policy_bundle_id": "policy:<id>",
  "verdict": "ACCEPT|REJECT|ABSTAIN|ABORT",
  "obs_event_id": "obs:...",
  "created_hlc": "hlc-string-or-hybrid",
  "prev_receipt_hash": "sha256:...|null",
  "node_id": "node:...",
  "dual_primary": 0
}
```

### 4.4 Adapter API (pseudocode)

```text
class LJudgeMixAdapter:
    def dry_run(self, req: JudgeRequest) -> JudgeResponse
        """Must not call side-effecting tools; may call engine."""

    def submit(self, req: JudgeRequest) -> JudgeResponse
        """Requires prior dry_run ACCEPT under same idempotency family
           when mode=live_advisory; always emits JudgeReceipt + OBS."""

    def status(self, request_id: str) -> JudgeResponse | Pending
    def cancel(self, request_id: str) -> CancelAck
```

---

## 5. Policy / ABORT semantics

| Condition | Behavior |
|-----------|----------|
| Schema invalid | `ABORT` / `SCHEMA_INVALID`; no engine call |
| Policy forbid | `ABORT` / `POLICY_ABORT`; receipt still recorded |
| Engine timeout / truncate | `ABSTAIN` or `ABORT` per policy; never silent ACCEPT |
| dual_primary ≠ 0 | Refuse new judge submits (fence) |
| Missing audit sink | no-audit=no-action |
| Side-effect without dry-run | Hard reject |

---

## 6. How LLM session amnesia is compensated

External engines forget across sessions. Mesh compensates by:

1. Rehydrating **goal + continuity + prior receipt digests** into each `JudgeRequest`.
2. Treating engine `rationale_ephemeral` as disposable; durable truth is digests + ledger.
3. Never trusting engine memory as authority for goals/progress.

Details: `docs/design/DURABLE_GOALS_CONTINUITY_DESIGN.md`.

---

## 7. Non-goals (this design + 0.19 track)

- Train / fine-tune / host own 70B weights (`DO_NOT_TRAIN_70B_NOW`)
- Claim Mesh is the judgment IQ / surpasses Astra-GPT on multimodal latency
- Unlock L_GIA / consciousness / AGI claims
- Raft / N>2 / multi-primary runtime
- SaaS productization or economy/settlement rails
- Silent plaintext engine channels
- Making the agent-shell the policy authority

**NO_HELD:** Raft,N>2,multi-primary,ML,R2,R3,plaintext,Vault-ACME-req,GIA,SLO_chase,tag_schema,EVERY_fsync

---

## 8. Implementation deferral

CP-0047 shipped **this design doc**. CP-0051 shipped schema stubs.
CP-0052 ships **integration design** + mock-tested contract
(`docs/design/L_JUDGE_MIX_INTEGRATION.md`). Live engine wiring remains future
(still without opening NO_HELD items; DO_NOT_TRAIN_70B_NOW).

## Related

- `docs/design/L_JUDGE_MIX_INTEGRATION.md` (CP-0052 concrete integration)
- `docs/design/DURABLE_GOALS_CONTINUITY_DESIGN.md`
- `docs/planning/0.19_SCOPE_DRAFT.md`
- `council/COUNCIL_AGREEMENT_HYPERBRAIN_ASTRA.md`
- `council/NORTH_STAR_RECALIBRATION.md`
- Blueprint I2..I6: `council/blueprint/FINAL_BLUEPRINT_ROOT.md`
