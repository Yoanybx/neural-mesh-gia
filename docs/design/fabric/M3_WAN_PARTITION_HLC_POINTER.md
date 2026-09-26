# M3 WAN Latency / Partition + HLC — Design Pointer Only

**Status:** POINTER (no WAN runtime)  
**Cycle:** 46 / CP-0050  
**Target doc (later):** `docs/wan/partition-v1.md` (+ latency bands)

## Required

- RTT / loss / heal window classes (ratifiable defaults later)
- **HLC required** for cross-site event ordering notes
- Partition matrix tests T-M3a/b are future — not this CP

## Non-goals

No world-scale deployment claim; no N>2; no Raft. **NO_HELD** unchanged.
