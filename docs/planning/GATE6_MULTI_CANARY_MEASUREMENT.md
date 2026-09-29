# Gate 6 — Multi-canary measurement (CP-0079 pack)

**Status:** **MEASURED** pack n=6 under CP-0077 sample policy · **seal_candidate=true** · **≠** product-ready 「listo」 · **≠** permanent LIVE  
**Date:** 2026-09-28 ~22:39 EDT (America/New_York)  
**Author:** Grok Bot `<grok-bot@local>`  
**Upstream:** `GATE5_MULTI_CANARY_EVIDENCE.md` · `GATE5_MULTI_CANARY_LEDGER.json`  
**Design:** `GATE6_METRIC_COMPLETION_DESIGN.md` (CP-0077) · `GATE6_LIVE_ACCEPTANCE_METRICS.md`

**Does not** unlock NO_HELD · **does not** flip module LIVE permanently · F4 still OPEN.

## Sample policy check

| Rule | Required | Observed |
|------|----------|----------|
| n ≥ N_min | 5 | **6** |
| N_edge ≥ 3 | 3 | **5** |
| N_kill_live ≥ 1 | 1 | **1** (E-KILL) |
| N_abort ≥ 1 | 1 | **3** |
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
| M-KILL-2-BUDGET | **PARTIAL** | Latency recorded (0 ms kill path); **ops budget still OPEN** |
| M-KILL-3-RESUME | **PASS (pack)** | E-RESUME auto-resume correctly failed |
| M-ABORT-1 | **PASS (pack)** | E-ABORT-ACCEPT Mesh ABORT > peer ACCEPT |
| M-ABORT-2 | **PASS (pack)** | E-ANOMALY missing gate → Refuse |
| M-ABORT-3 | **DESIGN** | E-CONFLICT not in this pack (residual) |
| M-LEDGER-1..2 | **PASS (pack)** | kinds present; kill has oversight+abort |
| M-LEDGER-3 | **PASS** | claim hygiene: seal_candidate ≠ 100% / ≠ listo |

## Explicit limits

- seal_candidate ≠ Gate6 **final product seal** without ops kill budget + F4 + review  
- M-ABORT-3 (conflict judges) not drilled this pack  
- Streaming not shipped · CI live forbidden  
- Module `LIVE_API_ENABLED=False` retained per permanent enable policy  

## Related

- Prior n=1: `GATE6_CANARY_MEASUREMENT.md` (historical)  
- Policy: `LIVE_API_PERMANENT_ENABLE_POLICY.md`  

---

*End GATE6_MULTI_CANARY_MEASUREMENT — n=6 seal-candidate; M-KILL-2 budget OPEN; F4 OPEN; LIVE False.*
