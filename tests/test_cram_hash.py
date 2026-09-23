"""C-RAM hashing determinism tests."""

from neural_mesh.cram.hashing import content_hash, root_hash, shard_dirs
from neural_mesh.twin.placement import CRAMPlacement
from neural_mesh.twin.schema import Topology, TopologyLink, TopologyNode


def test_content_hash_stable():
    assert content_hash(b"abc") == content_hash(b"abc")
    assert content_hash(b"abc") != content_hash(b"abd")
    assert len(content_hash(b"x")) == 64


def test_shard_dirs():
    assert shard_dirs("a91f82deadbeef") == ("a9", "1f82deadbeef")


def test_root_hash_order_independent():
    a = root_hash(["bb", "aa", "cc"])
    b = root_hash(["cc", "aa", "bb"])
    assert a == b
    assert root_hash([]) == content_hash(b"")


def test_placement_deterministic():
    topo = Topology(
        network_id="net-1",
        seed=1,
        nodes=[
            TopologyNode(id="node-01"),
            TopologyNode(id="node-02"),
            TopologyNode(id="node-03"),
        ],
        links=[TopologyLink(source="node-01", target="node-02")],
    )
    place = CRAMPlacement()
    key = "a91f82" + "0" * 58
    n1 = place.locate(key, topo)
    n2 = place.locate(key, topo)
    assert n1 == n2
    assert n1 in {"node-01", "node-02", "node-03"}
