"""P4 blob corruption + durability/fsync honesty."""

from pathlib import Path

import pytest

from neural_mesh.cram import CRAMCorrupt, CRAMStore, content_hash


def test_flip_byte_verify_fails_corrupt(tmp_path: Path):
    store = CRAMStore(tmp_path)
    key = store.put(b"ABCDEFGH")
    path = tmp_path / ".cram" / key[:2] / key[2:]
    raw = bytearray(path.read_bytes())
    raw[0] = raw[0] ^ 0xFF
    path.write_bytes(bytes(raw))
    assert store.verify(key) is False
    with pytest.raises(CRAMCorrupt) as ei:
        store.verify_or_raise(key)
    assert ei.value.code == "CRAM_CORRUPT"


def test_fsck_reports_corrupt_and_orphans(tmp_path: Path):
    store = CRAMStore(tmp_path)
    key = store.put(b"orphan-parent")
    path = tmp_path / ".cram" / key[:2] / key[2:]
    path.write_bytes(b"corrupted")
    # orphan sidecar without blob
    orphan_meta = tmp_path / ".cram" / "zz" / ("y" * 62 + ".meta.json")
    orphan_meta.parent.mkdir(parents=True, exist_ok=True)
    orphan_meta.write_text("{}", encoding="utf-8")
    report = store.fsck()
    assert key in report["corrupt"]
    assert any("zz" in o for o in report["orphans"])
    assert report["status"] == "CORRUPT"


def test_atomic_put_survives_reread(tmp_path: Path):
    """Durability as honest as practical: fsync+replace then new store instance sees bytes."""
    store = CRAMStore(tmp_path)
    key = store.put(b"durable-payload", metadata={"k": 1})
    store2 = CRAMStore(tmp_path)
    assert store2.exists(key)
    assert store2.get(key) == b"durable-payload"
    assert store2.verify(key)
    assert store2.get_metadata(key)["k"] == 1


def test_content_hash_stable_under_corruption_detection(tmp_path: Path):
    payload = b"hash-check"
    key = content_hash(payload)
    store = CRAMStore(tmp_path)
    assert store.put(payload) == key
    path = tmp_path / ".cram" / key[:2] / key[2:]
    path.write_bytes(payload + b"!")
    assert content_hash(path.read_bytes()) != key
    assert store.verify(key) is False
