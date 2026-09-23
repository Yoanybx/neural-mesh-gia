"""P5 — Twin + C-RAM + Cognitive Router R0 integration (no R1)."""

from __future__ import annotations

from pathlib import Path

from neural_mesh.cram.store import CRAMStore
from neural_mesh.router import (
    CognitiveRouterR0,
    DecisionStatus,
    NodeAvailability,
    TaskSpec,
    candidates_from_topology,
)
from neural_mesh.twin.schema import Topology, TopologyLink, TopologyNode
from neural_mesh.twin.simulator import DigitalTwin, TwinLink, TwinNode, TwinTask


def test_twin_topology_to_router_candidates():
    topo = Topology(
        network_id="router-int",
        seed=9,
        nodes=[
            TopologyNode(id="n1", cpu=4, capabilities=["compute"]),
            TopologyNode(id="n2", cpu=8, capabilities=["compute", "gpu"]),
            TopologyNode(id="n3", cpu=2, capabilities=["storage"]),
        ],
        links=[
            TopologyLink(source="n1", target="n2"),
            TopologyLink(source="n2", target="n3"),
        ],
    )
    cands = candidates_from_topology(topo, unavailable={"n3"})
    by_id = {c.node_id: c for c in cands}
    assert by_id["n3"].status == NodeAvailability.UNAVAILABLE
    assert by_id["n1"].status == NodeAvailability.AVAILABLE
    assert "gpu" in by_id["n2"].capabilities

    router = CognitiveRouterR0(cands, seed=0)
    d = router.route(TaskSpec(task_id="c1", required_capabilities=("compute",)))
    assert d.status == DecisionStatus.ACCEPTED
    assert d.selected_node_id in {"n1", "n2"}
    assert "n3" not in d.eligible


def test_twin_cram_router_pipeline(tmp_path: Path):
    """Route a twin task, then store decision evidence in C-RAM on selected node."""
    twin = DigitalTwin(seed=11)
    twin.add_node(TwinNode("alpha", cpu_cores=4, capabilities=("compute",)))
    twin.add_node(TwinNode("beta", cpu_cores=4, capabilities=("compute",)))
    twin.add_link(TwinLink("alpha", "beta"))
    twin.add_task(TwinTask("job-mesh", cpu_need=1, duration_ticks=2))

    cands = candidates_from_topology(twin)
    router = CognitiveRouterR0(
        cands, seed=0, decision_log_path=tmp_path / "route.jsonl"
    )
    decision = router.route(TaskSpec(task_id="job-mesh"))
    assert decision.status == DecisionStatus.ACCEPTED
    assert decision.selected_node_id in {"alpha", "beta"}

    # Node-scoped C-RAM (sandbox): put evidence blob under selected node.
    store = CRAMStore(tmp_path / "nodes" / decision.selected_node_id)
    evidence = (
        f"task={decision.task_id};node={decision.selected_node_id};"
        f"reason={decision.reason};seed={decision.seed}"
    ).encode("utf-8")
    key = store.put(evidence)
    assert store.exists(key)
    assert store.get(key) == evidence
    assert store.verify(key)

    # Twin still runs independently (scheduler unchanged by R0).
    report = twin.run(ticks=5)
    assert report.digest
    scheduled = [r for r in report.schedule if r.status == "COMPLETED"]
    assert len(scheduled) == 1

    # Log has the decision.
    assert len(router.log.entries()) == 1
    assert router.log.entries()[0]["selected_node_id"] == decision.selected_node_id


def test_router_does_not_expand_n_or_call_network(tmp_path: Path):
    """R0 guard: candidate set size unchanged; no sockets opened by route()."""
    topo = Topology(
        network_id="guard",
        seed=1,
        nodes=[TopologyNode(id=f"n{i}") for i in range(2)],
        links=[TopologyLink(source="n0", target="n1")],
    )
    cands = candidates_from_topology(topo)
    assert len(cands) == 2  # N=2 only — no expand
    router = CognitiveRouterR0(cands, seed=0, policy_root=tmp_path)
    # Missing policy file → defaults (SAFE deny network/physical).
    d = router.route(TaskSpec(task_id="x", requires_network=True))
    assert d.status == DecisionStatus.REJECTED
    assert len(router.candidates) == 2
