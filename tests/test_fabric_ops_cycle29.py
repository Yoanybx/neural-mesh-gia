"""Tests for Cycle 29 / CP-0033: Fabric ops UX (status / diagnose / reconnect).

Markers: fabric_ops_cycle29
Aim: ≥10 new tests — fail-closed TLS, no plaintext fallback, diagnose fields,
reconnect on tmp roots.
"""

from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

import pytest

from neural_mesh.network import (
    ExecutionEndpoint,
    FabricOps,
    FabricTLSError,
    NodeEndpoint,
    PlaintextForbidden,
    TransportMode,
    bootstrap_pair,
    cmd_fabric_diagnose,
    cmd_fabric_reconnect,
    cmd_fabric_status,
    issue_foreign_ca_leaf,
    load_endpoints_json,
    resolve_cert_paths,
)
from neural_mesh.network.ops import (
    SCHEMA_DIAGNOSE,
    SCHEMA_RECONNECT,
    SCHEMA_STATUS,
)

pytestmark = [pytest.mark.fabric_ops_cycle29]

REPO = Path(__file__).resolve().parents[1]


@pytest.fixture
def fabric_root(tmp_path: Path):
    """LocalCA layout under tmp_path/fabric with router + node-01 leafs."""
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


# --- docs / capability -------------------------------------------------------


def test_capability_doc_present():
    doc = (
        REPO / "docs" / "capabilities" / "MESH_FABRIC_OPS_UX.md"
    ).read_text(encoding="utf-8")
    assert "MESH_FABRIC_OPS_UX" in doc
    assert "no Vault" in doc or "No Vault" in doc or "Vault/ACME" in doc
    assert "plaintext" in doc.lower()
    assert "dual_primary" in doc
    assert "mesh fabric" in doc
    assert "CP-0033" in doc or "0033" in doc


def test_schemas_stable():
    assert SCHEMA_STATUS == "mesh.fabric.status/v1"
    assert SCHEMA_DIAGNOSE == "mesh.fabric.diagnose/v1"
    assert SCHEMA_RECONNECT == "mesh.fabric.reconnect/v1"


# --- layout helpers ----------------------------------------------------------


def test_resolve_cert_paths_and_endpoints_json(fabric_root, tmp_path: Path):
    root, _ca, _leaves = fabric_root
    paths = resolve_cert_paths(root, "router")
    assert paths is not None
    assert paths.node_id == "router"
    assert paths.ca_cert.is_file()
    assert paths.cert.is_file()
    assert paths.key.is_file()
    assert resolve_cert_paths(root, "missing-node") is None

    ep_path = _write_endpoints(
        tmp_path / "endpoints.json",
        [{"node_id": "node-01", "host": "127.0.0.1", "port": 9443}],
    )
    eps = load_endpoints_json(ep_path)
    assert "node-01" in eps
    assert eps["node-01"].port == 9443
    assert eps["node-01"].mode == TransportMode.TLS


def test_from_fabric_root_loads_layout(fabric_root, tmp_path: Path):
    root, _ca, _leaves = fabric_root
    _write_endpoints(
        root / "endpoints.json",
        [{"node_id": "node-01", "host": "127.0.0.1", "port": 1}],
    )
    ops = FabricOps.from_fabric_root(root, "router")
    assert ops.cert_paths is not None
    assert ops.tls_required is True
    assert "node-01" in ops.endpoints
    st = ops.status(probe=False)
    assert st.cert_ok is True
    assert st.endpoints_configured == 1
    assert st.dual_primary == 0
    assert st.plaintext_fallback == 0
    assert st.vault_acme_required is False


# --- status / diagnose with live TLS ----------------------------------------


def test_status_probe_healthy_peer(fabric_root, tmp_path: Path):
    root, _ca, leaves = fabric_root
    endpoint = _start_endpoint(leaves, "node-01", tmp_path)
    try:
        ops = FabricOps(
            "router",
            leaves["router"],
            endpoints={
                "node-01": NodeEndpoint(
                    "node-01",
                    mode=TransportMode.TLS,
                    host="127.0.0.1",
                    port=endpoint.bound_port,
                )
            },
            tls_required=True,
            fabric_root=root,
        )
        report = ops.status(probe=True)
        assert report.schema == SCHEMA_STATUS
        assert report.ok is True
        assert report.cert_ok is True
        assert len(report.peers) == 1
        peer = report.peers[0]
        assert peer.reachable is True
        assert peer.tls_ok is True
        assert peer.heartbeat_ok is True
        assert peer.latency_ms is not None
        assert peer.plaintext_attempted is False
        assert report.dual_primary == 0
        assert report.plaintext_fallback == 0
    finally:
        endpoint.stop()


def test_diagnose_reports_useful_fields(fabric_root, tmp_path: Path):
    root, _ca, leaves = fabric_root
    endpoint = _start_endpoint(leaves, "node-01", tmp_path)
    try:
        ops = FabricOps(
            "router",
            leaves["router"],
            endpoints={
                "node-01": NodeEndpoint(
                    "node-01",
                    mode=TransportMode.TLS,
                    host="127.0.0.1",
                    port=endpoint.bound_port,
                )
            },
            tls_required=True,
        )
        diag = ops.diagnose(probe=True)
        d = diag.to_dict()
        assert d["schema"] == SCHEMA_DIAGNOSE
        assert d["fail_closed"] is True
        assert d["plaintext_fallback"] == 0
        assert d["dual_primary"] == 0
        assert d["ok"] is True
        assert "recommendations" in d
        assert isinstance(d["recommendations"], list)
        st = d["status"]
        assert st["ca_cert_present"] is True
        assert st["leaf_cert_present"] is True
        assert st["peers"][0]["node_id"] == "node-01"
        assert st["peers"][0]["tls_ok"] is True
    finally:
        endpoint.stop()


def test_diagnose_missing_certs_recommends_bootstrap(tmp_path: Path):
    empty = tmp_path / "empty-fabric"
    empty.mkdir()
    ops = FabricOps.from_fabric_root(empty, "router", tls_required=True)
    diag = ops.diagnose(probe=False)
    assert diag.ok is False
    assert diag.status.cert_ok is False
    blob = " ".join(diag.recommendations).lower()
    assert "bootstrap" in blob or "ca" in blob or "leaf" in blob
    assert diag.plaintext_fallback == 0
    assert diag.dual_primary == 0


# --- fail-closed TLS / no plaintext -----------------------------------------


def test_fail_closed_foreign_ca(fabric_root, tmp_path: Path):
    root, _ca, leaves = fabric_root
    endpoint = _start_endpoint(leaves, "node-01", tmp_path)
    try:
        foreign = issue_foreign_ca_leaf("router", tmp_path / "foreign")
        ops = FabricOps(
            "router",
            foreign,
            endpoints={
                "node-01": NodeEndpoint(
                    "node-01",
                    mode=TransportMode.TLS,
                    host="127.0.0.1",
                    port=endpoint.bound_port,
                )
            },
            tls_required=True,
        )
        report = ops.status(probe=True)
        assert report.ok is False
        peer = report.peers[0]
        assert peer.tls_ok is False
        assert peer.reachable is False or peer.error_code == FabricTLSError.code
        assert peer.error_code == FabricTLSError.code
        assert peer.plaintext_attempted is False
        # Must not have silently fallen back
        assert report.plaintext_fallback == 0
    finally:
        endpoint.stop()


def test_no_plaintext_fallback_on_unix_endpoint(fabric_root, tmp_path: Path):
    root, _ca, leaves = fabric_root
    ops = FabricOps(
        "router",
        leaves["router"],
        endpoints={
            "unix-peer": NodeEndpoint(
                "unix-peer",
                mode=TransportMode.UNIX,
                unix_path=tmp_path / "sock",
            )
        },
        tls_required=True,
    )
    report = ops.status(probe=True)
    assert report.ok is False
    peer = report.peers[0]
    assert peer.error_code == PlaintextForbidden.code
    assert peer.plaintext_attempted is False
    assert report.plaintext_fallback == 0

    result = ops.reconnect("unix-peer", attempts=3)
    assert result.ok is False
    assert result.plaintext_attempted is False
    assert result.plaintext_fallback == 0
    assert result.results[0].error_code == PlaintextForbidden.code


def test_reconnect_refuses_plaintext_even_after_tls_error(
    fabric_root, tmp_path: Path
):
    """Reconnect must not degrade to unix/plaintext after TLS failure."""
    _root, _ca, leaves = fabric_root
    # Point at closed port → connection drop / TLS fail; no plaintext path.
    ops = FabricOps(
        "router",
        leaves["router"],
        endpoints={
            "node-01": NodeEndpoint(
                "node-01",
                mode=TransportMode.TLS,
                host="127.0.0.1",
                port=1,  # unlikely listening
            )
        },
        tls_required=True,
    )
    result = ops.reconnect(attempts=2)
    assert result.ok is False
    assert result.plaintext_attempted is False
    assert result.plaintext_fallback == 0
    assert result.dual_primary == 0
    assert all(r.plaintext_attempted is False for r in result.results)
    # Ensure we never mutated endpoint mode to unix
    assert ops.endpoints["node-01"].mode == TransportMode.TLS


# --- reconnect success on tmp roots -----------------------------------------


def test_reconnect_healthy_on_tmp_root(fabric_root, tmp_path: Path):
    root, _ca, leaves = fabric_root
    endpoint = _start_endpoint(leaves, "node-01", tmp_path)
    try:
        _write_endpoints(
            root / "endpoints.json",
            [
                {
                    "node_id": "node-01",
                    "host": "127.0.0.1",
                    "port": endpoint.bound_port,
                    "mode": "tls",
                }
            ],
        )
        ops = FabricOps.from_fabric_root(root, "router", tls_required=True)
        result = ops.reconnect("node-01", attempts=2)
        assert result.schema == SCHEMA_RECONNECT
        assert result.ok is True
        assert result.plaintext_attempted is False
        assert result.plaintext_fallback == 0
        assert result.dual_primary == 0
        assert result.results[0].heartbeat_ok is True
        assert result.results[0].tls_ok is True
    finally:
        endpoint.stop()


def test_reconnect_unknown_peer(fabric_root):
    root, _ca, leaves = fabric_root
    ops = FabricOps("router", leaves["router"], endpoints={}, tls_required=True)
    result = ops.reconnect("ghost", attempts=1)
    assert result.ok is False
    assert result.results[0].error_code == "INVALID_SESSION"
    assert result.plaintext_fallback == 0


# --- CLI --------------------------------------------------------------------


def test_cli_fabric_status_json(fabric_root, tmp_path: Path):
    root, _ca, leaves = fabric_root
    endpoint = _start_endpoint(leaves, "node-01", tmp_path)
    try:
        ep_path = _write_endpoints(
            tmp_path / "eps.json",
            [
                {
                    "node_id": "node-01",
                    "host": "127.0.0.1",
                    "port": endpoint.bound_port,
                }
            ],
        )
        proc = subprocess.run(
            [
                sys.executable,
                "-m",
                "neural_mesh.cli",
                "fabric",
                "status",
                "--fabric-root",
                str(root),
                "--node-id",
                "router",
                "--endpoints",
                str(ep_path),
                "--json",
            ],
            cwd=str(REPO),
            capture_output=True,
            text=True,
            check=False,
            env={
                **dict(__import__("os").environ),
                "PYTHONPATH": str(REPO / "src")
                + (
                    ":" + __import__("os").environ["PYTHONPATH"]
                    if __import__("os").environ.get("PYTHONPATH")
                    else ""
                ),
            },
        )
        assert proc.returncode == 0, proc.stderr
        data = json.loads(proc.stdout)
        assert data["schema"] == SCHEMA_STATUS
        assert data["ok"] is True
        assert data["dual_primary"] == 0
        assert data["plaintext_fallback"] == 0
    finally:
        endpoint.stop()


def test_cli_fabric_diagnose_and_reconnect(fabric_root, tmp_path: Path):
    root, _ca, leaves = fabric_root
    endpoint = _start_endpoint(leaves, "node-01", tmp_path)
    try:
        ep_path = _write_endpoints(
            tmp_path / "eps.json",
            [
                {
                    "node_id": "node-01",
                    "host": "127.0.0.1",
                    "port": endpoint.bound_port,
                }
            ],
        )
        env = {
            **dict(__import__("os").environ),
            "PYTHONPATH": str(REPO / "src"),
        }
        d = subprocess.run(
            [
                sys.executable,
                "-m",
                "neural_mesh.cli",
                "fabric",
                "diagnose",
                "--fabric-root",
                str(root),
                "--node-id",
                "router",
                "--endpoints",
                str(ep_path),
                "--json",
            ],
            cwd=str(REPO),
            capture_output=True,
            text=True,
            env=env,
            check=False,
        )
        assert d.returncode == 0, d.stderr
        diag = json.loads(d.stdout)
        assert diag["schema"] == SCHEMA_DIAGNOSE
        assert diag["fail_closed"] is True

        r = subprocess.run(
            [
                sys.executable,
                "-m",
                "neural_mesh.cli",
                "fabric",
                "reconnect",
                "--fabric-root",
                str(root),
                "--node-id",
                "router",
                "--peer",
                "node-01",
                "--endpoints",
                str(ep_path),
                "--json",
            ],
            cwd=str(REPO),
            capture_output=True,
            text=True,
            env=env,
            check=False,
        )
        assert r.returncode == 0, r.stderr
        rec = json.loads(r.stdout)
        assert rec["schema"] == SCHEMA_RECONNECT
        assert rec["ok"] is True
        assert rec["plaintext_attempted"] is False
    finally:
        endpoint.stop()


def test_cmd_helpers_direct(fabric_root, tmp_path: Path, capsys):
    root, _ca, leaves = fabric_root
    endpoint = _start_endpoint(leaves, "node-01", tmp_path)
    try:
        ep_path = _write_endpoints(
            tmp_path / "eps.json",
            [
                {
                    "node_id": "node-01",
                    "host": "127.0.0.1",
                    "port": endpoint.bound_port,
                }
            ],
        )
        assert (
            cmd_fabric_status(
                fabric_root=root,
                node_id="router",
                endpoints=ep_path,
                as_json=True,
            )
            == 0
        )
        assert (
            cmd_fabric_diagnose(
                fabric_root=root,
                node_id="router",
                endpoints=ep_path,
                as_json=False,
            )
            == 0
        )
        assert (
            cmd_fabric_reconnect(
                fabric_root=root,
                node_id="router",
                peer="node-01",
                endpoints=ep_path,
                as_json=True,
            )
            == 0
        )
        out = capsys.readouterr().out
        assert "mesh.fabric" in out or "fabric" in out.lower()
    finally:
        endpoint.stop()


def test_status_unreachable_peer_issues(fabric_root):
    _root, _ca, leaves = fabric_root
    ops = FabricOps(
        "router",
        leaves["router"],
        endpoints={
            "node-01": NodeEndpoint(
                "node-01", mode=TransportMode.TLS, host="127.0.0.1", port=1
            )
        },
        tls_required=True,
    )
    st = ops.status(probe=True)
    assert st.ok is False
    assert st.issues
    assert st.peers[0].error
    assert st.plaintext_fallback == 0
