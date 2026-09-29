"""CP-0078 — Authorized impl CP: LiveHttpTransport v0 (Gemini free under fences).

Minimum honest codec+transport implementing CP-0076 DESIGN_ONLY residual:

* Unary HTTP codec (TLS-only) with retries / backoff / idempotency / timeouts
* Error taxonomy → Mesh ABORT codes; ABORT/cancel hooks compose I5
* Default binding remains RefuseTransport when runtime LIVE off or I5 refuse
* Module constant ``LIVE_API_ENABLED`` stays **False** (not permanent product enable)
* CI must not enable live (``live_api_in_ci`` stays false)

Authority: CP-0076 design · Gate1 ENABLE_UNDER_FENCES · CP-0075 canary compose ·
CP-0058 RefuseTransport floors · CP-0068 continuity idempotency · CP-0069 I5.
Does **not** unlock NO_HELD / GIA / Raft / N>2 / train / SaaS / D3 / pkg0190.
"""

from __future__ import annotations

import hashlib
import json
import random
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Mapping

from neural_mesh.packaging.google_l_judge_peer_spike import (
    DEFAULT_DRY_RUN_MODEL,
    DEFAULT_GEMINI_ENV_PATH,
    load_gemini_key_from_secret_file,
)
from neural_mesh.packaging.l_judge_gemini_free_canary_impl import (
    I5KillArm,
    arm_i5_for_canary,
    live_api_canary_session,
    runtime_live_api_enabled,
    set_runtime_live_api_enabled,
)
from neural_mesh.packaging.l_judge_live_adapter_safety import (
    RATE_LIMIT_FLOORS,
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
    "DESIGN_CP_ID",
    "LIVE_API_ENABLED",
    "SCHEMA_IMPL",
    "SCHEMA_TRANSPORT",
    "SCHEMA_RESULT",
    "DEFAULT_SECRET_HANDLE",
    "DEFAULT_MODEL",
    "GEMINI_API_BASE",
    "ABORT_CODES_LHT",
    "SRC_LIVE_CODEC_SHIPPED",
    "IdempotencyStore",
    "LiveHttpTransport",
    "TransportHealth",
    "impl_cp_authorization_record",
    "is_impl_cp_authorized",
    "evaluate_lht_enablement",
    "default_lht_policy",
    "payload_digest",
]

PACKAGE_HELD = "0.18.0"
CYCLE = 74
SEAL_CP = "CP-0078"
PRIOR_CP = "CP-0077"
IMPL_CP_ID = "CP-0078"
DESIGN_CP_ID = "CP-0076"
# Product / module default stays False — never permanent enable under this CP.
LIVE_API_ENABLED = False
SRC_LIVE_CODEC_SHIPPED = True  # packaging LiveHttpTransport v0 under CP-0078

SCHEMA_IMPL = "mesh.judge.live_http_transport_impl/v0"
SCHEMA_TRANSPORT = "mesh.judge.live_http_transport/v0"
SCHEMA_RESULT = "mesh.judge.raw_engine/v0"
DEFAULT_SECRET_HANDLE = "mesh://secrets/judge/gemini-free@v1"
DEFAULT_MODEL = DEFAULT_DRY_RUN_MODEL  # gemini-flash-latest
GEMINI_API_BASE = "https://generativelanguage.googleapis.com/v1beta/models"

ABORT_CODES_LHT: tuple[str, ...] = (
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
    "CONT_IDEMPOTENCY_CONFLICT",
    "CONT_LIVE_DISABLED",
)


def payload_digest(request: Mapping[str, Any]) -> str:
    """Stable digest of call payload (no secrets)."""
    safe = {
        k: request.get(k)
        for k in ("prompt", "request_id", "model_ref", "mode", "endpoint")
        if k in request
    }
    blob = json.dumps(safe, sort_keys=True, default=str).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()[:16]


def default_lht_policy() -> dict[str, Any]:
    """v0 policy defaults (enabled must stay false as product default)."""
    return {
        "schema": SCHEMA_TRANSPORT,
        "enabled": False,
        "mode": "unary",
        "streaming_allowed": False,
        "secret_handle": DEFAULT_SECRET_HANDLE,
        "tls_required": True,
        "forbid_plaintext": True,
        "idempotency_required": True,
        "max_retries": int(RATE_LIMIT_FLOORS["max_retries"]),
        "backoff": {"strategy": "exponential_full_jitter", "bound_by_timeout": True},
        "timeout_s": float(RATE_LIMIT_FLOORS["timeout_s"]),
        "soft_timeout_s": float(RATE_LIMIT_FLOORS["timeout_s"]),
        "max_raw_bytes": int(RATE_LIMIT_FLOORS["max_raw_bytes"]),
        "max_calls_per_minute": int(RATE_LIMIT_FLOORS["max_calls_per_minute"]),
        "max_calls_per_hour": int(RATE_LIMIT_FLOORS["max_calls_per_hour"]),
        "max_concurrent": int(RATE_LIMIT_FLOORS["max_concurrent"]),
        "audit_required": True,
        "compose_continuity": True,
        "compose_oversight": True,
        "refuse_transport_default": True,
        "src_live_codec_shipped": SRC_LIVE_CODEC_SHIPPED,
        "LIVE_API_ENABLED": LIVE_API_ENABLED,
        "live_api_in_ci": False,
        "impl_cp": IMPL_CP_ID,
        "design_cp": DESIGN_CP_ID,
    }


def is_impl_cp_authorized() -> bool:
    """This module *is* the authorized impl CP for LiveHttpTransport v0."""
    return True


def impl_cp_authorization_record() -> dict[str, Any]:
    return {
        "schema": SCHEMA_IMPL,
        "impl_cp": IMPL_CP_ID,
        "design_cp": DESIGN_CP_ID,
        "cycle": CYCLE,
        "package_held": PACKAGE_HELD,
        "authorized": True,
        "scope": "live_http_transport_v0_gemini_free_under_fences",
        "provider": "gemini-free",
        "model_ref": DEFAULT_MODEL,
        "secret_handle": DEFAULT_SECRET_HANDLE,
        "binding": "LiveHttpTransport (unary v0) behind runtime LIVE + I5",
        "src_live_codec_shipped": SRC_LIVE_CODEC_SHIPPED,
        "full_live_http_codec_shipped": True,  # packaging v0; still default-off
        "streaming_shipped": False,
        "live_api_enabled_module_default": LIVE_API_ENABLED,
        "live_adapter_enabled_product_default": False,
        "permanent_live_enable": False,
        "canary_cp_compose": "CP-0075",
        "gates_required": [
            "Gate1 ENABLE_UNDER_FENCES SIGNED",
            "Gate2–4 ENABLE_READY",
            "CP-0076 DESIGN_ONLY residual",
            "I5 kill armed for live window",
            "evaluate_enablement_gates may_enable",
            "runtime LIVE window (not module default)",
        ],
        "forbidden": [
            "permanent LIVE_API_ENABLED=True",
            "live_api_in_ci=true",
            "Vertex paid",
            "keys in git",
            "NO_HELD unlocks",
            "D3 / MESH_PERF_EXPERIMENTAL",
            "silent ACCEPT on error",
            "half-ACCEPT on stream break",
            "advisory as Mesh SoT / M1",
        ],
        "note": (
            "Authorized minimum LiveHttpTransport v0 under fences. "
            "Module LIVE_API_ENABLED remains False; RefuseTransport default when live off."
        ),
    }


def evaluate_lht_enablement(
    *,
    flags: dict[str, bool] | None = None,
    secret_handle: str | None = None,
    tls_endpoint: bool = True,
    audit_sink: bool = True,
    prior_dry_run_proven: bool = True,
    safety_case_verified: bool = True,
    impl_cp_authorized: bool | None = None,
) -> Any:
    """Enablement for LiveHttpTransport under this impl CP (fail-closed without auth)."""
    return evaluate_enablement_gates(
        flags=flags,
        secret_handle=secret_handle if secret_handle is not None else DEFAULT_SECRET_HANDLE,
        tls_endpoint=tls_endpoint,
        audit_sink=audit_sink,
        prior_dry_run_proven=prior_dry_run_proven,
        safety_case_verified=safety_case_verified,
        impl_cp_authorized=(
            is_impl_cp_authorized() if impl_cp_authorized is None else bool(impl_cp_authorized)
        ),
    )


@dataclass
class IdempotencyStore:
    """Mesh-owned idempotency: same key+digest → replay; conflict → ABORT."""

    _by_key: dict[str, dict[str, Any]] = field(default_factory=dict)
    _cancelled: set[str] = field(default_factory=set)

    def lookup(self, key: str, digest: str) -> tuple[dict[str, Any] | None, str | None]:
        """Return (prior_result, error_code). error_code set on conflict/cancel."""
        if key in self._cancelled:
            return None, "HUMAN_ABORT"
        existing = self._by_key.get(key)
        if existing is None:
            return None, None
        if existing.get("payload_digest") != digest:
            return None, "CONT_IDEMPOTENCY_CONFLICT"
        return dict(existing["result"]), None

    def store(self, key: str, digest: str, result: Mapping[str, Any]) -> None:
        self._by_key[key] = {
            "payload_digest": digest,
            "result": dict(result),
            "sealed": True,
        }

    def cancel(self, key: str) -> None:
        self._cancelled.add(key)
        # Drop sealed success so cancel wins for subsequent submits.
        self._by_key.pop(key, None)

    def is_cancelled(self, key: str) -> bool:
        return key in self._cancelled


@dataclass
class TransportHealth:
    ok: bool
    binding: str
    live: bool
    live_api_enabled: bool
    live_api_enabled_module_default: bool
    i5_armed: bool
    i5_killed: bool
    src_live_codec_shipped: bool
    impl_cp: str
    mode: str
    provider: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "binding": self.binding,
            "live": self.live,
            "live_api_enabled": self.live_api_enabled,
            "live_api_enabled_module_default": self.live_api_enabled_module_default,
            "i5_armed": self.i5_armed,
            "i5_killed": self.i5_killed,
            "src_live_codec_shipped": self.src_live_codec_shipped,
            "impl_cp": self.impl_cp,
            "mode": self.mode,
            "provider": self.provider,
        }


def _abort(
    code: str,
    *,
    reason: str,
    provider: str = "live-http",
    model_ref: str = DEFAULT_MODEL,
    secret_handle: str | None = None,
    http_status: int | None = None,
    latency_ms: int = 0,
    extra: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    out: dict[str, Any] = {
        "schema": SCHEMA_RESULT,
        "ok": False,
        "http_status": http_status,
        "latency_ms": latency_ms,
        "raw_text": None,
        "error_code": code,
        "provider": provider,
        "model_ref": model_ref,
        "truncated": False,
        "verdict": "ABORT",
        "digest": "",
        "peer_id": "live-http-transport",
        "transport": "live_http",
        "secret_handle": secret_handle,
        "live_api_enabled": runtime_live_api_enabled(),
        "LIVE_API_ENABLED_module_default": LIVE_API_ENABLED,
        "impl_cp": IMPL_CP_ID,
        "advisory_only": True,
        "mesh_accept": False,
        "abort": {"code": code, "reason": reason},
        "src_live_codec_shipped": SRC_LIVE_CODEC_SHIPPED,
    }
    if extra:
        out.update(dict(extra))
    return out


def _backoff_sleep(
    attempt: int,
    *,
    remaining_s: float,
    sleeper: Callable[[float], None],
    rng: random.Random,
) -> float:
    """Exponential full jitter; never exceeds remaining timeout budget. Returns slept."""
    if remaining_s <= 0:
        return 0.0
    base = min(0.05 * (2**attempt), remaining_s)
    delay = rng.uniform(0.0, base)
    delay = min(delay, remaining_s)
    if delay > 0:
        sleeper(delay)
    return delay


@dataclass
class LiveHttpTransport:
    """v0 LiveHttpTransport — unary Gemini free under runtime LIVE + I5.

    When live is off / I5 refuse / enablement fail → RefuseTransport (zero network).
    """

    i5: I5KillArm
    model_ref: str = DEFAULT_MODEL
    secret_env_path: str = str(DEFAULT_GEMINI_ENV_PATH)
    secret_handle: str = DEFAULT_SECRET_HANDLE
    timeout_s: float = float(RATE_LIMIT_FLOORS["timeout_s"])
    max_retries: int = int(RATE_LIMIT_FLOORS["max_retries"])
    max_raw_bytes: int = int(RATE_LIMIT_FLOORS["max_raw_bytes"])
    audit_sink: bool = True
    tls_required: bool = True
    endpoint_base: str = GEMINI_API_BASE
    name: str = "LiveHttpTransport"
    provider: str = "gemini-free"
    idempotency: IdempotencyStore = field(default_factory=IdempotencyStore)
    _urlopen: Any = field(default=None, repr=False)
    _load_key: Callable[[str], str] | None = field(default=None, repr=False)
    _sleeper: Callable[[float], None] = field(default=time.sleep, repr=False)
    _rng: random.Random = field(default_factory=random.Random, repr=False)
    _call_count_minute: int = 0
    _max_calls_per_minute: int = int(RATE_LIMIT_FLOORS["max_calls_per_minute"])

    def health(self) -> dict[str, Any]:
        live = runtime_live_api_enabled() and self.i5.allow_network()
        h = TransportHealth(
            ok=True,
            binding=self.name if live else "RefuseTransport",
            live=bool(live),
            live_api_enabled=bool(live),
            live_api_enabled_module_default=LIVE_API_ENABLED,
            i5_armed=self.i5.armed,
            i5_killed=self.i5.killed,
            src_live_codec_shipped=SRC_LIVE_CODEC_SHIPPED,
            impl_cp=IMPL_CP_ID,
            mode="unary",
            provider=self.provider,
        )
        return h.to_dict()

    def cancel(self, idempotency_key: str | None = None, call_id: str | None = None) -> dict[str, Any]:
        """ABORT propagation hook — cancel in-flight family; bind refuse for key."""
        key = idempotency_key or call_id
        if not key:
            return {
                "ok": False,
                "error_code": "SCHEMA_INVALID",
                "abort": {"code": "SCHEMA_INVALID", "reason": "cancel requires idempotency_key|call_id"},
            }
        self.idempotency.cancel(key)
        # If I5 kill, also flip armed window closed via kill path.
        refuse = RefuseTransport().call({"reason": "cancel", "idempotency_key": key})
        return {
            "ok": True,
            "cancelled": key,
            "binding": "RefuseTransport",
            "error_code": "HUMAN_ABORT",
            "refuse": refuse,
            "impl_cp": IMPL_CP_ID,
        }

    def call(
        self,
        request: dict[str, Any] | None = None,
        *,
        idempotency_key: str | None = None,
        mode: str = "unary",
        timeout_s: float | None = None,
    ) -> dict[str, Any]:
        payload = dict(request or {})
        to = float(timeout_s if timeout_s is not None else self.timeout_s)
        deadline = time.monotonic() + to

        # T-lht-a: live off → RefuseTransport, zero network
        if not runtime_live_api_enabled() or not self.i5.allow_network():
            refused = RefuseTransport().call(payload, timeout_s=to)
            refused = dict(refused)
            refused["provider"] = self.provider
            refused["transport"] = "refuse"
            refused["live_api_enabled"] = False
            refused["LIVE_API_ENABLED_module_default"] = LIVE_API_ENABLED
            refused["secret_handle"] = self.secret_handle
            refused["impl_cp"] = IMPL_CP_ID
            refused["src_live_codec_shipped"] = SRC_LIVE_CODEC_SHIPPED
            refused["note"] = (
                "LiveHttpTransport refused: need runtime LIVE_API + I5 armed; "
                "module LIVE_API_ENABLED default remains False"
            )
            return refused

        # T-lht-i: missing audit sink
        if not self.audit_sink:
            return _abort(
                "NO_AUDIT",
                reason="audit sink required; no-audit=no-action",
                provider=self.provider,
                model_ref=self.model_ref,
                secret_handle=self.secret_handle,
            )

        # T-lht-b: secret_handle
        handle = str(payload.get("secret_handle") or self.secret_handle)
        if not is_valid_secret_handle(handle):
            return _abort(
                "ENGINE_AUTH",
                reason="invalid or missing secret_handle",
                provider=self.provider,
                model_ref=self.model_ref,
                secret_handle=handle,
            )

        # Endpoint / TLS (T-lht-c)
        endpoint = str(payload.get("endpoint") or f"{self.endpoint_base}/{self.model_ref}:generateContent")
        if self.tls_required and not endpoint.lower().startswith("https://"):
            return _abort(
                "PLAINTEXT_FORBIDDEN",
                reason="tls_required; plaintext/non-TLS endpoint refused",
                provider=self.provider,
                model_ref=self.model_ref,
                secret_handle=handle,
                extra={"error_code_alt": "ENGINE_TLS", "endpoint_scheme": endpoint.split(":", 1)[0]},
            )

        # Mode (streaming not shipped in v0)
        call_mode = str(payload.get("mode") or mode or "unary")
        if call_mode not in ("unary",):
            # T-lht-j-ish: stream unsupported → policy ABORT, never half-ACCEPT
            return _abort(
                "ENGINE_HTTP",
                reason=f"mode={call_mode} unsupported in v0; unary only (no half-ACCEPT)",
                provider=self.provider,
                model_ref=self.model_ref,
                secret_handle=handle,
                extra={"mode": call_mode, "streaming_allowed": False},
            )

        # Idempotency required (compose continuity)
        key = idempotency_key or payload.get("idempotency_key")
        if not key or not isinstance(key, str) or not key.strip():
            return _abort(
                "CONT_LIVE_DISABLED",
                reason="idempotency_key required on live path",
                provider=self.provider,
                model_ref=self.model_ref,
                secret_handle=handle,
            )
        key = key.strip()
        digest = payload_digest({**payload, "mode": call_mode, "endpoint": endpoint})

        prior, ierr = self.idempotency.lookup(key, digest)
        if ierr == "CONT_IDEMPOTENCY_CONFLICT":
            return _abort(
                "CONT_IDEMPOTENCY_CONFLICT",
                reason="same idempotency_key with different payload digest",
                provider=self.provider,
                model_ref=self.model_ref,
                secret_handle=handle,
                extra={"idempotency_key": key},
            )
        if ierr == "HUMAN_ABORT":
            return _abort(
                "HUMAN_ABORT",
                reason="call family cancelled / I5 abort",
                provider=self.provider,
                model_ref=self.model_ref,
                secret_handle=handle,
                extra={"idempotency_key": key},
            )
        if prior is not None:
            # T-lht-d: replay — no double-invoke
            replay = dict(prior)
            replay["idempotent_replay"] = True
            replay["idempotency_key"] = key
            return replay

        # Rate floor
        if self._call_count_minute >= self._max_calls_per_minute:
            return _abort(
                "ENGINE_RATE_LIMIT",
                reason="max_calls_per_minute floor tripped",
                provider=self.provider,
                model_ref=self.model_ref,
                secret_handle=handle,
            )

        # I5 kill mid-path check before network
        if self.i5.killed or not self.i5.allow_network():
            return _abort(
                "HUMAN_ABORT",
                reason="I5 kill / not allowing network",
                provider=self.provider,
                model_ref=self.model_ref,
                secret_handle=handle,
            )

        result = self._attempt_family(
            payload=payload,
            endpoint=endpoint,
            handle=handle,
            key=key,
            digest=digest,
            deadline=deadline,
            to=to,
        )
        return result

    def _attempt_family(
        self,
        *,
        payload: dict[str, Any],
        endpoint: str,
        handle: str,
        key: str,
        digest: str,
        deadline: float,
        to: float,
    ) -> dict[str, Any]:
        attempts = 0
        max_attempts = 1 + max(0, int(self.max_retries))
        last: dict[str, Any] | None = None

        while attempts < max_attempts:
            if self.idempotency.is_cancelled(key) or self.i5.killed:
                out = _abort(
                    "HUMAN_ABORT",
                    reason="I5 kill / cancel mid-family",
                    provider=self.provider,
                    model_ref=self.model_ref,
                    secret_handle=handle,
                    extra={"idempotency_key": key, "attempts": attempts},
                )
                self.idempotency.store(key, digest, out)
                return out

            remaining = deadline - time.monotonic()
            if remaining <= 0:
                out = _abort(
                    "ENGINE_TIMEOUT",
                    reason="hard timeout budget exhausted",
                    provider=self.provider,
                    model_ref=self.model_ref,
                    secret_handle=handle,
                    latency_ms=int(to * 1000),
                    extra={"idempotency_key": key},
                )
                self.idempotency.store(key, digest, out)
                return out

            attempts += 1
            self._call_count_minute += 1
            last = self._one_http(
                payload=payload,
                endpoint=endpoint,
                handle=handle,
                timeout_s=remaining,
                attempt=attempts,
            )

            if last.get("ok"):
                last["idempotency_key"] = key
                last["payload_digest"] = digest
                last["attempts"] = attempts
                last["idempotent_replay"] = False
                self.idempotency.store(key, digest, last)
                return last

            code = str(last.get("error_code") or "")
            # Non-retryable
            if code in {
                "ENGINE_AUTH",
                "ENGINE_TLS",
                "PLAINTEXT_FORBIDDEN",
                "SCHEMA_INVALID",
                "NO_AUDIT",
                "HUMAN_ABORT",
                "FENCE",
                "POLICY_ABORT",
                "CONT_IDEMPOTENCY_CONFLICT",
            }:
                last["idempotency_key"] = key
                last["attempts"] = attempts
                self.idempotency.store(key, digest, last)
                return last

            # Retryable: ENGINE_HTTP / ENGINE_RATE_LIMIT (conditional) / transient
            if attempts >= max_attempts:
                break
            remaining = deadline - time.monotonic()
            _backoff_sleep(
                attempts,
                remaining_s=max(0.0, remaining),
                sleeper=self._sleeper,
                rng=self._rng,
            )

        # Exhausted retries (T-lht-f)
        if last is None:
            last = _abort(
                "ENGINE_HTTP",
                reason="no attempt completed",
                provider=self.provider,
                model_ref=self.model_ref,
                secret_handle=handle,
            )
        last = dict(last)
        last["idempotency_key"] = key
        last["attempts"] = attempts
        last["retries_exhausted"] = True
        # Never invent ACCEPT
        if last.get("verdict") == "ACCEPT":
            last["verdict"] = "ABORT"
            last["ok"] = False
            last["error_code"] = last.get("error_code") or "ENGINE_HTTP"
            last["mesh_accept"] = False
        self.idempotency.store(key, digest, last)
        return last

    def _one_http(
        self,
        *,
        payload: dict[str, Any],
        endpoint: str,
        handle: str,
        timeout_s: float,
        attempt: int,
    ) -> dict[str, Any]:
        urlopen = self._urlopen if self._urlopen is not None else urllib.request.urlopen
        prompt = str(payload.get("prompt") or "Reply with exactly: MESH_LHT_OK")
        t0 = time.monotonic()

        try:
            loader = self._load_key or load_gemini_key_from_secret_file
            api_key = loader(self.secret_env_path)
        except (OSError, ValueError) as exc:
            return _abort(
                "ENGINE_AUTH",
                reason=f"secret unresolved: {type(exc).__name__}",
                provider=self.provider,
                model_ref=self.model_ref,
                secret_handle=handle,
                extra={"attempt": attempt, "error_class": "auth"},
            )

        try:
            url = endpoint if "key=" in endpoint else f"{endpoint}?key={api_key}"
            # Guard: never allow http:// even if somehow passed
            if not url.lower().startswith("https://"):
                return _abort(
                    "PLAINTEXT_FORBIDDEN",
                    reason="refused non-TLS URL at request time",
                    provider=self.provider,
                    model_ref=self.model_ref,
                    secret_handle=handle,
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
            try:
                with urlopen(req, timeout=timeout_s) as resp:
                    raw = resp.read()
                    status = int(getattr(resp, "status", 200) or 200)
            except urllib.error.HTTPError as exc:
                latency_ms = int((time.monotonic() - t0) * 1000)
                code_http = int(exc.code)
                if code_http in (401, 403):
                    ec = "ENGINE_AUTH"
                elif code_http == 429:
                    ec = "ENGINE_RATE_LIMIT"
                else:
                    ec = "ENGINE_HTTP"
                return _abort(
                    ec,
                    reason=f"HTTP {code_http}",
                    provider=self.provider,
                    model_ref=self.model_ref,
                    secret_handle=handle,
                    http_status=code_http,
                    latency_ms=latency_ms,
                    extra={"attempt": attempt, "network": True},
                )
            except (urllib.error.URLError, TimeoutError, OSError) as exc:
                latency_ms = int((time.monotonic() - t0) * 1000)
                # Timeout-ish → ENGINE_TIMEOUT; other network → ENGINE_HTTP
                name = type(exc).__name__
                ec = "ENGINE_TIMEOUT" if "Timeout" in name or "timed out" in str(exc).lower() else "ENGINE_HTTP"
                return _abort(
                    ec,
                    reason=name,
                    provider=self.provider,
                    model_ref=self.model_ref,
                    secret_handle=handle,
                    latency_ms=latency_ms,
                    extra={"attempt": attempt, "network": False, "error_class": "network"},
                )
        finally:
            api_key = ""  # noqa: F841

        latency_ms = int((time.monotonic() - t0) * 1000)
        if len(raw) > self.max_raw_bytes:
            return _abort(
                "SCHEMA_INVALID",
                reason="response exceeds max_raw_bytes; forbid silent accept",
                provider=self.provider,
                model_ref=self.model_ref,
                secret_handle=handle,
                http_status=status,
                latency_ms=latency_ms,
                extra={"attempt": attempt, "truncated": True, "oversize": True},
            )

        try:
            parsed = json.loads(raw.decode("utf-8"))
        except json.JSONDecodeError:
            return _abort(
                "SCHEMA_INVALID",
                reason="response JSON invalid",
                provider=self.provider,
                model_ref=self.model_ref,
                secret_handle=handle,
                http_status=status,
                latency_ms=latency_ms,
                extra={"attempt": attempt, "network": True},
            )

        text = _extract_text(parsed)
        digest = hashlib.sha256(
            json.dumps(
                {"peer": "live-http", "model": self.model_ref, "text": text[:200], "status": status},
                sort_keys=True,
            ).encode()
        ).hexdigest()[:16]
        ok = status == 200
        return {
            "schema": SCHEMA_RESULT,
            "ok": ok,
            "http_status": status,
            "latency_ms": latency_ms,
            "raw_text": text[:500],
            "error_code": None if ok else "ENGINE_HTTP",
            "provider": self.provider,
            "model_ref": self.model_ref,
            "network": True,
            "verdict": "ADVISORY" if ok else "ABORT",
            "digest": digest,
            "peer_id": "live-http-transport",
            "transport": "live_http",
            "secret_handle": handle,
            "live_api_enabled": True,
            "LIVE_API_ENABLED_module_default": LIVE_API_ENABLED,
            "impl_cp": IMPL_CP_ID,
            "advisory_only": True,
            "mesh_accept": False,
            "response_sha256": hashlib.sha256(raw).hexdigest(),
            "src_live_codec_shipped": SRC_LIVE_CODEC_SHIPPED,
            "attempt": attempt,
            "mode": "unary",
        }


def _extract_text(body: dict[str, Any]) -> str:
    cands = body.get("candidates") or []
    texts: list[str] = []
    for c in cands:
        content = (c or {}).get("content") or {}
        for part in content.get("parts") or []:
            t = part.get("text") if isinstance(part, dict) else None
            if t:
                texts.append(str(t))
    return "".join(texts).strip()


def main(argv: list[str] | None = None) -> int:
    import argparse
    import sys

    parser = argparse.ArgumentParser(
        prog="python -m neural_mesh.packaging.l_judge_live_http_transport",
        description="CP-0078 LiveHttpTransport v0 (ENABLE_UNDER_FENCES; default LIVE off).",
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="One fenced health/call under I5 if may_enable (restores LIVE false). Default: auth only.",
    )
    parser.add_argument("--prompt", default="Reply with exactly: MESH_LHT_OK")
    parser.add_argument("--secret-env", default=str(DEFAULT_GEMINI_ENV_PATH))
    args = parser.parse_args(argv)

    auth = impl_cp_authorization_record()
    enablement = evaluate_lht_enablement()
    summary: dict[str, Any] = {
        "authorization": auth,
        "enablement": enablement.to_dict(),
        "policy": default_lht_policy(),
        "LIVE_API_ENABLED_module_default": LIVE_API_ENABLED,
        "src_live_codec_shipped": SRC_LIVE_CODEC_SHIPPED,
        "runtime_live_before": runtime_live_api_enabled(),
    }
    if not args.execute:
        print(json.dumps(summary, indent=2, sort_keys=True))
        return 0 if enablement.may_enable else 2

    if not enablement.may_enable:
        print(json.dumps(summary, indent=2, sort_keys=True))
        return 2

    i5 = arm_i5_for_canary()
    transport = LiveHttpTransport(
        i5=i5,
        secret_env_path=args.secret_env,
    )
    try:
        with live_api_canary_session(i5=i5, enablement_ok=True):
            health = transport.health()
            out = transport.call(
                {"prompt": args.prompt},
                idempotency_key=f"lht-cli-{int(time.time())}",
            )
            summary["health_during"] = health
            summary["result"] = {
                k: v for k, v in out.items() if k != "raw_text"
            }
            if out.get("raw_text") is not None:
                summary["result"]["raw_text_truncated"] = str(out.get("raw_text"))[:200]
    finally:
        set_runtime_live_api_enabled(False)
        i5.enabled = False
        summary["runtime_live_after"] = runtime_live_api_enabled()
        summary["LIVE_API_ENABLED_module_default_final"] = LIVE_API_ENABLED
        summary["binding_final"] = "RefuseTransport"

    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0 if summary.get("result", {}).get("ok") else 2


if __name__ == "__main__":
    raise SystemExit(main())
