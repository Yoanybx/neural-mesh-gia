"""D1 L_judge safety-case maturation helpers (CP-0071 / Cycle 67).

Design-only: encode D4-A..K citation gates, authority matrix constants,
rollback verification IDs, and must-stay-false (live=DISABLED). No network.
No live codec. Does not enable live, open pkg0190, or select M1 consensus.
"""

from __future__ import annotations

import json
import os
import subprocess
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .release_checklist import NO_HELD_DEFAULT, GateResult
from .l_judge_live_adapter_safety import RefuseTransport

__all__ = [
    "PACKAGE_HELD",
    "CYCLE",
    "SEAL_CP",
    "PRIOR_CP",
    "PREFERRED_NEXT_DEFAULT",
    "SCHEMA_ID",
    "EXPERIMENTAL_FLAG_ENV",
    "D4_DEBT_IDS",
    "COMPOSED_CPS",
    "ROLLBACK_VERIFICATION_IDS",
    "AUTHORITY_MATRIX",
    "MUST_STAY_FALSE",
    "PLANNING_DOC",
    "CAPABILITY_DOC",
    "SCHEMA_DOC",
    "D1MaturationResult",
    "authority_matrix_as_rows",
    "default_maturation_gate",
    "run_d1_safety_maturation_gates",
    "mock_rv_verification_drill",
    "mock_i5_kill_to_refuse_drill",
]

PACKAGE_HELD = "0.18.0"
CYCLE = 67
SEAL_CP = "CP-0071"
PRIOR_CP = "CP-0070"
PREFERRED_NEXT_DEFAULT = "await_deepseek"
SCHEMA_ID = "mesh.judge.d1_safety_maturation/v0"
EXPERIMENTAL_FLAG_ENV = "MESH_PERF_EXPERIMENTAL"

D4_DEBT_IDS: tuple[str, ...] = (
    "D4-A",
    "D4-B",
    "D4-C",
    "D4-D",
    "D4-E",
    "D4-F",
    "D4-G",
    "D4-H",
    "D4-I",
    "D4-J",
    "D4-K",
)

COMPOSED_CPS: tuple[str, ...] = (
    "CP-0058",  # L_judge live-adapter safety case
    "CP-0068",  # continuity
    "CP-0069",  # oversight I5
)

ROLLBACK_VERIFICATION_IDS: tuple[str, ...] = tuple(f"RV-{i}" for i in range(1, 8))

# Component -> (propose, approve, veto, execute)
AUTHORITY_MATRIX: dict[str, tuple[bool, bool, bool, bool]] = {
    "L_judge": (True, False, False, False),
    "Oversight_I5": (True, True, True, False),
    "Continuity": (False, False, True, False),
    "Operator": (True, True, True, True),
    "OrchestratorRouter": (True, False, True, False),
    "RefuseTransport": (False, False, True, False),
}

MUST_STAY_FALSE: tuple[str, ...] = (
    "live_adapter.enabled",
    "live_api_in_ci",
    "src_live_codec_shipped",
    "d1_exit_ready_for_live",
    "mesh_is_frontier_model",
    "train_70b",
    "gia_unlocked",
    "raft_runtime",
    "n_gt_2",
    "saas_settlement",
    "m1_consensus_default_selected",
)

PLANNING_DOC = "docs/planning/D1_L_JUDGE_SAFETY_CASE_MATURATION.md"
CAPABILITY_DOC = "docs/capabilities/MESH_D1_L_JUDGE_SAFETY_CASE_MATURATION.md"
SCHEMA_DOC = "docs/schema/judge/d1_safety_maturation_v0.md"

_UPSTREAM_DOCS: tuple[str, ...] = (
    "docs/design/L_JUDGE_LIVE_ADAPTER_SAFETY_CASE.md",
    "docs/design/ORCHESTRATOR_CONTINUITY_DESIGN.md",
    "docs/design/ORCHESTRATOR_OVERSIGHT_HOOKS_DESIGN.md",
    "council/COUNCIL_AGREEMENT_D4.md",
    "council/D4_CHATGPT_FINDINGS.md",
)


def authority_matrix_as_rows() -> list[dict[str, Any]]:
    rows = []
    for name, (propose, approve, veto, execute) in AUTHORITY_MATRIX.items():
        rows.append(
            {
                "component": name,
                "propose": propose,
                "approve": approve,
                "veto": veto,
                "execute": execute,
            }
        )
    return rows


def default_maturation_gate() -> dict[str, Any]:
    return {
        "schema": SCHEMA_ID,
        "live_enabled": False,
        "m1_status": "NO_CONSENSUS_YET",
        "d4_debt_ids": list(D4_DEBT_IDS),
        "authority_matrix_frozen": True,
        "continuity_verified_state_only": True,
        "oversight_bounds_documented": True,
        "rollback_verification_ids": list(ROLLBACK_VERIFICATION_IDS),
        "policy_version_required": True,
        "audit_completeness_required": True,
        "d1_exit_ready_for_live": False,
        "mesh_perf_experimental": "OFF",
        "composed_cps": list(COMPOSED_CPS),
        "must_stay_false": {k: False for k in MUST_STAY_FALSE},
    }


def mock_rv_verification_drill() -> dict[str, Any]:
    """Mock-only RV-1..RV-7 green report (Hold cycle 5).

    Does **not** prove live transport, arm a canary, flip live flags, or mint
    keys. Scope remains mock/local under live=DISABLED.
    """
    results: dict[str, dict[str, Any]] = {}
    for rv in ROLLBACK_VERIFICATION_IDS:
        results[rv] = {
            "ok": True,
            "scope": "mock",
            "live_proof": False,
            "detail": f"{rv} mock-green under RefuseTransport / live=DISABLED",
        }
    return {
        "schema": "mesh.judge.mock_rv_drill/v0",
        "drill": "RV_1_TO_7",
        "ok": all(v["ok"] for v in results.values()),
        "live_armed": False,
        "canary_armed": False,
        "live_proof": False,
        "live_adapter.enabled": False,
        "LIVE_API_ENABLED": False,
        "dual_primary": 0,
        "rollback_verification_ids": list(ROLLBACK_VERIFICATION_IDS),
        "results": results,
        "note": (
            "Mock RV drill only. Gate2 / live RV evidence still OPEN; "
            "Gate1 UNSIGNED → cannot seal."
        ),
    }


def mock_i5_kill_to_refuse_drill() -> dict[str, Any]:
    """Mock-only I5 kill → RefuseTransport + continuity ABORT (Hold cycle 5).

    Simulates the design kill chain under live=DISABLED. Does **not** arm a
    live canary, flip enablement flags true, or perform network I/O.
    """
    # I5 may approve/veto/kill but cannot execute (matrix row).
    i5 = AUTHORITY_MATRIX["Oversight_I5"]
    if i5 != (True, True, True, False):
        raise RuntimeError("Oversight_I5 matrix drift; refuse mock kill drill")

    rt = RefuseTransport()
    health = rt.health()
    refused = rt.call({"reason": "mock_i5_kill"})
    return {
        "schema": "mesh.judge.mock_i5_kill_drill/v0",
        "drill": "I5_KILL_TO_REFUSE",
        "ok": True,
        "live_armed": False,
        "canary_armed": False,
        "kill_authority": "Oversight_I5",
        "i5_can_execute": False,
        "abort_code": "HUMAN_ABORT",
        "continuity": "ABORT",
        "binding": health.get("binding"),
        "live": bool(health.get("live")),
        "live_adapter.enabled": False,
        "LIVE_API_ENABLED": False,
        "refuse_call": refused,
        "health": health,
        "mesh_accept": False,
        "emergency_enabled_false": True,
        "note": (
            "Mock I5→Refuse drill only. Does not arm Gate5 canary; "
            "live track remains FROZEN under OPERATOR HOLD (A)."
        ),
    }


@dataclass
class D1MaturationResult:
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
            "m1_status": "NO_CONSENSUS_YET",
            "mesh_perf_experimental": "OFF",
            "d4_debt_ids": list(D4_DEBT_IDS),
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


def run_d1_safety_maturation_gates(
    root: Path,
    *,
    out_dir: Path | None = None,
    tip: str | None = None,
    timestamp: str | None = None,
    pytest_count: int | None = None,
    dual_primary: int = 0,
    force_fail: str | None = None,
    write_project_state: bool = False,
) -> D1MaturationResult:
    """Evaluate D1 maturation design gates (docs + fences). No live enablement."""
    root = Path(root)
    result = D1MaturationResult()
    result.version = _read_version(root)
    result.tip = _git_tip(root, tip)
    result.cp = SEAL_CP
    result.prior_cp = PRIOR_CP
    result.dual_primary = dual_primary
    result.timestamp = timestamp or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    result.pytest_count = pytest_count

    out = Path(out_dir) if out_dir else root / "dist" / "releases" / "d1-safety-maturation"
    out.mkdir(parents=True, exist_ok=True)

    ver_ok = result.version == PACKAGE_HELD and force_fail != "version_held"
    result.add("version_held", ver_ok, f"version={result.version} expect={PACKAGE_HELD}")

    planning = root / PLANNING_DOC
    planning_ok = planning.is_file() and force_fail != "planning_doc_present"
    result.add("planning_doc_present", planning_ok, PLANNING_DOC)

    planning_text = planning.read_text(encoding="utf-8") if planning.is_file() else ""

    missing_ids = [d for d in D4_DEBT_IDS if d not in planning_text]
    d4_ok = not missing_ids and force_fail != "d4_ids_cited"
    if force_fail == "d4_ids_cited":
        d4_ok = False
    result.add("d4_ids_cited", d4_ok, f"missing={missing_ids}")

    matrix_ok = (
        "Authority Matrix" in planning_text
        and "Can propose" in planning_text
        and "L_judge" in planning_text
        and force_fail != "authority_matrix"
    )
    if force_fail == "authority_matrix":
        matrix_ok = False
    result.add("authority_matrix", matrix_ok, "D4-A")

    consensus_ok = (
        "NO_CONSENSUS_YET" in planning_text
        and ("independence" in planning_text.lower() or "Independence" in planning_text)
        and "adversarial" in planning_text.lower()
        and force_fail != "consensus_draft_no_default"
    )
    if force_fail == "consensus_draft_no_default":
        consensus_ok = False
    result.add("consensus_draft_no_default", consensus_ok, "D4-B M1=NO_CONSENSUS_YET")

    cont_ok = (
        "verified" in planning_text.lower()
        and "Continuity limits" in planning_text
        and force_fail != "continuity_limits"
    )
    if force_fail == "continuity_limits":
        cont_ok = False
    result.add("continuity_limits", cont_ok, "D4-C")

    ovs_ok = (
        "Oversight I5" in planning_text
        and "deadman" in planning_text.lower()
        and ("conflict" in planning_text.lower() or "CoI" in planning_text)
        and force_fail != "oversight_bounds"
    )
    if force_fail == "oversight_bounds":
        ovs_ok = False
    result.add("oversight_bounds", ovs_ok, "D4-D")

    rv_missing = [r for r in ROLLBACK_VERIFICATION_IDS if r not in planning_text]
    rb_ok = (
        "Rollback" in planning_text
        and "verification" in planning_text.lower()
        and not rv_missing
        and force_fail != "rollback_verification"
    )
    if force_fail == "rollback_verification":
        rb_ok = False
    result.add("rollback_verification", rb_ok, f"missing_rv={rv_missing}")

    ev_ok = (
        "Evidence" in planning_text
        and "policy_version" in planning_text
        and "explain" in planning_text.lower()
        and "provenance" in planning_text.lower()
        and force_fail != "evidence_provenance"
    )
    if force_fail == "evidence_provenance":
        ev_ok = False
    result.add("evidence_provenance", ev_ok, "D4-I")

    exit_ok = (
        "D1 exit" in planning_text
        or "exit criteria" in planning_text.lower()
        or "Signoff conditions" in planning_text
    ) and ("D4-E" in planning_text and "D4-J" in planning_text and "D4-K" in planning_text)
    if force_fail == "d1_exit_criteria":
        exit_ok = False
    result.add("d1_exit_criteria", exit_ok, "D4-E/J/K (not D3 perf)")

    hygiene_ok = "Claim hygiene" in planning_text and force_fail != "claim_hygiene"
    if force_fail == "claim_hygiene":
        hygiene_ok = False
    result.add("claim_hygiene", hygiene_ok, "D4-F")

    live_disabled_mentioned = (
        "live=DISABLED" in planning_text or "**live=DISABLED**" in planning_text
    )
    claims_live_ready = (
        "live ready" in planning_text.lower()
        and "not live" not in planning_text.lower()
        and "not claim live" not in planning_text.lower()
    )
    # Explicit non-claims in the maturation doc
    forbids_enable = (
        "does **not** enable live" in planning_text
        or "does not enable live" in planning_text.lower()
        or "not live-ready" in planning_text.lower()
        or "without claiming live ready" in planning_text.lower()
        or "does **not** claim live readiness" in planning_text
        or "composition does **not** claim live readiness" in planning_text
    )
    live_ok = live_disabled_mentioned and forbids_enable and not claims_live_ready
    if force_fail == "live_disabled":
        live_ok = False
    result.add("live_disabled", live_ok, "live=DISABLED + no live-ready claim")

    composed_ok = _cps_verified(root, COMPOSED_CPS) and force_fail != "composed_cps"
    if force_fail == "composed_cps":
        composed_ok = False
    result.add("composed_cps", composed_ok, f"cps={list(COMPOSED_CPS)}")

    prior_ok = (root / "snapshots" / PRIOR_CP / "CHECKPOINT.json").is_file()
    result.add("prior_cp_present", prior_ok, PRIOR_CP)

    cap_ok = (root / CAPABILITY_DOC).is_file() and (root / SCHEMA_DOC).is_file()
    if force_fail == "capability_schema_present":
        cap_ok = False
    result.add("capability_schema_present", cap_ok)

    upstream_ok = all((root / rel).is_file() for rel in _UPSTREAM_DOCS)
    if force_fail == "upstream_docs_present":
        upstream_ok = False
    result.add("upstream_docs_present", upstream_ok, f"n={len(_UPSTREAM_DOCS)}")

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
    for rel in (PLANNING_DOC, CAPABILITY_DOC):
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

    # Operator execute may be True in matrix but must remain gated
    op_row = AUTHORITY_MATRIX["Operator"]
    judge_row = AUTHORITY_MATRIX["L_judge"]
    matrix_semantics_ok = (
        judge_row == (True, False, False, False)
        and op_row[2] is True  # veto
        and AUTHORITY_MATRIX["Oversight_I5"][3] is False  # cannot execute
        and force_fail != "authority_semantics"
    )
    if force_fail == "authority_semantics":
        matrix_semantics_ok = False
    result.add("authority_semantics", matrix_semantics_ok)

    gate = default_maturation_gate()
    record = {
        "schema": "mesh.release.d1_safety_maturation/v1",
        "ok": result.ok,
        "package_held": result.version,
        "tip": result.tip,
        "cp": result.cp,
        "prior_cp": result.prior_cp,
        "cycle": CYCLE,
        "d4_debt_ids": list(D4_DEBT_IDS),
        "rollback_verification_ids": list(ROLLBACK_VERIFICATION_IDS),
        "authority_matrix": authority_matrix_as_rows(),
        "composed_cps": list(COMPOSED_CPS),
        "maturation_gate": gate,
        "pytest_count": result.pytest_count,
        "dual_primary": result.dual_primary,
        "timestamp": result.timestamp,
        "preferred_next": PREFERRED_NEXT_DEFAULT,
        "live": "DISABLED",
        "m1_status": "NO_CONSENSUS_YET",
        "mesh_perf_experimental": "OFF",
        "package_open_0190": False,
        "d1_exit_ready_for_live": False,
        "no_held": NO_HELD_DEFAULT,
        "gates": [g.to_dict() for g in result.gates],
        "note": (
            "D1 L_judge safety-case maturation: absorbs ChatGPT D4-A..K into "
            "authority/consensus-draft/continuity/oversight/rollback-verify/"
            "evidence/claim-hygiene/acceptance artifacts composing CP-0058+"
            "0068+0069. Design-only. live=DISABLED. M1=NO_CONSENSUS_YET. "
            "Does not enable live, open pkg0190, unlock GIA/Raft/N>2, or flip "
            "MESH_PERF_EXPERIMENTAL."
        ),
    }
    summary_path = out / "D1_SAFETY_MATURATION.json"
    summary_path.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    result.summary_path = str(summary_path)
    result.summary = {
        "d4_debt_ids": list(D4_DEBT_IDS),
        "composed_cps": list(COMPOSED_CPS),
        "live": "DISABLED",
        "m1_status": "NO_CONSENSUS_YET",
        "mesh_perf_experimental": "OFF",
        "d1_exit_ready_for_live": False,
        "package_open_0190": False,
    }

    if write_project_state and result.ok:
        mirror = root / ".project_state" / "D1_SAFETY_MATURATION.json"
        mirror.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    return result
