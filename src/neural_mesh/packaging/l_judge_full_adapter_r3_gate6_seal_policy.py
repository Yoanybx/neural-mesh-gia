"""CP-0084 — Phase R3: Gate6 live-measurement seal policy (measurement/policy).

Seals honest policy: seal_candidate ≠ Gate6 live-measurement seal ≠ product seal.
Optional limited incremental real HAPPY under free-tier; module LIVE stays False.
Does NOT authorize R4/R5, invent F4, permanent LIVE, or claim live-measurement sealed.

Authority: CP-0081 §4 Phase R3 · operator R3 authorize · Gate1 ENABLE_UNDER_FENCES.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping

from neural_mesh.packaging.google_l_judge_peer_spike import DEFAULT_GEMINI_ENV_PATH
from neural_mesh.packaging.l_judge_gemini_free_canary_impl import (
    LIVE_API_ENABLED as CANARY_LIVE_API_ENABLED,
    runtime_live_api_enabled,
)
from neural_mesh.packaging.l_judge_live_http_transport import (
    LIVE_API_ENABLED as LHT_LIVE_API_ENABLED,
)
from neural_mesh.packaging.l_judge_multi_canary_pack import _run_happy

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
    "N_MIN",
    "N_REAL_HTTP_PACK_BASELINE",
    "N_REAL_HTTP_MIN_LIVE_MEASUREMENT_SEAL",
    "SEAL_CANDIDATE",
    "LIVE_MEASUREMENT_SEAL",
    "PRODUCT_SEAL",
    "SealPolicy",
    "IncrementalHappyResult",
    "is_impl_cp_authorized",
    "impl_cp_authorization_record",
    "r3_policy_rows",
    "evaluate_seal_policy",
    "run_incremental_happy_if_allowed",
    "run_r3_policy_suite",
    "assert_module_live_false",
]

PACKAGE_HELD = "0.18.0"
CYCLE = 80
SEAL_CP = "CP-0084"
PRIOR_CP = "CP-0083"
IMPL_CP_ID = "CP-0084"
DESIGN_CP_ID = "CP-0081"
# Product / module default stays False — R3 does not permanently enable.
LIVE_API_ENABLED = False
PHASE = "R3"

N_MIN = 5
# Gate6 pack (CP-0079) honest real HTTP count toward seal_candidate.
N_REAL_HTTP_PACK_BASELINE = 1
# Design bar for Gate6 *live-measurement seal* (not met this CP): need ≥3
# independent real HAPPY under free-tier + kill-armed I5. Not a product SLO.
# R3 does not invent that this bar is met; candidate remains until filled later.
N_REAL_HTTP_MIN_LIVE_MEASUREMENT_SEAL = 3

SEAL_CANDIDATE = True  # pack n=6 (1 real, 5 mock) met N_min
LIVE_MEASUREMENT_SEAL = False  # not sealed this CP
PRODUCT_SEAL = False  # needs F4 signed + live-measurement seal

DESCRIPTOR_IDS: tuple[str, ...] = (
    "T-fa-r3-a",  # seal_candidate vs live-measurement seal split
    "T-fa-r3-b",  # N_real_http bar documented; not falsely claimed met
    "T-fa-r3-c",  # product seal still needs F4 + more real HTTP
    "T-fa-r3-d",  # optional incremental real HAPPY under fences / quota honesty
    "T-fa-r3-e",  # module LIVE False + RefuseTransport final; R4/R5 not authorized
)


def is_impl_cp_authorized() -> bool:
    """R3 measurement/policy is authorized under this CP; R4–R5 are not."""
    return True


def impl_cp_authorization_record() -> dict[str, Any]:
    return {
        "schema": "mesh.judge.full_adapter_r3_gate6_seal_policy_auth/v0",
        "authorized": True,
        "impl_cp": IMPL_CP_ID,
        "design_cp": DESIGN_CP_ID,
        "prior_cp": PRIOR_CP,
        "phase": PHASE,
        "cycle": CYCLE,
        "package_held": PACKAGE_HELD,
        "authorizes": [
            "R3 Gate6 live-measurement seal policy (candidate vs seal bar)",
            "honest n_real_http accounting",
            "limited incremental real HAPPY under ENABLE_UNDER_FENCES + free-tier quota",
        ],
        "does_not_authorize": [
            "R4 streaming DEFER or streaming RV",
            "R5 F4 product ACK / permanent module True",
            "Gate6 live-measurement final seal claim",
            "Gate6 product seal claim",
            "permanent LIVE_API_ENABLED",
            "F4 invent",
            "NO_HELD unlock",
            "push/tags/secrets",
        ],
        "permanent_live_enable": False,
        "live_api_enabled_module_default": False,
        "canary_live_api_enabled_constant": CANARY_LIVE_API_ENABLED,
        "lht_live_api_enabled_constant": LHT_LIVE_API_ENABLED,
        "seal_candidate": SEAL_CANDIDATE,
        "live_measurement_seal": LIVE_MEASUREMENT_SEAL,
        "product_seal": PRODUCT_SEAL,
        "n_min": N_MIN,
        "n_real_http_pack_baseline": N_REAL_HTTP_PACK_BASELINE,
        "n_real_http_min_live_measurement_seal": N_REAL_HTTP_MIN_LIVE_MEASUREMENT_SEAL,
        "enable_ack": "docs/planning/GATE1_ENABLE_UNDER_FENCES_ACK_SIGNED.md",
    }


def r3_policy_rows() -> list[dict[str, str]]:
    return [
        {
            "id": "G6-POL-1",
            "topic": "seal_candidate",
            "rule": "N_min=5 met as pack n=6 (1 real, 5 mock)",
            "prove": "CP-0079 / GATE6_MULTI_CANARY_MEASUREMENT",
            "descriptor": "T-fa-r3-a",
        },
        {
            "id": "G6-POL-2",
            "topic": "live-measurement seal bar",
            "rule": f"Requires n_real_http ≥ {N_REAL_HTTP_MIN_LIVE_MEASUREMENT_SEAL} + variance; candidate alone insufficient",
            "prove": "evaluate_seal_policy",
            "descriptor": "T-fa-r3-b",
        },
        {
            "id": "G6-POL-3",
            "topic": "product seal",
            "rule": "Needs live-measurement seal + signed F4 product ACK + P7; ENABLE ≠ product",
            "prove": "F4_PRODUCT_ENABLE_ACK_DRAFT UNSIGNED",
            "descriptor": "T-fa-r3-c",
        },
        {
            "id": "G6-POL-4",
            "topic": "incremental real HTTP",
            "rule": "R3 may add limited real HAPPY under free-tier; document quota honestly; leave LIVE False",
            "prove": "run_incremental_happy_if_allowed",
            "descriptor": "T-fa-r3-d",
        },
        {
            "id": "G6-POL-5",
            "topic": "fences",
            "rule": "Module LIVE False; R4/R5 not authorized; no F4 invent / NO_HELD / push",
            "prove": "assert_module_live_false + auth record",
            "descriptor": "T-fa-r3-e",
        },
    ]


@dataclass
class SealPolicy:
    seal_candidate: bool
    live_measurement_seal: bool
    product_seal: bool
    n_min: int
    n_real_http_pack_baseline: int
    n_real_http_r3_incremental: int
    n_real_http_gate6_total: int
    n_real_http_min_live_measurement_seal: int
    bar_met: bool
    verdict: str
    reasons: list[str] = field(default_factory=list)
    f4_ack_signed: bool = False
    module_live_final: bool = False

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema": "mesh.judge.full_adapter_r3_gate6_seal_policy/v0",
            "seal_candidate": self.seal_candidate,
            "live_measurement_seal": self.live_measurement_seal,
            "product_seal": self.product_seal,
            "n_min": self.n_min,
            "n_real_http_pack_baseline": self.n_real_http_pack_baseline,
            "n_real_http_r3_incremental": self.n_real_http_r3_incremental,
            "n_real_http_gate6_total": self.n_real_http_gate6_total,
            "n_real_http_min_live_measurement_seal": self.n_real_http_min_live_measurement_seal,
            "bar_met": self.bar_met,
            "verdict": self.verdict,
            "reasons": list(self.reasons),
            "f4_ack_signed": self.f4_ack_signed,
            "module_live_final": self.module_live_final,
            "impl_cp": IMPL_CP_ID,
            "phase": PHASE,
        }


@dataclass
class IncrementalHappyResult:
    attempted: bool
    ok: bool
    real_http: bool
    http_status: int | None = None
    latency_ms: int | None = None
    verdict: str = ""
    error_code: str | None = None
    quota_hit: bool = False
    live_final: bool = False
    binding_final: str = "RefuseTransport"
    notes: list[str] = field(default_factory=list)
    request_id: str = ""
    result_safe: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return {
            "attempted": self.attempted,
            "ok": self.ok,
            "real_http": self.real_http,
            "http_status": self.http_status,
            "latency_ms": self.latency_ms,
            "verdict": self.verdict,
            "error_code": self.error_code,
            "quota_hit": self.quota_hit,
            "live_final": self.live_final,
            "binding_final": self.binding_final,
            "notes": list(self.notes),
            "request_id": self.request_id,
            "result_safe": dict(self.result_safe),
        }


def assert_module_live_false() -> None:
    assert LIVE_API_ENABLED is False
    assert CANARY_LIVE_API_ENABLED is False
    assert LHT_LIVE_API_ENABLED is False
    assert runtime_live_api_enabled() is False


def evaluate_seal_policy(
    *,
    n_real_http_r3_incremental: int = 0,
    f4_ack_signed: bool = False,
) -> SealPolicy:
    """Honest Gate6 seal policy evaluation.

    seal_candidate stays True from pack n=6.
    live-measurement seal only if n_real_http_gate6_total ≥ design bar.
    product seal only if live-measurement seal AND F4 signed.
    """
    total = N_REAL_HTTP_PACK_BASELINE + max(0, int(n_real_http_r3_incremental))
    bar_met = total >= N_REAL_HTTP_MIN_LIVE_MEASUREMENT_SEAL
    reasons: list[str] = []
    if SEAL_CANDIDATE:
        reasons.append("seal_candidate MET: pack n=6 (1 real, 5 mock) ≥ N_min=5")
    if not bar_met:
        reasons.append(
            f"live-measurement seal NOT MET: n_real_http_gate6_total={total} "
            f"< N_real_http_min={N_REAL_HTTP_MIN_LIVE_MEASUREMENT_SEAL}"
        )
        reasons.append(
            "policy: candidate remains until F4/operator fills real-HTTP bar via future CP"
        )
    else:
        reasons.append(
            f"live-measurement bar numerically met (n_real_http={total}); "
            "still requires variance review + separate seal attempt CP"
        )
    if not f4_ack_signed:
        reasons.append("product seal NOT MET: F4 product ACK UNSIGNED")
    # R3 seals *policy*; does not flip LIVE_MEASUREMENT_SEAL constant to True
    # even if bar_met — product/live seal remains explicit operator/future CP.
    live_seal = False
    product = False
    verdict = "POLICY_SEALED_CANDIDATE_REMAINS"
    if bar_met and f4_ack_signed:
        verdict = "BARS_NUMERIC_BUT_R3_DOES_NOT_PRODUCT_SEAL"
    return SealPolicy(
        seal_candidate=SEAL_CANDIDATE,
        live_measurement_seal=live_seal,
        product_seal=product,
        n_min=N_MIN,
        n_real_http_pack_baseline=N_REAL_HTTP_PACK_BASELINE,
        n_real_http_r3_incremental=max(0, int(n_real_http_r3_incremental)),
        n_real_http_gate6_total=total,
        n_real_http_min_live_measurement_seal=N_REAL_HTTP_MIN_LIVE_MEASUREMENT_SEAL,
        bar_met=bar_met,
        verdict=verdict,
        reasons=reasons,
        f4_ack_signed=f4_ack_signed,
        module_live_final=False,
    )


def run_incremental_happy_if_allowed(
    *,
    allow_real_http: bool = False,
    secret_env_path: str | None = None,
) -> IncrementalHappyResult:
    """At most one incremental E-HAPPY real HTTP under fences; mock if not allowed."""
    assert_module_live_false()
    mode = "real_http" if allow_real_http else "mock_local"
    path = secret_env_path or str(DEFAULT_GEMINI_ENV_PATH)
    att = _run_happy(
        index=84,
        mode=mode,
        secret_env_path=path,
        sleep_between_s=0.0,
    )
    quota = bool(
        att.http_status == 429
        or att.error_code in ("ENGINE_RATE_LIMIT",)
        or any("quota" in str(n).lower() or "rate-limit" in str(n).lower() for n in att.notes)
    )
    safe = {
        k: (att.result or {}).get(k)
        for k in (
            "ok",
            "http_status",
            "latency_ms",
            "verdict",
            "error_code",
            "network",
            "provider",
            "model_ref",
            "advisory_only",
            "mesh_accept",
            "digest",
            "transport",
        )
    }
    out = IncrementalHappyResult(
        attempted=True,
        ok=bool(att.ok),
        real_http=(mode == "real_http" and bool(att.network) and att.http_status == 200),
        http_status=att.http_status,
        latency_ms=att.latency_ms,
        verdict=str(att.verdict or ""),
        error_code=att.error_code,
        quota_hit=quota,
        live_final=bool(att.live_final),
        binding_final=str(att.binding_final or "RefuseTransport"),
        notes=list(att.notes),
        request_id=str(att.request_id or ""),
        result_safe=safe,
    )
    assert_module_live_false()
    return out


def run_r3_policy_suite(
    *,
    allow_real_http: bool = False,
    run_incremental: bool = True,
) -> dict[str, Any]:
    """Policy suite: evaluate seal bar; optional one incremental HAPPY; LIVE False."""
    assert_module_live_false()
    incr: IncrementalHappyResult | None = None
    n_incr = 0
    if run_incremental:
        incr = run_incremental_happy_if_allowed(allow_real_http=allow_real_http)
        if incr.real_http and incr.ok:
            n_incr = 1
        elif incr.quota_hit:
            n_incr = 0
    policy = evaluate_seal_policy(n_real_http_r3_incremental=n_incr, f4_ack_signed=False)
    descriptors = {
        "T-fa-r3-a": {
            "ok": policy.seal_candidate is True and policy.live_measurement_seal is False,
            "note": "candidate True; live-measurement seal False",
        },
        "T-fa-r3-b": {
            "ok": (
                policy.n_real_http_min_live_measurement_seal
                == N_REAL_HTTP_MIN_LIVE_MEASUREMENT_SEAL
                and policy.bar_met is False
            ),
            "note": f"bar={N_REAL_HTTP_MIN_LIVE_MEASUREMENT_SEAL}; total={policy.n_real_http_gate6_total}; bar_met=False",
        },
        "T-fa-r3-c": {
            "ok": policy.product_seal is False and policy.f4_ack_signed is False,
            "note": "product seal blocked on unsigned F4",
        },
        "T-fa-r3-d": {
            "ok": incr is not None and incr.attempted and incr.live_final is False,
            "note": (
                f"incremental real_http={incr.real_http if incr else False} "
                f"quota={incr.quota_hit if incr else False}"
            ),
        },
        "T-fa-r3-e": {
            "ok": (
                LIVE_API_ENABLED is False
                and runtime_live_api_enabled() is False
                and policy.module_live_final is False
            ),
            "note": "module + runtime LIVE False; R4/R5 not authorized",
        },
    }
    ok = all(d["ok"] for d in descriptors.values())
    assert_module_live_false()
    return {
        "schema": "mesh.judge.full_adapter_r3_gate6_seal_policy_suite/v0",
        "ok": ok,
        "phase": PHASE,
        "impl_cp": IMPL_CP_ID,
        "descriptors": descriptors,
        "checklist": r3_policy_rows(),
        "authorization": impl_cp_authorization_record(),
        "policy": policy.as_dict(),
        "incremental": None if incr is None else incr.as_dict(),
        "LIVE_API_ENABLED_module_final": False,
        "runtime_live_final": runtime_live_api_enabled(),
        "n_real_http_gate6_total": policy.n_real_http_gate6_total,
        "n_real_http_r3_incremental": policy.n_real_http_r3_incremental,
        "verdict": policy.verdict,
        "live_measurement_seal": False,
        "product_seal": False,
        "r4_r5_authorized": False,
        "binding_final": "RefuseTransport",
        "measured_at_unix": int(time.time()),
    }


def main(argv: list[str] | None = None) -> int:
    import argparse

    p = argparse.ArgumentParser(description="CP-0084 R3 Gate6 seal policy suite")
    p.add_argument("--real-http", action="store_true", help="allow one incremental real HAPPY")
    p.add_argument("--out", type=Path, default=None, help="write suite JSON")
    args = p.parse_args(argv)
    suite = run_r3_policy_suite(allow_real_http=args.real_http, run_incremental=True)
    text = json.dumps(suite, indent=2, sort_keys=True)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text + "\n", encoding="utf-8")
    print(text)
    return 0 if suite["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
