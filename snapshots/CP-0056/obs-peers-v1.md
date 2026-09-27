# OBS Peers v1 (ops surface)

**Blueprint path:** `D:docs/ops/obs-peers-v1.md` (L1 R2)  
**Capability:** `MESH_OBS_PEERS` — see `docs/capabilities/MESH_OBS_PEERS.md`  
**Evidence:** Cycle 30 / CP-0034 (tip `64747b9`); tests marker `obs_peers_cycle30`  
**Package line:** shipped under 0.17.0; current package held at **0.18.0**

## Purpose

Operator/ops documentation for **richer OBS peer summaries** on
`mesh.status.snapshot/v1`. This is the blueprint-named ops doc; the full
capability contract lives under `docs/capabilities/`.

## Surfaces

| Surface | Location |
|---------|----------|
| Capability | `docs/capabilities/MESH_OBS_PEERS.md` |
| Library | `src/neural_mesh/obs_peers.py`, richer rows in `status_snapshot.py` |
| CLI | `mesh status --snapshot [--peers-file\|--peers-json] [--probe-peer …]` |
| Tests | `tests/test_obs_peers_cycle30.py` (T-R2a inject; T-R2b RO probe +neg N>2) |

## Operator notes

1. Default snapshot remains **local-only** (ABORT→single-node view when peers absent).
2. Optional RO probe: max **2** peers; TLS heartbeat only; fail-closed; never mutates.
3. Probe refuses N>2; never plaintext fallback; never elects primary (`dual_primary=0`).

## Bounds

- L1 R2 OBS peers ≠ NO_HELD product layer **R2** (ML-router depth). Do **not** unlock NO_HELD R2/R3.
- No Raft / multi-primary / GIA claims from OBS peers UX.

## Related

- `docs/planning/L1_RESIDUE_CLOSEOUT.md`
- `docs/capabilities/MESH_FABRIC_OPS_UX.md` (probe reuses FabricOps TLS)
