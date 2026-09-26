# M2 Membership + Rejoin — Design Pointer Only

**Status:** POINTER (no SM runtime)  
**Cycle:** 46 / CP-0050  
**Target RFC (later):** `rfc/0002-membership.md`

## Proposed states (blueprint)

`JOINING → ACTIVE → DRAINING → LEFT → REJOIN`

## Tests (future, not now)

- T-M2a rejoin_state_machine
- T-M2b drain_no_loss

## Non-goals

No N>2 runtime; no Raft; dual_primary=0 held. **NO_HELD** unchanged.
