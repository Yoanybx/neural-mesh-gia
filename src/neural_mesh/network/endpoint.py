"""Execution stub endpoint — serves fabric messages over mTLS."""

from __future__ import annotations

import json
import socket
import threading
import time
from pathlib import Path
from typing import Any, Callable

from neural_mesh.cram.store import CRAMStore

from .errors import FabricTLSError, NetworkTimeout
from .protocol import FabricMessage, MessageType, make_ack, make_error
from .tls import NodeCertPaths
from .transport import FrameStream, accept_tls, listen_tcp
from .witness import PrimaryWitness


Handler = Callable[[FabricMessage], FabricMessage]


class ExecutionEndpoint:
    """Threaded accept loop: TASK_REQUEST → stub result + optional C-RAM notice."""

    def __init__(
        self,
        node_id: str,
        paths: NodeCertPaths,
        *,
        host: str = "127.0.0.1",
        port: int = 0,
        cram_root: str | Path | None = None,
        witness: PrimaryWitness | None = None,
        expected_peers: set[str] | None = None,
        handler: Handler | None = None,
    ):
        self.node_id = str(node_id)
        self.paths = paths
        self.host = host
        self.port = int(port)
        self.cram_root = Path(cram_root) if cram_root else None
        self.witness = witness
        self.expected_peers = expected_peers
        self.handler = handler
        self._listen: socket.socket | None = None
        self._thread: threading.Thread | None = None
        self._stop = threading.Event()
        self.served: list[str] = []
        self.last_error: str | None = None
        self._bound_port: int | None = None

    @property
    def bound_port(self) -> int:
        if self._bound_port is None:
            raise RuntimeError("endpoint not started")
        return self._bound_port

    def start(self) -> "ExecutionEndpoint":
        self._listen = listen_tcp(self.host, self.port, backlog=8)
        self._bound_port = int(self._listen.getsockname()[1])
        self._stop.clear()
        self._thread = threading.Thread(target=self._serve_loop, daemon=True)
        self._thread.start()
        return self

    def stop(self) -> None:
        self._stop.set()
        if self._listen is not None:
            try:
                self._listen.close()
            except OSError:
                pass
            self._listen = None
        if self._thread is not None:
            self._thread.join(timeout=2.0)
            self._thread = None

    def _serve_loop(self) -> None:
        assert self._listen is not None
        while not self._stop.is_set():
            try:
                stream = accept_tls(
                    self._listen,
                    self.paths,
                    expected_peer=None,
                    accept_timeout=0.5,
                )
            except NetworkTimeout:
                continue
            except FabricTLSError as exc:
                self.last_error = str(exc)
                continue
            except Exception as exc:  # noqa: BLE001 — stop/closing races
                if self._stop.is_set():
                    break
                # ConnectionDrop on closed listen socket during stop
                self.last_error = str(exc)
                continue
            # Thread-per-connection so a persistent peer session does not
            # block concurrent clients (Cycle 12 Phase 5A requirement).
            def _run(s=stream):
                try:
                    self._handle_conn(s)
                finally:
                    s.close()

            threading.Thread(target=_run, daemon=True).start()

    def _handle_conn(self, stream: FrameStream) -> None:
        peer = stream.peer_node_id
        if self.expected_peers is not None and peer not in self.expected_peers:
            # Identity already bound from cert; optional allow-list soft check.
            pass
        # Multi-message session until peer closes (Cycle 11 NodeSession reuse).
        while not self._stop.is_set():
            try:
                raw = stream.recv_frame()
                msg = FabricMessage.from_dict(raw)
            except Exception as exc:  # noqa: BLE001 — EOF / drop ends session
                self.last_error = str(exc)
                return
            self.served.append(msg.msg_id)
            try:
                resp = self._dispatch(msg)
                stream.send_frame(resp.to_dict())
            except Exception as exc:  # noqa: BLE001
                err = make_error(
                    from_node=self.node_id,
                    to_node=msg.from_node,
                    code="ENDPOINT_ERROR",
                    message=str(exc),
                    ref_msg_id=msg.msg_id,
                )
                try:
                    stream.send_frame(err.to_dict())
                except Exception:  # noqa: BLE001
                    return

    def _dispatch(self, msg: FabricMessage) -> FabricMessage:
        if self.handler is not None:
            return self.handler(msg)
        if msg.type == MessageType.HEARTBEAT:
            return make_ack(
                from_node=self.node_id,
                to_node=msg.from_node,
                ref_msg_id=msg.msg_id,
                extra={"pong": True},
            )
        if msg.type == MessageType.STATE_QUERY:
            state = {
                "node_id": self.node_id,
                "ready": True,
                "writable_primary": (
                    self.witness.writable_primary() if self.witness else None
                ),
            }
            return FabricMessage(
                MessageType.STATE_RESPONSE,
                from_node=self.node_id,
                to_node=msg.from_node,
                payload=state,
            )
        if msg.type == MessageType.CAPABILITY_UPDATE:
            return make_ack(
                from_node=self.node_id,
                to_node=msg.from_node,
                ref_msg_id=msg.msg_id,
                extra={"accepted": True},
            )
        if msg.type == MessageType.TASK_REQUEST:
            return self._handle_task(msg)
        if msg.type == MessageType.CHECKPOINT_NOTICE:
            return make_ack(
                from_node=self.node_id,
                to_node=msg.from_node,
                ref_msg_id=msg.msg_id,
            )
        return make_error(
            from_node=self.node_id,
            to_node=msg.from_node,
            code="UNKNOWN_TYPE",
            message=f"unsupported type {msg.type}",
            ref_msg_id=msg.msg_id,
        )

    def _handle_task(self, msg: FabricMessage) -> FabricMessage:
        # Stub execution: echo task_id, optionally claim primary + C-RAM notice
        if self.witness is not None:
            self.witness.claim(self.node_id)
        result: dict[str, Any] = {
            "task_id": msg.payload.get("task_id"),
            "status": "DONE",
            "node_id": self.node_id,
            "executed_at_ms": int(time.time() * 1000),
        }
        checkpoint_key = None
        if self.cram_root is not None:
            store = CRAMStore(self.cram_root)
            notice = {
                "type": "CHECKPOINT_NOTICE",
                "task_id": msg.payload.get("task_id"),
                "op_id": msg.payload.get("op_id"),
                "trace_id": msg.payload.get("trace_id"),
                "node_id": self.node_id,
                "result": result,
            }
            raw = json.dumps(notice, sort_keys=True, separators=(",", ":")).encode(
                "utf-8"
            )
            meta = {
                "kind": "fabric_checkpoint_notice",
                "task_id": str(msg.payload.get("task_id") or ""),
                "op_id": str(msg.payload.get("op_id") or ""),
            }
            checkpoint_key = store.put(raw, metadata=meta)
            result["checkpoint_content_hash"] = checkpoint_key
        return make_ack(
            from_node=self.node_id,
            to_node=msg.from_node,
            ref_msg_id=msg.msg_id,
            extra={"result": result},
        )


__all__ = ["ExecutionEndpoint"]
