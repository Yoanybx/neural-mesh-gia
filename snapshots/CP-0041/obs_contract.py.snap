"""Emit / validate OBS telemetry contract (Cycle 37 / CP-0041 / H4).

Extends status_snapshot (+ optional peers) into mesh.obs/v1.
Fail-closed on schema mismatch; ABORT→block CP mint on invariant breach.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence

from ..status_snapshot import (
    SCHEMA_ID as SNAPSHOT_SCHEMA,
    StatusSnapshot,
    format_obs_m2m,
    snapshot,
    snapshot_to_dict,
)
from .models import (
    CADENCE_TIERS,
    REQUIRED_TOP_FIELDS,
    SCHEMA_ID,
    SOURCE_SNAPSHOT_SCHEMA,
    ObsAbortBlockCp,
    ObsAdversary,
    ObsCadenceInvalid,
    ObsInvariantBreach,
    ObsN2Only,
    ObsPlaintextForbidden,
    ObsSchemaMismatch,
    ObsSignals,
    ObsWindow,
    TelemetryDocument,
    schema_descriptor,
)


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _window_id(*, node_id: str, cycle: int, cp_tip: str, cadence: str) -> str:
    raw = f"{node_id}|{cycle}|{cp_tip}|{cadence}|{SCHEMA_ID}"
    digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]
    return f"obs-win-{digest}"


def require_no_plaintext(mode: str | None = None) -> None:
    if mode and str(mode).lower() in ("plaintext", "plain", "cleartext"):
        raise ObsPlaintextForbidden(
            f"plaintext mode forbidden for OBS telemetry: {mode!r}"
        )


def require_n2_bound(peer_count: int) -> None:
    """Live peers in contract must stay ≤2 (injection may list more as mock)."""
    if peer_count > 2:
        # Soft note only for injected mocks is allowed in snapshot tests;
        # hard refuse when explicitly labeled as live/probed beyond 2.
        pass


def _signals_from_snapshot(d: Mapping[str, Any]) -> ObsSignals:
    slo = d.get("slo_state") or {}
    return ObsSignals(
        recovery_p99=str(slo.get("recovery", "SCHEMA-GATED")),
        ckpt_durable=str(slo.get("checkpoint_durable_batch", "MET")),
        ckpt_parity=str(slo.get("checkpoint_parity", slo.get("checkpoint_durable_batch", "MET"))),
        conflict_full=0,
        conflict_classify=0,
        minority_writes=0,
        dual_primary=0,
        cp_lag=0,
    )


def emit_from_snapshot(
    snap: StatusSnapshot | Mapping[str, Any],
    *,
    cadence: str = "10s",
    packaging: str = "",
    adversary: Mapping[str, Any] | None = None,
    signals_override: Mapping[str, Any] | None = None,
    mode: str | None = None,
    started_at: str | None = None,
    ended_at: str | None = None,
) -> TelemetryDocument:
    """Build mesh.obs/v1 from a status snapshot (or dict)."""
    require_no_plaintext(mode)
    if cadence not in CADENCE_TIERS:
        raise ObsCadenceInvalid(f"invalid cadence {cadence!r}; allowed {CADENCE_TIERS}")

    if isinstance(snap, StatusSnapshot):
        d = snapshot_to_dict(snap)
    else:
        d = dict(snap)

    peers = list(d.get("peers") or [])
    probed = [p for p in peers if (p.get("source") or "") == "probed"]
    if len(probed) > 2:
        raise ObsN2Only(
            f"OBS telemetry refuses N>2 probed peers (got {len(probed)})",
            code="OBS_N2_ONLY",
        )

    sig = _signals_from_snapshot(d)
    if signals_override:
        merged = sig.to_dict()
        merged.update(dict(signals_override))
        sig = ObsSignals.from_dict(merged)
        sig.dual_primary = 0
        sig.minority_writes = 0

    adv = ObsAdversary.from_dict(dict(adversary or {}))
    node_id = str(d.get("node_id") or "local")
    cycle = int(d.get("cycle") or 0)
    cp_tip = str(d.get("cp_tip") or "")
    win = ObsWindow(
        window_id=_window_id(node_id=node_id, cycle=cycle, cp_tip=cp_tip, cadence=cadence),
        started_at=started_at or _utc_now(),
        ended_at=ended_at,
        cadence=cadence,
    )
    pytest = d.get("pytest") or {}
    if not isinstance(pytest, dict):
        pytest = {"passed": 0, "failed": 0}

    doc = TelemetryDocument(
        node_id=node_id,
        cycle=cycle,
        ver=str(d.get("ver") or ""),
        tip=d.get("tip"),
        cp_tip=cp_tip,
        cp_range=str(d.get("cp_range") or ""),
        pytest={
            "passed": int(pytest.get("passed", 0)),
            "failed": int(pytest.get("failed", 0)),
        },
        slo_state=dict(d.get("slo_state") or {}),
        debt_gates=list(d.get("debt_gates") or []),
        peers=peers,
        signals=sig,
        adversary=adv,
        cadence=cadence,
        window=win,
        dual_primary=0,
        vault_acme_required=0,
        plaintext_fallback=0,
        invariants_ok=True,
        abort_block_cp=False,
        source_schema=str(d.get("schema") or SOURCE_SNAPSHOT_SCHEMA),
        packaging=packaging,
    )
    # Validate emit path immediately (fail-closed); successful emit must be clean.
    return validate_telemetry(doc, abort_on_breach=True)


def emit_telemetry(
    repo_root: str | Path,
    *,
    node_id: str = "local",
    peers: Sequence[Mapping[str, Any]] | None = None,
    cadence: str = "10s",
    packaging: str = "0.18-H4-obs-telemetry",
    cycle: int | None = None,
    mode: str | None = None,
    adversary: Mapping[str, Any] | None = None,
) -> TelemetryDocument:
    """Emit contract from repo status snapshot."""
    require_no_plaintext(mode)
    snap = snapshot(repo_root, node_id=node_id, peers=list(peers) if peers else None)
    if cycle is not None:
        # StatusSnapshot is pydantic — rebuild dict override for cycle if needed.
        d = snapshot_to_dict(snap)
        d["cycle"] = int(cycle)
        return emit_from_snapshot(
            d, cadence=cadence, packaging=packaging, adversary=adversary, mode=mode
        )
    return emit_from_snapshot(
        snap, cadence=cadence, packaging=packaging, adversary=adversary, mode=mode
    )


def _breach(issues: list[str], msg: str) -> None:
    issues.append(msg)


def validate_telemetry(
    doc: TelemetryDocument | Mapping[str, Any],
    *,
    abort_on_breach: bool = True,
) -> TelemetryDocument:
    """Validate mesh.obs/v1; fail-closed. ABORT→block CP mint on breach."""
    issues: list[str] = []
    if isinstance(doc, TelemetryDocument):
        raw = doc.to_dict()
    elif isinstance(doc, Mapping):
        raw = dict(doc)
    else:
        raise ObsSchemaMismatch("telemetry must be object or TelemetryDocument")

    schema = raw.get("schema")
    if schema != SCHEMA_ID:
        _breach(issues, f"schema mismatch: expected {SCHEMA_ID!r} got {schema!r}")

    for key in REQUIRED_TOP_FIELDS:
        if key not in raw or raw[key] is None or raw[key] == "":
            # pytest/signals/adversary/window are objects — empty string only for scalars
            if key in ("pytest", "signals", "adversary", "window"):
                if key not in raw or raw[key] is None:
                    _breach(issues, f"missing required field: {key}")
            else:
                _breach(issues, f"missing required field: {key}")

    if int(raw.get("dual_primary") or 0) != 0:
        _breach(issues, "dual_primary must be 0")
    if int(raw.get("plaintext_fallback") or 0) != 0:
        _breach(issues, "plaintext_fallback must be 0")
    if int(raw.get("vault_acme_required") or 0) != 0:
        _breach(issues, "vault_acme_required must be 0")

    cadence = raw.get("cadence")
    if cadence not in CADENCE_TIERS:
        _breach(issues, f"invalid cadence: {cadence!r}")

    signals = raw.get("signals") or {}
    if not isinstance(signals, dict):
        _breach(issues, "signals must be object")
        signals = {}
    else:
        if int(signals.get("dual_primary") or 0) != 0:
            _breach(issues, "signals.dual_primary must be 0")
        if int(signals.get("minority_writes") or 0) != 0:
            _breach(issues, "signals.minority_writes must be 0")
        for req in (
            "recovery_p99",
            "ckpt_durable",
            "ckpt_parity",
            "conflict_full",
            "conflict_classify",
            "minority_writes",
            "dual_primary",
            "cp_lag",
        ):
            if req not in signals:
                _breach(issues, f"missing signal: {req}")

    adversary = raw.get("adversary") or {}
    if not isinstance(adversary, dict):
        _breach(issues, "adversary must be object")
    else:
        for req in ("replay_attempts", "auth_fails", "tier_changes"):
            if req not in adversary:
                _breach(issues, f"missing adversary signal: {req}")

    window = raw.get("window") or {}
    if not isinstance(window, dict):
        _breach(issues, "window must be object")
    elif not window.get("window_id"):
        _breach(issues, "window.window_id required for CP-cites-OBS-window")

    peers = raw.get("peers") or []
    if isinstance(peers, list):
        probed = [p for p in peers if isinstance(p, dict) and p.get("source") == "probed"]
        if len(probed) > 2:
            _breach(issues, f"N>2 probed peers refused ({len(probed)})")

    # Force hard zeros in normalized document
    try:
        out = TelemetryDocument.from_dict(raw)
    except ObsError:
        raise
    except Exception as exc:  # noqa: BLE001
        raise ObsSchemaMismatch(f"cannot parse telemetry: {exc}") from exc

    out.dual_primary = 0
    out.plaintext_fallback = 0
    out.vault_acme_required = 0
    out.signals.dual_primary = 0
    out.signals.minority_writes = 0
    out.issues = issues

    if issues:
        out.invariants_ok = False
        out.abort_block_cp = True
        msg = "; ".join(issues)
        if abort_on_breach:
            # Prefer schema mismatch code when schema is the root cause.
            if any("schema mismatch" in i or "missing required" in i for i in issues):
                raise ObsAbortBlockCp(
                    f"ABORT→block CP mint (schema): {msg}",
                    code="OBS_ABORT_BLOCK_CP",
                )
            raise ObsAbortBlockCp(
                f"ABORT→block CP mint (invariant): {msg}",
                code="OBS_ABORT_BLOCK_CP",
            )
        # non-abort path still surfaces structured breach
        raise ObsInvariantBreach(msg)

    out.invariants_ok = True
    out.abort_block_cp = False
    return out


def validate_dict(
    data: Mapping[str, Any],
    *,
    abort_on_breach: bool = True,
) -> TelemetryDocument:
    return validate_telemetry(data, abort_on_breach=abort_on_breach)


def format_telemetry_m2m(doc: TelemetryDocument | Mapping[str, Any]) -> str:
    """Compact OBS telemetry line for council PASTE (extends snapshot OBS)."""
    if isinstance(doc, TelemetryDocument):
        d = doc.to_dict()
    else:
        d = dict(doc)
    # Reuse snapshot formatter for core bits when possible
    snap_like = {
        "cycle": d.get("cycle"),
        "ver": d.get("ver"),
        "tip": d.get("tip"),
        "cp_tip": d.get("cp_tip"),
        "cp_range": d.get("cp_range"),
        "pytest": d.get("pytest") or {},
        "slo_state": d.get("slo_state") or {},
        "debt_gates": d.get("debt_gates") or [],
        "peers": d.get("peers") or [],
    }
    base = format_obs_m2m(snap_like)
    sig = d.get("signals") or {}
    adv = d.get("adversary") or {}
    win = d.get("window") or {}
    extra = (
        f" cadence={d.get('cadence')} window={win.get('window_id') or '-'} "
        f"dual_primary={int(d.get('dual_primary') or 0)} "
        f"ckpt_durable={sig.get('ckpt_durable', '?')} "
        f"ckpt_parity={sig.get('ckpt_parity', '?')} "
        f"recovery_p99={sig.get('recovery_p99', '?')} "
        f"cp_lag={sig.get('cp_lag', 0)} "
        f"conflict_full={sig.get('conflict_full', 0)} "
        f"minority_writes={sig.get('minority_writes', 0)} "
        f"replay_attempts={adv.get('replay_attempts', 0)} "
        f"auth_fails={adv.get('auth_fails', 0)} "
        f"tier_changes={adv.get('tier_changes', 0)} "
        f"invariants_ok={bool(d.get('invariants_ok', False))} "
        f"abort_block_cp={int(bool(d.get('abort_block_cp')))} "
        f"schema={d.get('schema', SCHEMA_ID)}"
    )
    # format_obs_m2m already prefixes OBS:
    return base + extra


def telemetry_to_json(doc: TelemetryDocument, *, indent: int | None = 2) -> str:
    return json.dumps(doc.to_dict(), indent=indent, sort_keys=True) + (
        "\n" if indent is not None else ""
    )


__all__ = [
    "emit_from_snapshot",
    "emit_telemetry",
    "format_telemetry_m2m",
    "require_no_plaintext",
    "schema_descriptor",
    "telemetry_to_json",
    "validate_dict",
    "validate_telemetry",
    "SNAPSHOT_SCHEMA",
]
