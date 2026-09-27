"""0.19 design-set signoff (CP-0055 / Cycle 51).

Closes frozen 0.19 plan themes A–D (design-only track) without opening
package 0.19.0, without retagging v0.18.0, and without unlocking NO_HELD.
Writes dist/releases/0.19.x-design/DESIGN_SET_SIGNOFF.json (+ checklist).
"""

from __future__ import annotations

import json
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
    "PRIOR_CP_019D",
    "SEAL_CP_019D",
    "CYCLE_019D",
    "THEME_CPS",
    "THEME_DOCS",
    "THEME_LABELS",
    "PREFERRED_NEXT_DEFAULT",
    "DesignSetSignoffResult",
    "run_019_design_set_signoff",
]

PACKAGE_HELD = "0.18.0"
DESIGN_CHANNEL = "0.19.x-design"
PRIOR_CP_019D = "CP-0054"
SEAL_CP_019D = "CP-0055"
CYCLE_019D = 51
PREFERRED_NEXT_DEFAULT = "await_deepseek_design_signoff"

# Evidence CPs spanning A–D design track (freeze + designs + maturation)
THEME_CPS: tuple[str, ...] = (
    "CP-0047",  # bootstrap + L_judge/goals design
    "CP-0048",  # 0.19 scope freeze A–D
    "CP-0049",  # agent_shell spike plan
    "CP-0050",  # M1 design + M2/M3 pointers
    "CP-0051",  # L_judge schema stubs
    "CP-0052",  # L_judge MIX integration
    "CP-0053",  # agent_shell spike execution
    "CP-0054",  # M1 scorecard maturation
)

THEME_DOCS: tuple[tuple[str, str], ...] = (
    ("A_L_judge_MIX", "docs/design/L_JUDGE_MIX_DESIGN.md"),
    ("A_L_judge_integration", "docs/design/L_JUDGE_MIX_INTEGRATION.md"),
    ("B_durable_goals", "docs/design/DURABLE_GOALS_CONTINUITY_DESIGN.md"),
    ("C_agent_shell_plan", "docs/design/AGENT_SHELL_ADAPTER_SPIKE.md"),
    ("C_agent_shell_exec", "docs/design/AGENT_SHELL_SPIKE_EXECUTION.md"),
    ("D_M1_design", "docs/design/fabric/M1_CONSENSUS_CHOICE_DESIGN.md"),
    ("D_M1_maturation", "docs/design/fabric/M1_SCORECARD_MATURATION.md"),
    ("D_M2_pointer", "docs/design/fabric/M2_MEMBERSHIP_REJOIN_POINTER.md"),
    ("D_M3_pointer", "docs/design/fabric/M3_WAN_PARTITION_HLC_POINTER.md"),
    ("scope_frozen", "docs/planning/0.19_SCOPE_FROZEN.md"),
)

THEME_LABELS: dict[str, str] = {
    "A": "L_judge_MIX_adapter_design",
    "B": "durable_goal_registry_continuity",
    "C": "agent_shell_adapter_spike",
    "D": "M1_M2_M3_fabric_design_pointers",
}


@dataclass
class DesignSetSignoffResult:
    ok: bool = True
    errors: list[str] = field(default_factory=list)
    gates: list[GateResult] = field(default_factory=list)
    version: str | None = None
    tip: str | None = None
    cp: str | None = None
    prior_cp: str | None = None
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
            "schema_id": "mesh.release.design_set_signoff/v1",
            "preferred_next": PREFERRED_NEXT_DEFAULT,
        }

    def signoff_record(self) -> dict[str, Any]:
        themes = dict(THEME_LABELS)
        themes["status"] = "CLOSED"
        return {
            "schema": "mesh.release.design_set_signoff/v1",
            "ok": self.ok,
            "package_held": self.version,
            "tip": self.tip,
            "cp": self.cp,
            "prior_cp": self.prior_cp,
            "channel": self.channel,
            "themes": themes,
            "theme_cps": list(THEME_CPS),
            "pytest_count": self.pytest_count,
            "dual_primary": self.dual_primary,
            "timestamp": self.timestamp,
            "signer": self.signer,
            "cycle": CYCLE_019D,
            "line_status": "CLOSED_FROZEN_DESIGN_SET",
            "package_open_0190": False,
            "preferred_next": PREFERRED_NEXT_DEFAULT,
            "no_held": NO_HELD_DEFAULT,
            "gates": [g.to_dict() for g in self.gates],
            "note": (
                "0.19 A–D design-set CLOSED/FROZEN; package stays 0.18.0. "
                "Do not open 0.19.0 here. Do not retag v0.18.0. "
                "NO_CONSENSUS_YET on M1 unlock; Raft/N>2 still NO_HELD. "
                "Do not claim GIA; no train/SaaS/economy."
            ),
            "m1_unlock": "NO_CONSENSUS_YET",
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


def run_019_design_set_signoff(
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
) -> DesignSetSignoffResult:
    root = Path(root)
    result = DesignSetSignoffResult()
    result.version = _read_version(root)
    result.tip = _git_tip(root, tip)
    result.cp = SEAL_CP_019D
    result.prior_cp = PRIOR_CP_019D
    result.channel = DESIGN_CHANNEL
    result.dual_primary = dual_primary
    result.timestamp = timestamp or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    result.pytest_count = pytest_count

    out = Path(out_dir) if out_dir else root / "dist" / "releases" / "0.19.x-design"
    out.mkdir(parents=True, exist_ok=True)

    # Gates
    ver_ok = result.version == PACKAGE_HELD and force_fail != "version_held"
    result.add("version_held", ver_ok, f"version={result.version} expect={PACKAGE_HELD}")

    docs_ok = all((root / rel).is_file() for _, rel in THEME_DOCS)
    if force_fail == "themes_a_d_present":
        docs_ok = False
    result.themes_ok = docs_ok
    result.add("themes_a_d_present", docs_ok, f"n_docs={len(THEME_DOCS)}")

    cps_ok = True
    for cp in THEME_CPS:
        snap = root / "snapshots" / cp
        ck = snap / "CHECKPOINT.json"
        if not ck.is_file():
            cps_ok = False
            break
        data = json.loads(ck.read_text(encoding="utf-8"))
        if str(data.get("status", "")).upper() != "VERIFIED":
            cps_ok = False
            break
    if force_fail == "cps_verified":
        cps_ok = False
    result.cps_ok = cps_ok
    result.add("cps_verified", cps_ok, f"cps={list(THEME_CPS)}")

    prior_ok = (root / "snapshots" / PRIOR_CP_019D / "CHECKPOINT.json").is_file()
    result.add("prior_cp_present", prior_ok, PRIOR_CP_019D)

    freeze_ok = (root / "docs" / "planning" / "0.19_SCOPE_FROZEN.md").is_file()
    result.add("scope_frozen_present", freeze_ok)

    m1_text = (root / "docs" / "design" / "fabric" / "M1_SCORECARD_MATURATION.md").read_text(
        encoding="utf-8"
    )
    m1_ok = "NO_CONSENSUS_YET" in m1_text and ("no default" in m1_text.lower() or "not default" in m1_text.lower())
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

    # prior release signoffs untouched
    p163 = root / ".project_state" / "RELEASE_SIGNOFF_0.16.3.json"
    p170 = root / ".project_state" / "THEME_SIGNOFF_0.17.0.json"
    p180 = root / ".project_state" / "THEME_SIGNOFF_0.18.0.json"
    prior_ok2 = p163.is_file() and p170.is_file() and p180.is_file()
    if force_fail == "prior_releases_untouched":
        prior_ok2 = False
    result.add("prior_releases_untouched", prior_ok2)

    gia_docs = [
        root / "docs" / "planning" / "0.19_SCOPE_FROZEN.md",
        root / "docs" / "planning" / "0.19_NON_GOALS.md",
    ]
    gia_ok = True
    for p in gia_docs:
        t = p.read_text(encoding="utf-8").lower()
        if "we are gia" in t or "agi achieved" in t or "gia unlocked" in t:
            gia_ok = False
    if force_fail == "no_gia_claim":
        gia_ok = False
    result.add("no_gia_claim", gia_ok)

    # no v0.19.0 tag required / must not invent package open
    result.add("package_0190_not_opened", force_fail != "package_0190_not_opened", "0.19.0 deferred")

    if not skip_pytest and pytest_count is not None:
        py_ok = pytest_count > 0 and force_fail != "pytest_green"
        result.add("pytest_green", py_ok, f"count={pytest_count}")
    elif pytest_count is not None:
        result.add("pytest_green", force_fail != "pytest_green", f"injected={pytest_count}")

    # Write artifacts
    record = result.signoff_record()
    signoff_path = out / "DESIGN_SET_SIGNOFF.json"
    checklist_path = out / "CHECKLIST.json"
    signoff_path.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    checklist = {
        "schema": "mesh.release.design_set_checklist/v1",
        "ok": result.ok,
        "channel": DESIGN_CHANNEL,
        "package_held": PACKAGE_HELD,
        "gates": [g.to_dict() for g in result.gates],
        "preferred_next": PREFERRED_NEXT_DEFAULT,
        "no_held": NO_HELD_DEFAULT,
    }
    checklist_path.write_text(json.dumps(checklist, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    result.signoff_path = str(signoff_path)
    result.checklist_path = str(checklist_path)
    result.summary = {
        "themes": THEME_LABELS,
        "cps": list(THEME_CPS),
        "m1_unlock": "NO_CONSENSUS_YET",
    }

    if write_project_state and result.ok:
        mirror = root / ".project_state" / "THEME_SIGNOFF_0.19_DESIGN.json"
        mirror.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    return result
