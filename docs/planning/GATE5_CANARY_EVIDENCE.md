# Gate 5 — Canary evidence (step 6 + ledger step 7)

**Status:** Step (6) **EXECUTED** (one Gemini free canary) · step (7) ledger captured · final binding **RefuseTransport**  
**Date:** 2026-09-28 ~19:47 EDT (America/New_York)  
**Author:** Grok Bot `<grok-bot@local>`  
**Tip at capture base:** `7e40009` (+ CP-0075 impl in same cycle)  
**Impl CP:** **CP-0075** — `IMPL_CP_0075_GEMINI_FREE_CANARY.md`  
**ENABLE ACK:** `GATE1_ENABLE_UNDER_FENCES_ACK_SIGNED.md` — **「Aprobado」**  
**Ledger JSON:** `docs/planning/GATE5_CANARY_LEDGER.json`

---

## Preconditions

| # | Item | Today |
|---|------|-------|
| 1 | Gate1 ENABLE_UNDER_FENCES | **SIGNED** |
| 2–4 | Gates 2–4 ENABLE_READY | **YES** |
| 5 | Health (step 5) | **PASS** (prior) |
| NT-10 | `may_enable` | **True** under CP-0075 + gates (`reasons=[]`) |
| I5 | Kill armed | **Yes** before call |
| Key | oob only | `/home/box/.config/neural-mesh/gemini.env` · handle `mesh://secrets/judge/gemini-free@v1` |

## Enablement (pre-flip)

```text
evaluate_canary_enablement() → may_enable=True, reasons=[]
LIVE_API_ENABLED module default = False
runtime before = False
```

## Step (6) canary

| Field | Value |
|-------|-------|
| Request id | `gate5-canary-1790639263` |
| Model | `gemini-flash-latest` (provider version reported `gemini-3.8-flash`) |
| Prompt | synthetic `Reply with exactly: MESH_CANARY_OK` |
| Transport | `GeminiFreeCanaryTransport` (reuses free `generateContent`) |
| HTTP | **200** |
| Latency | **6621 ms** |
| Marker | **MESH_CANARY_OK** present (`ok_marker=true`) |
| Verdict | **ADVISORY** (not Mesh ACCEPT / not SoT) |
| Digest | `124e5c75934da4e7` |
| response_sha256 | `d917ede4db735989390bac6258f06575fc2e90f6237a2bb357dd7fc3a521bb5e` |
| I5 killed? | **No** (no anomaly) |
| Runtime LIVE during | **True** |
| Runtime LIVE final | **False** |
| Module LIVE_API_ENABLED final | **False** |
| Binding final | **RefuseTransport** |

## Step (7) hygiene

- No raw key / `AIza` / Bearer in ledger JSON or this doc  
- Handle id only  
- `mesh_accept=false` · `advisory_only=true` · `m1_status=NO_CONSENSUS_YET`  
- `src_live_codec_shipped=false`  
- Dry-run peer `30fe593` remains **≠** this canary  

## Rollback / final flag state (honest)

Per runbook preference **leave RefuseTransport-safe**:

| Flag | Final |
|------|-------|
| Module `LIVE_API_ENABLED` (peer spike + CP-0075) | **False** |
| Process runtime live | **False** |
| Binding | **RefuseTransport** |
| Re-enable | Requires re-walk Gate5 (1)–(7) |

## Related

- `GATE5_LIVE_FLAG_FLIP_RUNBOOK.md` · `GATE5_HEALTH_CHECK_EVIDENCE.md`  
- `GATE6_CANARY_MEASUREMENT.md` · `IMPL_CP_0075_GEMINI_FREE_CANARY.md`  
- `council/NOTE_IMPL_CP_0075_GEMINI_FREE_CANARY.md`

---

*End GATE5_CANARY_EVIDENCE — one canary HTTP 200; LIVE_API module False; RefuseTransport final.*
