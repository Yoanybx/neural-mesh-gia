# NOTE — CP-0087 Phase R5 F4 product-enable ACK SIGNED + LIVE flip

- **Date:** 2026-09-28 ~23:26 EDT (America/New_York)
- **Author:** Grok Bot `<grok-bot@local>`
- **Tip base:** `c64c0e0` (CP-0086 Gate6 live-measurement SEALED)
- **CP:** **CP-0087** — R5 seal (docs + product flip)
- **Authority:** Operator chat **「Firmalo por mi」** (~23:22 ET) · follow-up **「Ponlo live y seguimos」**

## What landed

| Item | Path / result |
|------|----------------|
| F4 ACK SIGNED | `docs/planning/F4_PRODUCT_ENABLE_ACK_SIGNED.md` |
| Draft historical | `docs/planning/F4_PRODUCT_ENABLE_ACK_DRAFT.md` |
| CP seal | `docs/planning/IMPL_CP_0087_F4_PRODUCT_ENABLE_R5.md` |
| Product modules | `LIVE_API_ENABLED=True` (peer / canary / LHT / multi-canary / R1–R4 / Gate6 incr) |
| Enablement lift | `live_adapter.enabled=true` authorized under F4 (no longer refusal) |

## Policy (español-friendly)

- Firmado F4 con 「Firmalo por mi」; flip con 「Ponlo live y seguimos」
- Producto LIVE **True** bajo fences (Gemini free, env local ACK’d)
- I5 / RefuseTransport siguen mandando la red si no armados
- Streaming **OUT**; Vertex **OUT**; **NO_HELD** sin cambio
- R5 **DONE**; P7 **SIGNED**

## Fences held

- No secrets in git · no push/tags · no Vertex/streaming/NO_HELD  
- Kill/rollback owner: Joan / Yoan V  
- Advisory ≠ Mesh SoT / M1  

## Honest 「listo」

| Track | Status |
|-------|--------|
| Bajo fences | **YES** |
| Full-adapter RV R0–R5 | **DONE** (streaming DEFER) |
| Product permanent | **YES** — module True + ACK SIGNED |

**Next:** product soak checklist · optional council STATUS a DeepSeek · seguir trabajo honesto de ingeniería.
