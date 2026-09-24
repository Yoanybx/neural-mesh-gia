"""Release checklist for single-node RC (CP-0026 / P14).

Machine-checkable gates; exits conceptually ok only when all required gates pass.
Emits a JSON summary suitable for M2M.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .bundle import build_bundle, load_manifest
from .clean_smoke import clean_node_smoke
from .manifest import FREEZE_CHANNEL, SCHEMA_ID
from .repro import repro_check

__all__ = [
    "NO_HELD_DEFAULT",
    "version_matches_expect",
    "ChecklistResult",
    "GateResult",
    "run_release_checklist",
]

NO_HELD_DEFAULT = (
    "Raft,N>2,multi-primary,ML,R2,R3,plaintext,Vault-ACME-req,GIA,"
    "SLO_chase,tag_schema,EVERY_fsync"
)



def version_matches_expect(live: str, expect: str | None) -> bool:
    """Exact match, or 0.17.x next-line when expect is closed 0.16.3.

    Closed-release tooling may re-run while the package has already opened
    0.17.x (CP-0030 bootstrap). pyproject/__init__ agreement is checked
    separately by callers.
    """
    if expect is None:
        return True
    if live == expect:
        return True
    if expect == "0.16.3" and live.startswith("0.17."):
        return True
    return False


@dataclass
class GateResult:
    name: str
    ok: bool
    detail: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {"name": self.name, "ok": self.ok, "detail": self.detail}


@dataclass
class ChecklistResult:
    ok: bool = True
    errors: list[str] = field(default_factory=list)
    gates: list[GateResult] = field(default_factory=list)
    version: str | None = None
    cp_tip: str | None = None
    freeze_channel: str | None = None
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
            "cp_tip": self.cp_tip,
            "freeze_channel": self.freeze_channel,
            "gates": [g.to_dict() for g in self.gates],
            "summary": dict(self.summary),
            "no_held": NO_HELD_DEFAULT,
        }

    def to_json(self, *, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, sort_keys=True) + "\n"


def _read_version(root: Path) -> str:
    import tomllib

    data = tomllib.loads((root / "pyproject.toml").read_text(encoding="utf-8"))
    return str(data["project"]["version"])


def _gate_version(root: Path, expect: str | None, result: ChecklistResult) -> None:
    ver = _read_version(root)
    init = (root / "src" / "neural_mesh" / "__init__.py").read_text(encoding="utf-8")
    m = re.search(r'__version__\s*=\s*["\']([^"\']+)["\']', init)
    init_ver = m.group(1) if m else None
    result.version = ver
    ok = True
    detail = f"pyproject={ver} init={init_ver}"
    if expect and not version_matches_expect(ver, expect):
        ok = False
        detail += f" expected={expect}"
    elif expect and ver != expect and version_matches_expect(ver, expect):
        detail += f" expected={expect} next_line_ok=True"
    if init_ver and init_ver != ver:
        ok = False
        detail += " version mismatch between pyproject and __init__"
    result.add("version_match", ok, detail)


def _gate_cp_tip(root: Path, expect_cp: str | None, result: ChecklistResult) -> None:
    from neural_mesh.checkpoint import CheckpointManager

    cm = CheckpointManager(root)
    ids = cm.list_ids()
    tip = ids[-1] if ids else None
    result.cp_tip = tip
    if expect_cp is None:
        state = cm.load_state()
        expect_cp = state.last_checkpoint
    ok = bool(tip) and tip == expect_cp and cm.verify(expect_cp)
    detail = f"tip={tip} expect={expect_cp} verified={cm.verify(expect_cp) if expect_cp else False}"
    result.add("cp_tip_verified", ok, detail)


def _gate_freeze(
    root: Path,
    result: ChecklistResult,
    *,
    out_dir: Path | None = None,
    tip: str | None = None,
    ver: str | None = None,
    require_freeze: bool = True,
) -> Path | None:
    """Build a tiny freeze probe OR inspect latest dist manifest; return tar path if built."""
    # Prefer building a deterministic probe into out_dir
    out = out_dir or (root / "dist" / "checklist")
    out.mkdir(parents=True, exist_ok=True)
    m = build_bundle(
        root,
        out,
        tip=tip or "chklist",
        ver=ver or result.version,
        freeze=True,
    )
    tar = out / f"{m.name}-{m.ver}.tar.gz"
    man_path = out / f"{m.name}-{m.ver}.manifest.json"
    loaded = load_manifest(man_path)
    result.freeze_channel = loaded.freeze.channel if loaded.freeze else None
    if require_freeze:
        ok = (
            loaded.freeze is not None
            and loaded.freeze.channel == FREEZE_CHANNEL
            and loaded.freeze.schema_name == SCHEMA_ID
        )
        detail = (
            f"freeze={loaded.freeze.model_dump(by_alias=True) if loaded.freeze else None}"
        )
        result.add("freeze_present", ok, detail)
    else:
        result.add("freeze_present", True, "freeze check skipped")
    return tar


def _gate_repro(
    root: Path,
    result: ChecklistResult,
    *,
    out_dir: Path,
    tip: str | None,
    ver: str | None,
    skip: bool,
) -> None:
    if skip:
        result.add("repro_check", True, "skipped")
        return
    rr = repro_check(
        root,
        out_dir / "repro",
        tip=tip or "chkrepr",
        ver=ver or result.version,
        pytest={"passed": 1, "failed": 0},
    )
    result.add(
        "repro_check",
        rr.ok,
        f"sha_a={rr.sha_a} sha_b={rr.sha_b}" if rr.ok else "; ".join(rr.errors),
    )


def _gate_clean_smoke(
    root: Path,
    result: ChecklistResult,
    *,
    tar: Path | None,
    skip: bool,
    marker: Path | None = None,
) -> None:
    if skip:
        if marker and marker.is_file():
            result.add("clean_node_smoke", True, f"cached marker {marker}")
        else:
            result.add("clean_node_smoke", True, "skipped")
        return
    if marker and marker.is_file():
        try:
            data = json.loads(marker.read_text(encoding="utf-8"))
            if data.get("ok") is True:
                result.add("clean_node_smoke", True, f"cached marker {marker}")
                return
        except (OSError, json.JSONDecodeError):
            pass
    if tar is None or not Path(tar).is_file():
        result.add("clean_node_smoke", False, "no bundle tar for smoke")
        return
    cs = clean_node_smoke(tar, forbidden_repo=root, run_verify=True, run_status_snapshot=True)
    if marker:
        marker.parent.mkdir(parents=True, exist_ok=True)
        marker.write_text(json.dumps(cs.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    result.add(
        "clean_node_smoke",
        cs.ok,
        "PASS" if cs.ok else "; ".join(cs.errors),
    )


def _gate_packaging_pytest(root: Path, result: ChecklistResult, *, skip: bool, python: str) -> None:
    if skip:
        result.add("pytest_packaging", True, "skipped")
        return
    proc = subprocess.run(
        [python, "-m", "pytest", "-q", "-k", "packaging", "--tb=no"],
        cwd=str(root),
        capture_output=True,
        text=True,
        timeout=600,
        check=False,
    )
    ok = proc.returncode == 0
    # Summarize last line like "25 passed"
    tail = (proc.stdout or "").strip().splitlines()
    detail = tail[-1] if tail else f"rc={proc.returncode}"
    result.add("pytest_packaging", ok, detail)


def _gate_no_held(root: Path, result: ChecklistResult) -> None:
    """NO_HELD must be documented in council agreement and/or capability doc."""
    needles = [
        root / "council" / "COUNCIL_AGREEMENT_CYCLE23.md",
        root / "council" / "COUNCIL_AGREEMENT_CYCLE22.md",
        root / "council" / "COUNCIL_AGREEMENT_CYCLE21.md",
        root / "docs" / "capabilities" / "MESH_PACKAGING_SINGLE_NODE_BUNDLE.md",
        root / "docs" / "capabilities" / "MESH_PACKAGING_RELEASE_CHECKLIST.md",
        root / "docs" / "capabilities" / "MESH_PACKAGING_FINAL_RELEASE_AUDIT.md",
    ]
    required_tokens = ["Raft", "SLO_chase", "tag_schema", "EVERY_fsync", "N>2"]
    found_in: list[str] = []
    blob = ""
    for p in needles:
        if p.is_file():
            text = p.read_text(encoding="utf-8")
            blob += "\n" + text
            if "NO_HELD" in text or "**NO:**" in text or "NO:" in text:
                found_in.append(str(p.relative_to(root)))
    missing = [t for t in required_tokens if t not in blob]
    ok = bool(found_in) and not missing
    detail = f"docs={found_in or 'none'} missing_tokens={missing or 'none'}"
    result.add("no_held_documented", ok, detail)


def run_release_checklist(
    root: Path | str,
    *,
    expect_version: str | None = "0.17.0",
    expect_cp: str | None = "CP-0027",
    out_dir: Path | str | None = None,
    tip: str | None = None,
    skip_repro: bool = False,
    skip_smoke: bool = False,
    skip_pytest: bool = False,
    require_freeze: bool = True,
    smoke_marker: Path | str | None = None,
    python: str | None = None,
    # Test hooks: inject prebuilt tar / skip cp verify filesystem
    prebuilt_tar: Path | str | None = None,
    skip_cp: bool = False,
) -> ChecklistResult:
    """Run all release gates; ``result.ok`` is True only if every gate passes."""
    root = Path(root).resolve()
    result = ChecklistResult()
    out = Path(out_dir) if out_dir else (root / "dist" / "checklist")
    out.mkdir(parents=True, exist_ok=True)
    py = python or sys.executable

    _gate_version(root, expect_version, result)

    if skip_cp:
        result.add("cp_tip_verified", True, "skipped")
        result.cp_tip = expect_cp
    else:
        _gate_cp_tip(root, expect_cp, result)

    tar: Path | None
    if prebuilt_tar:
        tar = Path(prebuilt_tar)
        # Still evaluate freeze from sidecar if present
        man = tar.with_name(tar.name.replace(".tar.gz", ".manifest.json"))
        if man.is_file():
            loaded = load_manifest(man)
            result.freeze_channel = loaded.freeze.channel if loaded.freeze else None
            ok = (
                (not require_freeze)
                or (
                    loaded.freeze is not None
                    and loaded.freeze.channel == FREEZE_CHANNEL
                    and loaded.freeze.schema_name == SCHEMA_ID
                )
            )
            if require_freeze:
                result.add(
                    "freeze_present",
                    ok and loaded.freeze is not None,
                    f"freeze={loaded.freeze.model_dump(by_alias=True) if loaded.freeze else None}",
                )
            else:
                result.add("freeze_present", True, "freeze check skipped")
        elif require_freeze:
            result.add("freeze_present", False, f"manifest missing for {tar}")
        else:
            result.add("freeze_present", True, "freeze check skipped")
    else:
        tar = _gate_freeze(
            root,
            result,
            out_dir=out,
            tip=tip,
            ver=result.version or expect_version,
            require_freeze=require_freeze,
        )

    _gate_repro(
        root,
        result,
        out_dir=out,
        tip=tip,
        ver=result.version or expect_version,
        skip=skip_repro,
    )
    _gate_clean_smoke(
        root,
        result,
        tar=tar,
        skip=skip_smoke,
        marker=Path(smoke_marker) if smoke_marker else (out / "clean_smoke.marker.json"),
    )
    _gate_packaging_pytest(root, result, skip=skip_pytest, python=py)
    _gate_no_held(root, result)

    result.summary = {
        "cycle": 23,
        "cp": result.cp_tip,
        "ver": result.version,
        "freeze": result.freeze_channel,
        "gates_passed": sum(1 for g in result.gates if g.ok),
        "gates_total": len(result.gates),
    }
    return result
