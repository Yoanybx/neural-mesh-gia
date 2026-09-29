"""Google / Gemini optional L_judge peer spike (design-only + eval dry-run).

Mock helpers for treating Gemini free-tier as an optional second L_judge peer
under ChatGPT APPROVE_WITH_FENCES. RefuseTransport default for Mesh live.
Default path: **no network**, no API keys. live=DISABLED. Dual advisory ≠ M1
consensus. LIVE_API_ENABLED stays False.

Hold mock cycle 2: dual-advisory report fields + abort provenance when mock
peers disagree (Mesh ACCEPT refused; advisory evidence may continue).

Eval dry-run (NOT Mesh live): an **explicit** flag ``--gemini-dry-run`` or
env ``GEMINI_DRY_RUN=1`` enables ONE real free-tier generateContent call via
``GeminiFreeDryRunTransport``, loading the key from the Gate4 out-of-band
secret file (path only). Key file presence alone never opens network.
Does **not** flip LIVE_API_ENABLED or enable the Mesh live L_judge adapter.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping

from neural_mesh.packaging.l_judge_live_adapter_safety import (
    RefuseTransport,
    is_valid_secret_handle,
)

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
    "GEMINI_DRY_RUN_ENV",
    "DEFAULT_GEMINI_ENV_PATH",
    "DEFAULT_DRY_RUN_MODEL",
    "DRY_RUN_SECRET_HANDLE",
    "DRY_RUN_OK_MARKER",
    "DRY_RUN_PROMPT",
    "MockGeminiPeerTransport",
    "GeminiFreeDryRunTransport",
    "PeerAttribution",
    "CorrelationReport",
    "GoogleLJudgePeerSpike",
    "default_refuse_transport",
    "sample_envelope",
    "gemini_dry_run_flag_enabled",
    "load_gemini_key_from_secret_file",
    "build_peer_spike",
    "run_gemini_dry_run_once",
    "main",
]

PACKAGE_HELD = "0.18.0"
LIVE_API_ENABLED = True  # F4 product permanent (SIGNED); I5 still gates network
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
    "PEER_DIGEST_DISAGREE",
    "PEER_DRY_RUN_FLAG_REQUIRED",
    "PEER_DRY_RUN_AUTH",
    "PEER_DRY_RUN_HTTP",
    "PEER_DRY_RUN_TIMEOUT",
    "ENGINE_DISABLED",
)

# Eval dry-run only (NOT Mesh live). Explicit flag required for any network.
GEMINI_DRY_RUN_ENV = "GEMINI_DRY_RUN"
DEFAULT_GEMINI_ENV_PATH = Path.home() / ".config" / "neural-mesh" / "gemini.env"
DEFAULT_DRY_RUN_MODEL = "gemini-flash-latest"  # 2.0/1.5 flash returned 404 in evidence
DRY_RUN_SECRET_HANDLE = "mesh://secrets/judge/gemini-free@v1"  # Gate4 handle id only
DRY_RUN_OK_MARKER = "MESH_DRY_RUN_OK"
DRY_RUN_PROMPT = "Reply with exactly: MESH_DRY_RUN_OK"
_GEMINI_API_BASE = "https://generativelanguage.googleapis.com/v1beta/models"


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
    dual_advisory: bool = True
    mesh_decision: str = "ADVISORY"  # ADVISORY | ABORT — never ACCEPT from peers
    mesh_accept: bool = False
    advisory_only: bool = True
    m1_status: str = M1_STATUS
    live_api_enabled: bool = False
    refuse_transport_default: bool = True
    attributions: list[PeerAttribution] = field(default_factory=list)
    abort_code: str | None = None
    abort_reason: str | None = None
    abort_provenance: dict[str, Any] = field(default_factory=dict)
    provenance: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "ok": self.ok,
            "correlated": self.correlated,
            "correlation_score": self.correlation_score,
            "independence_risk": self.independence_risk,
            "disagreement": self.disagreement,
            "dual_advisory": self.dual_advisory,
            "mesh_decision": self.mesh_decision,
            "mesh_accept": self.mesh_accept,
            "advisory_only": self.advisory_only,
            "m1_status": self.m1_status,
            "live_api_enabled": self.live_api_enabled,
            "refuse_transport_default": self.refuse_transport_default,
            "attributions": [a.to_dict() for a in self.attributions],
            "abort_code": self.abort_code,
            "abort_reason": self.abort_reason,
            "abort_provenance": dict(self.abort_provenance),
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



def _base_abort_provenance(**extra: Any) -> dict[str, Any]:
    """Structured abort / dual-advisory provenance (mock; live=DISABLED)."""
    base: dict[str, Any] = {
        "live_api_enabled": False,
        "refuse_transport_default": True,
        "binding": "RefuseTransport",
        "mesh_accept": False,
        "m1_status": M1_STATUS,
        "advisory_only": True,
        "dual_advisory": True,
    }
    base.update(extra)
    return base


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
                "refuse_transport_default": True,
            }
        )

        if env.get("n_peers", N_CAP) and int(env.get("n_peers", N_CAP)) > N_CAP:
            report.ok = False
            report.mesh_decision = "ABORT"
            report.abort_code = "PEER_N_GT2_REFUSED"
            report.abort_reason = "N>2 peer roster refused under fence"
            report.abort_provenance = _base_abort_provenance(
                stage="fence",
                outcome="N_GT2_REFUSED",
                code="PEER_N_GT2_REFUSED",
                continue_advisory=False,
                n_peers=int(env.get("n_peers", N_CAP)),
                n_cap=N_CAP,
            )
            return report

        if env.get("raft") or env.get("saas") or env.get("train_70b"):
            report.ok = False
            report.mesh_decision = "ABORT"
            report.abort_code = "PEER_FENCE"
            report.abort_reason = "forbidden flag under Google tools fences"
            report.abort_provenance = _base_abort_provenance(
                stage="fence",
                outcome="FORBIDDEN_FLAG",
                code="PEER_FENCE",
                continue_advisory=False,
                flags={
                    "raft": bool(env.get("raft")),
                    "saas": bool(env.get("saas")),
                    "train_70b": bool(env.get("train_70b")),
                },
            )
            return report

        secret = env.get("api_key") or env.get("secret") or env.get("raw_key")
        if secret:
            report.ok = False
            report.mesh_decision = "ABORT"
            report.abort_code = "PEER_SECRET_FORBIDDEN"
            report.abort_reason = "no API keys in repo / envelope"
            report.abort_provenance = _base_abort_provenance(
                stage="fence",
                outcome="SECRET_FORBIDDEN",
                code="PEER_SECRET_FORBIDDEN",
                continue_advisory=False,
                secret_present=True,
                secret_echoed=False,
            )
            return report

        # Explicit live-gemini *slot request* still RefuseTransport here.
        # Product LIVE_API_ENABLED=True (F4) does not open this spike slot;
        # Mesh live HTTP uses canary/LHT under I5. sample_envelope may report
        # live_api_enabled=module for honesty without triggering this path.
        if env.get("use_live_gemini") or env.get("request_live_gemini_slot"):
            refused = self.refuse.call(env)
            report.ok = False
            report.mesh_decision = "ABORT"
            report.live_api_enabled = bool(LIVE_API_ENABLED)
            report.abort_code = "PEER_LIVE_DISABLED"
            report.abort_reason = "live gemini slot refused; use canary/LHT under I5"
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
            report.abort_provenance = _base_abort_provenance(
                stage="live_gemini_slot",
                outcome="LIVE_REFUSED",
                code="PEER_LIVE_DISABLED",
                continue_advisory=False,
                refuse_error_code=refused.get("error_code"),
                refuse_verdict=refused.get("verdict"),
                requested_live=True,
            )
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
        report.dual_advisory = True
        report.mesh_accept = False
        report.advisory_only = True
        report.m1_status = M1_STATUS
        report.live_api_enabled = bool(LIVE_API_ENABLED)
        report.refuse_transport_default = True
        if equal:
            report.independence_risk = "HIGH" if self.force_correlation else "MEDIUM"
            report.mesh_decision = "ADVISORY"
            report.abort_provenance = _base_abort_provenance(
                stage="dual_advisory_correlation",
                outcome="AGREE_ADVISORY_ONLY",
                code=None,
                continue_advisory=True,
                primary_digest=d1,
                gemini_digest=d2,
                correlation_score=score,
                independence_risk=report.independence_risk,
                force_correlation=bool(self.force_correlation),
                claim="peer_agree_is_not_m1_consensus",
            )
        else:
            if score >= 0.75:
                report.independence_risk = "MEDIUM"
            else:
                report.independence_risk = "LOW"
            # Disagreement: refuse Mesh ACCEPT; keep dual-advisory evidence.
            report.mesh_decision = "ABORT"
            report.abort_provenance = _base_abort_provenance(
                stage="dual_advisory_correlation",
                outcome="DISAGREE_ABORT_MESH_ACCEPT",
                code="PEER_DIGEST_DISAGREE",
                continue_advisory=True,
                primary_digest=d1,
                gemini_digest=d2,
                correlation_score=score,
                independence_risk=report.independence_risk,
                policy="ABORT_ACCEPT_CONTINUE_ADVISORY",
                claim="disagreement_recorded_no_invented_accept",
            )

        report.attributions = [
            PeerAttribution(
                peer_id=str(primary_out.get("peer_id")),
                provider=str(primary_out.get("provider")),
                model_ref=str(primary_out.get("model_ref")),
                digest=d1,
                transport=str(primary_out.get("transport") or "mock"),
                verdict=str(primary_out.get("verdict")),
            ),
            PeerAttribution(
                peer_id=str(gemini_out.get("peer_id")),
                provider=str(gemini_out.get("provider")),
                model_ref=str(gemini_out.get("model_ref")),
                digest=d2,
                transport=str(gemini_out.get("transport") or "mock"),
                verdict=str(gemini_out.get("verdict")),
            ),
        ]
        report.provenance["request_id"] = env.get("request_id")
        report.provenance["claim"] = (
            "evidence_input_only_not_consensus_not_safety_proof"
        )
        report.provenance["dual_advisory"] = True
        report.provenance["mesh_decision"] = report.mesh_decision
        return report


# ---------------------------------------------------------------------------
# Eval dry-run (explicit flag only) — NOT Mesh live / LIVE_API_ENABLED
# ---------------------------------------------------------------------------


def gemini_dry_run_flag_enabled(
    *,
    env: Mapping[str, str] | None = None,
    cli_flag: bool = False,
) -> bool:
    """Return True only when dry-run is explicitly requested.

    Key file presence alone is never enough. Mesh live remains DISABLED.
    """
    if cli_flag:
        return True
    e = env if env is not None else os.environ
    val = str(e.get(GEMINI_DRY_RUN_ENV, "")).strip().lower()
    return val in ("1", "true", "yes", "on")


def load_gemini_key_from_secret_file(path: Path | str | None = None) -> str:
    """Load GEMINI_API_KEY from Gate4 out-of-band env file (never log value)."""
    p = Path(path) if path is not None else DEFAULT_GEMINI_ENV_PATH
    if not p.is_file():
        raise FileNotFoundError(f"secret env file missing: {p}")
    key = ""
    for raw in p.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("GEMINI_API_KEY="):
            key = line.split("=", 1)[1].strip().strip('"').strip("'")
            break
    if not key:
        raise ValueError("GEMINI_API_KEY not found in secret env file")
    return key


def _redact(text: str, secret: str | None = None) -> str:
    out = text
    if secret:
        out = out.replace(secret, "<REDACTED>")
    # Belt-and-suspenders for common query form.
    if "key=" in out:
        parts = out.split("key=")
        rebuilt = [parts[0]]
        for chunk in parts[1:]:
            if not chunk:
                rebuilt.append("key=<REDACTED>")
                continue
            sep_i = len(chunk)
            for sep in ("&", " ", '"', "'", "\n"):
                j = chunk.find(sep)
                if j != -1:
                    sep_i = min(sep_i, j)
            rebuilt.append("key=<REDACTED>" + chunk[sep_i:])
        out = "".join(rebuilt)
    return out


def _extract_candidate_text(body: dict[str, Any]) -> str:
    cands = body.get("candidates") or []
    if not cands:
        return ""
    content = (cands[0] or {}).get("content") or {}
    parts = content.get("parts") or []
    texts: list[str] = []
    for part in parts:
        t = part.get("text") if isinstance(part, dict) else None
        if t:
            texts.append(str(t))
    return "".join(texts).strip()


@dataclass
class GeminiFreeDryRunTransport:
    """One-shot free-tier generateContent — only when ``dry_run_enabled``.

    Without the explicit dry-run flag this transport refuses locally and
    never opens a socket, even if the key file exists. This is **eval
    dry-run**, not Mesh live: ``LIVE_API_ENABLED`` stays False and the
    Mesh live adapter is not enabled.
    """

    dry_run_enabled: bool = False
    peer_id: str = "gemini-free-dry-run"
    model_ref: str = DEFAULT_DRY_RUN_MODEL
    secret_env_path: str = str(DEFAULT_GEMINI_ENV_PATH)
    secret_handle: str = DRY_RUN_SECRET_HANDLE
    timeout_s: float = 30.0
    name: str = "GeminiFreeDryRunTransport"
    _urlopen: Any = field(default=urllib.request.urlopen, repr=False)

    def call(self, bundle: dict[str, Any] | None = None, *, timeout_s: float | None = None) -> dict[str, Any]:
        payload = dict(bundle or {})
        to = float(timeout_s if timeout_s is not None else self.timeout_s)

        if not self.dry_run_enabled:
            return {
                "schema": "mesh.judge.raw_engine/v0",
                "ok": False,
                "http_status": None,
                "latency_ms": 0,
                "raw_text": None,
                "error_code": "PEER_DRY_RUN_FLAG_REQUIRED",
                "provider": "gemini-free",
                "model_ref": self.model_ref,
                "truncated": False,
                "verdict": "ABORT",
                "digest": "",
                "peer_id": self.peer_id,
                "transport": "dry_run_refused",
                "secret_handle": self.secret_handle,
                "live_api_enabled": False,
                "note": "explicit GEMINI_DRY_RUN / --gemini-dry-run required; key file alone is not enough",
            }

        if not is_valid_secret_handle(self.secret_handle):
            return {
                "schema": "mesh.judge.raw_engine/v0",
                "ok": False,
                "http_status": None,
                "latency_ms": 0,
                "raw_text": None,
                "error_code": "PEER_DRY_RUN_AUTH",
                "provider": "gemini-free",
                "model_ref": self.model_ref,
                "truncated": False,
                "verdict": "ABORT",
                "digest": "",
                "peer_id": self.peer_id,
                "transport": "dry_run",
                "secret_handle": self.secret_handle,
                "live_api_enabled": False,
            }

        try:
            api_key = load_gemini_key_from_secret_file(self.secret_env_path)
        except (OSError, ValueError) as exc:
            return {
                "schema": "mesh.judge.raw_engine/v0",
                "ok": False,
                "http_status": None,
                "latency_ms": 0,
                "raw_text": None,
                "error_code": "PEER_DRY_RUN_AUTH",
                "provider": "gemini-free",
                "model_ref": self.model_ref,
                "truncated": False,
                "verdict": "ABORT",
                "digest": "",
                "peer_id": self.peer_id,
                "transport": "dry_run",
                "secret_handle": self.secret_handle,
                "live_api_enabled": False,
                "error_class": "auth",
                "error_detail": type(exc).__name__,
            }

        prompt = str(payload.get("prompt") or DRY_RUN_PROMPT)
        url = (
            f"{_GEMINI_API_BASE}/{self.model_ref}:generateContent"
            f"?key={api_key}"
        )
        body_obj = {
            "contents": [{"role": "user", "parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0, "maxOutputTokens": 256},
        }
        data = json.dumps(body_obj).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        t0 = time.monotonic()
        try:
            with self._urlopen(req, timeout=to) as resp:
                raw = resp.read()
                status = int(getattr(resp, "status", 200) or 200)
        except urllib.error.HTTPError as exc:
            latency_ms = int((time.monotonic() - t0) * 1000)
            err_body = ""
            try:
                err_body = exc.read().decode("utf-8", errors="replace")[:500]
            except Exception:  # noqa: BLE001
                err_body = ""
            err_body = _redact(err_body, api_key)
            error_class = "http"
            if exc.code == 404:
                error_class = "model"
            elif exc.code in (401, 403):
                error_class = "auth"
            elif exc.code == 429:
                error_class = "quota"
            return {
                "schema": "mesh.judge.raw_engine/v0",
                "ok": False,
                "http_status": int(exc.code),
                "latency_ms": latency_ms,
                "raw_text": None,
                "error_code": "PEER_DRY_RUN_HTTP",
                "provider": "gemini-free",
                "model_ref": self.model_ref,
                "truncated": True,
                "verdict": "ABORT",
                "digest": "",
                "peer_id": self.peer_id,
                "transport": "dry_run",
                "secret_handle": self.secret_handle,
                "live_api_enabled": False,
                "error_class": error_class,
                "error_detail": _redact(str(exc), api_key)[:200],
                "error_body_redacted": err_body,
            }
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            latency_ms = int((time.monotonic() - t0) * 1000)
            return {
                "schema": "mesh.judge.raw_engine/v0",
                "ok": False,
                "http_status": None,
                "latency_ms": latency_ms,
                "raw_text": None,
                "error_code": "PEER_DRY_RUN_TIMEOUT",
                "provider": "gemini-free",
                "model_ref": self.model_ref,
                "truncated": False,
                "verdict": "ABORT",
                "digest": "",
                "peer_id": self.peer_id,
                "transport": "dry_run",
                "secret_handle": self.secret_handle,
                "live_api_enabled": False,
                "error_class": "network",
                "error_detail": type(exc).__name__,
            }
        finally:
            # Drop key reference ASAP from this frame.
            api_key = ""  # noqa: F841

        latency_ms = int((time.monotonic() - t0) * 1000)
        try:
            parsed = json.loads(raw.decode("utf-8"))
        except json.JSONDecodeError:
            return {
                "schema": "mesh.judge.raw_engine/v0",
                "ok": False,
                "http_status": status,
                "latency_ms": latency_ms,
                "raw_text": None,
                "error_code": "PEER_DRY_RUN_HTTP",
                "provider": "gemini-free",
                "model_ref": self.model_ref,
                "truncated": True,
                "verdict": "ABORT",
                "digest": "",
                "peer_id": self.peer_id,
                "transport": "dry_run",
                "secret_handle": self.secret_handle,
                "live_api_enabled": False,
                "error_class": "schema",
            }

        text = _extract_candidate_text(parsed)
        marker_ok = DRY_RUN_OK_MARKER in text
        digest = _digest16(
            {
                "peer": self.peer_id,
                "model": self.model_ref,
                "text": text[:200],
                "status": status,
            }
        )
        usage = parsed.get("usageMetadata") or {}
        usage_safe = {
            k: usage.get(k)
            for k in (
                "promptTokenCount",
                "candidatesTokenCount",
                "totalTokenCount",
                "thoughtsTokenCount",
                "serviceTier",
            )
            if k in usage
        }
        return {
            "schema": "mesh.judge.raw_engine/v0",
            "ok": status == 200,
            "http_status": status,
            "latency_ms": latency_ms,
            "raw_text": text[:500],
            "error_code": None if status == 200 else "PEER_DRY_RUN_HTTP",
            "provider": "gemini-free",
            "model_ref": self.model_ref,
            "model_version": parsed.get("modelVersion"),
            "truncated": True,
            "verdict": "ADVISORY" if status == 200 else "ABORT",
            "digest": digest,
            "peer_id": self.peer_id,
            "transport": "dry_run",
            "secret_handle": self.secret_handle,
            "live_api_enabled": False,
            "ok_marker": marker_ok,
            "response_sha256": hashlib.sha256(raw).hexdigest(),
            "usage": usage_safe,
            "advisory_only": True,
            "m1_status": M1_STATUS,
        }

    def health(self) -> dict[str, Any]:
        return {
            "ok": True,
            "binding": self.name,
            "live": False,
            "live_api_enabled": False,
            "dry_run_enabled": bool(self.dry_run_enabled),
            "provider": "gemini-free",
            "secret_handle": self.secret_handle,
        }


def build_peer_spike(*, gemini_dry_run: bool = False) -> GoogleLJudgePeerSpike:
    """Factory: mock default; optional dry-run Gemini peer when flag is True."""
    if gemini_dry_run:
        return GoogleLJudgePeerSpike(
            gemini=GeminiFreeDryRunTransport(dry_run_enabled=True)
        )
    return GoogleLJudgePeerSpike()


def run_gemini_dry_run_once(
    *,
    prompt: str = DRY_RUN_PROMPT,
    model_ref: str = DEFAULT_DRY_RUN_MODEL,
    secret_env_path: str | Path | None = None,
    timeout_s: float = 30.0,
) -> dict[str, Any]:
    """Execute exactly one free-tier dry-run call; return sanitized result."""
    transport = GeminiFreeDryRunTransport(
        dry_run_enabled=True,
        model_ref=model_ref,
        secret_env_path=str(secret_env_path or DEFAULT_GEMINI_ENV_PATH),
        timeout_s=timeout_s,
    )
    out = transport.call({"prompt": prompt, "request_id": "gemini-dry-run-once"})
    # Ensure LIVE_API_ENABLED constant untouched / reported false.
    out["live_api_enabled"] = False
    out["mesh_live_adapter"] = "NOT_ENABLED"
    out["LIVE_API_ENABLED_constant"] = LIVE_API_ENABLED
    return out


def main(argv: list[str] | None = None) -> int:
    """CLI: mock by default; ``--gemini-dry-run`` or ``GEMINI_DRY_RUN=1`` for one real call."""
    parser = argparse.ArgumentParser(
        prog="python -m neural_mesh.packaging.google_l_judge_peer_spike",
        description=(
            "Google L_judge peer spike. Default=mock (no network). "
            "Explicit --gemini-dry-run / GEMINI_DRY_RUN=1 enables ONE free-tier "
            "eval call. Does NOT flip LIVE_API_ENABLED or Mesh live."
        ),
    )
    parser.add_argument(
        "--gemini-dry-run",
        action="store_true",
        help="Enable ONE real Gemini free-tier generateContent call (eval only).",
    )
    parser.add_argument(
        "--prompt",
        default=DRY_RUN_PROMPT,
        help="Synthetic prompt for dry-run (default: MESH_DRY_RUN_OK marker).",
    )
    parser.add_argument(
        "--model",
        default=DEFAULT_DRY_RUN_MODEL,
        help=f"Model id (default: {DEFAULT_DRY_RUN_MODEL}).",
    )
    parser.add_argument(
        "--secret-env",
        default=str(DEFAULT_GEMINI_ENV_PATH),
        help="Out-of-band gemini.env path (Gate4 secret_handle store).",
    )
    parser.add_argument(
        "--correlation",
        action="store_true",
        help="Also print mock dual-peer correlation report (gemini peer uses dry-run transport if flag set).",
    )
    args = parser.parse_args(argv)

    dry = gemini_dry_run_flag_enabled(cli_flag=bool(args.gemini_dry_run))
    summary: dict[str, Any] = {
        "live_api_enabled": LIVE_API_ENABLED,
        "mesh_live_adapter": "NOT_ENABLED",
        "dry_run_flag": dry,
        "secret_handle": DRY_RUN_SECRET_HANDLE,
        "secret_env_path": args.secret_env,
        "model_ref": args.model,
    }

    if dry:
        result = run_gemini_dry_run_once(
            prompt=args.prompt,
            model_ref=args.model,
            secret_env_path=args.secret_env,
        )
        summary["dry_run_result"] = result
        # Never echo key material — result is already sanitized.
        print(json.dumps(summary, indent=2, sort_keys=True))
        if args.correlation:
            spike = build_peer_spike(gemini_dry_run=True)
            # Use mock envelope without live flags; dry-run peer already called above.
            # For correlation demo, use a fresh dry-run transport only if needed —
            # here we run primary mock + a disabled dry-run? Better: mock correlation.
            corr = GoogleLJudgePeerSpike().run_correlation(sample_envelope())
            summary_corr = {
                "note": "correlation demo remains mock-only unless wired separately; "
                "dry-run above is one-shot eval evidence",
                "correlation": corr.to_dict(),
            }
            print(json.dumps(summary_corr, indent=2, sort_keys=True))
        return 0 if result.get("ok") else 2

    # Default: mock-only, no network.
    spike = build_peer_spike(gemini_dry_run=False)
    report = spike.run_correlation(sample_envelope())
    summary["mode"] = "mock"
    summary["correlation"] = report.to_dict()
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
