"""P1 NODE_LOSS → locate; valid route OK; no route → ERROR (no optimistic RECOVERABLE)."""

from pathlib import Path

import pytest

from neural_mesh.checkpoint import CheckpointManager
from neural_mesh.cram import (
    CRAMNodeUnavailable,
    CRAMStore,
    ObjectType,
    recover_after_node_loss,
)
from neural_mesh.cram.hashing import root_hash
from neural_mesh.cram.recovery import STATUS_ERROR, STATUS_RECOVERABLE
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


def test_node_loss_unresolved_returns_error(tmp_path: Path):
    """Owner NODE_LOSS with N=1 (no replica) ⇒ locate has no valid route ⇒ ERROR."""
    store = CRAMStore(tmp_path)
    topo = _demo_topology()
    place = CRAMPlacement()
    content = b'{"task":"unresolved"}'
    obj = store.put_object(content, ObjectType.STATE)
    owner = place.locate(obj.content_hash, topo)
    store.bind_to_node(obj.content_hash, owner)
    store.mark_node_lost(owner)

    result = recover_after_node_loss(
        store, place, topo, obj.content_hash, lost_nodes=[owner]
    )
    assert result.status == STATUS_ERROR
    assert result.error_code in {
        "CRAM_NODE_UNAVAILABLE",
        "CRAM_OBJECT_MISSING",
        "CRAM_LOCATE_FAILED",
    }
    # No optimistic RECOVERABLE; recovery_time still measured
    assert result.recovery_time_ms >= 0


def test_node_loss_resolved_returns_location(tmp_path: Path):
    """Non-owner NODE_LOSS: locate still finds live owner ⇒ location + RECOVERABLE with proof."""
    store = CRAMStore(tmp_path)
    topo = _demo_topology()
    place = CRAMPlacement()
    content = b'{"task":"resolved"}'
    obj = store.put_object(content, ObjectType.STATE)
    owner = place.locate(obj.content_hash, topo)
    store.bind_to_node(obj.content_hash, owner)
    others = [n.id for n in topo.nodes if n.id != owner]
    assert others, "need a non-owner node to lose"
    lost = others[0]
    store.mark_node_lost(lost)

    result = recover_after_node_loss(
        store, place, topo, obj.content_hash, lost_nodes=[lost]
    )
    assert result.status == STATUS_RECOVERABLE
    assert result.located_node == owner
    assert result.recovery_time_ms >= 0


def test_node_loss_locate_raises_on_stale_topology(tmp_path: Path):
    """If topology hash changed since checkpoint, must NOT silently return stale location."""
    store = CRAMStore(tmp_path)
    topo = _demo_topology()
    place = CRAMPlacement()
    content = b'{"task":"stale-topo"}'
    obj = store.put_object(content, ObjectType.STATE)
    owner = place.locate(obj.content_hash, topo)
    store.bind_to_node(obj.content_hash, owner)
    sealed_hash = topo.hash()

    # Mutate topology after checkpoint seal (add a node → hash drifts)
    stale = Topology(
        network_id=topo.network_id,
        seed=topo.seed,
        nodes=list(topo.nodes)
        + [TopologyNode(id="node-99", cpu=2)],
        links=list(topo.links),
    )
    assert stale.hash() != sealed_hash

    # Lose a non-owner so locate *would* succeed if we ignored hash drift
    others = [n.id for n in topo.nodes if n.id != owner]
    lost = others[0]
    store.mark_node_lost(lost)

    result = recover_after_node_loss(
        store,
        place,
        stale,
        obj.content_hash,
        lost_nodes=[lost],
        expect_topology_hash=sealed_hash,
    )
    assert result.status == STATUS_ERROR
    assert result.error_code == "CRAM_STALE_TOPOLOGY"
    assert result.located_node is None  # must NOT return stale location


def test_node_loss_node_local_get_fails_durable_intact(tmp_path: Path):
    """Cycle 4 durable path: node-local fails; durable CAS + checkpoint integrity still OK.

    Placement recovery is separate (ERROR on owner loss). This only checks durable bytes.
    """
    store = CRAMStore(tmp_path)
    topo = _demo_topology()
    place = CRAMPlacement()
    content = b'{"task":"t1","status":"STATE"}'
    obj = store.put_object(content, ObjectType.STATE, metadata={"role": "task-state"})
    node_a = place.locate(obj.content_hash, topo)
    store.bind_to_node(obj.content_hash, node_a)

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

    store.mark_node_lost(node_a)
    with pytest.raises(CRAMNodeUnavailable):
        store.get_from_node(obj.content_hash, node_a)

    assert store.exists(obj.content_hash)
    assert store.get(obj.content_hash) == content
    assert store.verify(obj.content_hash)

    # Durable integrity (not live placement recovery)
    result = store.recover_from_checkpoint(
        cp.cram_objects, expect_root_hash=cp.cram_root_hash
    )
    assert result["status"] == "RECOVERABLE"

    # Live placement recovery after owner loss ⇒ ERROR (ChatGPT P1)
    live = recover_after_node_loss(
        store, place, topo, obj.content_hash, lost_nodes=[node_a]
    )
    assert live.status == STATUS_ERROR


def test_placement_assigns_known_node():
    topo = _demo_topology()
    place = CRAMPlacement()
    key = "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff"
    node = place.locate(key, topo)
    assert node in {n.id for n in topo.nodes}
