"""Tests for Cycle 48 / CP-0052: L_judge MIX integration design + mock judge.

Markers: l_judge_integration_cycle48
No live API keys; MockLJudgePort only. No src/ runtime codec.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pytest

from neural_mesh import __version__

pytestmark = [pytest.mark.l_judge_integration_cycle48]

REPO = Path(__file__).resolve().parents[1]


def _sha256_hex(data: str | bytes) -> str:
    if isinstance(data, str):
        data = data.encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def _digest(obj: Any) -> str:
    return "sha256:" + _sha256_hex(json.dumps(obj, sort_keys=True, separators=(",", ":")))


def _hash16(obj: Any) -> str:
    return _sha256_hex(json.dumps(obj, sort_keys=True, separators=(",", ":")))[:16]


@dataclass
class MockLJudgePort:
    """In-test mock judgment port — no network, no API keys."""

    prev_receipt_hash: str | None = None
    dry_run_accepts: dict[str, str] = field(default_factory=dict)
    audit_sink: bool = True

    def dry_run(self, req: dict[str, Any]) -> dict[str, Any]:
        return self._run(req, require_prior_dry_run=False)

    def submit(self, req: dict[str, Any]) -> dict[str, Any]:
        return self._run(req, require_prior_dry_run=True)

    def _run(self, req: dict[str, Any], *, require_prior_dry_run: bool) -> dict[str, Any]:
        if req.get("schema") != "mesh.judge.request/v0":
            return self._abort(req, "SCHEMA_INVALID", "bad request schema")
        if not req.get("idempotency_key") or not req.get("request_id"):
            return self._abort(req, "SCHEMA_INVALID", "missing ids")
        if not req.get("goal_id"):
            return self._abort(req, "SCHEMA_INVALID", "missing goal_id")

        inj = req.get("injection") or {}
        fence = (inj.get("fence") or {})
        if int(fence.get("dual_primary", 0)) != 0:
            return self._abort(req, "FENCE", "dual_primary != 0")
        if not self.audit_sink:
            return self._abort(req, "NO_AUDIT", "no-audit=no-action")

        mode = req.get("mode")
        if mode not in ("dry_run", "live_advisory"):
            return self._abort(req, "SCHEMA_INVALID", "bad mode")

        family = req["idempotency_key"]
        if require_prior_dry_run or mode == "live_advisory":
            if mode == "live_advisory" and self.dry_run_accepts.get(family) != "ACCEPT":
                return self._abort(req, "POLICY_ABORT", "live_advisory requires prior dry_run ACCEPT")

        # Structured judgment (mock skips raw LLM parse)
        verdict = "ACCEPT"
        conf = 0.9
        resp_body = {
            "schema": "mesh.judge.response/v0",
            "request_id": req["request_id"],
            "verdict": verdict,
            "confidence": conf,
            "rationale_digest": _digest({"mock": True, "verdict": verdict}),
            "rationale_ephemeral": "mock-ok",
            "recommended_acts": [],
            "abort": {"code": None, "reason": None},
            "engine_meta": {"latency_ms": 0, "model_hint": "mock", "truncated": False},
        }
        receipt = self._receipt(req, resp_body, inj)
        resp_body["receipt_id"] = receipt["receipt_id"]
        if mode == "dry_run" and verdict == "ACCEPT":
            self.dry_run_accepts[family] = "ACCEPT"
        return resp_body

    def _abort(self, req: dict[str, Any], code: str, reason: str) -> dict[str, Any]:
        resp_body = {
            "schema": "mesh.judge.response/v0",
            "request_id": req.get("request_id"),
            "verdict": "ABORT",
            "confidence": 0.0,
            "rationale_digest": _digest({"abort": code, "reason": reason}),
            "rationale_ephemeral": reason,
            "recommended_acts": [],
            "abort": {"code": code, "reason": reason},
            "engine_meta": {"latency_ms": 0, "model_hint": "mock", "truncated": False},
        }
        receipt = self._receipt(req, resp_body, req.get("injection") or {})
        resp_body["receipt_id"] = receipt["receipt_id"]
        return resp_body

    def _receipt(self, req: dict[str, Any], resp: dict[str, Any], inj: dict[str, Any]) -> dict[str, Any]:
        req_d = _digest(req)
        resp_d = _digest({k: v for k, v in resp.items() if k != "receipt_id"})
        inj_d = _digest(inj) if inj else "sha256:" + ("0" * 64)
        payload = {
            "request_digest": req_d,
            "response_digest": resp_d,
            "prev_receipt_hash": self.prev_receipt_hash,
        }
        rid = "rcpt:" + _hash16(payload)
        receipt = {
            "schema": "mesh.judge.receipt/v0",
            "receipt_id": rid,
            "request_digest": req_d,
            "response_digest": resp_d,
            "injection_digest": inj_d,
            "goal_id": req.get("goal_id"),
            "continuity_id": (inj.get("continuity") or {}).get("continuity_id"),
            "policy_bundle_id": req.get("policy_bundle_id"),
            "verdict": resp["verdict"],
            "obs_event_id": "obs:" + _hash16({"rid": rid}),
            "evidence_entry_id": "ev:" + _hash16({"rid": rid, "kind": "judge_receipt"}),
            "created_hlc": "mock-hlc",
            "prev_receipt_hash": self.prev_receipt_hash,
            "node_id": "node:mock",
            "dual_primary": 0,
        }
        self.prev_receipt_hash = "sha256:" + _sha256_hex(json.dumps(receipt, sort_keys=True))
        return receipt


def _sample_req(**overrides: Any) -> dict[str, Any]:
    base = {
        "schema": "mesh.judge.request/v0",
        "request_id": "00000000-0000-4000-8000-000000000001",
        "idempotency_key": "fam-1",
        "goal_id": "goal:abcd1234abcd1234",
        "mode": "dry_run",
        "policy_bundle_id": "policy:default",
        "inputs": {
            "prompt_ref": "inline:mock",
            "artifacts": [],
            "constraints": {"max_tokens": 64, "timeout_ms": 1000, "forbid_side_effects": True},
        },
        "engine": {"provider": "mock", "model_hint": "mock", "endpoint_ref": "none"},
        "continuity_hint": {"step_id": "step:1", "resume_token": None},
        "injection": {
            "schema": "mesh.judge.injection/v0",
            "goal": {
                "goal_id": "goal:abcd1234abcd1234",
                "version": 1,
                "content_digest": "sha256:" + ("a" * 64),
                "title": "mock-goal",
                "terminal": False,
            },
            "continuity": {
                "continuity_id": "cont:bbbbbbbbbbbbbbbb",
                "state": "RUNNING",
                "step_id": "step:1",
                "resume_token": None,
                "last_receipt_id": None,
            },
            "obs_evidence": [],
            "policy_bundle_id": "policy:default",
            "fence": {"dual_primary": 0, "minority_writes": 0},
        },
    }
    base.update(overrides)
    return base


def test_version_held():
    assert __version__ == "0.18.0"


def test_integration_doc():
    text = (REPO / "docs" / "design" / "L_JUDGE_MIX_INTEGRATION.md").read_text(encoding="utf-8")
    assert "I2" in text and "I6" in text
    assert "InjectionEnv" in text or "injection" in text.lower()
    assert "JudgeReceipt" in text
    assert "ABORT" in text
    assert "DO_NOT_TRAIN_70B_NOW" in text
    assert "NO_HELD" in text
    assert "MockLJudge" in text or "mock" in text.lower()


def test_injection_schema_stub():
    text = (REPO / "docs" / "schema" / "judge" / "injection_v0.md").read_text(encoding="utf-8")
    assert "mesh.judge.injection/v0" in text
    assert "dual_primary" in text
    assert "NO_HELD" in text


def test_capability():
    text = (REPO / "docs" / "capabilities" / "MESH_L_JUDGE_MIX_INTEGRATION.md").read_text(
        encoding="utf-8"
    )
    assert "CP-0052" in text
    assert "agent_shell_spike_execution" in text


def test_mock_dry_run_accept():
    port = MockLJudgePort()
    resp = port.dry_run(_sample_req())
    assert resp["verdict"] == "ACCEPT"
    assert resp["receipt_id"].startswith("rcpt:")
    assert resp["abort"]["code"] is None


def test_mock_live_requires_dry_run():
    port = MockLJudgePort()
    resp = port.submit(_sample_req(mode="live_advisory"))
    assert resp["verdict"] == "ABORT"
    assert resp["abort"]["code"] == "POLICY_ABORT"
    # proper path
    assert port.dry_run(_sample_req())["verdict"] == "ACCEPT"
    ok = port.submit(_sample_req(mode="live_advisory", request_id="00000000-0000-4000-8000-000000000002"))
    assert ok["verdict"] == "ACCEPT"


def test_mock_fence_dual_primary_abort():
    port = MockLJudgePort()
    req = _sample_req()
    req["injection"]["fence"]["dual_primary"] = 1
    resp = port.dry_run(req)
    assert resp["verdict"] == "ABORT"
    assert resp["abort"]["code"] == "FENCE"


def test_mock_schema_invalid_abort():
    port = MockLJudgePort()
    resp = port.dry_run(_sample_req(schema="bad"))
    assert resp["verdict"] == "ABORT"
    assert resp["abort"]["code"] == "SCHEMA_INVALID"


def test_mock_receipt_hash_chain():
    port = MockLJudgePort()
    r1 = port.dry_run(_sample_req())
    r2 = port.dry_run(
        _sample_req(
            request_id="00000000-0000-4000-8000-000000000003",
            idempotency_key="fam-2",
        )
    )
    assert r1["receipt_id"] != r2["receipt_id"]
    assert port.prev_receipt_hash is not None
    assert port.prev_receipt_hash.startswith("sha256:")


def test_mock_no_audit_abort():
    port = MockLJudgePort(audit_sink=False)
    resp = port.dry_run(_sample_req())
    assert resp["verdict"] == "ABORT"
    assert resp["abort"]["code"] == "NO_AUDIT"


def test_no_runtime_codec_modules():
    src = REPO / "src" / "neural_mesh"
    for name in ("judge_mix.py", "l_judge.py", "judge_port.py", "judge_integration.py"):
        assert not (src / name).is_file(), name


def test_agreement_cycle48():
    text = (REPO / "council" / "COUNCIL_AGREEMENT_CYCLE48.md").read_text(encoding="utf-8")
    assert "CP-0052" in text


def test_no_gia_claims():
    for rel in (
        "docs/design/L_JUDGE_MIX_INTEGRATION.md",
        "docs/schema/judge/injection_v0.md",
        "docs/capabilities/MESH_L_JUDGE_MIX_INTEGRATION.md",
    ):
        text = (REPO / rel).read_text(encoding="utf-8").lower()
        assert "we are gia" not in text
        assert "agi achieved" not in text
