# Gate 6 — Canary measurement (post Gate5 canary)

**Status:** **MEASURED** on CP-0075 n=1 (historical) · **superseding pack** CP-0079 n=6 → `GATE6_MULTI_CANARY_MEASUREMENT.md`  
**Date:** 2026-09-28 ~19:47 EDT (America/New_York)  
**Author:** Grok Bot `<grok-bot@local>`  
**Upstream evidence:** `GATE5_CANARY_EVIDENCE.md` · `GATE5_CANARY_LEDGER.json`  
**Metrics design:** `GATE6_LIVE_ACCEPTANCE_METRICS.md` (DESIGN_SEALED)

**Does not** unlock NO_HELD · **does not** claim full live+API 100% product enable · **does not** flip module LIVE_API permanently.

## Measured against M-* (canary sample n=1)

| Metric | Result | Notes |
|--------|--------|-------|
| **M-REFUSE-1** | **PASS** (post) | After canary, runtime LIVE=False; RefuseTransport binding; zero further network from default path |
| **M-REFUSE-2** | **PASS** (unit) | NT-1..NT-10: default `may_enable=False`; NT-10 cleared only with authorized impl + gates (cycle54/71 tests) |
| **M-KILL-1** | **DESIGN+UNIT** | I5 kill → RefuseTransport proven in unit (`test_canary_transport_refuses_after_i5_kill`); not mid-flight killed (no anomaly) |
| **M-SEC-1** | **PASS** | Ledger/docs greppable: no raw key material |
| **M-ADV-1** | **PASS** | Verdict ADVISORY; `mesh_accept=false` |
| **M-ADV-3** | **PASS** | M1 remains NO_CONSENSUS_YET; agree ≠ unlock |
| Correctness (D4-E) | **PASS (sample)** | Synthetic marker returned exactly `MESH_CANARY_OK`; HTTP 200 |
| Reliability | **PASS (sample)** | Single call completed; abort path unused |
| Human factors | **PASS (design)** | I5 armed; final enabled=false; ledger complete |

## Explicit limits

- n=1 free-tier canary ≠ production SLO / multi-provider proof  
- Full LiveHttpTransport codec still **not** shipped  
- Module `LIVE_API_ENABLED=False` retained  
- **n=1 cannot seal** Gate6 live-measurement — see **CP-0077** `GATE6_METRIC_COMPLETION_DESIGN.md` (N_min=5 + edges; M-KILL live / M-ABORT / M-LEDGER still design-only here)

---

*End GATE6_CANARY_MEASUREMENT — historical n=1; see GATE6_MULTI_CANARY_MEASUREMENT for n=6 pack; RefuseTransport-safe final.*
