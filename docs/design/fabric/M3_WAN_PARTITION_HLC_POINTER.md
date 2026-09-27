# M3 WAN Latency / Partition + HLC — Design Pointer

**Status:** SUPERSEDED by design doc (stub retained)  
**Cycle:** 46 / CP-0050 (pointer); **56 / CP-0060 (design matured)**  
**Design:** `docs/design/fabric/M3_WAN_MODEL_DESIGN.md`  
**Target docs (later):** `docs/wan/partition-v1.md`, `docs/wan/latency-bands-v1.md`

## Required (now in design)

- RTT bands `RTT_lo` / `RTT_mid` / `RTT_hi` (+ `RTT_x` stress)
- Jitter / loss envelopes; heal windows; `P_partition`
- **HLC required** for cross-site event ordering (`wall_clock_as_authority=0`)
- Partition classes: split / heal / flip-flop / cascade
- Mock tests T-M3a/T-M3b (+neg) in CP-0060; runtime matrix later (M4 NO_HELD)

## Non-goals

No world-scale deployment claim; no N>2; no Raft. **NO_HELD** unchanged.
