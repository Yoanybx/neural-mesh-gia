# Gemini free-tier — next steps (ENABLE_UNDER_FENCES)

**Status:** Ordered plan under Gate1 **SIGNED ENABLE_UNDER_FENCES** (「Aprobado」 2026-09-28 ~19:41 ET)  
**Does not** mint keys into repo · **does not** start D3 · **does not** push/tag · **does not** invent impl CP / auto-flip without NT-10 clearance  
**Scope:** Gemini **free-tier canary only**; Vertex paid **OUT**  
**Posture:** **`LIVE_API_ENABLED=False`**; RefuseTransport default ON; Gates 2–4 ENABLE_READY  
**Cite:** `GATE1_ENABLE_UNDER_FENCES_ACK_SIGNED.md` · prior DISCUSS_ONLY + leave-Hold notes  
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
| **4b** | **Gate5 canary later** — health check → single canary under kill-armed I5 → ledger evidence (Gate5 steps 1–7) | **NOT STARTED / NOT AUTHORIZED** — only after Gates 2–4 **enable**-ready + Gate1 scope upgrade if operator marks ENABLE_UNDER_FENCES; dry-run `30fe593` ≠ canary | Canary / flip without full ENABLE chain |
| **5** | **Gate6 metrics design seal** — acceptance metrics toward DESIGN_SEALED (docs) | **DONE (DESIGN_SEALED)** — `GATE6_DESIGN_SEALED.md` · `GATE6_LIVE_ACCEPTANCE_METRICS.md`; live measurement OPEN; dry-run ≠ live RV | Claim canary evidence without Gate5 execution; flip live flags; invent ENABLE signature |
| **6** | **ENABLE_UNDER_FENCES** — operator signature | **SIGNED** — `GATE1_ENABLE_UNDER_FENCES_ACK_SIGNED.md` (「Aprobado」 ~19:41 ET) | Invent extra unlocks; commit keys |
| **6b** | **Gates 2–4 ENABLE_READY** — docs enable-ready seals under ENABLE | **DONE** — `GATE2/3/4_ENABLE_READY.md` | Claim live RV complete; flip without Gate5 |
| **6c** | **Gate5 step (5) health** | **PASS** — `GATE5_HEALTH_CHECK_EVIDENCE.md` | Treat as canary / flag flip |
| **7** | **Gate5 step (6) canary / LIVE_API_ENABLED flip** | **BLOCKED** — `may_enable=False` / `impl_cp_not_authorized` (NT-10); no Mesh live transport beyond RefuseTransport | Half-flip; invent impl CP; treat dry-run as canary |
| **8** | **Gate6 live measurement** on canary evidence | **OPEN** — after authorized canary | Claim design metrics = live RV |

---

## Serial gates reminder

Before any flag flip:

1. Gate2 — **ENABLE_READY** (docs) under SIGNED ENABLE; Mesh live RV still OPEN  
2. Gate3 — **ENABLE_READY** (docs); runtime not live-enabled  
3. Gate4 — **ENABLE_READY** (docs); oob key only  
4. Gate5 runbook DESIGN_SEALED; step (5) **PASS**; step (6) **BLOCKED** (`impl_cp_not_authorized`)  
5. Gate6 metrics DESIGN_SEALED; live measurement after canary  
6. ENABLE_UNDER_FENCES — **SIGNED**  

**Intent today:** **ENABLE_UNDER_FENCES** — canary path authorized in governance; **flag flip held** until authorized impl CP clears NT-10.

---

## Related

- `docs/planning/GEMINI_DRY_RUN_EVIDENCE.md` · `council/NOTE_GEMINI_DRY_RUN.md` · `council/NOTE_GEMINI_PEER_DRY_RUN_WIRE.md`
- `GATE1_ENABLE_UNDER_FENCES_ACK_SIGNED.md` · `GATE2_ENABLE_READY.md` · `GATE3_ENABLE_READY.md` · `GATE4_ENABLE_READY.md` · `GATE5_HEALTH_CHECK_EVIDENCE.md`
- `GATE5_LIVE_FLAG_FLIP_RUNBOOK.md` · `GATE5_DESIGN_SEALED.md` · `GATE6_LIVE_ACCEPTANCE_METRICS.md`
- `docs/planning/LIVE_READINESS_CHECKLIST.md`
- `docs/planning/LIVE_100_OPERATOR_WALL.md`
- `council/HOLD_POSTURE_AND_REOPEN_CONDITIONS.md`

---

*End GEMINI_FREE_NEXT_STEPS — ENABLE_UNDER_FENCES SIGNED; Gates 2–4 ENABLE_READY; LIVE_API_ENABLED=False; next=authorized impl CP then Gate5 canary; NO_HELD unchanged.*
