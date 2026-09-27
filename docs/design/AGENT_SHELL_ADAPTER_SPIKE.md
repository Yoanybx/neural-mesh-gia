# Agent-Shell Adapter Spike Plan — Design (docs only)

**Status:** SPIKE PLAN DRAFT → **EXECUTED @ CP-0053**  
**Cycle / Checkpoint:** 45 / CP-0049 (plan); 49 / CP-0053 (execution)  
**Date:** 2026-09-26 America/New_York (EDT)  
**Theme:** (C) from `0.19_SCOPE_FROZEN`  
**Authority:** `COUNCIL_AGREEMENT_HYPERBRAIN_ASTRA` RANKED #2  
**Related:** `NOTE_JARVIS_GITHUB_CANDIDATES.md` · `L_JUDGE_MIX_DESIGN.md` · `DURABLE_GOALS_CONTINUITY_DESIGN.md`

---

## 1. Intent

Plan a **bounded** adapter spike that treats an external agent shell (e.g. OpenJarvis
or similar) as a **client** of Mesh policy/OBS — not a second policy brain.

Pipeline:

```
bounded workload → normalized output → safety probes → receipts → reports
```

Mesh owns: policy evaluate, ABORT, OBS, receipts, goal/continuity hooks.  
Shell owns: agent loop, UI/voice/HUD, local tool execution surface.

## 2. Ownership boundary (hard)

| Concern | Owner | Must NOT |
|---------|-------|----------|
| Policy / fence / ABORT | Mesh | Shell inventing override |
| OBS + receipts | Mesh | Shell-only unaudited acts |
| Goal registry / continuity | Mesh substrate | Shell diary as SoT |
| L_judge MIX calls | Mesh adapter | Shell calling frontier APIs without Mesh gate |
| Agent loop / tool UX | Shell | Mesh becoming a chat UI |
| Settlement / reputation market | **PARKED** | Either side |

## 3. Spike scope (what “done” means for a later impl CP)

Docs-only this cycle. Later impl (still NO_HELD-safe) should demonstrate:

1. **Ingress:** Shell submits `ShellWorkload` with idempotency key + goal_id.
2. **Normalize:** Adapter maps shell events → `NormalizedEvent` schema.
3. **Probes:** Mesh runs safety probes (schema, policy dry-run, dual_primary==0).
4. **Judge (optional):** May call L_judge MIX dry_run/advisory under Mesh.
5. **Receipt:** Emit `ShellReceipt` + OBS event; append evidence for goal.
6. **Report:** Return `ShellReport` to shell (ACCEPT/REJECT/ABORT + digests).

Explicitly **out of spike:** payment rails, multi-tenant SaaS, Raft, N>2,
training, GIA claims, shell replacing Mesh policy.

## 4. Data shapes

### 4.1 `ShellWorkload`

```json
{
  "schema": "mesh.shell.workload/v0",
  "workload_id": "wl:<uuid>",
  "idempotency_key": "string",
  "goal_id": "goal:<hash16>|null",
  "shell": {"name": "openjarvis|peer", "version_hint": "string"},
  "bounds": {
    "max_steps": 8,
    "max_wall_ms": 60000,
    "forbid_side_effects": true,
    "tool_allowlist": ["read_only_tools_only"]
  },
  "payload": {"kind": "task_text|structured", "digest": "sha256:..."}
}
```

### 4.2 `NormalizedEvent`

```json
{
  "schema": "mesh.shell.event/v0",
  "event_id": "sev:<uuid>",
  "workload_id": "wl:<uuid>",
  "type": "step_start|tool_call|tool_result|final|error",
  "payload_digest": "sha256:...",
  "ts_hlc": "..."
}
```

### 4.3 `ShellReceipt` / `ShellReport`

```json
{
  "schema": "mesh.shell.receipt/v0",
  "receipt_id": "rcpt:<hash16>",
  "workload_id": "wl:<uuid>",
  "verdict": "ACCEPT|REJECT|ABORT",
  "probe_results": [{"name": "schema|policy_dry_run|dual_primary", "ok": true}],
  "judge_receipt_id": "rcpt:...|null",
  "obs_event_id": "obs:...",
  "prev_receipt_hash": "sha256:...|null",
  "dual_primary": 0
}
```

```json
{
  "schema": "mesh.shell.report/v0",
  "workload_id": "wl:<uuid>",
  "verdict": "ACCEPT|REJECT|ABORT",
  "receipt_id": "rcpt:<hash16>",
  "summary_digest": "sha256:...",
  "abort": {"code": null, "reason": null}
}
```

### 4.4 Adapter API (pseudocode)

```text
class AgentShellAdapter:
    def submit(self, wl: ShellWorkload) -> ShellReport
    def ingest_event(self, ev: NormalizedEvent) -> Ack
    def finalize(self, workload_id: str) -> ShellReport
```

## 5. Safety probes (minimum set)

| Probe | Fail → |
|-------|--------|
| Schema valid | ABORT SCHEMA_INVALID |
| dual_primary == 0 | ABORT FENCE |
| forbid_side_effects honored | ABORT POLICY |
| tool_allowlist | ABORT TOOL_DENIED |
| dry_run before any live advisory judge | ABORT NO_DRY_RUN |
| audit sink available | ABORT NO_AUDIT |

## 6. Candidate shells (reference only)

From `council/NOTE_JARVIS_GITHUB_CANDIDATES.md`:

- **OpenJarvis** — strongest framework fit; boundary-setting critical.
- **eadmin2/jarvis_ai** — operator HUD/approvals surface.
- Others — voice ingress / experimental only.

Spike does **not** vendor or fork them this cycle.

## 7. Non-goals

- Settlement, IOU, tokenless economy, market reputation
- SaaS multi-tenant productization
- Shell-as-policy-brain / Mesh-as-chat-UI swap
- Raft / N>2 / multi-primary / GIA unlock / train 70B
- Claiming Astra-beating multimodal UX

**NO_HELD:** Raft,N>2,multi-primary,ML,R2,R3,plaintext,Vault-ACME-req,GIA,SLO_chase,tag_schema,EVERY_fsync

## 8. Suggested later CP sequence (not opened here)

1. Schema stubs under `schema/shell/v0` (docs/json only)
2. In-process fake shell → adapter dry-run tests **(DONE CP-0053)**
3. Optional OpenJarvis stub client behind feature flag
4. Wire goal_id + continuity resume_token
5. Never: settlement, GIA, N>2

## Related

- `docs/design/AGENT_SHELL_SPIKE_EXECUTION.md` (CP-0053)
- `docs/planning/0.19_SCOPE_FROZEN.md`
- `docs/design/L_JUDGE_MIX_DESIGN.md`
- `docs/design/DURABLE_GOALS_CONTINUITY_DESIGN.md`
- `council/NOTE_JARVIS_GITHUB_CANDIDATES.md`
