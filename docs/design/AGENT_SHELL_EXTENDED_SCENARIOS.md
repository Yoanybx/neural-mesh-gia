# Agent-Shell Extended Scenarios — Spike

**Status:** SPIKE EXECUTED (mock-only; live=DISABLED)  
**Cycle / Checkpoint:** 58 / CP-0062  
**Date:** 2026-09-26 America/New_York (EDT)  
**Extends:** CP-0053 agent_shell_spike_execution  
**Composes (optional):** CP-0061 L_judge × M2 MembershipSM  
**Non-claim:** No live LLM · no N>2 · no settlement · no pkg0190 · no GIA.  
**Authority:** DeepSeek C57 Option 1 (SP4 spike bias).

---

## 1. Intent

Stress the **agent_shell** half of the PC-evaluator path under load after CP-0061
proved L_judge×M2. Extend the CP-0053 mock pipeline with:

1. **Multi-turn bounded workload** (tool_call / tool_result loops under max_steps)
2. **Safety-probe matrix** (schema / fence / audit / tool / policy / max_steps / NO_DRY_RUN)
3. **ABORT variants** including membership-gated codes
4. **Receipt chain verify under churn** (DRAINING / LEFT / REJOIN cancel in-flight)

```
bounded multi-turn → normalize → probe matrix → [optional Mock L_judge dry_run]
  → hash-chained receipts → membership churn cancels → chain still reconstructible
```

Implementation locus: `src/neural_mesh/packaging/agent_shell_extended.py`  
Tests: `tests/test_agent_shell_extended_cycle58.py`  
No live shell vendor; no settlement; `LIVE_API_ENABLED=False`.

---

## 2. Membership × shell matrix (when composed)

| Member state | submit / ingest / finalize | Notes |
|--------------|----------------------------|-------|
| JOINING / LEFT / REJOIN | ABORT `SHELL_MEMBER_NOT_ACTIVE` | Must reach ACTIVE T2\|T3 |
| ATTESTING | ABORT `SHELL_MEMBER_NOT_ACTIVE` | Shell needs ACTIVE (unlike judge dry_run) |
| ACTIVE (T2\|T3) | ALLOW | Happy multi-turn + optional judge dry_run |
| DRAINING | ABORT `SHELL_MEMBER_DRAINING`; in-flight → `SHELL_INFLIGHT_CANCELLED` | Critical ABORT |

Optional finalize `use_judge=True` routes dry_run through shared MockLJudgePort
(same MembershipSM via `ShellMembershipBridge.ensure_judge()`).

---

## 3. Scenarios exercised

1. **Happy multi-turn:** ACTIVE member; N turns echo/hash_probe; finalize ACCEPT; receipt.
2. **Probe matrix:** each probe failure → ABORT with expected code (never silent ACCEPT).
3. **Churn:** DRAINING mid-workload cancels; LEFT/REJOIN cancel; receipt chain verifies after.
4. **Compose L_judge:** finalize with Mock L_judge dry_run under ACTIVE; hash chain includes judge receipt id.

Negative tests:

| ID | Trigger | Expect |
|----|---------|--------|
| **T-shell-a** | shell while JOINING / LEFT / REJOIN / ATTESTING | `SHELL_MEMBER_NOT_ACTIVE` |
| **T-shell-b** | new shell / mid-workload while DRAINING | `SHELL_MEMBER_DRAINING` / `SHELL_INFLIGHT_CANCELLED` |
| **T-shell-c** | probe matrix (schema/fence/tool/policy/audit/max_steps/NO_DRY_RUN); N>2 refuse | matching ABORT / `MEMBER_N_GT2_REFUSED` |

---

## 4. Receipts / ABORT

- Every gate ABORT and every finalize emits `mesh.shell.receipt/v0` and advances
  `prev_receipt_hash` (hash chain).
- `verify_receipt_chain(receipts)` reconstructs after churn.
- Fence: `dual_primary != 0` → `FENCE`. No-audit → `NO_AUDIT`.
- N_CAP=2 held via MembershipSM.

---

## 5. Explicit non-goals (held)

- Settlement / IOU / tokenless economy / SaaS  
- live=ENABLED / API keys / frontier / train-70B / GIA  
- Raft / N>2 / multi-primary / pkg0190 / v0.19.0 tag  

**NO_HELD:** Raft,N>2,multi-primary,ML,R2,R3,plaintext,Vault-ACME-req,GIA,SLO_chase,tag_schema,EVERY_fsync

---

## 6. Related

- `docs/design/AGENT_SHELL_SPIKE_EXECUTION.md` (CP-0053)
- `docs/design/L_JUDGE_M2_E2E_SPIKE.md` (CP-0061)
- `docs/capabilities/MESH_AGENT_SHELL_EXTENDED.md`
