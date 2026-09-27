# Mesh L_judge Live-Adapter Design

**Capability:** `MESH_L_JUDGE_LIVE_ADAPTER_DESIGN`  
**Cycle / Checkpoint:** 53 / CP-0057  
**Version:** package **0.18.0** held  
**Status:** DESIGN ONLY  
**Scope:** Live-adapter plug-in boundary; no live API; no keys; no src codec

## Gates

| Gate | Meaning |
|------|---------|
| Design doc present | `docs/design/L_JUDGE_LIVE_ADAPTER_DESIGN.md` |
| Extends integration | References CP-0052 port + parse/ABORT |
| Secret-handle only | No raw keys in design samples |
| Live default off | `enabled=false` / RefuseTransport |
| NO_HELD held | No ML/GIA/Raft/N>2 unlock |

## Preferred next

`await_deepseek` (C52–C53 verdict)

## NO_HELD

**NO_HELD:** Raft,N>2,multi-primary,ML,R2,R3,plaintext,Vault-ACME-req,GIA,SLO_chase,tag_schema,EVERY_fsync
