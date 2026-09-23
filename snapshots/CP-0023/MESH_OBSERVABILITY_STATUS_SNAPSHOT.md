# Mesh Observability: Status Snapshot

**Capability:** `MESH_OBSERVABILITY_STATUS_SNAPSHOT`  
**Cycle / Checkpoint:** 19 / CP-0023  
**Version:** 0.15.0  
**Scope:** `capability_not_tags_not_SLO`  
**Schema:** `mesh.status.snapshot/v1`

## Purpose

Provide a **read-only**, deterministic status snapshot of a mesh node for:

- Local operator introspection (`mesh status --snapshot`)
- Council M2M STATUS posts (compact `OBS:` field)
- Multi-node summaries via **injected** peer payloads (no live consensus)

This capability does **not** chase SLOs, change tag schemas, or perform consensus writes.

## Schema (v1)

```json
{
  "schema": "mesh.status.snapshot/v1",
  "node_id": "local",
  "cycle": 19,
  "ver": "0.15.0",
  "tip": "<gitsha7 or null>",
  "cp_range": "CP-0001..0023",
  "cp_tip": "CP-0023",
  "pytest": {"passed": 384, "failed": 0},
  "slo_state": {
    "checkpoint_durable_batch": "MET",
    "checkpoint_every_floor": "SCHEMA-GATED",
    "recovery": "MET"
  },
  "debt_gates": [
    {
      "id": "CHECKPOINT_EVERY_FLOOR",
      "state": "SCHEMA-GATED",
      "path": "docs/debt/CHECKPOINT_EVERY_FLOOR.md"
    }
  ],
  "peers": [
    {"node_id": "n1", "reachable": true, "summary": {}}
  ],
  "local": {
    "last_checkpoint": "CP-0023",
    "current_phase": 5,
    "current_module": "mesh-observability",
    "safety_status": "SAFE",
    "status": "VERIFIED",
    "project_version": "0.15.0",
    "bounds": {
      "no_consensus_writes": true,
      "no_raft": true,
      "no_slo_chase": true,
      "no_tag_schema_change": true,
      "read_only": true
    }
  }
}
```

### Field notes

| Field | Source | Notes |
|-------|--------|-------|
| `ver` | `pyproject.toml` / project state | Package version |
| `tip` | `git rev-parse --short=7 HEAD` | `null` if unavailable |
| `cp_tip` / `cp_range` | `.project_state/CHECKPOINT.json` + `snapshots/CP-*` | Range is `CP-0001..NNNN` |
| `pytest` | Project state `test_summary` | Not a live re-run |
| `slo_state` | Known documented states + debt markers | **No re-benchmark** |
| `debt_gates` | `docs/debt/*.md` Status markers | Sorted by path |
| `peers` | Caller-injected only | Sorted by `node_id` |
| `local` | Project state summaries | Includes explicit bounds |

Serialization is JSON with **sorted keys** (`snapshot_to_json`).

## Python API

```python
from neural_mesh.status_snapshot import snapshot, format_obs_m2m, snapshot_to_json
# or
from neural_mesh.status import snapshot  # mesh.status.snapshot()

snap = snapshot("/path/to/repo", node_id="n0", peers=[...])  # peers optional
print(snapshot_to_json(snap))
print(format_obs_m2m(snap))
```

`snapshot()` is **read-only**: it never writes under the repo root, never opens Raft/consensus, and never mutates `tags.py`.

### Peers

Pass a list of `{node_id, reachable, summary}` dicts (or `PeerSummary` models). Unit/integration tests use a **3-node mock** by injecting fake summaries — no real network is required.

Optional light peer probe is **out of scope** unless existing fabric helpers make a trivial read-only call; CP-0023 ships injection/mock only.

## CLI

```bash
mesh status                 # unchanged: project state JSON
mesh status --snapshot      # observability snapshot JSON
mesh status --snapshot --json   # same (JSON is default for --snapshot)
mesh status --snapshot --m2m    # compact OBS: one-liner
mesh status --snapshot --node-id n0
```

## M2M OBS

`format_obs_m2m(snap)` / `mesh status --snapshot --m2m` emits a single line, e.g.:

```text
OBS: cycle=19 ver=0.15.0 tip=abcdef0 cp=CP-0023 cp_range=CP-0001..0023 pytest=384/0 slo_floor=SCHEMA-GATED slo_batch=MET slo_recovery=MET debt=CHECKPOINT_EVERY_FLOOR=SCHEMA-GATED peers=0
```

Embed under council STATUS posts as the `OBS` field.

## Bounds / Hard NO

From DeepSeek CAPABILITY_NEXT (`capability_not_tags_not_SLO`):

| Bound | Meaning |
|-------|---------|
| `NO_SLO_CHASE` | Report documented SLO/debt state only; do not rebench or “fix” floors |
| `NO_TAG_SCHEMA` | Do not edit `tags.py` schema gates (read-only reference OK) |
| `NO_RAFT` / `NO_N>2` | No consensus protocol; peers are injected mocks |
| `NO_ML` / `NO_PLAINTEXT` / `NO_GIA` | Out of scope |
| `NO_EVERY_fsync` | No EVERY fsync optimization work |
| `no_consensus_change` | Snapshot must not perform consensus writes |

## Tests

```bash
.venv/bin/pytest -q tests/test_observability_status_snapshot.py
# or
.venv/bin/pytest -q -k observability_status_snapshot
```

Gate: **≥12** passed / 0 failed (`observability_status_snapshot=12/0`).

## Acceptance (CP-0023)

- pytest full suite ≥ 384 (372+12)
- `AUDIT=PASS`
- `CP-0023=VERIFIED`
- Snapshot output stable (`sort_keys`)
- `no_SLO_chase` held
