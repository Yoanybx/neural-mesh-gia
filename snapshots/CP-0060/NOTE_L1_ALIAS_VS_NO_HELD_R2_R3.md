# NOTE — L1 display aliases vs NO_HELD product R2/R3 (SP2)

**Cycle / Checkpoint:** 56 / CP-0060  
**Authority:** DeepSeek C55 SP2 **ACK**  
**Scope:** Docs/blueprint **display alias only** — **no semantic change; no NO_HELD unlock**

## Problem

Blueprint **L1 REMAINING_0.17** historically labeled closed items **R1 / R2 / R3**
(fabric ops UX / OBS peers / external quickstart). The unlockable **NO_HELD**
list also contains product tracks **R2 / R3** (ML-router style). Same tokens,
different meanings → collision risk in STATUS/PASTE/council paste.

## Resolution (aliases)

| Historical L1 id | Display alias (preferred) | Evidence |
|------------------|---------------------------|----------|
| R1 | **L1-ops-UX** | CP-0033 / tip e1d5e50 |
| R2 | **L1-OBS-peers** | CP-0034 / tip 64747b9 |
| R3 | **L1-quickstart** | CP-0035 / tip e6a0964 |

Keep **R2 / R3** reserved in prose for **NO_HELD product ML tracks**.

## Explicit non-unlock

- NO_HELD product **R2 / R3** remain locked.
- No GIA / Raft / N>2 / train / SaaS motion.
- L1 remains **CLOSED** (CP-0056); this note only renames display labels.

## Touched

- `council/blueprint/FINAL_BLUEPRINT_ROOT.md`
- `council/blueprint/FINAL_BLUEPRINT_ROOT_READABLE.md`
- `council/blueprint/HUMAN_BLUEPRINT_ROOT.md`
- this note

**NO_HELD:** Raft,N>2,multi-primary,ML,R2,R3,plaintext,Vault-ACME-req,GIA,SLO_chase,tag_schema,EVERY_fsync
