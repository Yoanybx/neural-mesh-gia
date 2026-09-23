"""Deterministic Digital Twin simulator for Neural Mesh (Phase 1).

Simulates authorized mesh nodes, network links, workload schedule, fault
injection (NODE_LOSS, PACKET_DROP), JSON topology I/O, and a simple
benchmark harness. Pure Python + networkx; no hardware side effects.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

import networkx as nx

FAULT_NODE_LOSS = "NODE_LOSS"
FAULT_PACKET_DROP = "PACKET_DROP"
SUPPORTED_FAULTS = frozenset({FAULT_NODE_LOSS, FAULT_PACKET_DROP})


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


@dataclass(frozen=True)
class FaultEvent:
    """Deterministic fault injection event.

    NODE_LOSS: ``target`` is a node_id; node is dead from ``at_tick`` for
    ``duration_ticks`` (-1 = permanent).
    PACKET_DROP: ``target`` is ``src->dst`` (or either orientation match);
    ``drop_rate`` in [0,1] applied with seeded hash decisions.
    """

    fault_type: str
    at_tick: int
    target: str
    drop_rate: float = 1.0
    duration_ticks: int = -1

    def __post_init__(self) -> None:
        if self.fault_type not in SUPPORTED_FAULTS:
            raise ValueError(f"unsupported fault_type: {self.fault_type}")
        if not (0.0 <= self.drop_rate <= 1.0):
            raise ValueError("drop_rate must be in [0, 1]")
        if self.at_tick < 0:
            raise ValueError("at_tick must be >= 0")


@dataclass
class TaskResult:
    task_id: str
    node_id: str
    start_tick: int
    end_tick: int
    status: str


@dataclass
class BenchmarkMetrics:
    """Simple schedule latency / utilization harness results."""

    makespan: int
    mean_wait_ticks: float
    mean_latency_ticks: float
    scheduled_count: int
    failed_count: int
    unscheduled_count: int
    utilization: float
    packets_sent: int
    packets_dropped: int
    packet_drop_rate: float

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class SimulationReport:
    seed: int
    ticks: int
    nodes: list[str]
    links: list[tuple[str, str]]
    schedule: list[TaskResult]
    digest: str
    faults: list[dict[str, Any]] = field(default_factory=list)
    packets_sent: int = 0
    packets_dropped: int = 0
    metrics: BenchmarkMetrics | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "seed": self.seed,
            "ticks": self.ticks,
            "nodes": list(self.nodes),
            "links": [list(x) for x in self.links],
            "schedule": [asdict(t) for t in self.schedule],
            "digest": self.digest,
            "faults": list(self.faults),
            "packets_sent": self.packets_sent,
            "packets_dropped": self.packets_dropped,
            "metrics": self.metrics.to_dict() if self.metrics else None,
        }


class DigitalTwin:
    """Minimal deterministic mesh simulator with fault hooks + topology I/O."""

    def __init__(self, seed: int = 0):
        self.seed = int(seed)
        self.nodes: dict[str, TwinNode] = {}
        self.links: list[TwinLink] = []
        self.tasks: list[TwinTask] = []
        self.faults: list[FaultEvent] = []
        self._graph = nx.Graph()
        self._packet_seq = 0

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

    def inject_fault(self, fault: FaultEvent) -> None:
        if fault.fault_type == FAULT_NODE_LOSS and fault.target not in self.nodes:
            raise ValueError(f"NODE_LOSS target unknown: {fault.target}")
        if fault.fault_type == FAULT_PACKET_DROP:
            src, sep, dst = fault.target.partition("->")
            if not sep or src not in self.nodes or dst not in self.nodes:
                raise ValueError(
                    f"PACKET_DROP target must be 'src->dst' with known nodes: {fault.target}"
                )
        self.faults.append(fault)

    def _faults_as_dicts(self) -> list[dict[str, Any]]:
        return [asdict(f) for f in sorted(
            self.faults,
            key=lambda f: (f.at_tick, f.fault_type, f.target),
        )]

    def _node_alive(self, node_id: str, tick: int) -> bool:
        for f in self.faults:
            if f.fault_type != FAULT_NODE_LOSS or f.target != node_id:
                continue
            if tick < f.at_tick:
                continue
            if f.duration_ticks < 0 or tick < f.at_tick + f.duration_ticks:
                return False
        return True

    def _drop_rate_for_edge(self, src: str, dst: str, tick: int) -> float:
        rate = 0.0
        for f in self.faults:
            if f.fault_type != FAULT_PACKET_DROP:
                continue
            a, _, b = f.target.partition("->")
            if {a, b} != {src, dst}:
                continue
            if tick < f.at_tick:
                continue
            if f.duration_ticks >= 0 and tick >= f.at_tick + f.duration_ticks:
                continue
            rate = max(rate, f.drop_rate)
        return rate

    def packet_survives(self, src: str, dst: str, tick: int, seq: int | None = None) -> bool:
        """Deterministic Bernoulli trial for PACKET_DROP on edge src-dst."""
        if seq is None:
            seq = self._packet_seq
            self._packet_seq += 1
        rate = self._drop_rate_for_edge(src, dst, tick)
        if rate <= 0.0:
            return True
        if rate >= 1.0:
            return False
        # Stable hash → [0, 9999]; drop if < rate*10000
        h = hashlib.sha256(
            f"{self.seed}|{src}|{dst}|{tick}|{seq}".encode()
        ).hexdigest()
        bucket = int(h[:8], 16) % 10000
        return bucket >= int(rate * 10000)

    def _eligible_nodes(self, task: TwinTask, tick: int) -> list[str]:
        out = []
        for nid, node in sorted(self.nodes.items()):
            if not self._node_alive(nid, tick):
                continue
            caps = set(node.capabilities)
            if all(c in caps for c in task.preferred_capabilities):
                if node.cpu_cores >= task.cpu_need:
                    out.append(nid)
        return out

    def _simulate_placement_packets(
        self, node_id: str, tick: int
    ) -> tuple[int, int, bool]:
        """Simulate control-plane packets along a path from first alive node.

        Returns (sent, dropped, ok). If no path or all retries drop, ok=False.
        """
        sent = 0
        dropped = 0
        origins = [n for n in sorted(self.nodes) if n != node_id and self._node_alive(n, tick)]
        if not origins:
            # Local-only mesh: no network hop needed
            return 0, 0, True
        origin = origins[0]
        if origin == node_id:
            return 0, 0, True
        try:
            path = nx.shortest_path(self._graph, origin, node_id)
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            return 0, 0, False
        # Up to 3 deterministic retransmit attempts per hop
        for i in range(len(path) - 1):
            a, b = path[i], path[i + 1]
            hop_ok = False
            for attempt in range(3):
                seq = self._packet_seq
                self._packet_seq += 1
                sent += 1
                if self.packet_survives(a, b, tick, seq):
                    hop_ok = True
                    break
                dropped += 1
            if not hop_ok:
                return sent, dropped, False
        return sent, dropped, True

    def run(self, ticks: int, *, with_metrics: bool = True) -> SimulationReport:
        """Run a deterministic schedule for ``ticks`` discrete time steps.

        Placement policy (deterministic):
        - tasks processed in stable (earliest_start, task_id) order
        - among eligible free alive nodes, pick lexicographically smallest node_id
        - NODE_LOSS mid-flight → FAILED
        - PACKET_DROP on placement path may delay start (retry next tick) or leave UNSCHEDULED
        """
        if ticks < 0:
            raise ValueError("ticks must be >= 0")
        if not self.nodes:
            raise ValueError("simulator requires at least one node")

        self._packet_seq = 0
        busy_until: dict[str, int] = {nid: 0 for nid in self.nodes}
        # node_id -> TaskResult currently running (for NODE_LOSS interrupt)
        running: dict[str, TaskResult] = {}
        schedule: list[TaskResult] = []
        pending = sorted(self.tasks, key=lambda t: (t.earliest_start, t.task_id))
        packets_sent = 0
        packets_dropped = 0

        for tick in range(ticks + 1):
            # Interrupt tasks on newly lost nodes
            for nid, tr in list(running.items()):
                if not self._node_alive(nid, tick) and tr.end_tick > tick:
                    failed = TaskResult(
                        tr.task_id, tr.node_id, tr.start_tick, tick, "FAILED"
                    )
                    # replace prior RUNNING entry
                    schedule = [
                        failed if (s.task_id == tr.task_id and s.status == "RUNNING") else s
                        for s in schedule
                    ]
                    if not any(s.task_id == tr.task_id and s.status == "FAILED" for s in schedule):
                        schedule.append(failed)
                    del running[nid]
                    busy_until[nid] = tick

            # Free completed
            for nid, until in list(busy_until.items()):
                if until <= tick and nid in running:
                    del running[nid]

            still_pending: list[TwinTask] = []
            for task in pending:
                if task.earliest_start > tick:
                    still_pending.append(task)
                    continue
                eligible = [
                    nid
                    for nid in self._eligible_nodes(task, tick)
                    if busy_until[nid] <= tick
                ]
                if not eligible:
                    still_pending.append(task)
                    continue
                node_id = sorted(eligible)[0]
                sent, dropped, ok = self._simulate_placement_packets(node_id, tick)
                packets_sent += sent
                packets_dropped += dropped
                if not ok:
                    # Network could not deliver placement; retry later
                    still_pending.append(task)
                    continue
                end = tick + task.duration_ticks
                busy_until[node_id] = end
                tr = TaskResult(
                    task_id=task.task_id,
                    node_id=node_id,
                    start_tick=tick,
                    end_tick=end,
                    status="COMPLETED" if end <= ticks else "RUNNING",
                )
                schedule.append(tr)
                if end > tick:
                    running[node_id] = tr
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

        # Deduplicate: keep last status per task_id (FAILED overrides earlier RUNNING)
        by_id: dict[str, TaskResult] = {}
        for r in schedule:
            prev = by_id.get(r.task_id)
            if prev is None:
                by_id[r.task_id] = r
            elif r.status == "FAILED":
                by_id[r.task_id] = r
            elif prev.status == "FAILED":
                continue
            else:
                by_id[r.task_id] = r

        finalized: list[TaskResult] = []
        for tid in sorted(by_id.keys()):
            r = by_id[tid]
            if r.status == "RUNNING" and r.end_tick <= ticks:
                r = TaskResult(r.task_id, r.node_id, r.start_tick, r.end_tick, "COMPLETED")
            finalized.append(r)

        # Preserve original task order for schedule list stability
        order = {t.task_id: i for i, t in enumerate(self.tasks)}
        finalized.sort(key=lambda r: order.get(r.task_id, 9999))

        report = SimulationReport(
            seed=self.seed,
            ticks=ticks,
            nodes=sorted(self.nodes.keys()),
            links=sorted((lnk.src, lnk.dst) for lnk in self.links),
            schedule=finalized,
            digest="",
            faults=self._faults_as_dicts(),
            packets_sent=packets_sent,
            packets_dropped=packets_dropped,
        )
        if with_metrics:
            report.metrics = self.compute_metrics(report)
        report.digest = self._digest(report)
        return report

    def compute_metrics(self, report: SimulationReport) -> BenchmarkMetrics:
        task_by_id = {t.task_id: t for t in self.tasks}
        waits: list[int] = []
        lats: list[int] = []
        scheduled = 0
        failed = 0
        unscheduled = 0
        busy_ticks = 0
        for r in report.schedule:
            if r.status == "UNSCHEDULED":
                unscheduled += 1
                continue
            if r.status == "FAILED":
                failed += 1
                if r.start_tick >= 0:
                    busy_ticks += max(0, r.end_tick - r.start_tick)
                continue
            scheduled += 1
            t = task_by_id.get(r.task_id)
            earliest = t.earliest_start if t else 0
            waits.append(max(0, r.start_tick - earliest))
            lats.append(max(0, r.end_tick - r.start_tick))
            busy_ticks += max(0, min(r.end_tick, report.ticks) - r.start_tick)

        horizon = max(report.ticks, 1)
        capacity = len(report.nodes) * horizon
        utilization = (busy_ticks / capacity) if capacity else 0.0
        makespan = 0
        for r in report.schedule:
            if r.status in {"COMPLETED", "RUNNING", "FAILED"} and r.end_tick > makespan:
                makespan = r.end_tick
        sent = report.packets_sent
        dropped = report.packets_dropped
        return BenchmarkMetrics(
            makespan=makespan,
            mean_wait_ticks=(sum(waits) / len(waits)) if waits else 0.0,
            mean_latency_ticks=(sum(lats) / len(lats)) if lats else 0.0,
            scheduled_count=scheduled,
            failed_count=failed,
            unscheduled_count=unscheduled,
            utilization=utilization,
            packets_sent=sent,
            packets_dropped=dropped,
            packet_drop_rate=(dropped / sent) if sent else 0.0,
        )

    def _digest(self, report: SimulationReport) -> str:
        payload = {
            "seed": report.seed,
            "ticks": report.ticks,
            "nodes": report.nodes,
            "links": report.links,
            "schedule": [asdict(t) for t in report.schedule],
            "faults": report.faults,
            "packets_sent": report.packets_sent,
            "packets_dropped": report.packets_dropped,
        }
        blob = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
        h = hashlib.sha256()
        h.update(str(self.seed).encode())
        h.update(blob)
        return h.hexdigest()

    def to_topology_dict(self) -> dict[str, Any]:
        return {
            "seed": self.seed,
            "nodes": [
                {
                    "node_id": n.node_id,
                    "cpu_cores": n.cpu_cores,
                    "memory_gb": n.memory_gb,
                    "gpu_count": n.gpu_count,
                    "privacy_zone": n.privacy_zone,
                    "capabilities": list(n.capabilities),
                }
                for n in sorted(self.nodes.values(), key=lambda x: x.node_id)
            ],
            "links": [
                {
                    "src": lnk.src,
                    "dst": lnk.dst,
                    "latency_ms": lnk.latency_ms,
                    "bandwidth_mbps": lnk.bandwidth_mbps,
                }
                for lnk in sorted(self.links, key=lambda x: (x.src, x.dst))
            ],
            "tasks": [
                {
                    "task_id": t.task_id,
                    "cpu_need": t.cpu_need,
                    "duration_ticks": t.duration_ticks,
                    "earliest_start": t.earliest_start,
                    "preferred_capabilities": list(t.preferred_capabilities),
                }
                for t in self.tasks
            ],
            "faults": self._faults_as_dicts(),
        }

    def save_topology(self, path: str | Path) -> None:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(self.to_topology_dict(), indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

    @classmethod
    def load_topology(cls, path: str | Path) -> DigitalTwin:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        return cls.from_topology_dict(data)

    @classmethod
    def from_topology_dict(cls, data: dict[str, Any]) -> DigitalTwin:
        twin = cls(seed=int(data.get("seed", 0)))
        for n in data.get("nodes", []):
            twin.add_node(
                TwinNode(
                    node_id=n["node_id"],
                    cpu_cores=int(n.get("cpu_cores", 4)),
                    memory_gb=float(n.get("memory_gb", 16.0)),
                    gpu_count=int(n.get("gpu_count", 0)),
                    privacy_zone=str(n.get("privacy_zone", "default")),
                    capabilities=tuple(n.get("capabilities", ["compute"])),
                )
            )
        for lnk in data.get("links", []):
            twin.add_link(
                TwinLink(
                    src=lnk["src"],
                    dst=lnk["dst"],
                    latency_ms=float(lnk.get("latency_ms", 1.0)),
                    bandwidth_mbps=float(lnk.get("bandwidth_mbps", 1000.0)),
                )
            )
        for t in data.get("tasks", []):
            twin.add_task(
                TwinTask(
                    task_id=t["task_id"],
                    cpu_need=float(t["cpu_need"]),
                    duration_ticks=int(t["duration_ticks"]),
                    earliest_start=int(t.get("earliest_start", 0)),
                    preferred_capabilities=tuple(
                        t.get("preferred_capabilities", ["compute"])
                    ),
                )
            )
        for f in data.get("faults", []):
            twin.inject_fault(
                FaultEvent(
                    fault_type=f["fault_type"],
                    at_tick=int(f["at_tick"]),
                    target=f["target"],
                    drop_rate=float(f.get("drop_rate", 1.0)),
                    duration_ticks=int(f.get("duration_ticks", -1)),
                )
            )
        return twin

    @staticmethod
    def build_demo(seed: int = 42) -> DigitalTwin:
        """Build the canonical demo topology (no run)."""
        twin = DigitalTwin(seed=seed)
        twin.add_node(
            TwinNode("n0", cpu_cores=8, memory_gb=32, capabilities=("compute", "verify"))
        )
        twin.add_node(TwinNode("n1", cpu_cores=4, memory_gb=16, capabilities=("compute",)))
        twin.add_node(
            TwinNode(
                "n2", cpu_cores=4, memory_gb=16, gpu_count=1, capabilities=("compute", "ml")
            )
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
        return twin

    @staticmethod
    def demo(seed: int = 42, ticks: int = 20) -> SimulationReport:
        """Build a small canonical topology and run it."""
        return DigitalTwin.build_demo(seed=seed).run(ticks=ticks)
