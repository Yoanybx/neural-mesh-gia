"""Tests for Cycle 71 / CP-0075: Gemini free Gate5 canary impl (authorized).

Markers: l_judge_gemini_free_canary_impl_cycle71
No live network in default pytest; skip_network canary path + refuse paths.
Keys never asserted; NO_HELD unchanged.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

from neural_mesh import __version__
from neural_mesh.packaging.l_judge_gemini_free_canary_impl import (
    CANARY_MODEL,
    CANARY_OK_MARKER,
    CANARY_PROMPT,
    CANARY_SECRET_HANDLE,
    CYCLE,
    IMPL_CP_ID,
    LIVE_API_ENABLED,
    PACKAGE_HELD,
    PRIOR_CP,
    SEAL_CP,
    GeminiFreeCanaryTransport,
    arm_i5_for_canary,
    evaluate_canary_enablement,
    impl_cp_authorization_record,
    is_impl_cp_authorized,
    live_api_canary_session,
    run_gate5_canary_once,
    runtime_live_api_enabled,
    set_runtime_live_api_enabled,
)
from neural_mesh.packaging.l_judge_live_adapter_safety import (
    RefuseTransport,
    evaluate_enablement_gates,
)
from neural_mesh.packaging.google_l_judge_peer_spike import LIVE_API_ENABLED as PEER_LIVE

pytestmark = [pytest.mark.l_judge_gemini_free_canary_impl_cycle71]

REPO = Path(__file__).resolve().parents[1]
IMPL_DOC = REPO / "docs" / "planning" / "IMPL_CP_0075_GEMINI_FREE_CANARY.md"
ENABLE_ACK = REPO / "docs" / "planning" / "GATE1_ENABLE_UNDER_FENCES_ACK_SIGNED.md"
PKG = REPO / "src" / "neural_mesh" / "packaging" / "l_judge_gemini_free_canary_impl.py"


def setup_function(_fn=None):
    set_runtime_live_api_enabled(False)


def teardown_function(_fn=None):
    set_runtime_live_api_enabled(False)


def test_constants_and_authorization():
    assert __version__ == "0.18.0"
    assert PACKAGE_HELD == "0.18.0"
    assert SEAL_CP == "CP-0075" == IMPL_CP_ID
    assert PRIOR_CP == "CP-0074"
    assert CYCLE == 71
    assert LIVE_API_ENABLED is False
    assert PEER_LIVE is False
    assert is_impl_cp_authorized() is True
    assert CANARY_SECRET_HANDLE == "mesh://secrets/judge/gemini-free@v1"
    assert CANARY_MODEL == "gemini-flash-latest"
    auth = impl_cp_authorization_record()
    assert auth["authorized"] is True
    assert auth["full_live_http_codec_shipped"] is False
    assert auth["src_live_codec_shipped"] is False
    assert "gemini_free" in auth["scope"]


def test_nt10_default_still_fail_closed():
    res = evaluate_enablement_gates()
    assert res.may_enable is False
    assert "impl_cp_not_authorized" in res.reasons


def test_nt10_cleared_under_authorized_impl_cp():
    res = evaluate_canary_enablement()
    assert res.may_enable is True
    assert res.reasons == []
    # Explicit False still blocks
    blocked = evaluate_canary_enablement(impl_cp_authorized=False)
    assert blocked.may_enable is False
    assert "impl_cp_not_authorized" in blocked.reasons


def test_permanent_false_still_blocks():
    res = evaluate_canary_enablement(flags={"train_70b": True})
    assert res.may_enable is False
    assert any("train_70b" in r for r in res.reasons)


def test_canary_transport_refuses_without_runtime_live():
    i5 = arm_i5_for_canary()
    # Armed but runtime live still False → refuse
    t = GeminiFreeCanaryTransport(i5=i5)
    out = t.call({"prompt": CANARY_PROMPT})
    assert out["ok"] is False
    assert out["error_code"] == "ENGINE_DISABLED"
    assert out["verdict"] == "ABORT"
    assert runtime_live_api_enabled() is False
    health = t.health()
    assert health["live"] is False
    assert health["binding"] == "RefuseTransport"


def test_canary_transport_refuses_after_i5_kill():
    i5 = arm_i5_for_canary()
    with live_api_canary_session(i5=i5, enablement_ok=True):
        assert runtime_live_api_enabled() is True
        i5.kill("test_kill")
        t = GeminiFreeCanaryTransport(i5=i5)
        out = t.call({"prompt": CANARY_PROMPT})
        assert out["error_code"] == "ENGINE_DISABLED"
    assert runtime_live_api_enabled() is False


def test_live_api_session_restores_false():
    i5 = arm_i5_for_canary()
    with live_api_canary_session(i5=i5, enablement_ok=True):
        assert runtime_live_api_enabled() is True
    assert runtime_live_api_enabled() is False
    assert LIVE_API_ENABLED is False


def test_run_gate5_canary_skip_network():
    ledger = run_gate5_canary_once(skip_network=True, request_id="test-canary-1")
    assert ledger.may_enable is True
    assert ledger.i5_armed is True
    assert ledger.ok is True
    assert ledger.ok_marker is True
    assert ledger.verdict == "ADVISORY"
    assert ledger.live_api_enabled_during is True
    assert ledger.live_api_enabled_final is False
    assert ledger.binding_final == "RefuseTransport"
    assert runtime_live_api_enabled() is False
    d = ledger.to_dict()
    assert d["mesh_accept"] is False
    assert d["advisory_only"] is True
    assert d["src_live_codec_shipped"] is False
    assert CANARY_OK_MARKER in json.dumps(d)


def test_run_gate5_canary_blocked_without_impl():
    # Force unauthorized path via evaluate_enablement_gates directly is covered;
    # here: temporarily pretend by calling evaluate with False and ensuring
    # run path would abort — simulate by monkeypatching is_impl via gates.
    from neural_mesh.packaging import l_judge_gemini_free_canary_impl as mod

    real = mod.is_impl_cp_authorized
    mod.is_impl_cp_authorized = lambda: False  # type: ignore[assignment]
    try:
        ledger = run_gate5_canary_once(skip_network=True, request_id="blocked")
        assert ledger.may_enable is False
        assert ledger.ok is False
        assert "impl_cp_not_authorized" in ledger.reasons
        assert ledger.binding_final == "RefuseTransport"
    finally:
        mod.is_impl_cp_authorized = real  # type: ignore[assignment]


def test_docs_and_no_secrets():
    assert IMPL_DOC.is_file()
    assert ENABLE_ACK.is_file()
    assert PKG.is_file()
    text = IMPL_DOC.read_text(encoding="utf-8")
    assert "CP-0075" in text
    assert "NT-10" in text or "impl_cp" in text
    assert "ENABLE_UNDER_FENCES" in text
    assert "RefuseTransport" in text
    for path in (IMPL_DOC, PKG, ENABLE_ACK):
        body = path.read_text(encoding="utf-8")
        assert not re.search(r"sk-[A-Za-z0-9]{10,}", body), path.name
        assert "AIza" not in body
        assert "Authorization: Bearer sk-" not in body


def test_no_full_live_codec_shipped():
    src = REPO / "src" / "neural_mesh"
    banned = list(src.glob("judge*.py")) + list(src.glob("**/live_http*.py"))
    banned += list(src.glob("**/live_adapter_http*.py"))
    assert banned == [], f"unexpected live codec files: {banned}"
    assert (src / "packaging" / "l_judge_gemini_free_canary_impl.py").is_file()


def test_refuse_transport_still_default_binding():
    rt = RefuseTransport()
    h = rt.health()
    assert h["live"] is False
    assert h["binding"] == "RefuseTransport"
