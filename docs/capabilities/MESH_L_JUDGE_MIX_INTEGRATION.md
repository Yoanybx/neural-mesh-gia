# Mesh L_judge MIX Integration

**Capability:** `MESH_L_JUDGE_MIX_INTEGRATION`  
**Cycle / Checkpoint:** 48 / CP-0052  
**Version:** 0.18.0 HELD  
**Scope:** integration design + mock-tested contract; no live engine; no runtime codec in src/

## Gates

| Gate | Meaning |
|------|---------|
| `integration_doc` | docs/design/L_JUDGE_MIX_INTEGRATION.md |
| `injection_stub` | docs/schema/judge/injection_v0.md |
| `mock_judge` | in-test MockLJudgePort (no API keys) |
| `abort_paths` | schema / fence / dry_run gate covered |
| `receipt_chain` | hash-chained receipt fields specified + mock |
| `no_runtime_codec` | no src/ judge_*.py |
| `no_held` | NO_HELD unchanged |

## Preferred next

`agent_shell_spike_execution` (bounded workload → probes → receipts → reports; mock OK)

## NO_HELD

**NO_HELD:** Raft,N>2,multi-primary,ML,R2,R3,plaintext,Vault-ACME-req,GIA,SLO_chase,tag_schema,EVERY_fsync
