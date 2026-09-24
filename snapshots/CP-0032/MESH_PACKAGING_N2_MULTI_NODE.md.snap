# Mesh Packaging: N=2 Multi-Node Bundle

**Capability:** `MESH_PACKAGING_N2_MULTI_NODE`  
**Cycle / Checkpoint:** 27 / CP-0031  
**Version:** 0.17.0 (open 0.17.x line; does **not** reopen 0.16.3 RC)  
**Scope:** N=2 packaging only — primary + secondary role configs / replica scripts  
**Schema:** `mesh.bundle.manifest/v1-n2` (**FROZEN** for 0.17.x-n2 RC; Cycle 28 / CP-0032) (sibling of frozen `mesh.bundle.manifest/v1`)

## Purpose

Produce a **reproducible**, **checksum-verified** **two-node** tarball that packages
enough material for an N=2 local loopback CRAM replica (Phase 5A/5B) **without**
inventing Raft, quorum consensus, N>2 topology, or multi-primary.

This is the first frozen **0.17** theme (`docs/planning/0.17_SCOPE_FROZEN.md` #1).
Single-node `mesh.bundle.manifest/v1` remains **FROZEN** for the closed `0.16.x`
RC channel. N2 uses a **distinct sibling schema id** and product name.

## Product / schema

| Item | Value |
|------|-------|
| Product name | `neural-mesh-gia-n2` |
| Schema id | `mesh.bundle.manifest/v1-n2` |
| Topology | `n2` (exactly two roles) |
| Roles | `[primary, secondary]` |
| Entrypoints | pair: primary `mesh`, secondary `mesh` (same CLI; role via stub config) |
| `dual_primary` | **must remain `0`** |
| Majority / heal | **fenced primary / heal** — **NOT Raft** |

### Schema extension plan (additive sibling)

Prefer additive fields on sibling schema `mesh.bundle.manifest/v1-n2` (or product
`neural-mesh-gia-n2`) rather than mutating frozen v1:

```json
{
  "schema": "mesh.bundle.manifest/v1-n2",
  "name": "neural-mesh-gia-n2",
  "ver": "0.17.0",
  "tip": "<gitsha7 or override>",
  "cp_range": "CP-0001..0031",
  "pytest": {"passed": 0, "failed": 0},
  "topology": "n2",
  "roles": ["primary", "secondary"],
  "entrypoint": {
    "primary": "mesh",
    "secondary": "mesh"
  },
  "dual_primary": 0,
  "majority": "fenced_primary_heal",
  "checksums": {
    "bundle.tar.gz": "<sha256>",
    "pyproject.toml": "<sha256>",
    "src/neural_mesh/__init__.py": "<sha256>"
  },
  "n2_extras": [
    "docs/phase5_replication_n2.md",
    "src/neural_mesh/packaging/n2_stub_configs/node_a_primary.json"
  ],
  "core_parity": {
    "note": "sha256 of shared core paths must match single-node build at same tip/ver"
  },
  "freeze": {
    "channel": "0.17.x-n2",
    "schema": "mesh.bundle.manifest/v1-n2",
    "single_node_schema_frozen": "mesh.bundle.manifest/v1"
  }
}
```

**Frozen single-node v1 is untouched.** Breaking changes to v1 still require CP +
semver minor on the closed 0.16.x RC track (out of scope). N2 schema evolves only
additively within 0.17.x-n2.

## Consensus / heal model (explicit)

| Concept | N2 packaging meaning |
|---------|----------------------|
| Majority | **Fenced primary / heal** using existing Phase 5A/5B epoch fencing + witness |
| Raft / Paxos / quorum | **Out of scope** — never packaged as a consensus engine |
| dual_primary | **Hard 0** — promote requires fencing; packaging asserts `dual_primary == 0` |
| N>2 / multi-primary | **Held** (NO_HELD) |

Failover remains the existing CRAM replica path: `NODE_LOSS(primary)` → verified
secondary → promote with epoch++ / `.cram/witness`. Packaging does **not** add a
new consensus protocol.

## Bundle contents

### Shared with single-node (core parity)

- `pyproject.toml`
- `src/neural_mesh/` (full package including `cram/replication/`, `replica_cli.py`)
- Single-node packaging scripts already on INCLUDE_PATHS
- Debt / packaging capability docs that single-node already ships
- `.project_state/CHECKPOINT.json`

Core file checksums for shared paths **must match** a single-node bundle built
from the same tip/ver overrides (`core_parity` gate).

### N2-only extras

- `docs/phase5_replication_n2.md`
- `docs/cram_replica_n2_interface.md`
- `docs/cram_replica_n2_consistency.md`
- `docs/cram_replica_oop_transport.md`
- `docs/capabilities/MESH_PACKAGING_N2_MULTI_NODE.md`
- `src/neural_mesh/packaging/n2_stub_configs/node_a_primary.json`
- `src/neural_mesh/packaging/n2_stub_configs/node_b_secondary.json`
- `scripts/build_n2_bundle.py`, `scripts/verify_n2_bundle.py`
- `scripts/n2_install_rollback_smoke.py`

**Excluded (same as single-node):** `.venv`, `.git`, `__pycache__`, `experiments/`,
`snapshots/`, `council/`, large scratch.

Archive root: `neural-mesh-gia/` (same as single-node for extract familiarity).

## Local loopback install (P29)

Filesystem-level only — **no real multi-host network**:

1. Extract N2 bundle into two prefixes: `node-a/` (primary stub) and `node-b/` (secondary stub).
2. Smoke: `import neural_mesh` + `mesh --help` (or launcher) in each prefix.
3. Optional lightweight replica status **mock** (document that full `mesh cram replica serve`
   is **out-of-band** for this smoke).
4. Rollback one node to a prior-ver fixture and re-smoke (Cycle 22 filesystem pattern).

## Bounds / NO_HELD

**NO_HELD:** Raft, N>2, multi-primary, ML, R2, R3, plaintext, Vault-ACME-req, GIA,
SLO_chase, tag_schema, EVERY_fsync.

Do **not** reopen 0.16.3 RC. Do **not** alter tag `v0.16.3`. Prefer package version
**0.17.0** unless forced by conflict.

## Related

- Single-node: `docs/capabilities/MESH_PACKAGING_SINGLE_NODE_BUNDLE.md`
- Replica: `docs/phase5_replication_n2.md`, `docs/cram_replica_n2_*`
- Scope freeze: `docs/planning/0.17_SCOPE_FROZEN.md`
- Implementation: `neural_mesh.packaging.bundle_n2`, `manifest_n2`, `n2_install`


## Schema freeze (Cycle 28 / CP-0032)

N2 RC channel freeze is **embedded** by `build_n2_bundle` (always):

```json
"freeze": {
  "channel": "0.17.x-n2",
  "schema": "mesh.bundle.manifest/v1-n2",
  "single_node_schema_frozen": "mesh.bundle.manifest/v1"
}
```

`verify_n2_bundle(..., expect_freeze_channel="0.17.x-n2")` rejects missing/wrong
channel. Single-node `mesh.bundle.manifest/v1` / `0.16.x` freeze is **unchanged**.
