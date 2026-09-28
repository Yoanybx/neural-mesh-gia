# Gemini free-tier — next steps (DISCUSS_ONLY)

**Status:** Ordered plan under Gate1 **SIGNED DISCUSS_ONLY** (2026-09-28)  
**Does not** enable Mesh live · **does not** mint keys into repo · **does not** start D3 · **does not** push/tag · **does not** flip `LIVE_API_ENABLED`  
**Scope:** Gemini **free-tier eval only**; Vertex paid **OUT**  
**Posture:** **live=DISABLED**; flags `live=false` held  
**Cite:** `docs/planning/GATE1_LIVE_OPERATOR_ACK_SIGNED.md` · `council/NOTE_LEAVE_HOLD_GATE1_DISCUSS_ONLY.md`  
**Dry-run evidence:** `council/NOTE_GEMINI_DRY_RUN.md` · `docs/planning/GEMINI_DRY_RUN_EVIDENCE.md` (2026-09-28 18:09 ET)

---

## Ordered next (still no Mesh live enable)

| Step | Action | Status | Forbidden now |
|------|--------|--------|---------------|
| **1** | **secret_handle outside repo** — provision handle in out-of-band store; record handle path / digest only | **DONE (eval)** — handle at `/home/box/.config/neural-mesh/gemini.env`; `.gitignore` covers `gemini.env` / `.config/neural-mesh/`; key never in git | Raw key in repo, CI, evidence digests, chat |
| **2** | **Dry-run** — one-shot free `generateContent` with synthetic prompt; evidence without secrets | **DONE (eval)** — HTTP 200; model `gemini-flash-latest` (2.0/1.5 flash retired → 404 model); marker `MESH_DRY_RUN_OK`; see evidence notes | Mesh live adapter enable; flip `LIVE_API_ENABLED`; Gate5 canary without serial gates |
| **3** | **Gate5 canary later** — health check → single canary under kill-armed I5 → ledger evidence (Gate5 steps 1–7) | **NOT STARTED** — only after Gates 2–4 sealed + Gate1 scope upgrade if operator marks ENABLE_UNDER_FENCES | Canary / flip `live_adapter.enabled` / `LIVE_API_ENABLED` without full chain |

---

## Serial gates reminder

Before any flag flip:

1. Gate2 live safety-case amendment + live proof  
2. Gate3 Authority Matrix in use  
3. Gate4 secret_handle outside repo + live data schedule  
4. Gate5 canary under kill-armed I5  
5. Gate6 acceptance metrics on canary evidence  

**Intent today:** **DISCUSS_ONLY** — eval dry-run authorized; upgrade to ENABLE_UNDER_FENCES requires a **new** operator mark.

---

## Related

- `docs/planning/GEMINI_DRY_RUN_EVIDENCE.md` · `council/NOTE_GEMINI_DRY_RUN.md`
- `docs/planning/GATE4_LIVE_DATA_POLICY.md` · `docs/planning/GATE5_LIVE_FLAG_FLIP_RUNBOOK.md`
- `docs/planning/LIVE_READINESS_CHECKLIST.md`
- `docs/planning/LIVE_100_OPERATOR_WALL.md`
- `council/HOLD_POSTURE_AND_REOPEN_CONDITIONS.md`

---

*End GEMINI_FREE_NEXT_STEPS — discuss only; live=DISABLED; eval dry-run done; no Mesh live enable.*
