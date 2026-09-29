# Gemini free-tier — next steps (ENABLE_UNDER_FENCES)

**Status:** Ordered plan under Gate1 **SIGNED ENABLE_UNDER_FENCES** (「Aprobado」 2026-09-28 ~19:41 ET)  
**Does not** mint keys into repo · **does not** start D3 · **does not** push/tag · **does not** unlock NO_HELD  
**Scope:** Gemini **free-tier canary only**; Vertex paid **OUT**  
**Posture:** **`LIVE_API_ENABLED=False`** (module final); RefuseTransport default ON; Gates 2–4 ENABLE_READY; **CP-0075..0084** (… full-adapter R0–R3); F4 product ACK **UNSIGNED**; tip base **`56cdaa0`→CP-0084**  
**Cite:** `GATE1_ENABLE_UNDER_FENCES_ACK_SIGNED.md` · dual canary hygiene ACK · `REPLY_DEEPSEEK_CP0076_DESIGN_HYGIENE_ACK.md`  
**Dry-run evidence:** `council/NOTE_GEMINI_DRY_RUN.md` · `docs/planning/GEMINI_DRY_RUN_EVIDENCE.md` (2026-09-28 18:09 ET) · peer wire `council/NOTE_GEMINI_PEER_DRY_RUN_WIRE.md`

---

## Ordered next (still no Mesh live enable)

| Step | Action | Status | Forbidden now |
|------|--------|--------|---------------|
| **1** | **secret_handle outside repo** — provision handle in out-of-band store; record handle path / digest only | **DONE (eval)** — handle at `/home/box/.config/neural-mesh/gemini.env`; `.gitignore` covers `gemini.env` / `.config/neural-mesh/`; key never in git | Raw key in repo, CI, evidence digests, chat |
| **2** | **Dry-run** — one-shot free `generateContent` with synthetic prompt; evidence without secrets | **DONE (eval)** — HTTP 200; model `gemini-flash-latest` (2.0/1.5 flash retired → 404 model); marker `MESH_DRY_RUN_OK`; see evidence notes | Mesh live adapter enable; flip `LIVE_API_ENABLED`; Gate5 canary without serial gates |
| **2b** | **Peer spike dry-run wire** — mock Google L_judge peer gains explicit `--gemini-dry-run` / `GEMINI_DRY_RUN=1` path for ONE real free call; default remains mock/no-network | **DONE (eval)** — `GeminiFreeDryRunTransport` + CLI in `google_l_judge_peer_spike.py`; see `council/NOTE_GEMINI_PEER_DRY_RUN_WIRE.md` | Flip `LIVE_API_ENABLED`; enable Mesh live adapter; treat dry-run as Gate5 canary |
| **2c** | **Gate2 design seal** — bind amendment to dry-run/peer wire, Authority Matrix, RefuseTransport, secret_handle | **DONE (DESIGN_SEALED)** — `GATE2_DESIGN_SEALED.md`; ENABLE seal still OPEN | Invent operator ENABLE signature; flip live flags |
| **3** | **Gate3 design seal** — Authority Matrix config/ops binding (dry-run peer, secret_handle, RefuseTransport) | **DONE (DESIGN_SEALED)** — `GATE3_DESIGN_SEALED.md` · `GATE3_AUTHORITY_MATRIX_BINDING.md`; ENABLE / live-armed OPEN | Treat Gate3 design seal as enable seal; flip live flags |
| **3b** | **Gate4 design seal** — data policy + secret_handle schedule toward DESIGN_SEALED (eval handle already done) | **DONE (DESIGN_SEALED)** — `GATE4_DESIGN_SEALED.md` · `GATE4_LIVE_DATA_POLICY.md`; oob key load; dry-run≠RefuseTransport; ENABLE / Mesh live data seal OPEN | Treat Gate4 design seal as Mesh live enable; commit raw keys; execute Gate5 canary |
| **4** | **Gate5 runbook design seal** — docs/canary procedure toward DESIGN_SEALED (**not** execute canary) | **DONE (DESIGN_SEALED)** — `GATE5_DESIGN_SEALED.md` · `GATE5_LIVE_FLAG_FLIP_RUNBOOK.md`; procedure sealed; canary NOT AUTHORIZED | Flip `live_adapter.enabled` / `LIVE_API_ENABLED`; run canary without ENABLE chain; invent ENABLE_UNDER_FENCES |
| **4b** | **Gate5 canary** — health check → single canary under kill-armed I5 → ledger evidence (Gate5 steps 1–7) | **DONE** — CP-0075; `GATE5_CANARY_EVIDENCE.md` / ledger / Gate6 sample; dual council hygiene ACK; dry-run `30fe593` ≠ canary (historical) | Re-canary / flip without re-walk; treat as SLO |
| **5** | **Gate6 metrics design seal** — acceptance metrics toward DESIGN_SEALED (docs) | **DONE (DESIGN_SEALED)** — `GATE6_DESIGN_SEALED.md` · `GATE6_LIVE_ACCEPTANCE_METRICS.md`; live measurement OPEN; dry-run ≠ live RV | Claim canary evidence without Gate5 execution; flip live flags; invent ENABLE signature |
| **6** | **ENABLE_UNDER_FENCES** — operator signature | **SIGNED** — `GATE1_ENABLE_UNDER_FENCES_ACK_SIGNED.md` (「Aprobado」 ~19:41 ET) | Invent extra unlocks; commit keys |
| **6b** | **Gates 2–4 ENABLE_READY** — docs enable-ready seals under ENABLE | **DONE** — `GATE2/3/4_ENABLE_READY.md` | Claim live RV complete; flip without Gate5 |
| **6c** | **Gate5 step (5) health** | **PASS** — `GATE5_HEALTH_CHECK_EVIDENCE.md` | Treat as canary / flag flip |
| **7** | **Authorized impl CP (NT-10)** | **DONE** — **CP-0075** `IMPL_CP_0075_GEMINI_FREE_CANARY.md` (minimum canary binding; full LiveHttpTransport still design+spike) | Fake unlock; full codec claim |
| **7b** | **Gate5 step (6) canary / runtime LIVE flip** | **DONE** — one canary HTTP 200 / `MESH_CANARY_OK`; module `LIVE_API_ENABLED=False` final; RefuseTransport restored — `GATE5_CANARY_EVIDENCE.md` | Treat dry-run as canary; leave half-enabled |
| **8** | **Gate6 live measurement** on canary evidence | **DONE (sample n=1)** — `GATE6_CANARY_MEASUREMENT.md`; dual ACK: advisory≠SoT · n=1≠SLO | Claim production SLO / 100% product enable |
| **9** | **Full LiveHttpTransport residual design** (dual Option 1) | **DONE (DESIGN_ONLY)** — **CP-0076** `LIVE_HTTP_TRANSPORT_RESIDUAL_DESIGN.md` · schema `live_http_transport_v0.md` · neg descriptors T-lht-*; **does NOT authorize impl**; LIVE_API stays False | Codec impl; LIVE flip; claim CP-0075 = full adapter |
| **10** | **Gate6 metric completion design** (DeepSeek Option 2 / CP-0076 NEXT #1) | **DONE (DESIGN_ONLY)** — **CP-0077** `GATE6_METRIC_COMPLETION_DESIGN.md`; **n≥N_min=5**; M-KILL live / M-ABORT / M-LEDGER designed; **n=1 cannot seal** | Premature Gate6 live seal; multi-canary execute; permanent LIVE flip |
| **11** | **Multi-canary measurement pack** (n≥N + edges) | **DONE** — **CP-0079** **pack n=6 (1 real, 5 mock)**; `GATE5_MULTI_CANARY_EVIDENCE.md`; seal_candidate on n=6 total (not 5 live); module LIVE false | Claim F4/product listo; claim “5 live”; skip edges |
| **12** | **Codec impl CP** (after CP-0076 design) | **DONE** — **CP-0078** `IMPL_CP_0078_LIVE_HTTP_TRANSPORT.md` (v0 unary; runtime LIVE+I5; module LIVE false) | Claim permanent enable; streaming |
| **13** | **Permanent LIVE_API enable policy / runbook** | **DONE (policy)** — `LIVE_API_PERMANENT_ENABLE_POLICY.md` + Gate5 §8; **default still False**; F4 product-enable OPEN | Flip module True without F4 |
| **14** | **F4 product-enable** (permanent vs session) | **DESIGN_SEALED** + ACK **UNSIGNED** — `F4_DESIGN_SEALED.md` · `F4_PRODUCT_ENABLE_ACK_DRAFT.md`; ENABLE ≠ product | Invent F4 signature; flip module True |
| **15** | **M-KILL-2 ops kill→refuse budget** | **DONE** — ceiling **100 ms** process-local; drill PASS (`docs/ops/M_KILL_2_…`) | Invent network SLO as product |
| **16** | **M-ABORT-3 conflict/missing judges** | **DONE** — E-CONFLICT fail-closed PASS (CP-0080) | Auto-majority execute |
| **17** | **Full Mesh adapter live RV design** (DeepSeek NEXT-3) | **DONE (DESIGN_ONLY)** — **CP-0081** `MESH_FULL_ADAPTER_LIVE_RV_DESIGN.md`; multi-judge/SoT/Refuse/I5/Gate6/F4/streaming residuals named; **does NOT** flip LIVE / invent F4 / raise n_real_http | Codec beyond v0; permanent LIVE; claim full RV sealed |
| **18** | **Full-adapter R1 SoT+Refuse+I5 compose** | **DONE** — **CP-0082** checklist + descriptors T-fa-r1-a..e + unit compose on LiveHttpTransport+canary; **does NOT** authorize R2–R5 / flip LIVE / invent F4 | R2 multi-judge; R3 more HTTP; permanent LIVE |

---

## Serial gates reminder

Before any flag flip:

1. Gate2 — **ENABLE_READY** (docs) under SIGNED ENABLE; Mesh live RV still OPEN  
2. Gate3 — **ENABLE_READY** (docs); runtime not live-enabled  
3. Gate4 — **ENABLE_READY** (docs); oob key only  
4. Gate5 runbook DESIGN_SEALED; step (5) **PASS**; step (6) **EXECUTED** (CP-0075)  
5. Gate6 metrics DESIGN_SEALED; sample measurement **DONE** on canary  
6. ENABLE_UNDER_FENCES — **SIGNED**  

**Intent today:** ENABLE signed; CP-0075–0084 under fences; multi-canary + kill/abort drills **PASS**; F4 **DESIGN_SEALED**; full-adapter **R0–R3 DONE / R4 OPEN**; Gate6 **candidate remains**; **module LIVE_API_ENABLED=False**; 「listo」 **bajo fences**; remaining for product permanent: **operator F4 product ACK** · more real HTTP · streaming (optional).

---

## Related

- `docs/planning/GEMINI_DRY_RUN_EVIDENCE.md` · `council/NOTE_GEMINI_DRY_RUN.md` · `council/NOTE_GEMINI_PEER_DRY_RUN_WIRE.md`
- `GATE1_ENABLE_UNDER_FENCES_ACK_SIGNED.md` · `GATE2_ENABLE_READY.md` · `GATE3_ENABLE_READY.md` · `GATE4_ENABLE_READY.md` · `GATE5_HEALTH_CHECK_EVIDENCE.md`
- `GATE5_LIVE_FLAG_FLIP_RUNBOOK.md` · `GATE5_DESIGN_SEALED.md` · `GATE6_LIVE_ACCEPTANCE_METRICS.md`
- `docs/planning/LIVE_READINESS_CHECKLIST.md`
- `docs/planning/LIVE_100_OPERATOR_WALL.md`
- `docs/planning/LIVE_HTTP_TRANSPORT_RESIDUAL_DESIGN.md` · `DESIGN_CP_0076_LIVE_HTTP_TRANSPORT_RESIDUAL.md`
- `docs/planning/GATE6_METRIC_COMPLETION_DESIGN.md` · `DESIGN_CP_0077_GATE6_METRIC_COMPLETION.md`
- `docs/planning/IMPL_CP_0079_MULTI_CANARY_PACK.md` · `LIVE_API_PERMANENT_ENABLE_POLICY.md` · `GATE5_MULTI_CANARY_EVIDENCE.md` · `GATE6_MULTI_CANARY_MEASUREMENT.md`
- `docs/planning/IMPL_CP_0080_F4_KILL_ABORT.md` · `F4_DESIGN_SEALED.md` · `docs/ops/M_KILL_2_OPS_KILL_REFUSE_BUDGET.md` · `EVIDENCE_CP_0080_KILL_ABORT_DRILLS.md`
- `docs/planning/MESH_FULL_ADAPTER_LIVE_RV_DESIGN.md` · `DESIGN_CP_0081_MESH_FULL_ADAPTER_LIVE_RV.md` · `council/NOTE_DESIGN_CP_0081_MESH_FULL_ADAPTER_LIVE_RV.md`
- `docs/planning/MESH_FULL_ADAPTER_R1_SOT_REFUSE_I5_COMPOSE_CHECKLIST.md` · `IMPL_CP_0082_FULL_ADAPTER_R1_COMPOSE.md` · `council/NOTE_CP_0082_FULL_ADAPTER_R1_COMPOSE.md`
- `IMPL_CP_0083_FULL_ADAPTER_R2_MULTI_JUDGE.md` · `MESH_FULL_ADAPTER_R3_GATE6_SEAL_POLICY.md` · `IMPL_CP_0084_GATE6_LIVE_MEASUREMENT_SEAL_POLICY.md` · `council/NOTE_CP_0084_GATE6_LIVE_MEASUREMENT_SEAL_POLICY.md`
- `council/NOTE_DEEPSEEK_ACK_GATE5_CANARY.md` · `council/NOTE_DESIGN_CP_0076_LIVE_HTTP_TRANSPORT.md`
- `council/REPLY_DEEPSEEK_CP0076_DESIGN_HYGIENE_ACK.md` · `council/NOTE_DESIGN_CP_0077_GATE6_METRIC_COMPLETION.md`
- `council/HOLD_POSTURE_AND_REOPEN_CONDITIONS.md`

---

*End GEMINI_FREE_NEXT_STEPS — tip 56cdaa0→CP-0084; ENABLE SIGNED; CP-0075–0084; listo bajo fences; R3 DONE / R4 OPEN; Gate6 candidate remains; F4 ACK unsigned; module LIVE_API_ENABLED=False; NO_HELD unchanged.*
