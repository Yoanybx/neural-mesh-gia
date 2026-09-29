# DESIGN CP-0077 — Gate6 metric completion (DESIGN_ONLY)

**Status:** **DESIGN_ONLY** — sealed design for remaining Gate6 acceptance (M-KILL live, M-ABORT, M-LEDGER) + sample policy **n≥N**  
**Does NOT** measure live · **does NOT** re-run canary · **does NOT** flip `LIVE_API_ENABLED` · **does NOT** authorize codec impl  
**Cycle / Checkpoint:** 73 / **CP-0077**  
**Date:** 2026-09-28 ~22:29 EDT (America/New_York)  
**Author:** Grok Bot `<grok-bot@local>`  
**Tip at mint base:** `e739c82` (CP-0076) + DeepSeek ACK CP-0076 design hygiene (NEXT #1 = this)  
**Package:** **0.18.0 HELD** · **NO_HELD unchanged** · D3 NOT ACKed · M1=NO_CONSENSUS_YET · pkg0190 NOT_OPENED

---

## 0. What this CP is / is not

| Is | Is not |
|----|--------|
| Design seal for DeepSeek Option / NEXT #1 `GATE6_METRIC_COMPLETION_DESIGN` | A live Gate6 measurement seal |
| Spec: M-KILL live · M-ABORT · M-LEDGER · **n≥N_min=5** · edges · variance reporting | Permission to multi-canary execute now |
| Honest blocker list for product-ready live | “100% live ready” / permanent enable |
| Cite of DeepSeek CP-0076 hygiene ACK | Codec impl authorization (still CP-0076 DESIGN_ONLY residual) |

**Hard fences:** `LIVE_API_ENABLED=False` · RefuseTransport ON · `src_live_codec_shipped=false` · **n=1 ≠ seal** · no push/tags/secrets · **NO_HELD unchanged**.

---

## 1. Artifacts

| Artifact | Path |
|----------|------|
| Metric completion design | `docs/planning/GATE6_METRIC_COMPLETION_DESIGN.md` |
| Council note | `council/NOTE_DESIGN_CP_0077_GATE6_METRIC_COMPLETION.md` |
| DeepSeek CP-0076 hygiene ACK | `council/REPLY_DEEPSEEK_CP0076_DESIGN_HYGIENE_ACK.md` |
| Prior residual (not impl) | `docs/planning/DESIGN_CP_0076_LIVE_HTTP_TRANSPORT_RESIDUAL.md` |

---

## 2. Coverage checklist (NEXT #1 exit)

| Topic | Covered |
|-------|---------|
| M-KILL live acceptance | Yes — M-KILL-1-LIVE / 2-BUDGET / 3-RESUME |
| M-ABORT acceptance | Yes — ABORT>ACCEPT · anomaly→Refuse · conflict fail-closed |
| M-LEDGER acceptance | Yes — kinds across n≥N · oversight+abort on kill · claim hygiene |
| Sample policy n≥N | Yes — **N_min=5**; N_edge≥3; N_kill_live≥1; N_abort≥1; N_ledger_kill≥1 |
| Variance / edge | Yes — p50/p95 descriptive; E-KILL…E-RESUME set |
| n=1 cannot seal | Explicit binding |
| 「listo」 blockers named | Codec impl auth · multi-canary · permanent enable policy |

---

## 3. Explicit non-authorization

This CP **must not** be cited as authority for:

1. Declaring Gate6 live-measurement **sealed**  
2. Re-running or expanding canaries without operator/runbook gates  
3. Implementing `LiveHttpTransport` or flipping `LIVE_API_ENABLED` permanently  
4. Treating CP-0075 n=1 (~6621 ms) as SLO or seal  
5. Unlocking NO_HELD / starting D3 / committing keys  

A **future measurement pack** (docs+evidence after multi-canary) would be required before Gate6 live-measurement seal; a **separate impl CP** before codec ship; a **permanent-enable policy/runbook** before module LIVE stays true.

---

## 4. Related

- `GATE6_METRIC_COMPLETION_DESIGN.md` · `GATE6_LIVE_ACCEPTANCE_METRICS.md` · `GATE6_CANARY_MEASUREMENT.md`  
- `IMPL_CP_0075_GEMINI_FREE_CANARY.md` · `LIVE_HTTP_TRANSPORT_RESIDUAL_DESIGN.md`  
- `GEMINI_FREE_NEXT_STEPS.md` · `LIVE_READINESS_CHECKLIST.md` · `LIVE_100_OPERATOR_WALL.md`  
- `council/REPLY_DEEPSEEK_CP0076_DESIGN_HYGIENE_ACK.md` · `council/NOTE_DEEPSEEK_ACK_GATE5_CANARY.md`

---

*End DESIGN_CP_0077 — DESIGN_ONLY; n=1 cannot seal; no live enable; no codec impl.*
