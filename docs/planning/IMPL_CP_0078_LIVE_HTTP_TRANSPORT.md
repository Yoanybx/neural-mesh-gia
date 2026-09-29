# IMPL CP-0078 — LiveHttpTransport v0 (authorized under fences)

**Status:** **AUTHORIZED IMPL CP** — minimum honest `LiveHttpTransport` codec+transport for Gemini **free-tier** under ENABLE_UNDER_FENCES  
**Cycle / Checkpoint:** 74 / **CP-0078**  
**Date:** 2026-09-28 ~22:35 EDT (America/New_York)  
**Author:** Grok Bot `<grok-bot@local>`  
**Tip at mint base:** `46858e1` (CP-0077 Gate6 metric completion DESIGN_ONLY)  
**Design authority:** **CP-0076** `LIVE_HTTP_TRANSPORT_RESIDUAL_DESIGN.md` (DESIGN_ONLY → this CP implements)  
**Package:** **0.18.0 HELD** · **NO_HELD unchanged** · **D3 NOT ACKed** · pkg0190 **NOT_OPENED** · M1=**NO_CONSENSUS_YET**

---

## 0. What this is / is not

| Is | Is not |
|----|--------|
| Authorized **impl** of CP-0076 residual: unary codec + retries/backoff/idempotency/timeouts/taxonomy/ABORT hooks at **v0 minimum** | Permanent product `LIVE_API_ENABLED=True` / `live_adapter.enabled=true` |
| Packaging module `LiveHttpTransport` behind **runtime LIVE + I5**; RefuseTransport when live off | Streaming codec (v0 unary only) |
| Clears design fence “codec not authorized”; sets `src_live_codec_shipped=true` (packaging) | Gate6 live-measurement seal (still needs multi-canary n≥N_min=5) |
| Composes CP-0075 canary (does not break / supersede canary minimum) | Vertex paid · CI live network · keys in git |

**Hard fences held:** module **`LIVE_API_ENABLED=False`** · RefuseTransport default when live off · **NO_HELD unchanged** · no push/tags/secrets.

---

## 1. Artifacts

| Artifact | Path |
|----------|------|
| Impl module | `src/neural_mesh/packaging/l_judge_live_http_transport.py` |
| Tests (T-lht-* unit/negatives) | `tests/test_l_judge_live_http_transport_cycle74.py` |
| Evidence note | `docs/planning/EVIDENCE_CP_0078_LIVE_HTTP_TRANSPORT.md` |
| Council note | `council/NOTE_IMPL_CP_0078_LIVE_HTTP_TRANSPORT.md` |
| Schema (updated) | `docs/schema/judge/live_http_transport_v0.md` |
| Design (upstream) | `docs/planning/LIVE_HTTP_TRANSPORT_RESIDUAL_DESIGN.md` · `DESIGN_CP_0076_…` |

---

## 2. Surface shipped (v0 minimum)

```
LiveHttpTransport
  call(request, *, idempotency_key, mode=unary) -> TransportResult
  health() -> TransportHealth
  cancel(idempotency_key | call_id)  # ABORT propagation
```

| Concern | v0 binding |
|---------|------------|
| Default when live off | `RefuseTransport` → `ENGINE_DISABLED` (T-lht-a) |
| Runtime window | Reuses CP-0075 `live_api_canary_session` / `runtime_live_api_enabled` + I5 |
| Retries | `max_retries=1` floor; 5xx/transient retryable; 401/403 non-retry |
| Backoff | Exponential full jitter, bound by remaining `timeout_s` |
| Idempotency | Mesh-owned store; same digest replay; conflict → `CONT_IDEMPOTENCY_CONFLICT` |
| Timeouts | Hard = `timeout_s` (floor 30); map → `ENGINE_TIMEOUT` |
| Streaming | **Not** shipped; `mode=streaming` → ABORT (no half-ACCEPT) |
| Audit | `audit_required`; missing → `NO_AUDIT` |
| TLS | HTTPS only; plaintext → `PLAINTEXT_FORBIDDEN` |
| Verdict | Success → **ADVISORY** only; `mesh_accept=false`; never invent ACCEPT |

---

## 3. Flag posture

| Flag | During optional fenced call | Final / product default |
|------|-----------------------------|-------------------------|
| Module `LIVE_API_ENABLED` | **False** (constant) | **False** |
| Process runtime LIVE | True only inside session | **False** |
| `live_adapter.enabled` | false | **false** |
| `live_api_in_ci` | false | **false** |
| `src_live_codec_shipped` | **True** (this CP) | **True** |
| Binding default | RefuseTransport when off | RefuseTransport |

---

## 4. Residual (honest — still open toward 「listo」)

| Item | Status |
|------|--------|
| Multi-canary measurement pack **n≥N_min=5** + edges (CP-0077) | **OPEN** — not authorized/executed here |
| Permanent LIVE_API enable policy / runbook | **OPEN** — do **not** permanently flip |
| F4 permanent-enable operator ACK (beyond ENABLE_UNDER_FENCES canary) | **OPEN** if treated as product enable |
| Streaming mode | **NOT** shipped |
| Gate6 live-measurement seal | **OPEN** (n=1 ≠ seal) |
| CI live calls | **forbidden** |

---

## 5. Explicit non-goals

- Push / tags / secrets in git  
- NO_HELD unlocks (GIA, Raft, N>2, train-70B, SaaS)  
- D3 / `MESH_PERF_EXPERIMENTAL`  
- Treating advisory digests as Mesh SoT / M1  
- Claiming Gate6 sealed or product-ready live from this codec alone  
- Breaking CP-0075 canary path  

---

## 6. Related

- `IMPL_CP_0075_GEMINI_FREE_CANARY.md` · `LIVE_HTTP_TRANSPORT_RESIDUAL_DESIGN.md` · `GATE6_METRIC_COMPLETION_DESIGN.md`  
- `GEMINI_FREE_NEXT_STEPS.md` · `LIVE_READINESS_CHECKLIST.md` · `LIVE_100_OPERATOR_WALL.md`  
- `L_JUDGE_LIVE_ADAPTER_SAFETY_CASE.md` · `ORCHESTRATOR_CONTINUITY_DESIGN.md` · `ORCHESTRATOR_OVERSIGHT_HOOKS_DESIGN.md`

---

*End IMPL_CP_0078 — authorized LiveHttpTransport v0 under fences; module LIVE_API_ENABLED=False; multi-canary + permanent enable still residual.*
