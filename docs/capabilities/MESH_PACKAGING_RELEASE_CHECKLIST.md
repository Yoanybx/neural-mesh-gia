# Mesh Packaging: Single-Node RC Release Checklist

**Capability:** `MESH_PACKAGING_RELEASE_CHECKLIST`  
**Cycle / Checkpoint:** 22 / CP-0026  
**Version:** 0.16.2  
**Scope:** `capability_not_tags_not_SLO` (single-node RC packaging)  
**Schema:** `mesh.bundle.manifest/v1` (**FROZEN** for 0.16.x)

## Purpose

Machine-checkable release gates for the single-node RC channel before council seal.
Complements P12 (`rc_install_verify`) and P13 (`rollback_smoke`).

## Gates

| Gate | Meaning |
|------|---------|
| `version_match` | `pyproject.toml` and `src/neural_mesh/__init__.py` agree; match `--expect-version` |
| `cp_tip_verified` | Checkpoint tip exists and `CheckpointManager.verify` passes |
| `freeze_present` | Built/sidecar manifest embeds `freeze: {channel:"0.16.x", schema:v1}` |
| `repro_check` | Two builds → identical `bundle_sha256` |
| `clean_node_smoke` | Clean-node smoke PASS (or cached marker) |
| `pytest_packaging` | `pytest -k packaging` green |
| `no_held_documented` | NO_HELD bounds present in council/capability docs |

## CLI

```bash
.venv/bin/python scripts/release_checklist.py
.venv/bin/python scripts/release_checklist.py --json --skip-pytest
```

Exit code **0** only if all gates pass. `--json` emits an M2M-friendly summary.

## Library

```python
from neural_mesh.packaging import run_release_checklist
r = run_release_checklist("/path/to/repo", expect_version="0.16.2", expect_cp="CP-0026")
assert r.ok
print(r.to_json())
```

## Related P12 / P13

```bash
.venv/bin/python scripts/rc_install_verify.py dist/neural-mesh-gia-single-node-0.16.2.tar.gz
.venv/bin/python scripts/rollback_smoke.py --build --ver-a 0.16.1 --ver-b 0.16.2
```

## NO_HELD

**NO_HELD:** Raft,N>2,multi-primary,ML,R2,R3,plaintext,Vault-ACME-req,GIA,SLO_chase,tag_schema,EVERY_fsync

## Bounds

No tag schema edits, no SLO chase, no Raft/N>2/consensus, no plaintext/GIA, no EVERY fsync optimization.
Manifest schema v1 remains frozen for 0.16.x (additive fields OK).
