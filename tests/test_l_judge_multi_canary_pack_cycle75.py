"""Tests for Cycle 75 / CP-0079: multi-canary pack (n≥5) under fences.

Markers: l_judge_multi_canary_pack_cycle75
Default pytest: mock-only pack (no live network). Module LIVE stays False.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from neural_mesh import __version__
from neural_mesh.packaging.l_judge_gemini_free_canary_impl import (
    runtime_live_api_enabled,
    set_runtime_live_api_enabled,
)
from neural_mesh.packaging.l_judge_live_http_transport import (
    LIVE_API_ENABLED as LHT_LIVE,
)
from neural_mesh.packaging.l_judge_multi_canary_pack import (
    CYCLE,
    DESIGN_CP_ID,
    IMPL_CP_ID,
    LIVE_API_ENABLED,
    N_MIN,
    PACKAGE_HELD,
    PRIOR_CP,
    SEAL_CP,
    default_edge_plan,
    run_multi_canary_pack,
)

pytestmark = [pytest.mark.l_judge_multi_canary_pack_cycle75]

REPO = Path(__file__).resolve().parents[1]
POLICY = REPO / "docs" / "planning" / "LIVE_API_PERMANENT_ENABLE_POLICY.md"
IMPL = REPO / "docs" / "planning" / "IMPL_CP_0079_MULTI_CANARY_PACK.md"
PKG = REPO / "src" / "neural_mesh" / "packaging" / "l_judge_multi_canary_pack.py"


def setup_function(_fn=None):
    set_runtime_live_api_enabled(False)


def teardown_function(_fn=None):
    set_runtime_live_api_enabled(False)


def test_constants_and_docs():
    assert __version__ == "0.18.0"
    assert PACKAGE_HELD == "0.18.0"
    assert SEAL_CP == IMPL_CP_ID == "CP-0079"
    assert PRIOR_CP == "CP-0078"
    assert DESIGN_CP_ID == "CP-0077"
    assert CYCLE == 75
    assert N_MIN == 5
    assert LIVE_API_ENABLED is False
    assert LHT_LIVE is False
    assert POLICY.is_file()
    assert IMPL.is_file()
    assert PKG.is_file()
    body = POLICY.read_text(encoding="utf-8")
    assert "must return" in body.lower() or "must** return" in body.lower() or "Must return" in body or "must return / remain False" in body
    assert "F4" in body


def test_default_plan_covers_edges():
    plan = default_edge_plan(allow_real_http=False)
    assert len(plan) >= N_MIN
    ids = {p["edge_id"] for p in plan}
    assert "E-KILL" in ids
    assert "E-ABORT-ACCEPT" in ids
    assert "E-HAPPY" in ids


def test_mock_pack_reaches_n_min_and_restores_live_false():
    pack = run_multi_canary_pack(allow_real_http=False, sleep_between_s=0.0)
    assert pack.n >= N_MIN
    assert pack.n_kill_live >= 1
    assert pack.n_abort >= 1
    assert pack.n_ledger_kill >= 1
    assert pack.n_edge >= 3
    assert runtime_live_api_enabled() is False
    assert pack.live_api_enabled_module_final is False
    assert pack.binding_final == "RefuseTransport"
    assert LIVE_API_ENABLED is False
    # All edge attempts (non-happy) should ok under mock
    for a in pack.attempts:
        assert a.live_final is False
        if a.edge_id != "E-HAPPY":
            assert a.ok, (a.edge_id, a.notes, a.result)
    # Happy mock should also ok
    happy = [a for a in pack.attempts if a.edge_id == "E-HAPPY"]
    assert happy and happy[0].ok
    assert pack.ok is True
    d = pack.to_dict()
    assert d["mesh_accept"] is False
    assert "sample" in d["claim_hygiene"]
    # JSON round-trip hygiene — no raw key material
    blob = json.dumps(d)
    assert "AIza" not in blob
    assert "sk-" not in blob


def test_kill_edge_records_oversight_abort_ledger_kinds():
    pack = run_multi_canary_pack(allow_real_http=False, sleep_between_s=0.0)
    kill = next(a for a in pack.attempts if a.edge_id == "E-KILL")
    assert "oversight" in kill.ledger_kinds
    assert "abort" in kill.ledger_kinds
    assert kill.i5_killed is True
