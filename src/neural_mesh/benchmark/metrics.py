"""Benchmark metrics for twin experiments."""

from __future__ import annotations

from typing import Any

from neural_mesh.twin.simulator import SimulationReport


def build_metrics(
    report: SimulationReport,
    *,
    duration_ms: int,
    checkpoint_overhead_ms: float | None = None,
    recovery_time_ms: float | None = None,
) -> dict[str, Any]:
    """Collect initial ChatGPT metric set.

    recovery_time / checkpoint_overhead use honest STUB labels when not measured.
    """
    m = report.metrics
    scheduled = m.scheduled_count if m else 0
    failed = m.failed_count if m else 0
    sim_ticks = report.ticks
    throughput = (scheduled / sim_ticks) if sim_ticks else 0.0
    packet_loss = (
        (report.packets_dropped / report.packets_sent) if report.packets_sent else 0.0
    )
    latency = report.latency_avg
    if m and m.mean_latency_ticks and latency == 0.0:
        latency = float(m.mean_latency_ticks)

    metrics: dict[str, Any] = {
        "simulation_time": sim_ticks,
        "events_processed": report.events_executed,
        "node_failures": failed,
        "packet_loss": packet_loss,
        "latency": latency,
        "throughput": throughput,
        "wall_duration_ms": duration_ms,
    }
    if recovery_time_ms is None:
        metrics["recovery_time"] = {"value": None, "status": "STUB", "note": "not yet measurable"}
    else:
        metrics["recovery_time"] = {"value": recovery_time_ms, "status": "MEASURED"}
    if checkpoint_overhead_ms is None:
        metrics["checkpoint_overhead"] = {
            "value": None,
            "status": "STUB",
            "note": "not yet measurable",
        }
    else:
        metrics["checkpoint_overhead"] = {
            "value": checkpoint_overhead_ms,
            "status": "MEASURED",
        }
    return metrics
