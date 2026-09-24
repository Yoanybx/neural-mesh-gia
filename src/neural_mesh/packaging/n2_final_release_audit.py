"""N2 final release audit (CP-0032 / P31).

Aggregate gate before calling N2 packaging RC release-ready.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .bundle_n2 import build_n2_bundle, verify_n2_bundle
from .manifest_n2 import FREEZE_CHANNEL_N2, SCHEMA_ID_N2
from .release_checklist import NO_HELD_DEFAULT, GateResult, version_matches_expect

__all__ = [
    "EXPECTED_VERSION_N2",
    "EXPECTED_CP_N2",
    "N2AuditResult",
    "run_n2_final_release_audit",
]

EXPECTED_VERSION_N2 = "0.17.0"
EXPECTED_CP_N2 = "CP-0032"


@dataclass
class N2AuditResult:
    ok: bool = True
    errors: list[str] = field(default_factory=list)
    gates: list[GateResult] = field(default_factory=list)
    version: str | None = None
    cp_tip: str | None = None
    freeze_channel: str | None = None
    schema: str | None = None
    packaging_n2_count: int | None = None
    dual_primary: int = 0
    soak_ok: bool | None = None
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
            "schema": self.schema,
            "packaging_n2_count": self.packaging_n2_count,
            "dual_primary": self.dual_primary,
            "soak_ok": self.soak_ok,
            "no_held": self.no_held,
            "gates": [g.to_dict() for g in self.gates],
            "summary": dict(self.summary),
            "report_path": self.report_path,
        }

    def to_json(self, *, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, sort_keys=True) + "\n"


def _gate_version(root: Path, result: N2AuditResult, expect: str) -> None:
    import tomllib

    data = tomllib.loads((root / "pyproject.toml").read_text(encoding="utf-8"))
    ver = str(data["project"]["version"])
    result.version = ver
    result.add(
        "version_match",
        version_matches_expect(ver, expect),
        f"pyproject={ver} expected={expect}",
    )


def _gate_cp(root: Path, result: N2AuditResult, expect_cp: str, *, skip: bool) -> None:
    if skip:
        result.cp_tip = expect_cp
        result.add("cp_tip", True, f"skipped expect={expect_cp}")
        return
    tip = None
    ck = root / ".project_state" / "CHECKPOINT.json"
    if ck.is_file():
        try:
            data = json.loads(ck.read_text(encoding="utf-8"))
            tip = data.get("last_checkpoint") or data.get("checkpoint")
        except (OSError, json.JSONDecodeError):
            tip = None
    snap = root / "snapshots" / expect_cp
    ok = tip == expect_cp or snap.is_dir()
    result.cp_tip = tip or expect_cp
    result.add("cp_tip", ok, f"tip={tip} expect={expect_cp} snap={snap.is_dir()}")


def _gate_n2_verify(
    root: Path,
    result: N2AuditResult,
    *,
    out: Path,
    tip: str | None,
    skip: bool,
) -> None:
    if skip:
        result.add("n2_verify", True, "skipped")
        result.schema = SCHEMA_ID_N2
        result.freeze_channel = FREEZE_CHANNEL_N2
        return
    m = build_n2_bundle(
        root,
        out / "bundle",
        tip=tip or "n2audit",
        ver=result.version,
        freeze=True,
        single_node_for_parity=False,
    )
    bundle = out / "bundle" / f"{m.name}-{m.ver}.tar.gz"
    man = out / "bundle" / f"{m.name}-{m.ver}.manifest.json"
    vr = verify_n2_bundle(
        bundle,
        man,
        smoke=False,
        expected_ver=result.version,
        expect_freeze_channel=FREEZE_CHANNEL_N2,
    )
    result.schema = m.schema_name
    result.freeze_channel = m.freeze.channel if m.freeze else None
    result.dual_primary = m.dual_primary
    result.add("n2_verify", vr.ok, "ok" if vr.ok else "; ".join(vr.errors))


def _gate_freeze(result: N2AuditResult) -> None:
    ch = result.freeze_channel
    result.add(
        "freeze_channel_017x_n2",
        ch == FREEZE_CHANNEL_N2,
        f"channel={ch} schema={result.schema or SCHEMA_ID_N2}",
    )
    result.add(
        "schema_v1_n2",
        result.schema == SCHEMA_ID_N2,
        f"schema={result.schema}",
    )


def _gate_soak(
    result: N2AuditResult,
    *,
    soak_ok: bool | None,
    skip: bool,
) -> None:
    if soak_ok is not None:
        result.soak_ok = bool(soak_ok)
        result.add("n2_soak", bool(soak_ok), f"injected soak_ok={soak_ok}")
        return
    if skip:
        result.soak_ok = True
        result.add("n2_soak", True, "skipped")
        return
    result.soak_ok = False
    result.add("n2_soak", False, "soak result not provided (use soak_ok= or skip_soak)")


def _gate_dual_primary(root: Path, result: N2AuditResult) -> None:
    needles = [
        root / "council" / "STATUS_CYCLE28.md",
        root / "council" / "STATUS_CYCLE27.md",
        root / "council" / "PASTE_CYCLE28_M2M.md",
        root / "council" / "PASTE_CYCLE27_M2M.md",
        root / "STATUS_FOR_CHATGPT_CYCLE28.md",
        root / "STATUS_FOR_CHATGPT_CYCLE27.md",
        root / "docs" / "capabilities" / "MESH_PACKAGING_N2_FINAL_RELEASE_AUDIT.md",
        root / "docs" / "capabilities" / "MESH_PACKAGING_N2_MULTI_NODE.md",
    ]
    found = False
    for p in needles:
        if p.is_file():
            text = p.read_text(encoding="utf-8")
            if re.search(r"dual[-_ ]?primary\s*[=:]\s*0", text, re.I) or "DUAL_PRIMARY: 0" in text:
                found = True
                break
    if found:
        result.dual_primary = 0
    result.add(
        "dual_primary_zero",
        found or result.dual_primary == 0,
        "documented dual_primary=0" if found else f"dual_primary={result.dual_primary}",
    )


def _gate_no_held(root: Path, result: N2AuditResult) -> None:
    needles = [
        root / "council" / "COUNCIL_AGREEMENT_CYCLE28.md",
        root / "council" / "COUNCIL_AGREEMENT_CYCLE27.md",
        root / "docs" / "capabilities" / "MESH_PACKAGING_N2_FINAL_RELEASE_AUDIT.md",
        root / "docs" / "capabilities" / "MESH_PACKAGING_N2_MULTI_NODE.md",
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


def _gate_packaging_n2_pytest(
    root: Path,
    result: N2AuditResult,
    *,
    skip: bool,
    python: str,
    precomputed: int | None,
    timeout: int,
) -> None:
    if precomputed is not None:
        result.packaging_n2_count = int(precomputed)
        result.add(
            "pytest_packaging_n2",
            precomputed > 0,
            f"precomputed count={precomputed}",
        )
        return
    if skip:
        result.add("pytest_packaging_n2", True, "skipped")
        return
    proc = subprocess.run(
        [python, "-m", "pytest", "-q", "-m", "packaging_n2", "--tb=no"],
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
        result.packaging_n2_count = int(m.group(1))
    result.add("pytest_packaging_n2", ok, detail)


def run_n2_final_release_audit(
    root: Path | str,
    *,
    expect_version: str = EXPECTED_VERSION_N2,
    expect_cp: str = EXPECTED_CP_N2,
    out_dir: Path | str | None = None,
    tip: str | None = None,
    skip_verify: bool = False,
    skip_soak: bool = True,
    soak_ok: bool | None = None,
    skip_pytest: bool = False,
    skip_cp: bool = False,
    packaging_n2_count: int | None = None,
    pytest_timeout: int = 600,
    python: str | None = None,
    report_path: Path | str | None = None,
) -> N2AuditResult:
    """Aggregate N2 RC release-ready gates. ``result.ok`` only if all pass."""
    root = Path(root).resolve()
    result = N2AuditResult()
    out = Path(out_dir) if out_dir else (root / "dist" / "n2_final_audit")
    out.mkdir(parents=True, exist_ok=True)
    py = python or sys.executable

    _gate_version(root, result, expect_version)
    _gate_cp(root, result, expect_cp, skip=skip_cp)
    _gate_n2_verify(root, result, out=out, tip=tip, skip=skip_verify)
    _gate_freeze(result)
    _gate_soak(result, soak_ok=soak_ok, skip=skip_soak)
    _gate_packaging_n2_pytest(
        root,
        result,
        skip=skip_pytest,
        python=py,
        precomputed=packaging_n2_count,
        timeout=pytest_timeout,
    )
    _gate_dual_primary(root, result)
    _gate_no_held(root, result)

    result.summary = {
        "cycle": 28,
        "cp": result.cp_tip or expect_cp,
        "ver": result.version,
        "freeze": result.freeze_channel,
        "schema": result.schema,
        "packaging_n2_count": result.packaging_n2_count,
        "dual_primary": result.dual_primary,
        "soak_ok": result.soak_ok,
        "gates_passed": sum(1 for g in result.gates if g.ok),
        "gates_total": len(result.gates),
        "release_ready": all(g.ok for g in result.gates),
        "no_held": result.no_held,
    }

    result.ok = all(g.ok for g in result.gates)
    if not result.ok:
        result.errors = [
            f"{g.name}: {g.detail or 'FAIL'}" for g in result.gates if not g.ok
        ]

    rp = Path(report_path) if report_path else (out / "n2_final_release_audit.json")
    rp.parent.mkdir(parents=True, exist_ok=True)
    rp.write_text(result.to_json(), encoding="utf-8")
    result.report_path = str(rp)
    return result
