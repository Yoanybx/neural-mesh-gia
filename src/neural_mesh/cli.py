from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

from .checkpoint import CheckpointManager
from .digital_twin import (
    FAULT_NODE_LOSS,
    FAULT_PACKET_DROP,
    DigitalTwin,
    FaultEvent,
)
from .obsidian import ObsidianSync


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


def _load_twin(topology: str | None, seed: int) -> DigitalTwin:
    if topology:
        twin = DigitalTwin.load_topology(topology)
        if seed is not None:
            twin.seed = int(seed)
        return twin
    return DigitalTwin.build_demo(seed=seed)


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

    run_p = twins.add_parser("run", help="Run twin simulation (demo or topology file)")
    run_p.add_argument("--seed", type=int, default=42)
    run_p.add_argument("--ticks", type=int, default=20)
    run_p.add_argument("--topology", type=str, default=None, help="JSON topology path")
    run_p.add_argument(
        "--fault",
        action="append",
        default=[],
        metavar="SPEC",
        help="Fault SPEC: NODE_LOSS:node:at_tick[:duration] or "
        "PACKET_DROP:src->dst:at_tick:rate[:duration]",
    )
    run_p.add_argument("--json", action="store_true")

    top_p = twins.add_parser("topology", help="Save/load demo or file topology")
    tops = top_p.add_subparsers(dest="top_op", required=True)
    save_p = tops.add_parser("save")
    save_p.add_argument("path")
    save_p.add_argument("--seed", type=int, default=42)
    save_p.add_argument(
        "--from",
        dest="from_path",
        default=None,
        help="Copy existing topology JSON (default: write demo)",
    )
    load_p = tops.add_parser("load")
    load_p.add_argument("path")
    load_p.add_argument("--json", action="store_true")

    bench_p = twins.add_parser("bench", help="Benchmark schedule latency / utilization")
    bench_p.add_argument("--seed", type=int, default=42)
    bench_p.add_argument("--ticks", type=int, default=20)
    bench_p.add_argument("--topology", type=str, default=None)
    bench_p.add_argument("--fault", action="append", default=[])
    bench_p.add_argument("--json", action="store_true")

    a = parser.parse_args(argv)
    root = Path.cwd()
    mgr = CheckpointManager(root)

    if a.cmd == "init":
        mgr.save_state(mgr.load_state())
        ObsidianSync(root).bootstrap()
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
    elif a.cmd == "twin":
        if a.op == "topology":
            if a.top_op == "save":
                if a.from_path:
                    twin = DigitalTwin.load_topology(a.from_path)
                else:
                    twin = DigitalTwin.build_demo(seed=a.seed)
                twin.save_topology(a.path)
                print(a.path)
            elif a.top_op == "load":
                twin = DigitalTwin.load_topology(a.path)
                if a.json:
                    print(json.dumps(twin.to_topology_dict(), indent=2))
                else:
                    print(
                        f"seed={twin.seed} nodes={len(twin.nodes)} "
                        f"links={len(twin.links)} tasks={len(twin.tasks)} "
                        f"faults={len(twin.faults)}"
                    )
        elif a.op in {"run", "bench"}:
            twin = _load_twin(a.topology, a.seed)
            for spec in a.fault:
                twin.inject_fault(_parse_fault(spec))
            report = twin.run(ticks=a.ticks)
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
            else:
                print(
                    f"seed={report.seed} ticks={report.ticks} digest={report.digest}"
                )
                for r in report.schedule:
                    print(
                        f"  {r.task_id} -> {r.node_id or '-'} "
                        f"[{r.start_tick},{r.end_tick}] {r.status}"
                    )
                if report.packets_sent:
                    print(
                        f"  packets: sent={report.packets_sent} "
                        f"dropped={report.packets_dropped}"
                    )


def _parse_fault(spec: str) -> FaultEvent:
    """Parse CLI fault SPEC into FaultEvent."""
    parts = spec.split(":")
    if not parts:
        raise SystemExit(f"invalid fault SPEC: {spec}")
    kind = parts[0].upper()
    if kind == FAULT_NODE_LOSS:
        # NODE_LOSS:node:at_tick[:duration]
        if len(parts) < 3:
            raise SystemExit(
                "NODE_LOSS SPEC requires NODE_LOSS:node:at_tick[:duration]"
            )
        duration = int(parts[3]) if len(parts) > 3 else -1
        return FaultEvent(
            fault_type=FAULT_NODE_LOSS,
            target=parts[1],
            at_tick=int(parts[2]),
            duration_ticks=duration,
        )
    if kind == FAULT_PACKET_DROP:
        # PACKET_DROP:src->dst:at_tick:rate[:duration]
        if len(parts) < 4:
            raise SystemExit(
                "PACKET_DROP SPEC requires "
                "PACKET_DROP:src->dst:at_tick:rate[:duration]"
            )
        duration = int(parts[4]) if len(parts) > 4 else -1
        return FaultEvent(
            fault_type=FAULT_PACKET_DROP,
            target=parts[1],
            at_tick=int(parts[2]),
            drop_rate=float(parts[3]),
            duration_ticks=duration,
        )
    raise SystemExit(f"unsupported fault type: {kind}")


if __name__ == "__main__":
    main()
