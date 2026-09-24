"""Tests for Cycle 30 / CP-0034: richer OBS peers (injection + RO probe).

Markers: obs_peers_cycle30
Aim: ≥12 new tests — richer fields, inject/normalize, CLI, RO probe fail-closed,
no dual_primary, no mutation, N>2 refused.
"""

from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

import pytest

from neural_mesh.obs_peers import (
    MAX_OBS_PEER_PROBES,
    load_peers_json,
    merge_peer_summaries,
    normalize_peer_summaries,
    parse_peers_json,
    peer_summary_from_fabric_probe,
    peer_summary_from_mapping,
    probe_peer_readonly,
    probe_peers_readonly,
)
from neural_mesh.status_snapshot import (
    SCHEMA_ID,
    PeerSummary,
    format_obs_m2m,
    snapshot,
    snapshot_to_dict,
    snapshot_to_json,
)
from neural_mesh.network import (
    ExecutionEndpoint,
    FabricOps,
    NodeEndpoint,
    TransportMode,
    bootstrap_pair,
)
from neural_mesh.network.ops import PeerProbe

pytestmark = [pytest.mark.obs_peers_cycle30]

REPO = Path(__file__).resolve().parents[1]
MESH = [sys.executable, "-m", "neural_mesh.cli"]


def _write_mini_root(tmp: Path, *, ver: str = "0.17.0", cp: str = "CP-0034") -> Path:
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
        "current_module": "mesh-obs-peers",
        "safety_status": "SAFE",
        "status": "VERIFIED",
        "test_summary": {"passed": 532, "failed": 0},
    }
    (tmp / ".project_state" / "CHECKPOINT.json").write_text(
        json.dumps(state, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    (tmp / ".project_state" / "CURRENT_STATE.md").write_text(
        "# CURRENT STATE\n\n**Cycle:** 30\n**Checkpoint:** CP-0034 VERIFIED\n",
        encoding="utf-8",
    )
    (tmp / "docs" / "debt" / "CHECKPOINT_EVERY_FLOOR.md").write_text(
        "# EXPLICIT DEBT\n\n**Status:** SCHEMA-GATED\n",
        encoding="utf-8",
    )
    return tmp


@pytest.fixture
def fabric_root(tmp_path: Path):
    root = tmp_path / "fabric"
    ca, leaves = bootstrap_pair(root, ["router", "node-01", "node-02"])
    return root, ca, leaves


def _write_endpoints(path: Path, peers: list[dict]) -> Path:
    path.write_text(json.dumps({"peers": peers}, indent=2), encoding="utf-8")
    return path


def _start_endpoint(leaves, node_id: str, tmp_path: Path) -> ExecutionEndpoint:
    ep = ExecutionEndpoint(
        node_id,
        leaves[node_id],
        cram_root=tmp_path / f"cram-{node_id}",
    )
    ep.start()
    time.sleep(0.05)
    return ep


# --- docs --------------------------------------------------------------------


def test_capability_doc_present():
    doc = (REPO / "docs" / "capabilities" / "MESH_OBS_PEERS.md").read_text(
        encoding="utf-8"
    )
    assert "MESH_OBS_PEERS" in doc
    assert "CP-0034" in doc or "0034" in doc
    assert "no Raft" in doc or "No Raft" in doc
    assert "N>2" in doc or "N≤2" in doc or "max 2" in doc
    assert "dual_primary" in doc
    assert "probe" in doc.lower()
    assert "GIA" in doc


# --- richer model / normalize ------------------------------------------------


def test_peer_summary_richer_fields_defaults():
    p = PeerSummary(node_id="n1")
    assert p.reachable is False
    assert p.summary == {}
    assert p.source == "injected"
    assert p.ver is None
    assert p.tls_ok is None
    assert p.latency_ms is None


def test_peer_summary_from_mapping_lifts_summary_keys():
    p = peer_summary_from_mapping(
        {
            "node_id": "n2",
            "reachable": True,
            "summary": {"ver": "0.17.0", "cp_tip": "CP-0033", "role": "replica"},
        }
    )
    assert p.ver == "0.17.0"
    assert p.cp_tip == "CP-0033"
    assert p.role == "replica"
    assert "ver" not in p.summary


def test_normalize_dedup_last_wins_sorted():
    peers = normalize_peer_summaries(
        [
            {"node_id": "b", "reachable": False},
            {"node_id": "a", "reachable": True, "source": "file"},
            {"node_id": "b", "reachable": True, "source": "probed"},
        ]
    )
    assert [p.node_id for p in peers] == ["a", "b"]
    assert peers[1].reachable is True
    assert peers[1].source == "probed"


def test_load_and_parse_peers_json(tmp_path: Path):
    path = tmp_path / "peers.json"
    path.write_text(
        json.dumps(
            {
                "peers": [
                    {
                        "node_id": "n1",
                        "reachable": True,
                        "ver": "0.17.0",
                        "source": "file",
                    },
                    {"node_id": "n0", "reachable": False, "error": "down"},
                ]
            }
        ),
        encoding="utf-8",
    )
    loaded = load_peers_json(path)
    assert [p.node_id for p in loaded] == ["n0", "n1"]
    assert loaded[1].source == "file"
    parsed = parse_peers_json('[{"node_id":"x","reachable":true}]')
    assert len(parsed) == 1 and parsed[0].node_id == "x"


def test_merge_peer_summaries_override():
    a = [{"node_id": "n1", "reachable": False, "source": "file"}]
    b = [{"node_id": "n1", "reachable": True, "source": "probed", "tls_ok": True}]
    merged = merge_peer_summaries(a, b)
    assert len(merged) == 1
    assert merged[0].reachable is True
    assert merged[0].source == "probed"
    assert merged[0].tls_ok is True


def test_snapshot_injects_richer_peers(tmp_path: Path):
    root = _write_mini_root(tmp_path)
    peers = [
        {
            "node_id": "n2",
            "reachable": True,
            "ver": "0.17.0",
            "tip": "abc1234",
            "cp_tip": "CP-0033",
            "source": "file",
        },
        {"node_id": "n1", "reachable": False, "error": "mock-down", "source": "arg"},
    ]
    snap = snapshot(root, node_id="n0", peers=peers, tip="deadbee", cycle=30)
    d = snapshot_to_dict(snap)
    assert d["schema"] == SCHEMA_ID
    assert [p["node_id"] for p in d["peers"]] == ["n1", "n2"]
    assert d["peers"][1]["ver"] == "0.17.0"
    assert d["peers"][1]["source"] == "file"
    assert d["local"]["bounds"]["no_raft"] is True
    line = format_obs_m2m(snap)
    assert "peers=2" in line
    assert "peers_up=1" in line
    assert "peers_down=1" in line
    assert "n1/down/arg" in line
    assert "n2/up/file" in line


def test_snapshot_default_local_only_no_peers(tmp_path: Path):
    root = _write_mini_root(tmp_path)
    snap = snapshot(root, node_id="solo")
    assert snap.peers == []
    assert "peers=0" in format_obs_m2m(snap)


# --- CLI ---------------------------------------------------------------------


def test_cli_peers_file_injection(tmp_path: Path):
    peers = tmp_path / "p.json"
    peers.write_text(
        json.dumps(
            {
                "peers": [
                    {"node_id": "peer-a", "reachable": True, "ver": "0.17.0"},
                    {"node_id": "peer-b", "reachable": False},
                ]
            }
        ),
        encoding="utf-8",
    )
    r = subprocess.run(
        MESH + ["status", "--snapshot", "--peers-file", str(peers)],
        cwd=REPO,
        capture_output=True,
        text=True,
    )
    assert r.returncode == 0, r.stderr
    data = json.loads(r.stdout)
    assert len(data["peers"]) == 2
    assert data["peers"][0]["node_id"] == "peer-a"


def test_cli_peers_json_and_m2m(tmp_path: Path):
    payload = json.dumps(
        [{"node_id": "m2m-peer", "reachable": True, "source": "arg"}]
    )
    r = subprocess.run(
        MESH + ["status", "--snapshot", "--m2m", "--peers-json", payload],
        cwd=REPO,
        capture_output=True,
        text=True,
    )
    assert r.returncode == 0, r.stderr
    line = r.stdout.strip()
    assert line.startswith("OBS:")
    assert "peers=1" in line
    assert "m2m-peer/up/arg" in line or "peers_up=1" in line


def test_cli_probe_peer_requires_fabric_root():
    r = subprocess.run(
        MESH + ["status", "--snapshot", "--probe-peer", "node-01"],
        cwd=REPO,
        capture_output=True,
        text=True,
    )
    assert r.returncode != 0
    assert "fabric-root" in (r.stderr + r.stdout).lower()


def test_cli_probe_peer_refuses_n_gt_2(tmp_path: Path, fabric_root):
    root, _ca, _leaves = fabric_root
    r = subprocess.run(
        MESH
        + [
            "status",
            "--snapshot",
            "--fabric-root",
            str(root),
            "--node-id",
            "router",
            "--probe-peer",
            "a",
            "--probe-peer",
            "b",
            "--probe-peer",
            "c",
        ],
        cwd=REPO,
        capture_output=True,
        text=True,
    )
    assert r.returncode != 0
    combined = r.stderr + r.stdout
    assert "N>" in combined or "refuses" in combined.lower()


# --- RO probe ----------------------------------------------------------------


def test_peer_summary_from_fabric_probe_mapping():
    probe = PeerProbe(
        node_id="n1",
        mode="tls",
        host="127.0.0.1",
        port=9,
        reachable=True,
        tls_ok=True,
        heartbeat_ok=True,
        latency_ms=1.5,
        peer_identity="n1",
    )
    ps = peer_summary_from_fabric_probe(probe)
    assert ps.source == "probed"
    assert ps.reachable is True
    assert ps.tls_ok is True
    assert ps.heartbeat_ok is True
    assert ps.latency_ms == 1.5
    assert ps.summary.get("peer_identity") == "n1"


def test_probe_peers_readonly_refuses_n_gt_2(fabric_root):
    root, _ca, _leaves = fabric_root
    with pytest.raises(ValueError, match=r"N>"):
        probe_peers_readonly(
            local_node_id="router",
            peers=["a", "b", "c"],
            fabric_root=root,
        )
    assert MAX_OBS_PEER_PROBES == 2


def test_probe_peer_readonly_unreachable_fail_closed(fabric_root, tmp_path: Path):
    root, _ca, leaves = fabric_root
    ep_path = _write_endpoints(
        tmp_path / "endpoints.json",
        [
            {
                "node_id": "node-01",
                "host": "127.0.0.1",
                "port": 1,  # nothing listening
                "mode": "tls",
            }
        ],
    )
    # Mark mtimes before probe
    before = {
        str(p.relative_to(root)): p.stat().st_mtime_ns
        for p in root.rglob("*")
        if p.is_file()
    }
    ps = probe_peer_readonly(
        local_node_id="router",
        peer="node-01",
        fabric_root=root,
        endpoints_path=ep_path,
    )
    assert ps.source == "probed"
    assert ps.reachable is False
    assert ps.error is not None or ps.error_code is not None
    # No mutation under fabric root
    after = {
        str(p.relative_to(root)): p.stat().st_mtime_ns
        for p in root.rglob("*")
        if p.is_file()
    }
    assert after == before


def test_probe_peer_readonly_live_tls_ok(fabric_root, tmp_path: Path):
    root, _ca, leaves = fabric_root
    endpoint = _start_endpoint(leaves, "node-01", tmp_path)
    try:
        port = endpoint.bound_port
        assert port > 0
        ep_path = _write_endpoints(
            tmp_path / "endpoints.json",
            [
                {
                    "node_id": "node-01",
                    "host": "127.0.0.1",
                    "port": port,
                    "mode": "tls",
                }
            ],
        )
        marker = root / "WRITE_MARKER.txt"
        marker.write_text("untouched\n", encoding="utf-8")
        before_files = {str(p) for p in root.rglob("*") if p.is_file()}
        before_mtime = marker.stat().st_mtime_ns

        ps = probe_peer_readonly(
            local_node_id="router",
            peer="node-01",
            fabric_root=root,
            endpoints_path=ep_path,
        )
        assert ps.reachable is True
        assert ps.tls_ok is True
        assert ps.heartbeat_ok is True
        assert ps.source == "probed"
        assert marker.read_text(encoding="utf-8") == "untouched\n"
        assert marker.stat().st_mtime_ns == before_mtime
        after_files = {str(p) for p in root.rglob("*") if p.is_file()}
        assert after_files == before_files
    finally:
        endpoint.stop()


def test_probe_never_dual_primary_or_raft(fabric_root, tmp_path: Path):
    root, _ca, leaves = fabric_root
    endpoint = _start_endpoint(leaves, "node-01", tmp_path)
    try:
        ep_path = _write_endpoints(
            tmp_path / "endpoints.json",
            [
                {
                    "node_id": "node-01",
                    "host": "127.0.0.1",
                    "port": endpoint.bound_port,
                    "mode": "tls",
                }
            ],
        )
        ops = FabricOps.from_fabric_root(
            root, "router", endpoints_path=ep_path
        )
        ps = probe_peer_readonly(
            local_node_id="router",
            peer="node-01",
            ops=ops,
        )
        # dual_primary hard 0 via fabric status path
        st = ops.status(probe=False)
        assert st.dual_primary == 0
        assert st.plaintext_fallback == 0
        assert "raft" not in (ps.error or "").lower()
        assert ps.summary.get("plaintext_attempted") is not True
        # Snapshot bounds still RO
        snap = snapshot(
            _write_mini_root(tmp_path / "repo"),
            peers=[ps],
            tip="eeeeeee",
            cycle=30,
        )
        assert snap.local["bounds"]["no_raft"] is True
        assert snap.local["bounds"]["read_only"] is True
        assert snap.local["bounds"]["no_consensus_writes"] is True
    finally:
        endpoint.stop()


def test_cli_probe_peer_injects_into_snapshot(fabric_root, tmp_path: Path):
    root, _ca, leaves = fabric_root
    endpoint = _start_endpoint(leaves, "node-01", tmp_path)
    try:
        ep_path = _write_endpoints(
            tmp_path / "endpoints.json",
            [
                {
                    "node_id": "node-01",
                    "host": "127.0.0.1",
                    "port": endpoint.bound_port,
                    "mode": "tls",
                }
            ],
        )
        r = subprocess.run(
            MESH
            + [
                "status",
                "--snapshot",
                "--node-id",
                "router",
                "--fabric-root",
                str(root),
                "--endpoints",
                str(ep_path),
                "--probe-peer",
                "node-01",
            ],
            cwd=REPO,
            capture_output=True,
            text=True,
        )
        assert r.returncode == 0, r.stderr
        data = json.loads(r.stdout)
        assert len(data["peers"]) == 1
        peer = data["peers"][0]
        assert peer["node_id"] == "node-01"
        assert peer["source"] == "probed"
        assert peer["reachable"] is True
        assert peer["tls_ok"] is True
    finally:
        endpoint.stop()


def test_snapshot_json_stable_with_peers(tmp_path: Path):
    root = _write_mini_root(tmp_path)
    peers = [
        PeerSummary(
            node_id="z",
            reachable=True,
            source="file",
            ver="0.17.0",
        ),
        PeerSummary(node_id="a", reachable=False, source="arg", error="x"),
    ]
    snap = snapshot(root, peers=peers, tip="1111111", cycle=30, node_id="n0")
    js1 = snapshot_to_json(snap)
    js2 = snapshot_to_json(snap)
    assert js1 == js2
    parsed = json.loads(js1)
    assert list(parsed.keys()) == sorted(parsed.keys())
    assert [p["node_id"] for p in parsed["peers"]] == ["a", "z"]
