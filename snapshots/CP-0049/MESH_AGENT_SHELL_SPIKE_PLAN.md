# Mesh Agent-Shell Adapter Spike Plan

**Capability:** `MESH_AGENT_SHELL_SPIKE_PLAN`  
**Cycle / Checkpoint:** 45 / CP-0049  
**Version:** 0.18.0 HELD  
**Scope:** docs/design spike plan only

## Gates

| Gate | Meaning |
|------|---------|
| `spike_doc` | AGENT_SHELL_ADAPTER_SPIKE.md present with shapes + probes |
| `boundary` | Mesh=policy/OBS; shell=client documented |
| `no_economy` | settlement/reputation explicitly non-goal |
| `no_held` | NO_HELD unchanged |
| `version_held` | 0.18.0 |

## Preferred next

`M1_consensus_choice_design` (design-only scorecard; no Raft default)

## NO_HELD

**NO_HELD:** Raft,N>2,multi-primary,ML,R2,R3,plaintext,Vault-ACME-req,GIA,SLO_chase,tag_schema,EVERY_fsync
