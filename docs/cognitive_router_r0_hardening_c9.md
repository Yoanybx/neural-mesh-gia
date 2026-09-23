# Cognitive Router R0 — Hardening + Observability (Cycle 9)

**CP-0013.** Extends `docs/cognitive_router_r0.md` (C8 freeze). Does **not** change
the R0 determinism contract.

## P0 — Doc freeze (this cycle)

### Mid-route C-RAM failure

When a `DecisionStore` is configured, persist runs **before** the router mutates
RR state or returns a `RouteDecision`. If C-RAM is down / transport cut /
`put` raises ⇒ typed `CramPersistError` (`ROUTER_CRAM_PERSIST_FAILED`).
No decision object is returned to the caller.

### Phantom decision semantics

A **phantom** is any `RouteDecision` handed to the caller without a durable
C-RAM persist ACK for its `op_id`. Cycle 9 acceptance: **0 phantoms / 100**
kill-9 mid-decision trials (binary).

### Queue bound policy (rejected 100/1000)

Bench mix (Cycle 8/9 N=1000, `queue_bound=1000`):

| Reason | Count | Classification |
|--------|------:|----------------|
| `SAFETY_POLICY_BLOCKS_NETWORK` | 50 | **Intentional** — 5% of tasks set `requires_network=True` under deny policy |
| `NO_CAPABLE_NODE` | 50 | **Intentional** — 5% require capability `quantum` (no node) |
| `SATURATION_QUEUE_FULL` | 0 | Bound=1000; inflight never reaches bound in this mix |

**Verdict:** 100/1000 rejected is **100% justified by declared bench policy**, not
a capacity leak. Saturation reject remains the bound policy when
`inflight >= queue_bound`.

### TLS debt (formal)

- **Decision:** accept TLS/auth debt until **Phase 4 Network Fabric**.
- **Expiry:** **2026-12-31**. If Phase 4 has not closed TLS by that date, council
  must re-litigate before further transport expansion.
- Cycle 9 does **not** implement TLS (no silent TLS work).

## P1 — Persist-ack guard

```
compute decision → C-RAM put → ACK → advance RR / log / audit → return
                         ↘ fail → CramPersistError (no RR advance, no return)
```

## P3 — Audit + replay

- `router/audit.py`, `router/trace.py`
- `mesh router replay <trace_id> --store <root>` → byte-identical canonical form

## P6 — Strategy interface (R1 not activated)

- `RoutingStrategy` ABC
- `RoundRobinStrategy` — **live** (R0)
- `CapabilityAwareStrategy` — **STUB only** (`NotImplementedError`)

## Out of scope (still)

R1 active, Phase 4, ML, Raft, N>2, change R0 determinism contract, implement TLS.


## Superseded note (Cycle 10)

`CapabilityAwareStrategy` STUB was replaced by live R1 in Cycle 10 — see `docs/cognitive_router_r1_capability.md` / CP-0014.
