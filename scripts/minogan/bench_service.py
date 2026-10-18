#!/usr/bin/env python3
"""CP-0088 P0.5 latency benchmark: local loopback /v1/score with a 200-event ScorerInput.

Starts the service in-process on 127.0.0.1 (ephemeral port, temp memory root, throw-away token), sends N
sequential requests (now shifted +1 ms each so every request appends to AgentMemory), prints p50/p95/p99.
No network beyond loopback; nothing is written outside the temp dir.

    .venv/bin/python scripts/minogan/bench_service.py [-n 300] [--json]
"""

from __future__ import annotations

import argparse
import copy
import http.client
import io
import json
import secrets
import statistics
import sys
import tempfile
import threading
import time
from pathlib import Path

from neural_mesh.minogan.canonical import canonical_json
from neural_mesh.minogan.service import (
    MinoganService,
    TokenRegistry,
    hash_token,
    make_server,
)

REPO = Path(__file__).resolve().parents[2]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("-n", type=int, default=300)
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    fx = json.loads((REPO / "tests/fixtures/minogan/scorer_v1_fixtures.json").read_text(encoding="utf-8"))
    base = next(f["input"] for f in fx["fixtures"] if len(f["input"].get("events") or []) == 200)
    tok = secrets.token_urlsafe(24)
    with tempfile.TemporaryDirectory(prefix="mino-bench-") as td:
        svc = MinoganService(Path(td) / "mem", TokenRegistry({base["org_id"]: [hash_token(tok)]}), log=io.StringIO())
        httpd = make_server(svc, "127.0.0.1", 0)
        threading.Thread(target=httpd.serve_forever, daemon=True).start()
        conn = http.client.HTTPConnection("127.0.0.1", httpd.server_address[1], timeout=5)
        lat, size = [], 0
        try:
            for i in range(a.n):
                d = copy.deepcopy(base)
                d["now"] = base["now"] + i
                body = canonical_json(d)
                size = len(body)
                t0 = time.perf_counter()
                conn.request("POST", "/v1/score", body=body, headers={"Authorization": f"Bearer {tok}"})
                r = conn.getresponse()
                r.read()
                lat.append((time.perf_counter() - t0) * 1000)
                if r.status != 200:
                    print(f"request {i}: HTTP {r.status}", file=sys.stderr)
                    return 1
        finally:
            conn.close()
            httpd.shutdown()
            httpd.server_close()
            svc.close()
    lat.sort()
    q = statistics.quantiles(lat, n=100, method="inclusive")
    res = {"n": a.n, "events": 200, "body_bytes": size, "p50_ms": round(q[49], 2), "p95_ms": round(q[94], 2),
           "p99_ms": round(q[98], 2), "max_ms": round(lat[-1], 2), "target_p95_ms": 300, "ok": q[94] < 300}
    print(json.dumps(res) if a.json else " ".join(f"{k}={v}" for k, v in res.items()))
    return 0 if res["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
