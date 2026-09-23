from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

from .benchmark.runner import run_twin_basic
from .checkpoint import CheckpointManager
from .git_audit import audit_git
from .obsidian import ObsidianSync
from .safety import ensure_default_policy, safety_status
from .twin.events import FaultEvent
from .twin.faults import (
    FAULT_NODE_LOSS,
    FAULT_PACKET_DELAY,
    FAULT_PACKET_DROP,
)
from .twin.schema import Topology, Workload
from .twin.simulator import DigitalTwin, TwinTask
from .twin.storage import load_faults


def _git_commit(root: Path) -> str | None:
    try:
        out = subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=root,
            stderr=subprocess.DEVNULL,
            text=True,
        ).strip()
        return out or None
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None


def _load_twin(
    *,
    topology: str | None,
    workload: str | None,
    faults: str | None,
    seed: int,
) -> DigitalTwin:
    if topology:
        raw = json.loads(Path(topology).read_text(encoding="utf-8"))
        if "tasks" in raw or "faults" in raw:
            twin = DigitalTwin.from_topology_dict(raw)
        else:
            topo = Topology.from_dict(raw)
            wl = Workload.load(workload) if workload else Workload()
            twin = DigitalTwin.from_parts(topo, wl, seed=seed)
        twin.seed = int(seed)
    else:
        twin = DigitalTwin.build_demo(seed=seed)
        if workload:
            wl = Workload.load(workload)
            twin.tasks = []
            for t in wl.tasks:
                twin.add_task(
                    TwinTask(
                        task_id=t.task_id,
                        cpu_need=t.cpu_need,
                        duration_ticks=t.duration_ticks,
                        earliest_start=t.earliest_start,
                        preferred_capabilities=tuple(t.preferred_capabilities),
                    )
                )
    if faults:
        for f in load_faults(faults):
            twin.inject_fault(f)
    return twin


def main(argv: list[str] | None = None):
    parser = argparse.ArgumentParser(prog="mesh")
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("init")
    sub.add_parser("resume")
    sub.add_parser("status")
    sub.add_parser("agent-context")

    cp = sub.add_parser("checkpoint")
    cps = cp.add_subparsers(dest="op", required=True)
    c = cps.add_parser("create")
    c.add_argument("--phase", type=int, default=0)
    c.add_argument("--module", default="unknown")
    c.add_argument("--reason", default="manual")
    c.add_argument("--next", dest="next_action", required=True)
    c.add_argument("--evidence", action="append", default=[])
    c.add_argument("--tests-passed", type=int, default=None)
    c.add_argument("--tests-failed", type=int, default=None)
    c.add_argument("--status", default=None)
    c = cps.add_parser("verify")
    c.add_argument("id")
    cps.add_parser("latest")
    cps.add_parser("list")

    twin = sub.add_parser("twin")
    twins = twin.add_subparsers(dest="op", required=True)

    run_p = twins.add_parser("run", help="Run twin simulation (demo or JSON inputs)")
    run_p.add_argument("--seed", type=int, default=42)
    run_p.add_argument("--ticks", type=int, default=20)
    run_p.add_argument("--topology", type=str, default=None)
    run_p.add_argument("--workload", type=str, default=None)
    run_p.add_argument("--faults", type=str, default=None)
    run_p.add_argument("--fault", action="append", default=[], metavar="SPEC")
    run_p.add_argument("--json", action="store_true")
    run_p.add_argument("--summary", action="store_true")

    top_p = twins.add_parser("topology", help="Save/load demo or file topology")
    tops = top_p.add_subparsers(dest="top_op", required=True)
    save_p = tops.add_parser("save")
    save_p.add_argument("path")
    save_p.add_argument("--seed", type=int, default=42)
    save_p.add_argument("--from", dest="from_path", default=None)
    save_p.add_argument(
        "--schema", choices=("legacy", "chatgpt"), default="legacy"
    )
    load_p = tops.add_parser("load")
    load_p.add_argument("path")
    load_p.add_argument("--json", action="store_true")

    bench_p = twins.add_parser("bench", help="Benchmark schedule latency / utilization")
    bench_p.add_argument("--seed", type=int, default=42)
    bench_p.add_argument("--ticks", type=int, default=20)
    bench_p.add_argument("--topology", type=str, default=None)
    bench_p.add_argument("--workload", type=str, default=None)
    bench_p.add_argument("--faults", type=str, default=None)
    bench_p.add_argument("--fault", action="append", default=[])
    bench_p.add_argument("--json", action="store_true")

    bench_cmd = sub.add_parser("benchmark")
    bench_subs = bench_cmd.add_subparsers(dest="op", required=True)
    br = bench_subs.add_parser("run")
    br.add_argument("suite", choices=("twin-basic",))
    br.add_argument("--seed", type=int, default=42)
    br.add_argument("--ticks", type=int, default=20)
    br.add_argument("--json", action="store_true")

    audit_cmd = sub.add_parser("audit")
    audit_subs = audit_cmd.add_subparsers(dest="op", required=True)
    audit_subs.add_parser("git")

    safety_cmd = sub.add_parser("safety")
    safety_subs = safety_cmd.add_subparsers(dest="op", required=True)
    safety_subs.add_parser("status")

    a = parser.parse_args(argv)
    root = Path.cwd()
    mgr = CheckpointManager(root)

    if a.cmd == "init":
        mgr.save_state(mgr.load_state())
        ObsidianSync(root).bootstrap()
        ensure_default_policy(root)
        print("initialized")
    elif a.cmd == "status":
        print(mgr.load_state().model_dump_json(indent=2))
    elif a.cmd == "resume":
        s = mgr.load_state()
        print("NEURAL MESH RECOVERY")
        print(s.model_dump_json(indent=2))
        na = root / ".project_state" / "NEXT_ACTION.md"
        if na.exists():
            print("--- NEXT_ACTION ---")
            print(na.read_text(encoding="utf-8"))
    elif a.cmd == "agent-context":
        s = mgr.load_state()
        p = root / ".agent_context.md"
        p.write_text(
            "# AGENT CONTEXT\n\nRead .project_state/CURRENT_STATE.md, "
            ".project_state/NEXT_ACTION.md, .project_state/CHECKPOINT.json and "
            ".project_state/DECISIONS.md before changing code.\n\n"
            + s.model_dump_json(indent=2),
            encoding="utf-8",
        )
        print(p)
    elif a.cmd == "checkpoint":
        if a.op == "create":
            tests = {}
            if a.tests_passed is not None:
                tests["passed"] = a.tests_passed
            if a.tests_failed is not None:
                tests["failed"] = a.tests_failed
            cp_obj = mgr.create(
                a.phase,
                a.module,
                a.reason,
                a.next_action,
                git_commit=_git_commit(root),
                tests=tests or None,
                evidence=a.evidence,
                status=a.status,
            )
            ObsidianSync(root).record_checkpoint(cp_obj)
            print(cp_obj.checkpoint_id)
        elif a.op == "verify":
            print("VERIFIED" if mgr.verify(a.id) else "FAILED")
        elif a.op == "latest":
            latest = mgr.latest()
            print(latest.model_dump_json(indent=2) if latest else "NONE")
        elif a.op == "list":
            print("\n".join(mgr.list_ids()))
    elif a.cmd == "audit":
        if a.op == "git":
            result = audit_git(root)
            print(result.status_line)
            print(f"branch: {result.branch}")
            print(f"commit: {result.commit}")
            print(f"modified: {len(result.modified)}")
            for p in result.modified:
                print(f"  M {p}")
            print(f"untracked: {len(result.untracked)}")
            for p in result.untracked:
                print(f"  ? {p}")
            if result.error:
                print(f"error: {result.error}")
            raise SystemExit(0 if result.ok else 1)
    elif a.cmd == "safety":
        if a.op == "status":
            ensure_default_policy(root)
            st = safety_status(root)
            print(json.dumps(st.to_dict(), indent=2, sort_keys=True))
            print(f"SAFETY: {st.status}")
    elif a.cmd == "benchmark":
        if a.op == "run" and a.suite == "twin-basic":
            result = run_twin_basic(
                root,
                seed=a.seed,
                ticks=a.ticks,
                git_commit=_git_commit(root),
            )
            if a.json:
                print(json.dumps(result.to_dict(), indent=2))
            else:
                print(
                    f"experiment_id={result.experiment_id} "
                    f"duration_ms={result.duration_ms}"
                )
                print(f"artifacts={','.join(result.artifacts)}")
                print(
                    f"topology_hash={result.metrics.get('topology_hash')} "
                    f"checkpoint_id={result.metrics.get('checkpoint_id')}"
                )
    elif a.cmd == "twin":
        if a.op == "topology":
            if a.top_op == "save":
                if a.from_path:
                    twin_obj = DigitalTwin.load_topology(a.from_path)
                else:
                    twin_obj = DigitalTwin.build_demo(seed=a.seed)
                if a.schema == "chatgpt":
                    twin_obj.to_topology_model().save(a.path)
                else:
                    twin_obj.save_topology(a.path)
                print(a.path)
            elif a.top_op == "load":
                raw = json.loads(Path(a.path).read_text(encoding="utf-8"))
                nodes = raw.get("nodes") or []
                legacy = (
                    "tasks" in raw
                    or "faults" in raw
                    or (nodes and "node_id" in nodes[0])
                )
                if legacy:
                    twin_obj = DigitalTwin.load_topology(a.path)
                    info = (
                        f"seed={twin_obj.seed} nodes={len(twin_obj.nodes)} "
                        f"links={len(twin_obj.links)} tasks={len(twin_obj.tasks)} "
                        f"faults={len(twin_obj.faults)}"
                    )
                    payload = twin_obj.to_topology_dict()
                else:
                    topo = Topology.load(a.path)
                    info = (
                        f"network_id={topo.network_id} seed={topo.seed} "
                        f"nodes={len(topo.nodes)} links={len(topo.links)} "
                        f"hash={topo.hash()}"
                    )
                    payload = topo.to_dict()
                if a.json:
                    print(json.dumps(payload, indent=2))
                else:
                    print(info)
        elif a.op in {"run", "bench"}:
            twin_obj = _load_twin(
                topology=a.topology,
                workload=getattr(a, "workload", None),
                faults=getattr(a, "faults", None),
                seed=a.seed,
            )
            for spec in a.fault:
                twin_obj.inject_fault(_parse_fault(spec, seed=a.seed))
            report = twin_obj.run(ticks=a.ticks)
            if a.op == "bench" or a.json:
                if a.json:
                    print(json.dumps(report.to_dict(), indent=2))
                else:
                    m = report.metrics
                    assert m is not None
                    print(
                        f"seed={report.seed} ticks={report.ticks} digest={report.digest}"
                    )
                    print(
                        f"makespan={m.makespan} mean_wait={m.mean_wait_ticks:.3f} "
                        f"mean_latency={m.mean_latency_ticks:.3f} "
                        f"utilization={m.utilization:.3f}"
                    )
                    print(
                        f"scheduled={m.scheduled_count} failed={m.failed_count} "
                        f"unscheduled={m.unscheduled_count} "
                        f"pkt_drop_rate={m.packet_drop_rate:.3f} "
                        f"({m.packets_dropped}/{m.packets_sent})"
                    )
            elif getattr(a, "summary", False):
                print(json.dumps(report.run_summary(), indent=2, sort_keys=True))
            else:
                s = report.run_summary()
                print(
                    f"experiment_id={s['experiment_id']} seed={s['seed']} "
                    f"events_executed={s['events_executed']} "
                    f"nodes_alive={s['nodes_alive']} "
                    f"packets_sent={s['packets_sent']} "
                    f"packets_dropped={s['packets_dropped']} "
                    f"latency_avg={s['latency_avg']:.3f} "
                    f"checkpoint_id={s['checkpoint_id']}"
                )
                print(f"digest={report.digest}")
                for r in report.schedule:
                    print(
                        f"  {r.task_id} -> {r.node_id or '-'} "
                        f"[{r.start_tick},{r.end_tick}] {r.status}"
                    )


def _parse_fault(spec: str, seed: int = 0) -> FaultEvent:
    parts = spec.split(":")
    if not parts:
        raise SystemExit(f"invalid fault SPEC: {spec}")
    kind = parts[0].upper()
    if kind == FAULT_NODE_LOSS:
        if len(parts) < 3:
            raise SystemExit(
                "NODE_LOSS SPEC requires NODE_LOSS:node:at_tick[:duration]"
            )
        duration = int(parts[3]) if len(parts) > 3 else -1
        return FaultEvent.create(
            FAULT_NODE_LOSS,
            parts[1],
            at_tick=int(parts[2]),
            duration_ticks=duration,
            seed=seed,
        )
    if kind == FAULT_PACKET_DROP:
        if len(parts) < 4:
            raise SystemExit(
                "PACKET_DROP SPEC requires "
                "PACKET_DROP:src->dst:at_tick:rate[:duration]"
            )
        duration = int(parts[4]) if len(parts) > 4 else -1
        return FaultEvent.create(
            FAULT_PACKET_DROP,
            parts[1],
            at_tick=int(parts[2]),
            drop_rate=float(parts[3]),
            duration_ticks=duration,
            seed=seed,
        )
    if kind == FAULT_PACKET_DELAY:
        if len(parts) < 4:
            raise SystemExit(
                "PACKET_DELAY SPEC requires "
                "PACKET_DELAY:src->dst:at_tick:delay_ticks[:delay_ms]"
            )
        delay_ms = float(parts[4]) if len(parts) > 4 else 0.0
        return FaultEvent.create(
            FAULT_PACKET_DELAY,
            parts[1],
            at_tick=int(parts[2]),
            delay_ticks=int(parts[3]),
            delay_ms=delay_ms,
            seed=seed,
        )
    raise SystemExit(f"unsupported fault type: {kind}")


if __name__ == "__main__":
    main()
