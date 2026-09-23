from neural_mesh.digital_twin import (
    DigitalTwin,
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
    assert all(r.status in {"COMPLETED", "RUNNING", "UNSCHEDULED"} for r in a.schedule)


def test_seed_changes_digest_identity_but_schedule_policy_stable():
    # Same topology/tasks → same placement; digest still mixes seed.
    a = DigitalTwin.demo(seed=1, ticks=20)
    b = DigitalTwin.demo(seed=2, ticks=20)
    assert [ (r.task_id, r.node_id, r.start_tick, r.end_tick) for r in a.schedule ] == [
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
