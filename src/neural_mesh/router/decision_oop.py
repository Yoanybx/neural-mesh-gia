"""Out-of-process DecisionStore server — kill -9 crash frontier (Cycle 9).

Lightweight AF_UNIX stop-and-wait RPC wrapping DecisionStore so tests can
SIGKILL the C-RAM process mid-persist. Not a general mesh fabric (no TLS).
"""

from __future__ import annotations

import json
import os
import signal
import socket
import sys
import time
from pathlib import Path
from typing import Any

from neural_mesh.cram.replication.framing import (
    CONNECT_TIMEOUT,
    READ_TIMEOUT,
    WRITE_TIMEOUT,
    encode_frame,
    decode_payload,
    parse_header,
    HEADER_SIZE,
)
from neural_mesh.cram.replication.unix_transport import (
    FrameSocket,
    TransportError,
    connect_unix,
)

from .errors import CramPersistError
from .models import RouteDecision
from .persist import DecisionStore


def _recv_exact(sock: socket.socket, n: int, timeout: float) -> bytes:
    buf = bytearray()
    sock.settimeout(timeout)
    while len(buf) < n:
        chunk = sock.recv(n - len(buf))
        if not chunk:
            raise ConnectionError("peer closed")
        buf.extend(chunk)
    return bytes(buf)


def serve_decision_store(
    root: str | Path,
    socket_path: str | Path,
    *,
    ready_file: str | Path | None = None,
    put_delay_ms: float = 0.0,
) -> None:
    """Blocking server loop. ``put_delay_ms`` widens the kill -9 window."""
    root = Path(root)
    socket_path = Path(socket_path)
    if socket_path.exists():
        socket_path.unlink()
    store = DecisionStore(root)
    srv = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    srv.bind(str(socket_path))
    srv.listen(8)
    if ready_file:
        Path(ready_file).write_text("ready\n", encoding="utf-8")
    delay = float(put_delay_ms) / 1000.0
    try:
        while True:
            conn, _ = srv.accept()
            try:
                fs = FrameSocket(conn)
                while True:
                    try:
                        msg = fs.recv_frame()
                    except TransportError:
                        break
                    mtype = msg.get("type")
                    if mtype == "PING":
                        fs.send_frame({"type": "PONG"})
                    elif mtype == "PUT":
                        if delay > 0:
                            time.sleep(delay)
                        dec = RouteDecision.from_dict(msg["decision"])
                        replay = msg.get("replay") or {}
                        try:
                            key = store.put(dec, replay=replay)
                            fs.send_frame({"type": "ACK", "key": key})
                        except CramPersistError as exc:
                            fs.send_frame(
                                {
                                    "type": "ERROR",
                                    "code": exc.code,
                                    "message": str(exc),
                                }
                            )
                    elif mtype == "GET_OP":
                        d = store.get_by_op_id(str(msg.get("op_id", "")))
                        if d is None:
                            fs.send_frame({"type": "MISS"})
                        else:
                            fs.send_frame(
                                {"type": "HIT", "decision": d.to_dict()}
                            )
                    elif mtype == "COUNT":
                        fs.send_frame({"type": "COUNT", "n": store.count()})
                    elif mtype == "BYE":
                        fs.send_frame({"type": "BYE"})
                        break
                    else:
                        fs.send_frame(
                            {"type": "ERROR", "code": "UNKNOWN", "message": mtype}
                        )
            finally:
                try:
                    conn.close()
                except OSError:
                    pass
    finally:
        srv.close()
        if socket_path.exists():
            try:
                socket_path.unlink()
            except OSError:
                pass


class RemoteDecisionStore:
    """DecisionStore client over Unix socket — fail-closed on transport loss."""

    def __init__(
        self,
        socket_path: str | Path,
        *,
        connect_timeout: float = CONNECT_TIMEOUT,
        read_timeout: float = READ_TIMEOUT,
        write_timeout: float = WRITE_TIMEOUT,
    ):
        self.socket_path = Path(socket_path)
        self.connect_timeout = connect_timeout
        self.read_timeout = read_timeout
        self.write_timeout = write_timeout

    def _rpc(self, msg: dict[str, Any]) -> dict[str, Any]:
        try:
            with connect_unix(
                self.socket_path,
                connect_timeout=self.connect_timeout,
                read_timeout=self.read_timeout,
                write_timeout=self.write_timeout,
            ) as fs:
                return fs.request(msg)
        except (TransportError, OSError, ConnectionError) as exc:
            raise CramPersistError(
                "C-RAM OOP transport failed",
                op_id=str(msg.get("decision", {}).get("op_id", msg.get("op_id", ""))),
                cause=str(exc),
            ) from exc

    def put(
        self,
        decision: RouteDecision,
        *,
        replay: dict[str, Any] | None = None,
    ) -> str:
        resp = self._rpc(
            {
                "type": "PUT",
                "decision": decision.to_dict(),
                "replay": dict(replay) if replay else {},
            }
        )
        if resp.get("type") == "ACK" and resp.get("key"):
            return str(resp["key"])
        raise CramPersistError(
            "C-RAM OOP persist ack missing",
            op_id=decision.op_id,
            trace_id=decision.trace_id,
            cause=json.dumps(resp, sort_keys=True),
        )

    def get_by_op_id(self, op_id: str) -> RouteDecision | None:
        try:
            resp = self._rpc({"type": "GET_OP", "op_id": op_id})
        except CramPersistError:
            return None
        if resp.get("type") == "HIT":
            return RouteDecision.from_dict(resp["decision"])
        return None

    def count(self) -> int:
        resp = self._rpc({"type": "COUNT"})
        return int(resp.get("n", 0))

    def has_op_id(self, op_id: str) -> bool:
        return self.get_by_op_id(op_id) is not None

    # Local filesystem reopen helpers used after server death are on DecisionStore.


def spawn_decision_server(
    root: Path,
    socket_path: Path,
    *,
    ready_file: Path,
    put_delay_ms: float = 25.0,
) -> Any:
    """Start serve_decision_store in a child process; return Popen."""
    import subprocess

    env = os.environ.copy()
    env["PYTHONPATH"] = str(
        Path(__file__).resolve().parents[2]
    ) + os.pathsep + env.get("PYTHONPATH", "")
    proc = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "neural_mesh.router.decision_oop",
            "--root",
            str(root),
            "--socket",
            str(socket_path),
            "--ready-file",
            str(ready_file),
            "--put-delay-ms",
            str(put_delay_ms),
        ],
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
    )
    # Wait for ready
    for _ in range(200):
        if ready_file.exists():
            break
        if proc.poll() is not None:
            err = (proc.stderr.read() or b"").decode("utf-8", errors="replace")
            raise RuntimeError(f"decision_oop server exited early: {err}")
        time.sleep(0.01)
    if not ready_file.exists():
        proc.kill()
        raise RuntimeError("decision_oop server ready timeout")
    return proc


def kill9(proc: Any) -> None:
    try:
        os.kill(proc.pid, signal.SIGKILL)
    except ProcessLookupError:
        pass
    try:
        proc.wait(timeout=2)
    except Exception:  # noqa: BLE001
        pass


def main(argv: list[str] | None = None) -> int:
    import argparse

    p = argparse.ArgumentParser(prog="decision_oop")
    p.add_argument("--root", required=True)
    p.add_argument("--socket", required=True)
    p.add_argument("--ready-file", default=None)
    p.add_argument("--put-delay-ms", type=float, default=0.0)
    a = p.parse_args(argv)
    serve_decision_store(
        a.root,
        a.socket,
        ready_file=a.ready_file,
        put_delay_ms=a.put_delay_ms,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
