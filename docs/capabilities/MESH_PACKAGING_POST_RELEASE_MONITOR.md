# Mesh Packaging: Post-Release Monitor

**Capability:** `MESH_PACKAGING_POST_RELEASE_MONITOR`  
**Cycle / Checkpoint:** 25 / CP-0029 (extends 24 / CP-0028)  
**Version:** 0.16.3  
**Scope:** single-node RC; peers=0

## Purpose

Lightweight **post-release** monitor (complements Cycle 23 `post_rc_watch`).
Run once after signoff / tag / archive to confirm release artifacts and
invariants remain intact. Cycle 25 adds **continue** mode for repeated
healthy checks with JSONL history.

## Monitor checklist

| Check | Meaning |
|-------|---------|
| `signoff_present` | `SIGNOFF.json` present and `ok` for 0.16.3 |
| `tag_or_archive_marker` | Local tag exists **or** TAG_MARKER / ARCHIVE_MANIFEST / release tar |
| `freeze_intact` | Manifest freeze `{channel:"0.16.x", schema:v1}` |
| `debt_schema_gated` | `CHECKPOINT_EVERY_FLOOR` remains SCHEMA-GATED; no SLO chase |
| `obs_stable_fields` | `mesh.status.snapshot/v1` OBS fields unchanged |
| `no_forbidden_drift` | No Raft/N>2/multi-primary/ML/plaintext/GIA/SLO_chase/tag v2 drift; NO_HELD documented |

## CLI

```bash
.venv/bin/python scripts/post_release_monitor.py --once
.venv/bin/python scripts/post_release_monitor.py --once --json
.venv/bin/python scripts/post_release_monitor.py --continue
.venv/bin/python scripts/post_release_monitor.py --continue --json
```

Writes `dist/releases/0.16.3/MONITOR.json`.  
Continue mode also appends `dist/releases/0.16.3/monitor_history.jsonl`
(rolls at 500 entries). Exits 0 if still healthy; fails if signoff/archive
missing or other checklist gates fail.

## Scheduled routine (document only)

Future CI/cron may invoke `scripts/post_release_monitor.py --once` or
`--continue`. **Do NOT create Grok Bot routines** for this monitor.

## Related

- **P17** `post_rc_watch` — pre-signoff RC watch checklist
- **P18** `release_signoff` — SIGNOFF.json
- **P19** `release_tag_archive` — tag + archive under `dist/releases/0.16.3/`
- **P21** continue mode + history JSONL (CP-0029)
- **P23** `debt_gate_review` — SCHEMA-GATED consistency (CP-0029)

## NO_HELD

**NO_HELD:** Raft,N>2,multi-primary,ML,R2,R3,plaintext,Vault-ACME-req,GIA,SLO_chase,tag_schema,EVERY_fsync
