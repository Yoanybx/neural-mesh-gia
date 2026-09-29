# Gate 6 — Multi-canary measurement (CP-0079 pack + CP-0080 drills)

**Status:** **MEASURED** **pack n=6 (1 real, 5 mock)** (CP-0079) + CP-0080 M-KILL-2/M-ABORT-3 · **seal_candidate=true** · **CP-0086:** live-measurement seal **SEALED** (`n_real_http_gate6_total=3` ≥ bar 3) · product permanent 「listo」 **blocked on F4 ACK unsigned**  
**Date:** 2026-09-28 ~22:43 EDT (America/New_York)  
**Author:** Grok Bot `<grok-bot@local>`  
**Upstream:** `GATE5_MULTI_CANARY_EVIDENCE.md` · `GATE5_CP0080_DRILL_LEDGER.json` · `EVIDENCE_CP_0080_KILL_ABORT_DRILLS.md`  
**Design:** `GATE6_METRIC_COMPLETION_DESIGN.md` (CP-0077) · `GATE6_LIVE_ACCEPTANCE_METRICS.md`

**Does not** unlock NO_HELD · **does not** flip module LIVE permanently · F4 product ACK **UNSIGNED**.

## Sample policy check

| Rule | Required | Observed |
|------|----------|----------|
| n ≥ N_min | 5 | **6** = 1 real + 5 mock (CP-0079) / **7** mock re-run with E-CONFLICT (CP-0080) |
| N_edge ≥ 3 | 3 | **≥5** |
| N_kill_live ≥ 1 | 1 | **1** (E-KILL) |
| N_abort ≥ 1 | 1 | **≥3** (+ E-CONFLICT) |
| N_ledger_kill ≥ 1 | 1 | **1** (oversight+abort) |
| Independence | separate ids + LIVE false between | **Yes** |
| Final RefuseTransport + module LIVE false | Yes | **Yes** |

## Metric families (honest)

| Family | Result | Notes |
|--------|--------|-------|
| M-REFUSE-* | **PASS** (post + edges) | Default refuse; E-ANOMALY / post-kill / post-resume |
| M-SEC-* | **PASS** | No secrets in ledger; E-AUTH invalid handle |
| M-ADV-* | **PASS** | Happy ADVISORY; mesh_accept=false |
| M-KILL-1-LIVE | **PASS (pack)** | Mid-window I5 kill → RefuseTransport + continuity ABORT |
| M-KILL-2-BUDGET | **PASS (CP-0080)** | Ops ceiling **100 ms**; observed **0 ms**; ledger ok |
| M-KILL-3-RESUME | **PASS (pack)** | E-RESUME auto-resume correctly failed |
| M-ABORT-1 | **PASS (pack)** | E-ABORT-ACCEPT Mesh ABORT > peer ACCEPT |
| M-ABORT-2 | **PASS (pack)** | E-ANOMALY missing gate → Refuse |
| M-ABORT-3 | **PASS (CP-0080)** | E-CONFLICT conflicting + missing judges fail-closed |
| M-LEDGER-1..2 | **PASS (pack)** | kinds present; kill has oversight+abort |
| M-LEDGER-3 | **PASS** | claim hygiene: seal_candidate ≠ 100% / ≠ product listo |

## Explicit limits

- Prefer phrasing **「pack n=6 (1 real, 5 mock)」** — pack `n_real_http=1` · `n_mock=5`; seal_candidate on **n=6 total**, **not** “5 live”  
- **CP-0086:** Gate6 cumulative `n_real_http_gate6_total=3` (pack 1 + R3 incr 1 + CP-0086 incr 1); live-measurement bar **N_real_http_min=3** **MET** / **SEALED**; product still needs F4  
- seal_candidate ≠ Gate6 **live-measurement seal** ≠ **final product seal** without **signed** F4 product ACK  
- Module `LIVE_API_ENABLED=False` retained per permanent enable policy  
- Streaming not shipped · CI live forbidden  
- F4 **DESIGN_SEALED**; product ACK **UNSIGNED** (ENABLE_UNDER_FENCES ≠ permanent)  
- M-KILL-2 budget is **process-local** (≤100 ms); not a network/provider RTT SLO

## Related

- Prior n=1: `GATE6_CANARY_MEASUREMENT.md` (historical)  
- Policy: `LIVE_API_PERMANENT_ENABLE_POLICY.md`  
- Budget: `docs/ops/M_KILL_2_OPS_KILL_REFUSE_BUDGET.md`  
- F4: `F4_DESIGN_SEALED.md` · `F4_PRODUCT_ENABLE_ACK_DRAFT.md`

---

*End GATE6_MULTI_CANARY_MEASUREMENT — M-KILL-2/M-ABORT-3 PASS; CP-0086 live-measurement SEALED (n=3); F4 ACK unsigned; LIVE False.*
