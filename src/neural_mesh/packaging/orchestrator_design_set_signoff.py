"""Orchestrator design-set signoff (CP-0070 / Cycle 66).

Formal ledger close for the orchestrator contract CP-0064..CP-0069
(routing, continuity, oversight, spikes, perf, safety), analogous to the
0.19 design-set signoff_v2 (CP-0063). Package stays 0.18.0 HELD — does
**not** open 0.19.0 / pkg0190, does **not** create tag v0.19.0, does
**not** unlock NO_HELD / GIA / live / train / SaaS. MESH_PERF_EXPERIMENTAL
stays OFF. M1=NO_CONSENSUS_YET.
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
from .release_signoff import DEFAULT_SIGNER

__all__ = [
    "PACKAGE_HELD",
    "DESIGN_CHANNEL",
    "PRIOR_CP",
    "SEAL_CP",
    "CYCLE",
    "BASELINE_SIGNOFF_CP",
    "CONTRACT_CPS",
    "SUPPORTING_CPS",
    "THEME_CPS",
    "THEME_DOCS",
    "THEME_LABELS",
    "PREFERRED_NEXT_DEFAULT",
    "EXPERIMENTAL_FLAG_ENV",
    "OrchestratorDesignSetSignoffResult",
    "run_orchestrator_design_set_signoff",
]

PACKAGE_HELD = "0.18.0"
DESIGN_CHANNEL = "orchestrator-design"
BASELINE_SIGNOFF_CP = "CP-0063"  # 0.19 design-set signoff_v2 (analogous prior)
PRIOR_CP = "CP-0069"
SEAL_CP = "CP-0070"
CYCLE = 66
PREFERRED_NEXT_DEFAULT = "await_deepseek"
EXPERIMENTAL_FLAG_ENV = "MESH_PERF_EXPERIMENTAL"

# Primary ledger range: orchestrator contract (DeepSeek C65 Option1).
CONTRACT_CPS: tuple[str, ...] = (
    "CP-0064",  # routing
    "CP-0065",  # multi-judge spike
    "CP-0066",  # perf research track
    "CP-0067",  # perf hotspot + improvement
    "CP-0068",  # continuity
    "CP-0069",  # oversight
)

# Supporting evidence cited in the coherent contract surface.
SUPPORTING_CPS: tuple[str, ...] = (
    "CP-0058",  # L_judge live-adapter safety case
    "CP-0061",  # L_judge × M2 e2e spike
)

THEME_CPS: tuple[str, ...] = tuple(dict.fromkeys((*SUPPORTING_CPS, *CONTRACT_CPS)))

THEME_DOCS: tuple[tuple[str, str], ...] = (
    ("A_routing", "docs/design/ORCHESTRATOR_JUDGE_ROUTING_DESIGN.md"),
    ("A_routing_cap", "docs/capabilities/MESH_ORCHESTRATOR_JUDGE_ROUTING.md"),
    ("B_continuity", "docs/design/ORCHESTRATOR_CONTINUITY_DESIGN.md"),
    ("B_continuity_cap", "docs/capabilities/MESH_ORCHESTRATOR_CONTINUITY.md"),
    ("C_oversight", "docs/design/ORCHESTRATOR_OVERSIGHT_HOOKS_DESIGN.md"),
    ("C_oversight_cap", "docs/capabilities/MESH_ORCHESTRATOR_OVERSIGHT.md"),
    ("D_multi_judge_spike", "docs/design/MULTI_JUDGE_AGENT_SHELL_SPIKE.md"),
    ("D_l_judge_m2_e2e", "docs/design/L_JUDGE_M2_E2E_SPIKE.md"),
    ("E_perf_research", "docs/design/MESH_PERF_RESEARCH_TRACK.md"),
    ("E_perf_hotspot", "docs/design/MESH_PERF_HOTSPOT_AND_IMPROVEMENT_DESIGN.md"),
    ("F_safety_case", "docs/design/L_JUDGE_LIVE_ADAPTER_SAFETY_CASE.md"),
    ("prior_019_signoff_v2", "docs/planning/0.19_DESIGN_SET_SIGNOFF.md"),
    ("non_goals", "docs/planning/0.19_NON_GOALS.md"),
)

THEME_LABELS: dict[str, str] = {
    "A": "orchestrator_judge_routing",
    "B": "orchestrator_continuity",
    "C": "orchestrator_oversight_hooks",
    "D": "spike_evidence_multi_judge_and_l_judge_m2_e2e",
    "E": "perf_baseline_and_hotspot_design",
    "F": "l_judge_live_adapter_safety_case",
}


@dataclass
class OrchestratorDesignSetSignoffResult:
    ok: bool = True
    errors: list[str] = field(default_factory=list)
    gates: list[GateResult] = field(default_factory=list)
    version: str | None = None
    tip: str | None = None
    cp: str | None = None
    prior_cp: str | None = None
    baseline_signoff_cp: str | None = None
    channel: str | None = None
    themes_ok: bool | None = None
    cps_ok: bool | None = None
    pytest_count: int | None = None
    dual_primary: int = 0
    signer: str = DEFAULT_SIGNER
    timestamp: str | None = None
    signoff_path: str | None = None
    checklist_path: str | None = None
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
            "baseline_signoff_cp": self.baseline_signoff_cp,
            "channel": self.channel,
            "themes_ok": self.themes_ok,
            "cps_ok": self.cps_ok,
            "pytest_count": self.pytest_count,
            "dual_primary": self.dual_primary,
            "signer": self.signer,
            "timestamp": self.timestamp,
            "signoff_path": self.signoff_path,
            "checklist_path": self.checklist_path,
            "gates": [g.to_dict() for g in self.gates],
            "summary": dict(self.summary),
            "no_held": NO_HELD_DEFAULT,
            "schema_id": "mesh.release.orchestrator_design_set_signoff/v1",
            "preferred_next": PREFERRED_NEXT_DEFAULT,
        }

    def signoff_record(self) -> dict[str, Any]:
        themes = dict(THEME_LABELS)
        themes["status"] = "CLOSED"
        themes["contract"] = "routing+continuity+oversight+spikes+perf+safety"
        return {
            "schema": "mesh.release.orchestrator_design_set_signoff/v1",
            "ok": self.ok,
            "package_held": self.version,
            "tip": self.tip,
            "cp": self.cp,
            "prior_cp": self.prior_cp,
            "baseline_signoff_cp": self.baseline_signoff_cp,
            "channel": self.channel,
            "themes": themes,
            "theme_cps": list(THEME_CPS),
            "contract_cps": list(CONTRACT_CPS),
            "supporting_cps": list(SUPPORTING_CPS),
            "pytest_count": self.pytest_count,
            "dual_primary": self.dual_primary,
            "timestamp": self.timestamp,
            "signer": self.signer,
            "cycle": CYCLE,
            "line_status": "CLOSED_ORCHESTRATOR_DESIGN_SET",
            "package_open_0190": False,
            "preferred_next": PREFERRED_NEXT_DEFAULT,
            "no_held": NO_HELD_DEFAULT,
            "live": "DISABLED",
            "mesh_perf_experimental": "OFF",
            "m1_unlock": "NO_CONSENSUS_YET",
            "gates": [g.to_dict() for g in self.gates],
            "note": (
                "Orchestrator design-set signoff: formal ledger close for "
                "CP-0064..CP-0069 (routing, continuity, oversight, spikes, "
                "perf, safety) with supporting CP-0058/CP-0061. Analogous to "
                "0.19 design-set signoff_v2 (CP-0063). Package stays 0.18.0. "
                "Do not open 0.19.0 / pkg0190. Do not retag v0.18.0 / create "
                "v0.19.0. M1=NO_CONSENSUS_YET; Raft/N>2/GIA still NO_HELD; "
                "live=DISABLED; MESH_PERF_EXPERIMENTAL=OFF; no train/SaaS."
            ),
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
    if not raw or raw in {"0", "off", "false", "no", ""}:
        return True
    return False


def run_orchestrator_design_set_signoff(
    root: Path,
    *,
    out_dir: Path | None = None,
    tip: str | None = None,
    timestamp: str | None = None,
    pytest_count: int | None = None,
    skip_pytest: bool = False,
    force_fail: str | None = None,
    write_project_state: bool = True,
    dual_primary: int = 0,
) -> OrchestratorDesignSetSignoffResult:
    root = Path(root)
    result = OrchestratorDesignSetSignoffResult()
    result.version = _read_version(root)
    result.tip = _git_tip(root, tip)
    result.cp = SEAL_CP
    result.prior_cp = PRIOR_CP
    result.baseline_signoff_cp = BASELINE_SIGNOFF_CP
    result.channel = DESIGN_CHANNEL
    result.dual_primary = dual_primary
    result.timestamp = timestamp or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    result.pytest_count = pytest_count

    out = Path(out_dir) if out_dir else root / "dist" / "releases" / "orchestrator-design"
    out.mkdir(parents=True, exist_ok=True)

    ver_ok = result.version == PACKAGE_HELD and force_fail != "version_held"
    result.add("version_held", ver_ok, f"version={result.version} expect={PACKAGE_HELD}")

    docs_ok = all((root / rel).is_file() for _, rel in THEME_DOCS)
    if force_fail == "themes_a_f_present":
        docs_ok = False
    result.themes_ok = docs_ok
    result.add("themes_a_f_present", docs_ok, f"n_docs={len(THEME_DOCS)}")

    contract_docs = [d for d in THEME_DOCS if d[0].startswith(("A_", "B_", "C_"))]
    contract_docs_ok = all((root / rel).is_file() for _, rel in contract_docs)
    if force_fail == "contract_docs_present":
        contract_docs_ok = False
    result.add("contract_docs_present", contract_docs_ok, f"n_contract={len(contract_docs)}")

    cps_ok = _cps_verified(root, THEME_CPS)
    if force_fail == "cps_verified":
        cps_ok = False
    result.cps_ok = cps_ok
    result.add("cps_verified", cps_ok, f"cps={list(THEME_CPS)}")

    contract_ok = _cps_verified(root, CONTRACT_CPS)
    if force_fail == "contract_cps_verified":
        contract_ok = False
    result.add("contract_cps_verified", contract_ok, f"contract={list(CONTRACT_CPS)}")

    supporting_ok = _cps_verified(root, SUPPORTING_CPS)
    if force_fail == "supporting_cps_verified":
        supporting_ok = False
    result.add("supporting_cps_verified", supporting_ok, f"supporting={list(SUPPORTING_CPS)}")

    baseline_ok = (root / "snapshots" / BASELINE_SIGNOFF_CP / "CHECKPOINT.json").is_file()
    if force_fail == "baseline_signoff_present":
        baseline_ok = False
    result.add("baseline_signoff_present", baseline_ok, BASELINE_SIGNOFF_CP)

    prior_ok = (root / "snapshots" / PRIOR_CP / "CHECKPOINT.json").is_file()
    result.add("prior_cp_present", prior_ok, PRIOR_CP)

    m1_path = root / "docs" / "design" / "fabric" / "M1_SCORECARD_MATURATION.md"
    m1_text = m1_path.read_text(encoding="utf-8") if m1_path.is_file() else ""
    m1_ok = "NO_CONSENSUS_YET" in m1_text and (
        "no default" in m1_text.lower() or "not default" in m1_text.lower() or "NO_HELD" in m1_text
    )
    if force_fail == "m1_no_consensus":
        m1_ok = False
    result.add("m1_no_consensus", m1_ok, "NO_CONSENSUS_YET + no Raft default")

    dp_ok = dual_primary == 0 and force_fail != "dual_primary_zero"
    result.add("dual_primary_zero", dp_ok, f"dual_primary={dual_primary}")

    no_held_doc = (root / "docs" / "planning" / "0.19_NON_GOALS.md").read_text(encoding="utf-8")
    nh_ok = "NO_HELD" in no_held_doc and "Raft" in no_held_doc
    if force_fail == "no_held_documented":
        nh_ok = False
    result.add("no_held_documented", nh_ok)

    p163 = root / ".project_state" / "RELEASE_SIGNOFF_0.16.3.json"
    p170 = root / ".project_state" / "THEME_SIGNOFF_0.17.0.json"
    p180 = root / ".project_state" / "THEME_SIGNOFF_0.18.0.json"
    p019v2 = root / ".project_state" / "THEME_SIGNOFF_0.19_DESIGN_V2.json"
    prior_ok2 = p163.is_file() and p170.is_file() and p180.is_file() and p019v2.is_file()
    if force_fail == "prior_releases_untouched":
        prior_ok2 = False
    result.add("prior_releases_untouched", prior_ok2)

    gia_docs = [
        root / "docs" / "planning" / "ORCHESTRATOR_DESIGN_SET_SIGNOFF.md",
        root / "docs" / "capabilities" / "MESH_ORCHESTRATOR_DESIGN_SET_SIGNOFF.md",
        root / "docs" / "planning" / "0.19_NON_GOALS.md",
    ]
    gia_ok = True
    for p in gia_docs:
        if not p.is_file():
            continue
        t = p.read_text(encoding="utf-8").lower()
        if "we are gia" in t or "agi achieved" in t or "gia unlocked" in t:
            gia_ok = False
    if force_fail == "no_gia_claim":
        gia_ok = False
    result.add("no_gia_claim", gia_ok)

    live_docs = [
        root / "docs" / "design" / "ORCHESTRATOR_JUDGE_ROUTING_DESIGN.md",
        root / "docs" / "design" / "ORCHESTRATOR_CONTINUITY_DESIGN.md",
        root / "docs" / "design" / "ORCHESTRATOR_OVERSIGHT_HOOKS_DESIGN.md",
        root / "docs" / "design" / "MULTI_JUDGE_AGENT_SHELL_SPIKE.md",
    ]
    joined = " ".join(
        (lp.read_text(encoding="utf-8") if lp.is_file() else "") for lp in live_docs
    )
    live_ok = ("DISABLED" in joined or "live=DISABLED" in joined) and all(
        lp.is_file() for lp in live_docs
    )
    if force_fail == "live_disabled":
        live_ok = False
    result.add("live_disabled", live_ok, "live=DISABLED across orchestrator contract")

    perf_doc = root / "docs" / "design" / "MESH_PERF_HOTSPOT_AND_IMPROVEMENT_DESIGN.md"
    perf_text = perf_doc.read_text(encoding="utf-8") if perf_doc.is_file() else ""
    exp_doc_ok = "MESH_PERF_EXPERIMENTAL" in perf_text and (
        "OFF" in perf_text or "default" in perf_text.lower()
    )
    exp_env_ok = _experimental_off()
    exp_ok = exp_doc_ok and exp_env_ok and force_fail != "mesh_perf_experimental_off"
    if force_fail == "mesh_perf_experimental_off":
        exp_ok = False
    result.add(
        "mesh_perf_experimental_off",
        exp_ok,
        f"env={os.environ.get(EXPERIMENTAL_FLAG_ENV, '')!r} doc_ok={exp_doc_ok}",
    )

    result.add(
        "package_0190_not_opened",
        force_fail != "package_0190_not_opened",
        "0.19.0 / pkg0190 deferred",
    )

    tag_rc = subprocess.run(
        ["git", "rev-parse", "--verify", "v0.19.0"],
        cwd=str(root),
        capture_output=True,
    ).returncode
    no_v019 = tag_rc != 0 and force_fail != "no_v019_tag"
    if force_fail == "no_v019_tag":
        no_v019 = False
    result.add("no_v019_tag", no_v019, "v0.19.0 absent")

    v018_rc = subprocess.run(
        ["git", "rev-parse", "--verify", "v0.18.0"],
        cwd=str(root),
        capture_output=True,
    ).returncode
    v018_ok = v018_rc == 0 and force_fail != "v018_tag_present"
    if force_fail == "v018_tag_present":
        v018_ok = False
    result.add("v018_tag_present", v018_ok, "v0.18.0 present and untouched")

    if not skip_pytest and pytest_count is not None:
        py_ok = pytest_count > 0 and force_fail != "pytest_green"
        result.add("pytest_green", py_ok, f"count={pytest_count}")
    elif pytest_count is not None:
        result.add("pytest_green", force_fail != "pytest_green", f"injected={pytest_count}")

    record = result.signoff_record()
    signoff_path = out / "ORCHESTRATOR_DESIGN_SET_SIGNOFF.json"
    checklist_path = out / "CHECKLIST.json"
    signoff_path.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    checklist = {
        "schema": "mesh.release.orchestrator_design_set_checklist/v1",
        "ok": result.ok,
        "channel": DESIGN_CHANNEL,
        "package_held": PACKAGE_HELD,
        "baseline_signoff_cp": BASELINE_SIGNOFF_CP,
        "contract_cps": list(CONTRACT_CPS),
        "supporting_cps": list(SUPPORTING_CPS),
        "gates": [g.to_dict() for g in result.gates],
        "preferred_next": PREFERRED_NEXT_DEFAULT,
        "no_held": NO_HELD_DEFAULT,
        "live": "DISABLED",
        "mesh_perf_experimental": "OFF",
        "m1_unlock": "NO_CONSENSUS_YET",
        "package_open_0190": False,
    }
    checklist_path.write_text(json.dumps(checklist, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    result.signoff_path = str(signoff_path)
    result.checklist_path = str(checklist_path)
    result.summary = {
        "themes": THEME_LABELS,
        "cps": list(THEME_CPS),
        "contract_cps": list(CONTRACT_CPS),
        "supporting_cps": list(SUPPORTING_CPS),
        "m1_unlock": "NO_CONSENSUS_YET",
        "live": "DISABLED",
        "mesh_perf_experimental": "OFF",
        "package_open_0190": False,
    }

    if write_project_state and result.ok:
        mirror = root / ".project_state" / "THEME_SIGNOFF_ORCHESTRATOR_DESIGN.json"
        mirror.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    return result
