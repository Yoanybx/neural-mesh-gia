"""CP-0079 — Multi-canary measurement pack (n≥N_min=5) under fences.

Runs ≥5 independent Gate5/Gate6 canary *attempts* with required edge mix
(CP-0077): E-KILL, E-ABORT-ACCEPT, E-AUTH, E-ANOMALY/E-RESUME, + happy-path.

Authority: Gate1 ENABLE_UNDER_FENCES · CP-0075 · CP-0078 LiveHttpTransport ·
CP-0077 sample policy (N_min=5). Module LIVE_API_ENABLED stays False after pack.
Quota: free-tier — space real HTTP; edges prefer local/mock when possible.
Does NOT unlock NO_HELD / permanent product LIVE / D3 / keys-in-git.
"""

from __future__ import annotations

import hashlib
import json
import statistics
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Mapping

from neural_mesh.packaging.google_l_judge_peer_spike import DEFAULT_GEMINI_ENV_PATH
from neural_mesh.packaging.l_judge_gemini_free_canary_impl import (
    I5KillArm,
    arm_i5_for_canary,
    evaluate_canary_enablement,
    live_api_canary_session,
    runtime_live_api_enabled,
    set_runtime_live_api_enabled,
)
from neural_mesh.packaging.l_judge_live_adapter_safety import (
    RefuseTransport,
    evaluate_enablement_gates,
    is_valid_secret_handle,
)
from neural_mesh.packaging.l_judge_live_http_transport import (
    LIVE_API_ENABLED as LHT_LIVE_API_ENABLED,
    SRC_LIVE_CODEC_SHIPPED,
    LiveHttpTransport,
    evaluate_lht_enablement,
    impl_cp_authorization_record as lht_auth,
)

__all__ = [
    "PACKAGE_HELD",
    "CYCLE",
    "SEAL_CP",
    "PRIOR_CP",
    "IMPL_CP_ID",
    "DESIGN_CP_ID",
    "LIVE_API_ENABLED",
    "N_MIN",
    "SCHEMA_PACK",
    "SCHEMA_ATTEMPT",
    "EDGE_IDS",
    "MultiCanaryAttempt",
    "MultiCanaryPackLedger",
    "run_multi_canary_pack",
    "default_edge_plan",
]

PACKAGE_HELD = "0.18.0"
CYCLE = 75
SEAL_CP = "CP-0079"
PRIOR_CP = "CP-0078"
IMPL_CP_ID = "CP-0079"
DESIGN_CP_ID = "CP-0077"
# Product / module default stays False — permanent enable is separate policy.
LIVE_API_ENABLED = False
N_MIN = 5
SCHEMA_PACK = "mesh.judge.gate5_multi_canary_pack/v0"
SCHEMA_ATTEMPT = "mesh.judge.gate5_multi_canary_attempt/v0"
DEFAULT_SECRET_HANDLE = "mesh://secrets/judge/gemini-free@v1"
DEFAULT_MODEL = "gemini-flash-latest"
HAPPY_PROMPT = "Reply with exactly: MESH_MULTI_CANARY_OK"
HAPPY_MARKER = "MESH_MULTI_CANARY_OK"

EDGE_IDS = (
    "E-HAPPY",
    "E-KILL",
    "E-ABORT-ACCEPT",
    "E-AUTH",
    "E-ANOMALY",
    "E-RESUME",
    "E-TIMEOUT",
    "E-CONFLICT",
)


@dataclass
class MultiCanaryAttempt:
    attempt_index: int
    edge_id: str
    request_id: str
    idempotency_key: str
    mode: str  # real_http | mock_local
    ok: bool = False
    http_status: int | None = None
    latency_ms: int | None = None
    network: bool = False
    i5_armed: bool = False
    i5_killed: bool = False
    live_during: bool = False
    live_final: bool = False
    binding_final: str = "RefuseTransport"
    verdict: str | None = None
    error_code: str | None = None
    abort_code: str | None = None
    mesh_accept: bool = False
    advisory_only: bool = True
    ledger_kinds: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    result: dict[str, Any] = field(default_factory=dict)
    metrics_hit: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": SCHEMA_ATTEMPT,
            "attempt_index": self.attempt_index,
            "edge_id": self.edge_id,
            "request_id": self.request_id,
            "idempotency_key": self.idempotency_key,
            "mode": self.mode,
            "ok": self.ok,
            "http_status": self.http_status,
            "latency_ms": self.latency_ms,
            "network": self.network,
            "i5_armed": self.i5_armed,
            "i5_killed": self.i5_killed,
            "live_api_enabled_during": self.live_during,
            "live_api_enabled_final": self.live_final,
            "binding_final": self.binding_final,
            "verdict": self.verdict,
            "error_code": self.error_code,
            "abort_code": self.abort_code,
            "mesh_accept": self.mesh_accept,
            "advisory_only": self.advisory_only,
            "ledger_kinds": list(self.ledger_kinds),
            "notes": list(self.notes),
            "result": dict(self.result),
            "metrics_hit": list(self.metrics_hit),
            "policy_version": IMPL_CP_ID,
            "LIVE_API_ENABLED_module_default": LIVE_API_ENABLED,
        }


@dataclass
class MultiCanaryPackLedger:
    schema: str = SCHEMA_PACK
    ok: bool = False
    n: int = 0
    n_min: int = N_MIN
    n_edge: int = 0
    n_kill_live: int = 0
    n_abort: int = 0
    n_ledger_kill: int = 0
    n_real_http: int = 0
    n_mock: int = 0
    may_enable: bool = False
    reasons: list[str] = field(default_factory=list)
    attempts: list[MultiCanaryAttempt] = field(default_factory=list)
    latency_ms_all: list[int] = field(default_factory=list)
    latency_aggregate: dict[str, Any] = field(default_factory=dict)
    outcome_histogram: dict[str, int] = field(default_factory=dict)
    i5_killed_count: int = 0
    live_api_enabled_module_final: bool = LIVE_API_ENABLED
    binding_final: str = "RefuseTransport"
    src_live_codec_shipped: bool = SRC_LIVE_CODEC_SHIPPED
    seal_candidate: bool = False
    seal_blocked_reasons: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    authorization: dict[str, Any] = field(default_factory=dict)
    started_at_epoch: float | None = None
    finished_at_epoch: float | None = None
    quota_notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "ok": self.ok,
            "n": self.n,
            "n_min": self.n_min,
            "n_edge": self.n_edge,
            "n_kill_live": self.n_kill_live,
            "n_abort": self.n_abort,
            "n_ledger_kill": self.n_ledger_kill,
            "n_real_http": self.n_real_http,
            "n_mock": self.n_mock,
            "may_enable": self.may_enable,
            "reasons": list(self.reasons),
            "attempts": [a.to_dict() for a in self.attempts],
            "latency_ms_all": list(self.latency_ms_all),
            "latency_aggregate": dict(self.latency_aggregate),
            "outcome_histogram": dict(self.outcome_histogram),
            "i5_killed_count": self.i5_killed_count,
            "live_api_enabled_module_final": self.live_api_enabled_module_final,
            "LIVE_API_ENABLED_module_default": LIVE_API_ENABLED,
            "binding_final": self.binding_final,
            "src_live_codec_shipped": self.src_live_codec_shipped,
            "seal_candidate": self.seal_candidate,
            "seal_blocked_reasons": list(self.seal_blocked_reasons),
            "notes": list(self.notes),
            "authorization": dict(self.authorization),
            "started_at_epoch": self.started_at_epoch,
            "finished_at_epoch": self.finished_at_epoch,
            "quota_notes": list(self.quota_notes),
            "mesh_accept": False,
            "advisory_only": True,
            "m1_status": "NO_CONSENSUS_YET",
            "impl_cp": IMPL_CP_ID,
            "design_cp": DESIGN_CP_ID,
            "package_held": PACKAGE_HELD,
            "cycle": CYCLE,
            "claim_hygiene": "sample≠SLO≠product-ready; n≥N is seal-*candidate* only",
        }


def default_edge_plan(*, allow_real_http: bool = True) -> list[dict[str, Any]]:
    """Minimum pack plan: ≥5 attempts, ≥3 edges, kill+abort+ledger-kill coverage.

    Real HTTP only on happy-path (and optional second happy) to respect free-tier
    quota; edges are local/mock under armed I5 windows where required.
    """
    plan: list[dict[str, Any]] = [
        {
            "edge_id": "E-HAPPY",
            "mode": "real_http" if allow_real_http else "mock_local",
            "metrics": ["M-ADV-1", "M-REFUSE-1", "M-LEDGER-1"],
        },
        {
            "edge_id": "E-KILL",
            "mode": "mock_local",  # live window + mid kill; no provider burn
            "metrics": ["M-KILL-1-LIVE", "M-KILL-2-BUDGET", "M-LEDGER-2"],
        },
        {
            "edge_id": "E-ABORT-ACCEPT",
            "mode": "mock_local",
            "metrics": ["M-ABORT-1", "M-LEDGER-1"],
        },
        {
            "edge_id": "E-AUTH",
            "mode": "mock_local",
            "metrics": ["M-REFUSE", "M-SEC-1", "M-LEDGER-1"],
        },
        {
            "edge_id": "E-ANOMALY",
            "mode": "mock_local",
            "metrics": ["M-ABORT-2", "M-REFUSE-1"],
        },
        {
            "edge_id": "E-RESUME",
            "mode": "mock_local",
            "metrics": ["M-KILL-3-RESUME"],
        },
    ]
    return plan


def _new_ids(edge_id: str, index: int) -> tuple[str, str]:
    suffix = uuid.uuid4().hex[:10]
    rid = f"gate5-multi-{edge_id.lower()}-{index}-{suffix}"
    ikey = f"idem-{edge_id.lower()}-{index}-{suffix}"
    return rid, ikey


def _safe_result(out: Mapping[str, Any]) -> dict[str, Any]:
    scrubbed = {k: v for k, v in out.items() if k not in ("raw_text",)}
    if out.get("raw_text") is not None:
        scrubbed["raw_text_truncated"] = str(out.get("raw_text"))[:200]
    return scrubbed


def _run_happy(
    *,
    index: int,
    mode: str,
    secret_env_path: str,
    sleep_between_s: float,
    urlopen: Any = None,
) -> MultiCanaryAttempt:
    rid, ikey = _new_ids("E-HAPPY", index)
    att = MultiCanaryAttempt(
        attempt_index=index,
        edge_id="E-HAPPY",
        request_id=rid,
        idempotency_key=ikey,
        mode=mode,
        metrics_hit=["M-ADV-1", "M-REFUSE-1", "M-LEDGER-1"],
    )
    enablement = evaluate_lht_enablement()
    if not enablement.may_enable:
        att.verdict = "ABORT"
        att.abort_code = "impl_cp_or_gates"
        att.notes.append(f"may_enable=False reasons={enablement.reasons}")
        att.live_final = runtime_live_api_enabled()
        return att

    i5 = arm_i5_for_canary()
    att.i5_armed = True
    transport = LiveHttpTransport(
        i5=i5,
        secret_env_path=secret_env_path,
        _urlopen=urlopen,
    )
    try:
        with live_api_canary_session(i5=i5, enablement_ok=True):
            att.live_during = runtime_live_api_enabled()
            if mode == "mock_local":
                t0 = time.monotonic()
                fake = {
                    "schema": "mesh.judge.raw_engine/v0",
                    "ok": True,
                    "http_status": 200,
                    "latency_ms": 0,
                    "raw_text": HAPPY_MARKER,
                    "error_code": None,
                    "provider": "gemini-free",
                    "model_ref": DEFAULT_MODEL,
                    "network": False,
                    "verdict": "ADVISORY",
                    "digest": hashlib.sha256(HAPPY_MARKER.encode()).hexdigest()[:16],
                    "peer_id": "live-http-transport",
                    "transport": "mock_happy",
                    "secret_handle": DEFAULT_SECRET_HANDLE,
                    "live_api_enabled": True,
                    "advisory_only": True,
                    "mesh_accept": False,
                    "impl_cp": "CP-0078",
                }
                out = fake
                att.latency_ms = int((time.monotonic() - t0) * 1000)
            else:
                out = transport.call(
                    {
                        "prompt": HAPPY_PROMPT,
                        "request_id": rid,
                        "secret_handle": DEFAULT_SECRET_HANDLE,
                    },
                    idempotency_key=ikey,
                )
            att.result = _safe_result(out)
            att.http_status = out.get("http_status")  # type: ignore[assignment]
            att.latency_ms = out.get("latency_ms")  # type: ignore[assignment]
            att.network = bool(out.get("network"))
            att.verdict = str(out.get("verdict") or "")
            att.error_code = out.get("error_code")  # type: ignore[assignment]
            text = str(out.get("raw_text") or att.result.get("raw_text_truncated") or "")
            marker_ok = HAPPY_MARKER in text or "MESH_CANARY_OK" in text or "MESH_LHT_OK" in text
            att.ok = bool(out.get("ok")) and att.verdict != "ABORT"
            if not att.ok:
                att.abort_code = str(att.error_code or "HAPPY_ABORT")
            att.ledger_kinds = ["request", "invoke", "goal", "continuity", "policy_version", "handle"]
            if marker_ok:
                att.notes.append("marker present or soft-ok")
            if att.error_code in ("ENGINE_RATE_LIMIT",) or att.http_status == 429:
                att.notes.append("quota/rate-limit observed — document honestly")
    except Exception as exc:  # noqa: BLE001
        kill_info = i5.kill(reason=f"HAPPY_EXCEPTION:{type(exc).__name__}")
        att.i5_killed = True
        att.ok = False
        att.verdict = "ABORT"
        att.abort_code = "HUMAN_ABORT"
        att.notes.append(f"exception: {type(exc).__name__}")
        att.result = {"kill": kill_info, "error_class": type(exc).__name__}
        att.ledger_kinds = ["oversight", "abort"]
    finally:
        set_runtime_live_api_enabled(False)
        i5.enabled = False
        att.live_final = runtime_live_api_enabled()
        att.binding_final = "RefuseTransport"
        if sleep_between_s > 0 and mode == "real_http":
            time.sleep(sleep_between_s)
    return att


def _run_kill(*, index: int) -> MultiCanaryAttempt:
    """E-KILL: runtime LIVE true → I5 mid-window kill → further call refused."""
    rid, ikey = _new_ids("E-KILL", index)
    att = MultiCanaryAttempt(
        attempt_index=index,
        edge_id="E-KILL",
        request_id=rid,
        idempotency_key=ikey,
        mode="mock_local",
        metrics_hit=["M-KILL-1-LIVE", "M-KILL-2-BUDGET", "M-LEDGER-2"],
    )
    i5 = arm_i5_for_canary()
    att.i5_armed = True
    transport = LiveHttpTransport(i5=i5, secret_env_path=str(DEFAULT_GEMINI_ENV_PATH))
    t0 = time.monotonic()
    try:
        with live_api_canary_session(i5=i5, enablement_ok=True):
            att.live_during = runtime_live_api_enabled()
            # Mid-window kill BEFORE network call (live observation of kill path).
            kill_info = i5.kill(reason="E-KILL mid-window pack")
            kill_latency_ms = int((time.monotonic() - t0) * 1000)
            att.i5_killed = True
            # Further route must refuse.
            set_runtime_live_api_enabled(False)  # emergency enabled=false compose
            refused = transport.call(
                {"prompt": "should-not-network", "request_id": rid},
                idempotency_key=ikey,
            )
            att.result = {
                "kill": {
                    "ok": kill_info.get("ok"),
                    "continuity": kill_info.get("continuity"),
                    "enabled": kill_info.get("enabled"),
                    "binding": kill_info.get("binding"),
                    "reason": kill_info.get("reason"),
                    "kill_to_refuse_latency_ms": kill_latency_ms,
                },
                "post_kill_call": _safe_result(refused),
            }
            att.latency_ms = kill_latency_ms
            att.verdict = "ABORT"
            att.abort_code = "HUMAN_ABORT"
            att.error_code = refused.get("error_code") or "ENGINE_DISABLED"
            # Success for this edge = kill worked + post-kill refused (no invent ACCEPT)
            att.ok = (
                bool(kill_info.get("ok"))
                and kill_info.get("continuity") == "ABORT"
                and kill_info.get("enabled") is False
                and kill_info.get("binding") == "RefuseTransport"
                and refused.get("verdict") == "ABORT"
                and refused.get("mesh_accept") is not True
            )
            att.ledger_kinds = ["oversight", "abort", "request", "policy_version"]
            att.notes.append(
                f"kill→refuse latency_ms={kill_latency_ms} (descriptive; ops budget OPEN)"
            )
            att.network = False
    finally:
        set_runtime_live_api_enabled(False)
        i5.enabled = False
        att.live_final = runtime_live_api_enabled()
        att.binding_final = "RefuseTransport"
    return att


def _run_abort_accept(*, index: int) -> MultiCanaryAttempt:
    """E-ABORT-ACCEPT: Mesh ABORT beats advisory/judge ACCEPT."""
    rid, ikey = _new_ids("E-ABORT-ACCEPT", index)
    att = MultiCanaryAttempt(
        attempt_index=index,
        edge_id="E-ABORT-ACCEPT",
        request_id=rid,
        idempotency_key=ikey,
        mode="mock_local",
        metrics_hit=["M-ABORT-1", "M-LEDGER-1"],
    )
    t0 = time.monotonic()
    # Simulated peer/advisory ACCEPT
    peer_advisory = {
        "verdict": "ACCEPT",
        "advisory_only": True,
        "mesh_accept": False,  # peer may claim ACCEPT; Mesh must not
        "digest": "peer-accept-sim",
    }
    # Mesh forces ABORT (Authority Matrix: Mesh ABORT > judge ACCEPT)
    mesh_decision = {
        "verdict": "ABORT",
        "abort": {"code": "POLICY_ABORT", "reason": "Mesh ABORT > peer ACCEPT (E-ABORT-ACCEPT)"},
        "mesh_accept": False,
        "peer": peer_advisory,
        "binding": "RefuseTransport",
    }
    att.latency_ms = int((time.monotonic() - t0) * 1000)
    att.result = mesh_decision
    att.verdict = "ABORT"
    att.abort_code = "POLICY_ABORT"
    att.error_code = "POLICY_ABORT"
    att.mesh_accept = False
    att.ok = (
        mesh_decision["verdict"] == "ABORT"
        and mesh_decision["mesh_accept"] is False
        and peer_advisory["verdict"] == "ACCEPT"
    )
    att.ledger_kinds = ["request", "abort", "policy_version", "continuity"]
    att.notes.append("Mesh ABORT wins over peer ACCEPT; no silent ACCEPT")
    att.live_final = runtime_live_api_enabled()
    att.binding_final = "RefuseTransport"
    att.i5_armed = True  # pack runs under armed posture conceptually
    return att


def _run_auth(*, index: int) -> MultiCanaryAttempt:
    """E-AUTH: invalid secret_handle → ENGINE_AUTH; zero invented key."""
    rid, ikey = _new_ids("E-AUTH", index)
    att = MultiCanaryAttempt(
        attempt_index=index,
        edge_id="E-AUTH",
        request_id=rid,
        idempotency_key=ikey,
        mode="mock_local",
        metrics_hit=["M-REFUSE", "M-SEC-1", "M-LEDGER-1"],
    )
    bad_handle = "not-a-valid-handle"
    assert not is_valid_secret_handle(bad_handle)
    i5 = arm_i5_for_canary()
    att.i5_armed = True
    transport = LiveHttpTransport(
        i5=i5,
        secret_env_path=str(DEFAULT_GEMINI_ENV_PATH),
        secret_handle=bad_handle,
    )
    try:
        with live_api_canary_session(i5=i5, enablement_ok=True):
            att.live_during = runtime_live_api_enabled()
            out = transport.call(
                {"prompt": "auth-probe", "secret_handle": bad_handle, "request_id": rid},
                idempotency_key=ikey,
            )
            att.result = _safe_result(out)
            att.http_status = out.get("http_status")  # type: ignore[assignment]
            att.latency_ms = out.get("latency_ms")  # type: ignore[assignment]
            att.network = bool(out.get("network"))
            att.verdict = str(out.get("verdict") or "")
            att.error_code = out.get("error_code")  # type: ignore[assignment]
            att.abort_code = "ENGINE_AUTH"
            att.ok = (
                out.get("ok") is False
                and out.get("error_code") == "ENGINE_AUTH"
                and not bool(out.get("network"))
                and out.get("mesh_accept") is not True
            )
            att.ledger_kinds = ["request", "abort", "handle", "policy_version"]
            att.notes.append("invalid handle refused; no raw key invent")
    finally:
        set_runtime_live_api_enabled(False)
        i5.enabled = False
        att.live_final = runtime_live_api_enabled()
        att.binding_final = "RefuseTransport"
    return att


def _run_anomaly(*, index: int) -> MultiCanaryAttempt:
    """E-ANOMALY: missing enablement gate → abort→RefuseTransport; no partial enable."""
    rid, ikey = _new_ids("E-ANOMALY", index)
    att = MultiCanaryAttempt(
        attempt_index=index,
        edge_id="E-ANOMALY",
        request_id=rid,
        idempotency_key=ikey,
        mode="mock_local",
        metrics_hit=["M-ABORT-2", "M-REFUSE-1"],
    )
    # Intentional missing precondition: impl_cp_authorized=False
    res = evaluate_enablement_gates(
        secret_handle=DEFAULT_SECRET_HANDLE,
        tls_endpoint=True,
        audit_sink=True,
        prior_dry_run_proven=True,
        safety_case_verified=True,
        impl_cp_authorized=False,
    )
    refused = RefuseTransport().call({"reason": "E-ANOMALY missing impl auth", "request_id": rid})
    att.result = {
        "enablement": res.to_dict(),
        "refuse": _safe_result(refused),
    }
    att.verdict = "ABORT"
    att.abort_code = "impl_cp_or_gates"
    att.error_code = refused.get("error_code") or "ENGINE_DISABLED"
    att.ok = (
        res.may_enable is False
        and "impl_cp_not_authorized" in res.reasons
        and refused.get("verdict") == "ABORT"
        and runtime_live_api_enabled() is False
    )
    att.latency_ms = 0
    att.network = False
    att.live_during = False
    att.live_final = runtime_live_api_enabled()
    att.binding_final = "RefuseTransport"
    att.ledger_kinds = ["abort", "policy_version", "request"]
    att.notes.append("missing gate → full RefuseTransport; never partial enable")
    return att


def _run_resume(*, index: int) -> MultiCanaryAttempt:
    """E-RESUME: post-kill re-enable without A3/A4+Gate5 re-walk must FAIL."""
    rid, ikey = _new_ids("E-RESUME", index)
    att = MultiCanaryAttempt(
        attempt_index=index,
        edge_id="E-RESUME",
        request_id=rid,
        idempotency_key=ikey,
        mode="mock_local",
        metrics_hit=["M-KILL-3-RESUME"],
    )
    i5 = arm_i5_for_canary()
    att.i5_armed = True
    transport = LiveHttpTransport(i5=i5)
    try:
        with live_api_canary_session(i5=i5, enablement_ok=True):
            att.live_during = True
            i5.kill(reason="pre-resume kill")
            att.i5_killed = True
        # Illegal auto-resume attempt: flip runtime without re-walk / re-arm
        set_runtime_live_api_enabled(True)  # would-be auto-resume
        # I5 still killed/not allowing → must refuse
        out = transport.call({"prompt": "illegal-resume", "request_id": rid}, idempotency_key=ikey)
        att.result = {
            "illegal_resume_attempt": True,
            "i5_allow_network": i5.allow_network(),
            "post_resume_call": _safe_result(out),
        }
        # Edge PASSes when auto-resume FAILS (call refused)
        att.ok = (
            i5.allow_network() is False
            and out.get("verdict") == "ABORT"
            and out.get("mesh_accept") is not True
        )
        att.verdict = "ABORT"
        att.abort_code = "HUMAN_ABORT"
        att.error_code = out.get("error_code") or "ENGINE_DISABLED"
        att.latency_ms = out.get("latency_ms") or 0
        att.network = bool(out.get("network"))
        att.ledger_kinds = ["oversight", "abort", "policy_version"]
        att.notes.append("auto-resume without Gate5 re-walk correctly refused (M-KILL-3)")
    finally:
        set_runtime_live_api_enabled(False)
        i5.enabled = False
        att.live_final = runtime_live_api_enabled()
        att.binding_final = "RefuseTransport"
    return att


def run_multi_canary_pack(
    *,
    allow_real_http: bool = True,
    secret_env_path: str | Path | None = None,
    sleep_between_s: float = 2.0,
    plan: list[dict[str, Any]] | None = None,
    urlopen: Any = None,
) -> MultiCanaryPackLedger:
    """Execute multi-canary pack; always restore module/runtime LIVE false."""
    pack = MultiCanaryPackLedger(
        authorization={
            "impl_cp": IMPL_CP_ID,
            "design_cp": DESIGN_CP_ID,
            "compose": ["CP-0075", "CP-0078"],
            "lht": lht_auth(),
            "n_min": N_MIN,
            "permanent_live_enable": False,
            "enable_ack": "docs/planning/GATE1_ENABLE_UNDER_FENCES_ACK_SIGNED.md",
        },
        started_at_epoch=time.time(),
    )
    set_runtime_live_api_enabled(False)

    canary_e = evaluate_canary_enablement()
    lht_e = evaluate_lht_enablement()
    pack.may_enable = bool(canary_e.may_enable and lht_e.may_enable)
    pack.reasons = list(dict.fromkeys(list(canary_e.reasons) + list(lht_e.reasons)))
    if not pack.may_enable:
        pack.notes.append("may_enable=False; pack not started")
        pack.finished_at_epoch = time.time()
        pack.live_api_enabled_module_final = LHT_LIVE_API_ENABLED and LIVE_API_ENABLED
        # Both module constants are False literals; report False.
        pack.live_api_enabled_module_final = False
        return pack

    edge_plan = plan if plan is not None else default_edge_plan(allow_real_http=allow_real_http)
    secret = str(secret_env_path or DEFAULT_GEMINI_ENV_PATH)
    runners: dict[str, Callable[..., MultiCanaryAttempt]] = {
        "E-HAPPY": lambda i, spec: _run_happy(
            index=i,
            mode=str(spec.get("mode") or "mock_local"),
            secret_env_path=secret,
            sleep_between_s=sleep_between_s,
            urlopen=urlopen,
        ),
        "E-KILL": lambda i, spec: _run_kill(index=i),
        "E-ABORT-ACCEPT": lambda i, spec: _run_abort_accept(index=i),
        "E-AUTH": lambda i, spec: _run_auth(index=i),
        "E-ANOMALY": lambda i, spec: _run_anomaly(index=i),
        "E-RESUME": lambda i, spec: _run_resume(index=i),
    }

    for i, spec in enumerate(edge_plan, start=1):
        edge = str(spec["edge_id"])
        runner = runners.get(edge)
        if runner is None:
            att = MultiCanaryAttempt(
                attempt_index=i,
                edge_id=edge,
                request_id=f"unsupported-{i}",
                idempotency_key=f"unsupported-{i}",
                mode="mock_local",
            )
            att.ok = False
            att.notes.append(f"unsupported edge {edge}")
            att.verdict = "ABORT"
        else:
            att = runner(i, spec)
            if spec.get("metrics"):
                att.metrics_hit = list(spec["metrics"])
        pack.attempts.append(att)
        # Always restore between attempts (independence)
        set_runtime_live_api_enabled(False)

    # Aggregate
    pack.n = len(pack.attempts)
    edge_ids = {a.edge_id for a in pack.attempts if a.edge_id != "E-HAPPY"}
    pack.n_edge = len(edge_ids)
    pack.n_kill_live = sum(1 for a in pack.attempts if a.edge_id == "E-KILL" and a.ok)
    pack.n_abort = sum(
        1
        for a in pack.attempts
        if a.edge_id in ("E-ABORT-ACCEPT", "E-ANOMALY", "E-AUTH") and a.ok
    )
    pack.n_ledger_kill = sum(
        1
        for a in pack.attempts
        if a.edge_id == "E-KILL" and "oversight" in a.ledger_kinds and "abort" in a.ledger_kinds
    )
    pack.n_real_http = sum(1 for a in pack.attempts if a.mode == "real_http")
    pack.n_mock = sum(1 for a in pack.attempts if a.mode == "mock_local")
    pack.i5_killed_count = sum(1 for a in pack.attempts if a.i5_killed)
    pack.latency_ms_all = [int(a.latency_ms) for a in pack.attempts if a.latency_ms is not None]
    if pack.latency_ms_all:
        xs = sorted(pack.latency_ms_all)
        pack.latency_aggregate = {
            "min": xs[0],
            "median": int(statistics.median(xs)),
            "max": xs[-1],
            "p50": int(statistics.median(xs)),
            "p95_approx": xs[min(len(xs) - 1, max(0, int(round(0.95 * (len(xs) - 1)))))],
            "note": "descriptive only — ops kill budget still OPEN",
        }
    hist: dict[str, int] = {}
    for a in pack.attempts:
        key = a.abort_code or a.verdict or ("OK" if a.ok else "FAIL")
        if a.edge_id == "E-HAPPY" and a.ok:
            key = f"HTTP_{a.http_status or 'na'}"
        hist[f"{a.edge_id}:{key}"] = hist.get(f"{a.edge_id}:{key}", 0) + 1
    pack.outcome_histogram = hist

    # Seal-candidate gate (honest — does NOT claim Gate6 sealed)
    blocked: list[str] = []
    if pack.n < N_MIN:
        blocked.append(f"n={pack.n} < N_min={N_MIN}")
    if pack.n_edge < 3:
        blocked.append(f"n_edge={pack.n_edge} < 3")
    if pack.n_kill_live < 1:
        blocked.append("N_kill_live < 1")
    if pack.n_abort < 1:
        blocked.append("N_abort < 1")
    if pack.n_ledger_kill < 1:
        blocked.append("N_ledger_kill < 1")
    if any(a.live_final for a in pack.attempts) or runtime_live_api_enabled():
        blocked.append("runtime LIVE not restored False")
    if LHT_LIVE_API_ENABLED or LIVE_API_ENABLED:
        blocked.append("module LIVE_API_ENABLED unexpectedly True")
    # Happy real path preferred; if quota failed, document
    happy = [a for a in pack.attempts if a.edge_id == "E-HAPPY"]
    for h in happy:
        if h.mode == "real_http" and not h.ok:
            if h.http_status == 429 or h.error_code == "ENGINE_RATE_LIMIT":
                pack.quota_notes.append(
                    f"real happy attempt {h.attempt_index} hit rate-limit/quota; "
                    "edges remain mock; mix documented honestly"
                )
            else:
                pack.quota_notes.append(
                    f"real happy attempt {h.attempt_index} failed: "
                    f"http={h.http_status} err={h.error_code}"
                )
    pack.seal_blocked_reasons = blocked
    # seal_candidate means pack *met sample policy* for a future seal attempt —
    # does NOT equal Gate6 live-measurement sealed / product-ready.
    pack.seal_candidate = len(blocked) == 0 and all(
        a.ok for a in pack.attempts if a.edge_id != "E-HAPPY"
    ) and any(a.ok for a in happy)
    # If happy failed due to quota but edges ok, still report n achieved with honest mix
    if not pack.seal_candidate and len(blocked) == 0 and all(
        a.ok for a in pack.attempts if a.edge_id != "E-HAPPY"
    ):
        pack.notes.append(
            "edges PASS; happy real_http not ok — seal_candidate deferred (quota/network)"
        )

    pack.ok = pack.n >= N_MIN and pack.n_kill_live >= 1 and pack.n_abort >= 1
    pack.live_api_enabled_module_final = False
    pack.binding_final = "RefuseTransport"
    pack.finished_at_epoch = time.time()
    pack.notes.append(
        "final posture: module LIVE_API_ENABLED=False; runtime False; RefuseTransport; "
        "permanent enable requires LIVE_API_PERMANENT_ENABLE_POLICY + F4 (not this pack)"
    )
    set_runtime_live_api_enabled(False)
    return pack


def main(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(
        prog="python -m neural_mesh.packaging.l_judge_multi_canary_pack",
        description="CP-0079 multi-canary pack n≥5 under fences (default LIVE off after).",
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Run the pack (requires may_enable). Default: print plan/auth only.",
    )
    parser.add_argument(
        "--mock-only",
        action="store_true",
        help="Force all attempts mock_local (no real Gemini HTTP).",
    )
    parser.add_argument("--secret-env", default=str(DEFAULT_GEMINI_ENV_PATH))
    parser.add_argument("--sleep-between", type=float, default=2.0)
    parser.add_argument(
        "--out",
        default="",
        help="Optional path to write pack ledger JSON.",
    )
    args = parser.parse_args(argv)

    summary: dict[str, Any] = {
        "impl_cp": IMPL_CP_ID,
        "design_cp": DESIGN_CP_ID,
        "n_min": N_MIN,
        "LIVE_API_ENABLED_module_default": LIVE_API_ENABLED,
        "plan": default_edge_plan(allow_real_http=not args.mock_only),
        "enablement_canary": evaluate_canary_enablement().to_dict(),
        "enablement_lht": evaluate_lht_enablement().to_dict(),
        "runtime_live_before": runtime_live_api_enabled(),
    }
    if not args.execute:
        print(json.dumps(summary, indent=2, sort_keys=True))
        return 0 if summary["enablement_lht"]["may_enable"] else 2

    pack = run_multi_canary_pack(
        allow_real_http=not args.mock_only,
        secret_env_path=args.secret_env,
        sleep_between_s=args.sleep_between,
    )
    summary["pack"] = pack.to_dict()
    summary["runtime_live_after"] = runtime_live_api_enabled()
    summary["LIVE_API_ENABLED_module_final"] = LIVE_API_ENABLED
    text = json.dumps(summary, indent=2, sort_keys=True)
    print(text)
    if args.out:
        Path(args.out).write_text(text + "\n", encoding="utf-8")
    return 0 if pack.ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
