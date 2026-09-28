"""Tests for Google / Gemini optional L_judge peer spike (design-only).

Mock transport only; live=DISABLED; no API keys; no network.
Authority: council/NOTE_GOOGLE_AI_TOOLS_FENCED.md (APPROVE_WITH_FENCES).
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from neural_mesh import __version__
from neural_mesh.packaging.google_l_judge_peer_spike import (
    ABORT_CODES,
    AUTHORITY_NOTE,
    COLAB_PLACEHOLDER,
    LIVE_API_ENABLED,
    M1_STATUS,
    N_CAP,
    PACKAGE_HELD,
    SCHEMA_CORRELATION,
    SCHEMA_PEER,
    GoogleLJudgePeerSpike,
    MockGeminiPeerTransport,
    default_refuse_transport,
    sample_envelope,
)
from neural_mesh.packaging.l_judge_live_adapter_safety import RefuseTransport

pytestmark = [pytest.mark.google_l_judge_peer_spike]

REPO = Path(__file__).resolve().parents[1]
NOTE = REPO / "council" / "NOTE_GOOGLE_AI_TOOLS_FENCED.md"
REPLY = REPO / "council" / "CHATGPT_REPLY_GOOGLE_AI_TOOLS_APPROVAL.md"
PASTE = REPO / "council" / "PASTE_CHATGPT_GOOGLE_AI_TOOLS_APPROVAL.md"
PLAN = REPO / "docs" / "planning" / "GOOGLE_L_JUDGE_PEER_SPIKE.md"
COLAB = REPO / "notebooks" / "colab" / "README.md"
PKG = REPO / "src" / "neural_mesh" / "packaging" / "google_l_judge_peer_spike.py"


def test_version_and_constants():
    assert __version__ == "0.18.0"
    assert PACKAGE_HELD == "0.18.0"
    assert LIVE_API_ENABLED is False
    assert M1_STATUS == "NO_CONSENSUS_YET"
    assert N_CAP == 2
    assert SCHEMA_PEER == "mesh.judge.google_peer_spike/v0"
    assert SCHEMA_CORRELATION == "mesh.judge.google_peer_correlation/v0"
    assert COLAB_PLACEHOLDER == "notebooks/colab/README.md"
    assert AUTHORITY_NOTE == "council/NOTE_GOOGLE_AI_TOOLS_FENCED.md"
    assert "PEER_LIVE_DISABLED" in ABORT_CODES
    assert "ENGINE_DISABLED" in ABORT_CODES


def test_authority_docs_present():
    assert REPLY.is_file()
    assert PASTE.is_file()
    assert NOTE.is_file()
    assert PLAN.is_file()
    assert COLAB.is_file()
    assert PKG.is_file()

    reply = REPLY.read_text(encoding="utf-8")
    assert "APPROVE_WITH_FENCES" in reply
    assert "Gemini" in reply
    assert "Colab" in reply

    note = NOTE.read_text(encoding="utf-8")
    assert "ALLOWED" in note or "ALLOWED_TOOLS" in note
    assert "FENCES" in note
    assert "FORBIDDEN" in note
    assert "live" in note.lower() and "DISABLED" in note
    assert "NO_CONSENSUS_YET" in note or "NO_CONSENSUS" in note

    plan = PLAN.read_text(encoding="utf-8")
    assert "RefuseTransport" in plan
    assert "correlation" in plan.lower() or "Correlation" in plan
    assert "independence" in plan.lower()
    assert "live=DISABLED" in plan or "LIVE_API_ENABLED" in plan
    assert "no API keys" in plan.lower() or "No API keys" in plan

    colab = COLAB.read_text(encoding="utf-8")
    assert "No Colab login required" in colab or "no Colab login" in colab.lower()
    assert "not" in colab.lower() and "runtime" in colab.lower()


def test_no_api_keys_in_artifacts():
    for path in (NOTE, REPLY, PASTE, PLAN, COLAB, PKG):
        text = path.read_text(encoding="utf-8")
        assert not re.search(r"sk-[A-Za-z0-9]{10,}", text), path.name
        assert "Authorization: Bearer sk-" not in text
        assert "AIza" not in text  # common Google API key prefix


def test_refuse_transport_default():
    rt = default_refuse_transport()
    assert isinstance(rt, RefuseTransport)
    out = rt.call({"request_id": "x"})
    assert out["ok"] is False
    assert out["error_code"] == "ENGINE_DISABLED"
    assert out["verdict"] == "ABORT"
    assert rt.health()["live"] is False


def test_mock_peers_disagree_no_consensus_claim():
    spike = GoogleLJudgePeerSpike(
        primary=MockGeminiPeerTransport(peer_id="p1", forced_digest="aaaaaaaaaaaaaaaa"),
        gemini=MockGeminiPeerTransport(peer_id="g1", forced_digest="bbbbbbbbbbbbbbbb"),
    )
    report = spike.run_correlation(sample_envelope())
    assert report.ok is True
    assert report.correlated is False
    assert report.disagreement is True
    assert report.dual_advisory is True
    assert report.advisory_only is True
    assert report.mesh_accept is False
    assert report.mesh_decision == "ABORT"
    assert report.m1_status == "NO_CONSENSUS_YET"
    assert report.live_api_enabled is False
    assert report.refuse_transport_default is True
    assert report.independence_risk == "LOW"
    assert report.abort_code is None  # advisory evidence continues
    assert len(report.attributions) == 2
    ap = report.abort_provenance
    assert ap["stage"] == "dual_advisory_correlation"
    assert ap["outcome"] == "DISAGREE_ABORT_MESH_ACCEPT"
    assert ap["code"] == "PEER_DIGEST_DISAGREE"
    assert ap["continue_advisory"] is True
    assert ap["mesh_accept"] is False
    assert ap["refuse_transport_default"] is True
    assert ap["binding"] == "RefuseTransport"
    assert ap["primary_digest"] == "aaaaaaaaaaaaaaaa"
    assert ap["gemini_digest"] == "bbbbbbbbbbbbbbbb"
    assert ap["policy"] == "ABORT_ACCEPT_CONTINUE_ADVISORY"
    d = report.to_dict()
    assert d["provenance"]["mesh_authority"] is False
    assert "not_consensus" in d["provenance"]["claim"]
    assert d["dual_advisory"] is True
    assert d["mesh_decision"] == "ABORT"
    assert d["abort_provenance"]["code"] == "PEER_DIGEST_DISAGREE"


def test_forced_correlation_flags_independence_risk():
    spike = GoogleLJudgePeerSpike(force_correlation=True)
    report = spike.run_correlation()
    assert report.ok is True
    assert report.correlated is True
    assert report.correlation_score == 1.0
    assert report.independence_risk == "HIGH"
    assert report.advisory_only is True
    assert report.dual_advisory is True
    assert report.mesh_accept is False
    assert report.mesh_decision == "ADVISORY"
    assert report.m1_status == "NO_CONSENSUS_YET"
    assert report.refuse_transport_default is True
    ap = report.abort_provenance
    assert ap["outcome"] == "AGREE_ADVISORY_ONLY"
    assert ap["mesh_accept"] is False
    assert ap["claim"] == "peer_agree_is_not_m1_consensus"
    assert ap["refuse_transport_default"] is True


def test_live_gemini_path_refused():
    spike = GoogleLJudgePeerSpike()
    env = sample_envelope()
    env["use_live_gemini"] = True
    report = spike.run_correlation(env)
    assert report.ok is False
    assert report.mesh_decision == "ABORT"
    assert report.mesh_accept is False
    assert report.abort_code == "PEER_LIVE_DISABLED"
    assert report.attributions[0].transport == "refuse"
    assert report.provenance["refuse"]["error_code"] == "ENGINE_DISABLED"
    ap = report.abort_provenance
    assert ap["stage"] == "live_gemini_slot"
    assert ap["outcome"] == "LIVE_REFUSED"
    assert ap["code"] == "PEER_LIVE_DISABLED"
    assert ap["refuse_error_code"] == "ENGINE_DISABLED"
    assert ap["binding"] == "RefuseTransport"
    assert ap["refuse_transport_default"] is True
    assert ap["requested_live"] is True


def test_fence_n_gt2_and_secrets():
    spike = GoogleLJudgePeerSpike()
    r1 = spike.run_correlation({**sample_envelope(), "n_peers": 3})
    assert r1.ok is False
    assert r1.abort_code == "PEER_N_GT2_REFUSED"
    assert r1.mesh_decision == "ABORT"
    assert r1.abort_provenance["stage"] == "fence"
    assert r1.abort_provenance["code"] == "PEER_N_GT2_REFUSED"

    r2 = spike.run_correlation({**sample_envelope(), "raft": True})
    assert r2.ok is False
    assert r2.abort_code == "PEER_FENCE"
    assert r2.abort_provenance["outcome"] == "FORBIDDEN_FLAG"

    r3 = spike.run_correlation({**sample_envelope(), "api_key": "should-not-appear"})
    assert r3.ok is False
    assert r3.abort_code == "PEER_SECRET_FORBIDDEN"
    assert r3.abort_provenance["secret_echoed"] is False


def test_mock_health_not_live():
    peer = MockGeminiPeerTransport()
    h = peer.health()
    assert h["live"] is False
    assert h["binding"] == "MockGeminiPeerTransport"

def test_dual_advisory_report_fields_and_refuse_default():
    """Hold mock cycle 2: dual-advisory fields present; RefuseTransport default."""
    assert "PEER_DIGEST_DISAGREE" in ABORT_CODES
    spike = GoogleLJudgePeerSpike()
    assert isinstance(spike.refuse, RefuseTransport)
    report = spike.run_correlation(sample_envelope())
    d = report.to_dict()
    for key in (
        "dual_advisory",
        "mesh_decision",
        "mesh_accept",
        "refuse_transport_default",
        "abort_provenance",
        "advisory_only",
        "m1_status",
    ):
        assert key in d
    assert d["dual_advisory"] is True
    assert d["mesh_accept"] is False
    assert d["refuse_transport_default"] is True
    assert d["m1_status"] == "NO_CONSENSUS_YET"
    assert d["live_api_enabled"] is False
    assert d["abort_provenance"]["binding"] == "RefuseTransport"
    # Agree or disagree — never Mesh ACCEPT / M1 consensus from mock peers.
    assert d["mesh_decision"] in ("ADVISORY", "ABORT")
    assert d["mesh_decision"] != "ACCEPT"


def test_disagree_abort_provenance_no_mesh_accept():
    """Disagreement records PEER_DIGEST_DISAGREE provenance; no invented ACCEPT."""
    spike = GoogleLJudgePeerSpike(
        primary=MockGeminiPeerTransport(peer_id="p1", forced_digest="1111111111111111"),
        gemini=MockGeminiPeerTransport(peer_id="g1", forced_digest="2222222222222222"),
    )
    report = spike.run_correlation()
    assert report.ok is True  # advisory evidence row continues
    assert report.disagreement is True
    assert report.mesh_decision == "ABORT"
    assert report.mesh_accept is False
    assert report.m1_status == "NO_CONSENSUS_YET"
    assert report.abort_provenance["code"] == "PEER_DIGEST_DISAGREE"
    assert report.abort_provenance["continue_advisory"] is True
    assert "ACCEPT" not in (report.mesh_decision, report.abort_code or "")

