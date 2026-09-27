# Mesh M3 WAN Model Design

**Capability:** `MESH_M3_WAN_MODEL_DESIGN`  
**Cycle / Checkpoint:** 56 / CP-0060  
**Version:** package **0.18.0** held  
**Status:** DESIGN ONLY  
**Scope:** WAN latency bands + jitter/loss + P_partition + HLC ordering + partition classes; no N>2 runtime; no Raft

## Gates

| Gate | Meaning |
|------|---------|
| Design present | `docs/design/fabric/M3_WAN_MODEL_DESIGN.md` |
| Bands | RTT_lo / RTT_mid / RTT_hi (+ RTT_x stress) |
| Classes | SPLIT / HEAL / FLIP_FLOP / CASCADE |
| HLC order | wall_clock_as_authority=0; compose mesh.clock.hlc/v1 |
| Helpers + neg tests | packaging `m3_wan_model` mocks |
| After M2 | ACTIVE actors from membership SM |
| M1 orthogonal | NO_CONSENSUS_YET unchanged |
| NO_HELD held | No Raft/N>2/multi-primary/GIA |

## Preferred next

`await_deepseek` (C56 M3 design sealed; SP ACK noted; bias next spike per SP4 after ACK)

## NO_HELD

**NO_HELD:** Raft,N>2,multi-primary,ML,R2,R3,plaintext,Vault-ACME-req,GIA,SLO_chase,tag_schema,EVERY_fsync
