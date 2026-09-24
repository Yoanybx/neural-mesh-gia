# Mesh Observability: Richer OBS Peers

**Capability:** `MESH_OBS_PEERS`  
**Cycle / Checkpoint:** 30 / CP-0034  
**Version:** 0.17.0 (hold; do **not** reopen 0.16.3 RC)  
**Theme:** 0.17 frozen theme **#3** — Richer OBS peers  
**Schema:** `mesh.status.snapshot/v1` (peer row extended; schema id unchanged)  
**Depends on:** `MESH_OBSERVABILITY_STATUS_SNAPSHOT` (CP-0023), `MESH_FABRIC_OPS_UX` (CP-0033)

## Purpose

Extend **peer summary injection ergonomics** for council M2M OBS and
`mesh status --snapshot`. Optional **read-only** peer probe reuses FabricOps
TLS heartbeat diagnose/status paths when trivial — still **no consensus**,
**no Raft**, **no N>2**, **no multi-primary**, **no writes** under peer probe.

## What shipped

| Surface | Location |
|---------|----------|
| Richer `PeerSummary` fields | `src/neural_mesh/status_snapshot.py` |
| Inject / normalize helpers | `normalize_peer_summaries`, `load_peers_json`, `parse_peers_json`, `merge_peer_summaries` |
| Optional RO probe | `src/neural_mesh/obs_peers.py` — `probe_peer_readonly` / `probe_peers_readonly` (max 2) |
| CLI | `mesh status --snapshot [--peers-file\|--peers-json] [--probe-peer … --fabric-root]` |
| M2M OBS | `format_obs_m2m` emits `peers=N peers_up=… peers_down=… peers_detail=…` |
| Tests | `tests/test_obs_peers_cycle30.py` (marker `obs_peers_cycle30`) |

### PeerSummary fields (v1 + CP-0034)

| Field | Default | Notes |
|-------|---------|-------|
| `node_id` | required | Stable sort key |
| `reachable` | `false` | |
| `summary` | `{}` | Free-form extras |
| `source` | `injected` | `injected` \| `file` \| `arg` \| `probed` |
| `ver` / `tip` / `cp_tip` | `null` | Optional OBS lift from summary |
| `latency_ms` / `tls_ok` / `heartbeat_ok` | `null` | Filled by RO probe |
| `error` / `error_code` | `null` | Fail-closed probe errors |
| `host` / `port` / `role` | `null` | Optional endpoint / role hints |

### Operator flows

1. **Inject only (default local peers=[])**  
   `mesh status --snapshot` — unchanged local-only default.
2. **File / arg injection**  
   `mesh status --snapshot --peers-file peers.json`  
   `mesh status --snapshot --peers-json '[{"node_id":"n1","reachable":true}]'`
3. **Optional RO probe (≤2 peers)**  
   `mesh status --snapshot --fabric-root DIR --probe-peer node-01 [--endpoints PATH]`  
   Fail-closed TLS heartbeat only; refuses N>2; never plaintext fallback; never mutates.

## Bounds (NO_HELD)

| Held | Meaning here |
|------|----------------|
| No Raft / N>2 / multi-primary | Probe cap `MAX_OBS_PEER_PROBES=2`; no consensus |
| No silent plaintext | Probe uses FabricOps TLS fail-closed path |
| No Vault/ACME required | Unchanged |
| No GIA / AGI claims | OBS ergonomics only |
| No SLO chase / tag_schema / EVERY_fsync | Unchanged |
| dual_primary | **Hard 0** — probe never elects primary |

## Exit criteria

- [x] Capability doc present
- [x] Richer peer model + inject/normalize helpers
- [x] Optional RO probe helper fail-closed, N≤2, no writes
- [x] CLI peer injection + `--probe-peer` (default local-only)
- [x] ≥12 pytest cases (marker `obs_peers_cycle30`)
- [x] Full suite green; version **0.17.0**; CP-0034 VERIFIED
- [x] dual_primary=0; no Raft / N>2 / GIA

## Non-goals

- Fabric reconnect / write paths from OBS status
- Multi-primary / Raft / N>2 topology
- External quickstart (0.17 theme #4 — next)
- Re-benchmarking SLOs or changing tag schema

## Related

- `docs/capabilities/MESH_OBSERVABILITY_STATUS_SNAPSHOT.md`
- `docs/capabilities/MESH_FABRIC_OPS_UX.md`
- `docs/planning/0.17_SCOPE_FROZEN.md` theme 3
- `council/PASTE_CYCLE29_M2M.md` / DeepSeek C29 NEXT=`richer_OBS_peers`
