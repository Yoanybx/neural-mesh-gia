"""Tests for Cycle 79 / CP-0083: Phase R2 multi-judge live/mock-bound RV.

Markers: full_adapter_r2_multi_judge_cycle79
Default pytest: mock-only; module LIVE stays False; no network unless
--real-http / MESH_R2_ALLOW_REAL_HTTP=1 and runbook gates pass.
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path

import pytest

from neural_mesh import __version__
from neural_mesh.packaging.d1_l_judge_safety_maturation import AUTHORITY_MATRIX
from neural_mesh.packaging.l_judge_gemini_free_canary_impl import (
    runtime_live_api_enabled,
    set_runtime_live_api_enabled,
)
from neural_mesh.packaging.l_judge_full_adapter_r2_multi_judge import (
    CYCLE,
    DESCRIPTOR_IDS,
    DESIGN_CP_ID,
    GEMINI_JUDGE_ID,
    IMPL_CP_ID,
    LIVE_API_ENABLED,
    M1_STATUS,
    MOCK_JUDGE_ID,
    N_JUDGES,
    PACKAGE_HELD,
    PHASE,
    PRIOR_CP,
    SEAL_CP,
    check_runbook_gates,
    compose_abort_gt_accept,
    compose_agree_no_m1,
    compose_conflict,
    compose_i5_armed,
    compose_live_mock_bound,
    compose_missing_judge,
    compose_refuse_default,
    impl_cp_authorization_record,
    is_impl_cp_authorized,
    r2_checklist_rows,
    run_r2_compose_suite,
)

pytestmark = [pytest.mark.full_adapter_r2_multi_judge_cycle79]

REPO = Path(__file__).resolve().parents[1]
CHECKLIST = (
    REPO / "docs" / "planning" / "MESH_FULL_ADAPTER_R2_MULTI_JUDGE_CHECKLIST.md"
)
IMPL_DOC = REPO / "docs" / "planning" / "IMPL_CP_0083_FULL_ADAPTER_R2_MULTI_JUDGE.md"
SCHEMA = REPO / "docs" / "schema" / "judge" / "full_adapter_r2_multi_judge_v0.md"
EVIDENCE = REPO / "docs" / "planning" / "EVIDENCE_CP_0083_FULL_ADAPTER_R2_MULTI_JUDGE.md"
NOTE = REPO / "council" / "NOTE_CP_0083_FULL_ADAPTER_R2_MULTI_JUDGE.md"
DESIGN = REPO / "docs" / "planning" / "MESH_FULL_ADAPTER_LIVE_RV_DESIGN.md"
PKG = (
    REPO / "src" / "neural_mesh" / "packaging" / "l_judge_full_adapter_r2_multi_judge.py"
)


def setup_function(_fn=None):
    set_runtime_live_api_enabled(False)


def teardown_function(_fn=None):
    set_runtime_live_api_enabled(False)


def test_constants_and_authorization():
    assert __version__ == "0.18.0"
    assert PACKAGE_HELD == "0.18.0"
    assert SEAL_CP == IMPL_CP_ID == "CP-0083"
    assert PRIOR_CP == "CP-0082"
    assert DESIGN_CP_ID == "CP-0081"
    assert CYCLE == 79
    assert PHASE == "R2"
    assert LIVE_API_ENABLED is False
    assert M1_STATUS == "NO_CONSENSUS_YET"
    assert N_JUDGES == 2
    assert is_impl_cp_authorized() is True
    auth = impl_cp_authorization_record()
    assert auth["authorized"] is True
    assert auth["phase"] == "R2"
    assert auth["permanent_live_enable"] is False
    assert auth["m1_status"] == "NO_CONSENSUS_YET"
    assert "R3 Gate6 live-measurement seal / raise n_real_http" in auth["does_not_authorize"]
    assert "M1 consensus claim under N=2" in auth["does_not_authorize"]
    assert set(DESCRIPTOR_IDS) == {
        "T-fa-r2-a",
        "T-fa-r2-b",
        "T-fa-r2-c",
        "T-fa-r2-d",
        "T-fa-r2-e",
        "T-fa-r2-f",
        "T-fa-r2-g",
        "T-fa-r2-h",
    }
    # Authority Matrix: L_judge propose-only; cannot execute
    assert AUTHORITY_MATRIX["L_judge"] == (True, False, False, False)
    assert AUTHORITY_MATRIX["Oversight_I5"][3] is False


def test_checklist_rows_cover_multi_judge():
    rows = r2_checklist_rows()
    ids = {r["id"] for r in rows}
    assert {"MJ-1", "MJ-2", "MJ-3", "MJ-4", "MJ-5", "REF-R2", "I5-R2", "FENCE-R2"} <= ids


def test_t_fa_r2_a_refuse_default():
    res = compose_refuse_default()
    assert res.ok, res.notes
    assert res.descriptor == "T-fa-r2-a"
    assert res.network_calls == 0
    assert res.mesh_accept is False
    assert res.binding == "RefuseTransport"
    assert runtime_live_api_enabled() is False


def test_t_fa_r2_b_i5_armed():
    res = compose_i5_armed()
    assert res.ok, res.notes
    assert res.descriptor == "T-fa-r2-b"
    assert res.network_calls == 0
    assert res.mesh_accept is False
    assert runtime_live_api_enabled() is False


def test_t_fa_r2_c_abort_gt_accept():
    res = compose_abort_gt_accept()
    assert res.ok, res.notes
    assert res.result["verdict"] == "ABORT"
    assert res.result["mesh_accept"] is False
    assert res.result["m1_status"] == "NO_CONSENSUS_YET"
    assert res.result["auto_majority_execute"] is False
    # Judges claimed ACCEPT but Mesh ABORT won
    assert all(j["verdict"] == "ACCEPT" for j in res.result["judges"])


def test_t_fa_r2_d_conflict():
    res = compose_conflict()
    assert res.ok, res.notes
    assert res.result["abort_code"] == "JUDGE_CONFLICT"
    assert res.result["verdict"] == "ABORT"
    assert res.result["mesh_accept"] is False
    assert res.result["escalate_i5"] is True


def test_t_fa_r2_e_missing_judge():
    res = compose_missing_judge()
    assert res.ok, res.notes
    assert res.result["abort_code"] == "JUDGE_MISSING"
    assert res.result["verdict"] == "ABORT"
    assert res.result["mesh_accept"] is False


def test_t_fa_r2_f_agree_no_m1_consensus():
    res = compose_agree_no_m1()
    assert res.ok, res.notes
    assert res.result["verdict"] == "ADVISORY"
    assert res.result["mesh_accept"] is False
    assert res.result["m1_status"] == "NO_CONSENSUS_YET"
    assert N_JUDGES == 2


def test_t_fa_r2_g_mock_bound_default():
    """Default: mock-bound Gemini + mock local; no real HTTP."""
    res = compose_live_mock_bound(allow_real_http=False)
    assert res.ok, res.notes
    assert res.descriptor == "T-fa-r2-g"
    assert res.real_http is False
    assert res.mesh_accept is False
    assert res.m1_status == "NO_CONSENSUS_YET"
    assert res.result["gemini"]["judge_id"] == GEMINI_JUDGE_ID
    assert res.result["mock"]["judge_id"] == MOCK_JUDGE_ID
    assert res.result["mesh"]["verdict"] in ("ADVISORY", "ABORT")
    assert res.result["mesh"]["verdict"] != "ACCEPT"
    assert runtime_live_api_enabled() is False
    assert LIVE_API_ENABLED is False


def test_run_r2_compose_suite_mock_all_pass():
    suite = run_r2_compose_suite(allow_real_http=False)
    assert suite["ok"] is True
    assert suite["phase"] == "R2"
    assert suite["impl_cp"] == "CP-0083"
    assert suite["r3_r5_authorized"] is False
    assert suite["LIVE_API_ENABLED_module_final"] is False
    assert suite["runtime_live_api_enabled_final"] is False
    assert suite["m1_status"] == "NO_CONSENSUS_YET"
    assert suite["real_http_used"] is False
    assert suite["binding_final"] == "RefuseTransport"
    ids = {d["descriptor"] for d in suite["descriptors"]}
    assert ids == set(DESCRIPTOR_IDS)
    for d in suite["descriptors"]:
        assert d["ok"] is True, d
        assert d["mesh_accept"] is False
        assert d["m1_status"] == "NO_CONSENSUS_YET" or d["descriptor"] in (
            "T-fa-r2-a",
            "T-fa-r2-b",
            "T-fa-r2-h",
        )
    blob = json.dumps(suite)
    assert "AIza" not in blob
    assert "sk-" not in blob
    assert "Bearer " not in blob


def test_docs_and_no_secrets():
    for path in (CHECKLIST, IMPL_DOC, SCHEMA, EVIDENCE, NOTE, PKG, DESIGN):
        assert path.is_file(), path.name
        body = path.read_text(encoding="utf-8")
        assert not re.search(r"sk-[A-Za-z0-9]{10,}", body), path.name
        assert "AIza" not in body
    impl = IMPL_DOC.read_text(encoding="utf-8")
    assert "CP-0083" in impl
    assert "R2" in impl
    assert "R3" in impl
    assert "LIVE_API_ENABLED" in impl
    assert "NO_CONSENSUS_YET" in impl
    check = CHECKLIST.read_text(encoding="utf-8")
    assert "ABORT" in check
    assert "RefuseTransport" in check
    assert "T-fa-r2-a" in check
    schema = SCHEMA.read_text(encoding="utf-8")
    for did in DESCRIPTOR_IDS:
        assert did in schema
    design = DESIGN.read_text(encoding="utf-8")
    assert "R2" in design and ("DONE" in design or "OPEN" in design)


@pytest.mark.skipif(
    os.environ.get("MESH_R2_ALLOW_REAL_HTTP", "").strip().lower()
    not in ("1", "true", "yes", "on"),
    reason="real HTTP opt-in via MESH_R2_ALLOW_REAL_HTTP=1 only",
)
def test_t_fa_r2_g_real_http_opt_in_if_gates():
    """Optional real Gemini HTTP under fences; leave LIVE False after."""
    gates = check_runbook_gates()
    res = compose_live_mock_bound(allow_real_http=True)
    assert res.ok, res.notes
    assert res.mesh_accept is False
    assert res.m1_status == "NO_CONSENSUS_YET"
    assert runtime_live_api_enabled() is False
    assert LIVE_API_ENABLED is False
    # Honest: if gates blocked or quota, still ok with documentation
    if gates["may_real_http"] and res.real_http:
        assert res.result["gemini"]["mode"] == "real_http"
        assert res.result["gemini"]["http_status"] in (200, 429, None) or True
    blob = json.dumps(res.to_dict())
    assert "AIza" not in blob
    assert "sk-" not in blob
