"""CLI: mesh router route|explain."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MESH = [sys.executable, "-m", "neural_mesh.cli"]


def _run(args: list[str], *, cwd: Path):
    return subprocess.run(MESH + args, cwd=cwd, capture_output=True, text=True)


def test_mesh_router_route_and_explain(tmp_path: Path):
    from neural_mesh.safety import ensure_default_policy

    ensure_default_policy(tmp_path)
    log = tmp_path / "dec.jsonl"
    r = _run(
        [
            "router",
            "route",
            "task-cli-1",
            "--seed",
            "0",
            "--log",
            str(log),
            "--json",
        ],
        cwd=tmp_path,
    )
    assert r.returncode == 0, r.stderr
    data = json.loads(r.stdout)
    assert data["task_id"] == "task-cli-1"
    assert data["strategy"] == "ROUND_ROBIN"
    assert data["decision"]

    e = _run(["router", "explain", "task-cli-1", "--log", str(log)], cwd=tmp_path)
    assert e.returncode == 0, e.stderr
    exp = json.loads(e.stdout)
    assert exp["task_id"] == "task-cli-1"
    assert exp["decision"] == data["decision"]


def test_mesh_router_explain_safety_block(tmp_path: Path):
    from neural_mesh.safety import ensure_default_policy

    ensure_default_policy(tmp_path)
    r = _run(
        ["router", "route", "net-x", "--requires-network", "--seed", "1"],
        cwd=tmp_path,
    )
    assert r.returncode == 3
    out = json.loads(r.stdout)
    assert out["strategy"] == "SAFETY_POLICY_BLOCKS_NETWORK"
    assert out["decision"] is None
