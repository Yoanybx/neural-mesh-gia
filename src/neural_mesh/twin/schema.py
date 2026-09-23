"""JSON topology / workload schema with stable hashing."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


def _canonical_json(data: Any) -> str:
    return json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _sha256_hex(data: Any) -> str:
    return hashlib.sha256(_canonical_json(data).encode("utf-8")).hexdigest()


@dataclass
class TopologyNode:
    id: str
    cpu: int = 4
    memory: int = 16000  # MB (ChatGPT schema); memory_gb derived if needed
    capabilities: list[str] = field(default_factory=lambda: ["compute"])
    gpu_count: int = 0
    privacy_zone: str = "default"

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "cpu": int(self.cpu),
            "memory": int(self.memory),
            "capabilities": list(self.capabilities),
            "gpu_count": int(self.gpu_count),
            "privacy_zone": self.privacy_zone,
        }


@dataclass
class TopologyLink:
    source: str
    target: str
    latency_ms: float = 1.0
    bandwidth_mbps: float = 1000.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "source": self.source,
            "target": self.target,
            "latency_ms": float(self.latency_ms),
            "bandwidth_mbps": float(self.bandwidth_mbps),
        }


@dataclass
class Topology:
    """Network topology (ChatGPT P1 schema)."""

    network_id: str
    seed: int = 0
    nodes: list[TopologyNode] = field(default_factory=list)
    links: list[TopologyLink] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "network_id": self.network_id,
            "seed": self.seed,
            "nodes": [
                n.to_dict()
                for n in sorted(self.nodes, key=lambda x: x.id)
            ],
            "links": [
                lnk.to_dict()
                for lnk in sorted(self.links, key=lambda x: (x.source, x.target))
            ],
        }

    def hash(self) -> str:
        return _sha256_hex(self.to_dict())

    def save(self, path: str | Path) -> None:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(self.to_dict(), indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

    @classmethod
    def load(cls, path: str | Path) -> Topology:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        return cls.from_dict(data)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Topology:
        network_id = str(data.get("network_id") or data.get("id") or "unnamed-net")
        seed = int(data.get("seed", 0))
        nodes: list[TopologyNode] = []
        for n in data.get("nodes", []):
            # ChatGPT: id/cpu/memory ; Cycle-2: node_id/cpu_cores/memory_gb
            nid = str(n.get("id") or n.get("node_id"))
            if "cpu" in n:
                cpu = int(n["cpu"])
            else:
                cpu = int(n.get("cpu_cores", 4))
            if "memory" in n:
                memory = int(n["memory"])
            else:
                memory = int(float(n.get("memory_gb", 16.0)) * 1000)
            nodes.append(
                TopologyNode(
                    id=nid,
                    cpu=cpu,
                    memory=memory,
                    capabilities=list(n.get("capabilities", ["compute"])),
                    gpu_count=int(n.get("gpu_count", 0)),
                    privacy_zone=str(n.get("privacy_zone", "default")),
                )
            )
        links: list[TopologyLink] = []
        for lnk in data.get("links", []):
            src = str(lnk.get("source") or lnk.get("src"))
            dst = str(lnk.get("target") or lnk.get("dst"))
            links.append(
                TopologyLink(
                    source=src,
                    target=dst,
                    latency_ms=float(lnk.get("latency_ms", 1.0)),
                    bandwidth_mbps=float(lnk.get("bandwidth_mbps", 1000.0)),
                )
            )
        return cls(network_id=network_id, seed=seed, nodes=nodes, links=links)


@dataclass
class WorkloadTask:
    task_id: str
    cpu_need: float
    duration_ticks: int
    earliest_start: int = 0
    preferred_capabilities: list[str] = field(default_factory=lambda: ["compute"])

    def to_dict(self) -> dict[str, Any]:
        return {
            "task_id": self.task_id,
            "cpu_need": float(self.cpu_need),
            "duration_ticks": int(self.duration_ticks),
            "earliest_start": int(self.earliest_start),
            "preferred_capabilities": list(self.preferred_capabilities),
        }


@dataclass
class Workload:
    workload_id: str = "default"
    tasks: list[WorkloadTask] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "workload_id": self.workload_id,
            "tasks": [t.to_dict() for t in self.tasks],
        }

    def hash(self) -> str:
        return _sha256_hex(self.to_dict())

    def save(self, path: str | Path) -> None:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(self.to_dict(), indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

    @classmethod
    def load(cls, path: str | Path) -> Workload:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        return cls.from_dict(data)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Workload:
        # Accept bare task list or {workload_id, tasks} or legacy topology-with-tasks.
        if isinstance(data, list):
            tasks_raw = data
            wid = "default"
        else:
            tasks_raw = data.get("tasks", [])
            wid = str(data.get("workload_id", "default"))
        tasks = [
            WorkloadTask(
                task_id=str(t["task_id"]),
                cpu_need=float(t["cpu_need"]),
                duration_ticks=int(t["duration_ticks"]),
                earliest_start=int(t.get("earliest_start", 0)),
                preferred_capabilities=list(
                    t.get("preferred_capabilities", ["compute"])
                ),
            )
            for t in tasks_raw
        ]
        return cls(workload_id=wid, tasks=tasks)
