"""CP-0085 Phase R4 — Streaming DEFER / OUT_OF_SCOPE_FOR_F4 tests (LIVE default False)."""

from __future__ import annotations

from pathlib import Path

from neural_mesh.packaging.l_judge_full_adapter_r4_streaming_defer import (
    DESIGN_CP_ID,
    IMPL_CP_ID,
    LIVE_API_ENABLED,
    PHASE,
    PRODUCT_CODEC_MODE,
    STREAMING_ALLOWED,
    STREAMING_F4_SCOPE,
    STREAMING_POSTURE,
    STREAMING_SHIPPED,
    assert_module_live_false,
    assert_unary_only_product_path,
    evaluate_streaming_defer_policy,
    impl_cp_authorization_record,
    r4_defer_rows,
    run_r4_defer_suite,
)
from neural_mesh.packaging.l_judge_gemini_free_canary_impl import LIVE_API_ENABLED as CANARY_LIVE
from neural_mesh.packaging.l_judge_live_http_transport import LIVE_API_ENABLED as LHT_LIVE

REPO = Path(__file__).resolve().parents[1]
IMPL_DOC = REPO / "docs" / "planning" / "IMPL_CP_0085_STREAMING_DEFER_SEAL.md"
POLICY_DOC = REPO / "docs" / "planning" / "MESH_FULL_ADAPTER_R4_STREAMING_DEFER_SEAL.md"
SCHEMA = REPO / "docs" / "schema" / "judge" / "full_adapter_r4_streaming_defer_v0.md"
EVIDENCE = REPO / "docs" / "planning" / "EVIDENCE_CP_0085_STREAMING_DEFER_SEAL.md"
F4_DRAFT = REPO / "docs" / "planning" / "F4_PRODUCT_ENABLE_ACK_DRAFT.md"


def test_module_live_false_constants():
    assert LIVE_API_ENABLED is False
    assert CANARY_LIVE is False
    assert LHT_LIVE is False
    assert_module_live_false()


def test_phase_and_defer_constants():
    assert PHASE == "R4"
    assert IMPL_CP_ID == "CP-0085"
    assert DESIGN_CP_ID == "CP-0081"
    assert STREAMING_POSTURE == "DEFERRED"
    assert STREAMING_F4_SCOPE == "OUT_OF_SCOPE_FOR_F4"
    assert STREAMING_ALLOWED is False
    assert STREAMING_SHIPPED is False
    assert PRODUCT_CODEC_MODE == "unary"


def test_auth_record_does_not_authorize_r5():
    auth = impl_cp_authorization_record()
    assert auth["authorized"] is True
    assert auth["phase"] == "R4"
    joined = " ".join(auth["does_not_authorize"])
    assert "R5" in joined
    assert "F4 invent" in joined
    assert "streaming codec" in joined.lower() or "streaming" in joined.lower()
    assert auth["r5_authorized"] is False
    assert auth["permanent_live_enable"] is False
    assert auth["streaming_posture"] == "DEFERRED"
    assert auth["streaming_f4_scope"] == "OUT_OF_SCOPE_FOR_F4"


def test_t_fa_r4_a_unary_product_path():
    unary = assert_unary_only_product_path()
    assert unary["mode"] == "unary"
    pol = evaluate_streaming_defer_policy()
    assert pol.product_codec_mode == "unary"


def test_t_fa_r4_b_out_of_f4():
    pol = evaluate_streaming_defer_policy()
    assert pol.streaming_f4_scope == "OUT_OF_SCOPE_FOR_F4"
    f4 = F4_DRAFT.read_text(encoding="utf-8")
    assert "Streaming" in f4
    assert "OUT" in f4


def test_t_fa_r4_c_flags_false():
    unary = assert_unary_only_product_path()
    assert unary["streaming_allowed"] is False
    assert unary["streaming_shipped"] is False
    pol = evaluate_streaming_defer_policy()
    assert pol.streaming_allowed is False
    assert pol.streaming_shipped is False


def test_t_fa_r4_d_t_lht_j_deferred():
    pol = evaluate_streaming_defer_policy()
    assert pol.t_lht_j_deferred is True
    assert pol.streaming_posture == "DEFERRED"
    assert pol.verdict == "STREAMING_DEFERRED_OUT_OF_F4"
    assert any("T-lht-j" in r for r in pol.reasons)


def test_t_fa_r4_e_suite_ok():
    suite = run_r4_defer_suite()
    assert suite["ok"] is True
    assert suite["LIVE_API_ENABLED_module_final"] is False
    assert suite["r5_authorized"] is False
    assert suite["streaming_posture"] == "DEFERRED"
    assert suite["streaming_f4_scope"] == "OUT_OF_SCOPE_FOR_F4"
    assert suite["verdict"] == "STREAMING_DEFERRED_OUT_OF_F4"
    assert suite["binding_final"] == "RefuseTransport"
    assert_module_live_false()


def test_policy_rows_and_docs_exist():
    rows = r4_defer_rows()
    assert len(rows) >= 5
    assert IMPL_DOC.is_file()
    assert POLICY_DOC.is_file()
    assert SCHEMA.is_file()
    assert EVIDENCE.is_file()
    impl = IMPL_DOC.read_text(encoding="utf-8")
    assert "LIVE_API_ENABLED" in impl
    assert "DEFER" in impl or "DEFERRED" in impl
    assert "R5" in impl
    assert "OUT_OF_SCOPE_FOR_F4" in impl
