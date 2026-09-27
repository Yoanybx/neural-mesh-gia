"""L_judge mock e2e with M2 membership SM (CP-0061 / Cycle 57).

Composes existing Mock L_judge (CP-0052 style) with MembershipSM (CP-0059).
Mock-only: no live WAN, no N>2 runtime, no live LLM, live=DISABLED, no pkg0190.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import Any

from neural_mesh.packaging.m2_membership_rejoin import (
    N_CAP,
    MemberState,
    MembershipSM,
    TrustTierName,
)

__all__ = [
    "PACKAGE_HELD",
    "CYCLE",
    "SEAL_CP",
    "PRIOR_CP",
    "PREFERRED_NEXT_DEFAULT",
    "LIVE_API_ENABLED",
    "SCHEMA_BRIDGE",
    "N_CAP",
    "ABORT_CODES",
    "MockLJudgePort",
    "InFlightJudge",
    "JudgeMembershipBridge",
    "BridgeError",
    "sample_judge_request",
]

PACKAGE_HELD = "0.18.0"
CYCLE = 57
SEAL_CP = "CP-0061"
PRIOR_CP = "CP-0060"
PREFERRED_NEXT_DEFAULT = "await_deepseek"
LIVE_API_ENABLED = False  # must stay False (live=DISABLED)
SCHEMA_BRIDGE = "mesh.judge.m2_bridge/v0"

ABORT_CODES: tuple[str, ...] = (
    "JUDGE_MEMBER_NOT_ACTIVE",
    "JUDGE_MEMBER_ATTESTING_SUBMIT",
    "JUDGE_MEMBER_DRAINING",
    "JUDGE_INFLIGHT_CANCELLED",
    "JUDGE_LIVE_DISABLED",
    "SCHEMA_INVALID",
    "FENCE",
    "NO_AUDIT",
    "POLICY_ABORT",
    "MEMBER_N_GT2_REFUSED",
    "MEMBER_INVALID_TRANSITION",
)


def _sha256_hex(data: str | bytes) -> str:
    if isinstance(data, str):
        data = data.encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def _digest(obj: Any) -> str:
    return "sha256:" + _sha256_hex(json.dumps(obj, sort_keys=True, separators=(",", ":")))


def _hash16(obj: Any) -> str:
    return _sha256_hex(json.dumps(obj, sort_keys=True, separators=(",", ":")))[:16]


class BridgeError(RuntimeError):
    """Fail-closed bridge error."""

    code: str = "JUDGE_MEMBER_ERROR"

    def __init__(self, message: str, *, code: str | None = None):
        super().__init__(message)
        if code:
            self.code = code


@dataclass
class MockLJudgePort:
    """Deterministic mock judgment port — no network, no API keys, no live LLM."""

    prev_receipt_hash: str | None = None
    dry_run_accepts: dict[str, str] = field(default_factory=dict)
    audit_sink: bool = True
    receipts: list[dict[str, Any]] = field(default_factory=list)

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
        fence = inj.get("fence") or {}
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
                return self._abort(
                    req, "POLICY_ABORT", "live_advisory requires prior dry_run ACCEPT"
                )

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
            "engine_meta": {
                "latency_ms": 0,
                "model_hint": "mock",
                "truncated": False,
                "live_api": False,
            },
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
            "engine_meta": {
                "latency_ms": 0,
                "model_hint": "mock",
                "truncated": False,
                "live_api": False,
            },
        }
        receipt = self._receipt(req, resp_body, req.get("injection") or {})
        resp_body["receipt_id"] = receipt["receipt_id"]
        return resp_body

    def _receipt(
        self, req: dict[str, Any], resp: dict[str, Any], inj: dict[str, Any]
    ) -> dict[str, Any]:
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
            "node_id": req.get("node_id") or "node:mock",
            "dual_primary": 0,
            "live_api": False,
        }
        self.prev_receipt_hash = "sha256:" + _sha256_hex(
            json.dumps(receipt, sort_keys=True)
        )
        self.receipts.append(receipt)
        return receipt


@dataclass
class InFlightJudge:
    request_id: str
    node_id: str
    mode: str
    family: str
    status: str = "PENDING"  # PENDING | COMPLETED | CANCELLED


@dataclass
class JudgeMembershipBridge:
    """E2E orchestrator: M2 SM gates Mock L_judge. Not a fabric service."""

    sm: MembershipSM = field(default_factory=MembershipSM)
    judge: MockLJudgePort = field(default_factory=MockLJudgePort)
    inflight: dict[str, InFlightJudge] = field(default_factory=dict)
    live_api_enabled: bool = LIVE_API_ENABLED

    # --- membership passthrough ---

    def join(self, node_id: str, *, fingerprint: str = "fp-new", rejoin: bool = False):
        return self.sm.join_intent(node_id, fingerprint=fingerprint, rejoin=rejoin)

    def begin_attest(self, node_id: str):
        return self.sm.begin_attest(node_id)

    def attest_ok(self, node_id: str, *, tier: TrustTierName = TrustTierName.T2):
        return self.sm.attest_ok(node_id, tier=tier)

    def attest_fail(self, node_id: str):
        return self.sm.attest_fail(node_id)

    def drain(self, node_id: str):
        rec = self.sm.drain(node_id)
        # Mid-judgment: cancel in-flight for this node (fail-closed).
        self._cancel_inflight_for(node_id, reason="drain started")
        return rec

    def drain_complete(self, node_id: str):
        return self.sm.drain_complete(node_id)

    def rejoin_intent(self, node_id: str):
        rec = self.sm.rejoin_intent(node_id)
        self._cancel_inflight_for(node_id, reason="rejoin intent")
        return rec

    def enter_joining_from_rejoin(self, node_id: str):
        return self.sm.enter_joining_from_rejoin(node_id)

    # --- judge gated by membership ---

    def judge_dry_run(self, node_id: str, req: dict[str, Any]) -> dict[str, Any]:
        self._refuse_live_api(req)
        gate = self._gate(node_id, mode="dry_run")
        if gate is not None:
            return gate
        req = dict(req)
        req["node_id"] = node_id
        req["mode"] = "dry_run"
        self._stamp_member_fence(node_id, req)
        fid = req["request_id"]
        self.inflight[fid] = InFlightJudge(
            request_id=fid,
            node_id=node_id,
            mode="dry_run",
            family=req["idempotency_key"],
        )
        resp = self.judge.dry_run(req)
        self._complete_inflight(fid, resp)
        return resp

    def judge_submit(self, node_id: str, req: dict[str, Any]) -> dict[str, Any]:
        """live_advisory mock path — still live_api=DISABLED (no network)."""
        self._refuse_live_api(req)
        gate = self._gate(node_id, mode="live_advisory")
        if gate is not None:
            return gate
        req = dict(req)
        req["node_id"] = node_id
        req["mode"] = "live_advisory"
        self._stamp_member_fence(node_id, req)
        fid = req["request_id"]
        self.inflight[fid] = InFlightJudge(
            request_id=fid,
            node_id=node_id,
            mode="live_advisory",
            family=req["idempotency_key"],
        )
        resp = self.judge.submit(req)
        self._complete_inflight(fid, resp)
        return resp

    def cancel_inflight(self, request_id: str, *, reason: str = "cancel") -> dict[str, Any]:
        flight = self.inflight.get(request_id)
        if flight is None:
            return {
                "schema": "mesh.judge.response/v0",
                "request_id": request_id,
                "verdict": "ABORT",
                "abort": {"code": "SCHEMA_INVALID", "reason": "unknown inflight"},
                "receipt_id": None,
            }
        flight.status = "CANCELLED"
        return {
            "schema": "mesh.judge.response/v0",
            "request_id": request_id,
            "verdict": "ABORT",
            "confidence": 0.0,
            "abort": {"code": "JUDGE_INFLIGHT_CANCELLED", "reason": reason},
            "receipt_id": None,
            "engine_meta": {"live_api": False, "model_hint": "mock"},
        }

    def pending_for(self, node_id: str) -> list[InFlightJudge]:
        return [
            f
            for f in self.inflight.values()
            if f.node_id == node_id and f.status == "PENDING"
        ]

    # --- internals ---

    def _refuse_live_api(self, req: dict[str, Any]) -> None:
        if self.live_api_enabled:
            raise BridgeError(
                "live API must stay DISABLED this CP",
                code="JUDGE_LIVE_DISABLED",
            )
        eng = req.get("engine") or {}
        if eng.get("live") is True or eng.get("provider") not in (None, "mock"):
            # Only mock provider allowed while live=DISABLED.
            if eng.get("provider") not in (None, "mock"):
                raise BridgeError(
                    "non-mock engine refused while live=DISABLED",
                    code="JUDGE_LIVE_DISABLED",
                )

    def _gate(self, node_id: str, *, mode: str) -> dict[str, Any] | None:
        rec = self.sm.records.get(node_id)
        if rec is None:
            return self._member_abort(
                None, "JUDGE_MEMBER_NOT_ACTIVE", "unknown member", node_id
            )
        if rec.dual_primary != 0:
            return self._member_abort(
                None, "FENCE", "dual_primary != 0", node_id
            )
        state = rec.state
        if state == MemberState.ACTIVE:
            if rec.tier not in (TrustTierName.T2, TrustTierName.T3):
                return self._member_abort(
                    None, "JUDGE_MEMBER_NOT_ACTIVE", "ACTIVE requires T2|T3", node_id
                )
            return None  # allow dry_run + submit
        if state == MemberState.ATTESTING:
            if mode == "dry_run":
                return None  # attestation advisory dry_run allowed
            return self._member_abort(
                None,
                "JUDGE_MEMBER_ATTESTING_SUBMIT",
                "live_advisory submit forbidden while ATTESTING",
                node_id,
            )
        if state == MemberState.DRAINING:
            return self._member_abort(
                None,
                "JUDGE_MEMBER_DRAINING",
                "new judge refused while DRAINING",
                node_id,
            )
        # JOINING, LEFT, REJOIN
        return self._member_abort(
            None,
            "JUDGE_MEMBER_NOT_ACTIVE",
            f"judge refused in state {state.value}",
            node_id,
        )

    def _stamp_member_fence(self, node_id: str, req: dict[str, Any]) -> None:
        inj = dict(req.get("injection") or {})
        fence = dict(inj.get("fence") or {})
        fence.setdefault("dual_primary", 0)
        fence.setdefault("minority_writes", 0)
        fence["member_state"] = self.sm.records[node_id].state.value
        fence["member_tier"] = self.sm.records[node_id].tier.value
        fence["n_cap"] = N_CAP
        inj["fence"] = fence
        inj.setdefault("schema", "mesh.judge.injection/v0")
        req["injection"] = inj

    def _cancel_inflight_for(self, node_id: str, *, reason: str) -> None:
        for flight in self.inflight.values():
            if flight.node_id == node_id and flight.status == "PENDING":
                flight.status = "CANCELLED"
                # reason recorded on cancel helper; status is enough for e2e

    def _complete_inflight(self, request_id: str, resp: dict[str, Any]) -> None:
        flight = self.inflight.get(request_id)
        if flight is None:
            return
        if flight.status == "CANCELLED":
            # Race: membership cancelled while judge ran — force ABORT surface.
            resp["verdict"] = "ABORT"
            resp["abort"] = {
                "code": "JUDGE_INFLIGHT_CANCELLED",
                "reason": "cancelled by membership transition",
            }
            return
        flight.status = "COMPLETED"

    def _member_abort(
        self,
        req: dict[str, Any] | None,
        code: str,
        reason: str,
        node_id: str,
    ) -> dict[str, Any]:
        rid = (req or {}).get("request_id")
        body = {
            "schema": "mesh.judge.response/v0",
            "request_id": rid,
            "verdict": "ABORT",
            "confidence": 0.0,
            "rationale_digest": _digest({"abort": code, "reason": reason}),
            "rationale_ephemeral": reason,
            "recommended_acts": [],
            "abort": {"code": code, "reason": reason},
            "engine_meta": {
                "latency_ms": 0,
                "model_hint": "mock",
                "truncated": False,
                "live_api": False,
            },
            "member_node_id": node_id,
            "receipt_id": None,
        }
        # Still emit a receipt for audit when possible (hash-chain continuity).
        if req is not None:
            receipt = self.judge._receipt(req, body, req.get("injection") or {})
            body["receipt_id"] = receipt["receipt_id"]
        else:
            # Minimal audit receipt for gate ABORTs without a full request.
            stub_req = {
                "schema": "mesh.judge.request/v0",
                "request_id": rid or "gate-abort",
                "idempotency_key": "gate",
                "goal_id": "goal:gate000000000000",
                "mode": "dry_run",
                "policy_bundle_id": "policy:default",
                "node_id": node_id,
                "engine": {"provider": "mock"},
            }
            receipt = self.judge._receipt(stub_req, body, {})
            body["receipt_id"] = receipt["receipt_id"]
        return body


def sample_judge_request(**overrides: Any) -> dict[str, Any]:
    base: dict[str, Any] = {
        "schema": "mesh.judge.request/v0",
        "request_id": "00000000-0000-4000-8000-000000000001",
        "idempotency_key": "fam-m2-1",
        "goal_id": "goal:abcd1234abcd1234",
        "mode": "dry_run",
        "policy_bundle_id": "policy:default",
        "inputs": {
            "prompt_ref": "inline:mock",
            "artifacts": [],
            "constraints": {
                "max_tokens": 64,
                "timeout_ms": 1000,
                "forbid_side_effects": True,
            },
        },
        "engine": {"provider": "mock", "model_hint": "mock", "endpoint_ref": "none"},
        "continuity_hint": {"step_id": "step:1", "resume_token": None},
        "injection": {
            "schema": "mesh.judge.injection/v0",
            "goal": {
                "goal_id": "goal:abcd1234abcd1234",
                "version": 1,
                "content_digest": "sha256:" + ("a" * 64),
                "title": "mock-goal-m2",
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
