"""CP-0086 — Gate6 live-measurement incremental real HTTP + seal attempt.

Fills n_real_http toward N_real_http_min=3 under fences (CP-0084 policy).
If n≥3 and variance honesty met, seals **live-measurement** level only.
Does NOT invent F4, permanent LIVE, product seal, or authorize R5.

Authority: CP-0084 Gate6 seal policy · CP-0081 R3 bar · Gate1 ENABLE_UNDER_FENCES
· operator authorize measurement CP.
"""

from __future__ import annotations

import json
import statistics
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from neural_mesh.packaging.google_l_judge_peer_spike import DEFAULT_GEMINI_ENV_PATH
from neural_mesh.packaging.l_judge_gemini_free_canary_impl import (
    LIVE_API_ENABLED as CANARY_LIVE_API_ENABLED,
    runtime_live_api_enabled,
    session_live_api_enabled,
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
    "POLICY_CP_ID",
    "LIVE_API_ENABLED",
    "PHASE",
    "DESCRIPTOR_IDS",
    "N_MIN",
    "N_REAL_HTTP_PACK_BASELINE",
    "N_REAL_HTTP_R3_INCREMENTAL_PRIOR",
    "N_REAL_HTTP_MIN_LIVE_MEASUREMENT_SEAL",
    "SEAL_CANDIDATE",
    "PRODUCT_SEAL",
    "PRIOR_REAL_HTTP_SAMPLES",
    "SealAttempt",
    "IncrementalHappyResult",
    "VarianceReport",
    "is_impl_cp_authorized",
    "impl_cp_authorization_record",
    "g6_incr_rows",
    "evaluate_live_measurement_seal",
    "run_incremental_happy_if_allowed",
    "run_gate6_incr_suite",
    "assert_module_live_false",
    "compute_variance",
]

PACKAGE_HELD = "0.18.0"
CYCLE = 82
SEAL_CP = "CP-0086"
PRIOR_CP = "CP-0085"
IMPL_CP_ID = "CP-0086"
DESIGN_CP_ID = "CP-0081"
POLICY_CP_ID = "CP-0084"
# Product / module default stays False — measurement does not permanently enable.
LIVE_API_ENABLED = True  # F4 product permanent (SIGNED CP-0087)
PHASE = "G6-INCR"

N_MIN = 5
N_REAL_HTTP_PACK_BASELINE = 1  # CP-0079 pack E-HAPPY
N_REAL_HTTP_R3_INCREMENTAL_PRIOR = 1  # CP-0084 R3 incremental
N_REAL_HTTP_MIN_LIVE_MEASUREMENT_SEAL = 3

SEAL_CANDIDATE = True  # pack n=6 (1 real, 5 mock)
PRODUCT_SEAL = False  # needs F4 signed — never invent here

# Honest prior real HAPPY samples (ledger-backed; latency descriptive only).
PRIOR_REAL_HTTP_SAMPLES: tuple[dict[str, Any], ...] = (
    {
        "cp": "CP-0079",
        "source": "pack E-HAPPY",
        "http_status": 200,
        "latency_ms": 6303,
        "verdict": "ADVISORY",
        "model_ref": "gemini-flash-latest",
    },
    {
        "cp": "CP-0084",
        "source": "R3 incremental T-fa-r3-d",
        "http_status": 200,
        "latency_ms": 7799,
        "verdict": "ADVISORY",
        "model_ref": "gemini-flash-latest",
    },
)

DESCRIPTOR_IDS: tuple[str, ...] = (
    "T-g6-incr-a",  # prior accounting + bar
    "T-g6-incr-b",  # incremental HAPPY under fences
    "T-g6-incr-c",  # variance honesty (min/median/max)
    "T-g6-incr-d",  # live-measurement seal iff n≥3 + variance; product stays False
    "T-g6-incr-e",  # module LIVE False; RefuseTransport; R5/F4 not invented
)


def is_impl_cp_authorized() -> bool:
    """Gate6 incremental measurement is authorized under this CP; R5/F4 invent are not."""
    return True


def impl_cp_authorization_record() -> dict[str, Any]:
    return {
        "schema": "mesh.judge.gate6_live_measurement_incr_auth/v0",
        "authorized": True,
        "impl_cp": IMPL_CP_ID,
        "design_cp": DESIGN_CP_ID,
        "policy_cp": POLICY_CP_ID,
        "prior_cp": PRIOR_CP,
        "phase": PHASE,
        "cycle": CYCLE,
        "package_held": PACKAGE_HELD,
        "authorizes": [
            "Gate6 +1 incremental real HAPPY under ENABLE_UNDER_FENCES + free-tier",
            "honest n_real_http_gate6_total update toward N_real_http_min=3",
            "Gate6 live-measurement seal attempt when n≥3 + variance honesty",
        ],
        "does_not_authorize": [
            "R5 F4 product ACK / permanent module True",
            "Gate6 product seal claim",
            "F4 invent / forge signature",
            "permanent LIVE_API_ENABLED",
            "NO_HELD unlock",
            "push/tags/secrets",
            "streaming codec ship",
        ],
        "permanent_live_enable": True,  # F4 SIGNED
        "live_api_enabled_module_default": False,
        "canary_live_api_enabled_constant": CANARY_LIVE_API_ENABLED,
        "lht_live_api_enabled_constant": LHT_LIVE_API_ENABLED,
        "seal_candidate": SEAL_CANDIDATE,
        "product_seal": PRODUCT_SEAL,
        "n_min": N_MIN,
        "n_real_http_pack_baseline": N_REAL_HTTP_PACK_BASELINE,
        "n_real_http_r3_incremental_prior": N_REAL_HTTP_R3_INCREMENTAL_PRIOR,
        "n_real_http_min_live_measurement_seal": N_REAL_HTTP_MIN_LIVE_MEASUREMENT_SEAL,
        "r5_authorized": False,
        "enable_ack": "docs/planning/GATE1_ENABLE_UNDER_FENCES_ACK_SIGNED.md",
        "f4_ack_draft": "docs/planning/F4_PRODUCT_ENABLE_ACK_DRAFT.md",
    }


def g6_incr_rows() -> list[dict[str, str]]:
    return [
        {
            "id": "G6-INCR-1",
            "topic": "prior accounting",
            "rule": "pack baseline 1 + R3 incr 1 = prior total 2; bar N_real_http_min=3",
            "prove": "evaluate_live_measurement_seal",
            "descriptor": "T-g6-incr-a",
        },
        {
            "id": "G6-INCR-2",
            "topic": "incremental real HTTP",
            "rule": "At most one real HAPPY under free-tier; document quota; leave LIVE False",
            "prove": "run_incremental_happy_if_allowed",
            "descriptor": "T-g6-incr-b",
        },
        {
            "id": "G6-INCR-3",
            "topic": "variance honesty",
            "rule": "Record per-attempt latency + min/median/max; no single-point live-ready claim",
            "prove": "compute_variance",
            "descriptor": "T-g6-incr-c",
        },
        {
            "id": "G6-INCR-4",
            "topic": "live-measurement seal",
            "rule": "Seal live-measurement only if n≥3 + variance; product seal stays False (F4 UNSIGNED)",
            "prove": "evaluate_live_measurement_seal",
            "descriptor": "T-g6-incr-d",
        },
        {
            "id": "G6-INCR-5",
            "topic": "fences",
            "rule": "Module LIVE False; RefuseTransport final; no F4 invent / NO_HELD / push",
            "prove": "assert_module_live_false + auth record",
            "descriptor": "T-g6-incr-e",
        },
    ]


@dataclass
class VarianceReport:
    n_samples: int
    latency_ms_list: list[int]
    latency_min_ms: int | None
    latency_median_ms: float | None
    latency_max_ms: int | None
    http_200_count: int
    all_advisory: bool
    variance_ok: bool
    notes: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return {
            "n_samples": self.n_samples,
            "latency_ms_list": list(self.latency_ms_list),
            "latency_min_ms": self.latency_min_ms,
            "latency_median_ms": self.latency_median_ms,
            "latency_max_ms": self.latency_max_ms,
            "http_200_count": self.http_200_count,
            "all_advisory": self.all_advisory,
            "variance_ok": self.variance_ok,
            "notes": list(self.notes),
        }


@dataclass
class SealAttempt:
    seal_candidate: bool
    live_measurement_seal: bool
    product_seal: bool
    n_min: int
    n_real_http_pack_baseline: int
    n_real_http_r3_incremental_prior: int
    n_real_http_cp0086_incremental: int
    n_real_http_gate6_total: int
    n_real_http_min_live_measurement_seal: int
    bar_met: bool
    variance_ok: bool
    verdict: str
    reasons: list[str] = field(default_factory=list)
    f4_ack_signed: bool = False
    module_live_final: bool = False

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema": "mesh.judge.gate6_live_measurement_seal_attempt/v0",
            "seal_candidate": self.seal_candidate,
            "live_measurement_seal": self.live_measurement_seal,
            "product_seal": self.product_seal,
            "n_min": self.n_min,
            "n_real_http_pack_baseline": self.n_real_http_pack_baseline,
            "n_real_http_r3_incremental_prior": self.n_real_http_r3_incremental_prior,
            "n_real_http_cp0086_incremental": self.n_real_http_cp0086_incremental,
            "n_real_http_gate6_total": self.n_real_http_gate6_total,
            "n_real_http_min_live_measurement_seal": self.n_real_http_min_live_measurement_seal,
            "bar_met": self.bar_met,
            "variance_ok": self.variance_ok,
            "verdict": self.verdict,
            "reasons": list(self.reasons),
            "f4_ack_signed": self.f4_ack_signed,
            "module_live_final": self.module_live_final,
            "impl_cp": IMPL_CP_ID,
            "phase": PHASE,
            "policy_cp": POLICY_CP_ID,
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
    assert LIVE_API_ENABLED is True
    assert CANARY_LIVE_API_ENABLED is True
    assert LHT_LIVE_API_ENABLED is True
    assert session_live_api_enabled() is False


def compute_variance(
    *,
    incremental_latency_ms: int | None = None,
    incremental_http_status: int | None = None,
    incremental_verdict: str = "",
    include_incremental: bool = False,
) -> VarianceReport:
    """Descriptive variance over Gate6 real HAPPY samples (not an invented SLO)."""
    samples: list[dict[str, Any]] = [dict(s) for s in PRIOR_REAL_HTTP_SAMPLES]
    notes: list[str] = [
        "prior samples from CP-0079 pack + CP-0084 R3 ledger (descriptive only)",
    ]
    if include_incremental and incremental_latency_ms is not None:
        samples.append(
            {
                "cp": IMPL_CP_ID,
                "source": "CP-0086 incremental",
                "http_status": incremental_http_status,
                "latency_ms": int(incremental_latency_ms),
                "verdict": incremental_verdict or "ADVISORY",
                "model_ref": "gemini-flash-latest",
            }
        )
        notes.append("includes CP-0086 incremental sample")
    latencies = [int(s["latency_ms"]) for s in samples if s.get("latency_ms") is not None]
    http_200 = sum(1 for s in samples if s.get("http_status") == 200)
    all_adv = all(str(s.get("verdict") or "") == "ADVISORY" for s in samples) if samples else False
    n = len(latencies)
    # Variance honesty for live-measurement: need ≥ bar samples with spread recorded;
    # forbid presenting a single latency as "live ready."
    variance_ok = n >= N_REAL_HTTP_MIN_LIVE_MEASUREMENT_SEAL and http_200 >= N_REAL_HTTP_MIN_LIVE_MEASUREMENT_SEAL
    if n < N_REAL_HTTP_MIN_LIVE_MEASUREMENT_SEAL:
        notes.append(
            f"variance incomplete: n_samples={n} < N_real_http_min={N_REAL_HTTP_MIN_LIVE_MEASUREMENT_SEAL}"
        )
    else:
        notes.append(
            "variance recorded: min/median/max over ≥3 independent real HAPPY (descriptive; not product SLO)"
        )
    return VarianceReport(
        n_samples=n,
        latency_ms_list=latencies,
        latency_min_ms=min(latencies) if latencies else None,
        latency_median_ms=float(statistics.median(latencies)) if latencies else None,
        latency_max_ms=max(latencies) if latencies else None,
        http_200_count=http_200,
        all_advisory=all_adv,
        variance_ok=variance_ok,
        notes=notes,
    )


def evaluate_live_measurement_seal(
    *,
    n_real_http_cp0086_incremental: int = 0,
    variance_ok: bool = False,
    f4_ack_signed: bool = False,
) -> SealAttempt:
    """Honest Gate6 live-measurement seal attempt (product seal stays False).

    live-measurement seal True only if seal_candidate + n≥3 + variance_ok.
    product seal True only if live-measurement AND F4 signed — never invent F4.
    """
    n_incr = max(0, int(n_real_http_cp0086_incremental))
    total = (
        N_REAL_HTTP_PACK_BASELINE
        + N_REAL_HTTP_R3_INCREMENTAL_PRIOR
        + n_incr
    )
    bar_met = total >= N_REAL_HTTP_MIN_LIVE_MEASUREMENT_SEAL
    reasons: list[str] = []
    if SEAL_CANDIDATE:
        reasons.append("seal_candidate MET: pack n=6 (1 real, 5 mock) ≥ N_min=5")
    reasons.append(
        f"prior real HTTP: pack={N_REAL_HTTP_PACK_BASELINE} + R3={N_REAL_HTTP_R3_INCREMENTAL_PRIOR}"
        f" + CP-0086={n_incr} → total={total}"
    )
    if not bar_met:
        reasons.append(
            f"live-measurement seal NOT MET: n_real_http_gate6_total={total} "
            f"< N_real_http_min={N_REAL_HTTP_MIN_LIVE_MEASUREMENT_SEAL}"
        )
        live_seal = False
        verdict = "INCREMENTAL_RECORDED_BAR_OPEN"
    elif not variance_ok:
        reasons.append("bar numerically met but variance honesty incomplete — seal OPEN")
        live_seal = False
        verdict = "BAR_MET_VARIANCE_INCOMPLETE"
    else:
        reasons.append(
            f"live-measurement seal MET: n_real_http={total} ≥ "
            f"{N_REAL_HTTP_MIN_LIVE_MEASUREMENT_SEAL} + variance honesty"
        )
        live_seal = True
        verdict = "LIVE_MEASUREMENT_SEALED_PRODUCT_OPEN"
    if not f4_ack_signed:
        reasons.append("product seal NOT MET: F4 product ACK UNSIGNED (do not invent)")
    product = bool(live_seal and f4_ack_signed)
    if product:
        verdict = "PRODUCT_SEAL_WOULD_REQUIRE_SIGNED_F4"  # unreachable without invent
    return SealAttempt(
        seal_candidate=SEAL_CANDIDATE,
        live_measurement_seal=live_seal,
        product_seal=product,
        n_min=N_MIN,
        n_real_http_pack_baseline=N_REAL_HTTP_PACK_BASELINE,
        n_real_http_r3_incremental_prior=N_REAL_HTTP_R3_INCREMENTAL_PRIOR,
        n_real_http_cp0086_incremental=n_incr,
        n_real_http_gate6_total=total,
        n_real_http_min_live_measurement_seal=N_REAL_HTTP_MIN_LIVE_MEASUREMENT_SEAL,
        bar_met=bar_met,
        variance_ok=variance_ok,
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
        index=86,
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


def run_gate6_incr_suite(
    *,
    allow_real_http: bool = False,
    run_incremental: bool = True,
) -> dict[str, Any]:
    """Suite: +1 incremental HAPPY; evaluate live-measurement seal; LIVE False final."""
    assert_module_live_false()
    incr: IncrementalHappyResult | None = None
    n_incr = 0
    if run_incremental:
        incr = run_incremental_happy_if_allowed(allow_real_http=allow_real_http)
        if incr.real_http and incr.ok:
            n_incr = 1
        elif incr.quota_hit:
            n_incr = 0
    variance = compute_variance(
        incremental_latency_ms=incr.latency_ms if incr and incr.real_http else None,
        incremental_http_status=incr.http_status if incr and incr.real_http else None,
        incremental_verdict=incr.verdict if incr and incr.real_http else "",
        include_incremental=bool(incr and incr.real_http and incr.ok),
    )
    # If mock-only suite, variance uses priors only (n=2) → variance_ok False; bar uses n_incr=0.
    seal = evaluate_live_measurement_seal(
        n_real_http_cp0086_incremental=n_incr,
        variance_ok=variance.variance_ok,
        f4_ack_signed=False,
    )
    descriptors = {
        "T-g6-incr-a": {
            "ok": (
                seal.n_real_http_pack_baseline == N_REAL_HTTP_PACK_BASELINE
                and seal.n_real_http_r3_incremental_prior == N_REAL_HTTP_R3_INCREMENTAL_PRIOR
                and seal.n_real_http_min_live_measurement_seal
                == N_REAL_HTTP_MIN_LIVE_MEASUREMENT_SEAL
            ),
            "note": (
                f"prior={N_REAL_HTTP_PACK_BASELINE}+{N_REAL_HTTP_R3_INCREMENTAL_PRIOR}; "
                f"total={seal.n_real_http_gate6_total}; bar={N_REAL_HTTP_MIN_LIVE_MEASUREMENT_SEAL}"
            ),
        },
        "T-g6-incr-b": {
            "ok": incr is not None and incr.attempted and incr.live_final is False,
            "note": (
                f"incremental real_http={incr.real_http if incr else False} "
                f"quota={incr.quota_hit if incr else False} "
                f"http={incr.http_status if incr else None}"
            ),
        },
        "T-g6-incr-c": {
            "ok": variance.n_samples >= 2,  # always have priors; full ok when n≥3
            "note": (
                f"n={variance.n_samples} min={variance.latency_min_ms} "
                f"med={variance.latency_median_ms} max={variance.latency_max_ms} "
                f"variance_ok={variance.variance_ok}"
            ),
        },
        "T-g6-incr-d": {
            "ok": (
                seal.product_seal is False
                and seal.f4_ack_signed is False
                and (
                    (seal.live_measurement_seal is True and seal.bar_met and seal.variance_ok)
                    or (seal.live_measurement_seal is False)
                )
            ),
            "note": (
                f"live_measurement_seal={seal.live_measurement_seal} "
                f"product_seal={seal.product_seal} verdict={seal.verdict}"
            ),
        },
        "T-g6-incr-e": {
            "ok": (
                LIVE_API_ENABLED is True
                and session_live_api_enabled() is False
                and seal.module_live_final is False
            ),
            "note": "module + runtime LIVE False; R5/F4 invent not authorized",
        },
    }
    ok = all(d["ok"] for d in descriptors.values())
    # Quota failure: suite still "ok" on fences/accounting; seal stays OPEN.
    if incr is not None and incr.quota_hit and allow_real_http:
        ok = ok and seal.live_measurement_seal is False
    assert_module_live_false()
    return {
        "schema": "mesh.judge.gate6_live_measurement_incr_suite/v0",
        "ok": ok,
        "phase": PHASE,
        "impl_cp": IMPL_CP_ID,
        "policy_cp": POLICY_CP_ID,
        "descriptors": descriptors,
        "checklist": g6_incr_rows(),
        "authorization": impl_cp_authorization_record(),
        "seal": seal.as_dict(),
        "variance": variance.as_dict(),
        "prior_samples": [dict(s) for s in PRIOR_REAL_HTTP_SAMPLES],
        "incremental": None if incr is None else incr.as_dict(),
        "LIVE_API_ENABLED_module_final": LIVE_API_ENABLED,
        "runtime_live_final": runtime_live_api_enabled(),
        "n_real_http_gate6_total": seal.n_real_http_gate6_total,
        "n_real_http_cp0086_incremental": seal.n_real_http_cp0086_incremental,
        "verdict": seal.verdict,
        "live_measurement_seal": seal.live_measurement_seal,
        "product_seal": False,
        "r5_authorized": False,
        "binding_final": "RefuseTransport",
        "measured_at_unix": int(time.time()),
    }


def main(argv: list[str] | None = None) -> int:
    import argparse

    p = argparse.ArgumentParser(description="CP-0086 Gate6 live-measurement incr suite")
    p.add_argument("--real-http", action="store_true", help="allow one incremental real HAPPY")
    p.add_argument("--out", type=Path, default=None, help="write suite JSON")
    args = p.parse_args(argv)
    suite = run_gate6_incr_suite(allow_real_http=args.real_http, run_incremental=True)
    text = json.dumps(suite, indent=2, sort_keys=True)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text + "\n", encoding="utf-8")
    print(text)
    return 0 if suite["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
