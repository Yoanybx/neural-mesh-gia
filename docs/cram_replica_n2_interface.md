# C-RAM Replica N=2 — Interface Only (Cycle 5 / P6)

**Status:** Signature / documentation only. **No active replica code** in Cycle 5.
**Unlocks:** Cycle 6+ implementation after council APROBADO on Cycle 5.

## Purpose

Describe the minimum API surface for a two-copy mirror of selected C-RAM keys so that
`NODE_LOSS` of one placement node can still resolve `locate()` to a live peer and
complete real recovery proof (`get` from the surviving replica).

## Proposed types (not implemented)

```python
from typing import Protocol, Sequence

class ReplicaPlan(Protocol):
    """Deterministic N=2 placement plan for a content key."""

    def primary(self, cram_key: str, topology) -> str:
        """Primary node id (same rule as CRAMPlacement.locate today)."""
        ...

    def secondary(self, cram_key: str, topology) -> str:
        """Mirror node id ≠ primary; stable under node-set permutation rules TBD."""
        ...

    def replicas(self, cram_key: str, topology) -> Sequence[str]:
        """Return (primary, secondary). Length always 2 when topology has ≥2 live nodes."""
        ...


class ReplicaStore(Protocol):
    """Put/get that maintains N=2 bindings. Cycle 6 implements; Cycle 5 does not."""

    def put_replicated(self, content: bytes, *, topology) -> str:
        """CAS put + bind primary and secondary. Returns content hash."""
        ...

    def get_replicated(self, cram_key: str, *, topology, lost_nodes: Sequence[str] = ()) -> bytes:
        """locate among live replicas; raise NodeUnavailable / ObjectMissing typed errors."""
        ...

    def repair(self, cram_key: str, *, topology) -> dict:
        """Re-mirror if only one live copy remains. Returns status dict."""
        ...
```

## Recovery contract (Cycle 6 target)

1. `NODE_LOSS(node)` → filter live topology.
2. `locate` / replica plan → if **no valid route** among live replicas ⇒ **ERROR**
   (`NodeUnavailable` or `ObjectMissing`).
3. If valid route ⇒ return **location**; **RECOVERABLE** only after successful `get`
   (real recovery proof). Never optimistic RECOVERABLE.

## Explicit non-goals (Cycle 5)

- No Raft/Paxos/quorum consensus.
- No automatic background repair loop.
- No change to CAS content identity (SHA-256 of raw bytes).
- No Phase 3 Cognitive Router dependency.

## Acceptance when Cycle 6 starts

- Implement `ReplicaPlan` + `ReplicaStore` behind feature flag / explicit API.
- Bench: owner loss with N=2 ⇒ p99 recovery_time still measured; status RECOVERABLE
  with proof.
- Existing N=1 ERROR-on-owner-loss tests remain valid when replication is disabled.
