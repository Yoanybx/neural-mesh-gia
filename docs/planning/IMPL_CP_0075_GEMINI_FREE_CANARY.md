# IMPL CP-0075 — Gemini free-tier Gate5 canary (authorized under fences)

**Status:** **AUTHORIZED IMPL CP** (minimum canary binding) — clears NT-10 / `impl_cp_not_authorized` for Gemini **free-tier** Gate5 canary under fences  
**Cycle / Checkpoint:** 71 / **CP-0075**  
**Date:** 2026-09-28 ~19:46 EDT (America/New_York)  
**Author:** Grok Bot `<grok-bot@local>`  
**Tip at mint base:** `7e40009` (ENABLE_UNDER_FENCES signed; Gates 2–4 ENABLE_READY)  
**Package:** **0.18.0 HELD** · **NO_HELD unchanged** · **D3 NOT ACKed** · pkg0190 **NOT_OPENED** · M1=**NO_CONSENSUS_YET**

---

## 0. What this is / is not

| Is | Is not |
|----|--------|
| Honest **authorized impl CP** that lifts Cycle-54 **hard** `may_enable=False` when *all* enablement gates pass | A fake unlock / prose-only `may_enable` |
| **Minimum** Gate5 canary path: reuse Google free HTTP (`GeminiFreeDryRunTransport`) behind runtime `LIVE_API` + kill-armed I5 | Full `LiveHttpTransport` / `src/neural_mesh/judge_*.py` live codec |
| Scoped to Gemini **free-tier** canary (model `gemini-flash-latest`) under Gate1 ENABLE_UNDER_FENCES | Vertex paid · multi-canary · Mesh SoT authority |
| Leaves **module** `LIVE_API_ENABLED=False` after canary (RefuseTransport-safe) | Permanent live=ENABLED product default |

**Gap honesty:** Full L_judge live adapter (CP-0057 §8 LiveHttpTransport + parse/receipt codec) is **not** shipped. This CP documents that as **design+spike residual** and implements only what Gate5 runbook step (6) needs for **one** canary.

---

## 1. NT-10 / `impl_cp_not_authorized` — what was required

| Piece | Before CP-0075 | After CP-0075 |
|-------|----------------|---------------|
| `evaluate_enablement_gates(...)` | Always returned `may_enable=False` even when all inputs optimistic (Cycle 54 design posture) | Returns `may_enable=True` **iff** `reasons == []` |
| Reason `impl_cp_not_authorized` | Fired when `impl_cp_authorized=False` (default) | Still fires by default; cleared when caller passes `impl_cp_authorized=True` **and** this CP is the authorizing artifact |
| Permanent / must-stay-false | Already blocked | Unchanged (e.g. `train_70b`, asserting `live_adapter.enabled` while evaluating still refuses) |
| Default call | Fail-closed | **Still** fail-closed (`impl_cp_not_authorized`, missing handle, etc.) |

**Binding helpers:**

- `src/neural_mesh/packaging/l_judge_live_adapter_safety.py` — enablement lift  
- `src/neural_mesh/packaging/l_judge_gemini_free_canary_impl.py` — authorization record + canary runner  
- Tests: `tests/test_l_judge_live_adapter_safety_cycle54.py` · `tests/test_l_judge_gemini_free_canary_impl_cycle71.py`

---

## 2. Minimum wiring (Gate5 expectation)

```
evaluate_canary_enablement() → may_enable?
        │ no → ABORT / RefuseTransport
        ▼ yes
arm I5 (Oversight_I5 kill → RefuseTransport + enabled=false)
        │
        ▼
live_api_canary_session()  # runtime LIVE_API=True for window only
        │
        ▼
GeminiFreeCanaryTransport.call()  # reuses Gemini free generateContent
        │
        ▼
ledger (Gate5 step 7) + restore runtime LIVE_API=False
```

| Flag | During canary | Final (default) |
|------|---------------|-----------------|
| Module `LIVE_API_ENABLED` (peer spike + this CP) | **False** (constant) | **False** |
| Process runtime `MESH_LIVE_API_ENABLED` / session | **True** (window) | **False** |
| Binding | `GeminiFreeCanaryTransport` | `RefuseTransport` |
| `src_live_codec_shipped` | **False** | **False** |

**Secret:** handle id `mesh://secrets/judge/gemini-free@v1` → oob file `/home/box/.config/neural-mesh/gemini.env` (never in git).

---

## 3. Residual (full adapter — out of this CP)

| Item | Status |
|------|--------|
| `LiveHttpTransport` generic codec in `src/neural_mesh/` | **NOT shipped** (design+spike) |
| Judge parse/receipt live path beyond packaging canary | **NOT shipped** |
| `live_adapter.enabled` product default | **stays false** |
| CI live calls | **forbidden** (`live_api_in_ci` must stay false) |
| Vertex / paid | **OUT** |

---

## 4. Explicit non-goals

- Push / tags / secrets in git  
- NO_HELD unlocks (GIA, Raft, N>2, train-70B, SaaS)  
- D3 / `MESH_PERF_EXPERIMENTAL`  
- Treating prior dry-run `30fe593` as this canary  
- Partial peer enable / multi-canary fan-out  
- Claiming Mesh SoT / M1 consensus from canary advisory

---

## 5. Related

- `GATE5_LIVE_FLAG_FLIP_RUNBOOK.md` · `GATE5_HEALTH_CHECK_EVIDENCE.md` · `GATE5_CANARY_EVIDENCE.md`  
- `GATE1_ENABLE_UNDER_FENCES_ACK_SIGNED.md` · Gates 2–4 `*_ENABLE_READY.md`  
- `GEMINI_FREE_NEXT_STEPS.md` · `LIVE_READINESS_CHECKLIST.md` · `LIVE_100_OPERATOR_WALL.md`  
- `docs/design/L_JUDGE_LIVE_ADAPTER_DESIGN.md` §8 · `L_JUDGE_LIVE_ADAPTER_SAFETY_CASE.md` §6/§8  
- `google_l_judge_peer_spike.py` (`GeminiFreeDryRunTransport`)

---

*End IMPL_CP_0075 — authorized minimum canary binding; full live codec still design+spike; module LIVE_API_ENABLED=False final.*
