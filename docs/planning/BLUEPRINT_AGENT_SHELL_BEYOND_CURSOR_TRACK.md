# Blueprint — Mesh Beyond Cursor agent-shell track

**Status:** `DESIGN_ONLY` · aspirational product intent · no runtime/code unlock
**Date:** 2026-09-28 America/New_York (EDT)
**Owner:** Grok Bot
**Pointer:** `council/NORTH_STAR_RECALIBRATION.md`

## Intent

The product bar is **better than Cursor**, not “a Cursor clone” or merely
“tipo Cursor”: Mesh should combine an agent-shell surface with Mesh-owned
orchestration, audit/ledger, refusal, and bounded tool execution. This is a
north-star track, not a claim that Mesh currently equals or exceeds Cursor.

## Staged track

### Near — MCP-lite tool-bus + free L_judge peers

- Design an MCP-lite, capability-allowlisted tool bus with normalized calls,
  receipts, and fail-closed refusal.
- Route Gemini Free and DeepSeek Free L_judge work through the existing F4 LIVE
  boundary/authorization; judge output remains advisory and never becomes Mesh
  SoT, consensus, or an unlogged action.
- Keep provider quotas, I5/kill/abort controls, audit sinks, and secrets
  handling unchanged. **No new live flag, key, or provider permission is minted.**

### Mid — agent-shell UX

- Design a “beyond Cursor” surface: orchestrated tools, visible ledger,
  receipts, human oversight, and explicit refuse/abort states.
- Mesh owns policy, orchestration, audit/ledger, and refusal; the shell owns the
  interaction surface and bounded presentation. Do not claim a Cursor clone.
- Prefer the existing shell adapter concepts; any implementation needs a
  separately authorized CP and evidence.

### Far — GIA / self-building agent

- GIA, self-building behavior, self-modification, and an autonomous self-mod
  loop remain **NO_HELD**.
- Opening this layer requires council decision plus evidence bundle and the
  existing governance gates. This document is not an opening, design approval,
  or prose unlock.

## Honest fences / límites honestos

- **No code changes or runtime unlocks** are implied by this track.
- **LIVE stays as-is** under the current F4 product posture; this doc does not
  widen LIVE, CI networking, paid providers, streaming, or tool permissions.
- No GIA/AGI/consciousness claim, no training claim, no Raft/N>2 claim, and no
  self-modifying loop.
- Spanish-friendly summary: **Cerca:** bus MCP-lite + jueces gratis bajo F4;
  **medio:** UX de shell con orquestación, ledger y refuse; **lejos:** GIA y
  agente que se construye solo, todavía `NO_HELD` hasta consejo + evidencia.

## Related boundaries

- `docs/design/AGENT_SHELL_ADAPTER_SPIKE.md`
- `docs/design/AGENT_SHELL_EXTENDED_SCENARIOS.md`
- `docs/planning/F4_PRODUCT_ENABLE_ACK_SIGNED.md`
- `docs/planning/LIVE_100_OPERATOR_WALL.md`
