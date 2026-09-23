# Mesh Packaging: Post-RC Watch

**Capability:** `MESH_PACKAGING_POST_RC_WATCH`  
**Cycle / Checkpoint:** 23 / CP-0027  
**Version:** 0.16.3  
**Scope:** single-node RC; peers=0

## Purpose

Lightweight **post-RC** watch harness (not a CI daemon). Run once after RC seal
to confirm freeze / debt / tag / OBS invariants remain intact.

## Watch checklist

| Check | Meaning |
|-------|---------|
| `manifest_freeze_intact` | `freeze.channel=0.16.x` + schema v1 on probe/build |
| `debt_schema_gated_unchanged` | `CHECKPOINT_EVERY_FLOOR` remains SCHEMA-GATED; no SLO chase |
| `no_tag_schema_drift` | `schema_gate_checkpoint_every_floor` + floor tag pattern present; no v2 tag schema |
| `snapshot_obs_fields_stable` | `mesh.status.snapshot/v1` OBS fields unchanged |

## CLI

```bash
.venv/bin/python scripts/post_rc_watch.py --once
.venv/bin/python scripts/post_rc_watch.py --once --json
```

Writes JSON under `dist/post_rc_watch/post_rc_watch_report.json` (and mirrors to
`.project_state/post_rc_watch_report.json` when possible).

## Scheduled routine (document only)

Future CI/cron may invoke `scripts/post_rc_watch.py --once`.
**Do NOT create Grok Bot routines** for this watch.

## NO_HELD

**NO_HELD:** Raft,N>2,multi-primary,ML,R2,R3,plaintext,Vault-ACME-req,GIA,SLO_chase,tag_schema,EVERY_fsync
