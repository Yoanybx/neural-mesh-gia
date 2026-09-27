# M2 Membership + Rejoin — Design Pointer

**Status:** SUPERSEDED by design doc (stub retained)  
**Cycle:** 46 / CP-0050 (pointer); **55 / CP-0059 (design matured)**  
**Design:** `docs/design/fabric/M2_MEMBERSHIP_REJOIN_DESIGN.md`  
**Target RFC (later):** `rfc/0002-membership.md`

## Proposed states (canonical — CP-0059)

`JOINING → ATTESTING → ACTIVE → DRAINING → LEFT → REJOIN`

(ATTESTING added vs original blueprint five-name sketch to compose with H1.)

## Tests (mock in CP-0059; runtime later)

- T-M2a rejoin_state_machine (+ neg)
- T-M2b drain_no_loss (+ neg)

## Non-goals

No N>2 runtime; no Raft; dual_primary=0 held. **NO_HELD** unchanged.
