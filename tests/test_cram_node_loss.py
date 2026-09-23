"""P4 NODE_LOSS: node-local get fails; durable store + checkpoint → RECOVERABLE."""

from pathlib import Path

from neural_mesh.checkpoint import CheckpointManager
from neural_mesh.cram import CRAMNodeUnavailable, CRAMStore, ObjectType
from neural_mesh.cram.hashing import root_hash
from neural_mesh.twin.placement import CRAMPlacement
from neural_mesh.twin.schema import Topology, TopologyLink, TopologyNode


def _demo_topology() -> Topology:
    return Topology(
        network_id="cram-fault-net",
        seed=42,
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


def test_node_loss_then_recoverable_from_checkpoint(tmp_path: Path):
    store = CRAMStore(tmp_path)
    topo = _demo_topology()
    place = CRAMPlacement()

    content = b'{"task":"t1","status":"STATE"}'
    obj = store.put_object(content, ObjectType.STATE, metadata={"role": "task-state"})
    node_a = place.locate(obj.content_hash, topo)
    store.bind_to_node(obj.content_hash, node_a)

    # BEFORE: node-local get works
    assert store.get_from_node(obj.content_hash, node_a) == content

    objects = [obj.content_hash]
    rh = root_hash(objects)
    mgr = CheckpointManager(tmp_path)
    cp = mgr.create(
        phase=2,
        module="cram",
        reason="pre NODE_LOSS seal",
        next_action="inject NODE_LOSS then recover",
        cram_root_hash=rh,
        cram_objects=objects,
        status="VERIFIED",
    )
    assert mgr.verify(cp.checkpoint_id)

    # EVENT: NODE_LOSS(Node A)
    store.mark_node_lost(node_a)
    assert not store.node_available(node_a)

    try:
        store.get_from_node(obj.content_hash, node_a)
        raised = False
    except CRAMNodeUnavailable:
        raised = True
    assert raised, "expected node-local get to fail after NODE_LOSS"

    # Durable CAS still holds bytes
    assert store.exists(obj.content_hash)
    assert store.get(obj.content_hash) == content
    assert store.verify(obj.content_hash)

    # Checkpoint path → RECOVERABLE
    result = store.recover_from_checkpoint(
        cp.cram_objects, expect_root_hash=cp.cram_root_hash
    )
    assert result["status"] == "RECOVERABLE"
    assert obj.content_hash in result["recovered"]


def test_placement_assigns_known_node():
    topo = _demo_topology()
    place = CRAMPlacement()
    key = "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff"
    node = place.locate(key, topo)
    assert node in {n.id for n in topo.nodes}
