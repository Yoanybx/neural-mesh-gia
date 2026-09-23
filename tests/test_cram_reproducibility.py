"""C-RAM reproducibility: same content → same key; placement stable; root stable."""

from pathlib import Path

from neural_mesh.cram import CRAMStore, content_hash
from neural_mesh.cram.hashing import root_hash
from neural_mesh.twin.placement import CRAMPlacement
from neural_mesh.twin.schema import Topology, TopologyNode
from neural_mesh.twin.simulator import DigitalTwin, TwinNode


def test_two_stores_same_content_same_key(tmp_path: Path):
    a = CRAMStore(tmp_path / "a")
    b = CRAMStore(tmp_path / "b")
    payload = b"repro-payload-v1"
    assert a.put(payload) == b.put(payload) == content_hash(payload)


def test_placement_stable_across_topology_reload():
    nodes = [TopologyNode(id=f"node-{i:02d}") for i in range(1, 6)]
    t1 = Topology(network_id="n", seed=7, nodes=list(nodes))
    t2 = Topology(network_id="n", seed=7, nodes=list(reversed(nodes)))
    place = CRAMPlacement()
    key = content_hash(b"place-me")
    assert place.locate(key, t1) == place.locate(key, t2)


def test_placement_accepts_digital_twin_nodes():
    twin = DigitalTwin(seed=1)
    twin.add_node(TwinNode("alpha", cpu_cores=2))
    twin.add_node(TwinNode("beta", cpu_cores=2))
    twin.add_node(TwinNode("gamma", cpu_cores=2))
    place = CRAMPlacement()
    key = content_hash(b"twin-place")
    node = place.locate(key, twin)
    assert node in twin.nodes


def test_root_hash_reproducible_from_keys(tmp_path: Path):
    store = CRAMStore(tmp_path)
    keys = [store.put(f"obj-{i}".encode()) for i in range(5)]
    assert store.compute_root_hash(keys) == root_hash(keys)
    assert store.compute_root_hash(list(reversed(keys))) == root_hash(keys)
