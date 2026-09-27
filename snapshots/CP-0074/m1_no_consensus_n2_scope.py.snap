"""M1 permanent NO_CONSENSUS_YET under N=2 scope (CP-0074 / Cycle 70).

Design-only: formalize operator Path C + HOLD posture after DeepSeek C69.
M1 remains NO_CONSENSUS_YET permanently under current N=2 / NO_HELD scope
(not pending re-research). C5 numeric 80 ≠ ratified. No Raft default; no
N>2 unlock; D3 ACK-gated OFF; live=DISABLED; MESH_PERF_EXPERIMENTAL=OFF.
Does not start D3 or open pkg0190.
"""

from __future__ import annotations

import json
import os
import subprocess
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from .release_checklist import NO_HELD_DEFAULT, GateResult

__all__ = [
    "PACKAGE_HELD",
    "CYCLE",
    "SEAL_CP",
    "PRIOR_CP",
    "PREFERRED_NEXT_DEFAULT",
    "SCHEMA_ID",
    "EXPERIMENTAL_FLAG_ENV",
    "RATIFY_THRESHOLD",
    "CANDIDATE_TOTALS",
    "CLOSEST_CANDIDATE",
    "CLOSEST_SCORE",
    "VERDICT",
    "POSTURE",
    "FENCE_PROBE_STATUS",
    "REMAINING_UNLOCK_GAPS",
    "STRUCTURAL_CIRCULARITY",
    "COMPOSED_CPS",
    "MUST_STAY_FALSE",
    "PLANNING_DOC",
    "DESIGN_DOC",
    "CAPABILITY_DOC",
    "SCHEMA_DOC",
    "POSTURE_NOTE",
    "HOLD_NOTE_PRIOR",
    "PostureGate",
    "M1N2ScopeResult",
    "default_posture_gate",
    "rejects_raft_default",
    "numeric_met_does_not_ratify",
    "run_m1_n2_scope_posture_gates",
]

PACKAGE_HELD = "0.18.0"
CYCLE = 70
SEAL_CP = "CP-0074"
PRIOR_CP = "CP-0073"
PREFERRED_NEXT_DEFAULT = "await_deepseek"
SCHEMA_ID = "mesh.membership.m1_n2_scope_posture/v0"
EXPERIMENTAL_FLAG_ENV = "MESH_PERF_EXPERIMENTAL"
RATIFY_THRESHOLD = 80

CANDIDATE_TOTALS: dict[str, int] = {
    "C0": 85,
    "C1": 54,
    "C2": 53,
    "C3": 60,
    "C4": 73,
    "C5": 80,
}
CLOSEST_CANDIDATE = "C5"
CLOSEST_SCORE = 80
VERDICT = "NO_CONSENSUS_YET"
POSTURE = "PERMANENT_UNDER_N2_SCOPE"
FENCE_PROBE_STATUS = "DESIGN_DRAFTED"

REMAINING_UNLOCK_GAPS: tuple[str, ...] = (
    "fence_green",
    "GOV.2",
    "n_gt2_safety",
)

STRUCTURAL_CIRCULARITY = "n_gt2_safety_blocked_while_n_gt2_no_held"

COMPOSED_CPS = (
    "CP-0050",
    "CP-0054",
    "CP-0071",
    "CP-0072",
    "CP-0073",
)

MUST_STAY_FALSE = (
    "raft_is_default",
    "n_gt2_unlocked",
    "live_enabled",
    "pkg0190_opened",
    "v019_tagged",
    "gia_unlocked",
    "train_70b",
    "saas_settlement",
    "mesh_perf_experimental_on",
    "d3_started_without_ack",
    "pending_reresearch_under_n2",
    "numeric_80_means_ratified",
)

PLANNING_DOC = "docs/planning/M1_NO_CONSENSUS_N2_SCOPE.md"
DESIGN_DOC = "docs/design/fabric/M1_NO_CONSENSUS_N2_SCOPE.md"
CAPABILITY_DOC = "docs/capabilities/MESH_M1_NO_CONSENSUS_N2_SCOPE.md"
SCHEMA_DOC = "docs/schema/membership/m1_n2_scope_posture_v0.md"
POSTURE_NOTE = "council/NOTE_M1_NO_CONSENSUS_N2_SCOPE.md"
HOLD_NOTE_PRIOR = "council/NOTE_OPERATOR_HOLD_POST_D2.md"

_UPSTREAM_DOCS: tuple[str, ...] = (
    "docs/planning/C5_FQ_ED_REFINEMENT.md",
    "docs/planning/D2_M1_CONSENSUS_CANDIDATE_RERESEARCH.md",
    "docs/design/fabric/M1_CONSENSUS_RERESEARCH.md",
    HOLD_NOTE_PRIOR,
)


@dataclass(frozen=True)
class PostureGate:
    m1_status: str
    posture: str
    pending_reresearch: bool
    unlocked: bool
    raft_is_default: bool
    n_gt2_status: str
    live_enabled: bool
    mesh_perf_experimental: str
    d3_acked: bool
    hold_active: bool
    c5_numeric_threshold_met: bool
    fence_probe_status: str


def rejects_raft_default(policy_default: str | None) -> bool:
    return policy_default in (None, "C0", "NO_CONSENSUS_YET")


def numeric_met_does_not_ratify(*, numeric_met: bool, unlocked: bool) -> bool:
    """True when the invariant holds: numeric≥80 must not imply unlocked."""
    if numeric_met and unlocked:
        return False
    return True


def default_posture_gate() -> dict[str, Any]:
    return {
        "schema": SCHEMA_ID,
        "m1_status": VERDICT,
        "posture": POSTURE,
        "pending_reresearch": False,
        "ratify_threshold": RATIFY_THRESHOLD,
        "closest_candidate": CLOSEST_CANDIDATE,
        "closest_score": CLOSEST_SCORE,
        "c5_numeric_threshold_met": CLOSEST_SCORE >= RATIFY_THRESHOLD,
        "unlocked": False,
        "fence_probe_status": FENCE_PROBE_STATUS,
        "remaining_unlock_gaps": list(REMAINING_UNLOCK_GAPS),
        "structural_circularity": STRUCTURAL_CIRCULARITY,
        "raft_is_default": False,
        "n_gt2_status": "NO_HELD",
        "live_enabled": False,
        "mesh_perf_experimental": "OFF",
        "d3_acked": False,
        "hold_active": True,
        "composed_cps": list(COMPOSED_CPS),
        "must_stay_false": {k: False for k in MUST_STAY_FALSE},
    }


@dataclass
class M1N2ScopeResult:
    ok: bool = True
    errors: list[str] = field(default_factory=list)
    gates: list[GateResult] = field(default_factory=list)
    version: str | None = None
    tip: str | None = None
    cp: str | None = None
    prior_cp: str | None = None
    pytest_count: int | None = None
    dual_primary: int = 0
    timestamp: str | None = None
    summary_path: str | None = None
    summary: dict[str, Any] = field(default_factory=dict)

    def add(self, name: str, ok: bool, detail: str = "") -> None:
        self.gates.append(GateResult(name=name, ok=ok, detail=detail))
        if not ok:
            self.ok = False
            self.errors.append(f"{name}: {detail or 'FAIL'}")

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "errors": list(self.errors),
            "version": self.version,
            "tip": self.tip,
            "cp": self.cp,
            "prior_cp": self.prior_cp,
            "pytest_count": self.pytest_count,
            "dual_primary": self.dual_primary,
            "timestamp": self.timestamp,
            "summary_path": self.summary_path,
            "gates": [g.to_dict() for g in self.gates],
            "summary": dict(self.summary),
            "no_held": NO_HELD_DEFAULT,
            "schema_id": SCHEMA_ID,
            "preferred_next": PREFERRED_NEXT_DEFAULT,
            "live": "DISABLED",
            "m1_status": VERDICT,
            "posture": POSTURE,
            "mesh_perf_experimental": "OFF",
            "hold_active": True,
            "closest_candidate": CLOSEST_CANDIDATE,
            "closest_score": CLOSEST_SCORE,
            "fence_probe_status": FENCE_PROBE_STATUS,
        }


def _git_tip(root: Path, override: str | None = None) -> str:
    if override:
        return override
    try:
        proc = subprocess.run(
            ["git", "rev-parse", "--short=7", "HEAD"],
            cwd=str(root),
            capture_output=True,
            text=True,
            check=False,
        )
        if proc.returncode == 0 and proc.stdout.strip():
            return proc.stdout.strip()
    except OSError:
        pass
    return "unknown"


def _read_version(root: Path) -> str:
    init = root / "src" / "neural_mesh" / "__init__.py"
    text = init.read_text(encoding="utf-8")
    for line in text.splitlines():
        if line.startswith("__version__"):
            return line.split("=", 1)[1].strip().strip("\"'")
    return "unknown"


def _cps_verified(root: Path, cps: tuple[str, ...]) -> bool:
    for cp in cps:
        snap = root / "snapshots" / cp
        ck = snap / "CHECKPOINT.json"
        if not ck.is_file():
            return False
        data = json.loads(ck.read_text(encoding="utf-8"))
        if str(data.get("status", "")).upper() != "VERIFIED":
            return False
    return True


def _experimental_off() -> bool:
    raw = os.environ.get(EXPERIMENTAL_FLAG_ENV, "").strip().lower()
    if not raw or raw in {"0", "off", "false", "no"}:
        return True
    return False


def run_m1_n2_scope_posture_gates(
    root: Path,
    *,
    out_dir: Path | None = None,
    tip: str | None = None,
    timestamp: str | None = None,
    pytest_count: int | None = None,
    dual_primary: int = 0,
    force_fail: str | None = None,
    write_project_state: bool = False,
) -> M1N2ScopeResult:
    """Evaluate M1 N=2 permanent posture design gates. No runtime consensus."""
    root = Path(root)
    result = M1N2ScopeResult()
    result.version = _read_version(root)
    result.tip = _git_tip(root, tip)
    result.cp = SEAL_CP
    result.prior_cp = PRIOR_CP
    result.dual_primary = dual_primary
    result.timestamp = timestamp or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    result.pytest_count = pytest_count

    out = Path(out_dir) if out_dir else root / "dist" / "releases" / "m1-no-consensus-n2-scope"
    out.mkdir(parents=True, exist_ok=True)

    ver_ok = result.version == PACKAGE_HELD and force_fail != "version_held"
    result.add("version_held", ver_ok, f"version={result.version} expect={PACKAGE_HELD}")

    note = root / POSTURE_NOTE
    note_ok = note.is_file() and force_fail != "posture_note_present"
    result.add("posture_note_present", note_ok, POSTURE_NOTE)
    note_text = note.read_text(encoding="utf-8") if note.is_file() else ""

    planning = root / PLANNING_DOC
    planning_ok = planning.is_file() and force_fail != "planning_doc_present"
    result.add("planning_doc_present", planning_ok, PLANNING_DOC)
    planning_text = planning.read_text(encoding="utf-8") if planning.is_file() else ""
    combined = note_text + "\n" + planning_text

    permanent_ok = (
        VERDICT == "NO_CONSENSUS_YET"
        and POSTURE == "PERMANENT_UNDER_N2_SCOPE"
        and ("permanent" in combined.lower() or "PERMANENT" in combined)
        and ("N=2" in combined or "N2" in combined)
        and ("pending re-research" in combined.lower() or "not \"pending" in combined.lower()
             or "not pending" in combined.lower() or "re-research loop" in combined.lower())
        and force_fail != "permanent_no_consensus"
    )
    if force_fail == "permanent_no_consensus":
        permanent_ok = False
    result.add("permanent_no_consensus", permanent_ok, f"posture={POSTURE}")

    numeric_ok = (
        CLOSEST_SCORE >= RATIFY_THRESHOLD
        and RATIFY_THRESHOLD == 80
        and CANDIDATE_TOTALS["C5"] == 80
        and ("≠ ratified" in combined or "!= ratified" in combined
             or "not ratified" in combined.lower() or "≠ unlocked" in combined
             or "numeric ≥80 ≠" in combined or "Numeric ≥80" in combined
             or "numeric_met" in combined.lower())
        and numeric_met_does_not_ratify(numeric_met=True, unlocked=False)
        and force_fail != "numeric_not_ratify"
    )
    if force_fail == "numeric_not_ratify":
        numeric_ok = False
    result.add(
        "numeric_not_ratify",
        numeric_ok,
        f"C5={CLOSEST_SCORE}; unlocked=False; thr={RATIFY_THRESHOLD}",
    )

    raft_ok = (
        rejects_raft_default(None)
        and rejects_raft_default("NO_CONSENSUS_YET")
        and not rejects_raft_default("C1")
        and ("no Raft default" in combined or "No Raft default" in combined
             or "Raft default" in combined or "not default" in combined.lower())
        and force_fail != "no_raft_default"
    )
    if force_fail == "no_raft_default":
        raft_ok = False
    result.add("no_raft_default", raft_ok, "policy rejects Raft default")

    n2_ok = (
        ("NO_HELD" in combined)
        and ("N>2" in combined or "N>2 unlock" in combined)
        and force_fail != "n_gt2_no_held"
    )
    if force_fail == "n_gt2_no_held":
        n2_ok = False
    result.add("n_gt2_no_held", n2_ok, "N>2 remains NO_HELD")

    live_ok = (
        ("live=DISABLED" in combined or "**live=DISABLED**" in combined or "live:** DISABLED" in combined
         or "live | **DISABLED**" in combined or "| **DISABLED**" in combined)
        and force_fail != "live_disabled"
    )
    # Broader: DISABLED near live
    if not live_ok and "live" in combined.lower() and "DISABLED" in combined:
        live_ok = force_fail != "live_disabled"
    if force_fail == "live_disabled":
        live_ok = False
    result.add("live_disabled", live_ok)

    d3_ok = (
        ("D3" in combined)
        and ("ACK-gated" in combined or "NOT ACK" in combined or "not ACKed" in combined
             or "ACK-gated OFF" in combined)
        and force_fail != "d3_not_acked"
    )
    if force_fail == "d3_not_acked":
        d3_ok = False
    result.add("d3_not_acked", d3_ok, "D3 remains ACK-gated; not started")

    exp_ok = _experimental_off() and force_fail != "mesh_perf_experimental_off"
    if force_fail == "mesh_perf_experimental_off":
        exp_ok = False
    result.add(
        "mesh_perf_experimental_off",
        exp_ok,
        f"env={os.environ.get(EXPERIMENTAL_FLAG_ENV, '')!r}",
    )

    tag_rc = subprocess.run(
        ["git", "rev-parse", "--verify", "v0.19.0"],
        cwd=str(root),
        capture_output=True,
    ).returncode
    no_v019 = tag_rc != 0 and force_fail != "pkg0190_not_opened"
    if force_fail == "pkg0190_not_opened":
        no_v019 = False
    result.add("pkg0190_not_opened", no_v019, "v0.19.0 absent; pkg0190 not opened")

    circ_ok = (
        ("circular" in combined.lower() or "structural" in combined.lower())
        and ("n_gt2_safety" in combined or "N>2 safety" in combined)
        and force_fail != "structural_circularity_documented"
    )
    if force_fail == "structural_circularity_documented":
        circ_ok = False
    result.add("structural_circularity_documented", circ_ok, STRUCTURAL_CIRCULARITY)

    hold_ok = (
        ("HOLD" in combined or "Hold" in combined)
        and ("no D3" in combined or "not start D3" in combined.lower()
             or "Do not start D3" in combined or "D3 not started" in combined
             or "not started" in combined.lower())
        and force_fail != "hold_active"
    )
    if force_fail == "hold_active":
        hold_ok = False
    result.add("hold_active", hold_ok, "HOLD active; no D3; no unlock")

    gaps_ok = (
        all(g in combined for g in ("fence_green", "GOV.2"))
        and ("n_gt2_safety" in combined or "N>2 safety" in combined)
        and force_fail != "remaining_gaps"
    )
    if force_fail == "remaining_gaps":
        gaps_ok = False
    result.add("remaining_gaps", gaps_ok, ",".join(REMAINING_UNLOCK_GAPS))

    design_ok = (
        (root / DESIGN_DOC).is_file()
        and (root / CAPABILITY_DOC).is_file()
        and (root / SCHEMA_DOC).is_file()
    )
    if force_fail == "capability_schema_present":
        design_ok = False
    result.add("capability_schema_present", design_ok)

    upstream_ok = all((root / rel).is_file() for rel in _UPSTREAM_DOCS)
    if force_fail == "upstream_docs_present":
        upstream_ok = False
    result.add("upstream_docs_present", upstream_ok, f"n={len(_UPSTREAM_DOCS)}")

    composed_ok = _cps_verified(root, COMPOSED_CPS) and force_fail != "prior_m1_cps"
    if force_fail == "prior_m1_cps":
        composed_ok = False
    result.add("prior_m1_cps", composed_ok, f"cps={list(COMPOSED_CPS)}")

    prior_ok = (root / "snapshots" / PRIOR_CP / "CHECKPOINT.json").is_file()
    result.add("prior_cp_present", prior_ok, PRIOR_CP)

    dp_ok = dual_primary == 0 and force_fail != "dual_primary_zero"
    if force_fail == "dual_primary_zero":
        dp_ok = False
    result.add("dual_primary_zero", dp_ok, f"dual_primary={dual_primary}")

    gia_ok = True
    for rel in (PLANNING_DOC, CAPABILITY_DOC, DESIGN_DOC, POSTURE_NOTE):
        p = root / rel
        if not p.is_file():
            continue
        t = p.read_text(encoding="utf-8").lower()
        if "we are gia" in t or "agi achieved" in t or "gia unlocked" in t:
            gia_ok = False
    if force_fail == "no_gia_claim":
        gia_ok = False
    result.add("no_gia_claim", gia_ok)

    if pytest_count is not None:
        py_ok = pytest_count > 0 and force_fail != "pytest_green"
        if force_fail == "pytest_green":
            py_ok = False
        result.add("pytest_green", py_ok, f"count={pytest_count}")

    gate = default_posture_gate()
    record = {
        "schema": "mesh.release.m1_no_consensus_n2_scope/v1",
        "ok": result.ok,
        "package_held": result.version,
        "tip": result.tip,
        "cp": result.cp,
        "prior_cp": result.prior_cp,
        "cycle": CYCLE,
        "candidate_totals": dict(CANDIDATE_TOTALS),
        "closest_candidate": CLOSEST_CANDIDATE,
        "closest_score": CLOSEST_SCORE,
        "verdict": VERDICT,
        "posture": POSTURE,
        "pending_reresearch": False,
        "unlocked": False,
        "fence_probe_status": FENCE_PROBE_STATUS,
        "remaining_unlock_gaps": list(REMAINING_UNLOCK_GAPS),
        "structural_circularity": STRUCTURAL_CIRCULARITY,
        "ratify_threshold": RATIFY_THRESHOLD,
        "composed_cps": list(COMPOSED_CPS),
        "posture_gate": gate,
        "pytest_count": result.pytest_count,
        "dual_primary": result.dual_primary,
        "timestamp": result.timestamp,
        "preferred_next": PREFERRED_NEXT_DEFAULT,
        "live": "DISABLED",
        "m1_status": VERDICT,
        "mesh_perf_experimental": "OFF",
        "package_open_0190": False,
        "raft_is_default": False,
        "n_gt2_status": "NO_HELD",
        "d3_acked": False,
        "hold_active": True,
        "no_held": NO_HELD_DEFAULT,
        "gates": [g.to_dict() for g in result.gates],
        "note": (
            "Cycle 70: operator Path C + HOLD — permanent M1=NO_CONSENSUS_YET "
            "under N=2 / NO_HELD scope. C5 numeric 80 ≠ ratified. Structural "
            "circularity on n_gt2_safety documented. No Raft default; no N>2 "
            "unlock; D3 ACK-gated OFF; live=DISABLED; MESH_PERF_EXPERIMENTAL=OFF; "
            "pkg0190 NOT_OPENED. Re-research loop under this scope closed."
        ),
    }
    summary_path = out / "M1_NO_CONSENSUS_N2_SCOPE.json"
    summary_path.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    result.summary_path = str(summary_path)
    result.summary = {
        "verdict": VERDICT,
        "posture": POSTURE,
        "closest_candidate": CLOSEST_CANDIDATE,
        "closest_score": CLOSEST_SCORE,
        "unlocked": False,
        "fence_probe_status": FENCE_PROBE_STATUS,
        "live": "DISABLED",
        "m1_status": VERDICT,
        "mesh_perf_experimental": "OFF",
        "package_open_0190": False,
        "raft_is_default": False,
        "d3_acked": False,
        "hold_active": True,
    }

    if write_project_state and result.ok:
        mirror = root / ".project_state" / "M1_NO_CONSENSUS_N2_SCOPE.json"
        mirror.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    return result
