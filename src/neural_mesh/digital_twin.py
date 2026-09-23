"""Deterministic Digital Twin simulator for Neural Mesh (Phase 1 slice).

Simulates authorized mesh nodes, network links, and a simple workload
schedule with a replay seed. Pure Python + networkx; no hardware side effects.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field, asdict
from typing import Any

import networkx as nx


@dataclass(frozen=True)
class TwinNode:
    node_id: str
    cpu_cores: int = 4
    memory_gb: float = 16.0
    gpu_count: int = 0
    privacy_zone: str = "default"
    capabilities: tuple[str, ...] = ("compute",)


@dataclass(frozen=True)
class TwinLink:
    src: str
    dst: str
    latency_ms: float = 1.0
    bandwidth_mbps: float = 1000.0


@dataclass(frozen=True)
class TwinTask:
    task_id: str
    cpu_need: float
    duration_ticks: int
    earliest_start: int = 0
    preferred_capabilities: tuple[str, ...] = ("compute",)


@dataclass
class TaskResult:
    task_id: str
    node_id: str
    start_tick: int
    end_tick: int
    status: str


@dataclass
class SimulationReport:
    seed: int
    ticks: int
    nodes: list[str]
    links: list[tuple[str, str]]
    schedule: list[TaskResult]
    digest: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "seed": self.seed,
            "ticks": self.ticks,
            "nodes": list(self.nodes),
            "links": [list(x) for x in self.links],
            "schedule": [asdict(t) for t in self.schedule],
            "digest": self.digest,
        }


class DigitalTwin:
    """Minimal deterministic mesh simulator."""

    def __init__(self, seed: int = 0):
        self.seed = int(seed)
        self.nodes: dict[str, TwinNode] = {}
        self.links: list[TwinLink] = []
        self.tasks: list[TwinTask] = []
        self._graph = nx.Graph()

    def add_node(self, node: TwinNode) -> None:
        if node.node_id in self.nodes:
            raise ValueError(f"duplicate node_id: {node.node_id}")
        self.nodes[node.node_id] = node
        self._graph.add_node(node.node_id)

    def add_link(self, link: TwinLink) -> None:
        if link.src not in self.nodes or link.dst not in self.nodes:
            raise ValueError("link endpoints must exist as nodes")
        self.links.append(link)
        self._graph.add_edge(
            link.src,
            link.dst,
            latency_ms=link.latency_ms,
            bandwidth_mbps=link.bandwidth_mbps,
        )

    def add_task(self, task: TwinTask) -> None:
        self.tasks.append(task)

    def _eligible_nodes(self, task: TwinTask) -> list[str]:
        out = []
        for nid, node in sorted(self.nodes.items()):
            caps = set(node.capabilities)
            if all(c in caps for c in task.preferred_capabilities):
                if node.cpu_cores >= task.cpu_need:
                    out.append(nid)
        return out

    def run(self, ticks: int) -> SimulationReport:
        """Run a deterministic schedule for ``ticks`` discrete time steps.

        Placement policy (deterministic):
        - tasks processed in stable task_id order
        - among eligible free nodes, pick lexicographically smallest node_id
        - node is busy until task end_tick
        """
        if ticks < 0:
            raise ValueError("ticks must be >= 0")
        if not self.nodes:
            raise ValueError("simulator requires at least one node")

        busy_until: dict[str, int] = {nid: 0 for nid in self.nodes}
        remaining = sorted(self.tasks, key=lambda t: (t.earliest_start, t.task_id))
        schedule: list[TaskResult] = []
        pending = list(remaining)

        for tick in range(ticks + 1):
            # Free completed
            still_pending = []
            for task in pending:
                if task.earliest_start > tick:
                    still_pending.append(task)
                    continue
                eligible = [
                    nid
                    for nid in self._eligible_nodes(task)
                    if busy_until[nid] <= tick
                ]
                if not eligible:
                    still_pending.append(task)
                    continue
                node_id = sorted(eligible)[0]
                end = tick + task.duration_ticks
                busy_until[node_id] = end
                schedule.append(
                    TaskResult(
                        task_id=task.task_id,
                        node_id=node_id,
                        start_tick=tick,
                        end_tick=end,
                        status="COMPLETED" if end <= ticks else "RUNNING",
                    )
                )
            pending = still_pending

        for task in pending:
            schedule.append(
                TaskResult(
                    task_id=task.task_id,
                    node_id="",
                    start_tick=-1,
                    end_tick=-1,
                    status="UNSCHEDULED",
                )
            )

        # Finalize RUNNING vs COMPLETED against horizon
        finalized = []
        for r in schedule:
            if r.status == "RUNNING" and r.end_tick <= ticks:
                r = TaskResult(
                    r.task_id, r.node_id, r.start_tick, r.end_tick, "COMPLETED"
                )
            finalized.append(r)

        report = SimulationReport(
            seed=self.seed,
            ticks=ticks,
            nodes=sorted(self.nodes.keys()),
            links=sorted((lnk.src, lnk.dst) for lnk in self.links),
            schedule=finalized,
            digest="",
        )
        report.digest = self._digest(report)
        return report

    def _digest(self, report: SimulationReport) -> str:
        payload = {
            "seed": report.seed,
            "ticks": report.ticks,
            "nodes": report.nodes,
            "links": report.links,
            "schedule": [asdict(t) for t in report.schedule],
        }
        blob = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
        # Mix in seed explicitly for replay identity
        h = hashlib.sha256()
        h.update(str(self.seed).encode())
        h.update(blob)
        return h.hexdigest()

    @staticmethod
    def demo(seed: int = 42, ticks: int = 20) -> SimulationReport:
        """Build a small canonical topology and run it."""
        twin = DigitalTwin(seed=seed)
        twin.add_node(
            TwinNode("n0", cpu_cores=8, memory_gb=32, capabilities=("compute", "verify"))
        )
        twin.add_node(TwinNode("n1", cpu_cores=4, memory_gb=16, capabilities=("compute",)))
        twin.add_node(
            TwinNode("n2", cpu_cores=4, memory_gb=16, gpu_count=1, capabilities=("compute", "ml"))
        )
        twin.add_link(TwinLink("n0", "n1", latency_ms=0.5))
        twin.add_link(TwinLink("n1", "n2", latency_ms=1.0))
        twin.add_link(TwinLink("n0", "n2", latency_ms=1.5))
        twin.add_task(TwinTask("t0", cpu_need=2, duration_ticks=3, earliest_start=0))
        twin.add_task(TwinTask("t1", cpu_need=2, duration_ticks=4, earliest_start=0))
        twin.add_task(TwinTask("t2", cpu_need=4, duration_ticks=5, earliest_start=2))
        twin.add_task(
            TwinTask(
                "t3",
                cpu_need=1,
                duration_ticks=2,
                earliest_start=1,
                preferred_capabilities=("ml",),
            )
        )
        return twin.run(ticks=ticks)
