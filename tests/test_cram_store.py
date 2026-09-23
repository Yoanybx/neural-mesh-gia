"""P0 C-RAM content-addressable store tests."""

from pathlib import Path

import pytest

from neural_mesh.cram import CRAMKeyError, CRAMStore, content_hash


def test_put_get_exists_roundtrip(tmp_path: Path):
    store = CRAMStore(tmp_path)
    content = b"task state v1"
    key = store.put(content, metadata={"kind": "STATE"})
    assert key == content_hash(content)
    assert store.exists(key)
    assert store.get(key) == content
    assert store.get_metadata(key)["kind"] == "STATE"


def test_put_idempotent_same_hash(tmp_path: Path):
    store = CRAMStore(tmp_path)
    a = store.put(b"same-bytes")
    b = store.put(b"same-bytes", metadata={"note": "again"})
    assert a == b
    assert store.list_keys() == [a]


def test_sharded_on_disk_layout(tmp_path: Path):
    store = CRAMStore(tmp_path)
    key = store.put(b"layout-check")
    shard, rest = key[:2], key[2:]
    path = tmp_path / ".cram" / shard / rest
    assert path.exists()
    assert path.read_bytes() == b"layout-check"


def test_get_missing_raises(tmp_path: Path):
    store = CRAMStore(tmp_path)
    with pytest.raises(CRAMKeyError):
        store.get("0" * 64)


def test_put_rejects_non_bytes(tmp_path: Path):
    store = CRAMStore(tmp_path)
    with pytest.raises(TypeError):
        store.put("not-bytes")  # type: ignore[arg-type]
