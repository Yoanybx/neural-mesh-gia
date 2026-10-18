"""CP-0088 P0.7 — deploy PROPOSAL artifacts: Dockerfile / compose invariants + loopback smoke (no Docker needed)."""

from __future__ import annotations

import importlib.util
import json
import os
import re
import subprocess
import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.minogan_cp0088

REPO = Path(__file__).resolve().parents[1]
D = REPO / "deploy/minogan"
DOCKERFILE = (D / "Dockerfile").read_text(encoding="utf-8")
COMPOSE = (D / "compose.proposal.yaml").read_text(encoding="utf-8")


def _instr(name: str) -> list[str]:
    return [ln for ln in DOCKERFILE.splitlines() if ln.startswith(name + " ")]


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_dockerfile_invariants():
    froms = _instr("FROM")
    assert len(froms) == 2 and all("${PYTHON_IMAGE}" in f for f in froms)
    assert "ARG PYTHON_IMAGE=python:3.13-slim" in DOCKERFILE
    users = _instr("USER")
    assert users == ["USER 10001:10001"]
    assert DOCKERFILE.index("USER 10001") > DOCKERFILE.index("pip install --no-index")  # non-root after install
    assert _instr("VOLUME") == ['VOLUME ["/data"]']
    assert "MESH_MINOGAN_TOKENS_FILE=/run/secrets/minogan_tokens" in DOCKERFILE
    assert not _instr("EXPOSE")  # nothing on a routable interface
    ep = json.loads(_instr("ENTRYPOINT")[0].split(" ", 1)[1])
    assert ep[:3] == ["mesh", "minogan", "serve"] and ep[ep.index("--host") + 1] == "127.0.0.1"
    assert "0.0.0.0" not in DOCKERFILE
    hc = DOCKERFILE[DOCKERFILE.index("HEALTHCHECK"):]
    assert "http://127.0.0.1:%s/health" in hc
    assert _instr("STOPSIGNAL") == ["STOPSIGNAL SIGINT"]
    for bad in ("COPY tests", "COPY .project_state", "ADD ", "TOKEN=", "secret="):
        assert bad not in DOCKERFILE


def test_dockerignore_is_an_allowlist():
    lines = [ln.strip() for ln in (D / "Dockerfile.dockerignore").read_text().splitlines()
             if ln.strip() and not ln.startswith("#")]
    assert lines[0] == "*" and "!pyproject.toml" in lines and "!src/**" in lines
    assert not any(ln.startswith("!") and ln not in ("!pyproject.toml", "!src/", "!src/**") for ln in lines)


def test_compose_proposal_single_writer_no_ports_secrets_outside_repo():
    assert "PROPOSAL ONLY" in COMPOSE
    assert re.search(r"^\s*replicas: 1\b", COMPOSE, re.MULTILINE)
    assert 'network_mode: "service:mesh-minogan"' in COMPOSE
    assert not re.search(r"^\s*ports:", COMPOSE, re.MULTILINE)
    assert "file: /etc/mesh-minogan/tokens.json" in COMPOSE
    assert "minogan-data:/data" in COMPOSE


def test_proposal_doc_marks_no_cost_and_unbuilt_image():
    doc = (REPO / "docs/planning/CP_0088_P0_7_DEPLOY_PROPOSAL.md").read_text(encoding="utf-8")
    assert "No costs incurred" in doc and "2026-10-18" in doc
    assert "image was NOT built" in doc
    for url in ("https://fly.io/docs/about/pricing/", "https://www.digitalocean.com/pricing/droplets",
                "https://developers.cloudflare.com/containers/faq/", "https://railway.com/pricing",
                "https://render.com/pricing", "https://developers.cloudflare.com/r2/pricing/"):
        assert url in doc


def test_smoke_against_loopback_service_and_healthcheck(tmp_path, monkeypatch, capsys):
    svc_tests = _load(REPO / "tests/test_minogan_service_cp0088.py", "_mino_svc_tests_p07")
    smoke = _load(D / "smoke.py", "_mino_smoke")
    inp = json.loads((D / "smoke_input.json").read_text())
    fx = next(f for f in svc_tests.FX if f["input"] == inp)
    from neural_mesh.minogan.service import (
        MinoganService,
        TokenRegistry,
        hash_token,
        make_server,
    )

    tok = "smoke-" + "z" * 30
    svc = MinoganService(tmp_path / "data", TokenRegistry({inp["org_id"]: [hash_token(tok)]}),
                         log=open(os.devnull, "w"))  # noqa: SIM115
    httpd = make_server(svc, "127.0.0.1", 0)
    import threading

    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    port = httpd.server_address[1]
    try:
        monkeypatch.setenv("MINOGAN_SMOKE_TOKEN", tok)
        monkeypatch.setattr(sys, "argv", ["smoke.py", "--port", str(port), "--input", str(D / "smoke_input.json")])
        assert smoke.main() == 0
        res = json.loads(capsys.readouterr().out)
        assert res["ok"] and res["unauth_status"] == 401 and res["score"] == fx["expected"]["score"]
        assert res["ledger_id"].startswith("msl_") and tok not in json.dumps(res)
        hc = json.loads(DOCKERFILE[DOCKERFILE.index('CMD ["python"'):].split("\n")[0][4:])
        assert hc[0] == "python"
        r = subprocess.run([sys.executable, *hc[1:]], env={**os.environ, "MESH_MINOGAN_PORT": str(port)}, timeout=10, check=False)
        assert r.returncode == 0  # the image HEALTHCHECK command, verbatim
    finally:
        httpd.shutdown()
        httpd.server_close()
        svc.close()
