"""Deterministic Digital Twin simulator for Neural Mesh (Phase 1)."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

import networkx as nx

from .events import FaultEvent, faults_to_legacy_dicts
from .faults import (
    FAULT_NODE_LOSS,
    FAULT_PACKET_DELAY,
    FAULT_PACKET_DROP,
    SUPPORTED_FAULTS,
)
from .schema import Topology, Workload, WorkloadTask
from .storage import faults_hash


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
class BenchmarkMetrics:
    """Schedule latency / utilization harness results."""

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
    experiment_id: str = ""
    events_executed: int = 0
    nodes_alive: int = 0
    latency_avg: float = 0.0
    checkpoint_id: str | None = None
    topology_hash: str | None = None
    workload_hash: str | None = None
    faults_hash: str | None = None

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
            "experiment_id": self.experiment_id,
            "events_executed": self.events_executed,
            "nodes_alive": self.nodes_alive,
            "latency_avg": self.latency_avg,
            "checkpoint_id": self.checkpoint_id,
            "topology_hash": self.topology_hash,
            "workload_hash": self.workload_hash,
            "faults_hash": self.faults_hash,
        }

    def run_summary(self) -> dict[str, Any]:
        """ChatGPT CLI output fields for `mesh twin run`."""
        return {
            "experiment_id": self.experiment_id,
            "seed": self.seed,
            "events_executed": self.events_executed,
            "nodes_alive": self.nodes_alive,
            "packets_sent": self.packets_sent,
            "packets_dropped": self.packets_dropped,
            "latency_avg": self.latency_avg,
            "checkpoint_id": self.checkpoint_id,
        }


class DigitalTwin:
    """Minimal deterministic mesh simulator with fault hooks + topology I/O."""

    def __init__(self, seed: int = 0):
        self.seed = int(seed)
        self.nodes: dict[str, TwinNode] = {}
        self.links: list[TwinLink] = []
        self.tasks: list[TwinTask] = []
        self.faults: list[FaultEvent] = []
        self.network_id: str = "twin-net"
        self._graph = nx.Graph()
        self._packet_seq = 0
        self._latency_samples: list[float] = []

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
        if fault.fault_type not in SUPPORTED_FAULTS:
            raise ValueError(f"unsupported fault_type: {fault.fault_type}")
        if fault.fault_type == FAULT_NODE_LOSS and fault.target_id not in self.nodes:
            raise ValueError(f"NODE_LOSS target unknown: {fault.target_id}")
        if fault.fault_type in {FAULT_PACKET_DROP, FAULT_PACKET_DELAY}:
            src, sep, dst = fault.target_id.partition("->")
            if not sep or src not in self.nodes or dst not in self.nodes:
                raise ValueError(
                    f"{fault.fault_type} target must be 'src->dst' with known nodes: "
                    f"{fault.target_id}"
                )
        # Prefer simulator seed when event seed is 0
        if fault.seed == 0 and self.seed:
            fault = FaultEvent(
                event_id=fault.event_id,
                fault_type=fault.fault_type,
                target_id=fault.target_id,
                tick=fault.tick,
                seed=self.seed,
                parameters=dict(fault.parameters),
            )
        self.faults.append(fault)

    def _faults_as_dicts(self) -> list[dict[str, Any]]:
        return faults_to_legacy_dicts(self.faults)

    def _node_alive(self, node_id: str, tick: int) -> bool:
        for f in self.faults:
            if f.fault_type != FAULT_NODE_LOSS or f.target_id != node_id:
                continue
            if tick < f.tick:
                continue
            if f.duration_ticks < 0 or tick < f.tick + f.duration_ticks:
                return False
        return True

    def _active_edge_faults(self, src: str, dst: str, tick: int) -> list[FaultEvent]:
        out: list[FaultEvent] = []
        for f in self.faults:
            if f.fault_type not in {FAULT_PACKET_DROP, FAULT_PACKET_DELAY}:
                continue
            a, _, b = f.target_id.partition("->")
            if {a, b} != {src, dst}:
                continue
            if tick < f.tick:
                continue
            if f.duration_ticks >= 0 and tick >= f.tick + f.duration_ticks:
                continue
            out.append(f)
        return out

    def _drop_rate_for_edge(self, src: str, dst: str, tick: int) -> float:
        rate = 0.0
        for f in self._active_edge_faults(src, dst, tick):
            if f.fault_type == FAULT_PACKET_DROP:
                rate = max(rate, f.drop_rate)
        return rate

    def _delay_for_edge(self, src: str, dst: str, tick: int) -> tuple[int, float]:
        delay_ticks = 0
        delay_ms = 0.0
        for f in self._active_edge_faults(src, dst, tick):
            if f.fault_type == FAULT_PACKET_DELAY:
                delay_ticks = max(delay_ticks, f.delay_ticks)
                delay_ms = max(delay_ms, f.delay_ms)
        return delay_ticks, delay_ms

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
        seed = self.seed
        h = hashlib.sha256(
            f"{seed}|{src}|{dst}|{tick}|{seq}".encode()
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
    ) -> tuple[int, int, bool, int, float]:
        """Simulate control-plane packets along a path from first alive node.

        Returns (sent, dropped, ok, delay_ticks, path_latency_ms).
        """
        sent = 0
        dropped = 0
        delay_ticks = 0
        path_latency = 0.0
        origins = [
            n for n in sorted(self.nodes) if n != node_id and self._node_alive(n, tick)
        ]
        if not origins:
            return 0, 0, True, 0, 0.0
        origin = origins[0]
        try:
            path = nx.shortest_path(self._graph, origin, node_id)
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            return 0, 0, False, 0, 0.0
        for i in range(len(path) - 1):
            a, b = path[i], path[i + 1]
            edge = self._graph.edges[a, b]
            path_latency += float(edge.get("latency_ms", 1.0))
            d_ticks, d_ms = self._delay_for_edge(a, b, tick)
            delay_ticks += d_ticks
            path_latency += d_ms
            hop_ok = False
            for _attempt in range(3):
                seq = self._packet_seq
                self._packet_seq += 1
                sent += 1
                if self.packet_survives(a, b, tick, seq):
                    hop_ok = True
                    break
                dropped += 1
            if not hop_ok:
                return sent, dropped, False, delay_ticks, path_latency
        return sent, dropped, True, delay_ticks, path_latency

    def _events_executed_count(self, ticks: int) -> int:
        return sum(1 for f in self.faults if f.tick <= ticks)

    def _nodes_alive_at(self, tick: int) -> int:
        return sum(1 for nid in self.nodes if self._node_alive(nid, tick))

    def _experiment_id(
        self,
        *,
        topology_hash: str,
        workload_hash: str,
        f_hash: str,
    ) -> str:
        blob = f"{self.seed}|{topology_hash}|{workload_hash}|{f_hash}".encode()
        return "EXP-" + hashlib.sha256(blob).hexdigest()[:8].upper()

    def run(self, ticks: int, *, with_metrics: bool = True) -> SimulationReport:
        """Run a deterministic schedule for ``ticks`` discrete time steps."""
        if ticks < 0:
            raise ValueError("ticks must be >= 0")
        if not self.nodes:
            raise ValueError("simulator requires at least one node")

        self._packet_seq = 0
        self._latency_samples = []
        busy_until: dict[str, int] = {nid: 0 for nid in self.nodes}
        running: dict[str, TaskResult] = {}
        schedule: list[TaskResult] = []
        pending = sorted(self.tasks, key=lambda t: (t.earliest_start, t.task_id))
        packets_sent = 0
        packets_dropped = 0

        for tick in range(ticks + 1):
            for nid, tr in list(running.items()):
                if not self._node_alive(nid, tick) and tr.end_tick > tick:
                    failed = TaskResult(
                        tr.task_id, tr.node_id, tr.start_tick, tick, "FAILED"
                    )
                    schedule = [
                        failed
                        if (s.task_id == tr.task_id and s.status == "RUNNING")
                        else s
                        for s in schedule
                    ]
                    if not any(
                        s.task_id == tr.task_id and s.status == "FAILED" for s in schedule
                    ):
                        schedule.append(failed)
                    del running[nid]
                    busy_until[nid] = tick

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
                sent, dropped, ok, delay_ticks, path_lat = self._simulate_placement_packets(
                    node_id, tick
                )
                packets_sent += sent
                packets_dropped += dropped
                if not ok:
                    still_pending.append(task)
                    continue
                if path_lat or delay_ticks:
                    self._latency_samples.append(path_lat + float(delay_ticks))
                # Apply PACKET_DELAY once: schedule at delayed start without re-injecting delay.
                start = tick + delay_ticks
                if start > ticks:
                    still_pending.append(task)
                    continue
                end = start + task.duration_ticks
                busy_until[node_id] = end
                tr = TaskResult(
                    task_id=task.task_id,
                    node_id=node_id,
                    start_tick=start,
                    end_tick=end,
                    status="COMPLETED" if end <= ticks else "RUNNING",
                )
                schedule.append(tr)
                if end > start:
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

        order = {t.task_id: i for i, t in enumerate(self.tasks)}
        finalized.sort(key=lambda r: order.get(r.task_id, 9999))

        topo = self.to_topology_model()
        workload = self.to_workload_model()
        t_hash = topo.hash()
        w_hash = workload.hash()
        f_hash = faults_hash(self.faults)
        latency_avg = (
            sum(self._latency_samples) / len(self._latency_samples)
            if self._latency_samples
            else 0.0
        )

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
            experiment_id=self._experiment_id(
                topology_hash=t_hash, workload_hash=w_hash, f_hash=f_hash
            ),
            events_executed=self._events_executed_count(ticks),
            nodes_alive=self._nodes_alive_at(ticks),
            latency_avg=latency_avg,
            checkpoint_id=None,
            topology_hash=t_hash,
            workload_hash=w_hash,
            faults_hash=f_hash,
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

    def to_topology_model(self) -> Topology:
        from .schema import TopologyLink, TopologyNode

        return Topology(
            network_id=self.network_id,
            seed=self.seed,
            nodes=[
                TopologyNode(
                    id=n.node_id,
                    cpu=n.cpu_cores,
                    memory=int(n.memory_gb * 1000),
                    capabilities=list(n.capabilities),
                    gpu_count=n.gpu_count,
                    privacy_zone=n.privacy_zone,
                )
                for n in self.nodes.values()
            ],
            links=[
                TopologyLink(
                    source=lnk.src,
                    target=lnk.dst,
                    latency_ms=lnk.latency_ms,
                    bandwidth_mbps=lnk.bandwidth_mbps,
                )
                for lnk in self.links
            ],
        )

    def to_workload_model(self) -> Workload:
        return Workload(
            workload_id="twin-workload",
            tasks=[
                WorkloadTask(
                    task_id=t.task_id,
                    cpu_need=t.cpu_need,
                    duration_ticks=t.duration_ticks,
                    earliest_start=t.earliest_start,
                    preferred_capabilities=list(t.preferred_capabilities),
                )
                for t in self.tasks
            ],
        )

    def to_topology_dict(self) -> dict[str, Any]:
        # Cycle-2 compatible blob (includes tasks + faults for round-trip).
        return {
            "seed": self.seed,
            "network_id": self.network_id,
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
            "faults": [f.to_dict() for f in sorted(
                self.faults,
                key=lambda e: (e.tick, e.fault_type, e.target_id, e.event_id),
            )],
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
        twin.network_id = str(data.get("network_id", "twin-net"))
        for n in data.get("nodes", []):
            nid = str(n.get("node_id") or n.get("id"))
            if "cpu_cores" in n:
                cpu = int(n["cpu_cores"])
            else:
                cpu = int(n.get("cpu", 4))
            if "memory_gb" in n:
                mem = float(n["memory_gb"])
            else:
                mem = float(n.get("memory", 16000)) / 1000.0
            twin.add_node(
                TwinNode(
                    node_id=nid,
                    cpu_cores=cpu,
                    memory_gb=mem,
                    gpu_count=int(n.get("gpu_count", 0)),
                    privacy_zone=str(n.get("privacy_zone", "default")),
                    capabilities=tuple(n.get("capabilities", ["compute"])),
                )
            )
        for lnk in data.get("links", []):
            src = str(lnk.get("src") or lnk.get("source"))
            dst = str(lnk.get("dst") or lnk.get("target"))
            twin.add_link(
                TwinLink(
                    src=src,
                    dst=dst,
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
            twin.inject_fault(FaultEvent.from_dict(f))
        return twin

    @classmethod
    def from_parts(
        cls,
        topology: Topology,
        workload: Workload | None = None,
        faults: list[FaultEvent] | None = None,
        seed: int | None = None,
    ) -> DigitalTwin:
        twin = cls(seed=int(seed if seed is not None else topology.seed))
        twin.network_id = topology.network_id
        for n in topology.nodes:
            twin.add_node(
                TwinNode(
                    node_id=n.id,
                    cpu_cores=n.cpu,
                    memory_gb=n.memory / 1000.0,
                    gpu_count=n.gpu_count,
                    privacy_zone=n.privacy_zone,
                    capabilities=tuple(n.capabilities),
                )
            )
        for lnk in topology.links:
            twin.add_link(
                TwinLink(
                    src=lnk.source,
                    dst=lnk.target,
                    latency_ms=lnk.latency_ms,
                    bandwidth_mbps=lnk.bandwidth_mbps,
                )
            )
        if workload:
            for t in workload.tasks:
                twin.add_task(
                    TwinTask(
                        task_id=t.task_id,
                        cpu_need=t.cpu_need,
                        duration_ticks=t.duration_ticks,
                        earliest_start=t.earliest_start,
                        preferred_capabilities=tuple(t.preferred_capabilities),
                    )
                )
        for f in faults or []:
            twin.inject_fault(f)
        return twin

    @staticmethod
    def build_demo(seed: int = 42) -> DigitalTwin:
        """Build the canonical demo topology (no run)."""
        twin = DigitalTwin(seed=seed)
        twin.network_id = "demo-net"
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
