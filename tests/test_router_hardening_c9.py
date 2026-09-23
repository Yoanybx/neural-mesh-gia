"""Cycle 9 — R0 Hardening: persist-ack guard, crash frontier, audit, replay."""

from __future__ import annotations

import time
from pathlib import Path

import pytest

from neural_mesh.router import (
    CapabilityAwareStrategy,
    CognitiveRouterR0,
    CramPersistError,
    DecisionStatus,
    DecisionStore,
    RoundRobinStrategy,
    RouteCandidate,
    RoutingStrategy,
    TaskSpec,
    audit_from_decision,
    decision_hash,
    replay_from_store,
    trace_id_consistent,
)
from neural_mesh.router.decision_oop import (
    RemoteDecisionStore,
    kill9,
    spawn_decision_server,
)
from neural_mesh.router.metrics import percentile, summarize_decisions


def _nodes(*ids: str) -> list[RouteCandidate]:
    return [RouteCandidate(node_id=i, capabilities=("compute",)) for i in ids]


def test_persist_ack_required_else_typed_error(tmp_path: Path):
    store = DecisionStore(tmp_path / "dec")
    store.mark_unavailable()
    router = CognitiveRouterR0(
        _nodes("a", "b"), seed=0, decision_store=store, epoch=1
    )
    with pytest.raises(CramPersistError) as ei:
        router.route(TaskSpec(task_id="t1", op_id="op-down-1", trace_id="tr-down-1"))
    assert ei.value.code == "ROUTER_CRAM_PERSIST_FAILED"
    assert store.count() == 0
    # RR must not advance on failed persist
    assert int(getattr(router.strategy, "index", -1)) == 0


def test_no_phantom_when_store_down(tmp_path: Path):
    """Returning a decision without C-RAM ack is forbidden."""
    store = DecisionStore(tmp_path / "dec")
    store.mark_unavailable()
    router = CognitiveRouterR0(_nodes("a"), seed=1, decision_store=store)
    phantoms = 0
    for i in range(20):
        try:
            d = router.route(TaskSpec(task_id=f"p-{i}", op_id=f"op-p-{i}"))
            # If we got here, it must be in the store — else phantom
            if not store.has_op_id(d.op_id):
                phantoms += 1
        except CramPersistError:
            pass
    assert phantoms == 0


def test_router_restart_op_id_idempotent(tmp_path: Path):
    root = tmp_path / "cram"
    store = DecisionStore(root)
    r1 = CognitiveRouterR0(_nodes("a", "b"), seed=3, decision_store=store, epoch=9)
    task = TaskSpec(task_id="idem-rst", op_id="op-rst-1", trace_id="tr-rst-1")
    first = r1.route(task)
    assert first.status == DecisionStatus.ACCEPTED
    assert store.count() == 1
    # "Router restart" — new instance, same durable store
    r2 = CognitiveRouterR0(_nodes("a", "b"), seed=3, decision_store=DecisionStore(root), epoch=9)
    second = r2.route(task)
    assert second.canonical_bytes() == first.canonical_bytes()
    assert DecisionStore(root).count() == 1


def test_kill9_cram_mid_decision_zero_phantoms(tmp_path: Path):
    """100× kill -9 C-RAM mid-put ⇒ 0 phantom decisions (binary)."""
    phantoms = 0
    errors = 0
    persisted_ok = 0
    for i in range(100):
        root = tmp_path / f"oop-{i}"
        sock = tmp_path / f"s-{i}.sock"
        ready = tmp_path / f"ready-{i}"
        if ready.exists():
            ready.unlink()
        proc = spawn_decision_server(root, sock, ready_file=ready, put_delay_ms=40.0)
        store = RemoteDecisionStore(sock, read_timeout=2.0, write_timeout=2.0)
        router = CognitiveRouterR0(
            _nodes("a", "b"), seed=0, decision_store=store, epoch=1
        )
        op_id = f"op-kill-{i}"
        # Kill during the widened put window
        import threading

        def _kill():
            time.sleep(0.015)
            kill9(proc)

        th = threading.Thread(target=_kill, daemon=True)
        th.start()
        returned = None
        try:
            returned = router.route(
                TaskSpec(task_id=f"k-{i}", op_id=op_id, trace_id=f"tr-k-{i}")
            )
        except CramPersistError:
            errors += 1
        th.join(timeout=2)
        kill9(proc)
        # Inspect durable local store after process death
        local = DecisionStore(root)
        in_store = local.has_op_id(op_id)
        if returned is not None and not in_store:
            phantoms += 1
        if returned is not None and in_store:
            persisted_ok += 1
        if returned is None and in_store:
            # Persist completed but ack never returned — not a phantom (caller
            # got ERROR). Idempotent restart must surface the decision.
            restarted = CognitiveRouterR0(
                _nodes("a", "b"),
                seed=0,
                decision_store=DecisionStore(root),
                epoch=1,
            )
            d = restarted.route(
                TaskSpec(task_id=f"k-{i}", op_id=op_id, trace_id=f"tr-k-{i}")
            )
            assert d.op_id == op_id
    assert phantoms == 0, f"phantoms={phantoms} errors={errors} ok={persisted_ok}"


def test_route_audit_replay(tmp_path: Path):
    store = DecisionStore(tmp_path / "dec")
    router = CognitiveRouterR0(
        _nodes("a", "b", "c"), seed=5, decision_store=store, epoch=2
    )
    task = TaskSpec(task_id="aud-1", op_id="op-aud-1", trace_id="tr-aud-1")
    d = router.route(task)
    row = audit_from_decision(d, logical_timestamp=1)
    assert row.task_id == "aud-1"
    assert row.op_id == "op-aud-1"
    assert row.trace_id == "tr-aud-1"
    assert row.epoch == 2
    assert row.policy_hash == d.policy_hash
    assert row.candidates_fingerprint == d.candidates_fingerprint
    assert row.selected_node == d.selected_node_id
    assert row.decision_hash == decision_hash(d)
    stored, recomputed = replay_from_store(store, "tr-aud-1")
    assert stored.canonical_bytes() == recomputed.canonical_bytes()


def test_trace_id_consistency(tmp_path: Path):
    store = DecisionStore(tmp_path / "dec")
    router = CognitiveRouterR0(_nodes("a"), seed=0, decision_store=store)
    task = TaskSpec(task_id="tr-c", op_id="op-trc", trace_id="trace-consistent-1")
    d = router.route(task)
    assert d.trace_id == "trace-consistent-1"
    assert trace_id_consistent(d, task)
    assert router.audit.by_trace_id("trace-consistent-1")


def test_decision_hash_reproducible(tmp_path: Path):
    store = DecisionStore(tmp_path / "dec")
    task = TaskSpec(task_id="dh-1", op_id="op-dh-1", trace_id="tr-dh-1")
    d1 = CognitiveRouterR0(_nodes("a", "b"), seed=9, decision_store=store).route(task)
    # Idempotent second call
    d2 = CognitiveRouterR0(
        _nodes("a", "b"), seed=9, decision_store=DecisionStore(tmp_path / "dec")
    ).route(task)
    assert decision_hash(d1) == decision_hash(d2)
    assert d1.canonical_bytes() == d2.canonical_bytes()


def test_replay_byte_identical(tmp_path: Path):
    store = DecisionStore(tmp_path / "dec")
    router = CognitiveRouterR0(
        _nodes("a", "b", "c"), seed=11, decision_store=store, epoch=4
    )
    # Several accepts so rr_index_before != seed for later decision
    for i in range(3):
        router.route(TaskSpec(task_id=f"warm-{i}", op_id=f"op-warm-{i}", trace_id=f"tr-w-{i}"))
    target = TaskSpec(task_id="tgt", op_id="op-tgt", trace_id="tr-tgt-byte")
    d = router.route(target)
    stored, recomputed = replay_from_store(store, "tr-tgt-byte")
    assert stored.op_id == d.op_id
    assert stored.canonical_bytes() == recomputed.canonical_bytes()
    assert stored.canonical_bytes() == d.canonical_bytes()


def test_rejected_100_of_1000_classified_as_policy():
    """Document/assert bench reject mix is intentional policy, not saturation."""
    cands = _nodes("node-01", "node-02", "node-03")
    # Mirror bench mix without unavailable node (same reject reasons)
    router = CognitiveRouterR0(cands, seed=42, queue_bound=1000)
    decisions = []
    for i in range(1000):
        if i % 20 == 0:
            t = TaskSpec(
                task_id=f"t-{i:04d}",
                required_capabilities=("compute",),
                requires_network=True,
            )
        elif i % 20 == 1:
            t = TaskSpec(
                task_id=f"t-{i:04d}",
                required_capabilities=("quantum",),
            )
        else:
            t = TaskSpec(task_id=f"t-{i:04d}")
        decisions.append(router.route(t))
    summary = summarize_decisions(decisions)
    assert summary["rejected"] == 100
    assert summary["rejected_reasons"].get("SAFETY_POLICY_BLOCKS_NETWORK") == 50
    assert summary["rejected_reasons"].get("NO_CAPABLE_NODE") == 50
    assert "SATURATION_QUEUE_FULL" not in summary["rejected_reasons"]
    # Policy classification marker
    assert summary["reject_rate"] == 0.1


def test_fail_closed_cram_down_p99_under_10ms(tmp_path: Path):
    store = DecisionStore(tmp_path / "dec")
    store.mark_unavailable()
    router = CognitiveRouterR0(_nodes("a", "b"), seed=0, decision_store=store)
    lat: list[float] = []
    for i in range(200):
        t0 = time.perf_counter()
        try:
            router.route(TaskSpec(task_id=f"fc-{i}", op_id=f"op-fc-{i}"))
        except CramPersistError:
            pass
        lat.append((time.perf_counter() - t0) * 1000.0)
    p99 = percentile(lat, 99)
    assert p99 < 10.0, f"fail-closed p99 {p99:.4f}ms >= 10ms"


def test_healthy_store_latency_still_under_5ms(tmp_path: Path):
    store = DecisionStore(tmp_path / "dec")
    router = CognitiveRouterR0(
        _nodes("a", "b", "c"), seed=0, decision_store=store, queue_bound=10_000
    )
    lat: list[float] = []
    for i in range(300):
        t0 = time.perf_counter()
        router.route(TaskSpec(task_id=f"h-{i}", op_id=f"op-h-{i}"))
        lat.append((time.perf_counter() - t0) * 1000.0)
    assert percentile(lat, 99) < 5.0


def test_round_robin_strategy_live_capability_aware_stub_only():
    assert issubclass(RoundRobinStrategy, RoutingStrategy)
    assert issubclass(CapabilityAwareStrategy, RoutingStrategy)
    rr = RoundRobinStrategy(index=0)
    cands = _nodes("a", "b")
    chosen, idx = rr.select(TaskSpec(task_id="x"), cands)
    assert chosen is not None and idx == 0
    stub = CapabilityAwareStrategy()
    assert getattr(stub, "STUB", False) is True
    with pytest.raises(NotImplementedError):
        stub.select(TaskSpec(task_id="x"), cands)
    # Router must not activate stub
    with pytest.raises(NotImplementedError):
        CognitiveRouterR0(
            cands, seed=0, strategy=CapabilityAwareStrategy()
        ).route(TaskSpec(task_id="nope", op_id="op-nope"))


def test_metrics_include_c9_fields(tmp_path: Path):
    store = DecisionStore(tmp_path / "dec")
    router = CognitiveRouterR0(_nodes("a", "b"), seed=0, decision_store=store)
    ds = [
        router.route(TaskSpec(task_id=f"m-{i}", op_id=f"op-m-{i}"))
        for i in range(10)
    ]
    s = summarize_decisions(ds)
    assert "reject_rate" in s
    assert "node_distribution" in s
    assert "queue_time_ms" in s
    assert "policy_changes" in s
    assert "decision_latency_ms" in s
