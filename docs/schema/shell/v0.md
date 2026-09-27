# Schema: mesh.shell.*/v0 (STUB + spike execution)

**Status:** STUB (Cycle 47 / CP-0051) · spike exercised Cycle 49 / CP-0053  
**Design:** `docs/design/AGENT_SHELL_ADAPTER_SPIKE.md` · `docs/design/AGENT_SHELL_SPIKE_EXECUTION.md`

## Types

| Schema | Type | Notes |
|--------|------|-------|
| `mesh.shell.workload/v0` | ShellWorkload | bounds, tool_allowlist, forbid_side_effects |
| `mesh.shell.event/v0` | NormalizedEvent | step_start\|tool_call\|tool_result\|final\|error |
| `mesh.shell.receipt/v0` | ShellReceipt | hash-chained; probe_results[]; dual_primary=0 |
| `mesh.shell.report/v0` | ShellReport | ACCEPT\|REJECT\|ABORT + abort code/reason |

Mesh = policy/OBS; shell = client. No settlement / economy / reputation rails.

## ABORT codes (spike)

SCHEMA_INVALID · FENCE · POLICY · TOOL_DENIED · NO_AUDIT · NO_DRY_RUN

**NO_HELD:** Raft,N>2,multi-primary,ML,R2,R3,plaintext,Vault-ACME-req,GIA,SLO_chase,tag_schema,EVERY_fsync
