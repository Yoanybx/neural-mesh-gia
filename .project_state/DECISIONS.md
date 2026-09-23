# ARCHITECTURAL DECISIONS

Use ADR files for major decisions.

## ADR-0001 — Checkpoint integrity (Cycle 1)
- Store `manifest_sha256` inside `checkpoint.json` for humans/agents.
- Hash canonical JSON with `manifest_sha256` nulled to avoid circular digest.
- Freeze `.project_state/CHECKPOINT.json` into each snapshot folder so historical `verify` is independent of later global state.

## ADR-0002 — Digital Twin Phase 1 slice
- Pure Python + networkx public API; no Ray/torch required.
- Deterministic discrete-time scheduler; digest mixes seed + schedule for replay identity.
