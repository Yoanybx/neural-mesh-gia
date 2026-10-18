#!/usr/bin/env python3
"""Loopback smoke test for the Mesh Minogan service (stdlib only; runs inside the container or on the host).

    MINOGAN_SMOKE_TOKEN=<token> python smoke.py --port 8787 --input smoke_input.json

Checks: GET /health (ok, model_version, contract) · POST /v1/score without token → 401 · POST with token → 200,
X-Mesh-Ledger-Id present. The token comes from the environment (never argv, never printed).
"""

from __future__ import annotations

import argparse
import http.client
import json
import os
import sys


def req(port: int, method: str, path: str, body: bytes | None = None, token: str | None = None):
    c = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
    h = {"Content-Type": "application/json"}
    if token:
        h["Authorization"] = f"Bearer {token}"
    c.request(method, path, body=body, headers=h)
    r = c.getresponse()
    out = r.status, {k.lower(): v for k, v in r.getheaders()}, r.read()
    c.close()
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8787)
    ap.add_argument("--input", required=True)
    a = ap.parse_args()
    token = os.environ.get("MINOGAN_SMOKE_TOKEN")
    if not token:
        print("set MINOGAN_SMOKE_TOKEN", file=sys.stderr)
        return 2
    with open(a.input, "rb") as f:
        body = f.read()
    st, _, b = req(a.port, "GET", "/health")
    health = json.loads(b)
    res = {"health_status": st, "health_ok": health.get("ok"), "model_version": health.get("model_version"),
           "contract": health.get("contract")}
    res["unauth_status"] = req(a.port, "POST", "/v1/score", body)[0]
    st, h, b = req(a.port, "POST", "/v1/score", body, token)
    res["score_status"] = st
    if st == 200:
        out = json.loads(b)
        res.update(score=out["score"], uw_outcome=out["components"]["uw"]["outcome"],
                   input_digest=out["components"]["input_digest"], ledger_id=h.get("x-mesh-ledger-id"),
                   memory_seq=h.get("x-mesh-memory-seq"))
    ok = res["health_ok"] is True and res["unauth_status"] == 401 and st == 200 and bool(res.get("ledger_id"))
    res["ok"] = ok
    print(json.dumps(res, sort_keys=True))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
