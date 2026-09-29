"""Tests for Cycle 74 / CP-0078: LiveHttpTransport v0 (authorized under fences).

Markers: l_judge_live_http_transport_cycle74
Covers T-lht-* descriptors that are unit-testable now (mock HTTP; no live CI).
Module LIVE_API_ENABLED=True under F4 SIGNED; may_enable fail-closed without auth; I5 gates network.
"""

from __future__ import annotations

import io
import json
import re
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError

import pytest

from neural_mesh import __version__
from neural_mesh.packaging.l_judge_gemini_free_canary_impl import (
    arm_i5_for_canary,
    live_api_canary_session,
    runtime_live_api_enabled,
    set_runtime_live_api_enabled,
)
from neural_mesh.packaging.l_judge_live_adapter_safety import (
    MUST_STAY_FALSE,
    RefuseTransport,
    evaluate_enablement_gates,
)
from neural_mesh.packaging.l_judge_live_http_transport import (
    CYCLE,
    DEFAULT_SECRET_HANDLE,
    DESIGN_CP_ID,
    IMPL_CP_ID,
    LIVE_API_ENABLED,
    PACKAGE_HELD,
    PRIOR_CP,
    SEAL_CP,
    SRC_LIVE_CODEC_SHIPPED,
    IdempotencyStore,
    LiveHttpTransport,
    default_lht_policy,
    evaluate_lht_enablement,
    impl_cp_authorization_record,
    is_impl_cp_authorized,
    payload_digest,
)

pytestmark = [pytest.mark.l_judge_live_http_transport_cycle74]

REPO = Path(__file__).resolve().parents[1]
IMPL_DOC = REPO / "docs" / "planning" / "IMPL_CP_0078_LIVE_HTTP_TRANSPORT.md"
EVIDENCE = REPO / "docs" / "planning" / "EVIDENCE_CP_0078_LIVE_HTTP_TRANSPORT.md"
PKG = REPO / "src" / "neural_mesh" / "packaging" / "l_judge_live_http_transport.py"
SCHEMA = REPO / "docs" / "schema" / "judge" / "live_http_transport_v0.md"
FAKE_KEY = "test-key-not-a-real-secret"

def _transport(**kwargs):
    kwargs.setdefault("_load_key", lambda _p: FAKE_KEY)
    kwargs.setdefault("_sleeper", lambda _s: None)
    return LiveHttpTransport(**kwargs)


class _FakeResp:
    def __init__(self, body: bytes, status: int = 200):
        self._body = body
        self.status = status

    def read(self) -> bytes:
        return self._body

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


def _ok_body(text: str = "MESH_LHT_OK") -> bytes:
    return json.dumps(
        {"candidates": [{"content": {"parts": [{"text": text}]}}]}
    ).encode()


def setup_function(_fn=None):
    set_runtime_live_api_enabled(False)


def teardown_function(_fn=None):
    set_runtime_live_api_enabled(False)


def test_constants_and_authorization():
    assert __version__ == "0.18.0"
    assert PACKAGE_HELD == "0.18.0"
    assert SEAL_CP == "CP-0078" == IMPL_CP_ID
    assert PRIOR_CP == "CP-0077"
    assert DESIGN_CP_ID == "CP-0076"
    assert CYCLE == 74
    assert LIVE_API_ENABLED is True
    assert SRC_LIVE_CODEC_SHIPPED is True
    assert is_impl_cp_authorized() is True
    auth = impl_cp_authorization_record()
    assert auth["authorized"] is True
    assert auth["src_live_codec_shipped"] is True
    assert auth["full_live_http_codec_shipped"] is True
    assert auth["permanent_live_enable"] is True
    assert auth["live_api_enabled_module_default"] is True
    pol = default_lht_policy()
    assert pol["enabled"] is False
    assert pol["LIVE_API_ENABLED"] is True
    assert pol["streaming_allowed"] is False
    assert pol["max_retries"] == 1


def test_may_enable_fail_closed_without_auth():
    res = evaluate_enablement_gates()
    assert res.may_enable is False
    assert "impl_cp_not_authorized" in res.reasons
    blocked = evaluate_lht_enablement(impl_cp_authorized=False)
    assert blocked.may_enable is False
    assert "impl_cp_not_authorized" in blocked.reasons


def test_may_enable_under_authorized_impl():
    res = evaluate_lht_enablement()
    assert res.may_enable is True
    assert res.reasons == []


def test_src_live_codec_no_longer_blocks_enablement():
    # CP-0078 shipped codec; asserting flag True must not refuse may_enable.
    assert "src_live_codec_shipped" not in MUST_STAY_FALSE
    res = evaluate_lht_enablement(flags={"src_live_codec_shipped": True})
    assert res.may_enable is True
    # F4 SIGNED: live_adapter.enabled=True authorized (no longer a refusal)
    allowed = evaluate_lht_enablement(flags={"live_adapter.enabled": True})
    assert allowed.may_enable is True
    assert allowed.reasons == []


def test_t_lht_a_refuse_when_live_off():
    """T-lht-a: I5 not armed → RefuseTransport; zero network (module may be True under F4)."""
    from neural_mesh.packaging.l_judge_gemini_free_canary_impl import I5KillArm
    i5 = I5KillArm()
    calls = {"n": 0}

    def boom(*_a, **_k):
        calls["n"] += 1
        raise AssertionError("network must not open")

    t = _transport(i5=i5, _urlopen=boom)
    out = t.call({"prompt": "x"}, idempotency_key="k-a")
    assert out["ok"] is False
    assert out["error_code"] == "ENGINE_DISABLED"
    assert out["verdict"] == "ABORT"
    assert calls["n"] == 0
    assert t.health()["binding"] == "RefuseTransport"
    assert LIVE_API_ENABLED is True


def test_t_lht_b_invalid_secret_handle():
    """T-lht-b: missing/invalid secret_handle → ENGINE_AUTH."""
    i5 = arm_i5_for_canary()
    with live_api_canary_session(i5=i5, enablement_ok=True):
        t = _transport(i5=i5, secret_handle="not-a-handle", _urlopen=lambda *a, **k: None)
        out = t.call({"prompt": "x"}, idempotency_key="k-b")
        assert out["error_code"] == "ENGINE_AUTH"
        assert out["verdict"] == "ABORT"


def test_t_lht_c_plaintext_forbidden():
    """T-lht-c: plaintext / non-TLS → PLAINTEXT_FORBIDDEN."""
    i5 = arm_i5_for_canary()
    with live_api_canary_session(i5=i5, enablement_ok=True):
        t = LiveHttpTransport(
            i5=i5,
            endpoint_base="http://example.invalid/v1",
            _urlopen=lambda *a, **k: (_ for _ in ()).throw(AssertionError("no net")),
        )
        out = t.call({"prompt": "x"}, idempotency_key="k-c")
        assert out["error_code"] == "PLAINTEXT_FORBIDDEN"
        assert out["verdict"] == "ABORT"


def test_t_lht_d_idempotent_replay_no_double_invoke():
    """T-lht-d: duplicate key same payload → no double-invoke."""
    i5 = arm_i5_for_canary()
    hits = {"n": 0}

    def urlopen(_req, timeout=30.0):
        hits["n"] += 1
        return _FakeResp(_ok_body())

    with live_api_canary_session(i5=i5, enablement_ok=True):
        t = _transport(i5=i5, _urlopen=urlopen, _sleeper=lambda _s: None)
        a = t.call({"prompt": "same"}, idempotency_key="k-d")
        b = t.call({"prompt": "same"}, idempotency_key="k-d")
        assert a["ok"] is True
        assert b.get("idempotent_replay") is True
        assert hits["n"] == 1


def test_t_lht_e_idempotency_conflict():
    """T-lht-e: duplicate key different payload → CONT_IDEMPOTENCY_CONFLICT."""
    i5 = arm_i5_for_canary()

    def urlopen(_req, timeout=30.0):
        return _FakeResp(_ok_body())

    with live_api_canary_session(i5=i5, enablement_ok=True):
        t = _transport(i5=i5, _urlopen=urlopen, _sleeper=lambda _s: None)
        assert t.call({"prompt": "one"}, idempotency_key="k-e")["ok"] is True
        out = t.call({"prompt": "two"}, idempotency_key="k-e")
        assert out["error_code"] == "CONT_IDEMPOTENCY_CONFLICT"
        assert out["verdict"] == "ABORT"


def test_t_lht_f_retries_exhausted_on_5xx():
    """T-lht-f: exhaust max_retries on 5xx → ENGINE_HTTP; no ACCEPT invent."""
    i5 = arm_i5_for_canary()
    hits = {"n": 0}

    def urlopen(_req, timeout=30.0):
        hits["n"] += 1
        raise HTTPError("https://x", 503, "unavailable", hdrs=None, fp=io.BytesIO(b"{}"))

    with live_api_canary_session(i5=i5, enablement_ok=True):
        t = _transport(i5=i5, _urlopen=urlopen, _sleeper=lambda _s: None, max_retries=1)
        out = t.call({"prompt": "x"}, idempotency_key="k-f")
        assert out["error_code"] == "ENGINE_HTTP"
        assert out["verdict"] == "ABORT"
        assert out.get("mesh_accept") is False
        assert hits["n"] == 2  # initial + 1 retry
        assert out.get("retries_exhausted") is True


def test_t_lht_g_hard_timeout():
    """T-lht-g: hard timeout → ENGINE_TIMEOUT."""
    i5 = arm_i5_for_canary()

    def urlopen(_req, timeout=30.0):
        raise TimeoutError("simulated")

    with live_api_canary_session(i5=i5, enablement_ok=True):
        t = _transport(i5=i5, _urlopen=urlopen, _sleeper=lambda _s: None, timeout_s=1.0)
        out = t.call({"prompt": "x"}, idempotency_key="k-g", timeout_s=1.0)
        assert out["error_code"] == "ENGINE_TIMEOUT"
        assert out["verdict"] == "ABORT"


def test_t_lht_h_i5_kill_mid_call():
    """T-lht-h: I5 kill → HUMAN_ABORT; subsequent RefuseTransport."""
    i5 = arm_i5_for_canary()
    with live_api_canary_session(i5=i5, enablement_ok=True):
        t = _transport(i5=i5, _urlopen=lambda *a, **k: _FakeResp(_ok_body()))
        i5.kill("test_kill")
        out = t.call({"prompt": "x"}, idempotency_key="k-h")
        # After kill, allow_network False → RefuseTransport ENGINE_DISABLED OR HUMAN_ABORT
        assert out["verdict"] == "ABORT"
        assert out["error_code"] in ("ENGINE_DISABLED", "HUMAN_ABORT")
        # cancel path
        i52 = arm_i5_for_canary()
        with live_api_canary_session(i5=i52, enablement_ok=True):
            t2 = _transport(i5=i52, _urlopen=lambda *a, **k: _FakeResp(_ok_body()))
            t2.cancel(idempotency_key="k-h2")
            out2 = t2.call({"prompt": "x"}, idempotency_key="k-h2")
            assert out2["error_code"] == "HUMAN_ABORT"


def test_t_lht_i_missing_audit_sink():
    """T-lht-i: missing audit sink → NO_AUDIT."""
    i5 = arm_i5_for_canary()
    with live_api_canary_session(i5=i5, enablement_ok=True):
        t = _transport(i5=i5, audit_sink=False, _urlopen=lambda *a, **k: None)
        out = t.call({"prompt": "x"}, idempotency_key="k-i")
        assert out["error_code"] == "NO_AUDIT"


def test_t_lht_j_stream_unsupported_no_half_accept():
    """T-lht-j: stream mode unsupported → ABORT; no half-ACCEPT."""
    i5 = arm_i5_for_canary()
    with live_api_canary_session(i5=i5, enablement_ok=True):
        t = _transport(i5=i5, _urlopen=lambda *a, **k: None)
        out = t.call({"prompt": "x"}, idempotency_key="k-j", mode="streaming")
        assert out["ok"] is False
        assert out["verdict"] == "ABORT"
        assert out.get("mesh_accept") is False
        assert out["error_code"] == "ENGINE_HTTP"


def test_t_lht_k_live_api_in_ci_stays_refused():
    """T-lht-k: live_api_in_ci aspirational → refused in enablement."""
    res = evaluate_lht_enablement(flags={"live_api_in_ci": True})
    assert res.may_enable is False
    assert "live_api_in_ci_must_stay_false" in res.reasons
    assert LIVE_API_ENABLED is True


def test_t_lht_l_codec_authorized_under_impl_cp_not_design_only():
    """T-lht-l inverse: under CP-0078 (impl) src_live_codec_shipped is True; DESIGN_ONLY could not claim it."""
    assert SRC_LIVE_CODEC_SHIPPED is True
    assert IMPL_CP_ID == "CP-0078"
    assert DESIGN_CP_ID == "CP-0076"
    assert PKG.is_file()
    # Historical DESIGN_ONLY residual still on disk and must not claim impl auth alone
    design = (REPO / "docs" / "planning" / "DESIGN_CP_0076_LIVE_HTTP_TRANSPORT_RESIDUAL.md").read_text(
        encoding="utf-8"
    )
    assert "does NOT authorize codec implementation" in design or "Does NOT authorize" in design


def test_missing_idempotency_key_aborts():
    i5 = arm_i5_for_canary()
    with live_api_canary_session(i5=i5, enablement_ok=True):
        t = _transport(i5=i5, _urlopen=lambda *a, **k: _FakeResp(_ok_body()))
        out = t.call({"prompt": "x"})
        assert out["error_code"] in ("CONT_LIVE_DISABLED", "SCHEMA_INVALID")


def test_auth_401_non_retryable():
    i5 = arm_i5_for_canary()
    hits = {"n": 0}

    def urlopen(_req, timeout=30.0):
        hits["n"] += 1
        raise HTTPError("https://x", 401, "no", hdrs=None, fp=io.BytesIO(b"{}"))

    with live_api_canary_session(i5=i5, enablement_ok=True):
        t = _transport(i5=i5, _urlopen=urlopen, _sleeper=lambda _s: None)
        out = t.call({"prompt": "x"}, idempotency_key="k-401")
        assert out["error_code"] == "ENGINE_AUTH"
        assert hits["n"] == 1


def test_happy_path_mock_http_advisory_only():
    i5 = arm_i5_for_canary()

    def urlopen(_req, timeout=30.0):
        return _FakeResp(_ok_body("MESH_LHT_OK hello"))

    with live_api_canary_session(i5=i5, enablement_ok=True):
        t = _transport(i5=i5, _urlopen=urlopen, _sleeper=lambda _s: None)
        out = t.call({"prompt": "hi"}, idempotency_key="k-ok")
        assert out["ok"] is True
        assert out["verdict"] == "ADVISORY"
        assert out["mesh_accept"] is False
        assert out["advisory_only"] is True
        assert out["LIVE_API_ENABLED_module_default"] is True
    assert runtime_live_api_enabled() is True  # module F4 True; I5 still gates
    assert LIVE_API_ENABLED is True


def test_canary_compose_still_works():
    """CP-0075 canary path must remain usable / not broken by CP-0078."""
    from neural_mesh.packaging.l_judge_gemini_free_canary_impl import (
        LIVE_API_ENABLED as CANARY_LIVE,
        run_gate5_canary_once,
    )

    assert CANARY_LIVE is True
    ledger = run_gate5_canary_once(skip_network=True, request_id="compose-check")
    assert ledger.may_enable is True
    assert ledger.live_api_enabled_final is True  # F4 module permanent
    assert ledger.binding_final == "RefuseTransport"


def test_docs_and_no_secrets():
    assert IMPL_DOC.is_file()
    assert EVIDENCE.is_file()
    assert SCHEMA.is_file()
    assert PKG.is_file()
    for path in (IMPL_DOC, EVIDENCE, PKG, SCHEMA):
        body = path.read_text(encoding="utf-8")
        assert not re.search(r"sk-[A-Za-z0-9]{10,}", body), path.name
        assert "AIza" not in body
        assert "Authorization: Bearer sk-" not in body
    text = IMPL_DOC.read_text(encoding="utf-8")
    assert "CP-0078" in text
    assert "ENABLE_UNDER_FENCES" in text
    assert "RefuseTransport" in text
    assert "LIVE_API_ENABLED" in text


def test_refuse_transport_still_default_when_off():
    rt = RefuseTransport()
    assert rt.health()["live"] is False
    assert LIVE_API_ENABLED is True


def test_payload_digest_stable():
    assert payload_digest({"prompt": "a"}) == payload_digest({"prompt": "a"})
    assert payload_digest({"prompt": "a"}) != payload_digest({"prompt": "b"})


def test_idempotency_store_unit():
    store = IdempotencyStore()
    store.store("k", "d1", {"ok": True})
    prior, err = store.lookup("k", "d1")
    assert prior and prior["ok"] is True and err is None
    _, err2 = store.lookup("k", "d2")
    assert err2 == "CONT_IDEMPOTENCY_CONFLICT"
    store.cancel("k")
    _, err3 = store.lookup("k", "d1")
    assert err3 == "HUMAN_ABORT"
