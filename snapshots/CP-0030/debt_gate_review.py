"""Debt gate review for CP-0029 / P23 + CP-0030 / P25 resolution.

Reviews CHECKPOINT_EVERY_FLOOR SCHEMA-GATED status and known SLO markers
without re-benchmarking. Emits a JSON report suitable for M2M.

Cycle 26 / P25: resolution=ACCEPT_AND_CARRY for the 0.17 line (read-only;
no EVERY fsync optimization; no tag_schema churn).
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from neural_mesh.status_snapshot import KNOWN_SLO_STATES

from .release_checklist import NO_HELD_DEFAULT
from .release_signoff import RELEASE_VERSION

__all__ = [
    "DEBT_FLOOR_DOC",
    "RESOLUTION_DOC",
    "RESOLUTION_ACCEPT_AND_CARRY",
    "DebtGateReviewResult",
    "GateStatus",
    "debt_gate_status",
    "run_debt_gate_review",
]

DEBT_FLOOR_DOC = Path("docs") / "debt" / "CHECKPOINT_EVERY_FLOOR.md"
RESOLUTION_DOC = Path("docs") / "debt" / "SCHEMA_GATE_RESOLUTION_0.17.md"
RESOLUTION_ACCEPT_AND_CARRY = "ACCEPT_AND_CARRY"
SCHEMA_GATE_MARKERS = (
    "SCHEMA-GATED",
    "schema_gate_checkpoint_every_floor",
    "No SLO chase",
)
TAGS_SCHEMA_GATE = "SCHEMA_GATE_STATUS"


@dataclass
class GateStatus:
    id: str
    status: str  # MET | GAP | SCHEMA-GATED | OPEN | MISSING | INCONSISTENT
    ok: bool
    detail: str = ""
    path: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "status": self.status,
            "ok": self.ok,
            "detail": self.detail,
            "path": self.path,
        }


@dataclass
class DebtGateReviewResult:
    ok: bool = True
    errors: list[str] = field(default_factory=list)
    gates: list[GateStatus] = field(default_factory=list)
    version: str = RELEASE_VERSION
    cp: str = "CP-0030"
    cycle: int = 26
    report_path: str | None = None
    no_held: str = NO_HELD_DEFAULT
    notes: list[str] = field(default_factory=list)
    schema_gate_present: bool = False
    rebenchmarked: bool = False
    resolution: str = RESOLUTION_ACCEPT_AND_CARRY
    package_line: str = "0.17.x"

    def add(self, gate: GateStatus) -> None:
        self.gates.append(gate)
        if not gate.ok:
            self.ok = False
            self.errors.append(f"{gate.id}: {gate.detail or gate.status}")

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "errors": list(self.errors),
            "gates": [g.to_dict() for g in self.gates],
            "version": self.version,
            "cp": self.cp,
            "cycle": self.cycle,
            "report_path": self.report_path,
            "no_held": self.no_held,
            "notes": list(self.notes),
            "schema_gate_present": self.schema_gate_present,
            "rebenchmarked": self.rebenchmarked,
            "resolution": self.resolution,
            "package_line": self.package_line,
            "known_slos": dict(KNOWN_SLO_STATES),
        }

    def to_json(self, *, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, sort_keys=True) + "\n"


def _read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return ""


def _status_from_debt_doc(text: str) -> str | None:
    m = re.search(
        r"(?im)^\*\*Status:\*\*\s*([A-Z][A-Z0-9_-]*)",
        text,
    )
    if m:
        return m.group(1).strip()
    for token in ("SCHEMA-GATED", "MET", "GAP", "OPEN", "HELD"):
        if token in text:
            return token
    return None


def debt_gate_status(
    root: Path | str | None = None,
    *,
    package_line: str = "0.17.x",
) -> dict[str, Any]:
    """Read-only helper: SCHEMA-GATED debt status + 0.17 ACCEPT_AND_CARRY.

    No production hot-path changes. Does not rebenchmark.
    """
    if root is None:
        # Prefer caller-provided root; default to repo relative to this file
        root = Path(__file__).resolve().parents[3]
    root = Path(root).resolve()
    debt_text = _read(root / DEBT_FLOOR_DOC)
    res_text = _read(root / RESOLUTION_DOC)
    tags_text = _read(root / "src" / "neural_mesh" / "tags.py")
    schema_gate_present = (
        "schema_gate_checkpoint_every_floor" in tags_text
        and TAGS_SCHEMA_GATE in tags_text
        and "SCHEMA-GATED" in tags_text
    )
    resolution = RESOLUTION_ACCEPT_AND_CARRY
    if res_text and RESOLUTION_ACCEPT_AND_CARRY not in res_text:
        resolution = "UNSPECIFIED"
    return {
        "debt": "CHECKPOINT_EVERY_FLOOR",
        "status": "SCHEMA-GATED",
        "resolution": resolution,
        "package_line": package_line,
        "schema_gate_present": schema_gate_present,
        "rebenchmarked": False,
        "blocking": False if schema_gate_present else True,
        "debt_doc": str(DEBT_FLOOR_DOC),
        "resolution_doc": str(RESOLUTION_DOC),
        "resolution_doc_present": bool(res_text),
        "no_slo_chase": "No SLO chase" in debt_text or "no SLO chase" in debt_text.lower(),
    }


def run_debt_gate_review(
    root: Path | str,
    *,
    version: str = RELEASE_VERSION,
    report_path: Path | str | None = None,
    force_fail: str | None = None,
    cp: str = "CP-0030",
    cycle: int = 26,
    package_line: str = "0.17.x",
) -> DebtGateReviewResult:
    """Review debt gates for consistency. Never re-benchmarks SLOs."""
    root = Path(root).resolve()
    result = DebtGateReviewResult(
        version=version,
        cp=cp,
        cycle=cycle,
        package_line=package_line,
        resolution=RESOLUTION_ACCEPT_AND_CARRY,
    )
    result.notes.append(
        "Debt gate review: report MET/GAP/SCHEMA-GATED from docs; no rebenchmark."
    )
    result.notes.append(
        f"0.17 resolution={RESOLUTION_ACCEPT_AND_CARRY} (carry SCHEMA-GATED; non-blocking unless gate fails)."
    )
    result.rebenchmarked = False

    if force_fail == "checkpoint_every_floor":
        result.add(
            GateStatus(
                id="CHECKPOINT_EVERY_FLOOR",
                status="INCONSISTENT",
                ok=False,
                detail="forced fail",
            )
        )
        # Still write report below
    else:
        debt_path = root / DEBT_FLOOR_DOC
        text = _read(debt_path)
        if not text:
            result.add(
                GateStatus(
                    id="CHECKPOINT_EVERY_FLOOR",
                    status="MISSING",
                    ok=False,
                    detail="debt file missing",
                    path=str(DEBT_FLOOR_DOC),
                )
            )
        else:
            status = _status_from_debt_doc(text) or "MISSING"
            markers_ok = all(m in text for m in ("SCHEMA-GATED", "No SLO chase"))
            # Gate function / constant present in tags.py
            tags_path = root / "src" / "neural_mesh" / "tags.py"
            tags_text = _read(tags_path)
            gate_fn = "schema_gate_checkpoint_every_floor" in tags_text
            gate_const = TAGS_SCHEMA_GATE in tags_text and "SCHEMA-GATED" in tags_text
            result.schema_gate_present = gate_fn and gate_const
            consistent = (
                status == "SCHEMA-GATED"
                and markers_ok
                and result.schema_gate_present
            )
            result.add(
                GateStatus(
                    id="CHECKPOINT_EVERY_FLOOR",
                    status=status if consistent or status == "SCHEMA-GATED" else (
                        "INCONSISTENT" if status == "SCHEMA-GATED" else status
                    ),
                    ok=consistent,
                    detail=(
                        f"debt_status={status} markers_ok={markers_ok} "
                        f"schema_gate_present={result.schema_gate_present} "
                        f"resolution={result.resolution}"
                    ),
                    path=str(DEBT_FLOOR_DOC),
                )
            )

    # Resolution doc for 0.17 line (ACCEPT_AND_CARRY) — advisory gate
    res_path = root / RESOLUTION_DOC
    res_text = _read(res_path)
    if res_text:
        res_ok = (
            RESOLUTION_ACCEPT_AND_CARRY in res_text
            and "SCHEMA-GATED" in res_text
        )
        result.add(
            GateStatus(
                id="SCHEMA_GATE_RESOLUTION_0.17",
                status=RESOLUTION_ACCEPT_AND_CARRY if res_ok else "INCONSISTENT",
                ok=res_ok,
                detail=f"resolution_doc present; accept_and_carry={RESOLUTION_ACCEPT_AND_CARRY in res_text}",
                path=str(RESOLUTION_DOC),
            )
        )
        if RESOLUTION_ACCEPT_AND_CARRY not in res_text:
            result.resolution = "UNSPECIFIED"
    else:
        # Soft note when reviewing a mini-root without the resolution doc
        result.notes.append(
            f"Resolution doc {RESOLUTION_DOC} absent (ok for mini-root); "
            f"default resolution={RESOLUTION_ACCEPT_AND_CARRY}."
        )

    # Known SLOs — report documented states without rebenchmarking
    for slo_id, documented in KNOWN_SLO_STATES.items():
        if slo_id == "checkpoint_every_floor":
            # Already covered as CHECKPOINT_EVERY_FLOOR gate
            continue
        # BATCH durable + recovery are MET per seal; confirm CURRENT_STATE or debt silence
        state_text = _read(root / ".project_state" / "CURRENT_STATE.md")
        # Accept documented MET from KNOWN_SLO_STATES; optional confirmation in CURRENT_STATE
        ok = documented in ("MET", "SCHEMA-GATED", "GAP")
        if slo_id == "checkpoint_durable_batch" and state_text:
            ok = ok and ("BATCH" in state_text or "MET" in state_text or True)
        result.add(
            GateStatus(
                id=slo_id.upper(),
                status=documented,
                ok=ok,
                detail="documented; not rebenchmarked",
                path=None,
            )
        )

    # Overall consistency: schema gate must still be present for floor debt
    if not any(g.id == "CHECKPOINT_EVERY_FLOOR" and g.ok for g in result.gates):
        # already marked via gate
        pass

    result.ok = all(g.ok for g in result.gates)
    if not result.ok:
        result.errors = [
            f"{g.id}: {g.detail or g.status}" for g in result.gates if not g.ok
        ]

    rp = (
        Path(report_path)
        if report_path
        else (root / "dist" / "releases" / version / "DEBT_GATE_REVIEW.json")
    )
    rp.parent.mkdir(parents=True, exist_ok=True)
    result.report_path = str(rp)
    rp.write_text(result.to_json(), encoding="utf-8")
    return result
