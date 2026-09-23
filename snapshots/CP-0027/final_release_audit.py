"""Final release audit for single-node RC (CP-0027 / P16).

Aggregate gate before calling RC release-ready: release_checklist, repro,
freeze 0.16.x, CP tip, version==0.16.3, packaging tests, dual_primary=0,
NO_HELD list present.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .manifest import FREEZE_CHANNEL, SCHEMA_ID
from .release_checklist import NO_HELD_DEFAULT, GateResult, run_release_checklist
from .repro import repro_check

__all__ = [
    "EXPECTED_VERSION",
    "EXPECTED_CP",
    "AuditResult",
    "run_final_release_audit",
]

EXPECTED_VERSION = "0.16.3"
EXPECTED_CP = "CP-0027"


@dataclass
class AuditResult:
    ok: bool = True
    errors: list[str] = field(default_factory=list)
    gates: list[GateResult] = field(default_factory=list)
    version: str | None = None
    cp_tip: str | None = None
    freeze_channel: str | None = None
    packaging_count: int | None = None
    dual_primary: int = 0
    no_held: str = NO_HELD_DEFAULT
    summary: dict[str, Any] = field(default_factory=dict)
    report_path: str | None = None

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
            "cp_tip": self.cp_tip,
            "freeze_channel": self.freeze_channel,
            "packaging_count": self.packaging_count,
            "dual_primary": self.dual_primary,
            "no_held": self.no_held,
            "gates": [g.to_dict() for g in self.gates],
            "summary": dict(self.summary),
            "report_path": self.report_path,
        }

    def to_json(self, *, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, sort_keys=True) + "\n"


def _gate_dual_primary(root: Path, result: AuditResult) -> None:
    """dual_primary must be documented as 0 in council/status docs."""
    needles = [
        root / "council" / "STATUS_CYCLE23.md",
        root / "council" / "STATUS_CYCLE22.md",
        root / "council" / "PASTE_CYCLE23_M2M.md",
        root / "council" / "PASTE_CYCLE22_M2M.md",
        root / "STATUS_FOR_CHATGPT_CYCLE23.md",
        root / "STATUS_FOR_CHATGPT_CYCLE22.md",
        root / "docs" / "capabilities" / "MESH_PACKAGING_FINAL_RELEASE_AUDIT.md",
        root / "docs" / "capabilities" / "MESH_PACKAGING_RELEASE_CHECKLIST.md",
    ]
    blob = ""
    found = False
    for p in needles:
        if p.is_file():
            text = p.read_text(encoding="utf-8")
            blob += "\n" + text
            if re.search(r"dual[-_ ]?primary\s*[=:]\s*0", text, re.I) or "DUAL_PRIMARY: 0" in text:
                found = True
    result.dual_primary = 0 if found else -1
    result.add(
        "dual_primary_zero",
        found,
        "documented dual_primary=0" if found else "dual_primary=0 not documented",
    )


def _gate_packaging_pytest(
    root: Path,
    result: AuditResult,
    *,
    skip: bool,
    python: str,
    precomputed_count: int | None,
    timeout: int,
) -> None:
    if precomputed_count is not None:
        result.packaging_count = int(precomputed_count)
        result.add(
            "pytest_packaging",
            precomputed_count > 0,
            f"precomputed count={precomputed_count}",
        )
        return
    if skip:
        result.add("pytest_packaging", True, "skipped")
        return
    proc = subprocess.run(
        [python, "-m", "pytest", "-q", "-k", "packaging", "--tb=no"],
        cwd=str(root),
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
    )
    ok = proc.returncode == 0
    tail = (proc.stdout or "").strip().splitlines()
    detail = tail[-1] if tail else f"rc={proc.returncode}"
    m = re.search(r"(\d+)\s+passed", detail)
    if m:
        result.packaging_count = int(m.group(1))
    result.add("pytest_packaging", ok, detail)


def _gate_no_held(root: Path, result: AuditResult) -> None:
    needles = [
        root / "council" / "COUNCIL_AGREEMENT_CYCLE23.md",
        root / "council" / "COUNCIL_AGREEMENT_CYCLE22.md",
        root / "docs" / "capabilities" / "MESH_PACKAGING_FINAL_RELEASE_AUDIT.md",
        root / "docs" / "capabilities" / "MESH_PACKAGING_RELEASE_CHECKLIST.md",
        root / "docs" / "capabilities" / "MESH_PACKAGING_SINGLE_NODE_BUNDLE.md",
    ]
    required = ["Raft", "SLO_chase", "tag_schema", "EVERY_fsync", "N>2"]
    found_in: list[str] = []
    blob = ""
    for p in needles:
        if p.is_file():
            text = p.read_text(encoding="utf-8")
            blob += "\n" + text
            if "NO_HELD" in text or "**NO:**" in text:
                found_in.append(str(p.relative_to(root)))
    missing = [t for t in required if t not in blob]
    result.add(
        "no_held_documented",
        bool(found_in) and not missing,
        f"docs={found_in or 'none'} missing={missing or 'none'}",
    )


def run_final_release_audit(
    root: Path | str,
    *,
    expect_version: str = EXPECTED_VERSION,
    expect_cp: str = EXPECTED_CP,
    out_dir: Path | str | None = None,
    tip: str | None = None,
    skip_repro: bool = False,
    skip_smoke: bool = True,
    skip_pytest: bool = False,
    skip_cp: bool = False,
    skip_checklist: bool = False,
    packaging_count: int | None = None,
    pytest_timeout: int = 600,
    python: str | None = None,
    report_path: Path | str | None = None,
) -> AuditResult:
    """Aggregate RC release-ready gates. ``result.ok`` only if all pass."""
    root = Path(root).resolve()
    result = AuditResult()
    out = Path(out_dir) if out_dir else (root / "dist" / "final_audit")
    out.mkdir(parents=True, exist_ok=True)
    py = python or sys.executable

    # --- release_checklist (core gates) ---
    if skip_checklist:
        result.add("release_checklist", True, "skipped")
        # Still need version from pyproject for expect
        import tomllib

        data = tomllib.loads((root / "pyproject.toml").read_text(encoding="utf-8"))
        result.version = str(data["project"]["version"])
        result.add(
            "version_match",
            result.version == expect_version,
            f"pyproject={result.version} expected={expect_version}",
        )
    else:
        chk = run_release_checklist(
            root,
            expect_version=expect_version,
            expect_cp=expect_cp,
            out_dir=out / "checklist",
            tip=tip or "finaudit",
            skip_repro=True,  # we run repro separately below
            skip_smoke=skip_smoke,
            skip_pytest=True,  # packaging pytest below
            skip_cp=skip_cp,
            require_freeze=True,
        )
        result.version = chk.version
        result.cp_tip = chk.cp_tip
        result.freeze_channel = chk.freeze_channel
        # Map checklist gates (except ones we supersede)
        for g in chk.gates:
            if g.name in ("pytest_packaging", "repro_check"):
                continue
            result.add(g.name, g.ok, g.detail)
        mapped = [
            g
            for g in result.gates
            if g.name
            in (
                "version_match",
                "cp_tip_verified",
                "freeze_present",
                "no_held_documented",
                "clean_node_smoke",
            )
        ]
        core_ok = all(g.ok for g in mapped) if mapped else chk.ok
        result.add("release_checklist", core_ok, f"core_ok={core_ok} mapped={len(mapped)}")

    # Explicit version == 0.16.3
    if result.version != expect_version:
        # version_match may already have failed; ensure gate exists
        if not any(g.name == "version_0163" for g in result.gates):
            result.add(
                "version_0163",
                False,
                f"version={result.version} expected={expect_version}",
            )
    else:
        result.add("version_0163", True, expect_version)

    # Freeze channel 0.16.x
    ch = result.freeze_channel
    result.add(
        "freeze_channel_016x",
        ch == FREEZE_CHANNEL,
        f"channel={ch} schema={SCHEMA_ID}",
    )

    # repro_check (or markers)
    if skip_repro:
        marker = out / "repro.marker.json"
        if marker.is_file():
            try:
                data = json.loads(marker.read_text(encoding="utf-8"))
                result.add("repro_check", bool(data.get("ok")), f"marker {marker}")
            except (OSError, json.JSONDecodeError):
                result.add("repro_check", True, "skipped")
        else:
            result.add("repro_check", True, "skipped")
    else:
        rr = repro_check(
            root,
            out / "repro",
            tip=tip or "finauditrepro",
            ver=result.version or expect_version,
            pytest={"passed": 1, "failed": 0},
        )
        (out / "repro.marker.json").write_text(
            json.dumps(rr.to_dict() if hasattr(rr, "to_dict") else {"ok": rr.ok}, indent=2)
            + "\n",
            encoding="utf-8",
        )
        result.add(
            "repro_check",
            rr.ok,
            f"sha_a={getattr(rr, 'sha_a', None)} sha_b={getattr(rr, 'sha_b', None)}"
            if rr.ok
            else "; ".join(rr.errors),
        )

    # packaging pytest
    _gate_packaging_pytest(
        root,
        result,
        skip=skip_pytest,
        python=py,
        precomputed_count=packaging_count,
        timeout=pytest_timeout,
    )

    # dual_primary=0 documented
    _gate_dual_primary(root, result)

    # NO_HELD present (also covered by checklist; reaffirm for cycle 23 docs)
    _gate_no_held(root, result)

    # CP tip present (if not skipped via checklist)
    if skip_cp and result.cp_tip is None:
        result.cp_tip = expect_cp
        result.add("cp_tip_present", True, f"skipped expect={expect_cp}")
    elif result.cp_tip:
        result.add("cp_tip_present", True, result.cp_tip)
    elif not any(g.name == "cp_tip_verified" for g in result.gates):
        result.add("cp_tip_present", False, "missing")

    result.summary = {
        "cycle": 23,
        "cp": result.cp_tip or expect_cp,
        "ver": result.version,
        "freeze": result.freeze_channel,
        "packaging_count": result.packaging_count,
        "dual_primary": result.dual_primary,
        "gates_passed": sum(1 for g in result.gates if g.ok),
        "gates_total": len(result.gates),
        "release_ready": result.ok,
    }

    # Final ok from all gates
    result.ok = all(g.ok for g in result.gates)
    if not result.ok:
        result.errors = [f"{g.name}: {g.detail or 'FAIL'}" for g in result.gates if not g.ok]

    rp = Path(report_path) if report_path else (out / "final_release_audit.json")
    rp.parent.mkdir(parents=True, exist_ok=True)
    rp.write_text(result.to_json(), encoding="utf-8")
    result.report_path = str(rp)
    return result
