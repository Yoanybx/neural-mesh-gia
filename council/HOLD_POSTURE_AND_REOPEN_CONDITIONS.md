# Hold posture and reopen conditions

**Status:** Hold A **LEFT** (operator override 2026-09-28) · Gate1 **SIGNED DISCUSS_ONLY** · live still **DISABLED**  
**Prior seal:** Binding under **COUNCIL_AGREEMENT_HOLD_STAY** (2026-09-28) until operator leave  
**Tip at prior seal:** ~`ec11e55` / HOLD_STAY tip ~`9348651` · package **0.18.0 HELD** · **live=DISABLED**  
**Leave-Hold cite:** Operator YES in chat 2026-09-28 · `council/NOTE_LEAVE_HOLD_GATE1_DISCUSS_ONLY.md` · ACK `docs/planning/GATE1_LIVE_OPERATOR_ACK_SIGNED.md`

## Current posture

- Hold A **left** — operator explicit override (leave Hold + Gate1 DISCUSS_ONLY).
- Gate1 **SIGNED — DISCUSS_ONLY** (Gemini free-tier eval only; Vertex paid OUT).
- **Reopen trigger met for discussion only** — not for live enable.
- Live readiness Gates 2–6 remain **design drafts** — not sealed; no live proof.
- RefuseTransport default ON; no keys in repo; no real Gemini calls; D3 NOT ACKed; M1 NO_CONSENSUS_YET (N=2).
- Flags: `live_adapter.enabled=false` / `LIVE_API_ENABLED=false` **held**; network egress **none** until Gates 2–5.

## Reopen triggers (operator only)

Live-track discussion / enable path reopens **only** when the operator explicitly:

1. Leaves Hold (written), and  
2. Signs Gate1 (`GATE1_LIVE_OPERATOR_ACK_DRAFT.md` / `_SIGNED.md`) as DISCUSS_ONLY or ENABLE_UNDER_FENCES.

**2026-09-28:** Both met → **discussion reopen only** (intent DISCUSS_ONLY).  
Mock green / design completeness / HOLD_STAY consensus **do not** reopen live enable.

## Before any live flip (serial)

Gates 2–5 seal with evidence + Gate4 secret_handle **outside repo** + Gate5 canary under kill-armed I5 + Gate6 metrics + D4 F4 safety amendment. Agent must not flip `live_adapter.enabled` / `LIVE_API_ENABLED` without that chain.  
Next discuss path: `docs/planning/GEMINI_FREE_NEXT_STEPS.md`.

## Fences restated

- **F3:** D1/design artifacts do not enable live.  
- **F4:** live reconsideration needs separate cycle + operator ACK + safety amendment.  
- NO_HELD/PARKED: GIA, Raft/N>2, train 70B, SaaS, pkg0190 — unchanged.
- **DISCUSS_ONLY ≠ ENABLE** — signed Gate1 does not flip flags.

## Grok Bot under DISCUSS_ONLY (post leave-Hold)

Docs reconciliation + Gemini free next-steps design OK. No push/tags/keys/live/D3/experimental flips. No real API calls until Gates 2–5 chain + operator enable intent.
