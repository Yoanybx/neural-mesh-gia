"""Experiment runner — `mesh benchmark run twin-basic`."""

from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from neural_mesh.twin.events import FaultEvent
from neural_mesh.twin.faults import FAULT_NODE_LOSS, FAULT_PACKET_DROP
from neural_mesh.twin.simulator import DigitalTwin
from neural_mesh.twin.storage import save_faults, save_json

from .metrics import build_metrics
from neural_mesh.cram import CRAMStore, ObjectType
from neural_mesh.cram.recovery import recover_after_node_loss
from neural_mesh.twin.placement import CRAMPlacement


@dataclass
class ExperimentResult:
    experiment_id: str
    duration_ms: int
    metrics: dict[str, Any]
    artifacts: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _next_exp_id(experiments_dir: Path) -> str:
    existing = sorted(experiments_dir.glob("EXP-*"))
    n = 1
    if existing:
        nums = []
        for p in existing:
            parts = p.name.split("-")
            if len(parts) >= 2 and parts[1].isdigit():
                nums.append(int(parts[1]))
        if nums:
            n = max(nums) + 1
    return f"EXP-{n:04d}"


def run_twin_basic(
    root: str | Path,
    *,
    seed: int = 42,
    ticks: int = 20,
    git_commit: str | None = None,
    experiments_dir: str | Path | None = None,
) -> ExperimentResult:
    """Run the canonical twin-basic experiment and write artifacts under experiments/."""
    root = Path(root)
    experiments_dir = Path(experiments_dir) if experiments_dir else root / "experiments"
    experiments_dir.mkdir(parents=True, exist_ok=True)
    exp_id = _next_exp_id(experiments_dir)
    exp_dir = experiments_dir / exp_id
    exp_dir.mkdir(parents=True, exist_ok=False)

    twin = DigitalTwin.build_demo(seed=seed)
    twin.inject_fault(
        FaultEvent.create(FAULT_NODE_LOSS, "n1", at_tick=5, duration_ticks=3, seed=seed)
    )
    twin.inject_fault(
        FaultEvent.create(
            FAULT_PACKET_DROP,
            "n0->n2",
            at_tick=0,
            drop_rate=0.25,
            seed=seed,
        )
    )

    t0 = time.perf_counter()
    report = twin.run(ticks=ticks)
    duration_ms = int((time.perf_counter() - t0) * 1000)

    topology = twin.to_topology_model()
    workload = twin.to_workload_model()
    topology_path = exp_dir / "topology.json"
    workload_path = exp_dir / "workload.json"
    faults_path = exp_dir / "faults.json"
    result_path = exp_dir / "result.json"
    checkpoint_path = exp_dir / "checkpoint.json"

    topology.save(topology_path)
    workload.save(workload_path)
    save_faults(faults_path, twin.faults)

    topo_hash = topology.hash()
    work_hash = workload.hash()
    checkpoint_id = f"{exp_id}-CP"
    report.checkpoint_id = checkpoint_id

    # Experiment-local checkpoint evidence (ChatGPT shape); does not mutate snapshots/.
    checkpoint_doc = {
        "checkpoint_id": checkpoint_id,
        "experiment_id": exp_id,
        "module": "benchmark",
        "reason": "twin-basic",
        "seed": seed,
        "topology_hash": topo_hash,
        "workload_hash": work_hash,
        "faults_hash": report.faults_hash,
        "digest": report.digest,
        "git_commit": git_commit,
        "status": "VERIFIED",
    }
    checkpoint_path.write_text(
        json.dumps(checkpoint_doc, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    # Cycle 5 P0: real recovery_time (locate+get) — not STUB
    cram_root = exp_dir / "cram"
    store = CRAMStore(cram_root)
    place = CRAMPlacement()
    topo_model = topology
    sample_key = store.put_object(
        b"twin-basic-recovery-sample", ObjectType.EVIDENCE
    ).content_hash
    owner = place.locate(sample_key, topo_model)
    store.bind_to_node(sample_key, owner)
    # Lose a non-owner when possible so locate resolves (measured RECOVERABLE path)
    node_ids = sorted(n.id for n in topo_model.nodes)
    others = [n for n in node_ids if n != owner]
    lost = others[0] if others else owner
    store.mark_node_lost(lost)
    recovery = recover_after_node_loss(
        store, place, topo_model, sample_key, lost_nodes=[lost]
    )
    recovery_ms = recovery.recovery_time_ms

    metrics = build_metrics(
        report, duration_ms=duration_ms, recovery_time_ms=recovery_ms
    )
    metrics["recovery_detail"] = recovery.to_dict()
    metrics["digest"] = report.digest
    metrics["topology_hash"] = topo_hash
    metrics["workload_hash"] = work_hash
    metrics["seed"] = seed
    metrics["checkpoint_id"] = checkpoint_id

    artifacts = [
        "topology.json",
        "workload.json",
        "faults.json",
        "checkpoint.json",
        "result.json",
    ]
    result = ExperimentResult(
        experiment_id=exp_id,
        duration_ms=duration_ms,
        metrics=metrics,
        artifacts=artifacts,
    )
    payload = result.to_dict()
    payload["run_summary"] = report.run_summary()
    payload["schedule_digest"] = report.digest
    payload["artifact_dir"] = str(exp_dir)
    save_json(result_path, payload)
    return result
