"""Same topology+workload+seed+faults → same result."""

import json
from pathlib import Path

from neural_mesh.twin.events import FaultEvent
from neural_mesh.twin.faults import FAULT_NODE_LOSS, FAULT_PACKET_DELAY, FAULT_PACKET_DROP
from neural_mesh.twin.schema import Topology, Workload
from neural_mesh.twin.simulator import DigitalTwin
from neural_mesh.twin.storage import load_faults, save_faults


def _write_inputs(tmp_path: Path):
    twin = DigitalTwin.build_demo(seed=42)
    twin.to_topology_model().save(tmp_path / "topology.json")
    twin.to_workload_model().save(tmp_path / "workload.json")
    faults = [
        FaultEvent.create(FAULT_NODE_LOSS, "n1", at_tick=4, duration_ticks=2, seed=42),
        FaultEvent.create(FAULT_PACKET_DROP, "n0->n1", at_tick=0, drop_rate=0.2, seed=42),
        FaultEvent.create(
            FAULT_PACKET_DELAY, "n0->n2", at_tick=0, delay_ticks=1, delay_ms=5.0, seed=42
        ),
    ]
    save_faults(tmp_path / "faults.json", faults)
    return faults


def test_reproducibility_from_json_inputs(tmp_path: Path):
    _write_inputs(tmp_path)
    def run_once():
        topo = Topology.load(tmp_path / "topology.json")
        wl = Workload.load(tmp_path / "workload.json")
        faults = load_faults(tmp_path / "faults.json")
        twin = DigitalTwin.from_parts(topo, wl, faults, seed=42)
        return twin.run(ticks=20)

    a, b = run_once(), run_once()
    assert a.digest == b.digest
    assert a.experiment_id == b.experiment_id
    assert a.run_summary() == b.run_summary()
    assert a.packets_sent == b.packets_sent
    assert a.packets_dropped == b.packets_dropped
    assert a.latency_avg == b.latency_avg
    assert a.topology_hash == b.topology_hash


def test_cli_compatible_summary_fields(tmp_path: Path):
    _write_inputs(tmp_path)
    topo = Topology.load(tmp_path / "topology.json")
    wl = Workload.load(tmp_path / "workload.json")
    faults = load_faults(tmp_path / "faults.json")
    report = DigitalTwin.from_parts(topo, wl, faults, seed=42).run(ticks=20)
    summary = report.run_summary()
    for key in (
        "experiment_id",
        "seed",
        "events_executed",
        "nodes_alive",
        "packets_sent",
        "packets_dropped",
        "latency_avg",
        "checkpoint_id",
    ):
        assert key in summary
