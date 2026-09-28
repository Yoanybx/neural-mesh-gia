# NOTE — Gemini free eval dry-run (NOT Mesh live)

**Date:** 2026-09-28 18:09:36 EDT (ET)  
**Tip base:** `fc4ef9e` (Gate1 SIGNED DISCUSS_ONLY)  
**Operator auth:** real **eval dry-run** one Gemini free API call — **not** Mesh live adapter enable  

## Posture (unchanged)

| Flag / gate | Value |
|-------------|-------|
| Gate1 | **SIGNED DISCUSS_ONLY** |
| live | **DISABLED** |
| `LIVE_API_ENABLED` | **False** (not flipped) |
| Mesh live adapter | **NOT_ENABLED** |
| Push / tags | **NONE** |
| Keys in repo/git | **NONE** |

## Secret handle

- **Path only:** `/home/box/.config/neural-mesh/gemini.env` (`GEMINI_API_KEY`)
- **Not** under workspace; `.gitignore` covers `gemini.env` and `.config/neural-mesh/`
- Key value **never** printed, committed, or embedded in evidence

## Call (synthetic prompt only)

- **Endpoint:** `generativelanguage.googleapis.com/v1beta/.../generateContent` (Google AI free)
- **Prompt:** `Reply with exactly: MESH_DRY_RUN_OK`
- **Requested models:** `gemini-2.0-flash` / `gemini-1.5-flash` (operator preference)
- **Actual model used:** `gemini-flash-latest` — 2.0/1.5/2.5 flash returned **404 model** (retired / not for new users); free API accepted `gemini-flash-latest`

## Outcome

| Field | Value |
|-------|-------|
| HTTP status | **200** |
| Success | **True** |
| Response text (short) | `MESH_DRY_RUN_OK` |
| OK marker | **True** (`MESH_DRY_RUN_OK` present) |
| Response SHA-256 | `6425bf176545c93c236d3fea4444a782422b70f0a9f03dd2582b2057452ab4f0` |
| modelVersion | `gemini-3.8-flash` |
| Usage (no secrets) | prompt=13 candidates=8 thoughts=71 total=92 tier=standard |

### Retired-model probes (error class = model, not auth/quota)

| Model | HTTP | Class |
|-------|------|-------|
| gemini-2.0-flash | 404 | model |
| gemini-1.5-flash | 404 | model |
| gemini-2.5-flash | 404 | model |

## What this is / is not

- **Is:** one-shot free-tier generateContent dry-run with out-of-band secret handle
- **Is not:** Gate5 canary, D3 start, `LIVE_API_ENABLED` flip, live_adapter enable, Vertex paid, push/tag

## Related

- `docs/planning/GEMINI_DRY_RUN_EVIDENCE.md`
- `docs/planning/GEMINI_FREE_NEXT_STEPS.md` (steps 1–2 updated)
- `docs/planning/GATE1_LIVE_OPERATOR_ACK_SIGNED.md`
- `council/NOTE_LEAVE_HOLD_GATE1_DISCUSS_ONLY.md`

---
*End NOTE_GEMINI_DRY_RUN — live=DISABLED; Gate1 DISCUSS_ONLY; no keys in git.*
