"""Mesh Observability: Status Snapshot (CP-0023 / Cycle 19).

Read-only local (+ optional injected peer) status snapshot for council M2M OBS
and ``mesh status --snapshot``. Does **not** write consensus, Raft, tags schema,
or re-benchmark SLOs.
"""

from __future__ import annotations

import json
import re
import subprocess
import tomllib
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from pydantic import BaseModel, ConfigDict, Field

SCHEMA_ID = "mesh.status.snapshot/v1"
DEBT_DIR = Path("docs") / "debt"
CHECKPOINT_EVERY_FLOOR_DEBT = DEBT_DIR / "CHECKPOINT_EVERY_FLOOR.md"

# Documented SLO states (read from debt / prior seals — never re-benchmarked here).
KNOWN_SLO_STATES = {
    "checkpoint_every_floor": "SCHEMA-GATED",
    "checkpoint_durable_batch": "MET",
    "recovery": "MET",
}

__all__ = [
    "SCHEMA_ID",
    "DebtGate",
    "PeerSummary",
    "PytestSummary",
    "StatusSnapshot",
    "format_obs_m2m",
    "snapshot",
    "snapshot_to_dict",
    "snapshot_to_json",
]


class PytestSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    passed: int = 0
    failed: int = 0


class DebtGate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    state: str
    path: str


class PeerSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    node_id: str
    reachable: bool = False
    summary: dict[str, Any] = Field(default_factory=dict)


class StatusSnapshot(BaseModel):
    """Stable, JSON-serializable mesh status snapshot (v1)."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    schema_name: str = Field(default=SCHEMA_ID, alias="schema")
    node_id: str
    cycle: int
    ver: str
    tip: str | None = None
    cp_range: str
    cp_tip: str
    pytest: PytestSummary = Field(default_factory=PytestSummary)
    slo_state: dict[str, str] = Field(default_factory=dict)
    debt_gates: list[DebtGate] = Field(default_factory=list)
    peers: list[PeerSummary] = Field(default_factory=list)
    local: dict[str, Any] = Field(default_factory=dict)


def _read_pyproject_version(root: Path) -> str | None:
    pyproject = root / "pyproject.toml"
    if not pyproject.is_file():
        return None
    try:
        data = tomllib.loads(pyproject.read_text(encoding="utf-8"))
    except (OSError, tomllib.TOMLDecodeError):
        return None
    ver = data.get("project", {}).get("version")
    return str(ver) if ver else None


def _git_tip7(root: Path) -> str | None:
    try:
        out = subprocess.check_output(
            ["git", "rev-parse", "--short=7", "HEAD"],
            cwd=root,
            stderr=subprocess.DEVNULL,
            text=True,
        ).strip()
        return out or None
    except (subprocess.CalledProcessError, FileNotFoundError, OSError):
        return None


def _load_project_state(root: Path) -> dict[str, Any]:
    p = root / ".project_state" / "CHECKPOINT.json"
    if not p.is_file():
        return {}
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def _parse_cycle_from_docs(root: Path, cp_tip: str) -> int | None:
    """Prefer CURRENT_STATE Cycle; else derive from recent CP→cycle offset."""
    cur = root / ".project_state" / "CURRENT_STATE.md"
    if cur.is_file():
        text = cur.read_text(encoding="utf-8")
        m = re.search(r"(?im)^\*\*Cycle:\*\*\s*(\d+)", text) or re.search(
            r"(?im)^Cycle:\s*(\d+)", text
        )
        if m:
            return int(m.group(1))
    m = re.fullmatch(r"CP-(\d+)", cp_tip or "")
    if m:
        n = int(m.group(1))
        # CP-0018.. ↔ Cycle 14.. (offset 4) holds for recent seals.
        if n >= 18:
            return n - 4
        return n
    return None


def _cp_num(cp_id: str | None) -> int | None:
    if not cp_id:
        return None
    m = re.fullmatch(r"CP-(\d+)", str(cp_id).strip())
    return int(m.group(1)) if m else None


def _list_cp_ids(root: Path) -> list[str]:
    snaps = root / "snapshots"
    if not snaps.is_dir():
        return []
    ids: list[str] = []
    for p in snaps.glob("CP-*"):
        if p.is_dir() and re.fullmatch(r"CP-\d+", p.name):
            ids.append(p.name)
    return sorted(ids, key=lambda x: int(x.split("-")[1]))


def _debt_state_from_doc(text: str) -> str | None:
    """Extract debt Status marker (SCHEMA-GATED / MET / GAP / OPEN)."""
    m = re.search(
        r"(?im)^\*\*Status:\*\*\s*([A-Z][A-Z0-9_-]*(?:\s*/\s*[A-Z][A-Z0-9_-]*)?)",
        text,
    )
    if m:
        # First token (e.g. SCHEMA-GATED)
        return m.group(1).split()[0].split("/")[0].strip()
    for token in ("SCHEMA-GATED", "MET", "GAP", "OPEN", "HELD"):
        if token in text:
            return token
    return None


def _collect_debt_gates(root: Path) -> list[DebtGate]:
    """Collect debt gates that declare an explicit top-level **Status:** marker.

    Trackers without a document-level Status line (table-only notes) are skipped
    so OBS stays focused on schema/SLO debt gates such as CHECKPOINT_EVERY_FLOOR.
    """
    debt_root = root / DEBT_DIR
    gates: list[DebtGate] = []
    if not debt_root.is_dir():
        return gates
    for path in sorted(debt_root.glob("*.md")):
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            continue
        state = _debt_state_from_doc(text)
        if state is None:
            continue
        gate_id = path.stem.upper()
        rel = str(Path("docs") / "debt" / path.name)
        gates.append(DebtGate(id=gate_id, state=state, path=rel))
    return gates


def _slo_state_from_debt(root: Path, debt_gates: Sequence[DebtGate]) -> dict[str, str]:
    """Known SLO keys only — never re-benchmark; prefer debt doc markers."""
    out = dict(KNOWN_SLO_STATES)
    by_id = {g.id: g.state for g in debt_gates}
    if "CHECKPOINT_EVERY_FLOOR" in by_id:
        out["checkpoint_every_floor"] = by_id["CHECKPOINT_EVERY_FLOOR"]
    # Stable key order for callers that dump without sort_keys.
    return {k: out[k] for k in sorted(out)}


def _normalize_peers(
    peers: Sequence[PeerSummary | Mapping[str, Any]] | None,
) -> list[PeerSummary]:
    if not peers:
        return []
    out: list[PeerSummary] = []
    for p in peers:
        if isinstance(p, PeerSummary):
            out.append(p)
        else:
            out.append(PeerSummary.model_validate(dict(p)))
    # Deterministic peer order by node_id.
    return sorted(out, key=lambda x: x.node_id)


def snapshot(
    root: str | Path | None = None,
    *,
    node_id: str | None = None,
    peers: Sequence[PeerSummary | Mapping[str, Any]] | None = None,
    cycle: int | None = None,
    tip: str | None = None,
    pytest_summary: Mapping[str, int] | None = None,
) -> StatusSnapshot:
    """Build a LOCAL read-only status snapshot from ``root``.

    Peer summaries are injected only (no network / consensus). Passing
    ``peers`` never triggers Raft, N>2 fabric, or any write under ``root``.
    """
    base = Path(root) if root is not None else Path.cwd()
    state = _load_project_state(base)

    cp_ids = _list_cp_ids(base)
    last_cp = state.get("last_checkpoint") or (cp_ids[-1] if cp_ids else None)
    cp_tip = str(last_cp) if last_cp else "CP-0000"
    tip_n = _cp_num(cp_tip) or 0
    cp_range = f"CP-0001..{tip_n:04d}" if tip_n > 0 else "CP-0000..0000"

    ver = (
        _read_pyproject_version(base)
        or state.get("project_version")
        or "0.0.0"
    )
    resolved_cycle = cycle
    if resolved_cycle is None:
        resolved_cycle = _parse_cycle_from_docs(base, cp_tip)
    if resolved_cycle is None:
        resolved_cycle = tip_n

    ts = state.get("test_summary") or {}
    if pytest_summary is not None:
        passed = int(pytest_summary.get("passed", 0))
        failed = int(pytest_summary.get("failed", 0))
    else:
        passed = int(ts.get("passed", 0) or 0)
        failed = int(ts.get("failed", 0) or 0)

    debt_gates = _collect_debt_gates(base)
    slo_state = _slo_state_from_debt(base, debt_gates)

    resolved_node = node_id or state.get("node_id") or "local"
    resolved_tip = tip if tip is not None else _git_tip7(base)

    local = {
        "last_checkpoint": state.get("last_checkpoint"),
        "current_phase": state.get("current_phase"),
        "current_module": state.get("current_module"),
        "safety_status": state.get("safety_status"),
        "status": state.get("status"),
        "project_version": state.get("project_version"),
        "bounds": {
            "no_consensus_writes": True,
            "no_raft": True,
            "no_slo_chase": True,
            "no_tag_schema_change": True,
            "read_only": True,
        },
    }

    return StatusSnapshot(
        schema=SCHEMA_ID,
        node_id=str(resolved_node),
        cycle=int(resolved_cycle),
        ver=str(ver),
        tip=resolved_tip,
        cp_range=cp_range,
        cp_tip=cp_tip,
        pytest=PytestSummary(passed=passed, failed=failed),
        slo_state=slo_state,
        debt_gates=debt_gates,
        peers=_normalize_peers(peers),
        local=local,
    )


def snapshot_to_dict(snap: StatusSnapshot) -> dict[str, Any]:
    """Deterministic dict (alias ``schema``, sorted nested maps where needed)."""
    data = snap.model_dump(mode="json", by_alias=True)
    # Ensure slo_state keys sorted
    if isinstance(data.get("slo_state"), dict):
        data["slo_state"] = {k: data["slo_state"][k] for k in sorted(data["slo_state"])}
    # Peers already sorted by node_id; debt_gates already path-sorted.
    if isinstance(data.get("local"), dict) and isinstance(
        data["local"].get("bounds"), dict
    ):
        b = data["local"]["bounds"]
        data["local"]["bounds"] = {k: b[k] for k in sorted(b)}
    return data


def snapshot_to_json(snap: StatusSnapshot, *, indent: int | None = 2) -> str:
    """Stable JSON serialization with sorted object keys."""
    return json.dumps(snapshot_to_dict(snap), indent=indent, sort_keys=True) + (
        "\n" if indent is not None else ""
    )


def format_obs_m2m(snap: StatusSnapshot | Mapping[str, Any]) -> str:
    """Compact one-liner OBS field for council STATUS posts.

    Example::
        OBS: cycle=19 ver=0.15.0 cp=CP-0023 pytest=384/0 slo_floor=SCHEMA-GATED debt=CHECKPOINT_EVERY_FLOOR=SCHEMA-GATED
    """
    if isinstance(snap, StatusSnapshot):
        d = snapshot_to_dict(snap)
    else:
        d = dict(snap)
    pytest = d.get("pytest") or {}
    passed = pytest.get("passed", 0)
    failed = pytest.get("failed", 0)
    slo = d.get("slo_state") or {}
    floor = slo.get("checkpoint_every_floor", "UNKNOWN")
    debt_bits: list[str] = []
    for g in d.get("debt_gates") or []:
        debt_bits.append(f"{g.get('id')}={g.get('state')}")
    debt = ",".join(debt_bits) if debt_bits else "none"
    peers = d.get("peers") or []
    peer_n = len(peers)
    return (
        f"OBS: cycle={d.get('cycle')} ver={d.get('ver')} tip={d.get('tip') or 'null'} "
        f"cp={d.get('cp_tip')} cp_range={d.get('cp_range')} "
        f"pytest={passed}/{failed} slo_floor={floor} "
        f"slo_batch={slo.get('checkpoint_durable_batch', '?')} "
        f"slo_recovery={slo.get('recovery', '?')} "
        f"debt={debt} peers={peer_n}"
    )
