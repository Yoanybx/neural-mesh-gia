"""P1 JSON topology schema load/save/hash."""

import json
from pathlib import Path

from neural_mesh.twin.schema import Topology, TopologyLink, TopologyNode, Workload
from neural_mesh.twin.simulator import DigitalTwin


def test_topology_chatgpt_schema_roundtrip(tmp_path: Path):
    topo = Topology(
        network_id="test-net-001",
        seed=42,
        nodes=[
            TopologyNode(id="node-01", cpu=8, memory=32000, capabilities=["compute"]),
            TopologyNode(id="node-02", cpu=4, memory=16000, capabilities=["compute"]),
        ],
        links=[
            TopologyLink(
                source="node-01",
                target="node-02",
                latency_ms=5,
                bandwidth_mbps=1000,
            )
        ],
    )
    path = tmp_path / "topology.json"
    topo.save(path)
    loaded = Topology.load(path)
    assert loaded.to_dict() == topo.to_dict()
    assert loaded.hash() == topo.hash()
    raw = json.loads(path.read_text(encoding="utf-8"))
    assert raw["network_id"] == "test-net-001"
    assert raw["nodes"][0]["id"] == "node-01"
    assert "cpu" in raw["nodes"][0]
    assert raw["links"][0]["source"] == "node-01"


def test_topology_hash_stable_and_in_report():
    twin = DigitalTwin.build_demo(seed=42)
    topo = twin.to_topology_model()
    h1 = topo.hash()
    h2 = Topology.from_dict(topo.to_dict()).hash()
    assert h1 == h2
    report = twin.run(ticks=10)
    assert report.topology_hash == h1
    assert report.workload_hash is not None


def test_workload_hash_and_save(tmp_path: Path):
    twin = DigitalTwin.build_demo(seed=42)
    wl = twin.to_workload_model()
    path = tmp_path / "workload.json"
    wl.save(path)
    assert Workload.load(path).hash() == wl.hash()
