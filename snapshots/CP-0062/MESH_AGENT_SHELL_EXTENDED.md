# Mesh Agent-Shell Extended Scenarios (Mock)

**Capability:** `MESH_AGENT_SHELL_EXTENDED`  
**Cycle / Checkpoint:** 58 / CP-0062  
**Version:** package **0.18.0** held  
**Status:** SPIKE EXECUTED (mock-only; live=DISABLED)  
**Scope:** Extend CP-0053 shell spike — multi-turn, probe matrix, ABORT variants, receipt chain under M2 churn; optional L_judge compose

## Gates

| Gate | Meaning |
|------|---------|
| Design note | `docs/design/AGENT_SHELL_EXTENDED_SCENARIOS.md` |
| Packaging helpers | `agent_shell_extended` |
| Multi-turn | bounded tool_call/tool_result loops |
| Probe matrix | schema/fence/audit/tool/policy/max_steps/NO_DRY_RUN |
| Churn | DRAINING / LEFT / REJOIN cancel + chain verify |
| Neg tests | T-shell-a / T-shell-b / T-shell-c |
| live | DISABLED (no keys, no WAN, no frontier) |
| NO_HELD held | No Raft/N>2/multi-primary/GIA/train/SaaS/settlement |

## Preferred next

`0.19_design_set_signoff_v2` (DeepSeek C57: after Option1, likely Option2 to close design+spike window)

## NO_HELD

**NO_HELD:** Raft,N>2,multi-primary,ML,R2,R3,plaintext,Vault-ACME-req,GIA,SLO_chase,tag_schema,EVERY_fsync
