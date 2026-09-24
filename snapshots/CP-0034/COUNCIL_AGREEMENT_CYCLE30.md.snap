# Council Agreement — Cycle 30 / CP-0034

**Capability:** DeepSeek NEXT (Cycle 29 VERDICT) — richer_OBS_peers  
**Title:** Richer OBS peers (mesh.status.snapshot/v1 peer injection + optional RO probe)  
**Scope:** Peer summary ergonomics; optional fail-closed RO fabric probe ≤2; no Raft/N>2/writes  
**Version:** package **0.17.0** (hold)  
**Checkpoint:** `CP-0034`

## Semver note

Hold **0.17.0**. Do **not** reopen 0.16.3 / single-node freeze. Do **not** move/delete tag `v0.16.3`.

## Scope and deliverables

- Capability doc `MESH_OBS_PEERS`
- Richer `PeerSummary` + `normalize_peer_summaries` / `load_peers_json` / `merge_peer_summaries`
- `obs_peers.probe_peer_readonly` / `probe_peers_readonly` (MAX=2, fail-closed)
- CLI peer injection + optional `--probe-peer`
- ≥12 tests (shipped 19): inject, normalize, CLI, RO probe, no mutation, N>2 refused

## Acceptance gates

- obs_peers_cycle30 tests green; full pytest green (520+19=539)
- `CP-0034=VERIFIED`
- dual_primary=0; probe never mutates
- Version==0.17.0; `v0.16.3` tag untouched

## Explicit exclusions and bounds

**NO_HELD:** Raft, N>2, multi-primary, ML, R2, R3, plaintext, Vault-ACME-req, GIA, SLO_chase, tag_schema, EVERY_fsync.

Debt: SCHEMA-GATED ACCEPT_AND_CARRY (unchanged).
