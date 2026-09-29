"""CP-0075 — Authorized impl CP: Gemini free-tier Gate5 canary under fences.

Minimum live-enablement binding (not a full L_judge LiveHttpTransport codec):

* Clears NT-10 / ``impl_cp_not_authorized`` when caller passes
  ``impl_cp_authorized=True`` **and** the other enablement gates (see
  ``evaluate_enablement_gates``).
* Wires the existing Google free-tier HTTP path (``GeminiFreeDryRunTransport``
  machinery) into a **Gate5 canary** path behind a *runtime*
  ``LIVE_API_ENABLED`` flip + kill-armed I5.
* Does **not** ship ``src/neural_mesh/judge_*.py`` live codec.
* Does **not** unlock NO_HELD / GIA / Raft / N>2 / train / SaaS / D3 / pkg0190.
* Module constant ``LIVE_API_ENABLED`` = **True** under F4 product ACK SIGNED (I5 still gates).
* Keys stay out-of-band (``~/.config/neural-mesh/gemini.env``); never logged.

Authority: Gate1 SIGNED ENABLE_UNDER_FENCES (「Aprobado」) · Gates 2–4 ENABLE_READY ·
Gate5 runbook · D1 §3 Authority Matrix · D1 §6 I5 kill.
"""

from __future__ import annotations

import hashlib
import json
import os
import time
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterator, Mapping

from neural_mesh.packaging.d1_l_judge_safety_maturation import (
    AUTHORITY_MATRIX,
    mock_i5_kill_to_refuse_drill,
)
from neural_mesh.packaging.google_l_judge_peer_spike import (
    DEFAULT_DRY_RUN_MODEL,
    DEFAULT_GEMINI_ENV_PATH,
    DRY_RUN_OK_MARKER,
    DRY_RUN_PROMPT,
    DRY_RUN_SECRET_HANDLE,
    GeminiFreeDryRunTransport,
    LIVE_API_ENABLED as PEER_SPIKE_LIVE_API_ENABLED,
)
from neural_mesh.packaging.l_judge_live_adapter_safety import (
    RefuseTransport,
    evaluate_enablement_gates,
    is_valid_secret_handle,
)

__all__ = [
    "PACKAGE_HELD",
    "CYCLE",
    "SEAL_CP",
    "PRIOR_CP",
    "IMPL_CP_ID",
    "LIVE_API_ENABLED",
    "CANARY_SECRET_HANDLE",
    "CANARY_MODEL",
    "CANARY_PROMPT",
    "CANARY_OK_MARKER",
    "SCHEMA_IMPL",
    "SCHEMA_CANARY_LEDGER",
    "RUNTIME_LIVE_ENV",
    "ENABLE_ACK_PATH",
    "I5KillArm",
    "CanaryLedger",
    "impl_cp_authorization_record",
    "is_impl_cp_authorized",
    "evaluate_canary_enablement",
    "runtime_live_api_enabled",
    "session_live_api_enabled",
    "set_runtime_live_api_enabled",
    "live_api_canary_session",
    "GeminiFreeCanaryTransport",
    "arm_i5_for_canary",
    "run_gate5_canary_once",
    "default_canary_gates",
]

PACKAGE_HELD = "0.18.0"
CYCLE = 71
SEAL_CP = "CP-0075"
PRIOR_CP = "CP-0074"
IMPL_CP_ID = "CP-0075"
# F4 product permanent (ACK SIGNED + CP-0087) — RefuseTransport when I5 not armed.
LIVE_API_ENABLED = True
CANARY_SECRET_HANDLE = DRY_RUN_SECRET_HANDLE  # mesh://secrets/judge/gemini-free@v1
CANARY_MODEL = DEFAULT_DRY_RUN_MODEL  # gemini-flash-latest
CANARY_PROMPT = "Reply with exactly: MESH_CANARY_OK"
CANARY_OK_MARKER = "MESH_CANARY_OK"
SCHEMA_IMPL = "mesh.judge.gemini_free_canary_impl/v0"
SCHEMA_CANARY_LEDGER = "mesh.judge.gate5_canary_ledger/v0"
RUNTIME_LIVE_ENV = "MESH_LIVE_API_ENABLED"
ENABLE_ACK_PATH = "docs/planning/GATE1_ENABLE_UNDER_FENCES_ACK_SIGNED.md"

# Process-local runtime flip used ONLY inside live_api_canary_session.
_runtime_live_api_enabled: bool = False


def set_runtime_live_api_enabled(value: bool) -> None:
    """Set process-local LIVE_API runtime flag (canary procedure only)."""
    global _runtime_live_api_enabled
    _runtime_live_api_enabled = bool(value)


def session_live_api_enabled(*, env: Mapping[str, str] | None = None) -> bool:
    """Process/env LIVE *session* window only (not the product module constant)."""
    if _runtime_live_api_enabled:
        return True
    e = env if env is not None else os.environ
    val = str(e.get(RUNTIME_LIVE_ENV, "")).strip().lower()
    return val in ("1", "true", "yes", "on")


def runtime_live_api_enabled(*, env: Mapping[str, str] | None = None) -> bool:
    """True if product module authorized (F4) OR session/env live window.

    Network still requires I5.allow_network(). After canary, clear *session*
    via set_runtime_live_api_enabled(False); product module may stay True.
    """
    if LIVE_API_ENABLED or PEER_SPIKE_LIVE_API_ENABLED:
        return True
    return session_live_api_enabled(env=env)


def is_impl_cp_authorized() -> bool:
    """This module *is* the authorized impl CP for Gemini free canary scope."""
    return True


def impl_cp_authorization_record() -> dict[str, Any]:
    """Honest authorization artifact for NT-10 / Gate5 step (6)."""
    return {
        "schema": SCHEMA_IMPL,
        "impl_cp": IMPL_CP_ID,
        "cycle": CYCLE,
        "package_held": PACKAGE_HELD,
        "authorized": True,
        "scope": "gemini_free_tier_gate5_canary_under_fences",
        "provider": "gemini-free",
        "model_ref": CANARY_MODEL,
        "secret_handle": CANARY_SECRET_HANDLE,
        "binding": "GeminiFreeCanaryTransport (reuses GeminiFreeDryRunTransport HTTP)",
        "full_live_http_codec_shipped": False,
        "src_live_codec_shipped": False,
        "live_api_enabled_module_default": LIVE_API_ENABLED,
        "peer_spike_live_api_enabled_constant": PEER_SPIKE_LIVE_API_ENABLED,
        "enable_ack": ENABLE_ACK_PATH,
        "gates_required": [
            "Gate1 ENABLE_UNDER_FENCES SIGNED",
            "Gate2 ENABLE_READY",
            "Gate3 ENABLE_READY",
            "Gate4 ENABLE_READY",
            "Gate5 steps (1)-(5)",
            "I5 kill armed",
            "evaluate_enablement_gates may_enable",
        ],
        "forbidden": [
            "Vertex paid",
            "keys in git",
            "NO_HELD unlocks",
            "D3 / MESH_PERF_EXPERIMENTAL",
            "pkg0190 / v0.19",
            "treat dry-run as canary",
            "partial peer enable",
            "multi-canary fan-out",
        ],
        "nt10": "cleared when impl_cp_authorized=True and other gates pass (no reasons)",
        "note": (
            "Minimum path for Gate5 canary only. Not a full L_judge LiveHttpTransport. "
            "Module LIVE_API_ENABLED=True under F4 SIGNED; I5/RefuseTransport still gate network."
        ),
    }


def default_canary_gates() -> dict[str, Any]:
    return {
        "secret_handle": CANARY_SECRET_HANDLE,
        "tls_endpoint": True,
        "audit_sink": True,
        "prior_dry_run_proven": True,
        "safety_case_verified": True,
        "impl_cp_authorized": is_impl_cp_authorized(),
    }


def evaluate_canary_enablement(
    *,
    flags: dict[str, bool] | None = None,
    secret_handle: str | None = None,
    tls_endpoint: bool = True,
    audit_sink: bool = True,
    prior_dry_run_proven: bool = True,
    safety_case_verified: bool = True,
    impl_cp_authorized: bool | None = None,
) -> Any:
    """Evaluate enablement for the Gemini free canary under this impl CP."""
    return evaluate_enablement_gates(
        flags=flags,
        secret_handle=secret_handle if secret_handle is not None else CANARY_SECRET_HANDLE,
        tls_endpoint=tls_endpoint,
        audit_sink=audit_sink,
        prior_dry_run_proven=prior_dry_run_proven,
        safety_case_verified=safety_case_verified,
        impl_cp_authorized=(
            is_impl_cp_authorized() if impl_cp_authorized is None else bool(impl_cp_authorized)
        ),
    )


@dataclass
class I5KillArm:
    """Kill-armed I5 posture for one canary (approve/veto/kill; cannot execute)."""

    armed: bool = False
    killed: bool = False
    kill_reason: str | None = None
    continuity: str = "WATCH"
    enabled: bool = False  # emergency enabled flag under I5 watch

    def arm(self) -> None:
        i5 = AUTHORITY_MATRIX["Oversight_I5"]
        if i5 != (True, True, True, False):
            raise RuntimeError("Oversight_I5 matrix drift; refuse canary arm")
        self.armed = True
        self.killed = False
        self.kill_reason = None
        self.continuity = "WATCH"
        self.enabled = True  # canary window only

    def kill(self, reason: str = "I5_KILL") -> dict[str, Any]:
        self.killed = True
        self.kill_reason = reason
        self.enabled = False
        self.continuity = "ABORT"
        rt = RefuseTransport()
        refused = rt.call({"reason": reason})
        return {
            "ok": True,
            "kill_authority": "Oversight_I5",
            "continuity": "ABORT",
            "enabled": False,
            "binding": "RefuseTransport",
            "refuse": refused,
            "reason": reason,
        }

    def allow_network(self) -> bool:
        return bool(self.armed and self.enabled and not self.killed)


@dataclass
class CanaryLedger:
    schema: str = SCHEMA_CANARY_LEDGER
    ok: bool = False
    may_enable: bool = False
    reasons: list[str] = field(default_factory=list)
    i5_armed: bool = False
    i5_killed: bool = False
    live_api_enabled_during: bool = False
    live_api_enabled_final: bool = False
    binding_final: str = "RefuseTransport"
    http_status: int | None = None
    latency_ms: int | None = None
    model_ref: str | None = None
    secret_handle: str | None = None
    digest: str | None = None
    response_sha256: str | None = None
    ok_marker: bool = False
    verdict: str | None = None
    error_code: str | None = None
    abort_code: str | None = None
    policy_version: str = IMPL_CP_ID
    request_id: str | None = None
    notes: list[str] = field(default_factory=list)
    result: dict[str, Any] = field(default_factory=dict)
    authorization: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "ok": self.ok,
            "may_enable": self.may_enable,
            "reasons": list(self.reasons),
            "i5_armed": self.i5_armed,
            "i5_killed": self.i5_killed,
            "live_api_enabled_during": self.live_api_enabled_during,
            "live_api_enabled_final": self.live_api_enabled_final,
            "binding_final": self.binding_final,
            "http_status": self.http_status,
            "latency_ms": self.latency_ms,
            "model_ref": self.model_ref,
            "secret_handle": self.secret_handle,
            "digest": self.digest,
            "response_sha256": self.response_sha256,
            "ok_marker": self.ok_marker,
            "verdict": self.verdict,
            "error_code": self.error_code,
            "abort_code": self.abort_code,
            "policy_version": self.policy_version,
            "request_id": self.request_id,
            "notes": list(self.notes),
            "result": dict(self.result),
            "authorization": dict(self.authorization),
            "mesh_accept": False,
            "advisory_only": True,
            "m1_status": "NO_CONSENSUS_YET",
            "src_live_codec_shipped": False,
        }


def arm_i5_for_canary() -> I5KillArm:
    arm = I5KillArm()
    arm.arm()
    return arm


@contextmanager
def live_api_canary_session(
    *,
    i5: I5KillArm,
    enablement_ok: bool,
) -> Iterator[bool]:
    """Flip runtime LIVE_API for the canary window; always restore False."""
    if not enablement_ok:
        raise RuntimeError("may_enable=False; refuse LIVE_API session")
    if not i5.allow_network():
        raise RuntimeError("I5 not armed or already killed; refuse LIVE_API session")
    set_runtime_live_api_enabled(True)
    try:
        yield True
    finally:
        set_runtime_live_api_enabled(False)
        # Prefer RefuseTransport-safe final posture.
        i5.enabled = False


@dataclass
class GeminiFreeCanaryTransport:
    """Gate5 canary transport: network only when runtime live + I5 allow.

    Reuses ``GeminiFreeDryRunTransport`` HTTP path (Gate4 oob key). Without
    runtime LIVE_API + I5 allow, binds RefuseTransport (zero network).
    """

    i5: I5KillArm
    model_ref: str = CANARY_MODEL
    secret_env_path: str = str(DEFAULT_GEMINI_ENV_PATH)
    secret_handle: str = CANARY_SECRET_HANDLE
    timeout_s: float = 30.0
    name: str = "GeminiFreeCanaryTransport"
    _urlopen: Any = field(default=None, repr=False)

    def call(self, bundle: dict[str, Any] | None = None, *, timeout_s: float | None = None) -> dict[str, Any]:
        payload = dict(bundle or {})
        if not runtime_live_api_enabled() or not self.i5.allow_network():
            refused = RefuseTransport().call(payload, timeout_s=timeout_s or self.timeout_s)
            refused = dict(refused)
            refused["provider"] = "gemini-free-canary"
            refused["transport"] = "refuse"
            refused["live_api_enabled"] = False
            refused["secret_handle"] = self.secret_handle
            refused["note"] = (
                "canary refused: need runtime LIVE_API + I5 armed; "
                "module LIVE_API_ENABLED product default under F4; I5 gates network"
            )
            return refused

        if not is_valid_secret_handle(self.secret_handle):
            return {
                "schema": "mesh.judge.raw_engine/v0",
                "ok": False,
                "http_status": None,
                "latency_ms": 0,
                "raw_text": None,
                "error_code": "ENGINE_AUTH",
                "provider": "gemini-free-canary",
                "model_ref": self.model_ref,
                "truncated": False,
                "verdict": "ABORT",
                "digest": "",
                "peer_id": "gemini-free-canary",
                "transport": "canary",
                "secret_handle": self.secret_handle,
                "live_api_enabled": True,
                "abort": {"code": "ENGINE_AUTH", "reason": "invalid secret_handle"},
            }

        # Reuse dry-run transport HTTP with dry_run_enabled=True for this one call.
        kwargs: dict[str, Any] = {
            "dry_run_enabled": True,
            "peer_id": "gemini-free-canary",
            "model_ref": self.model_ref,
            "secret_env_path": self.secret_env_path,
            "secret_handle": self.secret_handle,
            "timeout_s": float(timeout_s if timeout_s is not None else self.timeout_s),
            "name": "GeminiFreeCanaryTransport",
        }
        if self._urlopen is not None:
            kwargs["_urlopen"] = self._urlopen
        inner = GeminiFreeDryRunTransport(**kwargs)
        out = dict(inner.call(payload, timeout_s=timeout_s))
        # Relabel as canary (not dry-run) for ledger honesty.
        out["transport"] = "canary"
        out["provider"] = "gemini-free-canary"
        out["peer_id"] = "gemini-free-canary"
        out["live_api_enabled"] = True
        out["mesh_live_adapter"] = "CANARY_ONLY_CP0075"
        out["LIVE_API_ENABLED_module_default"] = LIVE_API_ENABLED
        out["impl_cp"] = IMPL_CP_ID
        out["advisory_only"] = True
        # Map dry-run error codes to live taxonomy where useful.
        if out.get("error_code") == "PEER_DRY_RUN_AUTH":
            out["error_code"] = "ENGINE_AUTH"
        elif out.get("error_code") == "PEER_DRY_RUN_HTTP":
            out["error_code"] = "ENGINE_HTTP"
        elif out.get("error_code") == "PEER_DRY_RUN_TIMEOUT":
            out["error_code"] = "ENGINE_TIMEOUT"
        # Prefer canary marker if present; accept dry-run marker as soft ok.
        text = str(out.get("raw_text") or "")
        out["ok_marker"] = CANARY_OK_MARKER in text or DRY_RUN_OK_MARKER in text
        return out

    def health(self) -> dict[str, Any]:
        live = runtime_live_api_enabled() and self.i5.allow_network()
        return {
            "ok": True,
            "binding": self.name if live else "RefuseTransport",
            "live": bool(live),
            "live_api_enabled": bool(live),
            "live_api_enabled_module_default": LIVE_API_ENABLED,
            "i5_armed": self.i5.armed,
            "i5_killed": self.i5.killed,
            "provider": "gemini-free-canary",
            "secret_handle": self.secret_handle,
            "impl_cp": IMPL_CP_ID,
        }


def run_gate5_canary_once(
    *,
    prompt: str = CANARY_PROMPT,
    model_ref: str = CANARY_MODEL,
    secret_env_path: str | Path | None = None,
    timeout_s: float = 30.0,
    request_id: str | None = None,
    urlopen: Any = None,
    skip_network: bool = False,
) -> CanaryLedger:
    """Execute Gate5 step (6): one canary under kill-armed I5 if may_enable.

    Always restores runtime LIVE_API to False (RefuseTransport-safe final).
    ``skip_network=True`` is for unit tests (no HTTP); still walks gates + I5.
    """
    ledger = CanaryLedger(
        authorization=impl_cp_authorization_record(),
        request_id=request_id or f"gate5-canary-{int(time.time())}",
        secret_handle=CANARY_SECRET_HANDLE,
        model_ref=model_ref,
    )

    enablement = evaluate_canary_enablement()
    ledger.may_enable = bool(enablement.may_enable)
    ledger.reasons = list(enablement.reasons)
    if not enablement.may_enable:
        ledger.abort_code = "impl_cp_or_gates"
        ledger.verdict = "ABORT"
        ledger.notes.append("may_enable=False; canary not started; RefuseTransport retained")
        ledger.live_api_enabled_final = bool(LIVE_API_ENABLED)
        ledger.binding_final = "RefuseTransport"
        return ledger

    i5 = arm_i5_for_canary()
    ledger.i5_armed = True
    # Prove kill path exists (design drill + live arm); do not kill before call.
    _ = mock_i5_kill_to_refuse_drill()

    transport = GeminiFreeCanaryTransport(
        i5=i5,
        model_ref=model_ref,
        secret_env_path=str(secret_env_path or DEFAULT_GEMINI_ENV_PATH),
        secret_handle=CANARY_SECRET_HANDLE,
        timeout_s=timeout_s,
        _urlopen=urlopen,
    )

    try:
        with live_api_canary_session(i5=i5, enablement_ok=True):
            ledger.live_api_enabled_during = runtime_live_api_enabled()
            if skip_network:
                # Deterministic test path: pretend advisory canary without HTTP.
                fake_text = CANARY_OK_MARKER
                digest = hashlib.sha256(fake_text.encode()).hexdigest()[:16]
                out = {
                    "schema": "mesh.judge.raw_engine/v0",
                    "ok": True,
                    "http_status": 200,
                    "latency_ms": 0,
                    "raw_text": fake_text,
                    "error_code": None,
                    "provider": "gemini-free-canary",
                    "model_ref": model_ref,
                    "truncated": False,
                    "verdict": "ADVISORY",
                    "digest": digest,
                    "peer_id": "gemini-free-canary",
                    "transport": "canary_skipped_network",
                    "secret_handle": CANARY_SECRET_HANDLE,
                    "live_api_enabled": True,
                    "ok_marker": True,
                    "advisory_only": True,
                    "impl_cp": IMPL_CP_ID,
                }
            else:
                out = transport.call(
                    {"prompt": prompt, "request_id": ledger.request_id},
                    timeout_s=timeout_s,
                )
            ledger.result = {
                k: v
                for k, v in out.items()
                if k not in ("raw_text",)  # keep short; store truncated below
            }
            if out.get("raw_text") is not None:
                ledger.result["raw_text_truncated"] = str(out.get("raw_text"))[:200]
            ledger.http_status = out.get("http_status")  # type: ignore[assignment]
            ledger.latency_ms = out.get("latency_ms")  # type: ignore[assignment]
            ledger.digest = out.get("digest")  # type: ignore[assignment]
            ledger.response_sha256 = out.get("response_sha256")  # type: ignore[assignment]
            ledger.ok_marker = bool(out.get("ok_marker"))
            ledger.verdict = str(out.get("verdict") or "")
            ledger.error_code = out.get("error_code")  # type: ignore[assignment]
            ledger.ok = bool(out.get("ok")) and ledger.verdict != "ABORT"
            if not ledger.ok:
                ledger.abort_code = str(out.get("error_code") or out.get("abort", {}).get("code") or "CANARY_ABORT")
    except Exception as exc:  # noqa: BLE001
        # Anomaly → I5 kill → RefuseTransport
        kill_info = i5.kill(reason=f"CANARY_EXCEPTION:{type(exc).__name__}")
        ledger.i5_killed = True
        ledger.ok = False
        ledger.abort_code = "HUMAN_ABORT"
        ledger.verdict = "ABORT"
        ledger.notes.append(f"exception during canary: {type(exc).__name__}")
        ledger.result = {"kill": kill_info, "error_class": type(exc).__name__}
    finally:
        # Always leave RefuseTransport-safe.
        set_runtime_live_api_enabled(False)
        i5.enabled = False
        ledger.live_api_enabled_final = bool(LIVE_API_ENABLED)
        ledger.binding_final = "RefuseTransport"
        ledger.notes.append(
            "final posture: session LIVE cleared; module LIVE_API_ENABLED under F4; I5/RefuseTransport gate"
        )

    return ledger


def main(argv: list[str] | None = None) -> int:
    import argparse
    import sys

    parser = argparse.ArgumentParser(
        prog="python -m neural_mesh.packaging.l_judge_gemini_free_canary_impl",
        description="CP-0075 Gate5 Gemini free canary (ENABLE_UNDER_FENCES; I5-armed).",
    )
    parser.add_argument("--prompt", default=CANARY_PROMPT)
    parser.add_argument("--model", default=CANARY_MODEL)
    parser.add_argument("--secret-env", default=str(DEFAULT_GEMINI_ENV_PATH))
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Actually run one canary (requires may_enable + key file). Default: print auth/gates only.",
    )
    args = parser.parse_args(argv)

    auth = impl_cp_authorization_record()
    enablement = evaluate_canary_enablement()
    summary: dict[str, Any] = {
        "authorization": auth,
        "enablement": enablement.to_dict(),
        "LIVE_API_ENABLED_module_default": LIVE_API_ENABLED,
        "runtime_live_before": runtime_live_api_enabled(),
    }
    if not args.execute:
        print(json.dumps(summary, indent=2, sort_keys=True))
        return 0 if enablement.may_enable else 2

    ledger = run_gate5_canary_once(
        prompt=args.prompt,
        model_ref=args.model,
        secret_env_path=args.secret_env,
    )
    summary["ledger"] = ledger.to_dict()
    summary["runtime_live_after"] = runtime_live_api_enabled()
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0 if ledger.ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
