"""Local HTTP service for the Mesh Minogan scorer (CP-0088 P0.5) — stdlib only, loopback only.

Endpoints:
- ``GET  /health``    → ``{ok, service, model_version, contract, methodology, scorer}`` (no auth)
- ``POST /v1/score``  → ScorerOutput (canonical JSON). Body = one ScorerInput (``minogan.scorer/v1``).

Rules:
- ``Authorization: Bearer <token>``; only ``sha256(token)`` is configured (file or env), compared with
  ``hmac.compare_digest`` against every configured hash. The tenant comes from the token; ``org_id`` in the body
  must equal it (else 403 ``tenant_mismatch``).
- Body ≤ 1 MB (413 before reading), ``Content-Length`` required (411). Socket read timeout and a processing
  deadline keep every request < 2 s (408 slow body / 504 deadline); nothing is appended to memory after the deadline.
- Typed contract errors → 4xx JSON ``{"error": {code, message, path?}}``; request content is never echoed.
- Logs are one metadata JSON line per request (tenant, agent, status, latency, digest, score) — never bodies.
- Score is deterministic and LLM-free; after scoring, the memory record and then the score-ledger entry (P0.6) are
  appended (per-agent serialised); the ledger id is returned in ``X-Mesh-Ledger-Id``.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import socket
import sys
import threading
import time
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import TimeoutError as FutureTimeout
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, TextIO

from neural_mesh.minogan.canonical import canonical_json
from neural_mesh.minogan.contract import (
    CONTRACT_VERSION,
    MAX_BODY_BYTES,
    ContractError,
    ContractLimitError,
    parse_scorer_input,
)
from neural_mesh.minogan.ledger import (
    DeadlineExceeded,
    LedgerError,
    ScoreLedger,
    record_scoring,
)
from neural_mesh.minogan.memory import AgentMemory, MemoryError_, MemoryOrderError
from neural_mesh.minogan.scorer import METHODOLOGY, MODEL_VERSION, SCORER_ID, score

SERVICE = "mesh-minogan"
TOKENS_ENV = "MESH_MINOGAN_TOKENS"  # "tenant:sha256hex,tenant2:sha256hex"
TOKENS_FILE_ENV = "MESH_MINOGAN_TOKENS_FILE"  # JSON {"tenants": {"org": ["sha256:<hex>", ...]}}
READ_TIMEOUT_S = 1.0
DEADLINE_S = 1.5
LOOPBACK = {"127.0.0.1", "::1", "localhost"}
_ERR_MESSAGE = {
    "contract_version": "unsupported contract_version",
    "validation": "invalid ScorerInput",
    "content_key": "content keys are not accepted (metadata only)",
    "limit": "ScorerInput exceeds a contract limit",
}
_ERR_STATUS = {"contract_version": 422, "validation": 422, "content_key": 422, "limit": 422}


def hash_token(token: str) -> str:
    return "sha256:" + hashlib.sha256(token.encode("utf-8")).hexdigest()


class TokenRegistry:
    """sha256(token) → tenant. Plain tokens are never stored or logged."""

    def __init__(self, mapping: dict[str, list[str]]):
        self._pairs: list[tuple[str, str]] = []
        for tenant, hashes in mapping.items():
            for h in hashes:
                h = h if h.startswith("sha256:") else "sha256:" + h
                if len(h) != 71 or any(c not in "0123456789abcdef" for c in h[7:]):
                    raise ValueError(f"bad token hash for tenant {tenant!r}")
                self._pairs.append((h, tenant))
        if not self._pairs:
            raise ValueError("no tenant tokens configured")

    @classmethod
    def from_file(cls, path: str | Path) -> TokenRegistry:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        return cls({t: list(v) for t, v in data["tenants"].items()})

    @classmethod
    def from_env_string(cls, s: str) -> TokenRegistry:
        m: dict[str, list[str]] = {}
        for part in filter(None, (p.strip() for p in s.split(","))):
            tenant, _, h = part.partition(":")  # tenant ids contain no ':'; h may carry the sha256: prefix
            m.setdefault(tenant, []).append(h)
        return cls(m)

    @classmethod
    def from_environment(cls, path: str | None = None) -> TokenRegistry:
        path = path or os.environ.get(TOKENS_FILE_ENV)
        if path:
            return cls.from_file(path)
        if os.environ.get(TOKENS_ENV):
            return cls.from_env_string(os.environ[TOKENS_ENV])
        raise ValueError(f"set {TOKENS_FILE_ENV} or {TOKENS_ENV} (sha256 token hashes only)")

    def tenant_for(self, token: str | None) -> str | None:
        if not token:
            return None
        h = hash_token(token)
        found = None
        for known, tenant in self._pairs:  # scan all: no early exit on match
            if hmac.compare_digest(known, h):
                found = tenant
        return found


class MinoganService:
    def __init__(self, memory_root: str | Path, tokens: TokenRegistry, *, log: TextIO | None = None,
                 deadline_s: float = DEADLINE_S, read_timeout_s: float = READ_TIMEOUT_S,
                 score_fn: Callable[..., dict] = score):
        if deadline_s >= 2.0 or read_timeout_s >= 2.0:
            raise ValueError("timeouts must stay < 2 s")
        self.memory = AgentMemory(memory_root)
        self.ledger = ScoreLedger(memory_root)
        self.tokens = tokens
        self.log = log if log is not None else sys.stderr
        self.deadline_s = deadline_s
        self.read_timeout_s = read_timeout_s
        self.score_fn = score_fn
        self._pool = ThreadPoolExecutor(max_workers=8, thread_name_prefix="minogan-score")
        self._agent_locks: dict[tuple[str, str], threading.Lock] = {}
        self._locks_guard = threading.Lock()
        self._log_lock = threading.Lock()

    def _agent_lock(self, tenant: str, agent: str) -> threading.Lock:
        with self._locks_guard:
            return self._agent_locks.setdefault((tenant, agent), threading.Lock())

    def log_line(self, **fields: Any) -> None:
        with self._log_lock:
            self.log.write(json.dumps({"ts": int(time.time() * 1000), "svc": SERVICE, **fields}, sort_keys=True) + "\n")
            self.log.flush()

    def health(self) -> dict[str, Any]:
        return {"ok": True, "service": SERVICE, "model_version": MODEL_VERSION, "contract": CONTRACT_VERSION,
                "methodology": METHODOLOGY, "scorer": SCORER_ID}

    def _score_and_append(self, raw: bytes, tenant: str, deadline: float) -> tuple[int, dict, dict]:
        inp = parse_scorer_input(raw)
        meta = {"agent": inp.agent.id}
        if inp.org_id != tenant:
            return 403, {"error": {"code": "tenant_mismatch", "message": "org_id does not match the token's tenant"}}, meta
        with self._agent_lock(tenant, inp.agent.id):
            # never persist (memory or ledger) a result the client will not receive
            out, rec, entry = record_scoring(inp, self.memory, self.ledger, score_fn=self.score_fn,
                                             check=lambda: time.monotonic() <= deadline)
        meta.update(digest=out["components"]["input_digest"], score=out["score"], seq=rec["seq"], ledger=entry["id"])
        return 200, out, meta

    def handle_score(self, raw: bytes, tenant: str, started: float) -> tuple[int, dict, dict]:
        deadline = started + self.deadline_s
        fut = self._pool.submit(self._score_and_append, raw, tenant, deadline)
        try:
            return fut.result(timeout=max(0.0, deadline - time.monotonic()))
        except FutureTimeout:
            return 504, {"error": {"code": "deadline", "message": "scoring exceeded the deadline"}}, {}
        except ContractError as e:
            status = 413 if isinstance(e, ContractLimitError) and e.path == "$" else _ERR_STATUS.get(e.code, 400)
            # Fixed messages per code: the request content (and parser text derived from it) is never echoed.
            err: dict[str, Any] = {"code": e.code, "message": _ERR_MESSAGE.get(e.code, "invalid ScorerInput")}
            if e.path:
                err["path"] = str(e.path)[:200]
            if e.errors:
                err["errors"] = [{"loc": [str(p)[:64] for p in x["loc"]], "type": x["type"]} for x in e.errors[:20]]
            return status, {"error": err}, {}
        except DeadlineExceeded:
            return 504, {"error": {"code": "deadline", "message": "scoring exceeded the deadline; not recorded"}}, {}
        except LedgerError as e:
            return 500, {"error": {"code": e.code, "message": "score ledger integrity error"}}, {}
        except MemoryOrderError:
            return 409, {"error": {"code": "memory_order", "message": "now is older than this agent's last record"}}, {}
        except MemoryError_ as e:
            return 500, {"error": {"code": e.code, "message": "agent memory integrity error"}}, {}

    def close(self) -> None:
        self._pool.shutdown(wait=False, cancel_futures=True)


def _make_handler(svc: MinoganService) -> type[BaseHTTPRequestHandler]:
    class Handler(BaseHTTPRequestHandler):
        server_version = "mesh-minogan/0"
        sys_version = ""
        protocol_version = "HTTP/1.1"
        disable_nagle_algorithm = True  # headers + body are two writes; avoid Nagle/delayed-ACK 40 ms stalls
        timeout = svc.read_timeout_s  # applied to the connection socket by StreamRequestHandler

        def log_message(self, *_a: Any) -> None:  # default access log disabled (metadata log below)
            return

        def _send(self, status: int, body: dict, extra: dict | None = None) -> None:
            data = canonical_json(body)
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Cache-Control", "no-store")
            for k, v in (extra or {}).items():
                self.send_header(k, v)
            if status >= 400:
                self.send_header("Connection", "close")
                self.close_connection = True
            self.end_headers()
            self.wfile.write(data)

        def _done(self, status: int, started: float, **meta: Any) -> None:
            svc.log_line(method=self.command, path=self.path.split("?")[0], status=status,
                         latency_ms=round((time.monotonic() - started) * 1000, 2), **meta)

        def do_GET(self) -> None:
            t0 = time.monotonic()
            if self.path.split("?")[0] == "/health":
                self._send(200, svc.health())
                self._done(200, t0)
            else:
                self._send(404, {"error": {"code": "not_found", "message": "not found"}})
                self._done(404, t0)

        def do_POST(self) -> None:
            t0 = time.monotonic()
            if self.path.split("?")[0] != "/v1/score":
                self._send(404, {"error": {"code": "not_found", "message": "not found"}})
                return self._done(404, t0)
            auth = self.headers.get("Authorization", "")
            token = auth[7:].strip() if auth[:7].lower() == "bearer " else None
            tenant = svc.tokens.tenant_for(token)
            if tenant is None:
                self._send(401, {"error": {"code": "unauthorized", "message": "missing or invalid bearer token"}},
                           {"WWW-Authenticate": "Bearer"})
                return self._done(401, t0)
            cl = self.headers.get("Content-Length")
            if cl is None or not cl.strip().isdigit():
                self._send(411, {"error": {"code": "length_required", "message": "Content-Length required"}})
                return self._done(411, t0, tenant=tenant)
            n = int(cl)
            if n > MAX_BODY_BYTES:
                self._send(413, {"error": {"code": "payload_too_large", "message": f"body > {MAX_BODY_BYTES} bytes"}})
                return self._done(413, t0, tenant=tenant, bytes=n)
            try:
                raw = self.rfile.read(n)
            except TimeoutError:
                self._send(408, {"error": {"code": "request_timeout", "message": "body not received in time"}})
                return self._done(408, t0, tenant=tenant)
            if len(raw) != n:
                self._send(400, {"error": {"code": "short_body", "message": "body shorter than Content-Length"}})
                return self._done(400, t0, tenant=tenant)
            status, body, meta = svc.handle_score(raw, tenant, t0)
            extra = {"X-Mesh-Memory-Seq": str(meta["seq"]), "X-Mesh-Ledger-Id": meta["ledger"]} if "seq" in meta else None
            self._send(status, body, extra)
            self._done(status, t0, tenant=tenant, bytes=n, err=body.get("error", {}).get("code"), **meta)

    return Handler


class _Server(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = True


def make_server(svc: MinoganService, host: str = "127.0.0.1", port: int = 0) -> ThreadingHTTPServer:
    if host not in LOOPBACK:
        raise ValueError("P0.5 serves on loopback only (deployment is P0.7, operator OK required)")
    if host == "::1":
        _Server.address_family = socket.AF_INET6
    return _Server((host, port), _make_handler(svc))


def serve(memory_root: str, host: str = "127.0.0.1", port: int = 8787, tokens_file: str | None = None) -> None:
    svc = MinoganService(memory_root, TokenRegistry.from_environment(tokens_file))
    httpd = make_server(svc, host, port)
    svc.log_line(event="listening", host=host, port=httpd.server_address[1], model_version=MODEL_VERSION)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        httpd.server_close()
        svc.close()
