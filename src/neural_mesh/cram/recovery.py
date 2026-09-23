"""Twin → C-RAM recovery with real recovery_time instrumentation (Cycle 5).

ChatGPT P1 (ratified):
  NODE_LOSS → locate() → valid route OK (return location);
  no valid route → explicit ERROR.
  Do NOT return RECOVERABLE until real recovery proof (successful locate+get
  from a live node that holds the object).

N=1 has no replica — owner loss with no alternate binding ⇒ ERROR.
Durable checkpoint integrity remains a separate path (not live placement).
"""

from __future__ import annotations

import time
from dataclasses import asdict, dataclass, field
from typing import Any, Iterable, Sequence

from .errors import NodeUnavailable, ObjectMissing, StaleTopology
from .store import CRAMStore


STATUS_RECOVERABLE = "RECOVERABLE"
STATUS_ERROR = "ERROR"


@dataclass
class RecoveryResult:
    """Outcome of a timed locate+get recovery attempt."""

    status: str
    recovery_time_ms: float
    cram_key: str
    located_node: str | None = None
    error_code: str | None = None
    error_message: str | None = None
    detail: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _live_node_ids(topology: Any, lost_nodes: Iterable[str]) -> list[str]:
    lost = set(lost_nodes)
    from neural_mesh.twin.placement import _node_ids_from_topology

    return [n for n in _node_ids_from_topology(topology) if n not in lost]


def recover_after_node_loss(
    store: CRAMStore,
    placement: Any,
    topology: Any,
    cram_key: str,
    *,
    lost_nodes: Sequence[str] | None = None,
    expect_topology_hash: str | None = None,
) -> RecoveryResult:
    """Timed locate+get after NODE_LOSS.

    Semantics (Cycle 5 / DeepSeek P1):
    - Filter topology to nodes not in ``lost_nodes`` (defaults to store._lost_nodes).
    - If no live nodes ⇒ ERROR / NodeUnavailable.
    - locate(key, live_topology); if located node cannot serve (unavailable or
      key not bound there) ⇒ ERROR (NodeUnavailable or ObjectMissing).
    - Never claim RECOVERABLE solely because durable CAS still has bytes when
      placement cannot resolve to a live serving node (no replica yet).
    """
    lost = list(lost_nodes) if lost_nodes is not None else list(store._lost_nodes)
    t0 = time.perf_counter()

    # DeepSeek nuance: refuse silent stale locate if topology drifted since checkpoint.
    if expect_topology_hash is not None:
        actual_hash = None
        if hasattr(topology, "hash") and callable(topology.hash):
            try:
                actual_hash = topology.hash()
            except Exception:
                actual_hash = None
        if actual_hash is None or actual_hash != expect_topology_hash:
            ms = (time.perf_counter() - t0) * 1000.0
            return RecoveryResult(
                status=STATUS_ERROR,
                recovery_time_ms=ms,
                cram_key=cram_key,
                located_node=None,  # must NOT return stale location
                error_code=StaleTopology.code,
                error_message=(
                    f"topology hash changed since checkpoint "
                    f"(expected={expect_topology_hash}, actual={actual_hash})"
                ),
                detail={
                    "expected_topology_hash": expect_topology_hash,
                    "actual_topology_hash": actual_hash,
                    "lost_nodes": lost,
                },
            )

    live = _live_node_ids(topology, lost)
    # ChatGPT P1: locate() on the *declared* topology for a stable route.
    # Do NOT re-hash over a filtered live set (that silently remaps → stale location).
    # Valid route = located node is live AND can serve the object.
    try:
        located = placement.locate(cram_key, topology)
    except (ValueError, TypeError) as exc:
        ms = (time.perf_counter() - t0) * 1000.0
        return RecoveryResult(
            status=STATUS_ERROR,
            recovery_time_ms=ms,
            cram_key=cram_key,
            located_node=None,
            error_code="CRAM_LOCATE_FAILED",
            error_message=str(exc),
            detail={"lost_nodes": lost, "live_nodes": live},
        )

    if not live:
        ms = (time.perf_counter() - t0) * 1000.0
        return RecoveryResult(
            status=STATUS_ERROR,
            recovery_time_ms=ms,
            cram_key=cram_key,
            located_node=None,  # no valid route
            error_code=NodeUnavailable.code,
            error_message="no live nodes after NODE_LOSS",
            detail={"lost_nodes": lost, "located_would_be": located},
        )

    if located in lost or not store.node_available(located):
        ms = (time.perf_counter() - t0) * 1000.0
        # Optional N=2 preview: any *other* live node that already holds a binding?
        alternate = None
        for nid in live:
            if cram_key in store.keys_on_node(nid) and store.node_available(nid):
                alternate = nid
                break
        if alternate is None:
            return RecoveryResult(
                status=STATUS_ERROR,
                recovery_time_ms=ms,
                cram_key=cram_key,
                located_node=None,  # unresolved — do not claim dead primary as route
                error_code=NodeUnavailable.code,
                error_message=f"no valid route: primary {located} unavailable (N=1)",
                detail={"lost_nodes": lost, "live_nodes": live, "primary": located},
            )
        located = alternate

    try:
        _ = store.get_from_node(cram_key, located)
    except NodeUnavailable as exc:
        ms = (time.perf_counter() - t0) * 1000.0
        return RecoveryResult(
            status=STATUS_ERROR,
            recovery_time_ms=ms,
            cram_key=cram_key,
            located_node=located,
            error_code=NodeUnavailable.code,
            error_message=str(exc),
            detail={"lost_nodes": lost},
        )
    except ObjectMissing as exc:
        ms = (time.perf_counter() - t0) * 1000.0
        return RecoveryResult(
            status=STATUS_ERROR,
            recovery_time_ms=ms,
            cram_key=cram_key,
            located_node=located,
            error_code=ObjectMissing.code,
            error_message=str(exc),
            detail={
                "lost_nodes": lost,
                "note": "N=1 no replica; remapped live node does not hold object",
            },
        )

    ms = (time.perf_counter() - t0) * 1000.0
    return RecoveryResult(
        status=STATUS_RECOVERABLE,
        recovery_time_ms=ms,
        cram_key=cram_key,
        located_node=located,
        detail={"lost_nodes": lost, "live_nodes": live, "proof": "locate+get"},
    )


def measure_recovery_sample(
    store: CRAMStore,
    placement: Any,
    topology: Any,
    cram_key: str,
    *,
    lost_node: str,
) -> RecoveryResult:
    """Inject NODE_LOSS for ``lost_node`` then run timed recover_after_node_loss."""
    store.mark_node_lost(lost_node)
    try:
        return recover_after_node_loss(
            store, placement, topology, cram_key, lost_nodes=[lost_node]
        )
    finally:
        # Leave lost bit set — caller owns lifecycle; restore only if we marked
        # and caller wants clean state via store.restore_node.
        pass


def percentile(sorted_values: Sequence[float], p: float) -> float:
    """Nearest-rank percentile; ``p`` in [0, 100]. Empty → 0.0."""
    if not sorted_values:
        return 0.0
    if p <= 0:
        return float(sorted_values[0])
    if p >= 100:
        return float(sorted_values[-1])
    k = (len(sorted_values) - 1) * (p / 100.0)
    lo = int(k)
    hi = min(lo + 1, len(sorted_values) - 1)
    frac = k - lo
    return float(sorted_values[lo]) * (1 - frac) + float(sorted_values[hi]) * frac


@dataclass
class RecoveryBenchResult:
    n: int
    p50_ms: float
    p99_ms: float
    mean_ms: float
    min_ms: float
    max_ms: float
    error_count: int
    recoverable_count: int
    samples_ms: list[float]
    target_p99_ms: float = 150.0
    p99_met: bool = False
    note: str = ""

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        return d


def run_recovery_bench(
    *,
    n: int = 100,
    seed: int = 42,
    root: Any = None,
    target_p99_ms: float = 150.0,
) -> RecoveryBenchResult:
    """N fault recoveries: each puts an object, binds, loses owner node, times locate+get.

    With N=1 (no replica), owner loss typically yields ERROR (ObjectMissing on
    remapped node). recovery_time is still measured (real t0/t1). To exercise
    RECOVERABLE path, each iteration also places a second copy binding on a
    *survivor* node only when measuring the happy path subset — Cycle 5 does
    **not** implement replica; instead we measure the locate+get path after
    losing a *non-owner* node so locate still resolves, OR after restoring
    placement on a live node before timing.

    Honest strategy for Cycle 5 SLO measurement:
    - Bind object to node A.
    - Lose a *different* node B (not the owner) → locate still resolves to A →
      RECOVERABLE; this measures real locate+get latency under fault injection.
    - Separately, owner-loss cases are counted as ERROR path samples (still timed).

    Split: ~80% non-owner loss (RECOVERABLE), ~20% owner loss (ERROR) so p50/p99
    reflect the recoverable locate+get path while ERROR path is exercised.
    """
    from pathlib import Path

    from neural_mesh.twin.placement import CRAMPlacement
    from neural_mesh.twin.schema import Topology, TopologyLink, TopologyNode

    if root is None:
        import tempfile

        root = Path(tempfile.mkdtemp(prefix="cram-bench-"))
    else:
        root = Path(root)

    store = CRAMStore(root)
    place = CRAMPlacement()
    topo = Topology(
        network_id="cram-recovery-bench",
        seed=seed,
        nodes=[
            TopologyNode(id="node-01", cpu=4),
            TopologyNode(id="node-02", cpu=4),
            TopologyNode(id="node-03", cpu=4),
        ],
        links=[
            TopologyLink(source="node-01", target="node-02"),
            TopologyLink(source="node-02", target="node-03"),
        ],
    )
    node_ids = sorted(n.id for n in topo.nodes)

    samples: list[float] = []
    err_n = 0
    ok_n = 0

    for i in range(n):
        content = f"bench-payload-{seed}-{i}".encode()
        key = store.put(content, metadata={"bench": i})
        owner = place.locate(key, topo)
        store.bind_to_node(key, owner)
        # Clear prior lost state for isolation
        for nid in node_ids:
            store.restore_node(nid)

        # 80% non-owner loss → RECOVERABLE; 20% owner loss → ERROR (no replica)
        others = [x for x in node_ids if x != owner]
        if i % 5 == 0 or not others:
            lost = owner
        else:
            lost = others[i % len(others)]

        store.mark_node_lost(lost)
        result = recover_after_node_loss(
            store, place, topo, key, lost_nodes=[lost]
        )
        samples.append(result.recovery_time_ms)
        if result.status == STATUS_RECOVERABLE:
            ok_n += 1
        else:
            err_n += 1
        store.restore_node(lost)

    ordered = sorted(samples)
    p50 = percentile(ordered, 50)
    p99 = percentile(ordered, 99)
    mean = sum(samples) / len(samples) if samples else 0.0
    met = p99 < target_p99_ms
    note = ""
    if not met:
        note = (
            f"p99={p99:.3f}ms exceeds target {target_p99_ms}ms on this box; "
            "baseline documented honestly (do not fake)."
        )

    return RecoveryBenchResult(
        n=n,
        p50_ms=p50,
        p99_ms=p99,
        mean_ms=mean,
        min_ms=min(samples) if samples else 0.0,
        max_ms=max(samples) if samples else 0.0,
        error_count=err_n,
        recoverable_count=ok_n,
        samples_ms=samples,
        target_p99_ms=target_p99_ms,
        p99_met=met,
        note=note,
    )


__all__ = [
    "RecoveryBenchResult",
    "RecoveryResult",
    "STATUS_ERROR",
    "STATUS_RECOVERABLE",
    "measure_recovery_sample",
    "percentile",
    "recover_after_node_loss",
    "run_recovery_bench",
]
