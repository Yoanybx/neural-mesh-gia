# Mesh Packaging: Final Release Audit

**Capability:** `MESH_PACKAGING_FINAL_RELEASE_AUDIT`  
**Cycle / Checkpoint:** 23 / CP-0027  
**Version:** 0.16.3  
**Scope:** `capability_not_tags_not_SLO` (single-node RC packaging)  
**Schema:** `mesh.bundle.manifest/v1` (**FROZEN** for 0.16.x)

## Purpose

Aggregate gate before calling the single-node RC **release-ready**. Composes
prior packaging gates (P9–P14) with Cycle 23 soak / watch context.

Complements:

- **P15** `rc_soak` — deterministic multi-iteration install/status/verify soak
- **P17** `post_rc_watch` — lightweight post-RC checklist (`--once`)

## Gates

| Gate | Meaning |
|------|---------|
| `version_match` / `version_0163` | `pyproject` + `__init__` agree; equals **0.16.3** |
| `cp_tip_verified` / `cp_tip_present` | Checkpoint tip present (CP-0027) |
| `freeze_present` / `freeze_channel_016x` | Manifest freeze `{channel:"0.16.x", schema:v1}` |
| `repro_check` | Two builds → identical `bundle_sha256` (or marker) |
| `clean_node_smoke` | Optional / skipped in audit test mode |
| `pytest_packaging` | `pytest -k packaging` green (or `--packaging-count` precomputed) |
| `dual_primary_zero` | `dual_primary=0` documented |
| `no_held_documented` | NO_HELD list present in council/capability docs |
| `release_checklist` | Core P14 checklist aggregation |

## CLI

```bash
.venv/bin/python scripts/final_release_audit.py
.venv/bin/python scripts/final_release_audit.py --json --skip-pytest --packaging-count 48
```

Exit code **0** only if all gates pass. `--json` emits an M2M-friendly summary
under `dist/final_audit/final_release_audit.json`.

## Library

```python
from neural_mesh.packaging import run_final_release_audit
r = run_final_release_audit("/path/to/repo", expect_version="0.16.3", expect_cp="CP-0027")
assert r.ok
print(r.to_json())
```

## Related P15 / P17

```bash
.venv/bin/python scripts/rc_soak.py --n 5 --ver 0.16.3
.venv/bin/python scripts/post_rc_watch.py --once
```

## dual_primary

**dual_primary=0** (single-node RC; peers=0; no multi-primary).

## NO_HELD

**NO_HELD:** Raft,N>2,multi-primary,ML,R2,R3,plaintext,Vault-ACME-req,GIA,SLO_chase,tag_schema,EVERY_fsync

## Bounds

No tag schema edits, no SLO chase, no Raft/N>2/consensus, no plaintext/GIA, no EVERY fsync optimization.
Manifest schema v1 remains frozen for 0.16.x (additive fields OK).
