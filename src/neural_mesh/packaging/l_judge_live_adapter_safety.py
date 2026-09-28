"""L_judge live-adapter safety case helpers (CP-0058 / Cycle 54; enablement lift CP-0075).

Constants, secret_handle validation, RefuseTransport mock, and
enablement-gate evaluation. No network I/O here. No API keys. No live codec.
CP-0075 authorizes may_enable=True when all gates pass (NT-10 cleared).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

__all__ = [
    "PACKAGE_HELD",
    "CYCLE",
    "SEAL_CP",
    "PRIOR_CP",
    "PREFERRED_NEXT_DEFAULT",
    "SCHEMA_SAFETY",
    "SCHEMA_CONFIG",
    "SECRET_HANDLE_RE",
    "ABORT_CODES",
    "RATE_LIMIT_FLOORS",
    "MUST_STAY_FALSE",
    "PERMANENT_FALSE",
    "is_valid_secret_handle",
    "looks_like_raw_secret",
    "default_safety_gate",
    "evaluate_enablement_gates",
    "RefuseTransport",
    "EnablementResult",
]

PACKAGE_HELD = "0.18.0"
CYCLE = 54
SEAL_CP = "CP-0058"
PRIOR_CP = "CP-0057"
PREFERRED_NEXT_DEFAULT = "await_deepseek"

SCHEMA_SAFETY = "mesh.judge.live_adapter_safety/v0"
SCHEMA_CONFIG = "mesh.judge.live_adapter_config/v0"

# mesh://secrets/<scope>/<name>@<version>
SECRET_HANDLE_RE = re.compile(
    r"^mesh://secrets/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+@v[0-9]+$"
)

_RAW_SECRET_RE = re.compile(
    r"(sk-[A-Za-z0-9]{10,})|(Authorization:\s*Bearer\s+sk-)|(api_key\s*=\s*['\"]?[A-Za-z0-9_\-]{8,})",
    re.IGNORECASE,
)

ABORT_CODES: tuple[str, ...] = (
    "ENGINE_DISABLED",
    "ENGINE_AUTH",
    "ENGINE_TLS",
    "PLAINTEXT_FORBIDDEN",
    "ENGINE_HTTP",
    "ENGINE_TIMEOUT",
    "ENGINE_RATE_LIMIT",
    "SCHEMA_INVALID",
    "NO_AUDIT",
    "FENCE",
    "POLICY_ABORT",
    "HUMAN_ABORT",
)

RATE_LIMIT_FLOORS: dict[str, int | float] = {
    "max_calls_per_minute": 10,
    "max_calls_per_hour": 120,
    "max_retries": 1,
    "timeout_s": 30,
    "max_raw_bytes": 65536,
    "max_concurrent": 1,
}

# Flags that must remain false until evidence (safety case §8).
MUST_STAY_FALSE: tuple[str, ...] = (
    "live_adapter.enabled",
    "live_api_in_ci",
    "src_live_codec_shipped",
    "mesh_is_frontier_model",
    "train_70b",
    "gia_unlocked",
    "raft_runtime",
    "n_gt_2",
    "saas_settlement",
    "engine_is_goal_sot",
    "silent_accept_on_error",
)

# Subset that must never flip true on this product line.
PERMANENT_FALSE: frozenset[str] = frozenset(
    {
        "mesh_is_frontier_model",
        "train_70b",
        "gia_unlocked",
        "raft_runtime",
        "n_gt_2",
        "saas_settlement",
        "engine_is_goal_sot",
        "silent_accept_on_error",
    }
)


def is_valid_secret_handle(handle: str | None) -> bool:
    """Return True iff handle is a non-empty mesh://secrets reference."""
    if not handle or not isinstance(handle, str):
        return False
    if looks_like_raw_secret(handle):
        return False
    return bool(SECRET_HANDLE_RE.match(handle.strip()))


def looks_like_raw_secret(text: str) -> bool:
    """Heuristic: detect embedded live-looking secret material."""
    if not text:
        return False
    return bool(_RAW_SECRET_RE.search(text))


def default_safety_gate() -> dict[str, Any]:
    """Return the design-default safety gate (live disabled)."""
    must_false = {k: False for k in MUST_STAY_FALSE}
    return {
        "schema": SCHEMA_SAFETY,
        "enabled": False,
        "secret_handle": None,
        "refuse_transport_default": True,
        "tls_required": True,
        "forbid_plaintext": True,
        "require_prior_dry_run": True,
        "require_audit_sink": True,
        **{k: RATE_LIMIT_FLOORS[k] for k in RATE_LIMIT_FLOORS},
        "must_stay_false": must_false,
    }


@dataclass
class EnablementResult:
    """Outcome of evaluating whether live may be enabled (design check)."""

    may_enable: bool = False
    reasons: list[str] = field(default_factory=list)
    flags: dict[str, bool] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "may_enable": self.may_enable,
            "reasons": list(self.reasons),
            "flags": dict(self.flags),
        }


def evaluate_enablement_gates(
    *,
    flags: dict[str, bool] | None = None,
    secret_handle: str | None = None,
    tls_endpoint: bool = False,
    audit_sink: bool = False,
    prior_dry_run_proven: bool = False,
    safety_case_verified: bool = False,
    impl_cp_authorized: bool = False,
) -> EnablementResult:
    """Evaluate design enablement gates.

    By default all inputs are fail-closed: may_enable is False. This helper
    never performs network I/O and never flips permanent-false flags.
    """
    merged = {k: False for k in MUST_STAY_FALSE}
    if flags:
        for k, v in flags.items():
            if k in merged:
                merged[k] = bool(v)

    reasons: list[str] = []

    # Permanent refuses
    for k in PERMANENT_FALSE:
        if merged.get(k):
            reasons.append(f"permanent_false_asserted:{k}")

    if merged.get("live_adapter.enabled"):
        reasons.append("live_adapter.enabled_must_stay_false_until_evidence")
    if merged.get("live_api_in_ci"):
        reasons.append("live_api_in_ci_must_stay_false")
    if merged.get("src_live_codec_shipped"):
        reasons.append("src_live_codec_shipped_must_stay_false_this_cp")

    if not safety_case_verified:
        reasons.append("safety_case_not_verified")
    if not impl_cp_authorized:
        reasons.append("impl_cp_not_authorized")
    if not is_valid_secret_handle(secret_handle):
        reasons.append("secret_handle_invalid_or_missing")
    if not tls_endpoint:
        reasons.append("tls_endpoint_required")
    if not audit_sink:
        reasons.append("audit_sink_required")
    if not prior_dry_run_proven:
        reasons.append("prior_dry_run_not_proven")

    # Authorized impl CP (CP-0075 / Gemini free canary under fences) lifts the
    # Cycle-54 hard-false: may_enable is True only when *no* refusal reasons
    # remain. Default call still fails closed (impl_cp_not_authorized etc.).
    # Permanent-false / must-stay-false assertions still block.
    may = len(reasons) == 0
    return EnablementResult(may_enable=may, reasons=reasons, flags=merged)


class RefuseTransport:
    """Fail-closed transport: every call ABORTs with ENGINE_DISABLED.

    No network. Used as the design-default binding when live is disabled.
    """

    name = "RefuseTransport"

    def call(self, bundle: dict[str, Any] | None = None, *, timeout_s: float = 30.0) -> dict[str, Any]:
        _ = bundle, timeout_s
        return {
            "schema": "mesh.judge.raw_engine/v0",
            "ok": False,
            "http_status": None,
            "latency_ms": 0,
            "raw_text": None,
            "error_code": "ENGINE_DISABLED",
            "provider": "refuse",
            "model_ref": "none",
            "truncated": False,
            "verdict": "ABORT",
            "abort": {"code": "ENGINE_DISABLED", "reason": "live disabled; RefuseTransport default"},
        }

    def health(self) -> dict[str, Any]:
        return {"ok": True, "binding": self.name, "live": False}
