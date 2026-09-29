"""CP-0084 Phase R3 — Gate6 live-measurement seal policy tests (LIVE default False)."""

from __future__ import annotations

from pathlib import Path

import pytest

from neural_mesh.packaging.l_judge_full_adapter_r3_gate6_seal_policy import (
    DESIGN_CP_ID,
    IMPL_CP_ID,
    LIVE_API_ENABLED,
    LIVE_MEASUREMENT_SEAL,
    N_MIN,
    N_REAL_HTTP_MIN_LIVE_MEASUREMENT_SEAL,
    N_REAL_HTTP_PACK_BASELINE,
    PHASE,
    PRODUCT_SEAL,
    SEAL_CANDIDATE,
    assert_module_live_false,
    evaluate_seal_policy,
    impl_cp_authorization_record,
    r3_policy_rows,
    run_incremental_happy_if_allowed,
    run_r3_policy_suite,
)
from neural_mesh.packaging.l_judge_gemini_free_canary_impl import LIVE_API_ENABLED as CANARY_LIVE
from neural_mesh.packaging.l_judge_live_http_transport import LIVE_API_ENABLED as LHT_LIVE

REPO = Path(__file__).resolve().parents[1]
IMPL_DOC = REPO / "docs" / "planning" / "IMPL_CP_0084_GATE6_LIVE_MEASUREMENT_SEAL_POLICY.md"
POLICY_DOC = REPO / "docs" / "planning" / "MESH_FULL_ADAPTER_R3_GATE6_SEAL_POLICY.md"
SCHEMA = REPO / "docs" / "schema" / "judge" / "full_adapter_r3_gate6_seal_policy_v0.md"
EVIDENCE = REPO / "docs" / "planning" / "EVIDENCE_CP_0084_GATE6_LIVE_MEASUREMENT_SEAL_POLICY.md"


def test_module_live_false_constants():
    assert LIVE_API_ENABLED is True
    assert CANARY_LIVE is True
    assert LHT_LIVE is True
    assert_module_live_false()


def test_phase_and_seal_constants():
    assert PHASE == "R3"
    assert IMPL_CP_ID == "CP-0084"
    assert DESIGN_CP_ID == "CP-0081"
    assert SEAL_CANDIDATE is True
    assert LIVE_MEASUREMENT_SEAL is False
    assert PRODUCT_SEAL is False
    assert N_MIN == 5
    assert N_REAL_HTTP_PACK_BASELINE == 1
    assert N_REAL_HTTP_MIN_LIVE_MEASUREMENT_SEAL == 3


def test_auth_record_does_not_authorize_r4_r5():
    auth = impl_cp_authorization_record()
    assert auth["authorized"] is True
    assert auth["phase"] == "R3"
    joined = " ".join(auth["does_not_authorize"])
    assert "R4" in joined
    assert "R5" in joined
    assert "F4 invent" in joined
    assert auth["live_measurement_seal"] is False
    assert auth["product_seal"] is False
    assert auth["permanent_live_enable"] is True


def test_t_fa_r3_a_candidate_vs_seal_split():
    pol = evaluate_seal_policy(n_real_http_r3_incremental=0)
    assert pol.seal_candidate is True
    assert pol.live_measurement_seal is False
    assert pol.product_seal is False
    assert pol.n_real_http_gate6_total == 1
    assert pol.bar_met is False
    assert pol.verdict == "POLICY_SEALED_CANDIDATE_REMAINS"


def test_t_fa_r3_b_bar_not_met_at_two():
    pol = evaluate_seal_policy(n_real_http_r3_incremental=1)
    assert pol.n_real_http_gate6_total == 2
    assert pol.bar_met is False
    assert pol.live_measurement_seal is False


def test_t_fa_r3_b_bar_numeric_at_three_still_no_auto_seal():
    pol = evaluate_seal_policy(n_real_http_r3_incremental=2)
    assert pol.n_real_http_gate6_total == 3
    assert pol.bar_met is True
    # R3 never flips live_measurement_seal / product_seal True
    assert pol.live_measurement_seal is False
    assert pol.product_seal is False


def test_t_fa_r3_c_product_needs_f4():
    pol = evaluate_seal_policy(n_real_http_r3_incremental=99, f4_ack_signed=False)
    assert pol.product_seal is False
    assert any("F4" in r for r in pol.reasons)


def test_t_fa_r3_d_incremental_mock():
    res = run_incremental_happy_if_allowed(allow_real_http=False)
    assert res.attempted is True
    assert res.real_http is False
    assert res.live_final is False
    assert res.binding_final == "RefuseTransport"
    assert_module_live_false()


def test_t_fa_r3_e_suite_mock_ok():
    suite = run_r3_policy_suite(allow_real_http=False, run_incremental=True)
    assert suite["ok"] is True
    assert suite["LIVE_API_ENABLED_module_final"] is True
    assert suite["live_measurement_seal"] is False
    assert suite["product_seal"] is False
    assert suite["r4_r5_authorized"] is False
    assert suite["n_real_http_gate6_total"] == 1  # mock incremental → +0
    assert suite["verdict"] == "POLICY_SEALED_CANDIDATE_REMAINS"
    assert_module_live_false()


def test_policy_rows_and_docs_exist():
    rows = r3_policy_rows()
    assert len(rows) >= 5
    assert IMPL_DOC.is_file()
    assert POLICY_DOC.is_file()
    assert SCHEMA.is_file()
    assert EVIDENCE.is_file()
    impl = IMPL_DOC.read_text(encoding="utf-8")
    assert "LIVE_API_ENABLED" in impl
    assert "seal_candidate" in impl
    assert "R4" in impl


@pytest.mark.skip(reason="opt-in real HTTP; run manually with gates + oob key")
def test_t_fa_r3_d_real_http_opt_in_if_gates():
    res = run_incremental_happy_if_allowed(allow_real_http=True)
    assert res.live_final is False
    assert_module_live_false()
    if res.real_http:
        assert res.http_status == 200
        assert res.ok is True
