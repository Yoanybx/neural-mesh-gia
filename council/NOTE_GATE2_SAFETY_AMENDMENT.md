# Operator note — Gate 2 live safety-case amendment (design-only)

- **Date:** 2026-09-28 America/New_York (EDT)
- **Author:** Grok Bot (Staff Eng — docs only; not an unlock)
- **Tip stack:** parent `45ccc16` (Gate 5 flip runbook) · Gate4 `8f2eea6` · Gate1 draft `0b6353c` (unsigned) · checklist `8c771a7`
- **Package posture:** **0.18.0 HELD** · **live=DISABLED** · **M1=NO_CONSENSUS_YET** (N=2) · **D3 NOT ACKed** · **MESH_PERF_EXPERIMENTAL=OFF** · pkg0190 **NOT_OPENED**
- **Gate 1:** still **UNSIGNED** (`docs/planning/GATE1_LIVE_OPERATOR_ACK_DRAFT.md`)
- **Planning doc:** `docs/planning/GATE2_LIVE_SAFETY_CASE_AMENDMENT.md`
- **Checklist:** `docs/planning/LIVE_READINESS_CHECKLIST.md` Gate 2
- **CP minted:** **No** (docs-only; no helpers/tests; no keys; no flip)

## Operator choice reflected

Operator approved Gate 2 live safety-case **amendment** (design only — not live proof). **Do not** enable live · **do not** mint keys · **do not** call Gemini · **do not** start D3 · **do not** push/tag · **do not** mint CP.

## What this is

Design-only Gate 2 amendment covering: real transport blast radius; key compromise response; kill→RefuseTransport+ABORT; continuity under live peer failure; what D1 design proves vs what live still needs as evidence; RV-1..RV-7 drills still mock-green until live cycle; explicit NOT executed / not live proof. Cites D4-A..K, F4, RefuseTransport, I5 kill.

## What this is not

- **Not** a Gate 2 seal — Gate 1 unsigned → Gate 2 **cannot seal**
- **Not** live proof — RV drills remain mock-green; no real transport exercised
- **Does not** flip `live_adapter.enabled` / `LIVE_API_ENABLED`
- **Does not** mint keys, call Gemini/providers, start D3, push, tag, or mint CP
- Amendment **drafted as design**; live evidence **still Missing**

## Posture reaffirm

**live=DISABLED.** RefuseTransport default ON. No keys in repo. Gate 1 **UNSIGNED** → Gate 2 **cannot seal**. Gates **3–6** still open before any flip.

## Related

- `docs/planning/GATE2_LIVE_SAFETY_CASE_AMENDMENT.md`
- `docs/planning/LIVE_READINESS_CHECKLIST.md`
- `docs/planning/D1_L_JUDGE_SAFETY_CASE_MATURATION.md` (CP-0071)
- `council/COUNCIL_AGREEMENT_D4.md` (F4)
- `council/D4_CHATGPT_FINDINGS.md`
- `docs/planning/GATE1_LIVE_OPERATOR_ACK_DRAFT.md`
- `council/NOTE_GATE1_ACK_DRAFT.md`
- `docs/planning/GATE4_LIVE_DATA_POLICY.md`
- `docs/planning/GATE5_LIVE_FLAG_FLIP_RUNBOOK.md`
- `council/NOTE_GATE5_FLIP_RUNBOOK.md`
- `docs/design/L_JUDGE_LIVE_ADAPTER_SAFETY_CASE.md` (CP-0058)
- `src/neural_mesh/packaging/l_judge_live_adapter_safety.py`
