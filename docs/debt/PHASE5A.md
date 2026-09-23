# Phase 5A debt tracker

**Updated:** 2026-09-23 America/New_York (EDT) — Cycle 12 / CP-0016.

| Item | Status | Notes |
|------|--------|-------|
| Remote C-RAM API over Fabric mTLS | **RESOLVED** | put/get/verify/checkpoint_remote |
| N=2 active-passive replica + fencing | **RESOLVED** | epoch/promote; dual-primary=0 |
| Feature flag OFF → C11 single-node | **RESOLVED** | `NEURAL_MESH_PHASE5A_REPLICATION` |
| Raft / N>2 / multi-primary | **OUT OF SCOPE** | Hard NO for 5A |
| External PKI (Vault/ACME) | **EXPLICIT DEBT** (optional) | Not required |
| WAN multi-host ops hardening | **EXPLICIT DEBT** (optional) | Same code path |
