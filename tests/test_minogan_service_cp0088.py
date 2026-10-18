"""CP-0088 P0.5 — local loopback HTTP service: POST /v1/score, GET /health, auth, limits, timeouts, latency."""

from __future__ import annotations

import copy
import http.client
import io
import json
import socket
import statistics
import threading
import time
from pathlib import Path

import pytest

from neural_mesh.minogan import parse_scorer_input
from neural_mesh.minogan.canonical import canonical_json
from neural_mesh.minogan.contract import CONTRACT_VERSION, MAX_BODY_BYTES
from neural_mesh.minogan.memory import AgentMemory
from neural_mesh.minogan.scorer import MODEL_VERSION, score
from neural_mesh.minogan.service import (
    MinoganService,
    TokenRegistry,
    hash_token,
    make_server,
)

pytestmark = pytest.mark.minogan_cp0088

REPO = Path(__file__).resolve().parents[1]
FX = json.loads((REPO / "tests/fixtures/minogan/scorer_v1_fixtures.json").read_text(encoding="utf-8"))["fixtures"]
BIG = next(f["input"] for f in FX if len(f["input"].get("events") or []) == 200)
TENANT = BIG["org_id"]
OTHER = "org_other"
TOK_A = "tok-a-" + "x" * 32
TOK_B = "tok-b-" + "y" * 32


def _recv_all(c: socket.socket) -> str:
    """Read until the server closes (error responses send Connection: close; headers/body may arrive split)."""
    buf = b""
    while chunk := c.recv(65536):
        buf += chunk
    return buf.decode()


class Srv:
    def __init__(self, tmp: Path, **kw):
        self.log = io.StringIO()
        reg = TokenRegistry({TENANT: [hash_token(TOK_A)], OTHER: [hash_token(TOK_B)]})
        self.root = tmp / "mem"
        self.svc = MinoganService(self.root, reg, log=self.log, **kw)
        self.httpd = make_server(self.svc, "127.0.0.1", 0)
        self.port = self.httpd.server_address[1]
        self.t = threading.Thread(target=self.httpd.serve_forever, daemon=True)
        self.t.start()

    def req(self, method, path, body=None, token=TOK_A, headers=None):
        c = http.client.HTTPConnection("127.0.0.1", self.port, timeout=5)
        h = dict(headers or {})
        if token is not None:
            h["Authorization"] = f"Bearer {token}"
        data = body if isinstance(body, bytes | type(None)) else canonical_json(body)
        c.request(method, path, body=data, headers=h)
        r = c.getresponse()
        out = r.status, dict(r.getheaders()), r.read()
        c.close()
        return out

    def close(self):
        self.httpd.shutdown()
        self.httpd.server_close()
        self.svc.close()


@pytest.fixture
def srv(tmp_path):
    s = Srv(tmp_path)
    yield s
    s.close()


def _shift(inp, i):
    d = copy.deepcopy(inp)
    d["now"] = inp["now"] + i
    return d


# ----------------------------------------------------------------------------- health / happy path


def test_health(srv):
    st, h, b = srv.req("GET", "/health", token=None)
    assert st == 200 and h["Content-Type"] == "application/json"
    j = json.loads(b)
    assert j["ok"] is True and j["model_version"] == MODEL_VERSION and j["contract"] == CONTRACT_VERSION


def test_score_matches_direct_path_and_appends(srv, tmp_path):
    st, h, b = srv.req("POST", "/v1/score", BIG)
    assert st == 200, b
    direct = score(parse_scorer_input(BIG), memory=AgentMemory(tmp_path / "direct"))
    assert b == canonical_json(direct)  # byte-identical to the in-process deterministic scorer
    assert h["X-Mesh-Memory-Seq"] == "1"
    agent = BIG["agent"]["id"]
    assert AgentMemory(srv.root).head(TENANT, agent)["seq"] == 1
    st, h, _ = srv.req("POST", "/v1/score", _shift(BIG, 1000))
    assert st == 200 and h["X-Mesh-Memory-Seq"] == "2"
    assert AgentMemory(srv.root).verify_chain(TENANT, agent)["ok"] is True


def test_older_now_is_409(srv):
    assert srv.req("POST", "/v1/score", _shift(BIG, 10))[0] == 200
    st, _, b = srv.req("POST", "/v1/score", BIG)
    assert st == 409 and json.loads(b)["error"]["code"] == "memory_order"


def test_unknown_path_404(srv):
    assert srv.req("GET", "/nope")[0] == 404
    assert srv.req("POST", "/v1/other", BIG)[0] == 404


# ----------------------------------------------------------------------------- auth


@pytest.mark.parametrize(
    "headers,token",
    [({}, None), ({}, "wrong-token"), ({}, ""), ({"Authorization": f"Basic {TOK_A}"}, None),
     ({"Authorization": hash_token(TOK_A)}, None)],
)
def test_auth_missing_or_invalid_is_401(srv, headers, token):
    st, h, b = srv.req("POST", "/v1/score", BIG, token=token, headers=headers)
    assert st == 401 and h.get("WWW-Authenticate") == "Bearer"
    assert json.loads(b)["error"]["code"] == "unauthorized"
    assert not (srv.root / "tenants").exists() or not any((srv.root).rglob("head.json"))


def test_cross_tenant_org_mismatch_is_403_and_writes_nothing(srv):
    st, _, b = srv.req("POST", "/v1/score", BIG, token=TOK_B)  # valid token, other tenant
    assert st == 403 and json.loads(b)["error"]["code"] == "tenant_mismatch"
    assert not any(srv.root.rglob("head.json"))
    body = copy.deepcopy(BIG)
    body["org_id"] = OTHER
    st, _, b = srv.req("POST", "/v1/score", body, token=TOK_A)
    assert st == 403


def test_token_registry_stores_hashes_only():
    reg = TokenRegistry.from_env_string(f"{TENANT}:{hash_token(TOK_A)},{OTHER}:{hash_token(TOK_B)[7:]}")
    assert reg.tenant_for(TOK_A) == TENANT and reg.tenant_for(TOK_B) == OTHER and reg.tenant_for("x") is None
    assert TOK_A not in repr(reg.__dict__)
    with pytest.raises(ValueError):
        TokenRegistry({TENANT: [TOK_A]})  # a plaintext token is refused as a config value
    with pytest.raises(ValueError):
        TokenRegistry({})


def test_tokens_file(tmp_path, monkeypatch):
    p = tmp_path / "tokens.json"
    p.write_text(json.dumps({"tenants": {TENANT: [hash_token(TOK_A)]}}))
    monkeypatch.setenv("MESH_MINOGAN_TOKENS_FILE", str(p))
    assert TokenRegistry.from_environment().tenant_for(TOK_A) == TENANT


# ----------------------------------------------------------------------------- limits / contract errors


def test_body_over_1mb_is_413_without_reading(srv):
    c = socket.create_connection(("127.0.0.1", srv.port), timeout=5)
    c.sendall(
        f"POST /v1/score HTTP/1.1\r\nHost: x\r\nAuthorization: Bearer {TOK_A}\r\n"
        f"Content-Type: application/json\r\nContent-Length: {MAX_BODY_BYTES + 1}\r\n\r\n".encode()
    )
    t0 = time.monotonic()
    resp = _recv_all(c)
    c.close()
    assert resp.startswith("HTTP/1.1 413") and time.monotonic() - t0 < 1.0
    assert '"payload_too_large"' in resp


def test_missing_length_is_411(srv):
    c = socket.create_connection(("127.0.0.1", srv.port), timeout=5)
    c.sendall(f"POST /v1/score HTTP/1.1\r\nHost: x\r\nAuthorization: Bearer {TOK_A}\r\n\r\n".encode())
    assert _recv_all(c).startswith("HTTP/1.1 411")
    c.close()


SECRET = "S3CRET-CANARY-7731"


@pytest.mark.parametrize(
    "mutate,status,code",
    [
        (lambda d: d.update(contract=SECRET), 422, "contract_version"),
        (lambda d: d["events"][0].update(prompt=SECRET), 422, "content_key"),
        (lambda d: d["agent"].update(extra_field=SECRET), 422, "validation"),
        (lambda d: d.update(now=SECRET), 422, "validation"),
        (lambda d: d.update(events=d["events"] * 6), 422, "limit"),
    ],
)
def test_contract_errors_are_typed_4xx_without_echo(srv, mutate, status, code):
    d = copy.deepcopy(BIG)
    mutate(d)
    st, h, b = srv.req("POST", "/v1/score", d)
    assert st == status and h["Content-Type"] == "application/json"
    err = json.loads(b)["error"]
    assert err["code"] == code
    assert SECRET not in b.decode() and SECRET not in srv.log.getvalue()
    assert not any(srv.root.rglob("head.json"))


def test_invalid_json_is_4xx_without_echo(srv):
    st, _, b = srv.req("POST", "/v1/score", b'{"contract": "' + SECRET.encode() + b'", oops')
    assert st == 422 and SECRET not in b.decode()


# ----------------------------------------------------------------------------- timeouts (< 2 s)


def test_slow_scoring_hits_deadline_and_is_not_recorded(tmp_path):
    def slow(inp, memory=None):
        time.sleep(2.5)
        return score(inp, memory=memory)

    s = Srv(tmp_path, score_fn=slow)
    try:
        t0 = time.monotonic()
        st, _, b = s.req("POST", "/v1/score", BIG)
        el = time.monotonic() - t0
        assert st == 504 and json.loads(b)["error"]["code"] == "deadline"
        assert el < 2.0, el
        time.sleep(1.5)  # let the worker finish: it must not append after the deadline
        assert not any(s.root.rglob("days/*.jsonl"))
    finally:
        s.close()


def test_slow_body_is_408_under_2s(srv):
    c = socket.create_connection(("127.0.0.1", srv.port), timeout=5)
    c.sendall(
        f"POST /v1/score HTTP/1.1\r\nHost: x\r\nAuthorization: Bearer {TOK_A}\r\nContent-Length: 1000\r\n\r\n{{".encode()
    )
    t0 = time.monotonic()
    resp = _recv_all(c)
    el = time.monotonic() - t0
    c.close()
    assert resp.startswith("HTTP/1.1 408") and el < 2.0, (resp[:40], el)


def test_idle_connection_closed_under_2s(srv):
    c = socket.create_connection(("127.0.0.1", srv.port), timeout=5)
    t0 = time.monotonic()
    assert c.recv(1) == b""  # server drops a silent client after the read timeout
    assert time.monotonic() - t0 < 2.0
    c.close()


def test_timeouts_must_stay_under_2s(tmp_path):
    reg = TokenRegistry({TENANT: [hash_token(TOK_A)]})
    with pytest.raises(ValueError):
        MinoganService(tmp_path, reg, deadline_s=2.0)
    with pytest.raises(ValueError):
        MinoganService(tmp_path, reg, read_timeout_s=5)


# ----------------------------------------------------------------------------- loopback / logs / latency


def test_loopback_only(tmp_path):
    svc = MinoganService(tmp_path, TokenRegistry({TENANT: [hash_token(TOK_A)]}))
    with pytest.raises(ValueError):
        make_server(svc, "0.0.0.0", 0)
    svc.close()


def test_logs_are_metadata_only(srv):
    srv.req("POST", "/v1/score", BIG)
    srv.req("POST", "/v1/score", BIG, token="bad")
    log = srv.log.getvalue()
    lines = [json.loads(x) for x in log.splitlines()]
    assert [x["status"] for x in lines] == [200, 401]
    assert lines[0]["tenant"] == TENANT and lines[0]["score"] >= 0 and "digest" in lines[0]
    for needle in (TOK_A, "bad", BIG["agent"]["name"], BIG["agent"]["function"], BIG["events"][0]["name"],
                   BIG["events"][0]["trace_id"]):
        assert needle not in log, needle


def test_latency_p95_under_300ms_with_200_events(srv):
    lat = []
    for i in range(60):
        t0 = time.perf_counter()
        st, _, _ = srv.req("POST", "/v1/score", _shift(BIG, i))
        lat.append((time.perf_counter() - t0) * 1000)
        assert st == 200
    lat.sort()
    p50, p95 = statistics.median(lat), lat[int(0.95 * len(lat)) - 1]
    print(f"\n[P0.5 latency] n={len(lat)} events=200 p50={p50:.1f}ms p95={p95:.1f}ms")
    assert p95 < 300, (p50, p95)


# ----------------------------------------------------------------------------- CLI


def test_cli_hash_token_and_serve(tmp_path):
    import os
    import subprocess
    import sys

    env = {**os.environ, "PYTHONPATH": str(REPO / "src")}
    h = subprocess.run([sys.executable, "-m", "neural_mesh.cli", "minogan", "hash-token"], check=False, input=TOK_A + "\n",
                       capture_output=True, text=True, env=env, timeout=30, cwd=tmp_path)
    assert h.returncode == 0 and h.stdout.strip() == hash_token(TOK_A)
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        port = s.getsockname()[1]
    env["MESH_MINOGAN_TOKENS"] = f"{TENANT}:{h.stdout.strip()}"
    p = subprocess.Popen([sys.executable, "-m", "neural_mesh.cli", "minogan", "serve", "--port", str(port),
                          "--memory-root", str(tmp_path / "mem")], env=env, cwd=tmp_path,
                         stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    try:
        line = json.loads(p.stderr.readline())
        assert line["event"] == "listening" and line["host"] == "127.0.0.1" and line["port"] == port
        c = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
        c.request("GET", "/health")
        assert json.loads(c.getresponse().read())["contract"] == CONTRACT_VERSION
        c.request("POST", "/v1/score", body=canonical_json(BIG), headers={"Authorization": f"Bearer {TOK_A}"})
        assert c.getresponse().status == 200
        c.close()
    finally:
        p.terminate()
        p.wait(timeout=10)
    assert TOK_A not in p.stderr.read()
