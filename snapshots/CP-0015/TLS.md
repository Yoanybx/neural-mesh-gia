# TLS / PKI debt tracker

**Updated:** 2026-09-23 America/New_York (EDT) — Cycle 11 / CP-0015.

| Item | Status | Notes |
|------|--------|-------|
| Local mTLS (process↔process, localhost TCP, local CA, rotatable leafs) | **RESOLVED** | Implemented in `src/neural_mesh/network/`; trust model `docs/network_fabric_tls.md` |
| AuthN via cert CN/SAN = node_id | **RESOLVED** | Fail-closed identity check |
| Framing 16 MiB over TLS | **RESOLVED** | Same framing as Cycle 7 OOP |
| No silent plaintext fallback when TLS required | **RESOLVED** | Binary suite assertion |
| External / public PKI (Vault, ACME, public CA) | **EXPLICIT DEBT** (optional) | Not required for Cycle 11 acceptance; revisit before WAN mesh |
| WAN / multi-host deployment hardening | **EXPLICIT DEBT** (optional) | Same code path; ops/PKI outside local CA |

Historical note: Cycles 7–10 marked TLS as EXPLICIT DEBT with expiry 2026-12-31.
Cycle 11 paid the **local mTLS** portion before that expiry.
