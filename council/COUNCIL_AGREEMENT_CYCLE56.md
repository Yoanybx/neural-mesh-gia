# Council Agreement — Cycle 56 / CP-0060

**Capability:** M3_WAN_model_DESIGN  
**Scope:** Design-only WAN latency bands + jitter/loss + P_partition + HLC ordering + partition classes (SPLIT/HEAL/FLIP_FLOP/CASCADE); after M2; mock helpers + negative tests; no N>2 runtime; no Raft  
**Version:** 0.18.0 HELD  
**Checkpoint:** CP-0060  
**Authority:** DeepSeek C55 Preferred NEXT (`M3_WAN_model_DESIGN`) + SP1/SP2 ACK; SP3 ACK_WITH_FENCE; SP4 ACK_WITH_CAVEAT (M3 design-first)

## Deliverables

- docs/design/fabric/M3_WAN_MODEL_DESIGN.md
- docs/schema/wan/v0.md
- MESH_M3_WAN_MODEL_DESIGN
- packaging m3_wan_model helpers + neg tests T-M3a/T-M3b
- pointer updated; CP-0060 VERIFIED
- SP2 L1 display aliases (L1-ops-UX / L1-OBS-peers / L1-quickstart) + NOTE
- PASTE with SP ACK status + SP3 fence
- PREFERRED_NEXT=`await_deepseek`

## SP ACK (from DeepSeek C55)

| SP | Verdict | Fence / caveat |
|----|---------|----------------|
| SP1 LAST_SEALED | ACK | include in every STATUS |
| SP2 L1 alias vs NO_HELD R2/R3 | ACK | alias only; no unlock |
| SP3 batch STATUS 2–3 cycles | ACK_WITH_FENCE | only if no ABORT, no NO_HELD boundary, no live=ENABLED, no package tag open, no new NO_HELD proposal |
| SP4 empirical spike bias | ACK_WITH_CAVEAT | M3 design-first (cannot spike real WAN without N>2); safety-case ahead of live=ENABLED |

## Exclusions

**NO_HELD** unchanged. No GIA/Raft/N>2/train/SaaS. v0.18.0 untouched.
