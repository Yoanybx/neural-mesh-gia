import json
from pathlib import Path

from neural_mesh.digital_twin import (
    FAULT_NODE_LOSS,
    FAULT_PACKET_DROP,
    DigitalTwin,
    FaultEvent,
    TwinLink,
    TwinNode,
    TwinTask,
)


def test_demo_deterministic_replay():
    a = DigitalTwin.demo(seed=42, ticks=20)
    b = DigitalTwin.demo(seed=42, ticks=20)
    assert a.digest == b.digest
    assert a.to_dict() == b.to_dict()
    assert len(a.schedule) == 4
    assert all(
        r.status in {"COMPLETED", "RUNNING", "UNSCHEDULED", "FAILED"}
        for r in a.schedule
    )
    assert a.metrics is not None
    assert a.metrics.scheduled_count >= 1


def test_seed_changes_digest_identity_but_schedule_policy_stable():
    # Same topology/tasks → same placement; digest still mixes seed.
    a = DigitalTwin.demo(seed=1, ticks=20)
    b = DigitalTwin.demo(seed=2, ticks=20)
    assert [(r.task_id, r.node_id, r.start_tick, r.end_tick) for r in a.schedule] == [
        (r.task_id, r.node_id, r.start_tick, r.end_tick) for r in b.schedule
    ]
    assert a.digest != b.digest


def test_nodes_links_and_workload():
    twin = DigitalTwin(seed=7)
    twin.add_node(TwinNode("a", cpu_cores=2))
    twin.add_node(TwinNode("b", cpu_cores=2))
    twin.add_link(TwinLink("a", "b", latency_ms=2.0))
    twin.add_task(TwinTask("job1", cpu_need=1, duration_ticks=2))
    twin.add_task(TwinTask("job2", cpu_need=1, duration_ticks=2))
    report = twin.run(ticks=5)
    assert report.nodes == ["a", "b"]
    assert report.links == [("a", "b")]
    placed = [r for r in report.schedule if r.status == "COMPLETED"]
    assert len(placed) == 2
    assert {r.node_id for r in placed} == {"a", "b"}


def test_unscheduled_when_capacity_insufficient():
    twin = DigitalTwin(seed=0)
    twin.add_node(TwinNode("only", cpu_cores=1))
    twin.add_task(TwinTask("big", cpu_need=8, duration_ticks=1))
    report = twin.run(ticks=3)
    assert report.schedule[0].status == "UNSCHEDULED"


def test_node_loss_fails_running_and_blocks_placement():
    twin = DigitalTwin(seed=1)
    twin.add_node(TwinNode("a", cpu_cores=4))
    twin.add_node(TwinNode("b", cpu_cores=4))
    twin.add_link(TwinLink("a", "b"))
    twin.add_task(TwinTask("long", cpu_need=1, duration_ticks=10, earliest_start=0))
    twin.add_task(TwinTask("late", cpu_need=1, duration_ticks=2, earliest_start=3))
    twin.inject_fault(
        FaultEvent(fault_type=FAULT_NODE_LOSS, at_tick=2, target="a", duration_ticks=-1)
    )
    report = twin.run(ticks=12)
    by_id = {r.task_id: r for r in report.schedule}
    # long placed on 'a' (lexicographically first) then FAILED at tick 2
    assert by_id["long"].status == "FAILED"
    assert by_id["long"].node_id == "a"
    assert by_id["long"].end_tick == 2
    # late should land on surviving node b
    assert by_id["late"].status == "COMPLETED"
    assert by_id["late"].node_id == "b"
    assert report.faults[0]["fault_type"] == FAULT_NODE_LOSS


def _two_node_drop_twin(seed: int = 99) -> DigitalTwin:
    twin = DigitalTwin(seed=seed)
    twin.add_node(TwinNode("a", cpu_cores=4))
    twin.add_node(TwinNode("b", cpu_cores=4))
    twin.add_link(TwinLink("a", "b"))
    twin.add_task(TwinTask("j", cpu_need=1, duration_ticks=2))
    twin.inject_fault(
        FaultEvent(
            fault_type=FAULT_PACKET_DROP,
            at_tick=0,
            target="a->b",
            drop_rate=0.5,
            duration_ticks=-1,
        )
    )
    return twin


def test_packet_drop_deterministic_and_counted():
    r1 = _two_node_drop_twin(99).run(ticks=10)
    r2 = _two_node_drop_twin(99).run(ticks=10)
    assert r1.digest == r2.digest
    assert r1.packets_sent == r2.packets_sent
    assert r1.packets_dropped == r2.packets_dropped
    assert r1.packets_sent >= 0


def test_packet_drop_total_blocks_remote_placement():
    twin = DigitalTwin(seed=3)
    twin.add_node(TwinNode("coord", cpu_cores=1))  # origin for packets, too small for task
    twin.add_node(TwinNode("worker", cpu_cores=8))
    twin.add_link(TwinLink("coord", "worker"))
    twin.add_task(TwinTask("heavy", cpu_need=4, duration_ticks=2))
    twin.inject_fault(
        FaultEvent(
            fault_type=FAULT_PACKET_DROP,
            at_tick=0,
            target="coord->worker",
            drop_rate=1.0,
        )
    )
    report = twin.run(ticks=5)
    assert report.schedule[0].status == "UNSCHEDULED"
    assert report.packets_dropped >= 1
    assert report.packets_dropped == report.packets_sent


def test_topology_json_roundtrip(tmp_path: Path):
    twin = DigitalTwin.build_demo(seed=42)
    twin.inject_fault(
        FaultEvent(fault_type=FAULT_NODE_LOSS, at_tick=5, target="n1", duration_ticks=2)
    )
    path = tmp_path / "topo.json"
    twin.save_topology(path)
    loaded = DigitalTwin.load_topology(path)
    assert loaded.to_topology_dict() == twin.to_topology_dict()
    assert loaded.run(ticks=20).digest == twin.run(ticks=20).digest
    raw = json.loads(path.read_text(encoding="utf-8"))
    assert "nodes" in raw and "links" in raw and "tasks" in raw and "faults" in raw


def test_benchmark_metrics_bounds():
    report = DigitalTwin.demo(seed=42, ticks=20)
    m = report.metrics
    assert m is not None
    assert m.makespan >= 0
    assert 0.0 <= m.utilization <= 1.0
    assert m.scheduled_count + m.failed_count + m.unscheduled_count == len(report.schedule)
    assert m.mean_latency_ticks >= 0.0
    assert m.mean_wait_ticks >= 0.0


def test_fault_digest_changes_when_fault_added():
    base = DigitalTwin.build_demo(seed=42).run(ticks=20)
    twin = DigitalTwin.build_demo(seed=42)
    twin.inject_fault(
        FaultEvent(fault_type=FAULT_NODE_LOSS, at_tick=1, target="n0")
    )
    faulted = twin.run(ticks=20)
    assert base.digest != faulted.digest
