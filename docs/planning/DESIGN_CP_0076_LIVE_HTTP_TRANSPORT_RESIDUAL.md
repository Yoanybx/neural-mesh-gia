# DESIGN CP-0076 — LiveHttpTransport residual (DESIGN_ONLY)

**Status:** **DESIGN_ONLY** — sealed design artifact for full `LiveHttpTransport` residual  
**Does NOT authorize codec implementation** · **does NOT enable live** · **does NOT** flip `LIVE_API_ENABLED`  
**Cycle / Checkpoint:** 72 / **CP-0076**  
**Date:** 2026-09-28 ~19:54 EDT (America/New_York)  
**Author:** Grok Bot `<grok-bot@local>`  
**Tip at mint base:** `ca85688` (CP-0075) + dual council Gate5 canary hygiene ACK (DeepSeek Option 1 + ChatGPT RANK 1)  
**Package:** **0.18.0 HELD** · **NO_HELD unchanged** · D3 NOT ACKed · M1=NO_CONSENSUS_YET · pkg0190 NOT_OPENED

---

## 0. What this CP is / is not

| Is | Is not |
|----|--------|
| Design seal for the residual named “NOT shipped” by CP-0075 | An impl CP / codec ship authorization |
| Dual-council Option 1 execution (DeepSeek recommended + ChatGPT RANK 1) | A live enable or canary re-run |
| Design doc + schema stub + negative-test descriptors | Green network pytest / keys / push/tags |
| Compose citation of CP-0058 + CP-0068 + CP-0069 | A claim that canary = full adapter |

**Hard fences:** `LIVE_API_ENABLED=False` · RefuseTransport ON · `src_live_codec_shipped=false` · CP-0075 canary path remains **separate minimum**.

---

## 1. Artifacts

| Artifact | Path |
|----------|------|
| Residual design | `docs/planning/LIVE_HTTP_TRANSPORT_RESIDUAL_DESIGN.md` |
| Schema stub | `docs/schema/judge/live_http_transport_v0.md` |
| Council note | `council/NOTE_DESIGN_CP_0076_LIVE_HTTP_TRANSPORT.md` |
| Dual ACK | `council/NOTE_DEEPSEEK_ACK_GATE5_CANARY.md` · replies REPLY_*_GATE5_CANARY_HYGIENE_ACK.md |

---

## 2. Coverage checklist (Option 1 exit)

| Topic | Covered |
|-------|---------|
| Retries | Yes — floor `max_retries=1`; taxonomy-gated |
| Backoff | Yes — exponential full jitter bound by timeout |
| Idempotency | Yes — Continuity key; conflict / no double-invoke |
| Streaming vs unary | Yes — unary required; streaming optional + rules |
| Error taxonomy | Yes — extends CP-0057/0058 + continuity codes |
| Timeout bounds | Yes — soft/hard / connect subset |
| ABORT propagation | Yes — kill/orphan/timeout → RefuseTransport |
| Audit linkage | Yes — receipt + EvidenceEntry + OBS (no secrets) |

---

## 3. Explicit non-authorization

This CP **must not** be cited as authority for:

1. Implementing `LiveHttpTransport` in `src/neural_mesh/`  
2. Setting `live_adapter.enabled=true` or module `LIVE_API_ENABLED=True`  
3. New network canaries beyond CP-0075’s already-executed minimum  
4. Treating advisory / n=1 canary sample as SoT or SLO  
5. Unlocking NO_HELD (GIA, Raft, N>2, ML, train-70B, SaaS, …)

A **future impl CP** (new id) would be required before codec ship, still default-off, still NO_HELD-safe.

---

## 4. Related

- `IMPL_CP_0075_GEMINI_FREE_CANARY.md` · Gate5/6 canary evidence  
- `L_JUDGE_LIVE_ADAPTER_DESIGN.md` · `L_JUDGE_LIVE_ADAPTER_SAFETY_CASE.md`  
- `ORCHESTRATOR_CONTINUITY_DESIGN.md` · `ORCHESTRATOR_OVERSIGHT_HOOKS_DESIGN.md`  
- `GEMINI_FREE_NEXT_STEPS.md` · `LIVE_READINESS_CHECKLIST.md` · `LIVE_100_OPERATOR_WALL.md`

---

*End DESIGN_CP_0076 — DESIGN_ONLY; NOT authorizing impl; LIVE_API stays False.*
