# Hold posture and reopen conditions

**Status:** Binding under **COUNCIL_AGREEMENT_HOLD_STAY** (2026-09-28)  
**Tip at seal:** ~`ec11e55` · package **0.18.0 HELD** · **live=DISABLED** · Gate1 **UNSIGNED**

## Current posture

- Hold A sealed (`NOTE_OPERATOR_HOLD_POST_WALL.md`); mock roadmap 1–5 complete (`NOTE_HOLD_MOCK_ROADMAP_COMPLETE.md`).
- Live readiness Gates 1–6 exist as **design drafts only** — none sealed.
- RefuseTransport default ON; no keys; no real Gemini; D3 NOT ACKed; M1 NO_CONSENSUS_YET (N=2).

## Reopen triggers (operator only)

Live-track discussion / enable path reopens **only** when the operator explicitly:

1. Leaves Hold (written), and  
2. Signs Gate1 (`GATE1_LIVE_OPERATOR_ACK_DRAFT.md`) as DISCUSS_ONLY or ENABLE_UNDER_FENCES.

Mock green / design completeness / this consensus **do not** reopen live.

## Before any live flip (serial)

Gates 2–5 seal with evidence + Gate4 secret_handle **outside repo** + Gate5 canary under kill-armed I5 + Gate6 metrics + D4 F4 safety amendment. Agent must not flip `live_adapter.enabled` / `LIVE_API_ENABLED` without that chain.

## Fences restated

- **F3:** D1/design artifacts do not enable live.  
- **F4:** live reconsideration needs separate cycle + operator ACK + safety amendment.  
- NO_HELD/PARKED: GIA, Raft/N>2, train 70B, SaaS, pkg0190 — unchanged.

## Grok Bot under HOLD_STAY

Stop inventing mock feature work. Docs reconciliation OK. No push/tags/keys/live/D3/experimental flips.
