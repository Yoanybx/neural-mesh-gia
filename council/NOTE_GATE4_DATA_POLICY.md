# Operator note — Gate 4 live data policy (DESIGN_SEALED / DISCUSS_ONLY eval)

- **Date:** 2026-09-28 ~18:48 EDT (America/New_York) — design seal cycle
- **Author:** Grok Bot `<grok-bot@local>` (Staff Eng — docs only; not an unlock)
- **Tip stack:** base `ce53e7c` (Gate3 DESIGN_SEALED) · peer wire `30fe593` · dry-run `1e502c6` · leave-Hold `fc4ef9e`
- **Package posture:** **0.18.0 HELD** · **live=DISABLED** · **LIVE_API_ENABLED=False** · **RefuseTransport ON** · **M1=NO_CONSENSUS_YET** (N=2) · **D3 NOT ACKed** · **MESH_PERF_EXPERIMENTAL=OFF** · pkg0190 **NOT_OPENED** · **NO_HELD** stays NO_HELD
- **Gate 1:** **SIGNED DISCUSS_ONLY** (`GATE1_LIVE_OPERATOR_ACK_SIGNED.md`) — no invent ENABLE signature
- **Gate 2/3:** **DESIGN_SEALED** (discuss/eval)
- **Gate 4:** **DESIGN_SEALED** (discuss/eval) — `docs/planning/GATE4_DESIGN_SEALED.md` · `docs/planning/GATE4_LIVE_DATA_POLICY.md`
- **Checklist:** `docs/planning/LIVE_READINESS_CHECKLIST.md` Gate 4
- **CP minted:** **No** (docs-only; no helpers/tests; no keys in git)

## Operator choice reflected

Leave Gate 1 at **DISCUSS_ONLY**; seal Gate 4 **design** for eval data policy + secret_handle. **Do not** enable live. **Do not** execute Gate5 canary.

## What this is

DESIGN_SEALED Gate 4 schedule for DISCUSS_ONLY/eval: allowed vs forbidden egress classes, secret_handle create/rotate/revoke (I5 sees handle ids/digests never raw; handles live outside repo), eval handle `mesh://secrets/judge/gemini-free@v1` at oob `/home/box/.config/neural-mesh/gemini.env`, dry-run flag vs Mesh live RefuseTransport, logging hygiene (no `sk-`/Bearer in digests/CI).

## What this is not

- **Not** a Gate 4 **ENABLE** seal — Mesh live data ACK / ENABLE_UNDER_FENCES still **OPEN**
- **Does not** flip `live_adapter.enabled` / `LIVE_API_ENABLED`
- **Does not** mint keys into repo, call Mesh live Gemini, start D3, push, tag, or mint CP
- **Does not** authorize Gate5 canary execution
- Default Mesh live today remains **no real calls** (RefuseTransport)

## Posture reaffirm

**live=DISABLED.** RefuseTransport default ON. No keys in repo. Gate5 canary still **NOT** until ENABLE chain. Next design seal = **Gate5 runbook** (docs only).

## Related

- `docs/planning/GATE4_DESIGN_SEALED.md` · `docs/planning/GATE4_LIVE_DATA_POLICY.md`
- `docs/planning/LIVE_READINESS_CHECKLIST.md` · `docs/planning/GEMINI_FREE_NEXT_STEPS.md`
- `council/NOTE_GATE4_DESIGN_SEALED.md`
- `docs/planning/GATE1_LIVE_OPERATOR_ACK_SIGNED.md`
- `docs/design/L_JUDGE_LIVE_ADAPTER_SAFETY_CASE.md` (CP-0058)
- `docs/planning/D1_L_JUDGE_SAFETY_CASE_MATURATION.md` (§7.2)
- `council/NOTE_GOOGLE_AI_TOOLS_FENCED.md` · `NOTE_GEMINI_DRY_RUN.md` · `NOTE_GEMINI_PEER_DRY_RUN_WIRE.md`
