from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

from .checkpoint import CheckpointManager
from .digital_twin import DigitalTwin
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
    run_p = twins.add_parser("run")
    run_p.add_argument("--seed", type=int, default=42)
    run_p.add_argument("--ticks", type=int, default=20)
    run_p.add_argument("--json", action="store_true")

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
        if a.op == "run":
            report = DigitalTwin.demo(seed=a.seed, ticks=a.ticks)
            if a.json:
                print(json.dumps(report.to_dict(), indent=2))
            else:
                print(f"seed={report.seed} ticks={report.ticks} digest={report.digest}")
                for r in report.schedule:
                    print(
                        f"  {r.task_id} -> {r.node_id or '-'} "
                        f"[{r.start_tick},{r.end_tick}] {r.status}"
                    )


if __name__ == "__main__":
    main()
