# Agent-Shell Adapter Spike — Execution

**Status:** SPIKE EXECUTED (in-process mock; no live shell vendor; no settlement)  
**Cycle / Checkpoint:** 49 / CP-0053  
**Date:** 2026-09-26 America/New_York (EDT)  
**Plan:** `docs/design/AGENT_SHELL_ADAPTER_SPIKE.md` (CP-0049)  
**Non-claim:** Shell ≠ policy brain. DO_NOT_TRAIN_70B_NOW. L_GIA = NO_HELD.

---

## 1. Intent

Execute the bounded spike pipeline with an **in-process fake shell** + Mesh adapter
mock (no OpenJarvis vendor, no API keys required):

```
bounded workload → normalized output → safety probes → [optional L_judge dry_run]
  → hash-chained receipts → reports
```

Mesh remains policy/OBS/ABORT authority. Shell remains client.

---

## 2. What this CP demonstrates

| Step | Artifact | Gate |
|------|----------|------|
| Ingress | `ShellWorkload` (`mesh.shell.workload/v0`) | schema + idempotency + bounds |
| Normalize | `NormalizedEvent[]` (`mesh.shell.event/v0`) | type enum; payload digests |
| Probes | schema / dual_primary==0 / forbid_side_effects / tool_allowlist / audit | fail → ABORT |
| Judge (opt) | Mock L_judge MIX dry_run under Mesh | never shell-direct frontier call |
| Receipt | `ShellReceipt` hash-chained + OBS id + evidence id | `dual_primary: 0` |
| Report | `ShellReport` to shell | ACCEPT / REJECT / ABORT + digests |

Implementation locus this cycle: **`tests/test_agent_shell_spike_execution_cycle49.py`**
(`MockAgentShellAdapter`). No `src/neural_mesh/shell_*.py` runtime module yet.

---

## 3. ABORT paths (tested)

| Code | Trigger |
|------|---------|
| `SCHEMA_INVALID` | bad workload/event schema or missing ids |
| `FENCE` | `dual_primary != 0` |
| `POLICY` | `forbid_side_effects` violated / bounds exceeded |
| `TOOL_DENIED` | tool not on allowlist |
| `NO_AUDIT` | audit sink unavailable |
| `NO_DRY_RUN` | live judge path without prior dry_run (when judge enabled) |

Never silent ACCEPT on probe failure.

---

## 4. Receipt chaining

`receipt_id = rcpt:<hash16(request_digest, probe_digest, prev_receipt_hash)>`.  
`prev_receipt_hash` links prior shell receipts for reconstructibility.  
OBS + evidence entry ids emitted on every finalize (including ABORT).

---

## 5. Explicit non-goals (held)

- Settlement / IOU / tokenless economy / market reputation  
- SaaS multi-tenant / live OpenJarvis vendor fork  
- Raft / N>2 / multi-primary / GIA / train-70B  
- Shell overriding Mesh policy  

**NO_HELD:** Raft,N>2,multi-primary,ML,R2,R3,plaintext,Vault-ACME-req,GIA,SLO_chase,tag_schema,EVERY_fsync

---

## 6. Related

- `docs/design/AGENT_SHELL_ADAPTER_SPIKE.md`
- `docs/design/L_JUDGE_MIX_INTEGRATION.md`
- `docs/schema/shell/v0.md`
- `docs/capabilities/MESH_AGENT_SHELL_SPIKE_EXECUTION.md`
