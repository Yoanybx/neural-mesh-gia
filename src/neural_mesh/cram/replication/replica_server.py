"""Out-of-process secondary replica server (Cycle 7).

Serves a node-scoped CRAMStore over a Unix socket with size-limited framing.
Durability: fsync (via CRAMStore._atomic_write) completes before ACK ok=true.
"""

from __future__ import annotations

import base64
import json
import select
import signal
import socket
import sys
from pathlib import Path
from typing import Any, TextIO

from neural_mesh.cram.hashing import content_hash
from neural_mesh.cram.models import utc_now
from neural_mesh.cram.store import CRAMStore

from .framing import IDLE_TIMEOUT, FrameError, FrameTooLarge
from .unix_transport import FrameSocket, TransportError, listen_unix


def _b64encode(data: bytes) -> str:
    return base64.b64encode(data).decode("ascii")


def _b64decode(s: str) -> bytes:
    return base64.b64decode(s.encode("ascii"), validate=True)


class ReplicaServer:
    """Single-connection secondary apply server."""

    def __init__(
        self,
        root: str | Path,
        *,
        node_id: str = "node-02",
        socket_path: str | Path,
        idle_timeout: float = IDLE_TIMEOUT,
    ):
        self.root = Path(root)
        self.node_id = node_id
        self.socket_path = Path(socket_path)
        self.idle_timeout = float(idle_timeout)
        self.store = CRAMStore(self.root / "nodes" / node_id)
        self._seen_ops: set[str] = set()
        self._epochs: dict[str, int] = {}
        self._op_log = self.root / "replication" / f"server_{node_id}_ops.jsonl"
        self._op_log.parent.mkdir(parents=True, exist_ok=True)
        self._load_ops()
        self._listen: socket.socket | None = None
        self._stop = False

    def _load_ops(self) -> None:
        if not self._op_log.exists():
            return
        for line in self._op_log.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            rec = json.loads(line)
            oid = rec.get("op_id")
            if oid:
                self._seen_ops.add(oid)
            key = rec.get("content_hash")
            epoch = int(rec.get("epoch", 0))
            if key and rec.get("result") == "APPLIED":
                self._epochs[key] = max(self._epochs.get(key, 0), epoch)

    def _append_op(self, rec: dict[str, Any]) -> None:
        with self._op_log.open("a", encoding="utf-8") as f:
            f.write(json.dumps(rec, sort_keys=True) + "\n")
            f.flush()
            try:
                import os

                os.fsync(f.fileno())
            except OSError:
                pass

    def request_stop(self) -> None:
        self._stop = True

    def handle_message(self, msg: dict[str, Any]) -> dict[str, Any]:
        mtype = msg.get("type")
        if mtype == "HELLO":
            return {
                "type": "HELLO_ACK",
                "node_id": self.node_id,
                "ready": True,
            }
        if mtype == "PING":
            return {"type": "PONG", "node_id": self.node_id}
        if mtype == "STATUS":
            return {
                "type": "STATUS_RESP",
                "node_id": self.node_id,
                "ready": True,
                "keys": len(list(self.store.cram_dir.rglob("*"))) if self.store.cram_dir.exists() else 0,
            }
        if mtype == "PUT":
            return self._handle_put(msg)
        if mtype == "GET":
            return self._handle_get(msg)
        return {"type": "ERROR", "error": f"unknown type {mtype}"}

    def _handle_put(self, msg: dict[str, Any]) -> dict[str, Any]:
        op_id = str(msg.get("op_id") or "")
        key = str(msg.get("content_hash") or "")
        epoch = int(msg.get("epoch", 0))
        if not op_id or not key:
            return {
                "type": "ACK",
                "op_id": op_id,
                "ok": False,
                "error": "missing op_id or content_hash",
            }
        if op_id in self._seen_ops:
            return {
                "type": "ACK",
                "op_id": op_id,
                "ok": True,
                "duplicate": True,
                "content_hash": key,
            }
        current = self._epochs.get(key, 0)
        if epoch < current:
            self._seen_ops.add(op_id)
            self._append_op(
                {
                    "op_id": op_id,
                    "content_hash": key,
                    "epoch": epoch,
                    "result": "REJECTED_STALE_EPOCH",
                }
            )
            return {
                "type": "ACK",
                "op_id": op_id,
                "ok": False,
                "error": "REJECTED_STALE_EPOCH",
                "content_hash": key,
            }
        try:
            data = _b64decode(str(msg.get("data_b64") or ""))
        except Exception as exc:  # noqa: BLE001
            return {
                "type": "ACK",
                "op_id": op_id,
                "ok": False,
                "error": f"bad data_b64: {exc}",
            }
        if content_hash(data) != key:
            return {
                "type": "ACK",
                "op_id": op_id,
                "ok": False,
                "error": "content_hash mismatch",
                "content_hash": key,
            }
        meta = dict(msg.get("metadata") or {})
        meta.setdefault("stored_at", utc_now())
        meta.setdefault("epoch", epoch)
        meta.setdefault("replica_node", self.node_id)
        # Durable write before ACK (fsync inside _atomic_write).
        self.store._atomic_write(self.store._object_path(key), data)
        self.store._atomic_write(
            self.store._meta_path(key),
            json.dumps(meta, indent=2, sort_keys=True).encode("utf-8"),
        )
        self.store.bind_to_node(key, self.node_id)
        self._epochs[key] = max(current, epoch)
        self._seen_ops.add(op_id)
        self._append_op(
            {
                "op_id": op_id,
                "content_hash": key,
                "epoch": epoch,
                "result": "APPLIED",
            }
        )
        return {
            "type": "ACK",
            "op_id": op_id,
            "ok": True,
            "content_hash": key,
            "epoch": self._epochs[key],
        }

    def _handle_get(self, msg: dict[str, Any]) -> dict[str, Any]:
        key = str(msg.get("content_hash") or "")
        if not key or not self.store.exists(key):
            return {
                "type": "GET_RESP",
                "ok": False,
                "content_hash": key,
                "error": "missing",
            }
        try:
            data = self.store.get(key)
            if content_hash(data) != key:
                return {
                    "type": "GET_RESP",
                    "ok": False,
                    "content_hash": key,
                    "error": "corrupt",
                }
            epoch = self._epochs.get(key, 0)
            try:
                meta = self.store.get_metadata(key)
                if "epoch" in meta:
                    epoch = int(meta["epoch"])
            except Exception:  # noqa: BLE001
                pass
            return {
                "type": "GET_RESP",
                "ok": True,
                "content_hash": key,
                "data_b64": _b64encode(data),
                "epoch": epoch,
            }
        except Exception as exc:  # noqa: BLE001
            return {
                "type": "GET_RESP",
                "ok": False,
                "content_hash": key,
                "error": str(exc),
            }

    def serve_forever(self, *, ready_file: Path | None = None) -> int:
        self._listen = listen_unix(self.socket_path, backlog=1)

        def _sig(_signum: int, _frame: object) -> None:
            self.request_stop()

        signal.signal(signal.SIGTERM, _sig)
        signal.signal(signal.SIGINT, _sig)
        if ready_file is not None:
            ready_file.write_text("ready\n", encoding="utf-8")

        assert self._listen is not None
        while not self._stop:
            rlist, _, _ = select.select([self._listen], [], [], 0.5)
            if not rlist:
                continue
            try:
                conn, _ = self._listen.accept()
            except OSError:
                break
            # Cycle 7: one client at a time; handle then close.
            fs = FrameSocket(conn)
            try:
                self._serve_connection(fs)
            except (TransportError, FrameError, FrameTooLarge, OSError):
                pass
            finally:
                fs.close()
        if self._listen is not None:
            try:
                self._listen.close()
            except OSError:
                pass
        return 0

    def _serve_connection(self, fs: FrameSocket) -> None:
        while not self._stop:
            try:
                msg = fs.recv_frame()
            except TransportError:
                return
            try:
                resp = self.handle_message(msg)
            except Exception as exc:  # noqa: BLE001
                resp = {"type": "ERROR", "error": str(exc)}
            try:
                fs.send_frame(resp)
            except TransportError:
                return
            if msg.get("type") == "BYE":
                return


def run_server(
    *,
    root: Path,
    socket_path: Path,
    node_id: str = "node-02",
    ready_file: Path | None = None,
    out: TextIO = sys.stdout,
) -> int:
    out.write(
        json.dumps(
            {
                "serving": True,
                "socket": str(socket_path),
                "root": str(root),
                "node_id": node_id,
                "tls": "EXPLICIT_DEBT",
            },
            sort_keys=True,
        )
        + "\n"
    )
    out.flush()
    server = ReplicaServer(
        root, node_id=node_id, socket_path=socket_path
    )
    return server.serve_forever(ready_file=ready_file)


__all__ = ["ReplicaServer", "run_server"]
