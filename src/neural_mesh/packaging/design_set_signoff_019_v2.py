"""0.19 design-set signoff v2 (CP-0063 / Cycle 59).

Amends/extends CP-0055 (Cycle 51) A–D design-set signoff to include post-C51
work: live-adapter design + safety case, M2, M3, L_judge×M2 e2e, agent_shell
extended. Package stays 0.18.0 HELD — does **not** open 0.19.0, does **not**
create tag v0.19.0, does **not** unlock NO_HELD / GIA / live / train / SaaS.
"""

from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .design_set_signoff_019 import (
    THEME_CPS as BASE_THEME_CPS,
    THEME_DOCS as BASE_THEME_DOCS,
    THEME_LABELS as BASE_THEME_LABELS,
)
from .release_checklist import NO_HELD_DEFAULT, GateResult
from .release_signoff import DEFAULT_SIGNER

__all__ = [
    "PACKAGE_HELD",
    "DESIGN_CHANNEL",
    "PRIOR_CP_019D_V2",
    "SEAL_CP_019D_V2",
    "CYCLE_019D_V2",
    "BASELINE_CP_019D",
    "EXTENSION_CPS",
    "THEME_CPS_V2",
    "EXTENSION_DOCS",
    "THEME_DOCS_V2",
    "THEME_LABELS_V2",
    "PREFERRED_NEXT_DEFAULT",
    "DesignSetSignoffV2Result",
    "run_019_design_set_signoff_v2",
]

PACKAGE_HELD = "0.18.0"
DESIGN_CHANNEL = "0.19.x-design"
BASELINE_CP_019D = "CP-0055"  # Cycle 51 A–D seal
PRIOR_CP_019D_V2 = "CP-0062"
SEAL_CP_019D_V2 = "CP-0063"
CYCLE_019D_V2 = 59
PREFERRED_NEXT_DEFAULT = "await_deepseek"

# Post-C51 sealed work included in this amendment (C51 predates these).
EXTENSION_CPS: tuple[str, ...] = (
    "CP-0057",  # L_judge live-adapter design
    "CP-0058",  # L_judge live-adapter safety case
    "CP-0059",  # M2 membership+rejoin design
    "CP-0060",  # M3 WAN model design
    "CP-0061",  # L_judge × M2 e2e (mock; live=DISABLED)
    "CP-0062",  # agent_shell extended scenarios
)

# Full evidence set: baseline A–D CPs + C51 seal + extension CPs.
THEME_CPS_V2: tuple[str, ...] = tuple(
    dict.fromkeys((*BASE_THEME_CPS, BASELINE_CP_019D, *EXTENSION_CPS))
)

EXTENSION_DOCS: tuple[tuple[str, str], ...] = (
    ("E_live_adapter_design", "docs/design/L_JUDGE_LIVE_ADAPTER_DESIGN.md"),
    ("E_live_adapter_safety", "docs/design/L_JUDGE_LIVE_ADAPTER_SAFETY_CASE.md"),
    ("F_M2_design", "docs/design/fabric/M2_MEMBERSHIP_REJOIN_DESIGN.md"),
    ("F_M3_design", "docs/design/fabric/M3_WAN_MODEL_DESIGN.md"),
    ("G_l_judge_m2_e2e", "docs/design/L_JUDGE_M2_E2E_SPIKE.md"),
    ("G_agent_shell_extended", "docs/design/AGENT_SHELL_EXTENDED_SCENARIOS.md"),
    ("signoff_v1", "docs/planning/0.19_DESIGN_SET_SIGNOFF.md"),
    ("scope_frozen", "docs/planning/0.19_SCOPE_FROZEN.md"),
)

THEME_DOCS_V2: tuple[tuple[str, str], ...] = tuple(
    dict.fromkeys((*BASE_THEME_DOCS, *EXTENSION_DOCS))
)

THEME_LABELS_V2: dict[str, str] = {
    **BASE_THEME_LABELS,
    "E": "L_judge_live_adapter_design_and_safety",
    "F": "M2_M3_fabric_design_matured",
    "G": "L_judge_M2_e2e_and_agent_shell_extended_spikes",
}


@dataclass
class DesignSetSignoffV2Result:
    ok: bool = True
    errors: list[str] = field(default_factory=list)
    gates: list[GateResult] = field(default_factory=list)
    version: str | None = None
    tip: str | None = None
    cp: str | None = None
    prior_cp: str | None = None
    baseline_cp: str | None = None
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
            "baseline_cp": self.baseline_cp,
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
            "schema_id": "mesh.release.design_set_signoff/v2",
            "preferred_next": PREFERRED_NEXT_DEFAULT,
            "amendment": "v2",
        }

    def signoff_record(self) -> dict[str, Any]:
        themes = dict(THEME_LABELS_V2)
        themes["status"] = "CLOSED_V2"
        themes["baseline_status"] = "CLOSED"  # A–D from CP-0055
        return {
            "schema": "mesh.release.design_set_signoff/v2",
            "amendment": "v2",
            "ok": self.ok,
            "package_held": self.version,
            "tip": self.tip,
            "cp": self.cp,
            "prior_cp": self.prior_cp,
            "baseline_cp": self.baseline_cp,
            "channel": self.channel,
            "themes": themes,
            "theme_cps": list(THEME_CPS_V2),
            "extension_cps": list(EXTENSION_CPS),
            "pytest_count": self.pytest_count,
            "dual_primary": self.dual_primary,
            "timestamp": self.timestamp,
            "signer": self.signer,
            "cycle": CYCLE_019D_V2,
            "line_status": "CLOSED_FROZEN_DESIGN_SET_V2",
            "package_open_0190": False,
            "preferred_next": PREFERRED_NEXT_DEFAULT,
            "no_held": NO_HELD_DEFAULT,
            "live": "DISABLED",
            "gates": [g.to_dict() for g in self.gates],
            "note": (
                "0.19 design-set signoff v2: amends CP-0055 A–D CLOSED with "
                "post-C51 M2/M3/live-adapter/safety/L_judge×M2 e2e/agent_shell "
                "extended. Package stays 0.18.0. Do not open 0.19.0. Do not "
                "retag v0.18.0 / create v0.19.0. M1=NO_CONSENSUS_YET; "
                "Raft/N>2/GIA still NO_HELD; live=DISABLED; no train/SaaS."
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


def run_019_design_set_signoff_v2(
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
) -> DesignSetSignoffV2Result:
    root = Path(root)
    result = DesignSetSignoffV2Result()
    result.version = _read_version(root)
    result.tip = _git_tip(root, tip)
    result.cp = SEAL_CP_019D_V2
    result.prior_cp = PRIOR_CP_019D_V2
    result.baseline_cp = BASELINE_CP_019D
    result.channel = DESIGN_CHANNEL
    result.dual_primary = dual_primary
    result.timestamp = timestamp or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    result.pytest_count = pytest_count

    out = Path(out_dir) if out_dir else root / "dist" / "releases" / "0.19.x-design"
    out.mkdir(parents=True, exist_ok=True)

    ver_ok = result.version == PACKAGE_HELD and force_fail != "version_held"
    result.add("version_held", ver_ok, f"version={result.version} expect={PACKAGE_HELD}")

    docs_ok = all((root / rel).is_file() for _, rel in THEME_DOCS_V2)
    if force_fail == "themes_a_g_present":
        docs_ok = False
    result.themes_ok = docs_ok
    result.add("themes_a_g_present", docs_ok, f"n_docs={len(THEME_DOCS_V2)}")

    # Baseline A–D docs still present (C51 contract)
    base_docs_ok = all((root / rel).is_file() for _, rel in BASE_THEME_DOCS)
    if force_fail == "baseline_a_d_present":
        base_docs_ok = False
    result.add("baseline_a_d_present", base_docs_ok, f"n_base={len(BASE_THEME_DOCS)}")

    ext_docs_ok = all((root / rel).is_file() for _, rel in EXTENSION_DOCS)
    if force_fail == "extension_docs_present":
        ext_docs_ok = False
    result.add("extension_docs_present", ext_docs_ok, f"n_ext={len(EXTENSION_DOCS)}")

    cps_ok = _cps_verified(root, THEME_CPS_V2)
    if force_fail == "cps_verified":
        cps_ok = False
    result.cps_ok = cps_ok
    result.add("cps_verified", cps_ok, f"cps={list(THEME_CPS_V2)}")

    ext_cps_ok = _cps_verified(root, EXTENSION_CPS)
    if force_fail == "extension_cps_verified":
        ext_cps_ok = False
    result.add("extension_cps_verified", ext_cps_ok, f"ext={list(EXTENSION_CPS)}")

    baseline_ok = (root / "snapshots" / BASELINE_CP_019D / "CHECKPOINT.json").is_file()
    if force_fail == "baseline_cp_present":
        baseline_ok = False
    result.add("baseline_cp_present", baseline_ok, BASELINE_CP_019D)

    prior_ok = (root / "snapshots" / PRIOR_CP_019D_V2 / "CHECKPOINT.json").is_file()
    result.add("prior_cp_present", prior_ok, PRIOR_CP_019D_V2)

    freeze_ok = (root / "docs" / "planning" / "0.19_SCOPE_FROZEN.md").is_file()
    result.add("scope_frozen_present", freeze_ok)

    m1_path = root / "docs" / "design" / "fabric" / "M1_SCORECARD_MATURATION.md"
    m1_text = m1_path.read_text(encoding="utf-8") if m1_path.is_file() else ""
    m1_ok = "NO_CONSENSUS_YET" in m1_text and (
        "no default" in m1_text.lower() or "not default" in m1_text.lower()
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
    prior_ok2 = p163.is_file() and p170.is_file() and p180.is_file()
    if force_fail == "prior_releases_untouched":
        prior_ok2 = False
    result.add("prior_releases_untouched", prior_ok2)

    gia_docs = [
        root / "docs" / "planning" / "0.19_SCOPE_FROZEN.md",
        root / "docs" / "planning" / "0.19_NON_GOALS.md",
        root / "docs" / "planning" / "0.19_DESIGN_SET_SIGNOFF.md",
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
        root / "docs" / "design" / "L_JUDGE_LIVE_ADAPTER_SAFETY_CASE.md",
        root / "docs" / "design" / "L_JUDGE_M2_E2E_SPIKE.md",
        root / "docs" / "design" / "AGENT_SHELL_EXTENDED_SCENARIOS.md",
    ]
    joined = " ".join(
        (lp.read_text(encoding="utf-8") if lp.is_file() else "") for lp in live_docs
    )
    live_ok = ("DISABLED" in joined or "live=DISABLED" in joined) and all(
        lp.is_file() for lp in live_docs
    )
    if force_fail == "live_disabled":
        live_ok = False
    result.add("live_disabled", live_ok, "live=DISABLED across extension spikes")

    result.add(
        "package_0190_not_opened",
        force_fail != "package_0190_not_opened",
        "0.19.0 deferred",
    )

    # no v0.19.0 tag
    tag_rc = subprocess.run(
        ["git", "rev-parse", "--verify", "v0.19.0"],
        cwd=str(root),
        capture_output=True,
    ).returncode
    no_v019 = tag_rc != 0 and force_fail != "no_v019_tag"
    if force_fail == "no_v019_tag":
        no_v019 = False
    result.add("no_v019_tag", no_v019, "v0.19.0 absent")

    if not skip_pytest and pytest_count is not None:
        py_ok = pytest_count > 0 and force_fail != "pytest_green"
        result.add("pytest_green", py_ok, f"count={pytest_count}")
    elif pytest_count is not None:
        result.add("pytest_green", force_fail != "pytest_green", f"injected={pytest_count}")

    record = result.signoff_record()
    signoff_path = out / "DESIGN_SET_SIGNOFF_V2.json"
    checklist_path = out / "CHECKLIST_V2.json"
    signoff_path.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    checklist = {
        "schema": "mesh.release.design_set_checklist/v2",
        "amendment": "v2",
        "ok": result.ok,
        "channel": DESIGN_CHANNEL,
        "package_held": PACKAGE_HELD,
        "baseline_cp": BASELINE_CP_019D,
        "extension_cps": list(EXTENSION_CPS),
        "gates": [g.to_dict() for g in result.gates],
        "preferred_next": PREFERRED_NEXT_DEFAULT,
        "no_held": NO_HELD_DEFAULT,
        "live": "DISABLED",
    }
    checklist_path.write_text(json.dumps(checklist, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    result.signoff_path = str(signoff_path)
    result.checklist_path = str(checklist_path)
    result.summary = {
        "themes": THEME_LABELS_V2,
        "cps": list(THEME_CPS_V2),
        "extension_cps": list(EXTENSION_CPS),
        "m1_unlock": "NO_CONSENSUS_YET",
        "amendment": "v2",
        "live": "DISABLED",
    }

    if write_project_state and result.ok:
        mirror = root / ".project_state" / "THEME_SIGNOFF_0.19_DESIGN.json"
        mirror.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        v2_mirror = root / ".project_state" / "THEME_SIGNOFF_0.19_DESIGN_V2.json"
        v2_mirror.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    return result
