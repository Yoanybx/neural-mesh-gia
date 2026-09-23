"""Cycle 8 — Cognitive Router R0 mandatory acceptance tests."""

from __future__ import annotations

import json
from pathlib import Path

from neural_mesh.router import (
    CognitiveRouterR0,
    DecisionLog,
    DecisionStatus,
    NodeAvailability,
    RouteCandidate,
    TaskSpec,
)


def _three_compute(**kwargs) -> list[RouteCandidate]:
    return [
        RouteCandidate(node_id="node-a", capabilities=("compute",), **kwargs),
        RouteCandidate(node_id="node-b", capabilities=("compute",), **kwargs),
        RouteCandidate(node_id="node-c", capabilities=("compute",), **kwargs),
    ]


def test_round_robin_deterministic():
    router = CognitiveRouterR0(_three_compute(), seed=0)
    tasks = [TaskSpec(task_id=f"t{i}") for i in range(6)]
    decisions = router.route_many(tasks)
    selected = [d.selected_node_id for d in decisions]
    assert all(d.status == DecisionStatus.ACCEPTED for d in decisions)
    assert all(d.reason == "ROUND_ROBIN" for d in decisions)
    # Lexicographic eligible: a,b,c — seed 0 → a,b,c,a,b,c
    assert selected == [
        "node-a",
        "node-b",
        "node-c",
        "node-a",
        "node-b",
        "node-c",
    ]


def test_unavailable_node_excluded():
    cands = _three_compute()
    cands[1] = RouteCandidate(
        node_id="node-b",
        capabilities=("compute",),
        status=NodeAvailability.UNAVAILABLE,
    )
    router = CognitiveRouterR0(cands, seed=0)
    decisions = router.route_many([TaskSpec(task_id=f"t{i}") for i in range(4)])
    selected = [d.selected_node_id for d in decisions]
    assert "node-b" not in selected
    assert selected == ["node-a", "node-c", "node-a", "node-c"]
    for d in decisions:
        assert any(e["reason"] == "UNAVAILABLE" for e in d.excluded)


def test_no_capable_node_returns_error():
    cands = [
        RouteCandidate(
            node_id="gpu-only",
            capabilities=("gpu",),
            status=NodeAvailability.AVAILABLE,
        ),
        RouteCandidate(
            node_id="down",
            capabilities=("compute",),
            status=NodeAvailability.UNAVAILABLE,
        ),
    ]
    router = CognitiveRouterR0(cands, seed=1)
    d = router.route(TaskSpec(task_id="need-compute", required_capabilities=("compute",)))
    assert d.status == DecisionStatus.REJECTED
    assert d.reason == "NO_CAPABLE_NODE"
    assert d.selected_node_id is None
    assert d.eligible == []


def test_safety_policy_blocks_execution(tmp_path: Path):
    policy = {
        "allow_network_actions": False,
        "allow_physical_actions": False,
        "require_human_approval": True,
    }
    router = CognitiveRouterR0(_three_compute(), seed=0, policy=policy)
    net = router.route(
        TaskSpec(task_id="net-1", requires_network=True, required_capabilities=("compute",))
    )
    assert net.status == DecisionStatus.REJECTED
    assert net.reason == "SAFETY_POLICY_BLOCKS_NETWORK"
    assert net.selected_node_id is None

    phys = router.route(
        TaskSpec(task_id="phys-1", requires_physical=True, required_capabilities=("compute",))
    )
    assert phys.status == DecisionStatus.REJECTED
    assert phys.reason == "SAFETY_POLICY_BLOCKS_PHYSICAL"

    # Soft task still routes — router itself never opens sockets / actuators.
    ok = router.route(TaskSpec(task_id="local-1"))
    assert ok.status == DecisionStatus.ACCEPTED

    # Persist policy file path style also respected via policy_root.
    from neural_mesh.safety import ensure_default_policy

    ensure_default_policy(tmp_path)
    r2 = CognitiveRouterR0(_three_compute(), seed=0, policy_root=tmp_path)
    blocked = r2.route(TaskSpec(task_id="net-2", requires_network=True))
    assert blocked.reason == "SAFETY_POLICY_BLOCKS_NETWORK"


def test_route_decision_has_reason():
    router = CognitiveRouterR0(_three_compute(), seed=7)
    d = router.route(TaskSpec(task_id="r1"))
    assert d.reason
    assert d.reason == "ROUND_ROBIN"
    assert "decision_latency_ms" in d.metrics
    assert d.metrics["router_version"] == "R0"
    assert d.seed == 7
    payload = d.to_dict()
    assert payload["reason"] == "ROUND_ROBIN"
    assert payload["status"] == "ACCEPTED"


def test_route_reproducibility():
    tasks = [TaskSpec(task_id=f"job-{i}", required_capabilities=("compute",)) for i in range(20)]
    cands = _three_compute()
    a = CognitiveRouterR0(cands, seed=42)
    b = CognitiveRouterR0(list(cands), seed=42)
    da = [d.to_dict() for d in a.route_many(tasks)]
    db = [d.to_dict() for d in b.route_many(tasks)]

    def scrub(rows):
        out = []
        for r in rows:
            r = dict(r)
            r.pop("timestamp", None)
            m = dict(r.get("metrics") or {})
            m.pop("decision_latency_ms", None)
            r["metrics"] = m
            out.append(r)
        return out

    assert scrub(da) == scrub(db)
    # Different seed → different RR start offset (fresh routers).
    a2 = CognitiveRouterR0(cands, seed=42)
    c2 = CognitiveRouterR0(cands, seed=43)
    assert [d.selected_node_id for d in a2.route_many(tasks)] != [
        d.selected_node_id for d in c2.route_many(tasks)
    ]


def test_decision_log_persists(tmp_path: Path):
    log_path = tmp_path / "decisions.jsonl"
    router = CognitiveRouterR0(
        _three_compute(), seed=0, decision_log=DecisionLog(log_path)
    )
    router.route(TaskSpec(task_id="logged"))
    router.route(TaskSpec(task_id="blocked", requires_network=True))
    lines = log_path.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 2
    rows = [json.loads(x) for x in lines]
    assert rows[0]["status"] == "ACCEPTED"
    assert rows[1]["status"] == "REJECTED"
    assert len(router.log) == 2


def test_seed_offsets_rr_start():
    router = CognitiveRouterR0(_three_compute(), seed=1)
    d = router.route(TaskSpec(task_id="first"))
    # seed=1 → index 1 % 3 → node-b
    assert d.selected_node_id == "node-b"


def test_taskspec_validation_roundtrip():
    raw = {
        "task_id": "tv-1",
        "required_capabilities": ["compute", "gpu"],
        "objective": "train",
        "priority": 3,
        "resource_requirements": {"cpu": 2},
        "safety_level": "strict",
        "state_refs": ["hash:abc"],
        "requires_network": False,
    }
    spec = TaskSpec.from_dict(raw)
    assert spec.task_id == "tv-1"
    assert spec.required_capabilities == ("compute", "gpu")
    assert spec.priority == 3
    assert spec.state_refs == ("hash:abc",)
    assert TaskSpec.from_dict(spec.to_dict()).to_dict() == spec.to_dict()


def test_route_decision_schema():
    router = CognitiveRouterR0(_three_compute(), seed=0)
    d = router.route(TaskSpec(task_id="schema-1"))
    payload = d.to_dict()
    for key in (
        "task_id",
        "status",
        "reason",
        "selected_node_id",
        "candidates_considered",
        "eligible",
        "excluded",
        "metrics",
        "seed",
        "timestamp",
    ):
        assert key in payload
    assert payload["status"] == "ACCEPTED"
    assert isinstance(payload["metrics"]["decision_latency_ms"], float)


def test_explain_decision_shape():
    from neural_mesh.router import explain_decision

    router = CognitiveRouterR0(_three_compute(), seed=0)
    d = router.route(TaskSpec(task_id="ex-1"))
    exp = explain_decision(d)
    assert exp["task_id"] == "ex-1"
    assert exp["decision"] == d.selected_node_id
    assert exp["strategy"] == "ROUND_ROBIN"
    assert "excluded_nodes" in exp
