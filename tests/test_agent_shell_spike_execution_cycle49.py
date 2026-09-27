"""Tests for Cycle 49 / CP-0053: agent_shell_spike_execution.

Pipeline: workload → normalize → probes → receipts → reports.
Mock adapter only; no live API keys; no settlement; no src/shell runtime.
Markers: shell_spike_execution_cycle49
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pytest

from neural_mesh import __version__

pytestmark = [pytest.mark.shell_spike_execution_cycle49]

REPO = Path(__file__).resolve().parents[1]

ALLOWED_TOOLS = frozenset({"read_only_tools_only", "echo", "hash_probe"})


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
    """In-process Mesh-side adapter mock — shell is client only."""

    dual_primary: int = 0
    audit_sink: bool = True
    prev_receipt_hash: str | None = None
    workloads: dict[str, dict[str, Any]] = field(default_factory=dict)
    events: dict[str, list[dict[str, Any]]] = field(default_factory=dict)
    judge_dry_run_ok: dict[str, bool] = field(default_factory=dict)

    def submit(self, wl: dict[str, Any]) -> dict[str, Any]:
        probes = self._probes_workload(wl)
        if not all(p["ok"] for p in probes):
            return self._finalize_abort(wl, probes, self._first_fail(probes))
        wid = wl["workload_id"]
        self.workloads[wid] = wl
        self.events[wid] = []
        # normalize ingress as step_start
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
        if wid not in self.workloads:
            return {"ok": False, "abort": {"code": "SCHEMA_INVALID", "reason": "unknown workload"}}
        if ev.get("type") not in ("step_start", "tool_call", "tool_result", "final", "error"):
            return {"ok": False, "abort": {"code": "SCHEMA_INVALID", "reason": "bad event type"}}

        wl = self.workloads[wid]
        if ev["type"] == "tool_call":
            tool = (ev.get("tool") or {}).get("name")
            allow = set((wl.get("bounds") or {}).get("tool_allowlist") or [])
            if tool not in allow and tool not in ALLOWED_TOOLS.intersection(allow or ALLOWED_TOOLS):
                # strict: must be on workload allowlist
                if tool not in allow:
                    return {"ok": False, "abort": {"code": "TOOL_DENIED", "reason": f"tool {tool}"}}
            if (wl.get("bounds") or {}).get("forbid_side_effects") and (ev.get("tool") or {}).get(
                "side_effect"
            ):
                return {"ok": False, "abort": {"code": "POLICY", "reason": "side_effect forbidden"}}

        # bounds: max_steps
        max_steps = int((wl.get("bounds") or {}).get("max_steps") or 8)
        if len(self.events[wid]) >= max_steps and ev["type"] != "final":
            return {"ok": False, "abort": {"code": "POLICY", "reason": "max_steps exceeded"}}

        self.events[wid].append(ev)
        return {"ok": True, "abort": {"code": None, "reason": None}}

    def finalize(self, workload_id: str, *, use_judge: bool = False) -> dict[str, Any]:
        wl = self.workloads.get(workload_id)
        if not wl:
            return self._report_abort(
                {"workload_id": workload_id},
                [],
                "SCHEMA_INVALID",
                "unknown workload",
            )
        probes = self._probes_workload(wl)
        # re-check fence/audit at finalize
        if self.dual_primary != 0:
            probes.append({"name": "dual_primary", "ok": False, "code": "FENCE"})
        if not self.audit_sink:
            probes.append({"name": "audit", "ok": False, "code": "NO_AUDIT"})

        if use_judge:
            family = wl.get("idempotency_key") or workload_id
            if not self.judge_dry_run_ok.get(family):
                # mock Mesh-gated dry_run
                self.judge_dry_run_ok[family] = True
            # live path without flag would ABORT — spike only does dry_run here
            probes.append({"name": "judge_dry_run", "ok": True, "code": None})

        if not all(p["ok"] for p in probes):
            return self._finalize_abort(wl, probes, self._first_fail(probes))

        # ensure a final event exists (normalize output)
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
            "judge_receipt_id": None,
            "obs_event_id": "obs:" + _hash16({"rid": rid}),
            "evidence_entry_id": "ev:" + _hash16({"rid": rid, "kind": "shell_receipt"}),
            "prev_receipt_hash": self.prev_receipt_hash,
            "dual_primary": 0,
            "request_digest": req_digest,
            "probe_digest": probe_digest,
        }
        self.prev_receipt_hash = "sha256:" + _sha256_hex(json.dumps(receipt, sort_keys=True))
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
        }
        self.prev_receipt_hash = "sha256:" + _sha256_hex(json.dumps(receipt, sort_keys=True))
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


def _sample_wl(**overrides: Any) -> dict[str, Any]:
    base = {
        "schema": "mesh.shell.workload/v0",
        "workload_id": "wl:00000000-0000-4000-8000-000000000001",
        "idempotency_key": "shell-fam-1",
        "goal_id": "goal:abcd1234abcd1234",
        "shell": {"name": "fake_shell", "version_hint": "0.0-mock"},
        "bounds": {
            "max_steps": 8,
            "max_wall_ms": 60000,
            "forbid_side_effects": True,
            "tool_allowlist": ["echo", "hash_probe", "read_only_tools_only"],
        },
        "payload": {"kind": "task_text", "digest": "sha256:" + ("b" * 64)},
    }
    base.update(overrides)
    return base


def test_version_held():
    assert __version__ == "0.18.0"


def test_execution_doc():
    text = (REPO / "docs" / "design" / "AGENT_SHELL_SPIKE_EXECUTION.md").read_text(encoding="utf-8")
    assert "workload" in text.lower()
    assert "normalized" in text.lower() or "Normalize" in text
    assert "safety probes" in text.lower() or "Probes" in text
    assert "receipt" in text.lower()
    assert "ABORT" in text
    assert "NO_HELD" in text
    assert "settlement" in text.lower()


def test_capability():
    text = (REPO / "docs" / "capabilities" / "MESH_AGENT_SHELL_SPIKE_EXECUTION.md").read_text(
        encoding="utf-8"
    )
    assert "CP-0053" in text
    assert "M1_scorecard_maturation" in text


def test_shell_schema_abort_codes():
    text = (REPO / "docs" / "schema" / "shell" / "v0.md").read_text(encoding="utf-8")
    assert "TOOL_DENIED" in text
    assert "mesh.shell.receipt/v0" in text


def test_happy_path_pipeline():
    ad = MockAgentShellAdapter()
    sub = ad.submit(_sample_wl())
    assert sub["verdict"] == "ACCEPT"
    ack = ad.ingest_event(
        {
            "schema": "mesh.shell.event/v0",
            "event_id": "sev:tool1",
            "workload_id": sub["workload_id"],
            "type": "tool_call",
            "tool": {"name": "echo", "side_effect": False},
            "payload_digest": _digest({"argv": ["hi"]}),
            "ts_hlc": "mock-hlc-1",
        }
    )
    assert ack["ok"] is True
    ad.ingest_event(
        {
            "schema": "mesh.shell.event/v0",
            "event_id": "sev:tool1r",
            "workload_id": sub["workload_id"],
            "type": "tool_result",
            "payload_digest": _digest({"out": "hi"}),
            "ts_hlc": "mock-hlc-2",
        }
    )
    report = ad.finalize(sub["workload_id"], use_judge=True)
    assert report["verdict"] == "ACCEPT"
    assert report["receipt_id"].startswith("rcpt:")
    assert report["receipt"]["prev_receipt_hash"] is None or isinstance(
        report["receipt"]["prev_receipt_hash"], (str, type(None))
    )
    assert any(e["type"] == "final" for e in report["normalized_events"])
    assert all(p["ok"] for p in report["probe_results"])


def test_receipt_hash_chain():
    ad = MockAgentShellAdapter()
    w1 = _sample_wl()
    ad.submit(w1)
    r1 = ad.finalize(w1["workload_id"])
    w2 = _sample_wl(
        workload_id="wl:00000000-0000-4000-8000-000000000002",
        idempotency_key="shell-fam-2",
    )
    ad.submit(w2)
    r2 = ad.finalize(w2["workload_id"])
    assert r1["receipt_id"] != r2["receipt_id"]
    assert r2["receipt"]["prev_receipt_hash"] is not None
    assert r2["receipt"]["prev_receipt_hash"].startswith("sha256:")


def test_abort_schema_invalid():
    ad = MockAgentShellAdapter()
    report = ad.submit(_sample_wl(schema="bad"))
    assert report["verdict"] == "ABORT"
    assert report["abort"]["code"] == "SCHEMA_INVALID"
    assert report["receipt_id"].startswith("rcpt:")


def test_abort_fence_dual_primary():
    ad = MockAgentShellAdapter(dual_primary=1)
    report = ad.submit(_sample_wl())
    assert report["verdict"] == "ABORT"
    assert report["abort"]["code"] == "FENCE"


def test_abort_tool_denied():
    ad = MockAgentShellAdapter()
    sub = ad.submit(_sample_wl())
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
    assert ack["ok"] is False
    assert ack["abort"]["code"] == "TOOL_DENIED"


def test_abort_side_effect_policy():
    ad = MockAgentShellAdapter()
    sub = ad.submit(_sample_wl())
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
    assert ack["ok"] is False
    assert ack["abort"]["code"] == "POLICY"


def test_abort_no_audit_on_finalize():
    ad = MockAgentShellAdapter()
    sub = ad.submit(_sample_wl())
    ad.audit_sink = False
    report = ad.finalize(sub["workload_id"])
    assert report["verdict"] == "ABORT"
    assert report["abort"]["code"] == "NO_AUDIT"


def test_no_src_shell_runtime():
    src = REPO / "src" / "neural_mesh"
    for name in ("shell_adapter.py", "agent_shell.py", "shell_spike.py"):
        assert not (src / name).is_file(), name


def test_agreement_cycle49():
    text = (REPO / "council" / "COUNCIL_AGREEMENT_CYCLE49.md").read_text(encoding="utf-8")
    assert "CP-0053" in text


def test_no_gia_or_economy_unlock():
    for rel in (
        "docs/design/AGENT_SHELL_SPIKE_EXECUTION.md",
        "docs/capabilities/MESH_AGENT_SHELL_SPIKE_EXECUTION.md",
    ):
        text = (REPO / rel).read_text(encoding="utf-8").lower()
        assert "we are gia" not in text
        assert "agi achieved" not in text
        assert "settlement live" not in text
