# NOTE — CP-0087 residual (post F4 SIGNED + LIVE flip)

- **Date:** 2026-09-28 ~23:28 EDT
- **Tip base at sign:** `c64c0e0`
- **Done:** F4 `F4_PRODUCT_ENABLE_ACK_SIGNED.md` (「Firmalo por mi」) · product-path `LIVE_API_ENABLED=True` · `live_adapter.enabled` enablement lift · IMPL/NOTE CP-0087
- **Residual:** ~12 unit tests still assert pre-F4 “module/session False” hygiene (R1 kill restore, R2 suite, R3/Gate6 `live_final`, peer dry-run `live_api_enabled` report, multi-canary restore name, M-ABORT-3 conflict ok under product runtime_live OR). **I5 still gates network**; no secrets/push/NO_HELD.
- **Next engineer:** retarget those asserts to session_live / I5-not-armed / F4 module True; do not revert product flip.
