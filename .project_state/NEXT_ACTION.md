# NEXT ACTION

PREFERRED_NEXT: CP-0088 P0.5 — HTTP service (POST /v1/score, GET /health, per-tenant Bearer, 1 MB)

DONE: P0.4 AgentMemory on C-RAM (day-bucket index, hash chain, kill -9 safe, tenant-checked reads); scorer memory= adds drift_long / recurrence / decline.

DONE: P0.2 contract.py + frozen pilot fixtures (228 valid / 12 invalid); P0.3 Mesh scorer v0 (228/228 exact parity vs pilot computeScore score_v0.3; byte-identical; zero network).

CP-0088 OPEN (camino Minogan, operator Joan 2026-10-18). P0.1 done: `council/NOTE_S0_MESH_MINOGAN_INTELLIGENCE.md`,
`docs/schema/minogan/` (uw_v0 + components ext + scorer_contract_v1_mapping). Then P0.3 deterministic scorer
(parity ±1 vs pilot computeScore score_v0.3, ≥50 fixtures), P0.4 AgentMemory, P0.5 HTTP, P0.6 ledger/replay,
P0.7 deploy proposal only. P1 deferred. Package 0.18.0 held; M1=NO_CONSENSUS_YET (N=2 scope). No push/tags; no paid services; LIVE_API_ENABLED untouched.

dist/: operator option A done (4 tracked files restored byte-identical; lost release archives intentionally NOT rebuilt; 17 known failures, see TEST_STATUS.md).
