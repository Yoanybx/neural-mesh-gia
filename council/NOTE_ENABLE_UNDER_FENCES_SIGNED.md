# NOTE — Gate1 ENABLE_UNDER_FENCES SIGNED (2026-09-28)

- **Date:** 2026-09-28 ~19:41 EDT (America/New_York)
- **Author:** Grok Bot `<grok-bot@local>`
- **Operator:** Joan / Yoan V (repo owner)
- **Mark:** chat **「Aprobado」** — honest wall = approve signing `ENABLE_UNDER_FENCES`
- **Tip base:** `a816c34` (dual Gate2–6 hygiene ACK **PASS**; live was DISABLED pending this signature)
- **Artifact:** `docs/planning/GATE1_ENABLE_UNDER_FENCES_ACK_SIGNED.md`

## What changed

| Item | Prior | Now |
|------|-------|-----|
| Gate1 intent | **SIGNED DISCUSS_ONLY** | **SIGNED ENABLE_UNDER_FENCES** |
| Gates 2–4 | DESIGN_SEALED (discuss/eval) | **ENABLE_READY** (docs) + prior design seals |
| Gate5 | procedure DESIGN_SEALED; canary not authorized | step (5) health **PASS**; step (6) **BLOCKED** (`impl_cp_not_authorized` / NT-10) |
| `LIVE_API_ENABLED` | False | **False** (not flipped) |
| Dual hygiene ACK | PASS | PASS (unchanged; hygiene ≠ ENABLE) |

## What did not change

- No keys in git; key remains `/home/box/.config/neural-mesh/gemini.env` only
- RefuseTransport default **ON**
- NO_HELD: Raft/N>2/GIA/train/SaaS/pkg0190 — **unchanged**
- D3 NOT ACKed; no push/tags; no retag v0.16.3/v0.17.0/v0.18.0
- Dry-run ≠ canary / live RV
- `evaluate_enablement_gates` → `may_enable=False` until authorized impl CP

## Next (honest)

1. Authorized **impl CP** to clear NT-10 / controlled live binding (do not invent)
2. Gate5 step (6) single canary under kill-armed I5 + ledger
3. Gate6 live measurement on canary evidence

## Related

- `council/NOTE_LEAVE_HOLD_GATE1_DISCUSS_ONLY.md` (prior leave-Hold; intent now upgraded)
- `council/COUNCIL_AGREEMENT_DESIGN_SEAL_GATES_2_6.md` (hygiene PASS retained)
- `docs/planning/GATE5_HEALTH_CHECK_EVIDENCE.md`

---
*End NOTE_ENABLE_UNDER_FENCES_SIGNED — ENABLE signed; LIVE_API_ENABLED=False; canary blocked on impl CP.*
