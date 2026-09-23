# Council Agreement — Cycle 19 / CP-0023

**Capability:** DeepSeek NEXT  
**Title:** Mesh Observability: Status Snapshot  
**Scope:** `capability_not_tags_not_SLO`  
**Version next:** `0.15.0`  
**Checkpoint next:** `CP-0023`

## Scope and deliverables

- **P0 — Define the read-only snapshot schema:** `node_id`, `cycle`, `ver`, `cp_range`, `pytest`, `slo_state`, `debt_gates`.
- **P1 — Implement** `mesh.status.snapshot()` with local and peer summaries; no consensus writes.
- **P2 — Expose** `mesh status --snapshot` and M2M field `OBS`.
- **P3 — Test:** unit tests, integration tests with a 3-node mock, and golden output.
- **P4 — Document:** `docs/capabilities/MESH_OBSERVABILITY_STATUS_SNAPSHOT.md`.

## Acceptance gates

- `observability_status_snapshot=12/0` (`PYTEST_MIN`).
- `372+12` tests pass.
- `AUDIT=PASS`.
- `CP-0023=VERIFIED`.
- Snapshot output is stable.
- `no_SLO_chase` / `NO_SLO_CHASE` remains in force.

## Explicit exclusions and bounds

**NO:** `NO_SLO_CHASE`, `NO_TAG_SCHEMA`, `NO_RAFT`, `NO_N>2`, `NO_ML`, `NO_PLAINTEXT`, `NO_GIA`, `NO_EVERY_fsync`.

**BOUNDS:** `no_consensus_change`, `no_SLO_change`, `no_tag_schema`, `no_Raft`, `no_N>2`, `no_ML`, `no_plaintext`, `no_GIA`, `no_EVERY_fsync`.

This agreement authorizes documentation and implementation planning for the capability only; it does not authorize unrelated code changes or SLO work.
