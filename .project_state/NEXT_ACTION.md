# NEXT ACTION

PREFERRED_NEXT: CP-0088 P0 COMPLETE — await operator decision on P0.7 deploy proposal (hosting choice + approvals in `docs/planning/CP_0088_P0_7_DEPLOY_PROPOSAL.md`) or P1 scope

DONE: P0.7 deploy PROPOSAL ONLY: `deploy/minogan/` (Dockerfile non-root + /data volume + tokens secret + /health HEALTHCHECK, allowlist dockerignore, compose proposal with cloudflared sidecar sharing netns so the 127.0.0.1 guard stays, smoke.py) + proposal doc (cost table checked 2026-10-18; recommendation DO Basic 1 GiB + Tunnel + Workers VPC + R2 backups). Image NOT built (no docker on box). Nothing deployed; no accounts/keys/VMs/domains; no costs incurred.

DONE: P0.6 per-tenant hash-chained score ledger (`mesh.minogan.ledger/v0`): every scoring (service + optional in-process) with canonical metadata input, memory snapshot ref (before/used/appended), model_version, output digest; `mesh minogan replay <id>` byte-identical; `mesh minogan verify [--replay]` whole chain + memory refs + coverage.

DONE: P0.5 loopback HTTP service (stdlib): POST /v1/score + GET /health, sha256-only per-tenant Bearer, org_id==tenant, 1 MB/413, <2 s timeouts (408/504, no append after deadline), typed 4xx without echo, metadata-only logs; `mesh minogan serve|hash-token`; p95 27 ms @200 events.

DONE: P0.4 AgentMemory on C-RAM (day-bucket index, hash chain, kill -9 safe, tenant-checked reads); scorer memory= adds drift_long / recurrence / decline.

DONE: P0.2 contract.py + frozen pilot fixtures (228 valid / 12 invalid); P0.3 Mesh scorer v0 (228/228 exact parity vs pilot computeScore score_v0.3; byte-identical; zero network).

CP-0088 OPEN (camino Minogan, operator Joan 2026-10-18). P0.1 done: `council/NOTE_S0_MESH_MINOGAN_INTELLIGENCE.md`,
`docs/schema/minogan/` (uw_v0 + components ext + scorer_contract_v1_mapping). Then P0.3 deterministic scorer
(parity ±1 vs pilot computeScore score_v0.3, ≥50 fixtures), P0.4 AgentMemory, P0.5 HTTP, P0.6 ledger/replay,
P0.7 deploy proposal only. P1 deferred. Package 0.18.0 held; M1=NO_CONSENSUS_YET (N=2 scope). No push/tags; no paid services; LIVE_API_ENABLED untouched.

dist/: operator option A done (4 tracked files restored byte-identical; lost release archives intentionally NOT rebuilt; 17 known failures, see TEST_STATUS.md).
