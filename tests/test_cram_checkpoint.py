"""Checkpoint integration with cram_root_hash / cram_objects."""

from pathlib import Path

from neural_mesh.checkpoint import CheckpointManager
from neural_mesh.cram import CRAMStore
from neural_mesh.cram.hashing import root_hash
from neural_mesh.models import Checkpoint


def test_checkpoint_records_cram_fields(tmp_path: Path):
    store = CRAMStore(tmp_path)
    k1 = store.put(b"state-a", metadata={"t": "STATE"})
    k2 = store.put(b"evidence-b", metadata={"t": "EVIDENCE"})
    objects = [k1, k2]
    rh = root_hash(objects)

    mgr = CheckpointManager(tmp_path)
    cp = mgr.create(
        phase=2,
        module="cram",
        reason="cram checkpoint integration",
        next_action="continue",
        tests={"passed": 1, "failed": 0},
        cram_root_hash=rh,
        cram_objects=objects,
        status="VERIFIED",
    )
    assert cp.checkpoint_id == "CP-0001"
    assert cp.cram_root_hash == rh
    assert cp.cram_objects == objects
    assert mgr.verify("CP-0001")

    raw = Checkpoint.model_validate_json(
        (tmp_path / "snapshots/CP-0001/checkpoint.json").read_text(encoding="utf-8")
    )
    assert raw.cram_root_hash == rh
    assert set(raw.cram_objects) == set(objects)


def test_historical_checkpoint_schema_loads_without_cram_fields():
    """Old checkpoints without cram_* still validate (defaults)."""
    legacy = {
        "checkpoint_id": "CP-0001",
        "project_version": "0.5.3",
        "phase": 0,
        "module": "bootstrap",
        "reason": "legacy",
        "status": "VERIFIED",
    }
    cp = Checkpoint.model_validate(legacy)
    assert cp.cram_root_hash is None
    assert cp.cram_objects == []
