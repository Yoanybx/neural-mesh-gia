# Mesh Packaging: Single-Node Bundle

**Capability:** `MESH_PACKAGING_SINGLE_NODE_BUNDLE`  
**Cycle / Checkpoint:** 21 / CP-0025 (extends Cycle 20 / CP-0024)  
**Version:** 0.16.1  
**Scope:** `capability_not_tags_not_SLO`  
**Schema:** `mesh.bundle.manifest/v1` (**FROZEN** for 0.16.x)

## Purpose

Produce a **reproducible**, **checksum-verified** single-node tarball sufficient to run a local Neural Mesh node (`mesh` entrypoint / `python -m` via `src` layout), with a versioned JSON manifest for council/M2M continuity.

This capability does **not** change tag schemas, chase SLOs, alter consensus, Raft, or N>2 topology.

## Semver note (Cycle 21)

DeepSeek Cycle 20 VERDICT did not specify a hard next semver. Council chose **0.16.1** (patch): packaging RC hardening (clean-node smoke, manifest repro, RC freeze) on top of **0.16.0**. Documented in `council/COUNCIL_AGREEMENT_CYCLE21.md`.

## Schema (v1)

```json
{
  "schema": "mesh.bundle.manifest/v1",
  "name": "neural-mesh-gia-single-node",
  "ver": "0.16.1",
  "tip": "<gitsha7 or override>",
  "cp_range": "CP-0001..0025",
  "pytest": {"passed": 406, "failed": 0},
  "entrypoint": "mesh",
  "checksums": {
    "bundle.tar.gz": "<sha256 of archive>",
    "pyproject.toml": "<sha256>",
    "src/neural_mesh/__init__.py": "<sha256>"
  },
  "cp_tip": "CP-0025",
  "created_utc": "1970-01-01T00:00:00+00:00",
  "files": ["pyproject.toml", "src/neural_mesh/..."],
  "bundle_sha256": "<same as checksums.bundle.tar.gz>",
  "freeze": {"channel": "0.16.x", "schema": "mesh.bundle.manifest/v1"}
}
```

### Required fields (DeepSeek P0 / CP-0024)

| Field | Meaning |
|-------|---------|
| `name` | Bundle product name |
| `ver` | Package / bundle version |
| `tip` | Git tip (7-char) or override |
| `cp_range` | Checkpoint range `CP-0001..NNNN` |
| `pytest` | `{passed, failed}` summary embedded in manifest |
| `entrypoint` | Console script (`mesh`) |
| `checksums` | sha256 map: member paths + `bundle.tar.gz` |

### Additive optional (CP-0025)

| Field | Meaning |
|-------|---------|
| `freeze` | `{channel:"0.16.x", schema:"mesh.bundle.manifest/v1"}` — RC freeze marker |

## RC freeze (P11)

**`mesh.bundle.manifest/v1` is FROZEN for the `0.16.x` channel.**

Frozen / stable fields (no breaking changes without **CP + semver minor**):

- `schema` (= `mesh.bundle.manifest/v1`)
- `name`, `ver`, `tip`, `cp_range`, `pytest`, `entrypoint`, `checksums`
- Determinism contract: sorted members, `FIXED_MTIME=0`, uid/gid 0, gzip mtime 0, fixed `created_utc`
- Archive root: `neural-mesh-gia/`

**Policy:** additive optional fields (e.g. `freeze`) are allowed within 0.16.x; removing/renaming required fields or changing checksum semantics requires a new checkpoint and a **minor** version bump (0.17.0+).

Default builds embed:

```json
"freeze": {"channel": "0.16.x", "schema": "mesh.bundle.manifest/v1"}
```

`verify_bundle` validates `freeze.schema` when present. Omit with `build_bundle(..., freeze=False)` or `scripts/build_bundle.py --no-freeze`.

## Bundle contents

Included (when present):

- `pyproject.toml`
- `src/neural_mesh/` (package; excludes `__pycache__`)
- `scripts/build_bundle.py`, `scripts/verify_bundle.py`, `scripts/clean_node_smoke.py`, `scripts/repro_check.py`, `scripts/audit.sh`, `scripts/bootstrap.sh`
- `docs/debt/CHECKPOINT_EVERY_FLOOR.md` (debt marker)
- `docs/capabilities/MESH_PACKAGING_SINGLE_NODE_BUNDLE.md`
- `.project_state/CHECKPOINT.json`

**Excluded:** `.venv`, `.git`, `__pycache__`, `experiments/`, `snapshots/`, `council/`, large scratch.

Archive root directory: `neural-mesh-gia/`.

## Reproducibility (P10)

- Member names sorted
- Fixed `mtime=0`, `uid=0`, `gid=0`, normalized modes (`0644` / `0755` for scripts) — **name/suffix-based** (no `os.access` flake)
- Gzip `mtime=0`
- Manifest `created_utc` fixed to Unix epoch for bit-stable manifests when tip/ver/cp_range/pytest fixed

Two builds with the same tip/ver/cp_range/pytest and identical tree yield **identical** `bundle_sha256`.

```bash
.venv/bin/python scripts/repro_check.py --ver 0.16.1 --tip deadbee --cp-range CP-0001..0025
# or
.venv/bin/python scripts/build_bundle.py --repro-check --ver 0.16.1 --tip deadbee
```

## Clean-node smoke (P9)

Prove the bundle runs on a **clean node**: empty temp root with **no** reach-back into the original repo beyond the extracted tarball.

```bash
.venv/bin/python scripts/clean_node_smoke.py dist/neural-mesh-gia-single-node-0.16.1.tar.gz
# or build+smoke:
.venv/bin/python scripts/clean_node_smoke.py --build --out dist/
```

Steps:

1. `verify_bundle` (checksums + import smoke)
2. Extract to empty temp
3. Force `sys.path` to prefer `extract/src`; drop original-repo path entries
4. Assert `neural_mesh.__file__` is under extract (not under forbidden repo)
5. Run `mesh status --snapshot` equivalent (library + CLI) with `cwd=extract`

## CLI (DeepSeek names)

```bash
# Build
.venv/bin/python scripts/build_bundle.py --out dist/ [--ver 0.16.1] [--tip <sha7>]

# Verify (checksums + manifest + import smoke)
.venv/bin/python scripts/verify_bundle.py dist/neural-mesh-gia-single-node-0.16.1.tar.gz

# Clean-node smoke (P9)
.venv/bin/python scripts/clean_node_smoke.py dist/neural-mesh-gia-single-node-0.16.1.tar.gz

# Repro check (P10)
.venv/bin/python scripts/repro_check.py --ver 0.16.1 --tip <sha7>
```

Optional library API:

```python
from neural_mesh.packaging import build_bundle, verify_bundle, clean_node_smoke, repro_check

m = build_bundle("/path/to/repo", "/path/to/dist", tip="abc1234", ver="0.16.1")
r = verify_bundle("/path/to/dist/neural-mesh-gia-single-node-0.16.1.tar.gz")
assert r.ok
cs = clean_node_smoke(tar_path, forbidden_repo="/path/to/repo")
assert cs.ok
rr = repro_check("/path/to/repo", "/tmp/repro", tip="abc1234", ver="0.16.1")
assert rr.ok
```

Also available via package: `neural_mesh.packaging`.

## Verify steps

1. Load + validate `mesh.bundle.manifest/v1`
2. If `freeze` present: check `freeze.schema` matches schema id
3. Compare archive sha256 to `bundle_sha256` / `checksums["bundle.tar.gz"]`
4. Extract; compare each member file sha256
5. Smoke (default): `PYTHONPATH=src python -c "import neural_mesh"`

## Tests

- `tests/test_packaging_single_node_bundle.py` (keyword `packaging_single_node_bundle`) — unit schema, exclude rules, golden manifest, determinism, roundtrip verify, tamper detection, script CLI.
- `tests/test_packaging_rc_cycle21.py` (keyword `packaging_rc_cycle21`) — P9 clean-node smoke, P10 repro/hash-lock, P11 freeze/version gate (≥8).

## Bounds / NO

**NO:** tag schema edits, SLO chase / rebenchmark, Raft, N>2, ML, plaintext transport changes, GIA claims, EVERY fsync optimization, consensus changes.

## Related

- Debt: `docs/debt/CHECKPOINT_EVERY_FLOOR.md` (SCHEMA-GATED; reported only)
- Prior capability: `docs/capabilities/MESH_OBSERVABILITY_STATUS_SNAPSHOT.md`
- Council: `council/COUNCIL_AGREEMENT_CYCLE21.md`
