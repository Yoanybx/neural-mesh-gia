"""P0 fault injection tests (NODE_LOSS, PACKET_DROP, PACKET_DELAY)."""

from neural_mesh.twin.events import FaultEvent
from neural_mesh.twin.faults import (
    FAULT_NODE_LOSS,
    FAULT_PACKET_DELAY,
    FAULT_PACKET_DROP,
)
from neural_mesh.twin.simulator import DigitalTwin, TwinLink, TwinNode, TwinTask


def test_fault_event_chatgpt_fields():
    ev = FaultEvent(
        event_id="fault-0001",
        fault_type=FAULT_NODE_LOSS,
        target_id="node-03",
        tick=100,
        seed=42,
        parameters={"duration_ticks": -1},
    )
    assert ev.event_id == "fault-0001"
    assert ev.target_id == "node-03"
    assert ev.tick == 100
    assert ev.seed == 42
    d = ev.to_dict()
    assert FaultEvent.from_dict(d).event_id == "fault-0001"


def test_packet_delay_defers_start_and_raises_latency():
    twin = DigitalTwin(seed=7)
    twin.add_node(TwinNode("a", cpu_cores=1))  # origin
    twin.add_node(TwinNode("b", cpu_cores=8))
    twin.add_link(TwinLink("a", "b", latency_ms=2.0))
    twin.add_task(TwinTask("job", cpu_need=2, duration_ticks=2, earliest_start=0))
    twin.inject_fault(
        FaultEvent.create(
            FAULT_PACKET_DELAY,
            "a->b",
            at_tick=0,
            delay_ticks=3,
            delay_ms=10.0,
            seed=7,
        )
    )
    report = twin.run(ticks=20)
    by_id = {r.task_id: r for r in report.schedule}
    assert by_id["job"].status == "COMPLETED"
    assert by_id["job"].start_tick >= 3
    assert report.latency_avg > 0.0
    assert report.events_executed == 1


def test_node_loss_and_packet_drop_together_deterministic():
    def build():
        twin = DigitalTwin(seed=11)
        twin.add_node(TwinNode("n0", cpu_cores=4))
        twin.add_node(TwinNode("n1", cpu_cores=4))
        twin.add_link(TwinLink("n0", "n1"))
        twin.add_task(TwinTask("t0", cpu_need=1, duration_ticks=5))
        twin.inject_fault(FaultEvent.create(FAULT_NODE_LOSS, "n0", at_tick=2, seed=11))
        twin.inject_fault(
            FaultEvent.create(FAULT_PACKET_DROP, "n0->n1", at_tick=0, drop_rate=0.3, seed=11)
        )
        return twin.run(ticks=15)

    a, b = build(), build()
    assert a.digest == b.digest
    assert a.run_summary() == b.run_summary()
