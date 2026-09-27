# L_judge Mock × M2 Membership SM — E2E Spike

**Status:** SPIKE EXECUTED (mock-only; live=DISABLED)  
**Cycle / Checkpoint:** 57 / CP-0061  
**Date:** 2026-09-26 America/New_York (EDT)  
**Composes:** L_judge MIX mock (CP-0052) + M2 MembershipSM (CP-0059)  
**Non-claim:** No live WAN · no N>2 runtime · no live LLM · no pkg0190 · no GIA.  
**Authority:** DeepSeek C56 Option 1 (SP4 spike bias).

---

## 1. Intent

Wire existing **Mock L_judge** through the **M2 membership state machine** end-to-end
so membership state gates judgment, ABORT paths fire, and receipts stay hash-chained —
without opening any NO_HELD gate.

```
Caller ──► JudgeMembershipBridge ──► MembershipSM (gate)
                 │                         │
                 └──── MockLJudgePort ◄────┘ (only if gate allows)
                           │
                     JudgeReceipt (hash-chained) + OBS/evidence ids
```

Implementation locus: `src/neural_mesh/packaging/l_judge_m2_e2e.py`  
Tests: `tests/test_l_judge_m2_e2e_cycle57.py`  
No `src/neural_mesh/judge_*.py` runtime codec; no live transport.

---

## 2. Membership × judge matrix

| Member state | dry_run | live_advisory (mock) | Notes |
|--------------|---------|----------------------|-------|
| JOINING | ABORT `JUDGE_MEMBER_NOT_ACTIVE` | ABORT | Must attest first |
| ATTESTING | ALLOW | ABORT `JUDGE_MEMBER_ATTESTING_SUBMIT` | Attestation advisory only |
| ACTIVE (T2\|T3) | ALLOW | ALLOW (after dry_run ACCEPT) | Happy path |
| DRAINING | ABORT `JUDGE_MEMBER_DRAINING` | ABORT | New judge refused; in-flight cancelled |
| LEFT | ABORT `JUDGE_MEMBER_NOT_ACTIVE` | ABORT | In-flight cancelled |
| REJOIN | ABORT `JUDGE_MEMBER_NOT_ACTIVE` | ABORT | No shortcut to ACTIVE |

`live_advisory` here is the **mock** advisory mode from CP-0052 (requires prior dry_run
ACCEPT). **`LIVE_API_ENABLED=False`** — no network, no keys, no frontier call.

---

## 3. Scenarios exercised

1. **Happy:** JOINING→ATTESTING→ACTIVE(T2|T3) with dry_run (+ optional mock submit).
2. **DRAINING mid-judgment:** drain cancels PENDING in-flight (`JUDGE_INFLIGHT_CANCELLED`);
   new judge → `JUDGE_MEMBER_DRAINING`.
3. **LEFT/REJOIN with in-flight:** rejoin_intent cancels PENDING; judge refused until
   re-attested ACTIVE.

Negative tests:

| ID | Trigger | Expect |
|----|---------|--------|
| **T-M2-judge-a** | judge while JOINING / LEFT / REJOIN | `JUDGE_MEMBER_NOT_ACTIVE` |
| **T-M2-judge-b** | new judge while DRAINING; mid-judgment cancel | `JUDGE_MEMBER_DRAINING` / cancel |
| **T-M2-judge-c** | ATTESTING submit; N>2 refuse; LEFT→ACTIVE shortcut | attest-submit ABORT / `MEMBER_N_GT2_REFUSED` / invalid transition |

---

## 4. Receipts / ABORT

- Every gate ABORT and every mock judgment emits a `mesh.judge.receipt/v0` (or abort
  response with `receipt_id`) and advances `prev_receipt_hash` (hash chain).
- Fence: `dual_primary != 0` → `FENCE` (unchanged from CP-0052).
- No-audit → `NO_AUDIT`. Schema fail → `SCHEMA_INVALID`.
- N_CAP=2 held via MembershipSM (`MEMBER_N_GT2_REFUSED`).

---

## 5. Explicit non-goals (held)

- Real WAN / M3 runtime spike · Raft · N>2 · multi-primary  
- live=ENABLED / API keys / frontier transport · train-70B · GIA  
- pkg0190 / v0.19.0 tag · SaaS / settlement  

**NO_HELD:** Raft,N>2,multi-primary,ML,R2,R3,plaintext,Vault-ACME-req,GIA,SLO_chase,tag_schema,EVERY_fsync

---

## 6. Related

- `docs/design/L_JUDGE_MIX_INTEGRATION.md` (CP-0052)
- `docs/design/fabric/M2_MEMBERSHIP_REJOIN_DESIGN.md` (CP-0059)
- `docs/design/L_JUDGE_LIVE_ADAPTER_SAFETY_CASE.md` (CP-0058; stays ahead of live)
- `docs/capabilities/MESH_L_JUDGE_M2_E2E.md`
