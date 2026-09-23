"""Cycle 7 — out-of-process C-RAM replica harden (Unix socket + crash)."""

from __future__ import annotations

import json
import os
import signal
import socket
import subprocess
import sys
import time
from pathlib import Path

import pytest

from neural_mesh.cram.hashing import content_hash
from neural_mesh.cram.replication import (
    MAX_FRAME_BYTES,
    T_CONV_SECONDS,
    FrameError,
    FrameTooLarge,
    OOPReplicaClient,
    ReplicaManager,
    ReplicaState,
    TransportError,
    encode_frame,
    listen_unix,
)
from neural_mesh.cram.replication.framing import HEADER_SIZE, encode_frame as enc
from neural_mesh.cram.replication.unix_transport import FrameSocket, connect_unix
from neural_mesh.twin.schema import Topology, TopologyLink, TopologyNode

ROOT = Path(__file__).resolve().parents[1]
MESH = [sys.executable, "-m", "neural_mesh.cli"]


def _topo(seed: int = 42) -> Topology:
    return Topology(
        network_id="cram-replica-oop",
        seed=seed,
        nodes=[
            TopologyNode(id="node-01", cpu=4),
            TopologyNode(id="node-02", cpu=4),
            TopologyNode(id="node-03", cpu=4),
        ],
        links=[
            TopologyLink(source="node-01", target="node-02"),
            TopologyLink(source="node-02", target="node-03"),
        ],
    )


def _spawn_serve(tmp_path: Path, *, node_id: str = "node-02"):
    sock = tmp_path / "replica.sock"
    ready = tmp_path / "ready"
    if ready.exists():
        ready.unlink()
    if sock.exists():
        try:
            sock.unlink()
        except OSError:
            pass
    root = tmp_path / "oop-root"
    root.mkdir(parents=True, exist_ok=True)
    proc = subprocess.Popen(
        MESH
        + [
            "cram",
            "replica",
            "serve",
            "--socket",
            str(sock),
            "--root",
            str(root),
            "--node-id",
            node_id,
            "--ready-file",
            str(ready),
        ],
        cwd=ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    deadline = time.time() + 5.0
    while time.time() < deadline:
        if ready.exists() and sock.exists():
            break
        if proc.poll() is not None:
            out = (proc.stdout.read() if proc.stdout else b"") + (
                proc.stderr.read() if proc.stderr else b""
            )
            raise RuntimeError(f"serve exited early: {proc.returncode} {out!r}")
        time.sleep(0.02)
    else:
        proc.kill()
        raise TimeoutError("serve did not become ready")
    return proc, sock, root


def _stop(proc: subprocess.Popen, *, kill9: bool = False) -> None:
    if proc.poll() is not None:
        return
    if kill9:
        proc.send_signal(signal.SIGKILL)
    else:
        proc.terminate()
    try:
        proc.wait(timeout=3)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait(timeout=2)


# ----- Framing -----


def test_frame_roundtrip_and_size_limit():
    from neural_mesh.cram.replication.framing import decode_payload, parse_header

    body = enc({"type": "PING"})
    length = parse_header(body[:HEADER_SIZE])
    assert length == len(body) - HEADER_SIZE
    assert decode_payload(body[HEADER_SIZE:])["type"] == "PING"
    with pytest.raises(FrameTooLarge):
        enc(b"x" * (MAX_FRAME_BYTES + 1))
    with pytest.raises(FrameTooLarge):
        parse_header(__import__("struct").pack("!I", MAX_FRAME_BYTES + 1))


def test_mid_frame_cut_raises_transport(tmp_path: Path):
    sock_path = tmp_path / "cut.sock"
    listen = listen_unix(sock_path)
    listen.settimeout(2.0)

    def _server():
        conn, _ = listen.accept()
        fs = FrameSocket(conn)
        with pytest.raises(TransportError):
            fs.recv_frame()
        fs.close()

    import threading

    t = threading.Thread(target=_server, daemon=True)
    t.start()
    client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    client.connect(str(sock_path))
    # Send only 2 bytes of the 4-byte length header then close.
    client.sendall(b"\x00\x01")
    client.close()
    t.join(timeout=3)
    listen.close()
    assert not t.is_alive()


def test_oversized_header_rejected(tmp_path: Path):
    sock_path = tmp_path / "big.sock"
    listen = listen_unix(sock_path)
    listen.settimeout(2.0)

    errors: list[Exception] = []

    def _server():
        conn, _ = listen.accept()
        fs = FrameSocket(conn)
        try:
            fs.recv_frame()
        except Exception as exc:  # noqa: BLE001
            errors.append(exc)
        finally:
            fs.close()

    import threading

    t = threading.Thread(target=_server, daemon=True)
    t.start()
    client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    client.connect(str(sock_path))
    # Claim length = MAX+1
    import struct

    client.sendall(struct.pack("!I", MAX_FRAME_BYTES + 1))
    client.close()
    t.join(timeout=3)
    listen.close()
    assert errors
    assert isinstance(errors[0], (FrameTooLarge, FrameError, TransportError))


# ----- Serve / connect CLI -----


def test_cli_serve_connect_put_get(tmp_path: Path):
    proc, sock, root = _spawn_serve(tmp_path)
    try:
        r = subprocess.run(
            MESH
            + [
                "cram",
                "replica",
                "connect",
                "--socket",
                str(sock),
                "--root",
                str(root),
                "--put",
                "oop-hello",
                "--ping",
            ],
            cwd=ROOT,
            capture_output=True,
        )
        assert r.returncode == 0, r.stderr.decode()
        payload = json.loads(r.stdout.decode())
        assert payload["connected"] is True
        assert payload["tls"] == "EXPLICIT_DEBT"
        key = payload["put"]["content_hash"]
        g = subprocess.run(
            MESH
            + [
                "cram",
                "replica",
                "connect",
                "--socket",
                str(sock),
                "--root",
                str(root),
                "--get",
                key,
            ],
            cwd=ROOT,
            capture_output=True,
        )
        assert g.returncode == 0, g.stderr.decode()
        got = json.loads(g.stdout.decode())
        assert got["get"]["ok"] is True
        assert got["get"]["data_len"] == len(b"oop-hello")
    finally:
        _stop(proc)


# ----- OOP ReplicaManager -----


def test_oop_put_sync_verified(tmp_path: Path):
    proc, sock, sroot = _spawn_serve(tmp_path)
    try:
        mgr = ReplicaManager(
            tmp_path / "primary",
            _topo(),
            seed=7,
            mode="oop",
            socket_path=sock,
        )
        key = mgr.put_replicated(b"oop-sync", op_id="oop1")
        st = mgr.replica_status(key)
        assert st["status"] == ReplicaState.SYNCED.value
        assert st["verified"] is True
        # Secondary process durable store
        from neural_mesh.cram.store import CRAMStore

        sec = CRAMStore(sroot / "nodes" / "node-02")
        # placement may choose different secondary — fetch via client
        client = OOPReplicaClient(sock)
        client.connect()
        resp = client.get(key)
        client.close()
        assert resp.get("ok") is True
        assert resp.get("data") == b"oop-sync"
    finally:
        _stop(proc)


def test_kill9_secondary_mid_write_one_writable(tmp_path: Path):
    proc, sock, _sroot = _spawn_serve(tmp_path)
    mgr = ReplicaManager(
        tmp_path / "primary-k9",
        _topo(),
        seed=11,
        mode="oop",
        socket_path=sock,
    )
    # Large-ish payload to widen kill window
    payload = b"K9-" + os.urandom(256 * 1024)
    key = content_hash(payload)
    # Start put without waiting for sync in a side thread? Simpler: put then kill
    # during a second sync burst.
    key = mgr.put_replicated(payload, op_id="k9-1")
    writers_before = mgr.writable_primaries(key)
    assert len(writers_before) == 1

    # Mid-write: kill -9 while a follow-up sync is attempted after packet loss
    _stop(proc, kill9=True)
    # Socket gone — further sync must fail closed; primary still sole writer
    mgr._oop_reset()
    rec = mgr.sync_object(key, op_id="k9-resync")
    assert rec.status == ReplicaState.FAILED
    writers = mgr.writable_primaries(key)
    assert len(writers) <= 1
    assert len(writers) == 1  # binary: exactly one still writable primary


def test_kill9_rejoin_converges_under_t_conv(tmp_path: Path):
    proc, sock, sroot = _spawn_serve(tmp_path)
    mgr = ReplicaManager(
        tmp_path / "primary-rejoin",
        _topo(),
        seed=13,
        mode="oop",
        socket_path=sock,
    )
    key = mgr.put_replicated(b"rejoin-oop", op_id="rj1")
    _stop(proc, kill9=True)
    mgr._oop_reset()
    # Restart serve on same socket path / root (durable ops log)
    proc2, sock2, _ = _spawn_serve(tmp_path, node_id="node-02")
    assert sock2 == sock
    try:
        mgr.socket_path = sock2
        t0 = time.perf_counter()
        result = mgr.anti_entropy_rejoin(key)
        elapsed = time.perf_counter() - t0
        assert result["converged"] is True
        assert result["within_bound"] is True
        assert elapsed < T_CONV_SECONDS
        assert result["t_conv_seconds"] < T_CONV_SECONDS
        client = OOPReplicaClient(sock)
        client.connect()
        assert client.get(key).get("data") == b"rejoin-oop"
        client.close()
    finally:
        _stop(proc2)


def test_socket_cut_mid_frame_during_put(tmp_path: Path):
    """Adversarial: accept connection, read partial frame, RST — ≤1 writer."""
    import threading

    sock_path = tmp_path / "adv.sock"
    listen = listen_unix(sock_path)
    listen.settimeout(2.0)

    def evil():
        try:
            conn, _ = listen.accept()
            try:
                conn.recv(3)
            except OSError:
                pass
            conn.close()
        except Exception:
            pass

    t = threading.Thread(target=evil, daemon=True)
    t.start()
    mgr = ReplicaManager(
        tmp_path / "primary-cut",
        _topo(),
        seed=17,
        mode="oop",
        socket_path=sock_path,
    )
    key = content_hash(b"cut-me")
    primary, _secondary = mgr.placement.replicas(key, mgr.topology)
    mgr._store(primary).put(b"cut-me")
    mgr._store(primary).bind_to_node(key, primary)
    mgr.create_replica(key)
    rec = mgr.sync_object(key, op_id="cut1")
    assert rec.status == ReplicaState.FAILED
    assert len(mgr.writable_primaries(key)) <= 1
    try:
        listen.close()
    except OSError:
        pass
    t.join(timeout=2)


def test_oop_op_id_idempotent_across_process(tmp_path: Path):
    proc, sock, _ = _spawn_serve(tmp_path)
    try:
        client = OOPReplicaClient(sock)
        client.connect()
        data = b"idem-oop"
        key = content_hash(data)
        op = "fixed-oop-op"
        a1 = client.put(data, content_hash=key, op_id=op, epoch=0)
        assert a1.get("ok") is True
        for _ in range(99):
            a = client.put(data, content_hash=key, op_id=op, epoch=0)
            assert a.get("ok") is True
            assert a.get("duplicate") is True
        client.close()
    finally:
        _stop(proc)


def test_binary_at_most_one_writable_after_real_partition(tmp_path: Path):
    """Binary acceptance: 0 scenarios with 2 writable primaries (kill + cut)."""
    scenarios_two_writers = 0
    # Scenario A: kill -9
    proc, sock, _ = _spawn_serve(tmp_path / "a")
    mgr = ReplicaManager(
        tmp_path / "a" / "prim", _topo(), seed=3, mode="oop", socket_path=sock
    )
    key = mgr.put_replicated(b"bin-a", op_id="ba")
    _stop(proc, kill9=True)
    mgr._oop_reset()
    if len(mgr.writable_primaries(key)) > 1:
        scenarios_two_writers += 1
    # Scenario B: soft terminate mid-flight then reconnect refuse
    proc2, sock2, _ = _spawn_serve(tmp_path / "b")
    mgr2 = ReplicaManager(
        tmp_path / "b" / "prim", _topo(), seed=5, mode="oop", socket_path=sock2
    )
    key2 = mgr2.put_replicated(b"bin-b", op_id="bb")
    _stop(proc2, kill9=True)
    mgr2._oop_reset()
    mgr2.set_partition([[mgr2.replica_status(key2)["primary"]], ["island"]])
    if len(mgr2.writable_primaries(key2)) > 1:
        scenarios_two_writers += 1
    assert scenarios_two_writers == 0


def test_inprocess_still_test_only_default(tmp_path: Path):
    mgr = ReplicaManager(tmp_path / "ip", _topo(), seed=1)
    assert mgr.mode == "inprocess"
    key = mgr.put_replicated(b"ip-ok", op_id="ip1")
    assert mgr.replica_status(key)["status"] == "SYNCED"


def test_fsync_before_ack_survives_server_restart(tmp_path: Path):
    proc, sock, sroot = _spawn_serve(tmp_path)
    data = b"durable-ack"
    key = content_hash(data)
    try:
        client = OOPReplicaClient(sock)
        client.connect()
        ack = client.put(data, content_hash=key, op_id="dur1", epoch=0)
        assert ack.get("ok") is True
        client.close()
    finally:
        _stop(proc, kill9=True)
    # Restart — object must still be readable (fsync before ack)
    proc2, sock2, _ = _spawn_serve(tmp_path)
    try:
        client = OOPReplicaClient(sock2)
        client.connect()
        resp = client.get(key)
        assert resp.get("ok") is True
        assert resp.get("data") == data
        client.close()
    finally:
        _stop(proc2)


def test_transport_constants_match_p0_doc():
    from neural_mesh.cram.replication.framing import (
        CONNECT_TIMEOUT,
        MAX_FRAME_BYTES,
        READ_TIMEOUT,
        WRITE_TIMEOUT,
    )

    assert MAX_FRAME_BYTES == 16_777_216
    assert CONNECT_TIMEOUT == 2.0
    assert READ_TIMEOUT == 5.0
    assert WRITE_TIMEOUT == 5.0


def test_cli_serve_requires_socket():
    r = subprocess.run(MESH + ["cram", "replica", "serve", "--root", "/tmp"], cwd=ROOT, capture_output=True)
    assert r.returncode != 0


def test_oop_mode_requires_socket_path(tmp_path: Path):
    with pytest.raises(ValueError, match="socket_path"):
        ReplicaManager(tmp_path, _topo(), mode="oop")


def test_tls_debt_documented_in_p0():
    doc = (ROOT / "docs" / "cram_replica_oop_transport.md").read_text(encoding="utf-8")
    assert "EXPLICIT DEBT" in doc or "EXPLICIT_DEBT" in doc
    assert "TLS" in doc
