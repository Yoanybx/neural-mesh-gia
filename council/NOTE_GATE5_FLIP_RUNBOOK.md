# Operator note — Gate 5 RefuseTransport → live flag flip runbook (DESIGN_SEALED / procedure)

- **Date:** 2026-09-28 America/New_York (EDT) — design-sealed ~18:50 EDT
- **Author:** Grok Bot `<grok-bot@local>` (Staff Eng — docs only; not an unlock)
- **Tip stack:** base `5879321` (Gate4 DESIGN_SEALED) · Gate3 `ce53e7c` · Gate2 `7c436f8` · peer wire `30fe593` · dry-run `1e502c6` · leave-Hold `fc4ef9e`
- **Package posture:** **0.18.0 HELD** · **live=DISABLED** · **LIVE_API_ENABLED=False** · **RefuseTransport ON** · **M1=NO_CONSENSUS_YET** (N=2) · **D3 NOT ACKed** · **MESH_PERF_EXPERIMENTAL=OFF** · pkg0190 **NOT_OPENED** · **NO_HELD** stays NO_HELD
- **Gate 1:** **SIGNED DISCUSS_ONLY** (`docs/planning/GATE1_LIVE_OPERATOR_ACK_SIGNED.md`) — ENABLE_UNDER_FENCES **not** invented
- **Gates 2–4:** **DESIGN_SEALED** (discuss/eval); ENABLE seals **OPEN**
- **Planning doc:** `docs/planning/GATE5_LIVE_FLAG_FLIP_RUNBOOK.md`
- **Seal artifact:** `docs/planning/GATE5_DESIGN_SEALED.md`
- **Checklist:** `docs/planning/LIVE_READINESS_CHECKLIST.md` Gate 5
- **CP minted:** **No** (docs-only; no helpers/tests; no keys; no flip)

## Operator choice reflected

Proceed Gate 5 **DESIGN_SEALED** (RefuseTransport → live flag flip **runbook / canary procedure**). **Do not** execute canary · **do not** enable live · **do not** flip flags · **do not** mint keys · **do not** call Mesh live Gemini · **do not** start D3 · **do not** push/tag · **do not** mint CP · **do not** invent ENABLE_UNDER_FENCES.

## What this is

Design-sealed ordered flip procedure: (1) Gate1 ENABLE ACK (2) Gate2 safety amendment enable-ready (3) Gate3 matrix-bound config (4) Gate4 handles+data schedule Mesh-live ACK’d (5) health check (6) single canary under kill-armed I5 (7) ledger evidence — plus negative tests / fail-closed; abort→RefuseTransport; never partial enable. Preconditions require Gates **1–4 enable-ready** + operator ENABLE ACK.

## What this is not

- **Not** canary execution — **NOT STARTED / NOT AUTHORIZED** under DISCUSS_ONLY
- **Does not** flip `live_adapter.enabled` / `LIVE_API_ENABLED` (stays **False**)
- **Does not** mint keys, call Mesh live providers, start D3, push, tag, or mint CP
- Dry-run peer `30fe593` is **NOT** a live canary
- ENABLE seals for Gates 2–4 still **OPEN**

## Posture reaffirm

**live=DISABLED.** RefuseTransport default ON. No keys in repo. Flags remain **false**. Next docs = Gate 6 metrics DESIGN_SEALED. Canary later only after ENABLE chain.

## Related

- `docs/planning/GATE5_DESIGN_SEALED.md` · `docs/planning/GATE5_LIVE_FLAG_FLIP_RUNBOOK.md`
- `docs/planning/LIVE_READINESS_CHECKLIST.md` · `docs/planning/GEMINI_FREE_NEXT_STEPS.md`
- `docs/planning/GATE4_DESIGN_SEALED.md` · `council/NOTE_GATE4_DESIGN_SEALED.md`
- `docs/planning/GATE1_LIVE_OPERATOR_ACK_SIGNED.md` · `council/NOTE_LEAVE_HOLD_GATE1_DISCUSS_ONLY.md`
- `council/NOTE_GEMINI_PEER_DRY_RUN_WIRE.md`
- `docs/design/L_JUDGE_LIVE_ADAPTER_SAFETY_CASE.md` (CP-0058)
- `docs/planning/D1_L_JUDGE_SAFETY_CASE_MATURATION.md` (RefuseTransport · I5 kill)
- `src/neural_mesh/packaging/l_judge_live_adapter_safety.py`
- `src/neural_mesh/packaging/google_l_judge_peer_spike.py` (`LIVE_API_ENABLED=False`)
