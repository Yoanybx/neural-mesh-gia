# Operator note — Gate 4 live data policy (design-only)

- **Date:** 2026-09-27 America/New_York (EDT)
- **Author:** Grok Bot (Staff Eng — docs only; not an unlock)
- **Tip stack:** parent `0b6353c` (Gate 1 ACK draft unsigned) · `8c771a7` (live readiness checklist) · Google fenced / CP-0074
- **Package posture:** **0.18.0 HELD** · **live=DISABLED** · **M1=NO_CONSENSUS_YET** (N=2) · **D3 NOT ACKed** · **MESH_PERF_EXPERIMENTAL=OFF** · pkg0190 **NOT_OPENED**
- **Gate 1:** still **UNSIGNED** (`docs/planning/GATE1_LIVE_OPERATOR_ACK_DRAFT.md`)
- **Planning doc:** `docs/planning/GATE4_LIVE_DATA_POLICY.md`
- **Checklist:** `docs/planning/LIVE_READINESS_CHECKLIST.md` Gate 4
- **CP minted:** **No** (docs-only; no helpers/tests; no keys)

## Operator choice reflected

Leave Gate 1 **UNSIGNED**; proceed Gate 4 **docs only** (data policy + secret_handle for Gemini dry-run). **Do not** enable live.

## What this is

Design-only Gate 4 schedule: allowed vs forbidden egress classes, secret_handle create/rotate/revoke (I5 sees handle ids/digests never raw; handles live outside repo), Gemini free-tier dry-run schedule for *if* Gates 1–5 ever pass, logging hygiene (no `sk-`/Bearer in digests/CI).

## What this is not

- **Not** a Gate 4 seal — Gate 1 unsigned → Gate 4 **cannot seal**
- **Does not** flip `live_adapter.enabled` / `LIVE_API_ENABLED`
- **Does not** mint keys, call Gemini/providers, start D3, push, tag, or mint CP
- Default today remains **no real calls**

## Posture reaffirm

**live=DISABLED.** RefuseTransport default ON. No keys in repo. Gates **1–3** (and 5–6) still open before any flip.

## Related

- `docs/planning/GATE4_LIVE_DATA_POLICY.md`
- `docs/planning/LIVE_READINESS_CHECKLIST.md`
- `docs/planning/GATE1_LIVE_OPERATOR_ACK_DRAFT.md`
- `council/NOTE_GATE1_ACK_DRAFT.md`
- `council/NOTE_LIVE_READINESS.md`
- `docs/design/L_JUDGE_LIVE_ADAPTER_SAFETY_CASE.md` (CP-0058)
- `docs/planning/D1_L_JUDGE_SAFETY_CASE_MATURATION.md` (§7.2)
- `council/NOTE_GOOGLE_AI_TOOLS_FENCED.md`
