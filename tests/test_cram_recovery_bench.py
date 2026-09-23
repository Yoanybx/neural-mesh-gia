"""P0/P5 real recovery_time bench — N=100, p50/p99, no STUB."""

from pathlib import Path

from neural_mesh.cram.recovery import percentile, run_recovery_bench


def test_percentile_basic():
    vals = [1.0, 2.0, 3.0, 4.0, 5.0]
    assert percentile(vals, 50) == 3.0
    assert percentile(vals, 0) == 1.0
    assert percentile(vals, 100) == 5.0


def test_recovery_bench_n100_measured(tmp_path: Path):
    result = run_recovery_bench(n=100, seed=42, root=tmp_path / "bench")
    assert result.n == 100
    assert len(result.samples_ms) == 100
    assert result.p50_ms >= 0
    assert result.p99_ms >= result.p50_ms
    assert result.recoverable_count + result.error_count == 100
    # Must be real measurements (not STUB)
    assert all(isinstance(x, float) for x in result.samples_ms)
    d = result.to_dict()
    assert "p50_ms" in d and "p99_ms" in d
    # Honest baseline: record whether target met; do not fake
    assert isinstance(result.p99_met, bool)
    if not result.p99_met:
        assert "baseline" in result.note.lower() or "exceeds" in result.note.lower()
