"""CP-0083 — Phase R2: multi-judge live/mock-bound RV under Authority Matrix.

Binds one Gemini free advisory judge (real HTTP under ENABLE_UNDER_FENCES +
CP-0075/0078 when gates pass) + ≥1 deterministic mock/local advisory judge on
the full-adapter compose surface. Proves conflict / missing / ABORT > ACCEPT;
N=2 stays M1=NO_CONSENSUS_YET. I5 armed; RefuseTransport default; module
LIVE_API_ENABLED stays False final.

Authority: CP-0081 §4 Phase R2 · operator R2 authorize · Gate1 ENABLE_UNDER_FENCES.
Does NOT authorize R3–R5 · permanent LIVE · F4 invent · NO_HELD · push/tags/secrets.
"""

from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Mapping

from neural_mesh.packaging.d1_l_judge_safety_maturation import AUTHORITY_MATRIX
from neural_mesh.packaging.google_l_judge_peer_spike import DEFAULT_GEMINI_ENV_PATH
from neural_mesh.packaging.l_judge_gemini_free_canary_impl import (
    CANARY_SECRET_HANDLE,
    ENABLE_ACK_PATH,
    I5KillArm,
    arm_i5_for_canary,
    evaluate_canary_enablement,
    live_api_canary_session,
    runtime_live_api_enabled,
    set_runtime_live_api_enabled,
    LIVE_API_ENABLED as CANARY_LIVE_API_ENABLED,
)
from neural_mesh.packaging.l_judge_live_adapter_safety import RefuseTransport
from neural_mesh.packaging.l_judge_live_http_transport import (
    DEFAULT_SECRET_HANDLE,
    LIVE_API_ENABLED as LHT_LIVE_API_ENABLED,
    LiveHttpTransport,
    evaluate_lht_enablement,
)
from neural_mesh.packaging.multi_judge_agent_shell_spike import (
    ABORT_GT_ACCEPT_POLICY,
    M1_STATUS as SPIKE_M1_STATUS,
    evaluate_dual_digest_hygiene,
)

__all__ = [
    "PACKAGE_HELD",
    "CYCLE",
    "SEAL_CP",
    "PRIOR_CP",
    "IMPL_CP_ID",
    "DESIGN_CP_ID",
    "LIVE_API_ENABLED",
    "PHASE",
    "M1_STATUS",
    "N_JUDGES",
    "DESCRIPTOR_IDS",
    "ABORT_GT_ACCEPT",
    "GEMINI_JUDGE_ID",
    "MOCK_JUDGE_ID",
    "R2_PROMPT",
    "R2_OK_MARKER",
    "ENABLE_ACK",
    "JudgeAdvisory",
    "MeshDecision",
    "ComposeResult",
    "is_impl_cp_authorized",
    "impl_cp_authorization_record",
    "r2_checklist_rows",
    "assert_module_live_false",
    "check_runbook_gates",
    "invoke_mock_advisory",
    "invoke_gemini_advisory",
    "mesh_resolve_multi_judge",
    "compose_abort_gt_accept",
    "compose_conflict",
    "compose_missing_judge",
    "compose_agree_no_m1",
    "compose_refuse_default",
    "compose_i5_armed",
    "compose_live_mock_bound",
    "run_r2_compose_suite",
]

PACKAGE_HELD = "0.18.0"
CYCLE = 79
SEAL_CP = "CP-0083"
PRIOR_CP = "CP-0082"
IMPL_CP_ID = "CP-0083"
DESIGN_CP_ID = "CP-0081"
# Product / module default stays False — R2 does not permanently enable.
LIVE_API_ENABLED = False
PHASE = "R2"
M1_STATUS = "NO_CONSENSUS_YET"  # N=2 dual advisory ≠ M1 consensus
N_JUDGES = 2
ABORT_GT_ACCEPT = ABORT_GT_ACCEPT_POLICY
GEMINI_JUDGE_ID = "judge:gemini-free"
MOCK_JUDGE_ID = "judge:mock-local"
R2_PROMPT = "Reply with exactly: MESH_R2_MULTI_JUDGE_OK"
R2_OK_MARKER = "MESH_R2_MULTI_JUDGE_OK"
ENABLE_ACK = ENABLE_ACK_PATH

DESCRIPTOR_IDS: tuple[str, ...] = (
    "T-fa-r2-a",  # refuse default / live off
    "T-fa-r2-b",  # I5 armed compose
    "T-fa-r2-c",  # ABORT > ACCEPT (Mesh beats judge ACCEPT)
    "T-fa-r2-d",  # conflict → fail-closed ABORT
    "T-fa-r2-e",  # missing judge → fail-closed ABORT
    "T-fa-r2-f",  # agree digests still NO_CONSENSUS_YET / mesh_accept=false
    "T-fa-r2-g",  # live+mock-bound compose (real HTTP if gates; else mock-bound honest)
    "T-fa-r2-h",  # module LIVE False final + RefuseTransport
)


def is_impl_cp_authorized() -> bool:
    """R2 measurement/impl is authorized under this CP; R3–R5 are not."""
    return True


def impl_cp_authorization_record() -> dict[str, Any]:
    return {
        "schema": "mesh.judge.full_adapter_r2_multi_judge_auth/v0",
        "authorized": True,
        "impl_cp": IMPL_CP_ID,
        "design_cp": DESIGN_CP_ID,
        "prior_cp": PRIOR_CP,
        "phase": PHASE,
        "authorizes": [
            "R2 multi-judge live/mock-bound RV under Authority Matrix",
            "one Gemini free advisory + ≥1 deterministic mock advisory",
            "conflict / missing / ABORT>ACCEPT descriptors + compose",
            "optional one real HTTP under ENABLE_UNDER_FENCES + CP-0075/0078 when gates pass",
        ],
        "does_not_authorize": [
            "R3 Gate6 live-measurement seal / raise n_real_http",
            "R4 streaming DEFER or streaming RV",
            "R5 F4 product ACK / permanent module True",
            "permanent LIVE_API_ENABLED",
            "F4 invent",
            "M1 consensus claim under N=2",
            "NO_HELD unlock",
            "push/tags/secrets",
        ],
        "live_api_enabled_module_default": LIVE_API_ENABLED,
        "canary_live_api_enabled_constant": CANARY_LIVE_API_ENABLED,
        "lht_live_api_enabled_constant": LHT_LIVE_API_ENABLED,
        "permanent_live_enable": False,
        "m1_status": M1_STATUS,
        "n_judges": N_JUDGES,
        "abort_gt_accept": ABORT_GT_ACCEPT,
        "package_held": PACKAGE_HELD,
        "cycle": CYCLE,
        "enable_ack": ENABLE_ACK,
        "authority_matrix_cite": {
            "L_judge": list(AUTHORITY_MATRIX["L_judge"]),
            "Oversight_I5": list(AUTHORITY_MATRIX["Oversight_I5"]),
            "Operator": list(AUTHORITY_MATRIX["Operator"]),
            "RefuseTransport": list(AUTHORITY_MATRIX["RefuseTransport"]),
        },
        "surfaces": [
            "LiveHttpTransport",
            "GeminiFreeCanary",
            "MockLocalAdvisory",
            "RefuseTransport",
            "I5KillArm",
            "AuthorityMatrix",
        ],
    }


def assert_module_live_false() -> None:
    if LIVE_API_ENABLED or CANARY_LIVE_API_ENABLED or LHT_LIVE_API_ENABLED:
        raise AssertionError("LIVE_API_ENABLED module constant must stay False under R2")


def r2_checklist_rows() -> list[dict[str, Any]]:
    return [
        {
            "id": "MJ-1",
            "topic": "Dual advisory bind",
            "rule": "≥1 Gemini free advisory + ≥1 mock/local advisory under matrix",
            "prove": "compose_live_mock_bound binds both judge ids",
            "descriptor": "T-fa-r2-g",
        },
        {
            "id": "MJ-2",
            "topic": "ABORT > ACCEPT",
            "rule": "Mesh ABORT beats any judge ACCEPT; no judge-over-judge execute",
            "prove": "compose_abort_gt_accept",
            "descriptor": "T-fa-r2-c",
        },
        {
            "id": "MJ-3",
            "topic": "Conflict fail-closed",
            "rule": "Conflicting digests/verdicts → Mesh ABORT; escalate I5; no auto-majority",
            "prove": "compose_conflict",
            "descriptor": "T-fa-r2-d",
        },
        {
            "id": "MJ-4",
            "topic": "Missing judge fail-closed",
            "rule": "Expected judge missing → ABORT; never invent ACCEPT",
            "prove": "compose_missing_judge",
            "descriptor": "T-fa-r2-e",
        },
        {
            "id": "MJ-5",
            "topic": "M1 NO_CONSENSUS_YET",
            "rule": "N=2 dual advisory (even agree) ≠ M1 consensus; mesh_accept=false",
            "prove": "compose_agree_no_m1",
            "descriptor": "T-fa-r2-f",
        },
        {
            "id": "REF-R2",
            "topic": "RefuseTransport default",
            "rule": "live off → ENGINE_DISABLED; zero network",
            "prove": "compose_refuse_default",
            "descriptor": "T-fa-r2-a",
        },
        {
            "id": "I5-R2",
            "topic": "I5 armed",
            "rule": "Kill-armed; kill → Refuse + ABORT; no post-kill network",
            "prove": "compose_i5_armed",
            "descriptor": "T-fa-r2-b",
        },
        {
            "id": "FENCE-R2",
            "topic": "Module fence",
            "rule": "Module LIVE_API_ENABLED False final on canary + LHT + R2",
            "prove": "suite post-condition T-fa-r2-h",
            "descriptor": "T-fa-r2-h",
        },
    ]


@dataclass
class JudgeAdvisory:
    judge_id: str
    mode: str  # real_http | mock_local | refused
    verdict: str
    digest: str
    advisory_only: bool = True
    mesh_accept: bool = False
    http_status: int | None = None
    raw_text_truncated: str | None = None
    error_code: str | None = None
    network: bool = False
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "judge_id": self.judge_id,
            "mode": self.mode,
            "verdict": self.verdict,
            "digest": self.digest,
            "advisory_only": self.advisory_only,
            "mesh_accept": False,
            "http_status": self.http_status,
            "raw_text_truncated": self.raw_text_truncated,
            "error_code": self.error_code,
            "network": self.network,
            "notes": list(self.notes),
            "response_digest": self.digest,
        }


@dataclass
class MeshDecision:
    verdict: str  # ABORT | ADVISORY — never ACCEPT from dual advisory
    mesh_accept: bool
    m1_status: str
    abort_code: str | None
    reason: str
    judges: list[dict[str, Any]]
    escalate_i5: bool
    auto_majority_execute: bool
    binding: str
    policy: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "verdict": self.verdict,
            "mesh_accept": self.mesh_accept,
            "m1_status": self.m1_status,
            "abort_code": self.abort_code,
            "reason": self.reason,
            "judges": list(self.judges),
            "escalate_i5": self.escalate_i5,
            "auto_majority_execute": self.auto_majority_execute,
            "binding": self.binding,
            "policy": self.policy,
            "advisory_only": True,
            "n_judges": len(self.judges),
            "authority": {
                "L_judge_execute": AUTHORITY_MATRIX["L_judge"][3],
                "I5_execute": AUTHORITY_MATRIX["Oversight_I5"][3],
                "Operator_execute": AUTHORITY_MATRIX["Operator"][3],
            },
        }


@dataclass
class ComposeResult:
    ok: bool
    descriptor: str
    notes: list[str] = field(default_factory=list)
    result: dict[str, Any] = field(default_factory=dict)
    mesh_accept: bool = False
    m1_status: str = M1_STATUS
    binding: str = "RefuseTransport"
    network_calls: int = 0
    real_http: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "descriptor": self.descriptor,
            "notes": list(self.notes),
            "result": dict(self.result),
            "mesh_accept": self.mesh_accept,
            "m1_status": self.m1_status,
            "binding": self.binding,
            "network_calls": self.network_calls,
            "real_http": self.real_http,
            "impl_cp": IMPL_CP_ID,
            "phase": PHASE,
            "LIVE_API_ENABLED_module_default": LIVE_API_ENABLED,
        }


def check_runbook_gates(
    *,
    secret_env_path: str | Path | None = None,
) -> dict[str, Any]:
    """Check Gate1 ENABLE + canary/LHT enablement + oob key presence (no key read into logs)."""
    path = Path(secret_env_path or DEFAULT_GEMINI_ENV_PATH)
    ack = Path(ENABLE_ACK)
    # Resolve ACK relative to repo if needed
    if not ack.is_file():
        # packaging lives under src/neural_mesh/packaging → repo root = parents[3]
        repo = Path(__file__).resolve().parents[3]
        ack = repo / ENABLE_ACK
    canary = evaluate_canary_enablement()
    lht = evaluate_lht_enablement()
    key_present = path.is_file() and path.stat().st_size > 0
    ack_present = ack.is_file()
    may = bool(
        canary.may_enable
        and lht.may_enable
        and key_present
        and ack_present
        and is_impl_cp_authorized()
    )
    reasons: list[str] = []
    if not canary.may_enable:
        reasons.extend([f"canary:{r}" for r in canary.reasons] or ["canary_may_enable_false"])
    if not lht.may_enable:
        reasons.extend([f"lht:{r}" for r in lht.reasons] or ["lht_may_enable_false"])
    if not key_present:
        reasons.append("oob_key_missing")
    if not ack_present:
        reasons.append("enable_ack_missing")
    return {
        "may_real_http": may,
        "reasons": reasons,
        "canary_may_enable": bool(canary.may_enable),
        "lht_may_enable": bool(lht.may_enable),
        "oob_key_present": key_present,
        "enable_ack_present": ack_present,
        "enable_ack": ENABLE_ACK,
        "secret_env_path": str(path),
        "impl_cp_authorized": True,
        "note": "may_real_http authorizes fenced session only; module LIVE stays False",
    }


def _digest_of(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()[:16]


def invoke_mock_advisory(
    *,
    judge_id: str = MOCK_JUDGE_ID,
    verdict: str = "ADVISORY",
    digest: str | None = None,
    prompt: str = R2_PROMPT,
    force_accept_claim: bool = False,
) -> JudgeAdvisory:
    """Deterministic local advisory (zero network)."""
    body = f"mock:{judge_id}:{prompt}:agree"
    dig = digest or _digest_of(body)
    v = "ACCEPT" if force_accept_claim else verdict
    return JudgeAdvisory(
        judge_id=judge_id,
        mode="mock_local",
        verdict=v,
        digest=dig,
        advisory_only=True,
        mesh_accept=False,
        http_status=None,
        raw_text_truncated=R2_OK_MARKER if not force_accept_claim else "MOCK_ACCEPT_CLAIM",
        network=False,
        notes=["deterministic mock advisory; never Mesh SoT"],
    )


def invoke_gemini_advisory(
    *,
    i5: I5KillArm | None = None,
    allow_real_http: bool = False,
    secret_env_path: str | Path | None = None,
    urlopen: Callable[..., Any] | None = None,
    prompt: str = R2_PROMPT,
    forced_mock_digest: str | None = None,
) -> JudgeAdvisory:
    """Gemini free advisory: real HTTP only if gates + allow_real_http; else mock-bound.

    Always restores runtime LIVE False. Never logs secrets.
    """
    assert_module_live_false()
    gates = check_runbook_gates(secret_env_path=secret_env_path)
    arm = i5 or arm_i5_for_canary()

    # Forced mock path for unit tests / conflict digests without network
    if urlopen is None and (not allow_real_http or not gates["may_real_http"]):
        dig = forced_mock_digest or _digest_of(f"gemini-mock-bound:{prompt}")
        return JudgeAdvisory(
            judge_id=GEMINI_JUDGE_ID,
            mode="mock_local",
            verdict="ADVISORY",
            digest=dig,
            advisory_only=True,
            mesh_accept=False,
            raw_text_truncated=R2_OK_MARKER,
            network=False,
            notes=[
                "gemini path mock-bound (real HTTP not requested or gates blocked)",
                f"gates_may_real_http={gates['may_real_http']}",
                *([f"gate_reasons={gates['reasons']}"] if gates["reasons"] else []),
            ],
        )

    # Injected urlopen → still counts as non-real (test double) unless allow_real_http
    if urlopen is not None and not allow_real_http:
        dig = forced_mock_digest or _digest_of(f"gemini-urlopen-mock:{prompt}")
        # Exercise LiveHttpTransport with injected urlopen under session
        calls = {"n": 0}

        def wrapped(req: Any, timeout: float = 30.0) -> Any:
            calls["n"] += 1
            return urlopen(req, timeout=timeout)

        with live_api_canary_session(i5=arm, enablement_ok=True):
            t = LiveHttpTransport(
                i5=arm,
                secret_env_path=str(secret_env_path or DEFAULT_GEMINI_ENV_PATH),
                _load_key=lambda _p: "test-key-not-a-real-secret",
                _sleeper=lambda _s: None,
                _urlopen=wrapped,
            )
            out = t.call(
                {
                    "prompt": prompt,
                    "request_id": f"r2-gemini-mock-{int(time.time())}",
                    "secret_handle": DEFAULT_SECRET_HANDLE,
                },
                idempotency_key=f"r2-gemini-mock-{dig}",
            )
        set_runtime_live_api_enabled(False)
        return JudgeAdvisory(
            judge_id=GEMINI_JUDGE_ID,
            mode="mock_local",
            verdict=str(out.get("verdict") or "ADVISORY"),
            digest=str(out.get("digest") or dig),
            advisory_only=bool(out.get("advisory_only", True)),
            mesh_accept=False,
            http_status=out.get("http_status"),  # type: ignore[arg-type]
            raw_text_truncated=str(out.get("raw_text") or "")[:120] or None,
            error_code=out.get("error_code"),  # type: ignore[arg-type]
            network=False,
            notes=["injected urlopen mock under session; not real HTTP"],
        )

    # Real HTTP path under fences
    if not gates["may_real_http"]:
        return JudgeAdvisory(
            judge_id=GEMINI_JUDGE_ID,
            mode="refused",
            verdict="ABORT",
            digest=_digest_of("gemini-refused-gates"),
            advisory_only=True,
            mesh_accept=False,
            error_code="ENGINE_DISABLED",
            network=False,
            notes=["real HTTP refused: runbook gates not satisfied", *gates["reasons"]],
        )

    notes: list[str] = ["real HTTP under ENABLE_UNDER_FENCES + CP-0075/0078"]
    try:
        with live_api_canary_session(i5=arm, enablement_ok=True):
            t = LiveHttpTransport(
                i5=arm,
                secret_env_path=str(secret_env_path or DEFAULT_GEMINI_ENV_PATH),
                _sleeper=lambda _s: None,
            )
            out = t.call(
                {
                    "prompt": prompt,
                    "request_id": f"r2-gemini-live-{int(time.time())}",
                    "secret_handle": DEFAULT_SECRET_HANDLE,
                },
                idempotency_key=f"r2-gemini-live-{int(time.time())}",
            )
        set_runtime_live_api_enabled(False)
        text = str(out.get("raw_text") or "")
        truncated = text[:120] if text else None
        # Scrub accidental secret-looking prefixes from truncated text
        _secretish = ("AI" + "za", "sk" + "-")
        if truncated and any(n in truncated for n in _secretish):
            truncated = "[redacted]"
        ok = bool(out.get("ok")) and str(out.get("verdict")) != "ABORT"
        status = out.get("http_status")
        if status == 429 or out.get("error_code") == "ENGINE_RATE_LIMIT":
            notes.append("quota/rate-limit observed — document honestly")
        return JudgeAdvisory(
            judge_id=GEMINI_JUDGE_ID,
            mode="real_http",
            verdict=str(out.get("verdict") or ("ADVISORY" if ok else "ABORT")),
            digest=str(out.get("digest") or _digest_of(text or "empty")),
            advisory_only=True,
            mesh_accept=False,
            http_status=status if isinstance(status, int) else None,
            raw_text_truncated=truncated,
            error_code=out.get("error_code"),  # type: ignore[arg-type]
            network=bool(out.get("network")),
            notes=notes,
        )
    except Exception as exc:  # noqa: BLE001
        set_runtime_live_api_enabled(False)
        arm.kill(reason=f"R2_GEMINI_EXCEPTION:{type(exc).__name__}")
        return JudgeAdvisory(
            judge_id=GEMINI_JUDGE_ID,
            mode="real_http",
            verdict="ABORT",
            digest=_digest_of(f"exc:{type(exc).__name__}"),
            advisory_only=True,
            mesh_accept=False,
            error_code="HUMAN_ABORT",
            network=False,
            notes=[*notes, f"exception:{type(exc).__name__}"],
        )
    finally:
        set_runtime_live_api_enabled(False)


def mesh_resolve_multi_judge(
    judges: list[JudgeAdvisory],
    *,
    expected_ids: list[str] | None = None,
    mesh_force_abort: bool = False,
    mesh_abort_reason: str = "Mesh ABORT > judge ACCEPT (Authority Matrix)",
) -> MeshDecision:
    """Mesh SoT resolve under Authority Matrix — never ACCEPT from dual advisory."""
    expected = expected_ids or [GEMINI_JUDGE_ID, MOCK_JUDGE_ID]
    present = {j.judge_id for j in judges}
    missing = [jid for jid in expected if jid not in present]

    # Hygiene via dual digest (reuse spike helper)
    attributions = [j.to_dict() for j in judges]
    hygiene = evaluate_dual_digest_hygiene(attributions)

    # Missing judge → fail-closed
    if missing:
        return MeshDecision(
            verdict="ABORT",
            mesh_accept=False,
            m1_status=M1_STATUS,
            abort_code="JUDGE_MISSING",
            reason=f"Missing judges {missing} → fail-closed; no invent ACCEPT",
            judges=attributions,
            escalate_i5=True,
            auto_majority_execute=False,
            binding="RefuseTransport",
            policy=ABORT_GT_ACCEPT,
        )

    # Mesh-forced ABORT (ABORT > ACCEPT) even if a judge claims ACCEPT
    if mesh_force_abort:
        return MeshDecision(
            verdict="ABORT",
            mesh_accept=False,
            m1_status=M1_STATUS,
            abort_code="POLICY_ABORT",
            reason=mesh_abort_reason,
            judges=attributions,
            escalate_i5=True,
            auto_majority_execute=False,
            binding="RefuseTransport",
            policy=ABORT_GT_ACCEPT,
        )

    # Conflict (disagree digests or mixed verdicts that aren't pure advisory-agree)
    if hygiene["disagreement"]:
        return MeshDecision(
            verdict="ABORT",
            mesh_accept=False,
            m1_status=M1_STATUS,
            abort_code="JUDGE_CONFLICT",
            reason="Conflicting judges → fail-closed; no auto-majority execute",
            judges=attributions,
            escalate_i5=True,
            auto_majority_execute=False,
            binding="RefuseTransport",
            policy=ABORT_GT_ACCEPT,
        )

    # Any judge claiming ACCEPT still cannot become Mesh ACCEPT
    any_accept_claim = any(j.verdict == "ACCEPT" for j in judges)
    if any_accept_claim:
        return MeshDecision(
            verdict="ABORT",
            mesh_accept=False,
            m1_status=M1_STATUS,
            abort_code="POLICY_ABORT",
            reason="Judge ACCEPT claim ignored; Mesh ABORT > ACCEPT under matrix",
            judges=attributions,
            escalate_i5=True,
            auto_majority_execute=False,
            binding="RefuseTransport",
            policy=ABORT_GT_ACCEPT,
        )

    # Agree advisory-only — still NO_CONSENSUS_YET; never Mesh ACCEPT
    assert hygiene["mesh_accept"] is False
    assert hygiene["m1_status"] == SPIKE_M1_STATUS or hygiene["m1_status"] == M1_STATUS
    return MeshDecision(
        verdict="ADVISORY",
        mesh_accept=False,
        m1_status=M1_STATUS,
        abort_code=None,
        reason="dual advisory agree ≠ M1 consensus; mesh_accept=false",
        judges=attributions,
        escalate_i5=False,
        auto_majority_execute=False,
        binding="RefuseTransport",
        policy=ABORT_GT_ACCEPT,
    )


def compose_refuse_default() -> ComposeResult:
    """T-fa-r2-a: live off → RefuseTransport; zero network."""
    assert_module_live_false()
    set_runtime_live_api_enabled(False)
    i5 = arm_i5_for_canary()
    calls = {"n": 0}

    def boom(*_a: Any, **_k: Any) -> Any:
        calls["n"] += 1
        raise AssertionError("network must not open when live off")

    t = LiveHttpTransport(
        i5=i5,
        _load_key=lambda _p: "test-key-not-a-real-secret",
        _sleeper=lambda _s: None,
        _urlopen=boom,
    )
    out = t.call({"prompt": "r2-refuse"}, idempotency_key="r2-a")
    health = t.health()
    rt = RefuseTransport().call({"prompt": "r2-rt"})
    ok = (
        out.get("ok") is False
        and out.get("error_code") == "ENGINE_DISABLED"
        and calls["n"] == 0
        and health.get("binding") == "RefuseTransport"
        and rt.get("abort", {}).get("code") == "ENGINE_DISABLED"
        and runtime_live_api_enabled() is False
        and AUTHORITY_MATRIX["L_judge"][3] is False
    )
    notes = (
        ["refuse when live off; zero network; L_judge cannot execute"]
        if ok
        else [f"unexpected: {out!r} health={health!r}"]
    )
    return ComposeResult(
        ok=ok,
        descriptor="T-fa-r2-a",
        notes=notes,
        result={"lht": out, "refuse": rt, "health": health},
        mesh_accept=False,
        binding="RefuseTransport",
        network_calls=calls["n"],
    )


def compose_i5_armed() -> ComposeResult:
    """T-fa-r2-b: I5 armed; kill → ABORT + Refuse; zero post-kill network."""
    assert_module_live_false()
    i5 = arm_i5_for_canary()
    calls = {"n": 0}

    def boom(*_a: Any, **_k: Any) -> Any:
        calls["n"] += 1
        raise AssertionError("network must not open after I5 kill")

    notes: list[str] = []
    with live_api_canary_session(i5=i5, enablement_ok=True):
        t = LiveHttpTransport(
            i5=i5,
            _load_key=lambda _p: "test-key-not-a-real-secret",
            _sleeper=lambda _s: None,
            _urlopen=boom,
        )
        kill_receipt = i5.kill("R2_I5_ARMED_COMPOSE")
        out = t.call({"prompt": "r2-kill"}, idempotency_key="r2-b")
        health = t.health()
        ok = (
            out.get("verdict") == "ABORT"
            and out.get("error_code") in ("ENGINE_DISABLED", "HUMAN_ABORT")
            and calls["n"] == 0
            and i5.killed is True
            and health.get("binding") == "RefuseTransport"
            and (
                kill_receipt.get("binding") == "RefuseTransport"
                or kill_receipt.get("kill_authority") == "Oversight_I5"
            )
            and AUTHORITY_MATRIX["Oversight_I5"][3] is False
        )
        if ok:
            notes.append("I5 kill → ABORT + Refuse; I5 cannot execute; zero post-kill network")
        else:
            notes.append(f"unexpected i5: {out!r} health={health!r}")
    if runtime_live_api_enabled():
        ok = False
        notes.append("runtime LIVE not restored False")
    else:
        notes.append("session restored runtime LIVE False")
    return ComposeResult(
        ok=ok,
        descriptor="T-fa-r2-b",
        notes=notes,
        result=out,
        mesh_accept=False,
        binding="RefuseTransport",
        network_calls=calls["n"],
    )


def compose_abort_gt_accept() -> ComposeResult:
    """T-fa-r2-c: Mesh ABORT beats judge ACCEPT claims."""
    gemini = invoke_mock_advisory(
        judge_id=GEMINI_JUDGE_ID, force_accept_claim=True, digest="accept-claim-a"
    )
    mock = invoke_mock_advisory(
        judge_id=MOCK_JUDGE_ID, force_accept_claim=True, digest="accept-claim-b"
    )
    # Force Mesh ABORT regardless of judge claims
    decision = mesh_resolve_multi_judge(
        [gemini, mock],
        mesh_force_abort=True,
        mesh_abort_reason="Mesh ABORT > peer ACCEPT (T-fa-r2-c)",
    )
    ok = (
        decision.verdict == "ABORT"
        and decision.mesh_accept is False
        and decision.abort_code == "POLICY_ABORT"
        and decision.auto_majority_execute is False
        and decision.m1_status == M1_STATUS
        and gemini.verdict == "ACCEPT"
        and mock.verdict == "ACCEPT"
    )
    return ComposeResult(
        ok=ok,
        descriptor="T-fa-r2-c",
        notes=["Mesh ABORT > judge ACCEPT; no silent ACCEPT"] if ok else ["abort_gt_accept failed"],
        result=decision.to_dict(),
        mesh_accept=False,
        m1_status=M1_STATUS,
        binding="RefuseTransport",
    )


def compose_conflict() -> ComposeResult:
    """T-fa-r2-d: conflicting digests → fail-closed ABORT."""
    gemini = invoke_mock_advisory(
        judge_id=GEMINI_JUDGE_ID, digest="conflict-digest-aaa", verdict="ADVISORY"
    )
    mock = invoke_mock_advisory(
        judge_id=MOCK_JUDGE_ID, digest="conflict-digest-bbb", verdict="ADVISORY"
    )
    decision = mesh_resolve_multi_judge([gemini, mock])
    ok = (
        decision.verdict == "ABORT"
        and decision.abort_code == "JUDGE_CONFLICT"
        and decision.mesh_accept is False
        and decision.escalate_i5 is True
        and decision.auto_majority_execute is False
        and decision.m1_status == M1_STATUS
    )
    return ComposeResult(
        ok=ok,
        descriptor="T-fa-r2-d",
        notes=["conflict → fail-closed ABORT; escalate I5"] if ok else ["conflict failed"],
        result=decision.to_dict(),
        mesh_accept=False,
        m1_status=M1_STATUS,
        binding="RefuseTransport",
    )


def compose_missing_judge() -> ComposeResult:
    """T-fa-r2-e: missing expected judge → fail-closed ABORT."""
    only = invoke_mock_advisory(judge_id=MOCK_JUDGE_ID, digest="only-one")
    decision = mesh_resolve_multi_judge(
        [only], expected_ids=[GEMINI_JUDGE_ID, MOCK_JUDGE_ID]
    )
    ok = (
        decision.verdict == "ABORT"
        and decision.abort_code == "JUDGE_MISSING"
        and decision.mesh_accept is False
        and decision.auto_majority_execute is False
        and GEMINI_JUDGE_ID not in {j["judge_id"] for j in decision.judges}
    )
    return ComposeResult(
        ok=ok,
        descriptor="T-fa-r2-e",
        notes=["missing judge → fail-closed; no invent ACCEPT"] if ok else ["missing failed"],
        result=decision.to_dict(),
        mesh_accept=False,
        m1_status=M1_STATUS,
        binding="RefuseTransport",
    )


def compose_agree_no_m1() -> ComposeResult:
    """T-fa-r2-f: agreeing digests still NO_CONSENSUS_YET; mesh_accept=false."""
    shared = _digest_of("r2-agree-shared")
    gemini = invoke_mock_advisory(judge_id=GEMINI_JUDGE_ID, digest=shared)
    mock = invoke_mock_advisory(judge_id=MOCK_JUDGE_ID, digest=shared)
    decision = mesh_resolve_multi_judge([gemini, mock])
    ok = (
        decision.verdict == "ADVISORY"
        and decision.mesh_accept is False
        and decision.m1_status == M1_STATUS
        and decision.auto_majority_execute is False
        and N_JUDGES == 2
    )
    return ComposeResult(
        ok=ok,
        descriptor="T-fa-r2-f",
        notes=(
            ["agree dual advisory ≠ M1; N=2 stays NO_CONSENSUS_YET"]
            if ok
            else ["agree_no_m1 failed"]
        ),
        result=decision.to_dict(),
        mesh_accept=False,
        m1_status=M1_STATUS,
        binding="RefuseTransport",
    )


def compose_live_mock_bound(
    *,
    allow_real_http: bool = False,
    secret_env_path: str | Path | None = None,
    urlopen: Callable[..., Any] | None = None,
) -> ComposeResult:
    """T-fa-r2-g: bind Gemini (real or mock-bound) + mock local; resolve under matrix."""
    assert_module_live_false()
    gates = check_runbook_gates(secret_env_path=secret_env_path)
    i5 = arm_i5_for_canary()
    gemini = invoke_gemini_advisory(
        i5=i5,
        allow_real_http=allow_real_http,
        secret_env_path=secret_env_path,
        urlopen=urlopen,
    )
    # Align mock digest with gemini when gemini is advisory-ok so agree path is clean;
    # if gemini aborted (quota/error), still bind mock and let mesh resolve conflict/abort.
    if gemini.verdict == "ADVISORY" and gemini.digest:
        mock = invoke_mock_advisory(judge_id=MOCK_JUDGE_ID, digest=gemini.digest)
    else:
        mock = invoke_mock_advisory(judge_id=MOCK_JUDGE_ID, digest="mock-local-independent")
    decision = mesh_resolve_multi_judge([gemini, mock])
    set_runtime_live_api_enabled(False)

    real = gemini.mode == "real_http" and bool(gemini.network)
    # Suite PASSes when:
    # - both judges bound
    # - mesh_accept false
    # - m1 NO_CONSENSUS_YET
    # - if real HTTP attempted: either advisory ok or honest quota/error documented
    # - if mock-bound: decision is ADVISORY (agree) or ABORT (conflict) — never ACCEPT
    bound_ok = {GEMINI_JUDGE_ID, MOCK_JUDGE_ID} <= {gemini.judge_id, mock.judge_id}
    hygiene_ok = (
        decision.mesh_accept is False
        and decision.m1_status == M1_STATUS
        and decision.verdict in ("ADVISORY", "ABORT")
        and decision.auto_majority_execute is False
        and runtime_live_api_enabled() is False
    )
    if allow_real_http and gates["may_real_http"]:
        # Real path attempted — pass if we got a bound result without inventing ACCEPT
        attempt_ok = gemini.mode in ("real_http", "refused", "mock_local")
        if gemini.http_status == 429 or gemini.error_code == "ENGINE_RATE_LIMIT":
            notes_extra = ["real HTTP quota blocked — documented honestly; mock-bound still ok"]
            attempt_ok = True
        elif gemini.mode == "real_http" and gemini.verdict == "ADVISORY" and gemini.http_status == 200:
            notes_extra = ["real HTTP 200 advisory bound with mock; mesh_accept=false"]
        elif gemini.mode == "real_http":
            notes_extra = [
                f"real HTTP attempted status={gemini.http_status} verdict={gemini.verdict} "
                f"err={gemini.error_code} — documented; mesh fail-closed held"
            ]
            attempt_ok = True  # honest document still completes R2
        else:
            notes_extra = ["gates allowed but fell back; see gemini notes"]
            attempt_ok = True
    else:
        attempt_ok = gemini.mode == "mock_local" and decision.verdict in ("ADVISORY", "ABORT")
        notes_extra = [
            "mock-bound Gemini + mock local (real HTTP not requested or gates blocked)"
        ]

    ok = bound_ok and hygiene_ok and attempt_ok and LIVE_API_ENABLED is False
    notes = [
        f"gemini_mode={gemini.mode}",
        f"mock_mode={mock.mode}",
        f"mesh_verdict={decision.verdict}",
        f"m1={decision.m1_status}",
        f"real_http={real}",
        f"gates_may={gates['may_real_http']}",
        *notes_extra,
        *gemini.notes[:3],
    ]
    return ComposeResult(
        ok=ok,
        descriptor="T-fa-r2-g",
        notes=notes if ok else [*notes, "live_mock_bound failed"],
        result={
            "gemini": gemini.to_dict(),
            "mock": mock.to_dict(),
            "mesh": decision.to_dict(),
            "gates": {k: v for k, v in gates.items() if k != "secret_env_path"},
        },
        mesh_accept=False,
        m1_status=M1_STATUS,
        binding="RefuseTransport",
        network_calls=1 if real else 0,
        real_http=real,
    )


def run_r2_compose_suite(
    *,
    allow_real_http: bool = False,
    secret_env_path: str | Path | None = None,
) -> dict[str, Any]:
    """Run R2 multi-judge compose; always leave runtime LIVE False."""
    set_runtime_live_api_enabled(False)
    assert_module_live_false()
    gates = check_runbook_gates(secret_env_path=secret_env_path)

    results = [
        compose_refuse_default(),
        compose_i5_armed(),
        compose_abort_gt_accept(),
        compose_conflict(),
        compose_missing_judge(),
        compose_agree_no_m1(),
        compose_live_mock_bound(
            allow_real_http=allow_real_http,
            secret_env_path=secret_env_path,
        ),
    ]

    restore_ok = runtime_live_api_enabled() is False
    module_ok = (
        LIVE_API_ENABLED is False
        and CANARY_LIVE_API_ENABLED is False
        and LHT_LIVE_API_ENABLED is False
    )
    h_ok = ComposeResult(
        ok=restore_ok and module_ok,
        descriptor="T-fa-r2-h",
        notes=(
            ["module+runtime LIVE False; RefuseTransport default"]
            if (restore_ok and module_ok)
            else ["fence leak"]
        ),
        result={
            "r2": LIVE_API_ENABLED,
            "canary": CANARY_LIVE_API_ENABLED,
            "lht": LHT_LIVE_API_ENABLED,
            "runtime": runtime_live_api_enabled(),
        },
        mesh_accept=False,
        binding="RefuseTransport",
    )
    results.append(h_ok)
    set_runtime_live_api_enabled(False)

    real_http_used = any(r.real_http for r in results)
    all_ok = all(r.ok for r in results)
    return {
        "schema": "mesh.judge.full_adapter_r2_multi_judge_suite/v0",
        "ok": all_ok,
        "phase": PHASE,
        "impl_cp": IMPL_CP_ID,
        "design_cp": DESIGN_CP_ID,
        "prior_cp": PRIOR_CP,
        "descriptors": [r.to_dict() for r in results],
        "checklist": r2_checklist_rows(),
        "authorization": impl_cp_authorization_record(),
        "gates": {k: v for k, v in gates.items() if k != "secret_env_path"},
        "LIVE_API_ENABLED_module_final": LIVE_API_ENABLED,
        "runtime_live_api_enabled_final": runtime_live_api_enabled(),
        "m1_status": M1_STATUS,
        "n_judges": N_JUDGES,
        "abort_gt_accept": ABORT_GT_ACCEPT,
        "real_http_used": real_http_used,
        "r3_r5_authorized": False,
        "binding_final": "RefuseTransport",
    }


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="CP-0083 R2 multi-judge compose")
    parser.add_argument(
        "--real-http",
        action="store_true",
        help="Attempt one real Gemini free HTTP under fences if gates pass",
    )
    parser.add_argument("--secret-env", default=str(DEFAULT_GEMINI_ENV_PATH))
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    suite = run_r2_compose_suite(
        allow_real_http=args.real_http,
        secret_env_path=args.secret_env,
    )
    # Scrub anything secret-looking before print
    blob = json.dumps(suite, indent=2, sort_keys=True)
    for needle in ("AI" + "za", "sk" + "-", "Bearer "):
        if needle in blob:
            blob = blob.replace(needle, "[REDACTED]")
    if args.json:
        print(blob)
    else:
        print(
            f"ok={suite['ok']} phase={suite['phase']} real_http={suite['real_http_used']} "
            f"LIVE_final={suite['LIVE_API_ENABLED_module_final']} m1={suite['m1_status']}"
        )
        for d in suite["descriptors"]:
            print(f"  {d['descriptor']}: ok={d['ok']} real={d.get('real_http')} notes={d['notes'][:2]}")
