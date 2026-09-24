# External Quickstart — Neural Mesh 0.16.3 (single-node)

**Audience:** operators / external users of the **signed-off** single-node release  
**Release:** **0.16.3** — CLOSED / FROZEN (`mesh.bundle.manifest/v1`, channel `0.16.x`)  
**Archive:** `dist/releases/0.16.3/`  
**Capability:** `MESH_EXTERNAL_QUICKSTART` (Cycle 31 / CP-0035)  
**Do not:** reopen the 0.16.3 packaging RC, retag `v0.16.3`, or rebuild the release channel unless the archive is broken.

## What this is

A **public / external** path to install, verify, and smoke the **0.16.3 single-node**
bundle that council already signed off. This document does **not** introduce
multi-node consensus, Raft, N>2 topology, GIA, Vault/ACME hard requirements, or
silent plaintext.

## Prerequisites

- Linux (or compatible POSIX) with **Python ≥ 3.10**
- `sha256sum` (or equivalent) for archive integrity
- Optional: a virtualenv for running in-repo verify scripts from a checkout

You do **not** need Ray, Torch, OpenTelemetry, Vault, or ACME for the single-node path.

## Release artifacts (CLOSED)

| Artifact | Path under `dist/releases/0.16.3/` |
|----------|-----------------------------------|
| Single-node tarball | `neural-mesh-gia-single-node-0.16.3.tar.gz` |
| Manifest (`mesh.bundle.manifest/v1`) | `neural-mesh-gia-single-node-0.16.3.manifest.json` |
| Checksums | `SHA256SUMS` |
| Signoff | `SIGNOFF.json` (`mesh.release.signoff/v1`) |
| Tag marker / archive meta | `TAG_MARKER.json`, `ARCHIVE_MANIFEST.json` |

Expected product: `name=neural-mesh-gia-single-node`, `ver=0.16.3`,
`entrypoint=mesh`, freeze `{channel: "0.16.x", schema: "mesh.bundle.manifest/v1"}`.

## Path A — From a repo checkout (recommended for verify)

Assumes you have this repository checked out and a venv with the package
installable (or at least `PYTHONPATH=src`). Prefer **verify existing release
artifacts**; do **not** call `build_bundle` against the closed channel.

```bash
# 0) Optional dry-run helper (prints planned steps; no extract/install)
bash scripts/quickstart_0.16.3.sh --dry-run

# 1) Checksum the release directory entries
cd dist/releases/0.16.3
sha256sum -c SHA256SUMS

# 2) Verify bundle (manifest + member checksums + import smoke)
#    From repo root:
.venv/bin/python scripts/verify_bundle.py \
  dist/releases/0.16.3/neural-mesh-gia-single-node-0.16.3.tar.gz \
  --manifest dist/releases/0.16.3/neural-mesh-gia-single-node-0.16.3.manifest.json \
  --expected-ver 0.16.3

# 3) RC install verify into a clean prefix (help + status --snapshot)
.venv/bin/python scripts/rc_install_verify.py \
  dist/releases/0.16.3/neural-mesh-gia-single-node-0.16.3.tar.gz \
  --manifest dist/releases/0.16.3/neural-mesh-gia-single-node-0.16.3.manifest.json \
  --expect-freeze 0.16.x

# 4) Optional clean-node smoke (no reach-back into live repo)
.venv/bin/python scripts/clean_node_smoke.py \
  dist/releases/0.16.3/neural-mesh-gia-single-node-0.16.3.tar.gz \
  --manifest dist/releases/0.16.3/neural-mesh-gia-single-node-0.16.3.manifest.json
```

Helper (fail-closed; default is dry-run):

```bash
bash scripts/quickstart_0.16.3.sh            # dry-run
bash scripts/quickstart_0.16.3.sh --execute  # checksum + verify_bundle only
```

## Path B — Extract-only (minimal external)

If you only have the tarball + manifest + `SHA256SUMS`:

```bash
sha256sum -c SHA256SUMS
tar -xzf neural-mesh-gia-single-node-0.16.3.tar.gz
cd neural-mesh-gia
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -U pip
# Editable install from the extracted tree (single-node deps only):
python -m pip install -e .
mesh --help
mesh status --snapshot
```

Notes:

- Archive root is `neural-mesh-gia/`.
- Entrypoint console script is **`mesh`**.
- Prefer TLS fabric helpers if you later enable network paths; **no silent
  plaintext fallback** is supported or documented here.

## Honest bounds (read before claiming success)

| Bound | Meaning |
|-------|---------|
| Single-node only | This quickstart covers the **0.16.3 single-node** bundle |
| Release CLOSED | Do not rebuild / retag / reopen `0.16.x` RC packaging |
| No Raft / N>2 / multi-primary | Not in 0.16.3; not claimed here |
| No GIA / AGI | Product name retains historical “GIA”; **no GIA runtime claims** |
| No Vault / ACME required | Local single-node path does not hard-require external PKI |
| No plaintext fallback | Fabric/TLS paths fail closed; unix/plaintext is not a silent option |
| dual_primary | **0** (single-node) |
| Debt | `CHECKPOINT_EVERY_FLOOR` remains SCHEMA-GATED / ACCEPT_AND_CARRY |

## Smoke expectations

A successful verify / install path should show roughly:

- `VERIFY: PASS` with `VER: 0.16.3`
- `RC_INSTALL_VERIFY: PASS` with freeze `0.16.x`
- `mesh --help` exits 0
- `mesh status --snapshot` emits `mesh.status.snapshot/v1` JSON (local peers default empty)

## Related docs

- `docs/capabilities/MESH_PACKAGING_SINGLE_NODE_BUNDLE.md`
- `docs/capabilities/MESH_PACKAGING_RELEASE_SIGNOFF.md`
- `docs/capabilities/MESH_EXTERNAL_QUICKSTART.md`
- Forward-looking stub (0.17 themes, not a second release path):
  `docs/quickstart/QUICKSTART_0.17_STUB.md`

## Non-goals

- Reopening or rebuilding the 0.16.3 packaging channel
- Shipping unfinished 0.17 theme features as “done” in this quickstart
- Documenting Raft, N>2, multi-primary, or GIA as available
