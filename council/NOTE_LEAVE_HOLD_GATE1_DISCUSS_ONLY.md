# NOTE — Leave Hold A; Gate1 SIGNED DISCUSS_ONLY (2026-09-28)

- **Date:** 2026-09-28 America/New_York (EDT)
- **Author:** Grok Bot (Staff Eng — docs only; not an unlock)
- **Operator:** Joan Alberto Barrios Cruz / Yoan V
- **Cite:** Operator YES in chat 2026-09-28 — leave Hold; sign Gate1 as **DISCUSS_ONLY**; Gemini free-tier eval only
- **Tip parent:** ~`9348651` (`COUNCIL_AGREEMENT_HOLD_STAY` / reopen conditions)
- **Package posture:** **0.18.0 HELD** · **Hold A LEFT** · **live=DISABLED** · **Gate1 SIGNED DISCUSS_ONLY** · **M1=NO_CONSENSUS_YET** · **D3 NOT ACKed** · **MESH_PERF_EXPERIMENTAL=OFF** · pkg0190 **NOT_OPENED**

## What changed

| Item | Prior (HOLD_STAY) | Now |
|------|-------------------|-----|
| Hold A | Sealed / stay | **LEFT** — operator explicit override |
| Gate1 | UNSIGNED draft | **SIGNED — DISCUSS_ONLY** |
| Provider scope | N/A under Hold freeze | **Gemini free-tier eval only**; Vertex paid **OUT** |
| Live flags | DISABLED / FROZEN | Still **DISABLED** (`live=false` held) |
| Network egress | none | **none** until Gates 2–5 |
| Keys / real API calls | none | **none** in this commit; none until Gate4+Gate5 chain |
| D3 / push / tags | NO | **NO** |

## What did not change

- **live still DISABLED** — discussion ≠ enable
- No keys in repo; no secret_handle provisioned yet
- No real Gemini/provider calls
- Gates **2–5** (+ Gate 6 bundle) still required before any flag flip
- RefuseTransport default **ON**
- NO_HELD/PARKED: GIA, Raft/N>2, train 70B, SaaS, pkg0190 — unchanged
- D3 NOT ACKed; `MESH_PERF_EXPERIMENTAL=OFF`

## Reopen trigger

Per `council/HOLD_POSTURE_AND_REOPEN_CONDITIONS.md`: operator (1) left Hold in writing and (2) signed Gate1 as **DISCUSS_ONLY**.  
**Reopen = discussion only** — not live enable.

## Next (ordered; still no enable)

See `docs/planning/GEMINI_FREE_NEXT_STEPS.md`:

1. **Gate4** secret_handle provision **OUTSIDE repo** (design + out-of-band store; no keys in tree)
2. Dry-run script **design** (no real call yet)
3. Gate5 canary **later** under kill-armed I5 — not this commit

## Artifacts

- `docs/planning/GATE1_LIVE_OPERATOR_ACK_DRAFT.md` (SIGNED DISCUSS_ONLY in place)
- `docs/planning/GATE1_LIVE_OPERATOR_ACK_SIGNED.md` (signed copy)
- `docs/planning/GEMINI_FREE_NEXT_STEPS.md`
- `docs/planning/LIVE_100_OPERATOR_WALL.md` · `docs/planning/LIVE_READINESS_CHECKLIST.md`
- `council/HOLD_POSTURE_AND_REOPEN_CONDITIONS.md`
- `council/COUNCIL_AGREEMENT_HOLD_STAY.md` (historical; operator superseded for discussion reopen)

## Explicit non-goals (this leave-Hold)

- `live=ENABLED` / flag flips / real provider traffic
- Keys in repo / CI
- Gate5 canary execution
- D3, push, tags, CP mint
- Claiming DISCUSS_ONLY = live-ready

## Later upgrade (same day) — ENABLE_UNDER_FENCES

**2026-09-28 ~19:41 ET:** Operator **「Aprobado」** signed `docs/planning/GATE1_ENABLE_UNDER_FENCES_ACK_SIGNED.md`.  
This leave-Hold note remains the **DISCUSS_ONLY reopen** record. Intent upgrade and ENABLE-ready seals are recorded in:

- `council/NOTE_ENABLE_UNDER_FENCES_SIGNED.md`
- `docs/planning/GATE2_ENABLE_READY.md` · `GATE3_ENABLE_READY.md` · `GATE4_ENABLE_READY.md`
- `docs/planning/GATE5_HEALTH_CHECK_EVIDENCE.md`

**Still true from leave-Hold:** no keys in git; NO_HELD unchanged; D3/push/tags no.  
**Updated:** intent is no longer DISCUSS_ONLY-only — ENABLE_UNDER_FENCES is signed; **`LIVE_API_ENABLED` still False** (Gate5 step 6 blocked on `impl_cp_not_authorized`).

*End NOTE_LEAVE_HOLD_GATE1_DISCUSS_ONLY — Hold A left; DISCUSS_ONLY record retained; see ENABLE signed note for intent upgrade.*

