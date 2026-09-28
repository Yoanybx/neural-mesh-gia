# Gemini free-tier — next steps (DISCUSS_ONLY)

**Status:** Ordered plan under Gate1 **SIGNED DISCUSS_ONLY** (2026-09-28)  
**Does not** enable live · **does not** mint keys into repo · **does not** make real API calls · **does not** start D3 · **does not** push/tag  
**Scope:** Gemini **free-tier eval only**; Vertex paid **OUT**  
**Posture:** **live=DISABLED**; network egress **none** until Gates 2–5; flags `live=false` held  
**Cite:** `docs/planning/GATE1_LIVE_OPERATOR_ACK_SIGNED.md` · `council/NOTE_LEAVE_HOLD_GATE1_DISCUSS_ONLY.md`

---

## Ordered next (still no enable)

| Step | Action | When | Forbidden now |
|------|--------|------|---------------|
| **1** | **secret_handle outside repo** — provision/rotate handle in out-of-band store per Gate4 schedule; record handle id / digest only | Gate4 path; after discuss fences settled | Raw key in repo, CI, evidence digests, chat |
| **2** | **Dry-run script design** — document inputs/outputs, refuse-default negatives, no-network stub, kill-armed I5 preconditions | Design only; may land as docs/helpers later under separate ACK | Real Gemini call; resolving secret into process env on shared box without operator |
| **3** | **Gate5 canary later** — health check → single canary under kill-armed I5 → ledger evidence (Gate5 steps 1–7) | Only after Gates 2–4 sealed + Gate1 scope still DISCUSS→enable path if operator upgrades intent | Canary in this commit; flip `live_adapter.enabled` / `LIVE_API_ENABLED` without full chain |

---

## Serial gates reminder

Before any flag flip:

1. Gate2 live safety-case amendment + live proof  
2. Gate3 Authority Matrix in use  
3. Gate4 secret_handle outside repo + live data schedule  
4. Gate5 canary under kill-armed I5  
5. Gate6 acceptance metrics on canary evidence  

**Intent today:** **DISCUSS_ONLY** — upgrade to ENABLE_UNDER_FENCES requires a **new** operator mark if desired.

---

## Related

- `docs/planning/GATE4_LIVE_DATA_POLICY.md` · `docs/planning/GATE5_LIVE_FLAG_FLIP_RUNBOOK.md`
- `docs/planning/LIVE_READINESS_CHECKLIST.md`
- `docs/planning/LIVE_100_OPERATOR_WALL.md`
- `council/HOLD_POSTURE_AND_REOPEN_CONDITIONS.md`

---

*End GEMINI_FREE_NEXT_STEPS — discuss only; live=DISABLED; no enable.*
