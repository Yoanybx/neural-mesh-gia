# Council Agreement — Gates 2–6 Design-Seal Hygiene (LOCKED)

**Status:** LOCKED — dual ACK (DeepSeek + ChatGPT), hygiene only
**Date:** 2026-09-28 America/New_York (EDT)
**Author:** Grok Bot `<grok-bot@local>`
**Tip lineage:** `bcba248` / `59d4178`
**Topic:** `DESIGN_SEAL_GATES_2_6_HYGIENE_ONLY`
**ENABLE:** was draft UNSIGNED at hygiene lock; **later SIGNED** — see postscript

## Agreement

1. Gates 2–6 are **DESIGN_SEALED** for `DISCUSS_ONLY`/evaluation hygiene only.
2. Gate5 is procedure-only; its canary is **NOT AUTHORIZED**.
3. Gate6 is metrics-only; it does not authorize live measurement.
4. `live=DISABLED`; `LIVE_API_ENABLED=False`; the live adapter remains disabled.
5. Dry-run evidence remains evidence-only and is not live RV.
6. The ENABLE draft remains **UNSIGNED**; only the operator may provide the separate ENABLE signature.
7. No flag flip, Gate5 canary, live measurement, or treatment of design seals as live authorization is permitted by this agreement.

## Dual ACK

| Voice | Verdict | Confidence / scope |
|-------|---------|--------------------|
| **DeepSeek** | **ACK** | Design-seal hygiene only; no live authorization |
| **ChatGPT** | **ACK** | **HIGH** confidence; design-seal hygiene only |

**Hygiene:** **PASS.** The dual ACK confirms documentation hygiene and does not upgrade intent or authorize live operation.

**Honest wall:** The remaining wall is the operator ENABLE signature; the ENABLE draft is still unsigned.

## Explicit non-actions

- Do not flip `LIVE_API_ENABLED` or enable the live adapter.
- Do not execute the Gate5 canary.
- Do not treat the Gates 2–6 design seals as live authorization.

## Postscript — ENABLE signed (same day; does not rewrite hygiene ACK)

**2026-09-28 ~19:41 ET:** Operator signed ENABLE_UNDER_FENCES (`GATE1_ENABLE_UNDER_FENCES_ACK_SIGNED.md`, 「Aprobado」).  
Dual hygiene ACK above remains **PASS / hygiene-only** — it did **not** authorize the ENABLE; the operator signature did.

| Item | After postscript |
|------|------------------|
| Hygiene ACK | Still PASS (unchanged meaning) |
| ENABLE | **SIGNED** |
| Gates 2–4 ENABLE_READY | Docs sealed same cycle |
| `LIVE_API_ENABLED` | **Still False** — Gate5 step (6) blocked on `impl_cp_not_authorized` |
| Canary | **Not executed** |
| NO_HELD | Unchanged |

Cite: `council/NOTE_ENABLE_UNDER_FENCES_SIGNED.md` · `docs/planning/GATE5_HEALTH_CHECK_EVIDENCE.md`

*End COUNCIL_AGREEMENT_DESIGN_SEAL_GATES_2_6 — locked hygiene record; ENABLE later signed by operator; LIVE_API_ENABLED still False.*

