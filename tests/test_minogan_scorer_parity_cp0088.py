"""CP-0088 P0.3 — Mesh scorer v0: parity (±1) with pilot computeScore score_v0.3, determinism, zero network.

Expected outputs were captured from the REAL pilot JS (ruleScorer -> computeScore) by scripts/minogan/gen_fixtures.mjs.
"""

from __future__ import annotations

import ast
import hashlib
import json
import os
import socket
import subprocess
import sys
from pathlib import Path

import pytest

from neural_mesh.minogan import parse_scorer_input
from neural_mesh.minogan.contract import ContractError, ScorerOutput
from neural_mesh.minogan.scorer import (
    METHODOLOGY,
    MODEL_VERSION,
    MeshScorer,
    js_round,
    score,
    score_bytes,
    uw_outcome,
)

pytestmark = pytest.mark.minogan_cp0088

REPO = Path(__file__).resolve().parents[1]
FX = json.loads((REPO / "tests/fixtures/minogan/scorer_v1_fixtures.json").read_text(encoding="utf-8"))["fixtures"]
SCORER_SRC = REPO / "src/neural_mesh/minogan/scorer.py"


def _pilot_uw(s: int) -> str:  # rules.js uwOutcome, verbatim logic
    return "bind" if s < 40 else "bind-with-terms" if s < 65 else "refer"


def test_enough_fixtures():
    assert len(FX) >= 50
    assert sum("variant" not in f["step"] for f in FX) >= 50


def test_parity_within_one_on_all_fixtures():
    diffs = [abs(score(f["input"])["score"] - f["expected"]["score"]) for f in FX]
    assert max(diffs) <= 1, f"max abs diff {max(diffs)}"


def test_parity_exact_fields():
    """Stronger than required: exposure/behavior/drift/axes/cited/explain also match the pilot."""
    bad = []
    for f in FX:
        o, e = score(f["input"]), f["expected"]
        for k in ("score", "exposure", "behavior", "driftStatus", "axes", "cited_trace_ids"):
            if o[k] != e[k]:
                bad.append((f["id"], k))
        if abs(o["driftPct"] - e["driftPct"]) > 1e-9:
            bad.append((f["id"], "driftPct"))
        for k in ("explain", "floor", "drift", "exposure", "behavior"):
            if o["components"][k] != e["components"][k]:
                bad.append((f["id"], f"components.{k}"))
    assert not bad, bad[:10]


def test_same_input_byte_identical_output():
    for f in FX:
        assert score_bytes(f["input"]) == score_bytes(json.loads(json.dumps(f["input"])))


def test_byte_identical_across_processes_and_hash_seeds():
    code = (
        "import json,hashlib,sys;from neural_mesh.minogan.scorer import score_bytes;"
        "F=json.load(open(sys.argv[1]))['fixtures'];"
        "print(hashlib.sha256(b''.join(score_bytes(f['input']) for f in F)).hexdigest())"
    )
    fx = str(REPO / "tests/fixtures/minogan/scorer_v1_fixtures.json")
    outs = set()
    for seed in ("0", "1", "424242"):
        env = {**os.environ, "PYTHONHASHSEED": seed}
        r = subprocess.run([sys.executable, "-c", code, fx], capture_output=True, text=True, env=env, check=True, timeout=120)
        outs.add(r.stdout.strip())
    local = hashlib.sha256(b"".join(score_bytes(f["input"]) for f in FX)).hexdigest()
    assert outs == {local}


def test_output_contract_and_invariants():
    for f in FX:
        inp = parse_scorer_input(f["input"])
        o = score(inp)
        m = ScorerOutput.model_validate(o)
        universe = inp.trace_id_universe()
        assert set(m.cited_trace_ids) <= universe and len(m.cited_trace_ids) <= 50
        assert m.driftStatus in {"stable", "watch", "elevated", "critical"}
        c = m.components
        assert 0 <= c.confidence <= 1
        assert c.model_version == MODEL_VERSION and m.methodology == METHODOLOGY and m.scorer == "mesh"
        assert c.input_digest == "sha256:" + f["input_sha256"]
        assert c.advisory is None  # L_judge never involved in the number
        assert all(set(r.evidence_trace_ids) <= universe for r in c.reasons)
        assert abs(sum(r.weight for r in c.reasons) - m.score) <= 1.5, f["id"]


def test_drift_status_coverage():
    assert {score(f["input"])["driftStatus"] for f in FX} == {"stable", "watch", "elevated", "critical"}


def test_uw_outcome_matches_pilot_and_never_declines():
    seen = set()
    for f in FX:
        o = score(f["input"])
        uw = o["components"]["uw"]
        assert uw["outcome"] == _pilot_uw(f["expected"]["score"]) == uw_outcome(o["score"])
        assert uw["outcome"] != "decline"
        if uw["outcome"] == "bind":
            assert uw["conditions"] == []
        seen.add(uw["outcome"])
    assert seen == {"bind", "bind-with-terms", "refer"}


def test_js_round_semantics():
    assert [js_round(x) for x in (0.5, 1.5, 2.5, -0.5, -1.5, 2.4999)] == [1, 2, 3, 0, -1, 2]


def test_invalid_input_raises_typed_error():
    with pytest.raises(ContractError):
        score({"contract": "minogan.scorer/v2"})


def test_mesh_scorer_interface():
    s = MeshScorer()
    assert s.id == "mesh" and s.needs == () and s.score(FX[0]["input"]) == score(FX[0]["input"])


def test_no_socket_usage(monkeypatch):
    def _refuse(*a, **k):
        raise AssertionError("network access attempted by Mesh scorer")

    monkeypatch.setattr(socket, "socket", _refuse)
    monkeypatch.setattr(socket, "create_connection", _refuse)
    monkeypatch.setattr(socket, "getaddrinfo", _refuse)
    for f in FX:
        score(f["input"])


def test_scorer_imports_no_network_clock_or_randomness():
    tree = ast.parse(SCORER_SRC.read_text(encoding="utf-8"))
    mods = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            mods |= {a.name.split(".")[0] for a in node.names}
        elif isinstance(node, ast.ImportFrom) and node.module:
            mods.add(node.module.split(".")[0])
    forbidden = {"socket", "urllib", "http", "requests", "httpx", "random", "time", "datetime", "secrets", "uuid"}
    assert not (mods & forbidden), mods & forbidden
    assert mods <= {"__future__", "math", "typing", "neural_mesh"}
