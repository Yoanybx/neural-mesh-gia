"""P2 typed errors: NodeUnavailable vs ObjectMissing (≥4 cases each)."""

from pathlib import Path

import pytest

from neural_mesh.cram import (
    CRAMCorrupt,
    CRAMKeyError,
    CRAMNodeUnavailable,
    CRAMStore,
    NodeUnavailable,
    ObjectMissing,
)


def test_node_unavailable_on_lost_node_get(tmp_path: Path):
    store = CRAMStore(tmp_path)
    key = store.put(b"payload-nu-1")
    store.bind_to_node(key, "n1")
    store.mark_node_lost("n1")
    with pytest.raises(NodeUnavailable) as ei:
        store.get_from_node(key, "n1")
    assert ei.value.code == "CRAM_NODE_UNAVAILABLE"
    assert ei.value.node_id == "n1"


def test_node_unavailable_alias_cram_node_unavailable(tmp_path: Path):
    store = CRAMStore(tmp_path)
    key = store.put(b"payload-nu-2")
    store.bind_to_node(key, "n2")
    store.mark_node_lost("n2")
    with pytest.raises(CRAMNodeUnavailable):
        store.get_from_node(key, "n2")


def test_node_unavailable_is_retryable_after_restore(tmp_path: Path):
    store = CRAMStore(tmp_path)
    key = store.put(b"payload-nu-3")
    store.bind_to_node(key, "n3")
    store.mark_node_lost("n3")
    with pytest.raises(NodeUnavailable):
        store.get_from_node(key, "n3")
    store.restore_node("n3")
    assert store.get_from_node(key, "n3") == b"payload-nu-3"


def test_node_unavailable_message_includes_node_id(tmp_path: Path):
    store = CRAMStore(tmp_path)
    key = store.put(b"payload-nu-4")
    store.bind_to_node(key, "edge-99")
    store.mark_node_lost("edge-99")
    with pytest.raises(NodeUnavailable, match="edge-99"):
        store.get_from_node(key, "edge-99")


def test_object_missing_on_get(tmp_path: Path):
    store = CRAMStore(tmp_path)
    with pytest.raises(ObjectMissing) as ei:
        store.get("0" * 64)
    assert ei.value.code == "CRAM_OBJECT_MISSING"
    assert ei.value.key == "0" * 64


def test_object_missing_alias_cram_key_error(tmp_path: Path):
    store = CRAMStore(tmp_path)
    with pytest.raises(CRAMKeyError):
        store.get("a" * 64)


def test_object_missing_when_not_placed_on_node(tmp_path: Path):
    store = CRAMStore(tmp_path)
    key = store.put(b"payload-om-3")
    store.bind_to_node(key, "n1")
    with pytest.raises(ObjectMissing):
        store.get_from_node(key, "n2")


def test_object_missing_on_bind_unknown_key(tmp_path: Path):
    store = CRAMStore(tmp_path)
    with pytest.raises(ObjectMissing):
        store.bind_to_node("f" * 64, "n1")


def test_corrupt_raises_on_verify_or_raise(tmp_path: Path):
    store = CRAMStore(tmp_path)
    key = store.put(b"good-bytes")
    path = tmp_path / ".cram" / key[:2] / key[2:]
    path.write_bytes(b"flipped")
    with pytest.raises(CRAMCorrupt) as ei:
        store.verify_or_raise(key)
    assert ei.value.code == "CRAM_CORRUPT"
