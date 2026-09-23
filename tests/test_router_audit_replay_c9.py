"""Cycle 9 — ChatGPT-named audit/replay tests + CLI replay."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from neural_mesh.router import (
    AuditTrail,
    CognitiveRouterR0,
    DecisionStore,
    RouteCandidate,
    TaskSpec,
    decision_hash,
    replay_from_store,
)

ROOT = Path(__file__).resolve().parents[1]
MESH = [sys.executable, "-m", "neural_mesh.cli"]


def _nodes():
    return [
        RouteCandidate(node_id="n1", capabilities=("compute",)),
        RouteCandidate(node_id="n2", capabilities=("compute",)),
    ]


def test_route_audit_replay(tmp_path: Path):
    store = DecisionStore(tmp_path / "s")
    audit = AuditTrail(tmp_path / "audit.jsonl")
    r = CognitiveRouterR0(
        _nodes(), seed=2, decision_store=store, audit_trail=audit, epoch=1
    )
    d = r.route(TaskSpec(task_id="a1", op_id="op-a1", trace_id="trace-a1"))
    assert len(audit) == 1
    assert audit.by_op_id("op-a1") is not None
    stored, recomputed = replay_from_store(store, "trace-a1")
    assert stored.canonical_bytes() == recomputed.canonical_bytes() == d.canonical_bytes()


def test_trace_id_consistency(tmp_path: Path):
    store = DecisionStore(tmp_path / "s")
    r = CognitiveRouterR0(_nodes(), seed=0, decision_store=store)
    tid = "trace-xyz-99"
    d = r.route(TaskSpec(task_id="t", op_id="op-t", trace_id=tid))
    assert d.trace_id == tid
    env = store.get_envelope_by_trace_id(tid)
    assert env is not None
    assert env["decision"]["trace_id"] == tid


def test_decision_hash_reproducible():
    r = CognitiveRouterR0(_nodes(), seed=7)
    d1 = r.route(TaskSpec(task_id="h", op_id="op-h", trace_id="tr-h"))
    r2 = CognitiveRouterR0(_nodes(), seed=7)
    d2 = r2.route(TaskSpec(task_id="h", op_id="op-h", trace_id="tr-h"))
    assert decision_hash(d1) == decision_hash(d2)


def test_replay_byte_identical(tmp_path: Path):
    store = DecisionStore(tmp_path / "s")
    r = CognitiveRouterR0(_nodes(), seed=4, decision_store=store)
    d = r.route(TaskSpec(task_id="rb", op_id="op-rb", trace_id="tr-rb"))
    stored, recomputed = replay_from_store(store, "tr-rb")
    assert stored.canonical_bytes() == recomputed.canonical_bytes()
    assert decision_hash(stored) == decision_hash(d)


def test_mesh_router_replay_cli(tmp_path: Path):
    from neural_mesh.safety import ensure_default_policy

    ensure_default_policy(tmp_path)
    store_path = tmp_path / "cram"
    # Route via API into store, then CLI replay
    store = DecisionStore(store_path)
    from neural_mesh.twin.simulator import DigitalTwin
    from neural_mesh.router import candidates_from_topology

    twin = DigitalTwin.build_demo(seed=0)
    cands = candidates_from_topology(twin)
    router = CognitiveRouterR0(
        cands, seed=0, policy_root=tmp_path, decision_store=store
    )
    d = router.route(
        TaskSpec(task_id="cli-rep", op_id="op-cli-rep", trace_id="tr-cli-rep")
    )
    assert d.status.value == "ACCEPTED"
    proc = subprocess.run(
        MESH
        + [
            "router",
            "replay",
            "tr-cli-rep",
            "--store",
            str(store_path),
            "--json",
        ],
        cwd=tmp_path,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, proc.stderr + proc.stdout
    data = json.loads(proc.stdout)
    assert data["byte_identical"] is True
    assert data["trace_id"] == "tr-cli-rep"
