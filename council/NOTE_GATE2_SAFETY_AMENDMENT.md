# Operator note — Gate 2 live safety-case amendment

- **Date:** 2026-09-28 America/New_York (EDT) — refreshed at DESIGN_SEAL
- **Author:** Grok Bot `<grok-bot@local>` (Staff Eng — docs only; not an unlock)
- **Tip stack:** design seal atop peer wire `30fe593` · dry-run `1e502c6` · leave-Hold `fc4ef9e` · prior draft parent Gate5 `45ccc16`
- **Package posture:** **0.18.0 HELD** · **live=DISABLED** · **M1=NO_CONSENSUS_YET** (N=2) · **D3 NOT ACKed** · **MESH_PERF_EXPERIMENTAL=OFF** · pkg0190 **NOT_OPENED**
- **Gate 1:** **SIGNED DISCUSS_ONLY** (`docs/planning/GATE1_LIVE_OPERATOR_ACK_SIGNED.md`)
- **Gate 2 status:** **DESIGN_SEALED** (DISCUSS_ONLY / Gemini free eval) — `docs/planning/GATE2_DESIGN_SEALED.md`
- **Planning doc:** `docs/planning/GATE2_LIVE_SAFETY_CASE_AMENDMENT.md`
- **Checklist:** `docs/planning/LIVE_READINESS_CHECKLIST.md` Gate 2
- **CP minted:** **No** (docs-only; no flag flip)

## Operator / blueprint choice reflected

Serial step after Gemini dry-run peer wire: advance Gate2 live safety-case amendment toward seal. Honest outcome = **DESIGN_SEALED** for discuss/eval (not ENABLE). **Do not** enable live · **do not** mint keys into git · **do not** start D3 · **do not** push/tag · **do not** mint CP · **do not** invent ENABLE signature.

## What this is

Gate2 amendment covering: real transport blast radius; key compromise response; kill→RefuseTransport+ABORT; continuity under live peer failure; D1 vs live gaps; RV-1..RV-7 mock-green until live cycle. Now **bound** to dry-run evidence, peer wire, Authority Matrix, RefuseTransport, secret_handle.

## What this is not

- **Not** an ENABLE seal — needs user-written **ENABLE_UNDER_FENCES** ACK + Mesh live proof
- **Not** Gate5 canary / Mesh live adapter enable
- **Does not** flip `live_adapter.enabled` / `LIVE_API_ENABLED`
- Eval dry-run ≠ live RV proof

## Posture reaffirm

**live=DISABLED.** RefuseTransport default ON. No keys in repo. Gate1 **SIGNED DISCUSS_ONLY**. Gate2 **DESIGN_SEALED** (discuss/eval). **Next: Gate 3** design seal. Gates **3–6** still open before any enable flip.

## Related

- `docs/planning/GATE2_DESIGN_SEALED.md` · `council/NOTE_GATE2_DESIGN_SEALED.md`
- `docs/planning/GEMINI_FREE_NEXT_STEPS.md` · `council/NOTE_GEMINI_PEER_DRY_RUN_WIRE.md`
- `docs/planning/GATE1_LIVE_OPERATOR_ACK_SIGNED.md` · `council/NOTE_LEAVE_HOLD_GATE1_DISCUSS_ONLY.md`
- `docs/planning/GATE3_AUTHORITY_MATRIX_BINDING.md`
- `docs/planning/D1_L_JUDGE_SAFETY_CASE_MATURATION.md` (CP-0071)
- `council/COUNCIL_AGREEMENT_D4.md` (F4)
- `src/neural_mesh/packaging/l_judge_live_adapter_safety.py`
