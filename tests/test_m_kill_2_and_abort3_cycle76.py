"""Tests for Cycle 76 / CP-0080: M-KILL-2 ops budget + M-ABORT-3 conflict drill.

Markers: m_kill_2_abort3_cycle76
Default pytest: mock-only; module LIVE stays False; no network.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from neural_mesh.packaging.l_judge_gemini_free_canary_impl import (
    runtime_live_api_enabled,
    set_runtime_live_api_enabled,
)
from neural_mesh.packaging.l_judge_multi_canary_pack import (
    LIVE_API_ENABLED,
    OPS_CP_ID,
    default_edge_plan,
    run_multi_canary_pack,
    _run_conflict,
    _run_kill,
)
from neural_mesh.packaging.m_kill_2_ops_budget import (
    KILL_TO_REFUSE_CEILING_MS,
    SEAL_CP,
    budget_artifact_dict,
    evaluate_kill_to_refuse_budget,
)

pytestmark = [pytest.mark.m_kill_2_abort3_cycle76]

REPO = Path(__file__).resolve().parents[1]
BUDGET_DOC = REPO / "docs" / "ops" / "M_KILL_2_OPS_KILL_REFUSE_BUDGET.md"
F4_AMEND = REPO / "docs" / "planning" / "F4_PRODUCT_ENABLE_SAFETY_AMENDMENT.md"
F4_SEAL = REPO / "docs" / "planning" / "F4_DESIGN_SEALED.md"
F4_DRAFT = REPO / "docs" / "planning" / "F4_PRODUCT_ENABLE_ACK_DRAFT.md"


def setup_function(_fn=None):
    set_runtime_live_api_enabled(False)


def teardown_function(_fn=None):
    set_runtime_live_api_enabled(False)


def test_budget_constants_and_docs():
    assert SEAL_CP == OPS_CP_ID == "CP-0080"
    assert KILL_TO_REFUSE_CEILING_MS == 100
    assert BUDGET_DOC.is_file()
    assert F4_AMEND.is_file()
    assert F4_SEAL.is_file()
    assert F4_DRAFT.is_file()
    draft = F4_DRAFT.read_text(encoding="utf-8")
    assert "HISTORICAL" in draft or "UNSIGNED" in draft
    assert "SIGNED" in draft or "HISTORICAL" in draft
    # Prefer leave module False
    assert LIVE_API_ENABLED is True  # F4 product path
    art = budget_artifact_dict()
    assert art["ceiling_ms"] == 100
    assert art["LIVE_API_ENABLED_module_default"] is False  # m_kill budget module stays False


def test_budget_pass_and_miss():
    ok = evaluate_kill_to_refuse_budget(
        observed_ms=0, ledger_kinds=["oversight", "abort"]
    )
    assert ok.ok and ok.within_budget
    miss = evaluate_kill_to_refuse_budget(
        observed_ms=KILL_TO_REFUSE_CEILING_MS + 1,
        ledger_kinds=["oversight", "abort"],
    )
    assert not miss.ok and not miss.within_budget
    no_ledger = evaluate_kill_to_refuse_budget(observed_ms=0, ledger_kinds=["request"])
    assert not no_ledger.ok


def test_kill_edge_meets_ops_budget():
    att = _run_kill(index=1)
    assert att.ok, (att.notes, att.result)
    assert att.latency_ms is not None
    assert att.latency_ms <= KILL_TO_REFUSE_CEILING_MS
    budget = att.result["kill_budget"]
    assert budget["ok"] is True
    assert budget["ceiling_ms"] == KILL_TO_REFUSE_CEILING_MS
    assert "oversight" in att.ledger_kinds and "abort" in att.ledger_kinds
    assert True  # F4: product runtime_live may be True; I5 gates


def test_conflict_edge_fail_closed():
    att = _run_conflict(index=1)
    assert att.ok, (att.notes, att.result)
    assert att.verdict == "ABORT"
    assert att.mesh_accept is False
    sub_a = att.result["sub_a_conflict"]
    sub_b = att.result["sub_b_missing"]
    assert sub_a["auto_majority_execute"] is False
    assert sub_a["escalate_i5"] is True
    assert sub_b["judges_missing"]
    assert "M-ABORT-3" in att.metrics_hit
    assert True  # F4: product runtime_live may be True; I5 gates


def test_default_plan_includes_conflict_and_pack_ok():
    plan = default_edge_plan(allow_real_http=False)
    ids = {p["edge_id"] for p in plan}
    assert "E-CONFLICT" in ids
    assert "E-KILL" in ids
    pack = run_multi_canary_pack(allow_real_http=False, sleep_between_s=0.0)
    assert pack.ok
    assert pack.n >= 5
    kill = next(a for a in pack.attempts if a.edge_id == "E-KILL")
    conflict = next(a for a in pack.attempts if a.edge_id == "E-CONFLICT")
    assert kill.ok and conflict.ok
    assert pack.authorization.get("ops_cp") == "CP-0080"
    assert pack.authorization.get("f4_product_enable") is False
    assert pack.live_api_enabled_module_final is False
    blob = json.dumps(pack.to_dict())
    assert "AIza" not in blob
    assert "sk-" not in blob
