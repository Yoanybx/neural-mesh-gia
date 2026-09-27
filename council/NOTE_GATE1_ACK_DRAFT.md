# Operator note — Gate 1 live ACK draft (unsigned)

- **Date:** 2026-09-27 America/New_York (EDT)
- **Author:** Grok Bot (Staff Eng — docs only; not an unlock)
- **Tip stack:** parent `8c771a7` (live readiness checklist) · atop `74ce42e` (Google free AI tools fenced) · CP-0074 (`4b43bf4`)
- **Package posture:** **0.18.0 HELD** · **live=DISABLED** · **M1=NO_CONSENSUS_YET** (N=2) · **D3 NOT ACKed** · **MESH_PERF_EXPERIMENTAL=OFF** · pkg0190 **NOT_OPENED**
- **Draft artifact:** `docs/planning/GATE1_LIVE_OPERATOR_ACK_DRAFT.md`
- **Checklist:** `docs/planning/LIVE_READINESS_CHECKLIST.md` Gate 1
- **CP minted:** **No** (docs-only; no helpers/tests)

## What this is

Fillable / signable **Gate 1** draft for the operator (Joan / Yoan) to edit and later ACK for live *discussion* or *enable-under-fences* intent.

## What this is not

- **Not signed** — status remains DRAFT
- **Does not** flip `live_adapter.enabled` / `LIVE_API_ENABLED`
- **Does not** mint keys, call Gemini/providers, start D3, push, tag, or mint CP
- Google tools **APPROVE_WITH_FENCES**, D4 lock, D1 seal, and mock spike **do not** count as this ACK

## Posture reaffirm

**live=DISABLED.** Gates **2–5** (plus Gate 6 acceptance bundle) still required before any flip. RefuseTransport default stays ON.

## Operator next (optional)

1. Edit scope string fields in the draft (provider, env, data classes, kill/rollback, OUT-of-scope).
2. Choose intent: `DISCUSS_ONLY` or `ENABLE_UNDER_FENCES`.
3. Sign only when ready — signing still does not auto-enable live.

## Related

- `docs/planning/GATE1_LIVE_OPERATOR_ACK_DRAFT.md`
- `docs/planning/LIVE_READINESS_CHECKLIST.md`
- `council/NOTE_LIVE_READINESS.md`
- `council/COUNCIL_AGREEMENT_D4.md` (F3/F4)
- `docs/planning/D1_L_JUDGE_SAFETY_CASE_MATURATION.md`
- `council/NOTE_GOOGLE_AI_TOOLS_FENCED.md`
