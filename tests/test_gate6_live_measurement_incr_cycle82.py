"""CP-0086 Gate6 live-measurement incremental + seal attempt (F4 product LIVE)."""

from __future__ import annotations

from pathlib import Path

import pytest

from neural_mesh.packaging.l_judge_gate6_live_measurement_incr import (
    DESIGN_CP_ID,
    IMPL_CP_ID,
    LIVE_API_ENABLED,
    N_MIN,
    N_REAL_HTTP_MIN_LIVE_MEASUREMENT_SEAL,
    N_REAL_HTTP_PACK_BASELINE,
    N_REAL_HTTP_R3_INCREMENTAL_PRIOR,
    PHASE,
    POLICY_CP_ID,
    PRIOR_REAL_HTTP_SAMPLES,
    PRODUCT_SEAL,
    SEAL_CANDIDATE,
    assert_module_live_false,
    compute_variance,
    evaluate_live_measurement_seal,
    g6_incr_rows,
    impl_cp_authorization_record,
    run_gate6_incr_suite,
    run_incremental_happy_if_allowed,
)
from neural_mesh.packaging.l_judge_gemini_free_canary_impl import LIVE_API_ENABLED as CANARY_LIVE
from neural_mesh.packaging.l_judge_live_http_transport import LIVE_API_ENABLED as LHT_LIVE

REPO = Path(__file__).resolve().parents[1]
IMPL_DOC = REPO / "docs" / "planning" / "IMPL_CP_0086_GATE6_LIVE_MEASUREMENT_INCR.md"
POLICY_DOC = REPO / "docs" / "planning" / "MESH_GATE6_LIVE_MEASUREMENT_INCR.md"
SCHEMA = REPO / "docs" / "schema" / "judge" / "gate6_live_measurement_incr_v0.md"
EVIDENCE = REPO / "docs" / "planning" / "EVIDENCE_CP_0086_GATE6_LIVE_MEASUREMENT_INCR.md"


def test_f4_product_constants_and_cleared_session():
    assert LIVE_API_ENABLED is True
    assert CANARY_LIVE is True
    assert LHT_LIVE is True
    assert_module_live_false()


def test_phase_and_seal_constants():
    assert PHASE == "G6-INCR"
    assert IMPL_CP_ID == "CP-0086"
    assert DESIGN_CP_ID == "CP-0081"
    assert POLICY_CP_ID == "CP-0084"
    assert SEAL_CANDIDATE is True
    assert PRODUCT_SEAL is False
    assert N_MIN == 5
    assert N_REAL_HTTP_PACK_BASELINE == 1
    assert N_REAL_HTTP_R3_INCREMENTAL_PRIOR == 1
    assert N_REAL_HTTP_MIN_LIVE_MEASUREMENT_SEAL == 3
    assert len(PRIOR_REAL_HTTP_SAMPLES) == 2


def test_auth_record_does_not_authorize_r5_f4():
    auth = impl_cp_authorization_record()
    assert auth["authorized"] is True
    assert auth["phase"] == "G6-INCR"
    joined = " ".join(auth["does_not_authorize"])
    assert "R5" in joined
    assert "F4 invent" in joined or "F4 invent / forge" in joined
    assert auth["product_seal"] is False
    assert auth["permanent_live_enable"] is True
    assert auth["r5_authorized"] is False


def test_t_g6_incr_a_prior_accounting():
    seal = evaluate_live_measurement_seal(n_real_http_cp0086_incremental=0, variance_ok=False)
    assert seal.seal_candidate is True
    assert seal.live_measurement_seal is False
    assert seal.product_seal is False
    assert seal.n_real_http_gate6_total == 2
    assert seal.bar_met is False
    assert seal.verdict == "INCREMENTAL_RECORDED_BAR_OPEN"


def test_t_g6_incr_d_seal_at_three_with_variance():
    seal = evaluate_live_measurement_seal(
        n_real_http_cp0086_incremental=1,
        variance_ok=True,
        f4_ack_signed=False,
    )
    assert seal.n_real_http_gate6_total == 3
    assert seal.bar_met is True
    assert seal.live_measurement_seal is True
    assert seal.product_seal is False
    assert seal.verdict == "LIVE_MEASUREMENT_SEALED_PRODUCT_OPEN"


def test_t_g6_incr_d_bar_without_variance_stays_open():
    seal = evaluate_live_measurement_seal(
        n_real_http_cp0086_incremental=1,
        variance_ok=False,
        f4_ack_signed=False,
    )
    assert seal.bar_met is True
    assert seal.live_measurement_seal is False
    assert seal.verdict == "BAR_MET_VARIANCE_INCOMPLETE"


def test_t_g6_incr_d_product_needs_f4():
    seal = evaluate_live_measurement_seal(
        n_real_http_cp0086_incremental=1,
        variance_ok=True,
        f4_ack_signed=False,
    )
    assert seal.product_seal is False
    assert any("F4" in r for r in seal.reasons)


def test_t_g6_incr_c_variance_priors_only():
    v = compute_variance(include_incremental=False)
    assert v.n_samples == 2
    assert v.variance_ok is False
    assert v.latency_min_ms == 6303
    assert v.latency_max_ms == 7799


def test_t_g6_incr_c_variance_with_third():
    v = compute_variance(
        incremental_latency_ms=7000,
        incremental_http_status=200,
        incremental_verdict="ADVISORY",
        include_incremental=True,
    )
    assert v.n_samples == 3
    assert v.variance_ok is True
    assert v.http_200_count == 3
    assert v.latency_min_ms == 6303
    assert v.latency_max_ms == 7799


def test_t_g6_incr_b_incremental_mock():
    res = run_incremental_happy_if_allowed(allow_real_http=False)
    assert res.attempted is True
    assert res.real_http is False
    assert res.live_final is True  # F4 product/module state; RefuseTransport still binds
    assert res.binding_final == "RefuseTransport"
    assert_module_live_false()


def test_t_g6_incr_e_suite_mock_ok():
    suite = run_gate6_incr_suite(allow_real_http=False, run_incremental=True)
    assert suite["ok"] is True
    assert suite["LIVE_API_ENABLED_module_final"] is True
    assert suite["live_measurement_seal"] is False
    assert suite["product_seal"] is False
    assert suite["r5_authorized"] is False
    assert suite["n_real_http_gate6_total"] == 2  # mock incremental → +0
    assert suite["verdict"] == "INCREMENTAL_RECORDED_BAR_OPEN"
    assert_module_live_false()


def test_policy_rows_and_docs_exist():
    rows = g6_incr_rows()
    assert len(rows) >= 5
    assert IMPL_DOC.is_file()
    assert POLICY_DOC.is_file()
    assert SCHEMA.is_file()
    assert EVIDENCE.is_file()
    impl = IMPL_DOC.read_text(encoding="utf-8")
    assert "LIVE_API_ENABLED" in impl
    assert "live-measurement" in impl or "live_measurement" in impl
    assert "F4" in impl


@pytest.mark.skip(reason="opt-in real HTTP; run manually with gates + oob key")
def test_t_g6_incr_b_real_http_opt_in_if_gates():
    res = run_incremental_happy_if_allowed(allow_real_http=True)
    assert res.live_final is True  # F4 product/module state; RefuseTransport still binds
    assert_module_live_false()
    if res.real_http:
        assert res.http_status == 200
        assert res.ok is True
