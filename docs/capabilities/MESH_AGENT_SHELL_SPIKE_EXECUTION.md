# Mesh Agent-Shell Spike Execution

**Capability:** `MESH_AGENT_SHELL_SPIKE_EXECUTION`  
**Cycle / Checkpoint:** 49 / CP-0053  
**Version:** 0.18.0 HELD  
**Scope:** in-process mock adapter spike; hash-chained receipts; ABORT paths; no settlement

## Gates

| Gate | Meaning |
|------|---------|
| `execution_doc` | AGENT_SHELL_SPIKE_EXECUTION.md |
| `pipeline` | workload → normalize → probes → receipts → reports |
| `abort_paths` | schema/fence/policy/tool/audit covered |
| `receipt_chain` | hash-chained ShellReceipt |
| `mock_ok` | no live API keys / no vendor shell |
| `no_economy` | settlement/reputation still non-goal |
| `no_src_runtime` | no src/shell_*.py |
| `no_held` | NO_HELD unchanged |

## Preferred next

`M1_scorecard_maturation` (candidate selection or written no-consensus-yet; still no Raft default)

## NO_HELD

**NO_HELD:** Raft,N>2,multi-primary,ML,R2,R3,plaintext,Vault-ACME-req,GIA,SLO_chase,tag_schema,EVERY_fsync
