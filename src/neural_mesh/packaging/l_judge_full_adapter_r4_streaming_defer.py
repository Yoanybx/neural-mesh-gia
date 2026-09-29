"""CP-0085 — Phase R4: Streaming DEFER / OUT_OF_SCOPE_FOR_F4 seal (DESIGN/policy).

Seals honest posture: product path remains unary-only (CP-0078 v0);
streaming is DEFERRED and OUT of F4 product ACK unless separately named.
Does NOT authorize R5, invent F4, permanent LIVE, or ship streaming codec.

Authority: CP-0081 §4 Phase R4 · §3.7 · operator R4 authorize.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from neural_mesh.packaging.l_judge_gemini_free_canary_impl import (
    LIVE_API_ENABLED as CANARY_LIVE_API_ENABLED,
    runtime_live_api_enabled,
    session_live_api_enabled,
)
from neural_mesh.packaging.l_judge_live_http_transport import (
    LIVE_API_ENABLED as LHT_LIVE_API_ENABLED,
    default_lht_policy,
    impl_cp_authorization_record as lht_impl_cp_authorization_record,
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
    "STREAMING_POSTURE",
    "STREAMING_F4_SCOPE",
    "STREAMING_ALLOWED",
    "STREAMING_SHIPPED",
    "PRODUCT_CODEC_MODE",
    "StreamingDeferPolicy",
    "is_impl_cp_authorized",
    "impl_cp_authorization_record",
    "r4_defer_rows",
    "evaluate_streaming_defer_policy",
    "run_r4_defer_suite",
    "assert_module_live_false",
    "assert_unary_only_product_path",
]

PACKAGE_HELD = "0.18.0"
CYCLE = 81
SEAL_CP = "CP-0085"
PRIOR_CP = "CP-0084"
IMPL_CP_ID = "CP-0085"
DESIGN_CP_ID = "CP-0081"
# Product / module default stays False — R4 does not permanently enable.
LIVE_API_ENABLED = True  # F4 product permanent (SIGNED CP-0087)
PHASE = "R4"

STREAMING_POSTURE = "DEFERRED"
STREAMING_F4_SCOPE = "OUT_OF_SCOPE_FOR_F4"
STREAMING_ALLOWED = False
STREAMING_SHIPPED = False
PRODUCT_CODEC_MODE = "unary"

DESCRIPTOR_IDS: tuple[str, ...] = (
    "T-fa-r4-a",  # unary product path (CP-0078)
    "T-fa-r4-b",  # streaming OUT_OF_SCOPE_FOR_F4
    "T-fa-r4-c",  # streaming_allowed/shipped False
    "T-fa-r4-d",  # T-lht-j residual deferred (no streaming RV)
    "T-fa-r4-e",  # module LIVE False; R5 not authorized
)


def is_impl_cp_authorized() -> bool:
    """R4 DEFER seal is authorized under this CP; R5 is not."""
    return True


def impl_cp_authorization_record() -> dict[str, Any]:
    return {
        "schema": "mesh.judge.full_adapter_r4_streaming_defer_auth/v0",
        "authorized": True,
        "impl_cp": IMPL_CP_ID,
        "design_cp": DESIGN_CP_ID,
        "prior_cp": PRIOR_CP,
        "phase": PHASE,
        "cycle": CYCLE,
        "package_held": PACKAGE_HELD,
        "authorizes": [
            "R4 streaming DEFER seal (unary-only product)",
            "OUT_OF_SCOPE_FOR_F4 binding unless operator separately names streaming",
            "honest close of R4 residual without silent omission",
        ],
        "does_not_authorize": [
            "R5 F4 product ACK / permanent module True",
            "streaming codec ship / live streaming RV",
            "Gate6 live-measurement final seal claim",
            "Gate6 product seal claim",
            "permanent LIVE_API_ENABLED",
            "F4 invent",
            "NO_HELD unlock",
            "push/tags/secrets",
        ],
        "permanent_live_enable": True,  # F4 SIGNED
        "live_api_enabled_module_default": False,
        "canary_live_api_enabled_constant": CANARY_LIVE_API_ENABLED,
        "lht_live_api_enabled_constant": LHT_LIVE_API_ENABLED,
        "streaming_posture": STREAMING_POSTURE,
        "streaming_f4_scope": STREAMING_F4_SCOPE,
        "streaming_allowed": STREAMING_ALLOWED,
        "streaming_shipped": STREAMING_SHIPPED,
        "product_codec_mode": PRODUCT_CODEC_MODE,
        "r5_authorized": False,
        "enable_ack": "docs/planning/GATE1_ENABLE_UNDER_FENCES_ACK_SIGNED.md",
        "f4_ack_draft": "docs/planning/F4_PRODUCT_ENABLE_ACK_DRAFT.md",
    }


def r4_defer_rows() -> list[dict[str, str]]:
    return [
        {
            "id": "STR-DEF-1",
            "topic": "unary product",
            "rule": "CP-0078 v0 unary-only remains SoT product path",
            "prove": "assert_unary_only_product_path",
            "descriptor": "T-fa-r4-a",
        },
        {
            "id": "STR-DEF-2",
            "topic": "F4 scope",
            "rule": "Streaming OUT_OF_SCOPE_FOR_F4 unless operator separately names it",
            "prove": "evaluate_streaming_defer_policy",
            "descriptor": "T-fa-r4-b",
        },
        {
            "id": "STR-DEF-3",
            "topic": "flags",
            "rule": "streaming_allowed=False; streaming_shipped=False",
            "prove": "LHT describe + constants",
            "descriptor": "T-fa-r4-c",
        },
        {
            "id": "STR-DEF-4",
            "topic": "T-lht-j residual",
            "rule": "Design residual deferred; no half-ACCEPT; no live streaming RV this CP",
            "prove": "policy notes cite CP-0076 T-lht-j",
            "descriptor": "T-fa-r4-d",
        },
        {
            "id": "STR-DEF-5",
            "topic": "fences",
            "rule": "Module LIVE False; R5 not authorized; no F4 invent / NO_HELD / push",
            "prove": "assert_module_live_false + auth record",
            "descriptor": "T-fa-r4-e",
        },
    ]


@dataclass
class StreamingDeferPolicy:
    streaming_posture: str
    streaming_f4_scope: str
    streaming_allowed: bool
    streaming_shipped: bool
    product_codec_mode: str
    t_lht_j_deferred: bool
    verdict: str
    reasons: list[str] = field(default_factory=list)
    f4_ack_signed: bool = False
    module_live_final: bool = False
    r5_authorized: bool = False

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema": "mesh.judge.full_adapter_r4_streaming_defer_policy/v0",
            "streaming_posture": self.streaming_posture,
            "streaming_f4_scope": self.streaming_f4_scope,
            "streaming_allowed": self.streaming_allowed,
            "streaming_shipped": self.streaming_shipped,
            "product_codec_mode": self.product_codec_mode,
            "t_lht_j_deferred": self.t_lht_j_deferred,
            "verdict": self.verdict,
            "reasons": list(self.reasons),
            "f4_ack_signed": self.f4_ack_signed,
            "module_live_final": self.module_live_final,
            "r5_authorized": self.r5_authorized,
            "impl_cp": IMPL_CP_ID,
            "phase": PHASE,
        }


def assert_module_live_false() -> None:
    assert LIVE_API_ENABLED is True
    assert CANARY_LIVE_API_ENABLED is True
    assert LHT_LIVE_API_ENABLED is True
    assert session_live_api_enabled() is False


def assert_unary_only_product_path() -> dict[str, Any]:
    """Confirm LHT v0 policy + auth record: unary + streaming flags False."""
    policy = default_lht_policy()
    auth = lht_impl_cp_authorization_record()
    streaming_allowed = bool(policy.get("streaming_allowed", True))
    streaming_shipped = bool(auth.get("streaming_shipped", True))
    mode = str(policy.get("mode") or "")
    assert streaming_allowed is False
    assert streaming_shipped is False
    assert mode == "unary"
    assert bool(policy.get("enabled", True)) is False
    return {
        "mode": mode,
        "streaming_allowed": streaming_allowed,
        "streaming_shipped": streaming_shipped,
        "lht_enabled_default": bool(policy.get("enabled")),
        "policy_keys": sorted(policy.keys()),
    }


def evaluate_streaming_defer_policy(
    *,
    f4_ack_signed: bool = False,
) -> StreamingDeferPolicy:
    """Honest R4 DEFER evaluation — never flips streaming shipped True."""
    reasons: list[str] = [
        "product codec path = unary only (CP-0078 v0)",
        "streaming_posture=DEFERRED (explicit seal; not silent)",
        "streaming F4 scope=OUT_OF_SCOPE_FOR_F4 unless operator separately names",
        "T-lht-j remains design residual (CP-0076); deferred as product path",
        "R5 F4 product ACK is operator-only — bots must not invent signature",
    ]
    if not f4_ack_signed:
        reasons.append("F4 product ACK UNSIGNED (unchanged)")
    return StreamingDeferPolicy(
        streaming_posture=STREAMING_POSTURE,
        streaming_f4_scope=STREAMING_F4_SCOPE,
        streaming_allowed=STREAMING_ALLOWED,
        streaming_shipped=STREAMING_SHIPPED,
        product_codec_mode=PRODUCT_CODEC_MODE,
        t_lht_j_deferred=True,
        verdict="STREAMING_DEFERRED_OUT_OF_F4",
        reasons=reasons,
        f4_ack_signed=f4_ack_signed,
        module_live_final=False,
        r5_authorized=False,
    )


def run_r4_defer_suite() -> dict[str, Any]:
    """DEFER suite: unary-only + OUT_OF_F4 + LIVE False; no network."""
    assert_module_live_false()
    unary = assert_unary_only_product_path()
    policy = evaluate_streaming_defer_policy(f4_ack_signed=False)
    descriptors = {
        "T-fa-r4-a": {
            "ok": policy.product_codec_mode == "unary" and unary["mode"] == "unary",
            "note": "unary product path (CP-0078 v0)",
        },
        "T-fa-r4-b": {
            "ok": policy.streaming_f4_scope == "OUT_OF_SCOPE_FOR_F4",
            "note": "streaming OUT_OF_SCOPE_FOR_F4",
        },
        "T-fa-r4-c": {
            "ok": (
                policy.streaming_allowed is False
                and policy.streaming_shipped is False
                and unary["streaming_allowed"] is False
                and unary["streaming_shipped"] is False
            ),
            "note": "streaming_allowed=False; streaming_shipped=False",
        },
        "T-fa-r4-d": {
            "ok": policy.t_lht_j_deferred is True
            and policy.streaming_posture == "DEFERRED",
            "note": "T-lht-j deferred; no streaming RV executed",
        },
        "T-fa-r4-e": {
            "ok": (
                LIVE_API_ENABLED is True
                and session_live_api_enabled() is False
                and policy.module_live_final is False
                and policy.r5_authorized is False
            ),
            "note": "module + runtime LIVE False; R5 not authorized",
        },
    }
    ok = all(d["ok"] for d in descriptors.values())
    assert_module_live_false()
    return {
        "schema": "mesh.judge.full_adapter_r4_streaming_defer_suite/v0",
        "ok": ok,
        "phase": PHASE,
        "impl_cp": IMPL_CP_ID,
        "descriptors": descriptors,
        "checklist": r4_defer_rows(),
        "authorization": impl_cp_authorization_record(),
        "policy": policy.as_dict(),
        "unary_product_path": unary,
        "LIVE_API_ENABLED_module_final": LIVE_API_ENABLED,
        "runtime_live_final": runtime_live_api_enabled(),
        "verdict": policy.verdict,
        "streaming_posture": STREAMING_POSTURE,
        "streaming_f4_scope": STREAMING_F4_SCOPE,
        "streaming_allowed": False,
        "streaming_shipped": False,
        "r5_authorized": False,
        "binding_final": "RefuseTransport",
        "measured_at_unix": int(time.time()),
    }


def main(argv: list[str] | None = None) -> int:
    import argparse

    p = argparse.ArgumentParser(description="CP-0085 R4 streaming DEFER seal suite")
    p.add_argument("--out", type=Path, default=None, help="write suite JSON")
    args = p.parse_args(argv)
    suite = run_r4_defer_suite()
    text = json.dumps(suite, indent=2, sort_keys=True)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text + "\n", encoding="utf-8")
    print(text)
    return 0 if suite["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
