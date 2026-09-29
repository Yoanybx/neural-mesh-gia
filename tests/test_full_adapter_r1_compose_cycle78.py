"""Tests for Cycle 78 / CP-0082: Phase R1 full-adapter SoT+Refuse+I5 compose.

Markers: full_adapter_r1_compose_cycle78
Default pytest: mock-only; module LIVE stays False; no network; no R2–R5.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

from neural_mesh import __version__
from neural_mesh.packaging.l_judge_gemini_free_canary_impl import (
    runtime_live_api_enabled,
    set_runtime_live_api_enabled,
)
from neural_mesh.packaging.l_judge_full_adapter_r1_compose import (
    CYCLE,
    DESCRIPTOR_IDS,
    DESIGN_CP_ID,
    IMPL_CP_ID,
    LIVE_API_ENABLED,
    PACKAGE_HELD,
    PHASE,
    PRIOR_CP,
    SEAL_CP,
    SOT_BOUNDARIES,
    compose_advisory_not_sot,
    compose_i5_kill,
    compose_refuse_when_live_off,
    impl_cp_authorization_record,
    is_impl_cp_authorized,
    r1_checklist_rows,
    run_r1_compose_suite,
)

pytestmark = [pytest.mark.full_adapter_r1_compose_cycle78]

REPO = Path(__file__).resolve().parents[1]
CHECKLIST = (
    REPO / "docs" / "planning" / "MESH_FULL_ADAPTER_R1_SOT_REFUSE_I5_COMPOSE_CHECKLIST.md"
)
IMPL_DOC = REPO / "docs" / "planning" / "IMPL_CP_0082_FULL_ADAPTER_R1_COMPOSE.md"
SCHEMA = REPO / "docs" / "schema" / "judge" / "full_adapter_r1_compose_v0.md"
DESIGN_R1 = REPO / "docs" / "planning" / "MESH_FULL_ADAPTER_LIVE_RV_DESIGN.md"
PKG = REPO / "src" / "neural_mesh" / "packaging" / "l_judge_full_adapter_r1_compose.py"


def setup_function(_fn=None):
    set_runtime_live_api_enabled(False)


def teardown_function(_fn=None):
    set_runtime_live_api_enabled(False)


def test_constants_and_authorization():
    assert __version__ == "0.18.0"
    assert PACKAGE_HELD == "0.18.0"
    assert SEAL_CP == IMPL_CP_ID == "CP-0082"
    assert PRIOR_CP == DESIGN_CP_ID == "CP-0081"
    assert CYCLE == 78
    assert PHASE == "R1"
    assert LIVE_API_ENABLED is True
    assert is_impl_cp_authorized() is True
    auth = impl_cp_authorization_record()
    assert auth["authorized"] is True
    assert auth["phase"] == "R1"
    assert auth["permanent_live_enable"] is True
    assert "R2 multi-judge live/mock-bound RV" in auth["does_not_authorize"]
    assert "R5 F4 product ACK / permanent module True" in auth["does_not_authorize"]
    assert set(DESCRIPTOR_IDS) == {
        "T-fa-r1-a",
        "T-fa-r1-b",
        "T-fa-r1-c",
        "T-fa-r1-d",
        "T-fa-r1-e",
    }
    assert len(SOT_BOUNDARIES) >= 4


def test_checklist_rows_cover_sot_refuse_i5():
    rows = r1_checklist_rows()
    ids = {r["id"] for r in rows}
    assert {"SOT-1", "SOT-2", "SOT-3", "REF-1", "REF-2", "I5-1", "I5-2"} <= ids
    topics = " ".join(r["topic"] for r in rows)
    assert "SoT" in topics or "Mesh SoT" in topics
    assert "Refuse" in topics
    assert "Kill" in topics or "I5" in topics


def test_t_fa_r1_a_refuse_when_live_off():
    """T-fa-r1-a: refuse when live off on full-adapter compose surface."""
    res = compose_refuse_when_live_off()
    assert res.ok, res.notes
    assert res.descriptor == "T-fa-r1-a"
    assert res.network_calls == 0
    assert res.mesh_accept is False
    assert res.binding == "RefuseTransport"
    assert res.result["error_code"] == "ENGINE_DISABLED"
    assert runtime_live_api_enabled() is True  # module F4 True; I5 still gates
    assert LIVE_API_ENABLED is True


def test_t_fa_r1_b_i5_kill_compose():
    """T-fa-r1-b: I5 kill compose → ABORT + Refuse; zero post-kill network."""
    res = compose_i5_kill()
    assert res.ok, res.notes
    assert res.descriptor == "T-fa-r1-b"
    assert res.network_calls == 0
    assert res.mesh_accept is False
    assert res.result["verdict"] == "ABORT"
    assert res.result["error_code"] in ("ENGINE_DISABLED", "HUMAN_ABORT")
    assert runtime_live_api_enabled() is True  # module F4 True; I5 still gates


def test_t_fa_r1_c_advisory_not_sot_mesh_accept_false():
    """T-fa-r1-c: advisory ≠ SoT; mesh_accept stays false on happy mock."""
    res = compose_advisory_not_sot()
    assert res.ok, res.notes
    assert res.descriptor == "T-fa-r1-c"
    assert res.mesh_accept is False
    assert res.result["advisory_only"] is True
    assert res.result["verdict"] == "ADVISORY"
    assert res.result["mesh_accept"] is False
    assert runtime_live_api_enabled() is True  # module F4 True; I5 still gates


def test_run_r1_compose_suite_all_pass():
    suite = run_r1_compose_suite()
    assert suite["ok"] is True
    assert suite["phase"] == "R1"
    assert suite["impl_cp"] == "CP-0082"
    assert suite["r2_r5_authorized"] is False
    assert suite["LIVE_API_ENABLED_module_final"] is True
    assert suite["runtime_live_api_enabled_final"] is False
    ids = {d["descriptor"] for d in suite["descriptors"]}
    assert ids == set(DESCRIPTOR_IDS)
    for d in suite["descriptors"]:
        assert d["ok"] is True, d
        assert d["mesh_accept"] is False
    blob = json.dumps(suite)
    assert "AIza" not in blob
    assert "sk-" not in blob


def test_docs_and_no_secrets():
    assert CHECKLIST.is_file()
    assert IMPL_DOC.is_file()
    assert SCHEMA.is_file()
    assert PKG.is_file()
    assert DESIGN_R1.is_file()
    for path in (CHECKLIST, IMPL_DOC, SCHEMA, PKG):
        body = path.read_text(encoding="utf-8")
        assert not re.search(r"sk-[A-Za-z0-9]{10,}", body), path.name
        assert "AIza" not in body
    impl = IMPL_DOC.read_text(encoding="utf-8")
    assert "CP-0082" in impl
    assert "R1" in impl
    assert "does NOT authorize R2" in impl or "does_not_authorize" in impl or "R2–R5" in impl
    assert "LIVE_API_ENABLED" in impl
    check = CHECKLIST.read_text(encoding="utf-8")
    assert "SoT" in check
    assert "RefuseTransport" in check
    assert "I5" in check
    assert "T-fa-r1-a" in check
    schema = SCHEMA.read_text(encoding="utf-8")
    for did in DESCRIPTOR_IDS:
        assert did in schema
