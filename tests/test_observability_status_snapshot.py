"""Cycle 19 / CP-0023 — Mesh Observability Status Snapshot (≥12 tests)."""

from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from neural_mesh.status_snapshot import (
    SCHEMA_ID,
    StatusSnapshot,
    format_obs_m2m,
    snapshot,
    snapshot_to_dict,
    snapshot_to_json,
)
from neural_mesh import status as status_mod

ROOT = Path(__file__).resolve().parents[1]
MESH = [sys.executable, "-m", "neural_mesh.cli"]

REQUIRED_TOP_KEYS = {
    "schema",
    "node_id",
    "cycle",
    "ver",
    "tip",
    "cp_range",
    "cp_tip",
    "pytest",
    "slo_state",
    "debt_gates",
    "peers",
    "local",
}


def _write_mini_root(tmp: Path, *, ver: str = "0.15.0", cp: str = "CP-0023") -> Path:
    """Minimal repo-like tree for local snapshot tests (no network)."""
    (tmp / ".project_state").mkdir(parents=True)
    (tmp / "docs" / "debt").mkdir(parents=True)
    (tmp / "snapshots" / "CP-0001").mkdir(parents=True)
    (tmp / "snapshots" / cp).mkdir(parents=True)
    (tmp / "pyproject.toml").write_text(
        f'[project]\nname = "neural-mesh-gia"\nversion = "{ver}"\n',
        encoding="utf-8",
    )
    state = {
        "last_checkpoint": cp,
        "project_version": ver,
        "current_phase": 5,
        "current_module": "mesh-observability",
        "safety_status": "SAFE",
        "status": "VERIFIED",
        "test_summary": {"passed": 384, "failed": 0},
    }
    (tmp / ".project_state" / "CHECKPOINT.json").write_text(
        json.dumps(state, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    (tmp / ".project_state" / "CURRENT_STATE.md").write_text(
        "# CURRENT STATE\n\n**Cycle:** 19\n**Checkpoint:** CP-0023 VERIFIED\n",
        encoding="utf-8",
    )
    (tmp / "docs" / "debt" / "CHECKPOINT_EVERY_FLOOR.md").write_text(
        "# EXPLICIT DEBT — checkpoint_every_floor\n\n"
        "**Status:** SCHEMA-GATED (CP-0022) — no chase\n\n"
        "BATCH MET; recovery MET.\n",
        encoding="utf-8",
    )
    return tmp


def test_observability_status_snapshot_schema_fields_present():
    snap = snapshot(ROOT, node_id="test-node", tip="deadbee")
    d = snapshot_to_dict(snap)
    assert REQUIRED_TOP_KEYS <= set(d.keys())
    assert d["schema"] == SCHEMA_ID
    assert d["node_id"] == "test-node"
    assert isinstance(d["cycle"], int)
    assert isinstance(d["ver"], str)
    assert "passed" in d["pytest"] and "failed" in d["pytest"]
    assert isinstance(d["slo_state"], dict)
    assert isinstance(d["debt_gates"], list)
    assert isinstance(d["peers"], list)
    assert isinstance(d["local"], dict)


def test_observability_status_snapshot_golden_stable_serialization(tmp_path: Path):
    root = _write_mini_root(tmp_path)
    snap = snapshot(root, node_id="golden-node", tip="abc1234", cycle=19)
    js1 = snapshot_to_json(snap)
    js2 = snapshot_to_json(snap)
    assert js1 == js2
    # sort_keys → lexicographic top-level key order
    parsed = json.loads(js1)
    assert list(parsed.keys()) == sorted(parsed.keys())
    assert parsed["schema"] == SCHEMA_ID
    assert parsed["node_id"] == "golden-node"
    assert parsed["cycle"] == 19
    assert parsed["ver"] == "0.15.0"
    assert parsed["cp_tip"] == "CP-0023"
    assert parsed["cp_range"] == "CP-0001..0023"
    assert parsed["pytest"] == {"failed": 0, "passed": 384}
    h = hashlib.sha256(js1.encode("utf-8")).hexdigest()
    # Recompute — same fixture must hash identically
    assert hashlib.sha256(snapshot_to_json(snap).encode("utf-8")).hexdigest() == h


def test_observability_status_snapshot_local_only(tmp_path: Path):
    root = _write_mini_root(tmp_path)
    snap = snapshot(root, node_id="solo", tip=None)
    d = snapshot_to_dict(snap)
    assert d["peers"] == []
    assert d["local"]["bounds"]["read_only"] is True
    assert d["local"]["bounds"]["no_consensus_writes"] is True
    assert d["local"]["last_checkpoint"] == "CP-0023"


def test_observability_status_snapshot_three_node_mock_peers(tmp_path: Path):
    root = _write_mini_root(tmp_path)
    peers = [
        {"node_id": "n2", "reachable": True, "summary": {"ver": "0.15.0", "cp": "CP-0023"}},
        {"node_id": "n3", "reachable": False, "summary": {"reason": "mock-down"}},
        {"node_id": "n1", "reachable": True, "summary": {"role": "local-peer"}},
    ]
    snap = snapshot(root, node_id="n0", peers=peers, tip="feedfac")
    d = snapshot_to_dict(snap)
    assert len(d["peers"]) == 3
    # Deterministic sort by node_id
    assert [p["node_id"] for p in d["peers"]] == ["n1", "n2", "n3"]
    assert d["peers"][1]["reachable"] is True
    assert d["peers"][2]["reachable"] is False
    # No real network — injected only
    assert d["local"]["bounds"]["no_raft"] is True


def test_observability_status_snapshot_no_consensus_write_side_effects(tmp_path: Path):
    root = _write_mini_root(tmp_path)
    # Marker that must remain untouched; also no new write-side files.
    marker = root / ".project_state" / "WRITE_MARKER.txt"
    marker.write_text("untouched\n", encoding="utf-8")
    before = {
        str(p.relative_to(root)): (p.stat().st_mtime_ns, p.read_bytes() if p.is_file() else b"")
        for p in root.rglob("*")
        if p.is_file()
    }
    _ = snapshot(
        root,
        node_id="side-effect-check",
        peers=[{"node_id": "p1", "reachable": True, "summary": {}}],
    )
    after_files = {str(p.relative_to(root)) for p in root.rglob("*") if p.is_file()}
    assert after_files == set(before.keys())
    for rel, (mtime, data) in before.items():
        p = root / rel
        assert p.read_bytes() == data
        assert p.stat().st_mtime_ns == mtime
    assert marker.read_text(encoding="utf-8") == "untouched\n"
    # No consensus / raft / wal markers created
    for name in ("raft", "consensus", "wal", "APPEND_ONLY"):
        assert not list(root.rglob(f"*{name}*"))


def test_observability_status_snapshot_cli_snapshot_json():
    r = subprocess.run(
        MESH + ["status", "--snapshot"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    assert r.returncode == 0, r.stderr
    data = json.loads(r.stdout)
    assert data["schema"] == SCHEMA_ID
    assert "cp_tip" in data
    assert "debt_gates" in data
    assert data["ver"] == "0.15.0"


def test_observability_status_snapshot_cli_m2m():
    r = subprocess.run(
        MESH + ["status", "--snapshot", "--m2m"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    assert r.returncode == 0, r.stderr
    line = r.stdout.strip()
    assert line.startswith("OBS:")
    assert "cycle=" in line
    assert "ver=" in line
    assert "cp=" in line
    assert "pytest=" in line


def test_observability_status_snapshot_m2m_formatter_fields(tmp_path: Path):
    root = _write_mini_root(tmp_path)
    snap = snapshot(root, node_id="m2m", tip="abcdef0", cycle=19)
    line = format_obs_m2m(snap)
    assert line.startswith("OBS:")
    assert "cycle=19" in line
    assert "ver=0.15.0" in line
    assert "cp=CP-0023" in line
    assert "pytest=384/0" in line
    assert "slo_floor=SCHEMA-GATED" in line
    assert "CHECKPOINT_EVERY_FLOOR=SCHEMA-GATED" in line
    assert len(line) > 40


def test_observability_status_snapshot_debt_gates_schema_gated(tmp_path: Path):
    root = _write_mini_root(tmp_path)
    snap = snapshot(root, tip="1111111")
    gates = {g.id: g for g in snap.debt_gates}
    assert "CHECKPOINT_EVERY_FLOOR" in gates
    assert gates["CHECKPOINT_EVERY_FLOOR"].state == "SCHEMA-GATED"
    assert gates["CHECKPOINT_EVERY_FLOOR"].path == "docs/debt/CHECKPOINT_EVERY_FLOOR.md"
    assert snap.slo_state["checkpoint_every_floor"] == "SCHEMA-GATED"
    assert snap.slo_state["checkpoint_durable_batch"] == "MET"
    assert snap.slo_state["recovery"] == "MET"


def test_observability_status_snapshot_bounds_no_tag_schema_mutation():
    """Snapshot must not mutate tags.py / tag schema gates (read-only bound)."""
    tags_path = ROOT / "src" / "neural_mesh" / "tags.py"
    before = tags_path.read_bytes()
    before_mtime = tags_path.stat().st_mtime_ns
    snap = snapshot(ROOT, node_id="bounds-tags")
    assert tags_path.read_bytes() == before
    assert tags_path.stat().st_mtime_ns == before_mtime
    # Does not chase / rewrite schema gate constants via import side effects
    from neural_mesh.tags import (
        CHECKPOINT_EVERY_FLOOR_SLO_CHASE,
        SCHEMA_GATE_STATUS,
    )

    assert CHECKPOINT_EVERY_FLOOR_SLO_CHASE is False
    assert SCHEMA_GATE_STATUS == "SCHEMA-GATED"
    assert snap.local["bounds"]["no_tag_schema_change"] is True


def test_observability_status_snapshot_bounds_no_slo_chase(tmp_path: Path):
    root = _write_mini_root(tmp_path)
    # Copy real debt doc text that says no chase; ensure we only report state
    src_debt = ROOT / "docs" / "debt" / "CHECKPOINT_EVERY_FLOOR.md"
    if src_debt.is_file():
        shutil.copy(src_debt, root / "docs" / "debt" / "CHECKPOINT_EVERY_FLOOR.md")
    snap = snapshot(root)
    assert snap.local["bounds"]["no_slo_chase"] is True
    # Must not invent MET for EVERY floor
    assert snap.slo_state["checkpoint_every_floor"] == "SCHEMA-GATED"
    assert snap.slo_state["checkpoint_every_floor"] != "MET"


def test_observability_status_snapshot_status_module_api():
    """neural_mesh.status.snapshot is the public mesh.status.snapshot() surface."""
    assert status_mod.snapshot is snapshot
    assert status_mod.format_obs_m2m is format_obs_m2m
    snap = status_mod.snapshot(ROOT, node_id="api", tip="0000000")
    assert isinstance(snap, StatusSnapshot)
    assert snap.schema_name == SCHEMA_ID


def test_observability_status_snapshot_bare_status_unchanged():
    """Bare `mesh status` still prints project state JSON (not snapshot)."""
    r = subprocess.run(
        MESH + ["status"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    assert r.returncode == 0, r.stderr
    data = json.loads(r.stdout)
    assert "schema" not in data or data.get("schema_version") == "1.0"
    assert "last_checkpoint" in data
    assert "project_version" in data


def test_observability_status_snapshot_cp_range_and_version(tmp_path: Path):
    root = _write_mini_root(tmp_path, ver="0.15.0", cp="CP-0023")
    snap = snapshot(root, tip="bbbbbbb", cycle=19)
    assert snap.ver == "0.15.0"
    assert snap.cp_tip == "CP-0023"
    assert snap.cp_range == "CP-0001..0023"
    assert snap.cycle == 19
