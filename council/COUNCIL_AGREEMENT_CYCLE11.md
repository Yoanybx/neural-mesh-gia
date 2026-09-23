# Consejo Ciclo 11 — Phase 4 Network Fabric + TLS

| Voz | NEXT |
|-----|------|
| ChatGPT | **A)** Network Fabric v0 + close TLS debt → CP-0015 ≥210 |
| DeepSeek | **A)** Fabric + mTLS pay debt → CP-0015 ≥215 |
| Grok | **A** unificado |

## Trust model (P0 freeze)
- Scope: **mTLS process↔process on localhost** first (host↔host same code path); AF_UNIX remains for local/test-only paths; **no silent plaintext fallback** when TLS mode required.
- Node identity = cert CN/SAN = node_id; local CA + rotatable leaf certs (no external Vault/ACME — EXPLICIT DEBT if needed later).
- Framing: preserve 16MiB size limit over TLS; fail-closed on handshake/frame errors (`FABRIC_TLS_ERROR`).
- Compat: AF_UNIX + TLS modes coexist; mode explicit in config.

## Plan
P0 Doc freeze (trust, rotation, framing, fail-closed, AF_UNIX↔TLS)
P1 network/: transport, tls, protocol, session — TLS on; NodeSession connect/send/receive/close
P2 Messages: TASK_REQUEST, STATE_QUERY/RESPONSE, HEARTBEAT, CAPABILITY_UPDATE, CHECKPOINT_NOTICE
P3 Router R1 → Fabric → endpoint → C-RAM checkpoint integration tests
P4 Faults: NETWORK_TIMEOUT, CONNECTION_DROP, INVALID_SESSION, MESSAGE_CORRUPTION; kill -9 mid-handshake/mid-frame; dual-primary 0
P5 Bench N=1000: latency, TLS overhead vs C7 baseline; throughput; recovery; integrity
P6 Close TLS debt docs → RESOLVED (local mTLS); note external PKI still optional debt
P7 ≥215 tests; audit; **CP-0015**; version 0.11.0

NO: Raft, N>2, ML, Phase 5, plaintext fallback, external PKI requirement.
