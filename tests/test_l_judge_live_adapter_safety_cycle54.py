"""Tests for Cycle 54 / CP-0058: L_judge live-adapter safety case (design-only).

Markers: l_judge_live_adapter_safety_cycle54
Negative refusal paths; no live API keys; no network; no src live codec.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

import pytest

from neural_mesh import __version__
from neural_mesh.packaging.l_judge_live_adapter_safety import (
    ABORT_CODES,
    CYCLE,
    MUST_STAY_FALSE,
    PACKAGE_HELD,
    PERMANENT_FALSE,
    PREFERRED_NEXT_DEFAULT,
    PRIOR_CP,
    RATE_LIMIT_FLOORS,
    SCHEMA_SAFETY,
    SEAL_CP,
    RefuseTransport,
    default_safety_gate,
    evaluate_enablement_gates,
    is_valid_secret_handle,
    looks_like_raw_secret,
)

pytestmark = [pytest.mark.l_judge_live_adapter_safety_cycle54]

REPO = Path(__file__).resolve().parents[1]
DESIGN = REPO / "docs" / "design" / "L_JUDGE_LIVE_ADAPTER_SAFETY_CASE.md"
PRIOR_DESIGN = REPO / "docs" / "design" / "L_JUDGE_LIVE_ADAPTER_DESIGN.md"
CAP = REPO / "docs" / "capabilities" / "MESH_L_JUDGE_LIVE_ADAPTER_SAFETY_CASE.md"
SCHEMA = REPO / "docs" / "schema" / "judge" / "live_adapter_safety_v0.md"


def test_version_and_constants():
    assert __version__ == "0.18.0"
    assert PACKAGE_HELD == "0.18.0"
    assert SEAL_CP == "CP-0058"
    assert PRIOR_CP == "CP-0057"
    assert CYCLE == 54
    assert PREFERRED_NEXT_DEFAULT == "await_deepseek"
    assert SCHEMA_SAFETY == "mesh.judge.live_adapter_safety/v0"


def test_safety_case_doc_present():
    assert DESIGN.is_file()
    text = DESIGN.read_text(encoding="utf-8")
    assert "DESIGN ONLY" in text
    assert "CP-0058" in text
    assert "Threat model" in text or "threat model" in text.lower()
    assert "secret_handle" in text
    assert "RefuseTransport" in text
    assert "Rate limits" in text or "rate limit" in text.lower()
    assert "must stay false" in text.lower() or "Must stay" in text
    assert "ENGINE_RATE_LIMIT" in text
    assert "no-audit" in text.lower() or "NO_AUDIT" in text
    assert "no live API" in text.lower() or "No live API" in text


def test_extends_prior_live_adapter_design():
    text = DESIGN.read_text(encoding="utf-8")
    assert "L_JUDGE_LIVE_ADAPTER_DESIGN" in text
    assert PRIOR_DESIGN.is_file()
    assert "CP-0057" in text or "CP-0057" in PRIOR_DESIGN.read_text(encoding="utf-8")
    assert SCHEMA.is_file()
    stext = SCHEMA.read_text(encoding="utf-8")
    assert "mesh.judge.live_adapter_safety/v0" in stext
    assert "must_stay_false" in stext


def test_no_live_api_or_keys_in_safety_docs():
    for path in (DESIGN, SCHEMA, CAP):
        text = path.read_text(encoding="utf-8")
        assert not re.search(r"sk-[A-Za-z0-9]{10,}", text), path.name
        assert "Authorization: Bearer sk-" not in text
    assert "secret_handle" in DESIGN.read_text(encoding="utf-8")


def test_abort_and_rate_limit_coverage():
    text = DESIGN.read_text(encoding="utf-8")
    for code in ABORT_CODES:
        assert code in text, code
    assert RATE_LIMIT_FLOORS["max_calls_per_minute"] == 10
    assert RATE_LIMIT_FLOORS["max_retries"] == 1
    assert "never invent" in text.lower() or "Never invent" in text


def test_must_stay_false_table():
    text = DESIGN.read_text(encoding="utf-8").lower()
    for key in (
        "live_adapter.enabled",
        "live_api_in_ci",
        "train_70b",
        "gia_unlocked",
        "raft_runtime",
        "silent_accept_on_error",
    ):
        assert key in text or key.replace("_", " ") in text or key in DESIGN.read_text(
            encoding="utf-8"
        )
    assert set(MUST_STAY_FALSE) >= PERMANENT_FALSE
    assert "gia_unlocked" in PERMANENT_FALSE
    assert "train_70b" in PERMANENT_FALSE


def test_secret_handle_rules_helpers():
    assert is_valid_secret_handle("mesh://secrets/judge/live@v1")
    assert is_valid_secret_handle("mesh://secrets/judge/live_adapter@v2")
    assert not is_valid_secret_handle(None)
    assert not is_valid_secret_handle("")
    assert not is_valid_secret_handle("sk-abcdefghijklmnopqrstuvwxyz")
    assert not is_valid_secret_handle("api_key=supersecretvalue")
    assert not is_valid_secret_handle("https://example/secrets/x")
    assert looks_like_raw_secret("Authorization: Bearer sk-abcdefghijklmnop")
    assert looks_like_raw_secret("api_key=abcd1234efgh")
    assert not looks_like_raw_secret("mesh://secrets/judge/live@v1")


def test_refuse_transport_negative_paths():
    rt = RefuseTransport()
    out = rt.call({"request_id": "r1"}, timeout_s=1.0)
    assert out["ok"] is False
    assert out["error_code"] == "ENGINE_DISABLED"
    assert out["verdict"] == "ABORT"
    assert out["abort"]["code"] == "ENGINE_DISABLED"
    assert out["raw_text"] is None
    health = rt.health()
    assert health["live"] is False
    assert health["binding"] == "RefuseTransport"


def test_enablement_gates_fail_closed():
    gate = default_safety_gate()
    assert gate["enabled"] is False
    assert gate["refuse_transport_default"] is True
    assert gate["schema"] == SCHEMA_SAFETY
    assert all(v is False for v in gate["must_stay_false"].values())

    # Default: may not enable
    res = evaluate_enablement_gates()
    assert res.may_enable is False
    assert "safety_case_not_verified" in res.reasons
    assert "secret_handle_invalid_or_missing" in res.reasons

    # Even with optimistic inputs, THIS CP hard-refuses may_enable
    optimistic = evaluate_enablement_gates(
        flags={"live_adapter.enabled": True, "train_70b": True},
        secret_handle="mesh://secrets/judge/live@v1",
        tls_endpoint=True,
        audit_sink=True,
        prior_dry_run_proven=True,
        safety_case_verified=True,
        impl_cp_authorized=True,
    )
    assert optimistic.may_enable is False
    assert any("permanent_false" in r or "train_70b" in r for r in optimistic.reasons)
    assert any("live_adapter.enabled" in r for r in optimistic.reasons)


def test_capability_and_agreement():
    assert CAP.is_file()
    ctext = CAP.read_text(encoding="utf-8")
    assert "CP-0058" in ctext
    assert "DESIGN ONLY" in ctext
    assert "NO_HELD" in ctext
    atext = (REPO / "council" / "COUNCIL_AGREEMENT_CYCLE54.md").read_text(encoding="utf-8")
    assert "CP-0058" in atext
    assert "safety" in atext.lower()


def test_no_src_live_codec():
    src = REPO / "src" / "neural_mesh"
    banned = list(src.glob("judge*.py")) + list(src.glob("**/live_http*.py"))
    banned += list(src.glob("**/live_adapter_http*.py"))
    assert banned == [], f"unexpected live codec files: {banned}"
    # Helper module is packaging safety only — allowed
    assert (src / "packaging" / "l_judge_live_adapter_safety.py").is_file()


def test_no_gia_raft_train_claims():
    text = DESIGN.read_text(encoding="utf-8")
    low = text.lower()
    assert "NO_HELD" in text
    assert "DO_NOT_TRAIN_70B_NOW" in text
    assert "we unlocked gia" not in low
    assert "n>2" in low or "n_gt_2" in low
    assert "no live api" in low or "No live API" in text


def test_prior_cp_and_l1_context():
    assert (REPO / "snapshots" / "CP-0057").is_dir()
    bp = (REPO / "council" / "blueprint" / "FINAL_BLUEPRINT_ROOT.md").read_text(
        encoding="utf-8"
    )
    assert "L1 REMAINING_0.17 [CLOSED]" in bp


def test_tags_untouched():
    for tag in ("v0.18.0", "v0.17.0", "v0.16.3"):
        assert (
            subprocess.run(
                ["git", "rev-parse", "--verify", tag],
                cwd=str(REPO),
                capture_output=True,
            ).returncode
            == 0
        )


def test_pyproject_marker_registered():
    text = (REPO / "pyproject.toml").read_text(encoding="utf-8")
    assert "l_judge_live_adapter_safety_cycle54" in text
