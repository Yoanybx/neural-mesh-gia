# IMPL CP-0087 — Phase R5 F4 product-enable ACK SIGNED + permanent LIVE flip

**Status:** **AUTHORIZED docs + product flip** under fences — **R5 DONE**  
**Cycle / Checkpoint:** 83 / **CP-0087**  
**Date:** 2026-09-28 ~23:26 EDT (America/New_York)  
**Author:** Grok Bot `<grok-bot@local>`  
**Tip at mint base:** `c64c0e0` (CP-0086 Gate6 live-measurement SEALED)  
**Package:** **0.18.0 HELD** · **LIVE_API_ENABLED=True** (product path) · **NO_HELD unchanged** · D3 NOT ACKed · M1=**NO_CONSENSUS_YET**  
**Parent design:** CP-0081 `MESH_FULL_ADAPTER_LIVE_RV_DESIGN.md` §4 Phase **R5** · F4 amendment · permanent policy P7

---

## 0. What this is / is not

| Is | Is not |
|----|--------|
| Record operator F4 product ACK **SIGNED** (「Firmalo por mi」) + flip product module LIVE True | Vertex paid / streaming / CI live / NO_HELD |
| P7 met; R5 DONE; `live_adapter.enabled` authorized in ACK’d local env | Waive I5 kill-arm / RefuseTransport when not armed |
| Docs + product-path packaging constants | Push/tags/secrets in git |
| Follow-up 「Ponlo live y seguimos」 flip under fences | Invent beyond operator chat marks |

---

## 1. Operator marks (recorded, not invented)

| Mark | Time (ET) | Meaning |
|------|-----------|---------|
| **「Firmalo por mi」** | ~23:22 | Sign F4 product-enable ACK |
| **「Ponlo live y seguimos」** | ~23:24+ | After SIGNED: flip product permanent LIVE under fences |

**Tip at sign:** `c64c0e0`

---

## 2. Artifacts

| Artifact | Path |
|----------|------|
| F4 ACK **SIGNED** | `docs/planning/F4_PRODUCT_ENABLE_ACK_SIGNED.md` |
| F4 ACK draft (historical) | `docs/planning/F4_PRODUCT_ENABLE_ACK_DRAFT.md` |
| CP seal (this) | `docs/planning/IMPL_CP_0087_F4_PRODUCT_ENABLE_R5.md` |
| Council note | `council/NOTE_CP_0087_F4_PRODUCT_ENABLE_R5.md` |
| Policy P7 | `LIVE_API_PERMANENT_ENABLE_POLICY.md` → **SIGNED** |
| Wall / checklist / RV | `LIVE_100_OPERATOR_WALL.md` · `LIVE_READINESS_CHECKLIST.md` · `MESH_FULL_ADAPTER_LIVE_RV_DESIGN.md` |

**Product modules flipped `LIVE_API_ENABLED=True`:** peer spike · gemini free canary · LiveHttpTransport · multi-canary · full-adapter R1–R4 · Gate6 live-measurement incr.  
**Left False (non-product / held):** orchestrator_* · agent_shell* · mesh_perf_* · m_kill_2 · m2_e2e · etc.

---

## 3. Outcomes

| Item | Result |
|------|--------|
| F4 product ACK | **SIGNED** |
| P7 | **SIGNED / met** |
| R5 | **DONE** |
| Module LIVE (product path) | **True** |
| `live_adapter.enabled` | **Authorized true** (ACK’d local); enablement no longer refuses it |
| I5 / RefuseTransport | Still gate network when not armed |
| Streaming | **OUT** (CP-0085 DEFER) |
| Vertex / NO_HELD | **OUT** / unchanged |
| Verdict | **R5_F4_PRODUCT_ENABLE_DONE** |

---

## 4. Explicit non-authorization

This CP **must not** be cited as authority for:

1. Vertex paid / streaming codec ship  
2. CI live (`live_api_in_ci`)  
3. NO_HELD unlocks (GIA / Raft / N>2 / train / SaaS)  
4. Push / tags / secrets in git  
5. Waiving I5 for live network windows  
6. Claiming advisory = Mesh SoT / M1  

---

## 5. Honest 「listo」 after this CP

| Track | Status |
|-------|--------|
| Listo bajo fences | **YES** |
| Full Mesh adapter live RV | **R0–R5 DONE** (streaming DEFERRED residual closed as DEFER) |
| Product permanent LIVE | **YES** — ACK SIGNED + module True (Gemini free, ACK’d local) |
| Streaming | **DEFERRED** / OUT_OF_F4 |
| Next | Product soak / optional council STATUS to DeepSeek; keep I5 honest |

---

*End IMPL_CP_0087 — R5 DONE; F4 SIGNED; LIVE True (product path); streaming OUT; NO_HELD unchanged.*
