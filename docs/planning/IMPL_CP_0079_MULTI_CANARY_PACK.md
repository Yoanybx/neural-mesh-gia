# IMPL CP-0079 — Multi-canary measurement pack (n≥N_min=5) + permanent enable policy

**Status:** **AUTHORIZED MEASUREMENT / POLICY CP** under fences  
**Cycle / Checkpoint:** 75 / **CP-0079**  
**Date:** 2026-09-28 ~22:40 EDT (America/New_York)  
**Author:** Grok Bot `<grok-bot@local>`  
**Tip at mint base:** `ee0c0c6` (CP-0078)  
**Design authority:** **CP-0077** `GATE6_METRIC_COMPLETION_DESIGN.md` (N_min=5 · edges · M-KILL/ABORT/LEDGER)  
**Package:** **0.18.0 HELD** · **NO_HELD unchanged** · D3 NOT ACKed · M1=NO_CONSENSUS_YET

---

## 0. What this is / is not

| Is | Is not |
|----|--------|
| Multi-canary harness + executed pack toward n≥5 with E-* edges | Gate6 live-measurement **final seal** (seal-*candidate* only) |
| Permanent LIVE_API enable **policy** + Gate5 runbook §8 | F4 product-enable ACK (still OPEN) |
| Honest real+mock mix under free-tier quota | Permanent module `LIVE_API_ENABLED=True` |
| Leaves module LIVE **False** after pack | NO_HELD / D3 / keys-in-git unlock |

### Claim hygiene (I-5 / DeepSeek handoff audit)

Prefer phrasing **「pack n=6 (1 real, 5 mock)」**:

| Field | Binding |
|-------|---------|
| **n** | **6** total attempts (meets N_min=5 sample policy) |
| **n_real_http** | **1** (E-HAPPY Gemini free HTTP 200) |
| **n_mock** | **5** (E-KILL / E-ABORT-ACCEPT / E-AUTH / E-ANOMALY / E-RESUME) |
| **seal_candidate** | **true** on **n=6 total**, **not** on “5 live” / “n=5 real HTTP” |

Do **not** claim five live HTTP canaries, five live samples, or “n=5 live sealed.” seal_candidate ≠ Gate6 final product seal ≠ F4 product ACK.

---

## 1. Artifacts

| Artifact | Path |
|----------|------|
| Harness | `src/neural_mesh/packaging/l_judge_multi_canary_pack.py` |
| Permanent enable policy | `docs/planning/LIVE_API_PERMANENT_ENABLE_POLICY.md` |
| Gate5 runbook §8 | `GATE5_LIVE_FLAG_FLIP_RUNBOOK.md` |
| Evidence | `GATE5_MULTI_CANARY_EVIDENCE.md` · `GATE5_MULTI_CANARY_LEDGER.json` |
| Gate6 measurement update | `GATE6_CANARY_MEASUREMENT.md` · `GATE6_MULTI_CANARY_MEASUREMENT.md` |
| Tests | `tests/test_l_judge_multi_canary_pack_cycle75.py` |
| Council note | `council/NOTE_IMPL_CP_0079_MULTI_CANARY_PACK.md` |

---

## 2. Pack plan (default)

| # | Edge | Mode | Primary metrics |
|---|------|------|-----------------|
| 1 | E-HAPPY | real_http (Gemini free) | M-ADV / M-REFUSE / M-LEDGER-1 |
| 2 | E-KILL | mock_local + live window | M-KILL-1-LIVE / M-LEDGER-2 |
| 3 | E-ABORT-ACCEPT | mock_local | M-ABORT-1 |
| 4 | E-AUTH | mock_local | M-REFUSE / M-SEC |
| 5 | E-ANOMALY | mock_local | M-ABORT-2 |
| 6 | E-RESUME | mock_local | M-KILL-3-RESUME |

Independence: separate `request_id` / idempotency key; runtime LIVE restored False between attempts.

---

## 3. Flag posture

| Flag | During attempt window | After pack |
|------|----------------------|------------|
| Module `LIVE_API_ENABLED` | **False** | **False** |
| Runtime LIVE | True only in session | **False** |
| Binding | LiveHttpTransport or Refuse | **RefuseTransport** |
| Permanent product enable | Forbidden without F4 | Policy on disk; F4 OPEN |

---

## 4. Explicit non-goals

- Push / tags / secrets in git  
- Claiming 「listo」 / 100% product live without F4  
- Inventing kill latency SLO numbers (descriptive p50/p95 only)  
- Streaming / Vertex paid / CI live  

---

*End IMPL_CP_0079 — multi-canary + permanent enable policy; module LIVE false; NO_HELD unchanged.*
