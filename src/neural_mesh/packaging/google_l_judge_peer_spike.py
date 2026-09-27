"""Google / Gemini optional L_judge peer spike (design-only).

Mock / dry-run helpers for treating Gemini free-tier as an optional second
L_judge peer under ChatGPT APPROVE_WITH_FENCES. RefuseTransport default.
No network. No API keys. live=DISABLED. Dual advisory ≠ M1 consensus.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import Any

from neural_mesh.packaging.l_judge_live_adapter_safety import RefuseTransport

__all__ = [
    "PACKAGE_HELD",
    "LIVE_API_ENABLED",
    "M1_STATUS",
    "SCHEMA_PEER",
    "SCHEMA_CORRELATION",
    "N_CAP",
    "ABORT_CODES",
    "COLAB_PLACEHOLDER",
    "AUTHORITY_NOTE",
    "MockGeminiPeerTransport",
    "PeerAttribution",
    "CorrelationReport",
    "GoogleLJudgePeerSpike",
    "default_refuse_transport",
    "sample_envelope",
]

PACKAGE_HELD = "0.18.0"
LIVE_API_ENABLED = False  # must stay False (live=DISABLED)
M1_STATUS = "NO_CONSENSUS_YET"
SCHEMA_PEER = "mesh.judge.google_peer_spike/v0"
SCHEMA_CORRELATION = "mesh.judge.google_peer_correlation/v0"
N_CAP = 2
COLAB_PLACEHOLDER = "notebooks/colab/README.md"
AUTHORITY_NOTE = "council/NOTE_GOOGLE_AI_TOOLS_FENCED.md"

ABORT_CODES: tuple[str, ...] = (
    "PEER_LIVE_DISABLED",
    "PEER_N_GT2_REFUSED",
    "PEER_FENCE",
    "PEER_SECRET_FORBIDDEN",
    "PEER_SCHEMA_INVALID",
    "ENGINE_DISABLED",
)


def _digest16(payload: dict[str, Any]) -> str:
    blob = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(blob).hexdigest()[:16]


def default_refuse_transport() -> RefuseTransport:
    """Fail-closed binding for any live Gemini slot."""
    return RefuseTransport()


def sample_envelope(
    *,
    request_id: str = "req-google-peer-1",
    prompt: str = "advise on mock envelope",
) -> dict[str, Any]:
    return {
        "schema": SCHEMA_PEER,
        "request_id": request_id,
        "prompt": prompt,
        "live_api_enabled": LIVE_API_ENABLED,
        "advisory_only": True,
        "m1_status": M1_STATUS,
    }


@dataclass
class PeerAttribution:
    peer_id: str
    provider: str
    model_ref: str
    digest: str
    transport: str  # mock | refuse
    verdict: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "peer_id": self.peer_id,
            "provider": self.provider,
            "model_ref": self.model_ref,
            "digest": self.digest,
            "transport": self.transport,
            "verdict": self.verdict,
        }


@dataclass
class CorrelationReport:
    schema: str = SCHEMA_CORRELATION
    ok: bool = True
    correlated: bool = False
    correlation_score: float = 0.0
    independence_risk: str = "UNKNOWN"  # LOW | MEDIUM | HIGH | UNKNOWN
    disagreement: bool = False
    advisory_only: bool = True
    m1_status: str = M1_STATUS
    live_api_enabled: bool = False
    attributions: list[PeerAttribution] = field(default_factory=list)
    abort_code: str | None = None
    abort_reason: str | None = None
    provenance: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "ok": self.ok,
            "correlated": self.correlated,
            "correlation_score": self.correlation_score,
            "independence_risk": self.independence_risk,
            "disagreement": self.disagreement,
            "advisory_only": self.advisory_only,
            "m1_status": self.m1_status,
            "live_api_enabled": self.live_api_enabled,
            "attributions": [a.to_dict() for a in self.attributions],
            "abort_code": self.abort_code,
            "abort_reason": self.abort_reason,
            "provenance": dict(self.provenance),
        }


@dataclass
class MockGeminiPeerTransport:
    """In-process mock Gemini peer — never opens network; never reads keys."""

    peer_id: str = "gemini-mock-peer"
    model_ref: str = "mock-gemini-free"
    forced_digest: str | None = None
    name: str = "MockGeminiPeerTransport"

    def call(self, bundle: dict[str, Any] | None = None, *, timeout_s: float = 30.0) -> dict[str, Any]:
        _ = timeout_s
        payload = dict(bundle or {})
        digest = self.forced_digest or _digest16(
            {"peer": self.peer_id, "prompt": payload.get("prompt"), "rid": payload.get("request_id")}
        )
        return {
            "schema": "mesh.judge.raw_engine/v0",
            "ok": True,
            "http_status": None,
            "latency_ms": 0,
            "raw_text": None,
            "error_code": None,
            "provider": "gemini-mock",
            "model_ref": self.model_ref,
            "truncated": False,
            "verdict": "ADVISORY",
            "digest": digest,
            "peer_id": self.peer_id,
            "transport": "mock",
        }

    def health(self) -> dict[str, Any]:
        return {"ok": True, "binding": self.name, "live": False, "provider": "gemini-mock"}


class GoogleLJudgePeerSpike:
    """Dry-run spike: primary mock + optional Gemini mock peer; RefuseTransport on live."""

    def __init__(
        self,
        *,
        primary: MockGeminiPeerTransport | None = None,
        gemini: MockGeminiPeerTransport | None = None,
        refuse: RefuseTransport | None = None,
        force_correlation: bool = False,
    ) -> None:
        self.primary = primary or MockGeminiPeerTransport(
            peer_id="primary-mock-peer", model_ref="mock-primary"
        )
        self.gemini = gemini or MockGeminiPeerTransport()
        self.refuse = refuse or default_refuse_transport()
        self.force_correlation = force_correlation
        if self.force_correlation:
            # Same digest → independence_risk HIGH for review (design signal only).
            shared = _digest16({"forced": "correlation-fixture"})
            self.primary.forced_digest = shared
            self.gemini.forced_digest = shared

    def run_correlation(self, envelope: dict[str, Any] | None = None) -> CorrelationReport:
        env = dict(envelope or sample_envelope())
        report = CorrelationReport(
            provenance={
                "authority_note": AUTHORITY_NOTE,
                "colab_placeholder": COLAB_PLACEHOLDER,
                "evidence_only": True,
                "mesh_authority": False,
            }
        )

        if env.get("n_peers", N_CAP) and int(env.get("n_peers", N_CAP)) > N_CAP:
            report.ok = False
            report.abort_code = "PEER_N_GT2_REFUSED"
            report.abort_reason = "N>2 peer roster refused under fence"
            return report

        if env.get("raft") or env.get("saas") or env.get("train_70b"):
            report.ok = False
            report.abort_code = "PEER_FENCE"
            report.abort_reason = "forbidden flag under Google tools fences"
            return report

        secret = env.get("api_key") or env.get("secret") or env.get("raw_key")
        if secret:
            report.ok = False
            report.abort_code = "PEER_SECRET_FORBIDDEN"
            report.abort_reason = "no API keys in repo / envelope"
            return report

        # Live path is always refused while LIVE_API_ENABLED is False.
        if env.get("live_api_enabled") or env.get("use_live_gemini"):
            refused = self.refuse.call(env)
            report.ok = False
            report.live_api_enabled = False
            report.abort_code = "PEER_LIVE_DISABLED"
            report.abort_reason = "live=DISABLED; RefuseTransport default"
            report.attributions.append(
                PeerAttribution(
                    peer_id="gemini-live-slot",
                    provider="refuse",
                    model_ref="none",
                    digest="",
                    transport="refuse",
                    verdict=str(refused.get("verdict") or "ABORT"),
                )
            )
            report.provenance["refuse"] = {
                "error_code": refused.get("error_code"),
                "abort": refused.get("abort"),
            }
            return report

        primary_out = self.primary.call(env)
        gemini_out = self.gemini.call(env)
        d1 = str(primary_out.get("digest") or "")
        d2 = str(gemini_out.get("digest") or "")
        equal = bool(d1) and d1 == d2
        # Mock Hamming on hex digests for a soft score when unequal.
        if equal:
            score = 1.0
        elif not d1 or not d2:
            score = 0.0
        else:
            same = sum(a == b for a, b in zip(d1, d2))
            score = same / max(len(d1), len(d2))

        report.correlated = equal
        report.correlation_score = score
        report.disagreement = not equal
        if equal:
            report.independence_risk = "HIGH" if self.force_correlation else "MEDIUM"
        elif score >= 0.75:
            report.independence_risk = "MEDIUM"
        else:
            report.independence_risk = "LOW"

        report.attributions = [
            PeerAttribution(
                peer_id=str(primary_out.get("peer_id")),
                provider=str(primary_out.get("provider")),
                model_ref=str(primary_out.get("model_ref")),
                digest=d1,
                transport="mock",
                verdict=str(primary_out.get("verdict")),
            ),
            PeerAttribution(
                peer_id=str(gemini_out.get("peer_id")),
                provider=str(gemini_out.get("provider")),
                model_ref=str(gemini_out.get("model_ref")),
                digest=d2,
                transport="mock",
                verdict=str(gemini_out.get("verdict")),
            ),
        ]
        report.provenance["request_id"] = env.get("request_id")
        report.provenance["claim"] = (
            "evidence_input_only_not_consensus_not_safety_proof"
        )
        return report
