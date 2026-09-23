# Mesh Packaging: Single-Node Bundle

**Capability:** `MESH_PACKAGING_SINGLE_NODE_BUNDLE`  
**Cycle / Checkpoint:** 20 / CP-0024  
**Version:** 0.16.0  
**Scope:** `capability_not_tags_not_SLO`  
**Schema:** `mesh.bundle.manifest/v1`

## Purpose

Produce a **reproducible**, **checksum-verified** single-node tarball sufficient to run a local Neural Mesh node (`mesh` entrypoint / `python -m` via `src` layout), with a versioned JSON manifest for council/M2M continuity.

This capability does **not** change tag schemas, chase SLOs, alter consensus, Raft, or N>2 topology.

## Schema (v1)

```json
{
  "schema": "mesh.bundle.manifest/v1",
  "name": "neural-mesh-gia-single-node",
  "ver": "0.16.0",
  "tip": "<gitsha7 or override>",
  "cp_range": "CP-0001..0024",
  "pytest": {"passed": 396, "failed": 0},
  "entrypoint": "mesh",
  "checksums": {
    "bundle.tar.gz": "<sha256 of archive>",
    "pyproject.toml": "<sha256>",
    "src/neural_mesh/__init__.py": "<sha256>"
  },
  "cp_tip": "CP-0024",
  "created_utc": "1970-01-01T00:00:00+00:00",
  "files": ["pyproject.toml", "src/neural_mesh/..."],
  "bundle_sha256": "<same as checksums.bundle.tar.gz>"
}
```

### Required fields (DeepSeek P0)

| Field | Meaning |
|-------|---------|
| `name` | Bundle product name |
| `ver` | Package / bundle version |
| `tip` | Git tip (7-char) or override |
| `cp_range` | Checkpoint range `CP-0001..NNNN` |
| `pytest` | `{passed, failed}` summary embedded in manifest |
| `entrypoint` | Console script (`mesh`) |
| `checksums` | sha256 map: member paths + `bundle.tar.gz` |

## Bundle contents

Included (when present):

- `pyproject.toml`
- `src/neural_mesh/` (package; excludes `__pycache__`)
- `scripts/build_bundle.py`, `scripts/verify_bundle.py`, `scripts/audit.sh`, `scripts/bootstrap.sh`
- `docs/debt/CHECKPOINT_EVERY_FLOOR.md` (debt marker)
- `docs/capabilities/MESH_PACKAGING_SINGLE_NODE_BUNDLE.md`
- `.project_state/CHECKPOINT.json`

**Excluded:** `.venv`, `.git`, `__pycache__`, `experiments/`, `snapshots/`, `council/`, large scratch.

Archive root directory: `neural-mesh-gia/`.

## Reproducibility

- Member names sorted
- Fixed `mtime=0`, `uid=0`, `gid=0`, normalized modes (`0644` / `0755` for scripts)
- Gzip `mtime=0`
- Manifest `created_utc` fixed to Unix epoch for bit-stable manifests when tip/ver/cp_range fixed

Two builds with the same tip/ver/cp_range and identical tree yield **identical** `bundle_sha256`.

## CLI (DeepSeek names)

```bash
# Build
.venv/bin/python scripts/build_bundle.py --out dist/ [--ver 0.16.0] [--tip <sha7>]

# Verify (checksums + manifest + import smoke)
.venv/bin/python scripts/verify_bundle.py dist/neural-mesh-gia-single-node-0.16.0.tar.gz
```

Optional library API:

```python
from neural_mesh.packaging import build_bundle, verify_bundle

m = build_bundle("/path/to/repo", "/path/to/dist", tip="abc1234", ver="0.16.0")
r = verify_bundle("/path/to/dist/neural-mesh-gia-single-node-0.16.0.tar.gz")
assert r.ok
```

Also available via package: `neural_mesh.packaging`.

## Verify steps

1. Load + validate `mesh.bundle.manifest/v1`
2. Compare archive sha256 to `bundle_sha256` / `checksums["bundle.tar.gz"]`
3. Extract; compare each member file sha256
4. Smoke (default): `PYTHONPATH=src python -c "import neural_mesh"`

## Tests

`tests/test_packaging_single_node_bundle.py` (keyword `packaging_single_node_bundle`) — unit schema, exclude rules, golden manifest, determinism, roundtrip verify, tamper detection, script CLI.

## Bounds / NO

**NO:** tag schema edits, SLO chase / rebenchmark, Raft, N>2, ML, plaintext transport changes, GIA claims, EVERY fsync optimization, consensus changes.

## Related

- Debt: `docs/debt/CHECKPOINT_EVERY_FLOOR.md` (SCHEMA-GATED; reported only)
- Prior capability: `docs/capabilities/MESH_OBSERVABILITY_STATUS_SNAPSHOT.md`
