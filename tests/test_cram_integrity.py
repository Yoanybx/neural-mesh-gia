"""C-RAM integrity / verify / object model tests."""

from pathlib import Path

import pytest

from neural_mesh.cram import CRAMObject, CRAMStore, ObjectType, content_hash


def test_verify_ok_and_tamper_detected(tmp_path: Path):
    store = CRAMStore(tmp_path)
    key = store.put(b"evidence-payload")
    assert store.verify(key) is True
    path = tmp_path / ".cram" / key[:2] / key[2:]
    path.write_bytes(b"tampered")
    assert store.verify(key) is False


def test_cram_object_types_and_put_object(tmp_path: Path):
    store = CRAMStore(tmp_path)
    obj = store.put_object(
        b'{"result": 42}',
        ObjectType.EVIDENCE,
        metadata={"artifact": "result.json"},
        parent_refs=[],
    )
    assert isinstance(obj, CRAMObject)
    assert obj.object_type == ObjectType.EVIDENCE
    assert obj.content_hash == content_hash(b'{"result": 42}')
    assert store.verify(obj.content_hash)


def test_rejects_private_thoughts_metadata():
    with pytest.raises(ValueError, match="private thoughts"):
        CRAMObject(
            id="x",
            object_type=ObjectType.MEMORY,
            content_hash="0" * 64,
            metadata={"private_thoughts": "should not store"},
        )


def test_all_object_types_accepted(tmp_path: Path):
    store = CRAMStore(tmp_path)
    for ot in ObjectType:
        obj = store.put_object(f"payload-{ot.value}".encode(), ot)
        assert obj.object_type == ot
        assert store.exists(obj.content_hash)
