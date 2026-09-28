# Multi-Judge + Agent-Shell Spike

**Status:** SPIKE EXECUTED (mock-only; live=DISABLED)  
**Cycle / Checkpoint:** 61 / CP-0065  
**Date:** 2026-09-26 America/New_York (EDT)  
**Theme:** `multi_judge_agent_shell_spike`  
**Authority:** DeepSeek C60 NEXT Option 1 (SP4 spike bias after CP-0064 routing design)  
**Composes:** OrchestratorRouter (CP-0064) · agent_shell_extended (CP-0062) ·
two mock judgment engines · M2 MembershipSM churn (CP-0059)  
**Non-claim:** No live LLM · no N>2 · no Raft · no train · no GIA · no SaaS.
M1 = **NO_CONSENSUS_YET** (dual advisory ≠ consensus protocol).

**Hold mock cycle 3 (local hygiene):** disagreement → **ABORT > ACCEPT**. Post-invoke dual digests that diverge emit `SPIKE_JUDGE_DIGEST_DISAGREE` with `abort_provenance.policy=ABORT_GT_ACCEPT`; agreeing dual paths stay `mesh_decision=ADVISORY` / `mesh_accept=False` (routing ALLOW ≠ Mesh ACCEPT ≠ M1).

---

## 1. Intent

Empirically stress CP-0064 routing under a **two-mock-judge + agent_shell** composition
with membership churn **DRAINING → LEFT → REJOIN**, before more design layers stack.

```
Caller ──► MultiJudgeAgentShellSpike
              │
              ├─ M2 MembershipSM (gate ACTIVE T2|T3)
              ├─ OrchestratorRouter (policy select)
              │     ├─ DUAL_JUDGE_ADVISORY (advisory_only)
              │     ├─ FALLBACK_CHAIN
              │     ├─ ABORT_ON_MISMATCH
              │     └─ AGENT_SHELL path
              ├─ MockJudgmentEngine ×2 (invoke + attribution)
              └─ MockAgentShellAdapter (bounded tools)
                    │
              SpikeReceipt (hash-chained; m1=NO_CONSENSUS_YET)
```

Implementation: `src/neural_mesh/packaging/multi_judge_agent_shell_spike.py`  
Tests: `tests/test_multi_judge_agent_shell_spike_cycle61.py`  
No `src/neural_mesh/judge_*.py` codec; no live transport; no keys.

---

## 2. Scenarios exercised

1. **Happy dual advisory:** ACTIVE + two capable engines → ALLOW; attributions for
   both; `advisory_only=True`; `m1_status=NO_CONSENSUS_YET`.
2. **Happy FALLBACK:** RTT_x → FALLBACK_CHAIN; single engine invoke; attribution.
3. **Happy agent_shell:** SHELL_BOUNDED routed + submit/finalize; live=DISABLED.
4. **Churn:** DRAINING → LEFT → REJOIN each ABORT new dual/fallback/shell routes
   (`ROUTE_MEMBER_DRAINING` / `ROUTE_MEMBER_NOT_ACTIVE`).
5. **ABORT_MISMATCH:** injected dual digest disagreement → `ROUTE_JUDGE_MISMATCH`.
6. **No double-invoke:** second invoke of same engine for same request_id →
   `SPIKE_DOUBLE_INVOKE`.
7. **Attribution completeness:** every selected `engine_id` appears in attributions.

Negative tests:

| ID | Trigger | Expect |
|----|---------|--------|
| **T-route-spike-a** | Dual/shell under DRAINING/LEFT/REJOIN | membership ABORT; chain intact |
| **T-route-spike-b** | Dual digest mismatch; missing attribution / double-invoke | `ROUTE_JUDGE_MISMATCH` / `SPIKE_DOUBLE_INVOKE` / `SPIKE_MISSING_ATTRIBUTION` |
| **T-route-spike-c** | N>2, live=ENABLED, dual_primary≠0, FALLBACK exhaust (empty registry) | `ROUTE_N_GT2_REFUSED` / `SPIKE_LIVE_DISABLED` or `ROUTE_LIVE_DISABLED` / `FENCE` / `ROUTE_FALLBACK_EXHAUSTED` |

---

## 3. Receipts / invariants

- Spike receipts schema `mesh.orchestrator.spike_receipt/v0`; hash-chained via
  `prev_receipt_hash`.
- Every ALLOW L_judge path records per-engine attribution (`engine_id`,
  `invoke_ordinal`, digests).
- `dual_primary=0`, `live_api=False`, `advisory_only=True`, `m1_status=NO_CONSENSUS_YET`
  on every spike receipt.
- Routing receipts from OrchestratorRouter remain separately hash-chained.

---

## 4. Explicit non-goals (held)

- Live multi-engine HTTPS/SDK · train-70B · GIA unlock  
- Raft / N>2 runtime / multi-primary  
- Collapsing DUAL_ADVISORY into M1 consensus semantics  
- pkg0190 / v0.19.0 tag · SaaS / settlement  

**NO_HELD:** Raft,N>2,multi-primary,ML,R2,R3,plaintext,Vault-ACME-req,GIA,SLO_chase,tag_schema,EVERY_fsync

---

## 5. Related

- `docs/design/ORCHESTRATOR_JUDGE_ROUTING_DESIGN.md` (CP-0064)
- `docs/design/AGENT_SHELL_EXTENDED_SCENARIOS.md` (CP-0062)
- `docs/design/L_JUDGE_M2_E2E_SPIKE.md` (CP-0061)
- `docs/capabilities/MESH_MULTI_JUDGE_AGENT_SHELL_SPIKE.md`
