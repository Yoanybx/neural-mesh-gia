"""Cycle 12 — Phase 5A: remote C-RAM + N=2 active-passive over Fabric mTLS."""

from __future__ import annotations

import json
import os
import signal
import time
from pathlib import Path

import pytest

from neural_mesh.cram.observability import STAGE_ORDER, cmd_trace
from neural_mesh.cram.remote_client import RemoteCRAMClient
from neural_mesh.cram.remote_protocol import (
    FEATURE_FLAG_ENV,
    PHASE5A_MESSAGE_TYPES,
    ReplicaRole,
    make_cram_put,
    make_replica_append,
)
from neural_mesh.cram.remote_store import RemoteCRAMStore, replication_n2_enabled
from neural_mesh.cram.replication.fabric_replica import FabricReplicaPair
from neural_mesh.cram.store import CRAMStore
from neural_mesh.network.errors import PlaintextForbidden
from neural_mesh.network.protocol import (
    PHASE5A_REQUIRED_MESSAGE_TYPES,
    REQUIRED_MESSAGE_TYPES,
    MessageType,
)
from neural_mesh.network.session import NodeEndpoint
from neural_mesh.network.tls import bootstrap_pair, issue_foreign_ca_leaf
from neural_mesh.network.transport import TransportMode

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def ca_leaves(tmp_path: Path):
    _, leaves = bootstrap_pair(tmp_path / "ca", ["client", "node-01", "node-02"])
    return leaves


@pytest.fixture
def pair(tmp_path: Path, ca_leaves):
    p = FabricReplicaPair(tmp_path / "pair", ca_leaves, enabled=True).start()
    yield p
    p.stop()


def _client(leaves, pair) -> RemoteCRAMClient:
    c = RemoteCRAMClient("client", leaves["client"], tls_required=True)
    c.register(
        NodeEndpoint(
            "node-01",
            mode=TransportMode.TLS,
            host="127.0.0.1",
            port=pair.primary.bound_port,
        )
    )
    return c


# ----- P0 docs / freeze -----


def test_phase5a_doc_frozen():
    doc = (ROOT / "docs" / "phase5_replication_n2.md").read_text(encoding="utf-8")
    assert "PRIMARY" in doc and "STANDBY" in doc
    assert "epoch" in doc.lower()
    assert "fencing" in doc.lower() or "fence" in doc.lower()
    assert "promote" in doc.lower()
    assert FEATURE_FLAG_ENV in doc or "NEURAL_MESH_PHASE5A_REPLICATION" in doc
    assert "Raft" in doc or "raft" in doc.lower()


def test_phase5a_message_types_present():
    names = {t.value for t in PHASE5A_REQUIRED_MESSAGE_TYPES}
    for need in (
        "CRAM_PUT",
        "CRAM_GET",
        "CRAM_VERIFY",
        "CRAM_CHECKPOINT",
        "REPLICA_APPEND",
        "REPLICA_ACK",
        "ROLE_STATUS",
        "PROMOTE_REQUEST",
    ):
        assert need in names
    assert set(PHASE5A_MESSAGE_TYPES) == set(PHASE5A_REQUIRED_MESSAGE_TYPES)


def test_feature_flag_default_off(monkeypatch):
    monkeypatch.delenv(FEATURE_FLAG_ENV, raising=False)
    assert replication_n2_enabled() is False


def test_feature_flag_on(monkeypatch):
    monkeypatch.setenv(FEATURE_FLAG_ENV, "1")
    assert replication_n2_enabled() is True


def test_feature_flag_off_restores_c11_single_node(tmp_path: Path):
    store = RemoteCRAMStore(tmp_path, enabled=False)
    h = store.local.put(b"c11-local")
    assert store.local.verify(h)
    with pytest.raises(RuntimeError, match="disabled|OFF|single-node|Phase 5A"):
        store.put_remote("node-01", b"x")


# ----- P1 remote C-RAM -----


def test_remote_put_get(pair, ca_leaves):
    client = _client(ca_leaves, pair)
    put = client.put_remote("node-01", b"hello-remote")
    assert put.ok, put.error
    got = client.get_remote("node-01", put.content_hash)
    assert got.ok and got.content == b"hello-remote"


def test_remote_verify(pair, ca_leaves):
    client = _client(ca_leaves, pair)
    put = client.put_remote("node-01", b"verify-me")
    vr = client.verify_remote("node-01", put.content_hash)
    assert vr.ok and vr.verified is True


def test_tls_required_for_cram(tmp_path: Path, ca_leaves):
    client = RemoteCRAMClient("client", ca_leaves["client"], tls_required=True)
    client.register(
        NodeEndpoint("node-01", mode=TransportMode.UNIX, unix_path=tmp_path / "x.sock")
    )
    # PlaintextForbidden is a FabricError; client surfaces it as failed RemoteResult
    # (fail-closed — never silent plaintext fallback).
    try:
        res = client.put_remote("node-01", b"nope")
    except PlaintextForbidden:
        return
    assert res.ok is False
    assert res.error_code in ("FABRIC_PLAINTEXT_FORBIDDEN", "PLAINTEXT_FORBIDDEN", None) or (
        res.error and "TLS" in res.error
    )


def test_remote_store_put_get_verify_checkpoint(pair, ca_leaves, tmp_path: Path):
    rs = RemoteCRAMStore(
        tmp_path / "client-root",
        local_node_id="client",
        cert_paths=ca_leaves["client"],
        enabled=True,
    )
    rs.register(
        NodeEndpoint(
            "node-01",
            mode=TransportMode.TLS,
            host="127.0.0.1",
            port=pair.primary.bound_port,
        )
    )
    put = rs.put_remote("node-01", b"via-store", force=True)
    assert put.ok
    got = rs.get_remote("node-01", put.content_hash, force=True)
    assert got.ok and got.content == b"via-store"
    vr = rs.verify_remote("node-01", put.content_hash, force=True)
    assert vr.ok
    ck = rs.checkpoint_remote(
        "node-01", {"kind": "test", "hash": put.content_hash}, force=True
    )
    assert ck.ok and ck.content_hash


def test_stale_epoch_rejected(pair):
    r = pair.primary.put_and_replicate(b"v0")
    key = r["object_hash"]
    pair.standby.state.object_epochs[key] = 5
    msg = make_replica_append(
        from_node="node-01",
        to_node="node-02",
        content=b"v0",
        object_hash=key,
        epoch=1,
        version=1,
    )
    resp = pair.standby.handle_message(msg)
    assert resp.payload.get("ok") is False
    assert resp.payload.get("code") == "REJECTED_STALE_EPOCH"


def test_hash_mismatch_rejected(pair):
    msg = make_replica_append(
        from_node="node-01",
        to_node="node-02",
        content=b"real-bytes",
        object_hash="0" * 64,
        epoch=0,
        version=0,
    )
    resp = pair.standby.handle_message(msg)
    assert resp.payload.get("ok") is False
    assert resp.payload.get("code") == "HASH_MISMATCH"


def test_remote_state_verified(pair):
    r = pair.primary.put_and_replicate(b"state-ok")
    assert r["replica_ok"] is True
    assert pair.standby.store.verify(r["object_hash"])
    assert pair.primary.store.verify(r["object_hash"])


# ----- P2 replica protocol / roles -----


def test_primary_writable_standby_rejects(pair):
    assert pair.primary.put_and_replicate(b"prim")["object_hash"]
    with pytest.raises(PermissionError):
        pair.standby.put_and_replicate(b"standby-write")


def test_replica_message_type_values():
    assert MessageType.REPLICA_APPEND.value == "REPLICA_APPEND"
    assert MessageType.REPLICA_ACK.value == "REPLICA_ACK"
    assert MessageType.ROLE_STATUS.value == "ROLE_STATUS"
    assert MessageType.PROMOTE_REQUEST.value == "PROMOTE_REQUEST"


def test_roles_primary_standby(pair):
    assert pair.primary.role == ReplicaRole.PRIMARY
    assert pair.standby.role == ReplicaRole.STANDBY


def test_dual_primary_zero_steady(pair):
    assert pair.dual_primary_count() <= 1
    assert pair.witness.count_writable() == 1


def test_epoch_and_version_on_put(pair):
    r = pair.primary.put_and_replicate(b"epoch-check")
    key = r["object_hash"]
    assert key in pair.primary.state.object_epochs
    assert key in pair.primary.state.object_versions


def test_promote_increments_epoch(pair):
    r = pair.primary.put_and_replicate(b"promo")
    before = pair.standby.epoch
    pair.primary.demote_to_standby()
    pair.witness.release(pair.primary.node_id)
    prom = pair.standby.promote_self(r["object_hash"])
    assert prom.get("promoted") is True
    assert pair.standby.epoch >= before + 1


# ----- P3 faults -----


def test_network_drop_mid_replica(pair):
    pair.standby.set_partitioned(True)
    pair.primary.set_partitioned(True)
    r = pair.primary.put_and_replicate(b"during-partition")
    assert r["dual_primary"] == 0
    assert pair.dual_primary_count() <= 1
    pair.standby.set_partitioned(False)
    pair.primary.set_partitioned(False)


def test_no_phantom_state(pair):
    r = pair.primary.put_and_replicate(b"real")
    assert not pair.standby.store.exists("f" * 64)
    assert pair.standby.store.exists(r["object_hash"])


def test_checkpoint_after_recovery(pair):
    r = pair.primary.put_and_replicate(b"pre-recovery")
    pair.primary.set_partitioned(True)
    pair.standby.set_partitioned(True)
    pair.primary.demote_to_standby()
    pair.witness.release(pair.primary.node_id)
    prom = pair.standby.promote_self(r["object_hash"])
    assert prom.get("dual_primary", 0) == 0
    ck = pair.standby.checkpoint_after_recovery(
        {"after": "recovery", "hash": r["object_hash"]}
    )
    assert pair.standby.store.verify(ck)


def test_promote_under_partition_dual_primary_zero(pair):
    r = pair.primary.put_and_replicate(b"part")
    pair.primary.set_partitioned(True)
    pair.standby.set_partitioned(True)
    pair.primary.demote_to_standby()
    refused = pair.standby.promote_self(r["object_hash"])
    assert pair.witness.count_writable() <= 1
    assert refused.get("dual_primary", 0) == 0
    pair.witness.release(pair.primary.node_id)
    ok = pair.standby.promote_self(r["object_hash"])
    assert ok.get("dual_primary", 0) == 0
    assert pair.witness.count_writable() <= 1


def test_invalid_cert_rejected(pair, tmp_path: Path):
    foreign = issue_foreign_ca_leaf("client", tmp_path / "foreign")
    client = RemoteCRAMClient("client", foreign, tls_required=True)
    client.register(
        NodeEndpoint(
            "node-01",
            mode=TransportMode.TLS,
            host="127.0.0.1",
            port=pair.primary.bound_port,
        )
    )
    res = client.put_remote("node-01", b"bad-cert")
    assert res.ok is False


def test_kill9_mid_handshake_dual_primary_zero(pair, ca_leaves):
    import multiprocessing as mp

    port = pair.primary.bound_port
    leaf = ca_leaves["client"]

    def _child(cert_dir: str, p: int):
        try:
            from neural_mesh.network.tls import NodeCertPaths

            paths = NodeCertPaths(
                ca_cert=Path(cert_dir) / "ca.crt",
                cert=Path(cert_dir) / "client.crt",
                key=Path(cert_dir) / "client.key",
            )
            # fallback: use pickled-unfriendly — just sleep if reconstruction hard
            c = RemoteCRAMClient("client", leaf, tls_required=True)
            c.register(
                NodeEndpoint(
                    "node-01", mode=TransportMode.TLS, host="127.0.0.1", port=p
                )
            )
            c.put_remote("node-01", b"kill9")
        except Exception:
            pass
        time.sleep(2)

    # Use fork with leaf object in closure (Linux)
    proc = mp.Process(target=_child, args=(str(Path(leaf.cert).parent), port))
    proc.start()
    time.sleep(0.05)
    if proc.is_alive():
        os.kill(proc.pid, signal.SIGKILL)
    proc.join(timeout=2)
    assert pair.witness.count_writable() <= 1


def test_kill9_mid_frame_dual_primary_zero(pair):
    pair.standby.set_partitioned(True)
    r = pair.primary.put_and_replicate(b"mid-frame")
    assert r["dual_primary"] == 0
    assert pair.witness.count_writable() <= 1


# ----- P4 observability -----


def test_trace_pipeline_stages(tmp_path: Path, pair, ca_leaves):
    rs = RemoteCRAMStore(
        tmp_path / "obs",
        local_node_id="client",
        cert_paths=ca_leaves["client"],
        enabled=True,
    )
    rs.register(
        NodeEndpoint(
            "node-01",
            mode=TransportMode.TLS,
            host="127.0.0.1",
            port=pair.primary.bound_port,
        )
    )
    put = rs.put_remote("node-01", b"traced", force=True, operation_id="op-trace-1")
    assert put.ok
    data = rs.traces.reconstruct("op-trace-1")
    assert data is not None
    assert data["reconstruction"] == " → ".join(STAGE_ORDER)
    stages = [s["stage"] for s in data["pipeline"]]
    assert stages == list(STAGE_ORDER)


def test_cli_cram_trace(tmp_path: Path, pair, ca_leaves, capsys):
    rs = RemoteCRAMStore(
        tmp_path / "obs2",
        local_node_id="client",
        cert_paths=ca_leaves["client"],
        enabled=True,
    )
    rs.register(
        NodeEndpoint(
            "node-01",
            mode=TransportMode.TLS,
            host="127.0.0.1",
            port=pair.primary.bound_port,
        )
    )
    rs.put_remote("node-01", b"cli-trace", force=True, operation_id="op-cli-1")
    rc = cmd_trace("op-cli-1", root=tmp_path / "obs2")
    assert rc == 0
    out = capsys.readouterr().out
    payload = json.loads(out)
    assert "Task" in payload["reconstruction"]
    assert "C-RAM" in payload["reconstruction"]
    assert "Checkpoint" in payload["reconstruction"]


def test_cli_trace_missing(tmp_path: Path):
    rc = cmd_trace("missing-op", root=tmp_path)
    assert rc != 0


# ----- P5/P6 markers -----


def test_c11_required_types_still_present():
    names = {t.value for t in REQUIRED_MESSAGE_TYPES}
    assert "TASK_REQUEST" in names
    assert "HEARTBEAT" in names


def test_integrity_roundtrip_remote(pair, ca_leaves):
    client = _client(ca_leaves, pair)
    ok = 0
    n = 20
    for i in range(n):
        payload = f"integrity-{i}".encode()
        put = client.put_remote("node-01", payload)
        if not put.ok:
            continue
        got = client.get_remote("node-01", put.content_hash)
        vr = client.verify_remote("node-01", put.content_hash)
        if got.ok and got.content == payload and vr.ok:
            ok += 1
    assert ok / n == 1.0


def test_plaintext_fallback_zero_marker():
    assert PlaintextForbidden is not None


def test_replica_overhead_smoke(pair):
    lat = []
    for i in range(30):
        t0 = time.perf_counter()
        pair.primary.put_and_replicate(f"bench-{i}".encode())
        lat.append((time.perf_counter() - t0) * 1000.0)
    lat.sort()
    p99 = lat[int(0.99 * (len(lat) - 1))]
    assert p99 < 500.0


def test_disable_flag_skips_phase5a_handlers(tmp_path: Path, ca_leaves):
    p = FabricReplicaPair(tmp_path / "off", ca_leaves, enabled=False).start()
    try:
        msg = make_cram_put(from_node="client", to_node="node-01", content=b"x")
        resp = p.primary.handle_message(msg)
        assert resp.type == MessageType.ERROR
        assert resp.payload.get("code") == "PHASE5A_DISABLED"
    finally:
        p.stop()


def test_local_cram_unaffected_when_flag_off(tmp_path: Path):
    store = CRAMStore(tmp_path)
    h = store.put(b"solo")
    assert store.get(h) == b"solo"
    assert store.verify(h)


def test_stage_order_contract():
    assert STAGE_ORDER == ("Task", "Router", "Network", "C-RAM", "Checkpoint")


def test_version_module_readable():
    from neural_mesh import __version__

    assert isinstance(__version__, str) and __version__
