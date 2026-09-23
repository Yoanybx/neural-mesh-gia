"""DeepSeek Cycle 8 acceptance — determinism, safety fail-closed, C-RAM idempotency."""

from __future__ import annotations

import time
from pathlib import Path

import pytest

from neural_mesh.router import (
    CognitiveRouterR0,
    DecisionStatus,
    DecisionStore,
    NodeAvailability,
    RouteCandidate,
    TaskSpec,
    UnknownPolicy,
    normalize_policy,
    policy_hash,
)
from neural_mesh.router.metrics import percentile


def _nodes(*ids: str) -> list[RouteCandidate]:
    return [
        RouteCandidate(node_id=i, capabilities=("compute",)) for i in ids
    ]


def test_1000_runs_byte_identical_zero_divergences():
    """1000 identical runs → 0 byte divergences on canonical RouteDecision."""
    cands = _nodes("a", "b", "c")
    task = TaskSpec(task_id="det-1", op_id="op-det-1", trace_id="tr-det-1")
    seed = 42
    policy = {
        "policy_schema_version": 1,
        "allow_network_actions": False,
        "allow_physical_actions": False,
        "require_human_approval": True,
    }
    baseline = CognitiveRouterR0(cands, seed=seed, policy=policy).route(task)
    base = baseline.canonical_bytes()
    divergences = 0
    for _ in range(1000):
        d = CognitiveRouterR0(cands, seed=seed, policy=policy).route(task)
        if d.canonical_bytes() != base:
            divergences += 1
    assert divergences == 0
    assert baseline.policy_hash == policy_hash(policy)
    assert baseline.op_id == "op-det-1"
    assert baseline.trace_id == "tr-det-1"


@pytest.mark.parametrize(
    "case_id,policy,task_kwargs,expect_reason",
    [
        (
            "network_denied",
            {
                "policy_schema_version": 1,
                "allow_network_actions": False,
                "allow_physical_actions": False,
                "require_human_approval": True,
            },
            {"requires_network": True},
            "SAFETY_POLICY_BLOCKS_NETWORK",
        ),
        (
            "physical_denied",
            {
                "policy_schema_version": 1,
                "allow_network_actions": False,
                "allow_physical_actions": False,
                "require_human_approval": True,
            },
            {"requires_physical": True},
            "SAFETY_POLICY_BLOCKS_PHYSICAL",
        ),
        (
            "unknown_policy_key",
            {
                "policy_schema_version": 1,
                "allow_network_actions": False,
                "allow_physical_actions": False,
                "require_human_approval": True,
                "allow_exfiltration": True,  # unknown
            },
            {},
            "UNKNOWN_POLICY",
        ),
        (
            "unknown_policy_version",
            {
                "policy_schema_version": 99,
                "allow_network_actions": False,
                "allow_physical_actions": False,
                "require_human_approval": True,
            },
            {},
            "UNKNOWN_POLICY",
        ),
        (
            "no_capable",
            {
                "policy_schema_version": 1,
                "allow_network_actions": False,
                "allow_physical_actions": False,
                "require_human_approval": True,
            },
            {"required_capabilities": ("quantum",)},
            "NO_CAPABLE_NODE",
        ),
        (
            "all_unavailable",
            {
                "policy_schema_version": 1,
                "allow_network_actions": False,
                "allow_physical_actions": False,
                "require_human_approval": True,
            },
            {},
            "NO_CAPABLE_NODE",
        ),
        (
            "network_and_unknown_key",
            {
                "policy_schema_version": 1,
                "allow_network_actions": True,
                "allow_physical_actions": False,
                "require_human_approval": True,
                "extra_flag": 1,
            },
            {"requires_network": True},
            "UNKNOWN_POLICY",  # unknown wins — fail-closed before allow
        ),
        (
            "invalid_version_type",
            {
                "policy_schema_version": "not-an-int",
                "allow_network_actions": False,
                "allow_physical_actions": False,
                "require_human_approval": True,
            },
            {},
            "UNKNOWN_POLICY",
        ),
    ],
)
def test_safety_fail_closed_cases(case_id, policy, task_kwargs, expect_reason):
    if case_id == "all_unavailable":
        cands = [
            RouteCandidate(
                node_id="x",
                capabilities=("compute",),
                status=NodeAvailability.UNAVAILABLE,
            )
        ]
    else:
        cands = _nodes("n1", "n2")
    router = CognitiveRouterR0(cands, seed=0, policy=policy)
    task = TaskSpec(task_id=f"safe-{case_id}", **task_kwargs)
    d = router.route(task)
    assert d.status == DecisionStatus.REJECTED
    assert d.reason == expect_reason
    assert d.selected_node_id is None  # never silent fallback


def test_unknown_policy_normalize_raises():
    with pytest.raises(UnknownPolicy):
        normalize_policy({"policy_schema_version": 1, "weird": True})


def test_idempotent_op_id_100_retries_one_decision(tmp_path: Path):
    store = DecisionStore(tmp_path / "decisions")
    router = CognitiveRouterR0(
        _nodes("a", "b"),
        seed=7,
        decision_store=store,
        epoch=3,
    )
    task = TaskSpec(task_id="idem-1", op_id="op-idem-1", trace_id="tr-1")
    first = router.route(task)
    assert first.status == DecisionStatus.ACCEPTED
    assert first.epoch == 3
    assert store.count() == 1
    nodes = {first.selected_node_id}
    for _ in range(99):
        d = router.route(task)
        assert d.op_id == "op-idem-1"
        assert d.canonical_bytes() == first.canonical_bytes()
        nodes.add(d.selected_node_id)
    assert store.count() == 1
    assert store.op_ids() == ["op-idem-1"]
    # RR cursor must not advance on retries — still one logical decision.
    assert len(nodes) == 1


def test_routing_p99_under_5ms_inprocess():
    router = CognitiveRouterR0(_nodes("a", "b", "c"), seed=0, queue_bound=10_000)
    lat: list[float] = []
    for i in range(1000):
        t0 = time.perf_counter()
        router.route(TaskSpec(task_id=f"lat-{i}", op_id=f"op-lat-{i}"))
        lat.append((time.perf_counter() - t0) * 1000.0)
    p99 = percentile(lat, 99)
    assert p99 < 5.0, f"routing p99 {p99:.4f}ms >= 5ms"


def test_decision_persisted_cram_op_id_epoch_trace(tmp_path: Path):
    store = DecisionStore(tmp_path / "cram-dec")
    router = CognitiveRouterR0(
        _nodes("a"), seed=1, decision_store=store, epoch=5
    )
    d = router.route(
        TaskSpec(task_id="p1", op_id="op-p1", trace_id="trace-p1")
    )
    loaded = store.get_by_op_id("op-p1")
    assert loaded is not None
    assert loaded.op_id == "op-p1"
    assert loaded.epoch == 5
    assert loaded.trace_id == "trace-p1"
    assert loaded.policy_hash == d.policy_hash
    assert loaded.canonical_bytes() == d.canonical_bytes()


def test_saturation_queue_full_rejects(tmp_path: Path):
    router = CognitiveRouterR0(
        _nodes("a", "b"),
        seed=0,
        queue_bound=2,
        decision_store=DecisionStore(tmp_path / "sat"),
    )
    d0 = router.route(TaskSpec(task_id="s0", op_id="op-s0"))
    d1 = router.route(TaskSpec(task_id="s1", op_id="op-s1"))
    assert d0.status == DecisionStatus.ACCEPTED
    assert d1.status == DecisionStatus.ACCEPTED
    d2 = router.route(TaskSpec(task_id="s2", op_id="op-s2"))
    assert d2.status == DecisionStatus.REJECTED
    assert d2.reason == "SATURATION_QUEUE_FULL"
    assert d2.selected_node_id is None
    # complete frees a slot
    router.complete("op-s0")
    d3 = router.route(TaskSpec(task_id="s3", op_id="op-s3"))
    assert d3.status == DecisionStatus.ACCEPTED


def test_policy_hash_stable_and_in_decision():
    policy = {
        "policy_schema_version": 1,
        "allow_network_actions": False,
        "allow_physical_actions": False,
        "require_human_approval": True,
    }
    h1 = policy_hash(policy)
    h2 = policy_hash(dict(policy))
    assert h1 == h2
    d = CognitiveRouterR0(_nodes("a"), seed=0, policy=policy).route(
        TaskSpec(task_id="ph")
    )
    assert d.policy_hash == h1
