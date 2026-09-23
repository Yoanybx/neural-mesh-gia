from pathlib import Path
import json

from neural_mesh.checkpoint import CheckpointManager
from neural_mesh.obsidian import ObsidianSync


def test_init_and_checkpoint(tmp_path):
    m = CheckpointManager(tmp_path)
    ObsidianSync(tmp_path).bootstrap()
    cp = m.create(0, "bootstrap", "test", "implement next module")
    assert cp.checkpoint_id == "CP-0001"
    assert m.latest().checkpoint_id == "CP-0001"
    assert m.verify("CP-0001")
    assert (tmp_path / ".project_state/CURRENT_STATE.md").exists()
    assert (tmp_path / ".project_state/NEXT_ACTION.md").exists()
    assert (tmp_path / "obsidian/Neural-Mesh-Vault/00_INDEX.md").exists()
    assert (tmp_path / "snapshots/CP-0001/CHECKPOINT.json").exists()
    assert cp.manifest_sha256


def test_corruption_detected(tmp_path):
    m = CheckpointManager(tmp_path)
    m.create(0, "x", "test", "next")
    p = tmp_path / "snapshots/CP-0001/checkpoint.json"
    data = json.loads(p.read_text(encoding="utf-8"))
    data["reason"] = "tampered"
    p.write_text(json.dumps(data, indent=2), encoding="utf-8")
    assert not m.verify("CP-0001")


def test_frozen_state_corruption_detected(tmp_path):
    m = CheckpointManager(tmp_path)
    m.create(0, "x", "test", "next")
    p = tmp_path / "snapshots/CP-0001/CHECKPOINT.json"
    data = json.loads(p.read_text(encoding="utf-8"))
    data["next_action"] = "tampered"
    p.write_text(json.dumps(data, indent=2, sort_keys=True), encoding="utf-8")
    assert not m.verify("CP-0001")


def test_historical_checkpoints_preserved(tmp_path):
    m = CheckpointManager(tmp_path)
    a = m.create(0, "bootstrap", "first", "continue")
    b = m.create(0, "bootstrap", "second", "continue")
    assert a.checkpoint_id == "CP-0001"
    assert b.checkpoint_id == "CP-0002"
    assert m.list_ids() == ["CP-0001", "CP-0002"]
    assert m.verify("CP-0001")
    assert m.verify("CP-0002")
    assert (tmp_path / "snapshots/CP-0001/checkpoint.json").exists()
    assert (tmp_path / "snapshots/CP-0002/checkpoint.json").exists()


def test_atomic_state_file(tmp_path):
    m = CheckpointManager(tmp_path)
    m.create(0, "bootstrap", "atomic", "next")
    state = tmp_path / ".project_state/CHECKPOINT.json"
    assert state.exists()
    assert "last_checkpoint" in state.read_text(encoding="utf-8")
