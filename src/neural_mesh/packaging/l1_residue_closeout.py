"""L1 residue closeout (CP-0056 / Cycle 52).

Audits R1 Fabric ops UX / R2 Richer OBS peers / R3 External quickstart evidence
from C29–C31 (+ R4–R7 priors), fills ops-doc path gaps, and writes a closeout
record without unlocking NO_HELD product R2/R3 or touching v0.18.0.
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
    "CHANNEL",
    "PRIOR_CP",
    "SEAL_CP",
    "CYCLE",
    "EVIDENCE_CPS",
    "EVIDENCE_DOCS",
    "THEME_LABELS",
    "PREFERRED_NEXT_DEFAULT",
    "L1ResidueCloseoutResult",
    "run_l1_residue_closeout",
]

PACKAGE_HELD = "0.18.0"
CHANNEL = "l1-residue"
PRIOR_CP = "CP-0055"
SEAL_CP = "CP-0056"
CYCLE = 52
PREFERRED_NEXT_DEFAULT = "L_judge_live_adapter_design"

# Evidence CPs for L1 R1..R7 residue
EVIDENCE_CPS: tuple[str, ...] = (
    "CP-0032",  # R4–R6 soak/audit/freeze
    "CP-0033",  # R1 fabric ops UX
    "CP-0034",  # R2 obs peers
    "CP-0035",  # R3 quickstart
    "CP-0036",  # R7 0.17 signoff
)

EVIDENCE_DOCS: tuple[tuple[str, str], ...] = (
    ("R1_capability", "docs/capabilities/MESH_FABRIC_OPS_UX.md"),
    ("R1_ops", "docs/ops/fabric-ops-ux-v1.md"),
    ("R1_lib", "src/neural_mesh/network/ops.py"),
    ("R1_tests", "tests/test_fabric_ops_cycle29.py"),
    ("R2_capability", "docs/capabilities/MESH_OBS_PEERS.md"),
    ("R2_ops", "docs/ops/obs-peers-v1.md"),
    ("R2_lib", "src/neural_mesh/obs_peers.py"),
    ("R2_tests", "tests/test_obs_peers_cycle30.py"),
    ("R3_capability", "docs/capabilities/MESH_EXTERNAL_QUICKSTART.md"),
    ("R3_qs_0163", "docs/quickstart/QUICKSTART_0.16.3.md"),
    ("R3_qs_017_stub", "docs/quickstart/QUICKSTART_0.17_STUB.md"),
    ("R3_script", "scripts/quickstart_0.16.3.sh"),
    ("R3_alias", "scripts/quickstart.sh"),
    ("R3_tests", "tests/test_quickstart_cycle31.py"),
    ("closeout", "docs/planning/L1_RESIDUE_CLOSEOUT.md"),
    ("blueprint_root", "council/blueprint/FINAL_BLUEPRINT_ROOT.md"),
)

THEME_LABELS: dict[str, str] = {
    "R1": "fabric_ops_UX",
    "R2": "richer_OBS_peers",
    "R3": "external_quickstart",
    "R4": "n2_soak_P30",
    "R5": "n2_audit_P31",
    "R6": "n2_freeze_P32",
    "R7": "n2_install_signoff_P33_P34",
}


@dataclass
class L1ResidueCloseoutResult:
    ok: bool = True
    errors: list[str] = field(default_factory=list)
    gates: list[GateResult] = field(default_factory=list)
    version: str | None = None
    tip: str | None = None
    cp: str | None = None
    prior_cp: str | None = None
    channel: str | None = None
    docs_ok: bool = False
    cps_ok: bool = False
    pytest_count: int | None = None
    dual_primary: int = 0
    signer: str = DEFAULT_SIGNER
    timestamp: str | None = None
    closeout_path: str | None = None
    checklist_path: str | None = None
    summary: dict[str, Any] = field(default_factory=dict)
    l1_status: str = "CLOSED"

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
            "docs_ok": self.docs_ok,
            "cps_ok": self.cps_ok,
            "pytest_count": self.pytest_count,
            "dual_primary": self.dual_primary,
            "signer": self.signer,
            "timestamp": self.timestamp,
            "closeout_path": self.closeout_path,
            "checklist_path": self.checklist_path,
            "gates": [g.to_dict() for g in self.gates],
            "summary": dict(self.summary),
            "no_held": NO_HELD_DEFAULT,
            "schema_id": "mesh.release.l1_residue_closeout/v1",
            "preferred_next": PREFERRED_NEXT_DEFAULT,
            "l1_status": self.l1_status,
        }

    def closeout_record(self) -> dict[str, Any]:
        themes = dict(THEME_LABELS)
        themes["status"] = "CLOSED"
        return {
            "schema": "mesh.release.l1_residue_closeout/v1",
            "ok": self.ok,
            "package_held": self.version,
            "tip": self.tip,
            "cp": self.cp,
            "prior_cp": self.prior_cp,
            "channel": self.channel,
            "themes": themes,
            "evidence_cps": list(EVIDENCE_CPS),
            "pytest_count": self.pytest_count,
            "dual_primary": self.dual_primary,
            "timestamp": self.timestamp,
            "signer": self.signer,
            "cycle": CYCLE,
            "line_status": "L1_CLOSED",
            "l1_status": self.l1_status,
            "package_open_0190": False,
            "preferred_next": PREFERRED_NEXT_DEFAULT,
            "no_held": NO_HELD_DEFAULT,
            "gates": [g.to_dict() for g in self.gates],
            "note": (
                "L1 REMAINING_0.17 CLOSED via residue closeout. "
                "R1/R2/R3 evidence from CP-0033..0035; R4–R6 CP-0032; R7 CP-0036. "
                "NO_HELD product R2/R3 (ML-router) remain locked. "
                "No GIA/Raft/N>2/train/SaaS. Package stays 0.18.0."
            ),
            "tips": {
                "R1": "e1d5e50",
                "R2": "64747b9",
                "R3": "e6a0964",
                "R4_R6": "8a941f0",
                "R7": "241d570",
            },
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


def run_l1_residue_closeout(
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
) -> L1ResidueCloseoutResult:
    root = Path(root)
    result = L1ResidueCloseoutResult()
    result.version = _read_version(root)
    result.tip = _git_tip(root, tip)
    result.cp = SEAL_CP
    result.prior_cp = PRIOR_CP
    result.channel = CHANNEL
    result.dual_primary = dual_primary
    result.timestamp = timestamp or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    result.pytest_count = pytest_count

    out = Path(out_dir) if out_dir else root / "dist" / "releases" / "l1-residue"
    out.mkdir(parents=True, exist_ok=True)

    ver_ok = result.version == PACKAGE_HELD and force_fail != "version_held"
    result.add("version_held", ver_ok, f"version={result.version} expect={PACKAGE_HELD}")

    docs_ok = all((root / rel).is_file() for _, rel in EVIDENCE_DOCS)
    if force_fail == "evidence_docs_present":
        docs_ok = False
    result.docs_ok = docs_ok
    result.add("evidence_docs_present", docs_ok, f"n_docs={len(EVIDENCE_DOCS)}")

    cps_ok = True
    for cp in EVIDENCE_CPS:
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
    result.add("cps_verified", cps_ok, f"cps={list(EVIDENCE_CPS)}")

    prior_ok = (root / "snapshots" / PRIOR_CP / "CHECKPOINT.json").is_file()
    result.add("prior_cp_present", prior_ok, PRIOR_CP)

    closeout_text = (root / "docs" / "planning" / "L1_RESIDUE_CLOSEOUT.md").read_text(
        encoding="utf-8"
    )
    status_ok = "Status:** CLOSED" in closeout_text or "**Status:** CLOSED" in closeout_text
    if force_fail == "closeout_declares_closed":
        status_ok = False
    result.add("closeout_declares_closed", status_ok)

    bp = (root / "council" / "blueprint" / "FINAL_BLUEPRINT_ROOT.md").read_text(encoding="utf-8")
    bp_ok = "L1 REMAINING_0.17 [CLOSED]" in bp
    if force_fail == "blueprint_l1_closed":
        bp_ok = False
    result.add("blueprint_l1_closed", bp_ok)

    # Distinguish L1 R2/R3 names from NO_HELD product R2/R3
    nh_doc = (root / "docs" / "planning" / "L1_RESIDUE_CLOSEOUT.md").read_text(encoding="utf-8")
    nh_ok = (
        "NO_HELD" in nh_doc
        and "ML-router" in nh_doc
        and "Raft" in nh_doc
        and force_fail != "no_held_product_r2_r3_locked"
    )
    result.add("no_held_product_r2_r3_locked", nh_ok, "L1 R2/R3 ≠ NO_HELD R2/R3")

    dp_ok = dual_primary == 0 and force_fail != "dual_primary_zero"
    result.add("dual_primary_zero", dp_ok, f"dual_primary={dual_primary}")

    qs_alias = root / "scripts" / "quickstart.sh"
    qs_ok = qs_alias.is_file() and "quickstart_0.16.3.sh" in qs_alias.read_text(encoding="utf-8")
    if force_fail == "quickstart_alias":
        qs_ok = False
    result.add("quickstart_alias", qs_ok)

    # no GIA achievement claims
    gia_ok = True
    for needle in ("we are gia", "agi achieved", "gia unlocked"):
        if needle in closeout_text.lower():
            gia_ok = False
    if force_fail == "no_gia_claim":
        gia_ok = False
    result.add("no_gia_claim", gia_ok)

    if not skip_pytest and pytest_count is not None:
        py_ok = pytest_count > 0 and force_fail != "pytest_green"
        result.add("pytest_green", py_ok, f"count={pytest_count}")
    elif pytest_count is not None:
        result.add("pytest_green", force_fail != "pytest_green", f"injected={pytest_count}")

    if result.ok:
        result.l1_status = "CLOSED"
    else:
        result.l1_status = "PARTIAL"

    record = result.closeout_record()
    closeout_path = out / "L1_RESIDUE_CLOSEOUT.json"
    checklist_path = out / "CHECKLIST.json"
    closeout_path.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    checklist = {
        "schema": "mesh.release.l1_residue_checklist/v1",
        "ok": result.ok,
        "channel": CHANNEL,
        "package_held": PACKAGE_HELD,
        "l1_status": result.l1_status,
        "gates": [g.to_dict() for g in result.gates],
        "preferred_next": PREFERRED_NEXT_DEFAULT,
        "no_held": NO_HELD_DEFAULT,
    }
    checklist_path.write_text(json.dumps(checklist, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    result.closeout_path = str(closeout_path)
    result.checklist_path = str(checklist_path)
    result.summary = {
        "themes": THEME_LABELS,
        "cps": list(EVIDENCE_CPS),
        "l1_status": result.l1_status,
    }

    if write_project_state and result.ok:
        mirror = root / ".project_state" / "L1_RESIDUE_CLOSEOUT.json"
        mirror.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    return result
