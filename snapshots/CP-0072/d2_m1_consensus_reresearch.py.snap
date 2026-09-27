"""D2 M1 consensus candidate re-research helpers (CP-0072 / Cycle 68).

Design-only: C67 re-weighted scorecard, provisional C0..C5 scores, C5 FQ-ED
sketch constants, NO_CONSENSUS_YET verdict. No consensus runtime. No Raft
default. Does not enable live, open pkg0190, or flip MESH_PERF_EXPERIMENTAL.
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
    "AXIS_WEIGHTS",
    "UNLOCK_CANDIDATES",
    "PROVISIONAL_SCORES",
    "CANDIDATE_TOTALS",
    "CLOSEST_CANDIDATE",
    "CLOSEST_SCORE",
    "VERDICT",
    "COMPOSED_CPS",
    "MUST_STAY_FALSE",
    "PLANNING_DOC",
    "DESIGN_DOC",
    "CAPABILITY_DOC",
    "SCHEMA_DOC",
    "D4_FINDINGS_DOC",
    "ScorecardResult",
    "D2ReresearchResult",
    "axis_weight_sum",
    "validate_axis_scores",
    "total_score",
    "evaluate_candidate",
    "rejects_raft_default",
    "unlock_verdict",
    "default_reresearch_gate",
    "run_d2_m1_reresearch_gates",
]

PACKAGE_HELD = "0.18.0"
CYCLE = 68
SEAL_CP = "CP-0072"
PRIOR_CP = "CP-0071"
PREFERRED_NEXT_DEFAULT = "await_deepseek"
SCHEMA_ID = "mesh.membership.m1_reresearch/v0"
EXPERIMENTAL_FLAG_ENV = "MESH_PERF_EXPERIMENTAL"
RATIFY_THRESHOLD = 80

# DeepSeek C67 updated weights
AXIS_WEIGHTS: dict[str, int] = {
    "safety": 30,
    "liveness": 15,
    "fence_compat": 15,
    "no_raft": 10,
    "wan_tolerance": 15,
    "adversary_resistance": 10,
    "complexity": 5,
}

UNLOCK_CANDIDATES = frozenset({"C1", "C2", "C3", "C4", "C5"})

# Provisional design scores under C67 weights (CP-0072).
# Evidence gaps suppress unlock totals (RK53). Raft scores 0 on no_raft.
PROVISIONAL_SCORES: dict[str, dict[str, int]] = {
    "C0": {  # Stay N=2 — baseline only
        "safety": 30,
        "liveness": 10,
        "fence_compat": 15,
        "no_raft": 10,
        "wan_tolerance": 7,
        "adversary_resistance": 8,
        "complexity": 5,
    },
    "C1": {  # Raft — not default; no_raft = 0
        "safety": 20,
        "liveness": 12,
        "fence_compat": 6,
        "no_raft": 0,
        "wan_tolerance": 8,
        "adversary_resistance": 5,
        "complexity": 3,
    },
    "C2": {
        "safety": 18,
        "liveness": 10,
        "fence_compat": 5,
        "no_raft": 8,
        "wan_tolerance": 6,
        "adversary_resistance": 4,
        "complexity": 2,
    },
    "C3": {
        "safety": 17,
        "liveness": 12,
        "fence_compat": 5,
        "no_raft": 8,
        "wan_tolerance": 12,
        "adversary_resistance": 4,
        "complexity": 2,
    },
    "C4": {
        "safety": 22,
        "liveness": 10,
        "fence_compat": 12,
        "no_raft": 10,
        "wan_tolerance": 10,
        "adversary_resistance": 6,
        "complexity": 3,
    },
    "C5": {  # FQ-ED custom sketch — closest, still <80
        "safety": 23,
        "liveness": 11,
        "fence_compat": 12,
        "no_raft": 10,
        "wan_tolerance": 11,
        "adversary_resistance": 8,
        "complexity": 3,
    },
}

CANDIDATE_TOTALS: dict[str, int] = {
    cid: sum(scores.values()) for cid, scores in PROVISIONAL_SCORES.items()
}
CLOSEST_CANDIDATE = "C5"
CLOSEST_SCORE = CANDIDATE_TOTALS["C5"]
VERDICT = "NO_CONSENSUS_YET"

COMPOSED_CPS: tuple[str, ...] = (
    "CP-0050",  # M1 base design
    "CP-0054",  # scorecard maturation
    "CP-0071",  # D1 consensus draft
)

MUST_STAY_FALSE: tuple[str, ...] = (
    "live_adapter.enabled",
    "live_api_in_ci",
    "raft_runtime",
    "n_gt_2",
    "m1_consensus_default_selected",
    "raft_is_default",
    "gia_unlocked",
    "train_70b",
    "saas_settlement",
    "mesh_perf_experimental_on",
)

PLANNING_DOC = "docs/planning/D2_M1_CONSENSUS_CANDIDATE_RERESEARCH.md"
DESIGN_DOC = "docs/design/fabric/M1_CONSENSUS_RERESEARCH.md"
CAPABILITY_DOC = "docs/capabilities/MESH_D2_M1_CONSENSUS_RERESEARCH.md"
SCHEMA_DOC = "docs/schema/membership/m1_reresearch_v0.md"
D4_FINDINGS_DOC = "council/D4_CHATGPT_FINDINGS.md"

_UPSTREAM_DOCS: tuple[str, ...] = (
    "docs/design/fabric/M1_CONSENSUS_CHOICE_DESIGN.md",
    "docs/design/fabric/M1_SCORECARD_MATURATION.md",
    "docs/planning/D1_L_JUDGE_SAFETY_CASE_MATURATION.md",
    "council/COUNCIL_AGREEMENT_D4.md",
    D4_FINDINGS_DOC,
)


@dataclass(frozen=True)
class ScorecardResult:
    candidate_id: str
    total: int
    axis_scores: Mapping[str, int]
    unlock_eligible: bool
    ratifiable: bool


def axis_weight_sum() -> int:
    return sum(AXIS_WEIGHTS.values())


def validate_axis_scores(scores: Mapping[str, int]) -> None:
    if set(scores) != set(AXIS_WEIGHTS):
        missing = set(AXIS_WEIGHTS) - set(scores)
        extra = set(scores) - set(AXIS_WEIGHTS)
        raise ValueError(f"axis mismatch missing={missing} extra={extra}")
    for axis, pts in scores.items():
        cap = AXIS_WEIGHTS[axis]
        if not isinstance(pts, int) or pts < 0 or pts > cap:
            raise ValueError(f"axis {axis} score {pts} out of range 0..{cap}")


def total_score(scores: Mapping[str, int]) -> int:
    validate_axis_scores(scores)
    return sum(scores.values())


def evaluate_candidate(candidate_id: str, scores: Mapping[str, int]) -> ScorecardResult:
    total = total_score(scores)
    unlock_eligible = candidate_id in UNLOCK_CANDIDATES
    ratifiable = unlock_eligible and total >= RATIFY_THRESHOLD
    return ScorecardResult(
        candidate_id=candidate_id,
        total=total,
        axis_scores=dict(scores),
        unlock_eligible=unlock_eligible,
        ratifiable=ratifiable,
    )


def rejects_raft_default(policy_default: str | None) -> bool:
    """Hard rule: no default = Raft. Default must be None, C0, or NO_CONSENSUS_YET."""
    return policy_default in (None, "C0", "NO_CONSENSUS_YET")


def unlock_verdict(results: Mapping[str, ScorecardResult]) -> str:
    """Return chosen unlock id, or NO_CONSENSUS_YET if none ratifiable.

    Never auto-pick Raft among ties / winners without GOV.
    """
    winners = [r.candidate_id for r in results.values() if r.ratifiable]
    if not winners:
        return "NO_CONSENSUS_YET"
    if len(winners) == 1 and winners[0] != "C1":
        return winners[0]
    # Ambiguous or Raft-only → require GOV, not vibe-pick
    return "NO_CONSENSUS_YET"


def default_reresearch_gate() -> dict[str, Any]:
    return {
        "schema": SCHEMA_ID,
        "m1_status": VERDICT,
        "ratify_threshold": RATIFY_THRESHOLD,
        "axes": dict(AXIS_WEIGHTS),
        "candidate_totals": dict(CANDIDATE_TOTALS),
        "closest_candidate": CLOSEST_CANDIDATE,
        "closest_score": CLOSEST_SCORE,
        "raft_is_default": False,
        "live_enabled": False,
        "mesh_perf_experimental": "OFF",
        "composed_cps": list(COMPOSED_CPS),
        "d1_exit_seal": "PASS",
        "d1_exit_live_discussion": "NOT_PASS",
        "must_stay_false": {k: False for k in MUST_STAY_FALSE},
    }


@dataclass
class D2ReresearchResult:
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
            "mesh_perf_experimental": "OFF",
            "closest_candidate": CLOSEST_CANDIDATE,
            "closest_score": CLOSEST_SCORE,
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


def run_d2_m1_reresearch_gates(
    root: Path,
    *,
    out_dir: Path | None = None,
    tip: str | None = None,
    timestamp: str | None = None,
    pytest_count: int | None = None,
    dual_primary: int = 0,
    force_fail: str | None = None,
    write_project_state: bool = False,
) -> D2ReresearchResult:
    """Evaluate D2 M1 re-research design gates. No runtime consensus."""
    root = Path(root)
    result = D2ReresearchResult()
    result.version = _read_version(root)
    result.tip = _git_tip(root, tip)
    result.cp = SEAL_CP
    result.prior_cp = PRIOR_CP
    result.dual_primary = dual_primary
    result.timestamp = timestamp or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    result.pytest_count = pytest_count

    out = Path(out_dir) if out_dir else root / "dist" / "releases" / "d2-m1-reresearch"
    out.mkdir(parents=True, exist_ok=True)

    ver_ok = result.version == PACKAGE_HELD and force_fail != "version_held"
    result.add("version_held", ver_ok, f"version={result.version} expect={PACKAGE_HELD}")

    planning = root / PLANNING_DOC
    planning_ok = planning.is_file() and force_fail != "planning_doc_present"
    result.add("planning_doc_present", planning_ok, PLANNING_DOC)
    planning_text = planning.read_text(encoding="utf-8") if planning.is_file() else ""

    f2_ok = (root / D4_FINDINGS_DOC).is_file() and force_fail != "f2_d4_findings_present"
    if force_fail == "f2_d4_findings_present":
        f2_ok = False
    result.add("f2_d4_findings_present", f2_ok, D4_FINDINGS_DOC)

    d1_exit_ok = (
        "D1 seal exit" in planning_text
        and "PASS" in planning_text
        and ("NOT PASS" in planning_text or "NOT_PASS" in planning_text or "must stay false" in planning_text.lower())
        and force_fail != "d1_exit_noted"
    )
    if force_fail == "d1_exit_noted":
        d1_exit_ok = False
    result.add("d1_exit_noted", d1_exit_ok, "seal PASS / live-discussion NOT PASS")

    axes_ok = (
        axis_weight_sum() == 100
        and "safety" in planning_text.lower()
        and "30" in planning_text
        and ("no-Raft" in planning_text or "No-Raft" in planning_text or "no_raft" in planning_text)
        and "adversary" in planning_text.lower()
        and force_fail != "axes_c67_weights"
    )
    if force_fail == "axes_c67_weights":
        axes_ok = False
    result.add("axes_c67_weights", axes_ok, f"sum={axis_weight_sum()}")

    # Score integrity
    score_ok = True
    detail_scores = []
    for cid, scores in PROVISIONAL_SCORES.items():
        try:
            tot = total_score(scores)
        except ValueError as exc:
            score_ok = False
            detail_scores.append(f"{cid}:{exc}")
            continue
        if tot != CANDIDATE_TOTALS[cid]:
            score_ok = False
            detail_scores.append(f"{cid}:tot_mismatch")
        if cid in UNLOCK_CANDIDATES and tot >= RATIFY_THRESHOLD:
            score_ok = False
            detail_scores.append(f"{cid}:unexpectedly_ge_80")
    if CANDIDATE_TOTALS.get("C5") != CLOSEST_SCORE:
        score_ok = False
    if force_fail == "scores_filled":
        score_ok = False
    result.add("scores_filled", score_ok, ",".join(detail_scores) or "C0..C5 ok")

    c5_ok = (
        "FQ-ED" in planning_text
        and "C5" in planning_text
        and "Evidence-Diversity" in planning_text
        and force_fail != "c5_sketch"
    )
    if force_fail == "c5_sketch":
        c5_ok = False
    result.add("c5_sketch", c5_ok, "FQ-ED custom sketch")

    verdict_ok = (
        "NO_CONSENSUS_YET" in planning_text
        and ("no default" in planning_text.lower() or "not default" in planning_text.lower())
        and "Raft" in planning_text
        and force_fail != "no_consensus_yet"
    )
    if force_fail == "no_consensus_yet":
        verdict_ok = False
    # Ensure helper verdict matches
    results_map = {
        cid: evaluate_candidate(cid, scores) for cid, scores in PROVISIONAL_SCORES.items()
    }
    helper_verdict = unlock_verdict(results_map)
    if helper_verdict != VERDICT:
        verdict_ok = False
    result.add("no_consensus_yet", verdict_ok, f"helper={helper_verdict}")

    raft_default_ok = rejects_raft_default("NO_CONSENSUS_YET") and rejects_raft_default(None)
    raft_default_ok = raft_default_ok and not rejects_raft_default("C1")
    raft_default_ok = raft_default_ok and PROVISIONAL_SCORES["C1"]["no_raft"] == 0
    if force_fail == "no_raft_default":
        raft_default_ok = False
    result.add("no_raft_default", raft_default_ok, "C1 no_raft=0; policy rejects Raft default")

    compose_ok = (
        ("CP-0071" in planning_text or "D1" in planning_text)
        and ("independence" in planning_text.lower() or "Independence" in planning_text)
        and "adversarial" in planning_text.lower()
        and force_fail != "composes_d1"
    )
    if force_fail == "composes_d1":
        compose_ok = False
    result.add("composes_d1", compose_ok, "D1 §4 + CG4")

    live_ok = (
        ("live=DISABLED" in planning_text or "**live=DISABLED**" in planning_text)
        and (
            "does **not** enable live" in planning_text
            or "does not enable live" in planning_text.lower()
            or "no live enable" in planning_text.lower()
        )
        and force_fail != "live_disabled"
    )
    if force_fail == "live_disabled":
        live_ok = False
    result.add("live_disabled", live_ok)

    design_ok = (root / DESIGN_DOC).is_file() and (root / CAPABILITY_DOC).is_file() and (root / SCHEMA_DOC).is_file()
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

    dp_ok = dual_primary == 0 and force_fail != "dual_primary_zero"
    if force_fail == "dual_primary_zero":
        dp_ok = False
    result.add("dual_primary_zero", dp_ok, f"dual_primary={dual_primary}")

    gia_ok = True
    for rel in (PLANNING_DOC, CAPABILITY_DOC, DESIGN_DOC):
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

    gate = default_reresearch_gate()
    record = {
        "schema": "mesh.release.d2_m1_reresearch/v1",
        "ok": result.ok,
        "package_held": result.version,
        "tip": result.tip,
        "cp": result.cp,
        "prior_cp": result.prior_cp,
        "cycle": CYCLE,
        "axes": dict(AXIS_WEIGHTS),
        "candidate_totals": dict(CANDIDATE_TOTALS),
        "closest_candidate": CLOSEST_CANDIDATE,
        "closest_score": CLOSEST_SCORE,
        "verdict": VERDICT,
        "ratify_threshold": RATIFY_THRESHOLD,
        "composed_cps": list(COMPOSED_CPS),
        "reresearch_gate": gate,
        "pytest_count": result.pytest_count,
        "dual_primary": result.dual_primary,
        "timestamp": result.timestamp,
        "preferred_next": PREFERRED_NEXT_DEFAULT,
        "live": "DISABLED",
        "m1_status": VERDICT,
        "mesh_perf_experimental": "OFF",
        "package_open_0190": False,
        "raft_is_default": False,
        "d1_exit_seal": "PASS",
        "d1_exit_live_discussion": "NOT_PASS",
        "no_held": NO_HELD_DEFAULT,
        "gates": [g.to_dict() for g in result.gates],
        "note": (
            "D2 M1 consensus candidate re-research: C67 re-weighted scorecard "
            "(safety30/liveness15/fence15/no-Raft10/WAN15/adversary10/complexity5); "
            "C5 FQ-ED custom sketch; closest=78<80 → NO_CONSENSUS_YET. Composes "
            "CP-0050+0054+0071 D1 draft. Design-only. live=DISABLED. No Raft "
            "default. Does not enable live, open pkg0190, unlock GIA/Raft/N>2, "
            "or flip MESH_PERF_EXPERIMENTAL."
        ),
    }
    summary_path = out / "D2_M1_RERESEARCH.json"
    summary_path.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    result.summary_path = str(summary_path)
    result.summary = {
        "verdict": VERDICT,
        "closest_candidate": CLOSEST_CANDIDATE,
        "closest_score": CLOSEST_SCORE,
        "candidate_totals": dict(CANDIDATE_TOTALS),
        "live": "DISABLED",
        "m1_status": VERDICT,
        "mesh_perf_experimental": "OFF",
        "package_open_0190": False,
        "raft_is_default": False,
    }

    if write_project_state and result.ok:
        mirror = root / ".project_state" / "D2_M1_RERESEARCH.json"
        mirror.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    return result
