"""CP-0082 — Phase R1: full-adapter SoT + RefuseTransport + I5 compose (thin IMPL).

Composes packaging LiveHttpTransport v0 + Gemini free canary path under fences.
Docs/tests descriptors only — **does not** permanently enable LIVE, raise n_real_http,
authorize R2–R5, invent F4, or unlock NO_HELD.

Authority: CP-0081 DESIGN_ONLY phases · operator R1 authorize · LIVE_API_ENABLED=False.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Mapping

from neural_mesh.packaging.l_judge_gemini_free_canary_impl import (
    I5KillArm,
    arm_i5_for_canary,
    live_api_canary_session,
    runtime_live_api_enabled,
    set_runtime_live_api_enabled,
    LIVE_API_ENABLED as CANARY_LIVE_API_ENABLED,
)
from neural_mesh.packaging.l_judge_live_adapter_safety import RefuseTransport
from neural_mesh.packaging.l_judge_live_http_transport import (
    LIVE_API_ENABLED as LHT_LIVE_API_ENABLED,
    LiveHttpTransport,
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
    "DESCRIPTOR_IDS",
    "SOT_BOUNDARIES",
    "ComposeResult",
    "is_impl_cp_authorized",
    "impl_cp_authorization_record",
    "r1_checklist_rows",
    "compose_refuse_when_live_off",
    "compose_i5_kill",
    "compose_advisory_not_sot",
    "run_r1_compose_suite",
    "assert_module_live_false",
]

PACKAGE_HELD = "0.18.0"
CYCLE = 78
SEAL_CP = "CP-0082"
PRIOR_CP = "CP-0081"
IMPL_CP_ID = "CP-0082"
DESIGN_CP_ID = "CP-0081"
# Product / module default stays False — R1 does not permanently enable.
LIVE_API_ENABLED = False
PHASE = "R1"

# Negative-test descriptor IDs for full-adapter R1 compose surface.
DESCRIPTOR_IDS: tuple[str, ...] = (
    "T-fa-r1-a",  # refuse when live off (zero network)
    "T-fa-r1-b",  # I5 kill → ABORT + subsequent Refuse
    "T-fa-r1-c",  # advisory ≠ SoT; mesh_accept stays false
    "T-fa-r1-d",  # session restore → runtime LIVE False + Refuse binding
    "T-fa-r1-e",  # module LIVE_API_ENABLED False on both canary + LHT surfaces
)

SOT_BOUNDARIES: tuple[str, ...] = (
    "Mesh = SoT for goals / evidence / continuity / ABORT",
    "Judge = propose-only (Authority Matrix); L_judge cannot execute",
    "Advisory digests / Gemini text never become Mesh ACCEPT or continuity SoT",
    "Resume from Mesh registry+ledger only — not LLM chat context",
    "canary 200 ≠ live ready · ADVISORY ≠ SoT · seal_candidate ≠ F4 · ENABLE ≠ product",
)


def is_impl_cp_authorized() -> bool:
    """R1 thin IMPL is authorized under this CP; R2–R5 are not."""
    return True


def impl_cp_authorization_record() -> dict[str, Any]:
    return {
        "schema": "mesh.judge.full_adapter_r1_compose_auth/v0",
        "authorized": True,
        "impl_cp": IMPL_CP_ID,
        "design_cp": DESIGN_CP_ID,
        "phase": PHASE,
        "authorizes": [
            "R1 checklist",
            "negative-test descriptors",
            "unit compose SoT + RefuseTransport + I5 on packaging LiveHttpTransport + canary path",
        ],
        "does_not_authorize": [
            "R2 multi-judge live/mock-bound RV",
            "R3 Gate6 live-measurement seal / raise n_real_http",
            "R4 streaming DEFER or streaming RV",
            "R5 F4 product ACK / permanent module True",
            "permanent LIVE_API_ENABLED",
            "F4 invent",
            "NO_HELD unlock",
            "push/tags/secrets",
        ],
        "live_api_enabled_module_default": LIVE_API_ENABLED,
        "canary_live_api_enabled_constant": CANARY_LIVE_API_ENABLED,
        "lht_live_api_enabled_constant": LHT_LIVE_API_ENABLED,
        "permanent_live_enable": False,
        "package_held": PACKAGE_HELD,
        "cycle": CYCLE,
        "surfaces": ["LiveHttpTransport", "GeminiFreeCanary", "RefuseTransport", "I5KillArm"],
    }


def assert_module_live_false() -> None:
    """Hard fence: packaging module constants must stay False."""
    if LIVE_API_ENABLED or CANARY_LIVE_API_ENABLED or LHT_LIVE_API_ENABLED:
        raise AssertionError("LIVE_API_ENABLED module constant must stay False under R1")

def _mesh_accept_of(out: Mapping[str, Any] | None) -> bool:
    """Missing mesh_accept on refuse path counts as false (advisory never SoT)."""
    if not out:
        return False
    if "mesh_accept" in out:
        return bool(out["mesh_accept"])
    # RefuseTransport bare abort shape has no mesh_accept key — treat as false.
    return False


def _is_abort(out: Mapping[str, Any] | None) -> bool:
    if not out:
        return False
    if out.get("verdict") == "ABORT":
        return True
    abort = out.get("abort")
    if isinstance(abort, dict) and abort.get("code"):
        return True
    return out.get("ok") is False and out.get("error_code") in (
        "ENGINE_DISABLED",
        "HUMAN_ABORT",
    )


def r1_checklist_rows() -> list[dict[str, Any]]:
    """Ordered SoT / Refuse / I5 compose checklist rows (docs + code share)."""
    return [
        {
            "id": "SOT-1",
            "topic": "Mesh SoT",
            "rule": "Mesh owns goals / evidence / continuity / ABORT",
            "prove": "compose receipt keeps mesh_accept=false on advisory",
            "descriptor": "T-fa-r1-c",
        },
        {
            "id": "SOT-2",
            "topic": "Judge propose-only",
            "rule": "L_judge cannot execute; I5/Operator own kill and live-enable",
            "prove": "I5 kill → ABORT; no post-kill execute",
            "descriptor": "T-fa-r1-b",
        },
        {
            "id": "SOT-3",
            "topic": "Advisory ≠ SoT",
            "rule": "Gemini/advisory text never becomes Mesh ACCEPT or continuity SoT",
            "prove": "happy mock advisory → advisory_only=true, mesh_accept=false",
            "descriptor": "T-fa-r1-c",
        },
        {
            "id": "REF-1",
            "topic": "RefuseTransport default ON",
            "rule": "enabled=false → ENGINE_DISABLED; zero network",
            "prove": "LiveHttpTransport.call with live off never opens network",
            "descriptor": "T-fa-r1-a",
        },
        {
            "id": "REF-2",
            "topic": "Session restore",
            "rule": "After canary/LHT session, runtime LIVE False + Refuse binding",
            "prove": "live_api_canary_session finally restores False",
            "descriptor": "T-fa-r1-d",
        },
        {
            "id": "I5-1",
            "topic": "Kill-armed compose",
            "rule": "Mid-flight / pre-call kill → Refuse + ABORT; no resume without re-ACK",
            "prove": "I5.kill then call → ABORT; health binding RefuseTransport",
            "descriptor": "T-fa-r1-b",
        },
        {
            "id": "I5-2",
            "topic": "Module fence",
            "rule": "Module LIVE_API_ENABLED stays False on canary + LHT surfaces",
            "prove": "constants False after suite",
            "descriptor": "T-fa-r1-e",
        },
    ]


@dataclass
class ComposeResult:
    ok: bool
    descriptor: str
    notes: list[str] = field(default_factory=list)
    result: dict[str, Any] = field(default_factory=dict)
    mesh_accept: bool = False
    binding: str = "RefuseTransport"
    network_calls: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "descriptor": self.descriptor,
            "notes": list(self.notes),
            "result": dict(self.result),
            "mesh_accept": self.mesh_accept,
            "binding": self.binding,
            "network_calls": self.network_calls,
            "impl_cp": IMPL_CP_ID,
            "phase": PHASE,
            "LIVE_API_ENABLED_module_default": LIVE_API_ENABLED,
        }


def _fake_ok_transport(
    i5: I5KillArm,
    *,
    urlopen: Callable[..., Any] | None = None,
) -> LiveHttpTransport:
    return LiveHttpTransport(
        i5=i5,
        _load_key=lambda _p: "test-key-not-a-real-secret",
        _sleeper=lambda _s: None,
        _urlopen=urlopen,
    )


def compose_refuse_when_live_off() -> ComposeResult:
    """T-fa-r1-a: live off → RefuseTransport; zero network on full-adapter surface."""
    assert_module_live_false()
    set_runtime_live_api_enabled(False)
    i5 = arm_i5_for_canary()
    calls = {"n": 0}

    def boom(*_a: Any, **_k: Any) -> Any:
        calls["n"] += 1
        raise AssertionError("network must not open when live off")

    t = _fake_ok_transport(i5, urlopen=boom)
    out = t.call({"prompt": "r1-refuse"}, idempotency_key="r1-a")
    health = t.health()
    notes: list[str] = []
    ok = (
        out.get("ok") is False
        and out.get("error_code") == "ENGINE_DISABLED"
        and _is_abort(out)
        and _mesh_accept_of(out) is False
        and calls["n"] == 0
        and health.get("binding") == "RefuseTransport"
        and runtime_live_api_enabled() is False
    )
    if not ok:
        notes.append(f"unexpected refuse compose: {out!r} health={health!r} calls={calls['n']}")
    else:
        notes.append("refuse when live off; zero network; mesh_accept=false")
    # Also prove bare RefuseTransport still default
    rt = RefuseTransport().call({"prompt": "r1-rt"})
    if rt.get("abort", {}).get("code") != "ENGINE_DISABLED":
        ok = False
        notes.append("RefuseTransport bare call failed")
    return ComposeResult(
        ok=ok,
        descriptor="T-fa-r1-a",
        notes=notes,
        result=out,
        mesh_accept=_mesh_accept_of(out),
        binding=str(health.get("binding") or "RefuseTransport"),
        network_calls=calls["n"],
    )


def compose_i5_kill() -> ComposeResult:
    """T-fa-r1-b: I5 kill compose → ABORT; subsequent Refuse; no post-kill network."""
    assert_module_live_false()
    i5 = arm_i5_for_canary()
    calls = {"n": 0}

    def urlopen(_req: Any, timeout: float = 30.0) -> Any:
        calls["n"] += 1
        raise AssertionError("network must not open after I5 kill")

    notes: list[str] = []
    with live_api_canary_session(i5=i5, enablement_ok=True):
        t = _fake_ok_transport(i5, urlopen=urlopen)
        kill_receipt = i5.kill("R1_I5_KILL_COMPOSE")
        out = t.call({"prompt": "r1-kill"}, idempotency_key="r1-b")
        health = t.health()
        bind_ok = (
            kill_receipt.get("binding") == "RefuseTransport"
            or kill_receipt.get("kill_authority") == "Oversight_I5"
        )
        ok = (
            _is_abort(out)
            and out.get("error_code") in ("ENGINE_DISABLED", "HUMAN_ABORT")
            and _mesh_accept_of(out) is False
            and calls["n"] == 0
            and i5.killed is True
            and health.get("binding") == "RefuseTransport"
            and bind_ok
        )
        if not ok:
            notes.append(f"unexpected i5 kill compose: {out!r} health={health!r}")
        else:
            notes.append("I5 kill → ABORT + Refuse binding; zero post-kill network")
        # No resume without re-ACK: killed arm still refuses
        out2 = t.call({"prompt": "r1-kill-2"}, idempotency_key="r1-b2")
        if not _is_abort(out2) or _mesh_accept_of(out2) is not False:
            ok = False
            notes.append("post-kill second call did not stay ABORT/mesh_accept=false")
    # Session must restore runtime False
    if runtime_live_api_enabled():
        ok = False
        notes.append("runtime LIVE not restored False after kill session")
    else:
        notes.append("session restored runtime LIVE False")
    return ComposeResult(
        ok=ok,
        descriptor="T-fa-r1-b",
        notes=notes,
        result=out,
        mesh_accept=_mesh_accept_of(out),
        binding="RefuseTransport",
        network_calls=calls["n"],
    )


def compose_advisory_not_sot() -> ComposeResult:
    """T-fa-r1-c: mock advisory happy path still mesh_accept=false (advisory ≠ SoT)."""
    assert_module_live_false()
    i5 = arm_i5_for_canary()
    calls = {"n": 0}

    class _FakeResp:
        def __init__(self, body: bytes, status: int = 200):
            self._body = body
            self.status = status

        def read(self) -> bytes:
            return self._body

        def __enter__(self) -> "_FakeResp":
            return self

        def __exit__(self, *_a: Any) -> bool:
            return False

    import json

    body = json.dumps(
        {"candidates": [{"content": {"parts": [{"text": "MESH_R1_ADVISORY_OK"}]}}]}
    ).encode()

    def urlopen(_req: Any, timeout: float = 30.0) -> Any:
        calls["n"] += 1
        return _FakeResp(body)

    notes: list[str] = []
    with live_api_canary_session(i5=i5, enablement_ok=True):
        t = _fake_ok_transport(i5, urlopen=urlopen)
        out = t.call({"prompt": "r1-advisory"}, idempotency_key="r1-c")
        ok = (
            out.get("ok") is True
            and out.get("verdict") == "ADVISORY"
            and out.get("advisory_only") is True
            and out.get("mesh_accept") is False
            and out.get("LIVE_API_ENABLED_module_default") is False
            and calls["n"] == 1
        )
        if not ok:
            notes.append(f"unexpected advisory compose: {out!r}")
        else:
            notes.append("advisory HTTP-ok mock ≠ Mesh SoT; mesh_accept=false")
        # Continuity SoT hygiene: advisory must not imply Mesh ACCEPT
        for boundary in SOT_BOUNDARIES:
            if "never become Mesh ACCEPT" in boundary or "ADVISORY ≠ SoT" in boundary:
                notes.append(f"boundary cited: {boundary[:48]}…")
    if runtime_live_api_enabled():
        ok = False
        notes.append("runtime LIVE not restored after advisory session")
    return ComposeResult(
        ok=ok,
        descriptor="T-fa-r1-c",
        notes=notes,
        result=out,
        mesh_accept=_mesh_accept_of(out),
        binding="LiveHttpTransport",
        network_calls=calls["n"],
    )


def run_r1_compose_suite() -> dict[str, Any]:
    """Run R1 compose negatives; always leave runtime LIVE False."""
    set_runtime_live_api_enabled(False)
    assert_module_live_false()
    results = [
        compose_refuse_when_live_off(),
        compose_i5_kill(),
        compose_advisory_not_sot(),
    ]
    # T-fa-r1-d / T-fa-r1-e covered by suite post-conditions
    restore_ok = runtime_live_api_enabled() is False
    module_ok = (
        LIVE_API_ENABLED is False
        and CANARY_LIVE_API_ENABLED is False
        and LHT_LIVE_API_ENABLED is False
    )
    d_ok = ComposeResult(
        ok=restore_ok,
        descriptor="T-fa-r1-d",
        notes=["runtime LIVE False after suite" if restore_ok else "restore failed"],
        result={"runtime_live_api_enabled": runtime_live_api_enabled()},
        mesh_accept=False,
        binding="RefuseTransport",
    )
    e_ok = ComposeResult(
        ok=module_ok,
        descriptor="T-fa-r1-e",
        notes=["module LIVE False on canary+LHT+R1" if module_ok else "module True leak"],
        result={
            "r1": LIVE_API_ENABLED,
            "canary": CANARY_LIVE_API_ENABLED,
            "lht": LHT_LIVE_API_ENABLED,
        },
        mesh_accept=False,
        binding="RefuseTransport",
    )
    results.extend([d_ok, e_ok])
    set_runtime_live_api_enabled(False)
    all_ok = all(r.ok for r in results)
    return {
        "schema": "mesh.judge.full_adapter_r1_compose_suite/v0",
        "ok": all_ok,
        "phase": PHASE,
        "impl_cp": IMPL_CP_ID,
        "design_cp": DESIGN_CP_ID,
        "descriptors": [r.to_dict() for r in results],
        "checklist": r1_checklist_rows(),
        "authorization": impl_cp_authorization_record(),
        "LIVE_API_ENABLED_module_final": LIVE_API_ENABLED,
        "runtime_live_api_enabled_final": runtime_live_api_enabled(),
        "sot_boundaries": list(SOT_BOUNDARIES),
        "r2_r5_authorized": False,
    }
