"""Agent-shell extended scenarios (CP-0062 / Cycle 58).

Extends CP-0053 MockAgentShellAdapter with multi-turn workloads, safety-probe
matrix, ABORT variants, and receipt-chain verify under membership churn.
Optionally composes with M2 MembershipSM + Mock L_judge (CP-0061) when natural.

Mock-only: no live LLM, no N>2, no settlement, live=DISABLED, no pkg0190.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import Any, Callable, Iterable

from neural_mesh.packaging.l_judge_m2_e2e import (
    JudgeMembershipBridge,
    MockLJudgePort,
    sample_judge_request,
)
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
    "SCHEMA_SHELL_EXT",
    "N_CAP",
    "ALLOWED_TOOLS",
    "ABORT_CODES",
    "PROBE_NAMES",
    "MockAgentShellAdapter",
    "ShellMembershipBridge",
    "ProbeMatrixResult",
    "sample_workload",
    "run_multi_turn",
    "run_probe_matrix",
    "verify_receipt_chain",
]

PACKAGE_HELD = "0.18.0"
CYCLE = 58
SEAL_CP = "CP-0062"
PRIOR_CP = "CP-0061"
PREFERRED_NEXT_DEFAULT = "0.19_design_set_signoff_v2"
LIVE_API_ENABLED = False  # must stay False (live=DISABLED)
SCHEMA_SHELL_EXT = "mesh.shell.extended_bridge/v0"

ALLOWED_TOOLS = frozenset({"read_only_tools_only", "echo", "hash_probe"})

ABORT_CODES: tuple[str, ...] = (
    "SCHEMA_INVALID",
    "FENCE",
    "POLICY",
    "TOOL_DENIED",
    "NO_AUDIT",
    "NO_DRY_RUN",
    "SHELL_MEMBER_NOT_ACTIVE",
    "SHELL_MEMBER_DRAINING",
    "SHELL_INFLIGHT_CANCELLED",
    "SHELL_LIVE_DISABLED",
    "MEMBER_N_GT2_REFUSED",
)

PROBE_NAMES: tuple[str, ...] = (
    "schema",
    "dual_primary",
    "audit",
    "bounds",
    "tool_allowlist",
    "forbid_side_effects",
    "max_steps",
    "member_active",
)


def _sha256_hex(data: str | bytes) -> str:
    if isinstance(data, str):
        data = data.encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def _digest(obj: Any) -> str:
    return "sha256:" + _sha256_hex(json.dumps(obj, sort_keys=True, separators=(",", ":")))


def _hash16(obj: Any) -> str:
    return _sha256_hex(json.dumps(obj, sort_keys=True, separators=(",", ":")))[:16]


@dataclass
class MockAgentShellAdapter:
    """In-process Mesh-side adapter mock — shell is client only (CP-0053 + extensions)."""

    dual_primary: int = 0
    audit_sink: bool = True
    prev_receipt_hash: str | None = None
    workloads: dict[str, dict[str, Any]] = field(default_factory=dict)
    events: dict[str, list[dict[str, Any]]] = field(default_factory=dict)
    judge_dry_run_ok: dict[str, bool] = field(default_factory=dict)
    receipts: list[dict[str, Any]] = field(default_factory=list)
    cancelled: set[str] = field(default_factory=set)
    live_api_enabled: bool = LIVE_API_ENABLED

    def submit(self, wl: dict[str, Any]) -> dict[str, Any]:
        if self.live_api_enabled:
            return self._report_abort(
                wl, [], "SHELL_LIVE_DISABLED", "live API must stay DISABLED"
            )
        probes = self._probes_workload(wl)
        if not all(p["ok"] for p in probes):
            return self._finalize_abort(wl, probes, self._first_fail(probes))
        wid = wl["workload_id"]
        self.workloads[wid] = wl
        self.events[wid] = []
        self.ingest_event(
            {
                "schema": "mesh.shell.event/v0",
                "event_id": "sev:" + _hash16({"wl": wid, "t": "start"}),
                "workload_id": wid,
                "type": "step_start",
                "payload_digest": _digest({"ingress": True}),
                "ts_hlc": "mock-hlc-0",
            }
        )
        return {
            "schema": "mesh.shell.report/v0",
            "workload_id": wid,
            "verdict": "ACCEPT",
            "receipt_id": None,
            "summary_digest": _digest({"phase": "accepted"}),
            "abort": {"code": None, "reason": None},
            "probe_results": probes,
        }

    def ingest_event(self, ev: dict[str, Any]) -> dict[str, Any]:
        if ev.get("schema") != "mesh.shell.event/v0":
            return {"ok": False, "abort": {"code": "SCHEMA_INVALID", "reason": "bad event schema"}}
        wid = ev.get("workload_id")
        if wid in self.cancelled:
            return {
                "ok": False,
                "abort": {"code": "SHELL_INFLIGHT_CANCELLED", "reason": "workload cancelled"},
            }
        if wid not in self.workloads:
            return {"ok": False, "abort": {"code": "SCHEMA_INVALID", "reason": "unknown workload"}}
        if ev.get("type") not in ("step_start", "tool_call", "tool_result", "final", "error"):
            return {"ok": False, "abort": {"code": "SCHEMA_INVALID", "reason": "bad event type"}}

        wl = self.workloads[wid]
        if ev["type"] == "tool_call":
            tool = (ev.get("tool") or {}).get("name")
            allow = set((wl.get("bounds") or {}).get("tool_allowlist") or [])
            if tool not in allow:
                return {"ok": False, "abort": {"code": "TOOL_DENIED", "reason": f"tool {tool}"}}
            if (wl.get("bounds") or {}).get("forbid_side_effects") and (ev.get("tool") or {}).get(
                "side_effect"
            ):
                return {"ok": False, "abort": {"code": "POLICY", "reason": "side_effect forbidden"}}

        max_steps = int((wl.get("bounds") or {}).get("max_steps") or 8)
        if len(self.events[wid]) >= max_steps and ev["type"] != "final":
            return {"ok": False, "abort": {"code": "POLICY", "reason": "max_steps exceeded"}}

        self.events[wid].append(ev)
        return {"ok": True, "abort": {"code": None, "reason": None}}

    def cancel_workload(self, workload_id: str, *, reason: str = "cancel") -> dict[str, Any]:
        self.cancelled.add(workload_id)
        wl = self.workloads.get(workload_id) or {"workload_id": workload_id}
        return self._report_abort(wl, [], "SHELL_INFLIGHT_CANCELLED", reason)

    def finalize(
        self,
        workload_id: str,
        *,
        use_judge: bool = False,
        judge_port: MockLJudgePort | None = None,
        require_prior_dry_run: bool = False,
    ) -> dict[str, Any]:
        if workload_id in self.cancelled:
            wl = self.workloads.get(workload_id) or {"workload_id": workload_id}
            return self._report_abort(wl, [], "SHELL_INFLIGHT_CANCELLED", "cancelled before finalize")
        wl = self.workloads.get(workload_id)
        if not wl:
            return self._report_abort(
                {"workload_id": workload_id},
                [],
                "SCHEMA_INVALID",
                "unknown workload",
            )
        probes = self._probes_workload(wl)
        if self.dual_primary != 0:
            probes.append({"name": "dual_primary", "ok": False, "code": "FENCE"})
        if not self.audit_sink:
            probes.append({"name": "audit", "ok": False, "code": "NO_AUDIT"})

        judge_receipt_id = None
        if use_judge:
            family = wl.get("idempotency_key") or workload_id
            if require_prior_dry_run and not self.judge_dry_run_ok.get(family):
                probes.append({"name": "judge_dry_run", "ok": False, "code": "NO_DRY_RUN"})
            else:
                if judge_port is not None:
                    req = sample_judge_request(
                        request_id="00000000-0000-4000-8000-" + _hash16({"wl": workload_id})[:12].ljust(12, "0"),
                        idempotency_key=family,
                        mode="dry_run",
                    )
                    resp = judge_port.dry_run(req)
                    if resp.get("verdict") != "ACCEPT":
                        probes.append(
                            {
                                "name": "judge_dry_run",
                                "ok": False,
                                "code": (resp.get("abort") or {}).get("code") or "POLICY",
                            }
                        )
                    else:
                        self.judge_dry_run_ok[family] = True
                        judge_receipt_id = resp.get("receipt_id")
                        probes.append({"name": "judge_dry_run", "ok": True, "code": None})
                else:
                    self.judge_dry_run_ok[family] = True
                    probes.append({"name": "judge_dry_run", "ok": True, "code": None})

        if not all(p["ok"] for p in probes):
            return self._finalize_abort(wl, probes, self._first_fail(probes))

        evs = self.events.get(workload_id) or []
        if not any(e.get("type") == "final" for e in evs):
            self.ingest_event(
                {
                    "schema": "mesh.shell.event/v0",
                    "event_id": "sev:" + _hash16({"wl": workload_id, "t": "final"}),
                    "workload_id": workload_id,
                    "type": "final",
                    "payload_digest": _digest({"events": len(evs)}),
                    "ts_hlc": "mock-hlc-final",
                }
            )
            evs = self.events[workload_id]

        probe_digest = _digest(probes)
        req_digest = _digest({"wl": wl, "events": [e["event_id"] for e in evs]})
        payload = {
            "request_digest": req_digest,
            "probe_digest": probe_digest,
            "prev_receipt_hash": self.prev_receipt_hash,
        }
        rid = "rcpt:" + _hash16(payload)
        receipt = {
            "schema": "mesh.shell.receipt/v0",
            "receipt_id": rid,
            "workload_id": workload_id,
            "verdict": "ACCEPT",
            "probe_results": probes,
            "judge_receipt_id": judge_receipt_id,
            "obs_event_id": "obs:" + _hash16({"rid": rid}),
            "evidence_entry_id": "ev:" + _hash16({"rid": rid, "kind": "shell_receipt"}),
            "prev_receipt_hash": self.prev_receipt_hash,
            "dual_primary": 0,
            "request_digest": req_digest,
            "probe_digest": probe_digest,
            "live_api": False,
        }
        self.prev_receipt_hash = "sha256:" + _sha256_hex(json.dumps(receipt, sort_keys=True))
        self.receipts.append(receipt)
        return {
            "schema": "mesh.shell.report/v0",
            "workload_id": workload_id,
            "verdict": "ACCEPT",
            "receipt_id": rid,
            "summary_digest": _digest({"receipt": rid, "n_events": len(evs)}),
            "abort": {"code": None, "reason": None},
            "receipt": receipt,
            "normalized_events": evs,
            "probe_results": probes,
        }

    def _probes_workload(self, wl: dict[str, Any]) -> list[dict[str, Any]]:
        probes: list[dict[str, Any]] = []
        ok_schema = (
            wl.get("schema") == "mesh.shell.workload/v0"
            and bool(wl.get("workload_id"))
            and bool(wl.get("idempotency_key"))
            and isinstance(wl.get("bounds"), dict)
        )
        probes.append(
            {
                "name": "schema",
                "ok": ok_schema,
                "code": None if ok_schema else "SCHEMA_INVALID",
            }
        )
        ok_fence = self.dual_primary == 0
        probes.append({"name": "dual_primary", "ok": ok_fence, "code": None if ok_fence else "FENCE"})
        ok_audit = self.audit_sink
        probes.append({"name": "audit", "ok": ok_audit, "code": None if ok_audit else "NO_AUDIT"})
        bounds = wl.get("bounds") or {}
        ok_bounds = bool(bounds.get("forbid_side_effects", True)) and int(bounds.get("max_steps") or 0) > 0
        probes.append({"name": "bounds", "ok": ok_bounds, "code": None if ok_bounds else "POLICY"})
        return probes

    @staticmethod
    def _first_fail(probes: list[dict[str, Any]]) -> tuple[str, str]:
        for p in probes:
            if not p["ok"]:
                return p.get("code") or "POLICY", p["name"]
        return "POLICY", "unknown"

    def _finalize_abort(
        self, wl: dict[str, Any], probes: list[dict[str, Any]], fail: tuple[str, str]
    ) -> dict[str, Any]:
        code, name = fail
        return self._report_abort(wl, probes, code, f"probe:{name}")

    def _report_abort(
        self, wl: dict[str, Any], probes: list[dict[str, Any]], code: str, reason: str
    ) -> dict[str, Any]:
        wid = wl.get("workload_id")
        payload = {
            "abort": code,
            "reason": reason,
            "prev_receipt_hash": self.prev_receipt_hash,
            "workload_id": wid,
        }
        rid = "rcpt:" + _hash16(payload)
        receipt = {
            "schema": "mesh.shell.receipt/v0",
            "receipt_id": rid,
            "workload_id": wid,
            "verdict": "ABORT",
            "probe_results": probes,
            "judge_receipt_id": None,
            "obs_event_id": "obs:" + _hash16({"rid": rid}),
            "evidence_entry_id": "ev:" + _hash16({"rid": rid, "kind": "shell_abort"}),
            "prev_receipt_hash": self.prev_receipt_hash,
            "dual_primary": self.dual_primary,
            "live_api": False,
        }
        self.prev_receipt_hash = "sha256:" + _sha256_hex(json.dumps(receipt, sort_keys=True))
        self.receipts.append(receipt)
        return {
            "schema": "mesh.shell.report/v0",
            "workload_id": wid,
            "verdict": "ABORT",
            "receipt_id": rid,
            "summary_digest": _digest(payload),
            "abort": {"code": code, "reason": reason},
            "receipt": receipt,
            "probe_results": probes,
        }


@dataclass
class ShellMembershipBridge:
    """Orchestrator: M2 SM gates shell adapter; optional Mock L_judge on finalize.

    Not a fabric service. live=DISABLED. N_CAP=2 held via MembershipSM.
    """

    sm: MembershipSM = field(default_factory=MembershipSM)
    shell: MockAgentShellAdapter = field(default_factory=MockAgentShellAdapter)
    judge_bridge: JudgeMembershipBridge | None = None
    live_api_enabled: bool = LIVE_API_ENABLED
    inflight_workloads: dict[str, str] = field(default_factory=dict)  # wl_id -> node_id

    def ensure_judge(self) -> JudgeMembershipBridge:
        if self.judge_bridge is None:
            # Share the same MembershipSM so shell + judge see one membership view.
            self.judge_bridge = JudgeMembershipBridge(sm=self.sm)
        return self.judge_bridge

    # --- membership passthrough ---

    def join(self, node_id: str, *, fingerprint: str = "fp-shell", rejoin: bool = False):
        return self.sm.join_intent(node_id, fingerprint=fingerprint, rejoin=rejoin)

    def begin_attest(self, node_id: str):
        return self.sm.begin_attest(node_id)

    def attest_ok(self, node_id: str, *, tier: TrustTierName = TrustTierName.T2):
        return self.sm.attest_ok(node_id, tier=tier)

    def drain(self, node_id: str):
        rec = self.sm.drain(node_id)
        self._cancel_inflight_for(node_id, reason="drain started")
        if self.judge_bridge is not None:
            self.judge_bridge._cancel_inflight_for(node_id, reason="drain started")
        return rec

    def drain_complete(self, node_id: str):
        return self.sm.drain_complete(node_id)

    def rejoin_intent(self, node_id: str):
        rec = self.sm.rejoin_intent(node_id)
        self._cancel_inflight_for(node_id, reason="rejoin intent")
        return rec

    def enter_joining_from_rejoin(self, node_id: str):
        return self.sm.enter_joining_from_rejoin(node_id)

    def bring_active(self, node_id: str, *, tier: TrustTierName = TrustTierName.T2) -> None:
        """Convenience: JOINING→ATTESTING→ACTIVE for happy-path tests."""
        if node_id not in self.sm.records:
            self.join(node_id)
        rec = self.sm.records[node_id]
        if rec.state == MemberState.JOINING:
            self.begin_attest(node_id)
            rec = self.sm.records[node_id]
        if rec.state == MemberState.ATTESTING:
            self.attest_ok(node_id, tier=tier)

    # --- shell gated by membership ---

    def submit(self, node_id: str, wl: dict[str, Any]) -> dict[str, Any]:
        if self.live_api_enabled:
            return self.shell._report_abort(
                wl, [], "SHELL_LIVE_DISABLED", "live API must stay DISABLED"
            )
        gate = self._gate(node_id)
        if gate is not None:
            return gate
        report = self.shell.submit(wl)
        if report.get("verdict") == "ACCEPT":
            self.inflight_workloads[wl["workload_id"]] = node_id
        return report

    def ingest_event(self, node_id: str, ev: dict[str, Any]) -> dict[str, Any]:
        gate = self._gate(node_id, allow_attesting=False)
        if gate is not None:
            return {"ok": False, "abort": gate["abort"]}
        return self.shell.ingest_event(ev)

    def finalize(
        self,
        node_id: str,
        workload_id: str,
        *,
        use_judge: bool = False,
    ) -> dict[str, Any]:
        gate = self._gate(node_id)
        if gate is not None:
            # still emit abort receipt via shell cancel path for chain continuity
            if workload_id in self.shell.workloads and workload_id not in self.shell.cancelled:
                return self.shell.cancel_workload(
                    workload_id, reason=gate["abort"]["reason"] or "member gate"
                )
            return gate
        judge_port = None
        if use_judge:
            jb = self.ensure_judge()
            judge_port = jb.judge
        report = self.shell.finalize(
            workload_id,
            use_judge=use_judge,
            judge_port=judge_port,
        )
        self.inflight_workloads.pop(workload_id, None)
        return report

    def _gate(self, node_id: str, *, allow_attesting: bool = False) -> dict[str, Any] | None:
        rec = self.sm.records.get(node_id)
        if rec is None:
            return self._member_abort("SHELL_MEMBER_NOT_ACTIVE", "unknown member", node_id)
        if rec.dual_primary != 0:
            return self._member_abort("FENCE", "dual_primary != 0", node_id)
        state = rec.state
        if state == MemberState.ACTIVE:
            if rec.tier not in (TrustTierName.T2, TrustTierName.T3):
                return self._member_abort(
                    "SHELL_MEMBER_NOT_ACTIVE", "ACTIVE requires T2|T3", node_id
                )
            return None
        if state == MemberState.DRAINING:
            return self._member_abort("SHELL_MEMBER_DRAINING", "member draining", node_id)
        if state == MemberState.ATTESTING and allow_attesting:
            return None
        return self._member_abort(
            "SHELL_MEMBER_NOT_ACTIVE", f"state={state.value}", node_id
        )

    def _member_abort(self, code: str, reason: str, node_id: str) -> dict[str, Any]:
        payload = {"abort": code, "reason": reason, "node_id": node_id}
        rid = "rcpt:" + _hash16(payload)
        receipt = {
            "schema": "mesh.shell.receipt/v0",
            "receipt_id": rid,
            "workload_id": None,
            "verdict": "ABORT",
            "probe_results": [{"name": "member_active", "ok": False, "code": code}],
            "prev_receipt_hash": self.shell.prev_receipt_hash,
            "dual_primary": 0,
            "live_api": False,
        }
        self.shell.prev_receipt_hash = "sha256:" + _sha256_hex(
            json.dumps(receipt, sort_keys=True)
        )
        self.shell.receipts.append(receipt)
        return {
            "schema": "mesh.shell.report/v0",
            "workload_id": None,
            "verdict": "ABORT",
            "receipt_id": rid,
            "summary_digest": _digest(payload),
            "abort": {"code": code, "reason": reason},
            "receipt": receipt,
            "probe_results": receipt["probe_results"],
        }

    def _cancel_inflight_for(self, node_id: str, *, reason: str) -> None:
        for wid, nid in list(self.inflight_workloads.items()):
            if nid == node_id and wid not in self.shell.cancelled:
                self.shell.cancel_workload(wid, reason=reason)
                self.inflight_workloads.pop(wid, None)


def sample_workload(**overrides: Any) -> dict[str, Any]:
    base = {
        "schema": "mesh.shell.workload/v0",
        "workload_id": "wl:00000000-0000-4000-8000-000000000001",
        "idempotency_key": "shell-ext-fam-1",
        "goal_id": "goal:abcd1234abcd1234",
        "shell": {"name": "fake_shell", "version_hint": "0.0-mock"},
        "bounds": {
            "max_steps": 16,
            "max_wall_ms": 60000,
            "forbid_side_effects": True,
            "tool_allowlist": ["echo", "hash_probe", "read_only_tools_only"],
        },
        "payload": {"kind": "task_text", "digest": "sha256:" + ("c" * 64)},
    }
    base.update(overrides)
    return base


def run_multi_turn(
    adapter: MockAgentShellAdapter,
    wl: dict[str, Any],
    *,
    turns: int = 3,
    use_judge: bool = False,
    judge_port: MockLJudgePort | None = None,
) -> dict[str, Any]:
    """Bounded multi-turn tool_call/tool_result then finalize."""
    sub = adapter.submit(wl)
    if sub["verdict"] != "ACCEPT":
        return sub
    wid = wl["workload_id"]
    for i in range(turns):
        ack = adapter.ingest_event(
            {
                "schema": "mesh.shell.event/v0",
                "event_id": f"sev:turn{i}-call",
                "workload_id": wid,
                "type": "tool_call",
                "tool": {"name": "echo", "side_effect": False},
                "payload_digest": _digest({"turn": i, "argv": [f"t{i}"]}),
                "ts_hlc": f"mock-hlc-t{i}a",
            }
        )
        if not ack.get("ok"):
            return {
                "schema": "mesh.shell.report/v0",
                "workload_id": wid,
                "verdict": "ABORT",
                "receipt_id": None,
                "abort": ack["abort"],
                "probe_results": [],
            }
        adapter.ingest_event(
            {
                "schema": "mesh.shell.event/v0",
                "event_id": f"sev:turn{i}-res",
                "workload_id": wid,
                "type": "tool_result",
                "payload_digest": _digest({"turn": i, "out": f"t{i}"}),
                "ts_hlc": f"mock-hlc-t{i}b",
            }
        )
    return adapter.finalize(wid, use_judge=use_judge, judge_port=judge_port)


@dataclass
class ProbeMatrixResult:
    cases: list[dict[str, Any]] = field(default_factory=list)

    @property
    def all_aborted_or_ok(self) -> bool:
        return all(c.get("ok") for c in self.cases)


def run_probe_matrix(make_adapter: Callable[[], MockAgentShellAdapter] | None = None) -> ProbeMatrixResult:
    """Safety-probe matrix: each probe failure → ABORT with expected code."""
    factory = make_adapter or MockAgentShellAdapter
    cases: list[dict[str, Any]] = []

    # schema invalid
    ad = factory()
    r = ad.submit(sample_workload(schema="bad"))
    cases.append(
        {
            "name": "schema",
            "expect": "SCHEMA_INVALID",
            "got": r["abort"]["code"],
            "ok": r["verdict"] == "ABORT" and r["abort"]["code"] == "SCHEMA_INVALID",
        }
    )

    # fence
    ad = factory()
    ad.dual_primary = 1
    r = ad.submit(sample_workload())
    cases.append(
        {
            "name": "dual_primary",
            "expect": "FENCE",
            "got": r["abort"]["code"],
            "ok": r["verdict"] == "ABORT" and r["abort"]["code"] == "FENCE",
        }
    )

    # no audit on finalize
    ad = factory()
    sub = ad.submit(sample_workload())
    assert sub["verdict"] == "ACCEPT"
    ad.audit_sink = False
    r = ad.finalize(sub["workload_id"])
    cases.append(
        {
            "name": "audit",
            "expect": "NO_AUDIT",
            "got": r["abort"]["code"],
            "ok": r["verdict"] == "ABORT" and r["abort"]["code"] == "NO_AUDIT",
        }
    )

    # tool denied
    ad = factory()
    sub = ad.submit(sample_workload())
    ack = ad.ingest_event(
        {
            "schema": "mesh.shell.event/v0",
            "event_id": "sev:badtool",
            "workload_id": sub["workload_id"],
            "type": "tool_call",
            "tool": {"name": "rm_rf", "side_effect": True},
            "payload_digest": _digest({"x": 1}),
            "ts_hlc": "mock-hlc-x",
        }
    )
    cases.append(
        {
            "name": "tool_allowlist",
            "expect": "TOOL_DENIED",
            "got": ack["abort"]["code"],
            "ok": ack["ok"] is False and ack["abort"]["code"] == "TOOL_DENIED",
        }
    )

    # side effect policy
    ad = factory()
    sub = ad.submit(sample_workload())
    ack = ad.ingest_event(
        {
            "schema": "mesh.shell.event/v0",
            "event_id": "sev:se",
            "workload_id": sub["workload_id"],
            "type": "tool_call",
            "tool": {"name": "echo", "side_effect": True},
            "payload_digest": _digest({"x": 2}),
            "ts_hlc": "mock-hlc-y",
        }
    )
    cases.append(
        {
            "name": "forbid_side_effects",
            "expect": "POLICY",
            "got": ack["abort"]["code"],
            "ok": ack["ok"] is False and ack["abort"]["code"] == "POLICY",
        }
    )

    # max_steps
    ad = factory()
    wl = sample_workload(bounds={
        "max_steps": 2,
        "max_wall_ms": 60000,
        "forbid_side_effects": True,
        "tool_allowlist": ["echo"],
    })
    sub = ad.submit(wl)
    # submit already added step_start → 1 event; one more non-final fills max; next fails
    ad.ingest_event(
        {
            "schema": "mesh.shell.event/v0",
            "event_id": "sev:fill",
            "workload_id": sub["workload_id"],
            "type": "tool_result",
            "payload_digest": _digest({"fill": 1}),
            "ts_hlc": "mock-hlc-fill",
        }
    )
    ack = ad.ingest_event(
        {
            "schema": "mesh.shell.event/v0",
            "event_id": "sev:over",
            "workload_id": sub["workload_id"],
            "type": "tool_call",
            "tool": {"name": "echo", "side_effect": False},
            "payload_digest": _digest({"over": 1}),
            "ts_hlc": "mock-hlc-over",
        }
    )
    cases.append(
        {
            "name": "max_steps",
            "expect": "POLICY",
            "got": ack["abort"]["code"],
            "ok": ack["ok"] is False and ack["abort"]["code"] == "POLICY",
        }
    )

    # NO_DRY_RUN when require_prior_dry_run and none recorded
    ad = factory()
    sub = ad.submit(sample_workload(idempotency_key="no-dry-fam"))
    r = ad.finalize(sub["workload_id"], use_judge=True, require_prior_dry_run=True)
    # first finalize with require_prior and no prior → NO_DRY_RUN
    cases.append(
        {
            "name": "no_dry_run",
            "expect": "NO_DRY_RUN",
            "got": r["abort"]["code"],
            "ok": r["verdict"] == "ABORT" and r["abort"]["code"] == "NO_DRY_RUN",
        }
    )

    return ProbeMatrixResult(cases=cases)


def verify_receipt_chain(receipts: Iterable[dict[str, Any]]) -> bool:
    """Verify hash chain: each receipt's prev matches prior receipt body hash."""
    prev: str | None = None
    for r in receipts:
        if r.get("prev_receipt_hash") != prev:
            return False
        prev = "sha256:" + _sha256_hex(json.dumps(r, sort_keys=True))
    return True
