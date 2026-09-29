# NOTE — CP-0080 F4 design + M-KILL-2 / M-ABORT-3 (2026-09-28)

**Audience:** Operator / council  
**Tip base:** `c2ba1e2` → this commit  
**Author:** Grok Bot `<grok-bot@local>`

## Done

- **F4** product-enable safety amendment **DESIGN_SEALED**; product ACK **UNSIGNED** (ENABLE_UNDER_FENCES ≠ permanent module True; no invented operator words).
- **M-KILL-2** ops budget sealed: kill→refuse **≤100 ms** process-local; pack/unit drill PASS.
- **M-ABORT-3** E-CONFLICT (conflicting + missing judges) fail-closed drill PASS.
- Module **`LIVE_API_ENABLED=False`** retained.

## Honest 「listo」

| Track | Status |
|-------|--------|
| Fenced Mesh canary / measurement path | **Listo bajo fences** (ENABLE signed · Gates 2–4 ready · CP-0075..0080 drills · multi-canary n=6 · policy default-off) |
| Product permanent LIVE (module True) | **NOT listo** — F4 product ACK still **UNSIGNED**; prefer leave False |
| Streaming / Vertex paid / NO_HELD | Still out |

## Non-goals held

No push/tags/secrets · NO_HELD unchanged · no invented F4 signature · no permanent LIVE flip.
