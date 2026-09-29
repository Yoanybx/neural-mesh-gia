# Gate 5 — Multi-canary pack evidence (CP-0079)

**Status:** Pack **EXECUTED** · n=6 ≥ N_min=5 · edges PASS · final binding **RefuseTransport** · module **LIVE_API_ENABLED=False**  
**Date:** 2026-09-28 ~22:39 EDT (America/New_York)  
**Author:** Grok Bot `<grok-bot@local>`  
**Tip at capture base:** `ee0c0c6` (+ CP-0079 in same cycle)  
**Impl CP:** **CP-0079** — `IMPL_CP_0079_MULTI_CANARY_PACK.md`  
**Design:** CP-0077 `GATE6_METRIC_COMPLETION_DESIGN.md`  
**ENABLE ACK:** `GATE1_ENABLE_UNDER_FENCES_ACK_SIGNED.md`  
**Ledger JSON:** `docs/planning/GATE5_MULTI_CANARY_LEDGER.json`  
**Permanent policy:** `LIVE_API_PERMANENT_ENABLE_POLICY.md` (default still False after pack; F4 OPEN)

---

## Preconditions

| # | Item | Today |
|---|------|-------|
| 1 | Gate1 ENABLE_UNDER_FENCES | **SIGNED** |
| 2–4 | Gates 2–4 ENABLE_READY | **YES** |
| 5 | Health | **PASS** (prior) |
| CP-0075/0078 | canary + LiveHttpTransport v0 | **YES** |
| may_enable | canary + LHT | **True** (`reasons=[]`) |
| I5 | Armed per attempt | **Yes** |
| Key | oob only | `/home/box/.config/neural-mesh/gemini.env` |

## Pack summary

| Field | Value |
|-------|-------|
| n | **6** (≥ N_min=5) |
| n_edge | **5** (≥3) |
| n_kill_live | **1** |
| n_abort | **3** |
| n_ledger_kill | **1** |
| n_real_http | **1** |
| n_mock | **5** |
| seal_candidate | **true** (sample policy met — **≠** Gate6 final seal / ≠ product 「listo」) |
| Module LIVE final | **False** |
| Runtime LIVE final | **False** |
| Binding final | **RefuseTransport** |
| Quota issues | **none** |

## Attempts

| # | Edge | Mode | HTTP / outcome | latency_ms | ok |
|---|------|------|----------------|------------|-----|
| 1 | E-HAPPY | real_http | **200** / ADVISORY `MESH_MULTI_CANARY_OK` | **6303** | yes |
| 2 | E-KILL | mock_local | mid-window kill → ENGINE_DISABLED | 0 | yes |
| 3 | E-ABORT-ACCEPT | mock_local | Mesh POLICY_ABORT > peer ACCEPT | 0 | yes |
| 4 | E-AUTH | mock_local | ENGINE_AUTH (invalid handle) | 0 | yes |
| 5 | E-ANOMALY | mock_local | may_enable=False → RefuseTransport | 0 | yes |
| 6 | E-RESUME | mock_local | auto-resume refused (M-KILL-3) | 0 | yes |

## Latency aggregate (descriptive)

| Stat | ms |
|------|-----|
| min | 0 |
| median / p50 | 0 |
| max / p95_approx | 6303 |
| Note | ops kill→refuse budget still **OPEN** (M-KILL-2) |

## Hygiene

- No raw key / `AIza` / Bearer in ledger or this doc  
- Handle id only · `mesh_accept=false` · `advisory_only=true` · M1=NO_CONSENSUS_YET  
- Prior CP-0075 n=1 remains historical sample; this pack is independent n=6  

## Related

- `GATE5_MULTI_CANARY_LEDGER.json` · `GATE6_MULTI_CANARY_MEASUREMENT.md`  
- `LIVE_API_PERMANENT_ENABLE_POLICY.md` · `GATE5_LIVE_FLAG_FLIP_RUNBOOK.md` §8  

---

*End GATE5_MULTI_CANARY_EVIDENCE — n=6; HTTP 200 happy; edges PASS; LIVE False; RefuseTransport final.*
