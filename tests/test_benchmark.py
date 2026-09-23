"""P2 benchmark harness twin-basic."""

from pathlib import Path

from neural_mesh.benchmark.runner import run_twin_basic


def test_twin_basic_writes_artifacts(tmp_path: Path):
    result = run_twin_basic(tmp_path, seed=42, ticks=20)
    assert result.experiment_id.startswith("EXP-")
    assert result.duration_ms >= 0
    exp_dir = tmp_path / "experiments" / result.experiment_id
    for name in (
        "result.json",
        "topology.json",
        "workload.json",
        "faults.json",
        "checkpoint.json",
    ):
        assert (exp_dir / name).exists(), name
    assert "simulation_time" in result.metrics
    assert "events_processed" in result.metrics
    assert "node_failures" in result.metrics
    assert "packet_loss" in result.metrics
    assert "latency" in result.metrics
    assert "throughput" in result.metrics
    assert result.metrics["recovery_time"]["status"] == "MEASURED"
    assert result.metrics["recovery_time"]["value"] is not None
    assert result.metrics["recovery_time"]["value"] >= 0
    assert result.metrics["checkpoint_overhead"]["status"] == "STUB"
    assert result.metrics["topology_hash"]
    assert result.metrics["checkpoint_id"]


def test_twin_basic_sequential_ids(tmp_path: Path):
    a = run_twin_basic(tmp_path, seed=1, ticks=5)
    b = run_twin_basic(tmp_path, seed=1, ticks=5)
    assert a.experiment_id == "EXP-0001"
    assert b.experiment_id == "EXP-0002"
