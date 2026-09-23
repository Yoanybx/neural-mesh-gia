# Network Fabric v0 + mTLS — Trust Model (FROZEN Cycle 11 / P0)

**Status:** FROZEN merge gate (ChatGPT Cycle 10 reply A + DeepSeek Cycle 10 reply A +
`council/COUNCIL_AGREEMENT_CYCLE11.md`).
**Date:** 2026-09-23 America/New_York (EDT).
**Scope:** Phase 4 Network Fabric v0 — process↔process mTLS on localhost first
(host↔host reuses the same code path). Closes local TLS debt from Cycles 7–10.

This document is the authoritative **trust / transport** contract for Cycle 11.
Code must not diverge without a new council ADR.

---

## 1. Trust boundary

| Boundary | Meaning |
|----------|---------|
| Node | Process that holds a leaf cert whose CN/SAN equals `node_id` |
| Fabric | mTLS-secured framed stream between two nodes |
| Local / test-only | Explicit `mode="unix"` AF_UNIX path (no TLS claim) |

- **Primary path (Cycle 11):** mTLS process↔process on `127.0.0.1` / localhost TCP.
- **Same code path** is intended for host↔host later; no separate protocol.
- AF_UNIX remains available for local/test-only coexistence; mode is **explicit**
  in config (`tls` | `unix`). Never inferred silently.

---

## 2. Identity

- Node identity = X.509 leaf certificate **CN** (and DNS SAN) = `node_id`.
- Local CA issues rotatable leaf certs (PEM). No external Vault / ACME required.
- Peer identity verified after handshake: extracted CN/SAN must equal expected
  `node_id` or session fails closed (`FABRIC_TLS_ERROR` / `INVALID_SESSION`).
- Cert rotation: issue new leaf under the same CA, reload SSL context; in-flight
  sessions may close and reconnect (0 silent identity downgrade).

External / public PKI (Vault, ACME, public CAs) remains **optional EXPLICIT DEBT**
— see `docs/debt/TLS.md`.

---

## 3. Modes & no plaintext fallback

| Mode | Transport | When |
|------|-----------|------|
| `tls` | TCP + mTLS | Default fabric / production acceptance |
| `unix` | AF_UNIX framed | Local / test-only; **not** a security claim |

When `mode="tls"` is required:

- Handshake failure ⇒ typed `FABRIC_TLS_ERROR` (fail-closed).
- **No silent plaintext fallback** (binary acceptance: 0 plaintext fallbacks
  in the suite when TLS is required).
- Invalid / expired / wrong-CA / wrong-identity cert ⇒ reject.

---

## 4. Framing (preserved from Cycle 7)

Over TLS (and over AF_UNIX in unix mode), framing is identical to
`docs/cram_replica_oop_transport.md`:

```
+------------------+---------------------------+
| u32 BE length N  | N bytes payload (UTF-8 JSON) |
+------------------+---------------------------+
```

| Parameter | Value |
|-----------|-------|
| **MAX_FRAME_BYTES** | **16_777_216** (16 MiB) |
| Oversized / corrupt | Fail-closed: close session; typed error |
| Mid-frame EOF / kill | `CONNECTION_DROP` or `MESSAGE_CORRUPTION`; no partial apply |

---

## 5. Message types (P2)

| type | Purpose |
|------|---------|
| `TASK_REQUEST` | Router-selected task dispatch to execution endpoint |
| `STATE_QUERY` / `STATE_RESPONSE` | Lightweight node state |
| `HEARTBEAT` | Liveness |
| `CAPABILITY_UPDATE` | Capability advertisement (registry feed) |
| `CHECKPOINT_NOTICE` | Remote task completion → C-RAM checkpoint notice |
| `ACK` / `ERROR` | Protocol responses |

---

## 6. NodeSession contract

```
NodeSession.connect(node) → send(message) → receive() → close()
```

Typed faults: `NETWORK_TIMEOUT`, `CONNECTION_DROP`, `INVALID_SESSION`,
`MESSAGE_CORRUPTION`, `FABRIC_TLS_ERROR`.

---

## 7. Integration (Router → Fabric → Endpoint → C-RAM)

```
TaskSpec → Router R1 → selected node → Network Fabric → execution stub endpoint
         → CHECKPOINT_NOTICE / C-RAM checkpoint
```

---

## 8. Fault expectations

- kill -9 mid-handshake / mid-frame: no phantom ACK; recovery via checkpoint /
  reconnect; **dual writable primary = 0** (parity with CP-0011).
- Invalid cert rejected; node identity verified.
- No ghost sessions after drop (`INVALID_SESSION` on reuse).

---

## 9. Non-goals (Cycle 11)

- Raft / consensus / N>2
- ML / adaptive routing
- Phase 5 Cognitive/Memory distributed
- Silent plaintext fallback
- Requiring Vault / ACME / external PKI

---

## 10. Acceptance checklist

- [ ] This trust model frozen
- [ ] `network/{transport,tls,protocol,session}.py` with mTLS on
- [ ] Message types above
- [ ] Router → Fabric → endpoint → C-RAM tests
- [ ] Fault suite + dual-primary 0
- [ ] Bench N=1000 latency / TLS overhead / throughput / recovery / integrity
- [ ] Local mTLS debt **RESOLVED**; external PKI optional debt
- [ ] pytest ≥ 215; audit PASS; **CP-0015 VERIFIED**; version **0.11.0**
