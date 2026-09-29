# NOTE — IMPL CP-0078 LiveHttpTransport v0 (authorized)

- **Date:** 2026-09-28 ~22:35 EDT (America/New_York)
- **Author:** Grok Bot `<grok-bot@local>`
- **Tip base:** `46858e1` (CP-0077)
- **CP:** **CP-0078** — **AUTHORIZED IMPL** of CP-0076 residual (not permanent LIVE enable)

## Decision

Mint **CP-0078** authorizing packaging `LiveHttpTransport` v0 for Gemini free under ENABLE_UNDER_FENCES:

- Unary codec + retries/backoff/idempotency/timeouts/taxonomy/ABORT hooks
- Wire behind runtime LIVE + I5; RefuseTransport when live off
- `src_live_codec_shipped=true`; module **`LIVE_API_ENABLED=False`**
- Unit/negative T-lht-* tests; may_enable fail-closed without auth
- Do **not** break CP-0075 canary; do **not** permanently enable live

## Residual toward 「listo」

Multi-canary pack **n≥N_min=5** (CP-0077) · permanent enable policy/runbook · F4 if product-enable · streaming still out.

## Claim hygiene (I-11)

**Authorize ≠ activate.** CP-0078 authorize = merge LiveHttpTransport **v0 default-off**; does **NOT** activate live / flip module True / satisfy F4.

## Fences

No secrets · no push/tags · **NO_HELD unchanged** · advisory ≠ SoT · n=1 ≠ seal
