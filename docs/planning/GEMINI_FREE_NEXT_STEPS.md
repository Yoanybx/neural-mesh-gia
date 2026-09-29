# Gemini free-tier — next steps (ENABLE_UNDER_FENCES)

**Status:** Ordered plan under Gate1 **SIGNED ENABLE_UNDER_FENCES** (「Aprobado」 2026-09-28 ~19:41 ET)  
**Does not** mint keys into repo · **does not** start D3 · **does not** push/tag · **does not** unlock NO_HELD  
**Scope:** Gemini **free-tier canary only**; Vertex paid **OUT**  
**Posture:** **`LIVE_API_ENABLED=False`** (module final); RefuseTransport default ON; Gates 2–4 ENABLE_READY; **CP-0075** canary; **CP-0076 DESIGN_ONLY**; **CP-0077** Gate6 metric design; **CP-0078 IMPL** LiveHttpTransport v0 (still default-off)  
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
| **11** | **Multi-canary measurement pack** (n≥N + edges) | **OPEN** — needs operator/runbook; not authorized by CP-0077 | Claim seal from n=1; skip E-KILL/E-ABORT |
| **12** | **Codec impl CP** (after CP-0076 design) | **DONE** — **CP-0078** `IMPL_CP_0078_LIVE_HTTP_TRANSPORT.md` (v0 unary; runtime LIVE+I5; module LIVE false) | Claim permanent enable; streaming |
| **13** | **Permanent LIVE_API enable policy / runbook** | **OPEN** — do **not** permanently flip without runbook | Leave module LIVE true after canary |
| **14** | **F4 product-enable ACK** (if treating as listo beyond ENABLE_UNDER_FENCES) | **OPEN** — ENABLE_UNDER_FENCES signed for canary/fenced path; permanent product enable still operator | Invent F4 unlock |

---

## Serial gates reminder

Before any flag flip:

1. Gate2 — **ENABLE_READY** (docs) under SIGNED ENABLE; Mesh live RV still OPEN  
2. Gate3 — **ENABLE_READY** (docs); runtime not live-enabled  
3. Gate4 — **ENABLE_READY** (docs); oob key only  
4. Gate5 runbook DESIGN_SEALED; step (5) **PASS**; step (6) **EXECUTED** (CP-0075)  
5. Gate6 metrics DESIGN_SEALED; sample measurement **DONE** on canary  
6. ENABLE_UNDER_FENCES — **SIGNED**  

**Intent today:** ENABLE signed; CP-0075 canary done; CP-0076/0077 DESIGN_ONLY; **CP-0078** LiveHttpTransport v0 **authorized/shipped** (default-off); **module LIVE_API_ENABLED=False**; multi-canary n≥5 + permanent enable policy + F4 product-enable still **OPEN**.

---

## Related

- `docs/planning/GEMINI_DRY_RUN_EVIDENCE.md` · `council/NOTE_GEMINI_DRY_RUN.md` · `council/NOTE_GEMINI_PEER_DRY_RUN_WIRE.md`
- `GATE1_ENABLE_UNDER_FENCES_ACK_SIGNED.md` · `GATE2_ENABLE_READY.md` · `GATE3_ENABLE_READY.md` · `GATE4_ENABLE_READY.md` · `GATE5_HEALTH_CHECK_EVIDENCE.md`
- `GATE5_LIVE_FLAG_FLIP_RUNBOOK.md` · `GATE5_DESIGN_SEALED.md` · `GATE6_LIVE_ACCEPTANCE_METRICS.md`
- `docs/planning/LIVE_READINESS_CHECKLIST.md`
- `docs/planning/LIVE_100_OPERATOR_WALL.md`
- `docs/planning/LIVE_HTTP_TRANSPORT_RESIDUAL_DESIGN.md` · `DESIGN_CP_0076_LIVE_HTTP_TRANSPORT_RESIDUAL.md`
- `docs/planning/GATE6_METRIC_COMPLETION_DESIGN.md` · `DESIGN_CP_0077_GATE6_METRIC_COMPLETION.md`
- `council/NOTE_DEEPSEEK_ACK_GATE5_CANARY.md` · `council/NOTE_DESIGN_CP_0076_LIVE_HTTP_TRANSPORT.md`
- `council/REPLY_DEEPSEEK_CP0076_DESIGN_HYGIENE_ACK.md` · `council/NOTE_DESIGN_CP_0077_GATE6_METRIC_COMPLETION.md`
- `council/HOLD_POSTURE_AND_REOPEN_CONDITIONS.md`

---

*End GEMINI_FREE_NEXT_STEPS — ENABLE SIGNED; CP-0075 canary; CP-0076/0077 DESIGN_ONLY; CP-0078 LiveHttpTransport v0 shipped (default-off); module LIVE_API_ENABLED=False; n=1≠seal; multi-canary+permanent enable OPEN; NO_HELD unchanged.*
