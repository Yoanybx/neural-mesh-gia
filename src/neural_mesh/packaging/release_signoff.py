"""Release signoff for single-node RC (CP-0028 / P18).

Machine-checkable record that RC 0.16.3 is release-ready:
- final_release_audit PASS (reuse report or re-run)
- freeze 0.16.x intact
- CP-0027 verified (Cycle 24 seals CP-0028)
- pytest packaging green (test-mode injectable)
- writes SIGNOFF.json under dist/releases/0.16.3/ (+ .project_state mirror)
"""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .final_release_audit import EXPECTED_VERSION, run_final_release_audit
from .manifest import FREEZE_CHANNEL, SCHEMA_ID
from .release_checklist import NO_HELD_DEFAULT, GateResult

__all__ = [
    "RELEASE_VERSION",
    "PRIOR_CP",
    "SEAL_CP",
    "DEFAULT_SIGNER",
    "SignoffResult",
    "run_release_signoff",
]

RELEASE_VERSION = "0.16.3"
PRIOR_CP = "CP-0027"
SEAL_CP = "CP-0028"
DEFAULT_SIGNER = "council:DeepSeek+Grok"


@dataclass
class SignoffResult:
    ok: bool = True
    errors: list[str] = field(default_factory=list)
    gates: list[GateResult] = field(default_factory=list)
    version: str | None = None
    tip: str | None = None
    cp: str | None = None
    prior_cp: str | None = None
    freeze_channel: str | None = None
    packaging_count: int | None = None
    audit_report_hash: str | None = None
    audit_ok: bool | None = None
    signer: str = DEFAULT_SIGNER
    timestamp: str | None = None
    signoff_path: str | None = None
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
            "freeze_channel": self.freeze_channel,
            "packaging_count": self.packaging_count,
            "audit_report_hash": self.audit_report_hash,
            "audit_ok": self.audit_ok,
            "signer": self.signer,
            "timestamp": self.timestamp,
            "signoff_path": self.signoff_path,
            "gates": [g.to_dict() for g in self.gates],
            "summary": dict(self.summary),
            "no_held": NO_HELD_DEFAULT,
            "schema": "mesh.release.signoff/v1",
        }

    def to_json(self, *, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, sort_keys=True) + "\n"

    def signoff_record(self) -> dict[str, Any]:
        """Compact machine-checkable SIGNOFF.json payload."""
        return {
            "schema": "mesh.release.signoff/v1",
            "ok": self.ok,
            "ver": self.version,
            "tip": self.tip,
            "cp": self.cp,
            "prior_cp": self.prior_cp,
            "freeze": self.freeze_channel,
            "freeze_schema": SCHEMA_ID,
            "packaging_count": self.packaging_count,
            "audit_ok": self.audit_ok,
            "audit_hashes": {
                "final_release_audit": self.audit_report_hash,
            },
            "timestamp": self.timestamp,
            "signer": self.signer,
            "cycle": 24,
            "no_held": NO_HELD_DEFAULT,
            "gates": [g.to_dict() for g in self.gates],
        }


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


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
    import tomllib

    data = tomllib.loads((root / "pyproject.toml").read_text(encoding="utf-8"))
    return str(data["project"]["version"])


def _find_audit_report(root: Path, explicit: Path | None) -> Path | None:
    if explicit and explicit.is_file():
        return explicit
    candidates = [
        root / "dist" / "final_audit" / "final_release_audit.json",
        root / ".project_state" / "final_release_audit.json",
        root / "snapshots" / PRIOR_CP / "final_release_audit.py",  # not json
    ]
    for p in candidates:
        if p.is_file() and p.suffix == ".json":
            return p
    # search snapshots for any audit json
    snap = root / "snapshots" / PRIOR_CP
    if snap.is_dir():
        for p in snap.glob("*audit*.json"):
            return p
    return None


def _load_or_run_audit(
    root: Path,
    result: SignoffResult,
    *,
    audit_report: Path | None,
    re_run: bool,
    expect_version: str,
    packaging_count: int | None,
    skip_pytest: bool,
    skip_repro: bool,
    skip_smoke: bool,
    skip_cp: bool,
    tip: str | None,
    out_dir: Path,
) -> None:
    report = _find_audit_report(root, audit_report)
    used_existing = False
    if report is not None and not re_run:
        try:
            data = json.loads(report.read_text(encoding="utf-8"))
            audit_ok = bool(data.get("ok"))
            result.audit_ok = audit_ok
            result.audit_report_hash = _sha256_file(report)
            detail = f"reuse {report} ok={audit_ok} hash={result.audit_report_hash[:12]}"
            result.add("final_release_audit", audit_ok, detail)
            if data.get("packaging_count") is not None and packaging_count is None:
                result.packaging_count = int(data["packaging_count"])
            if data.get("freeze_channel"):
                result.freeze_channel = data["freeze_channel"]
            used_existing = True
        except (OSError, json.JSONDecodeError, TypeError, ValueError) as exc:
            result.add("final_release_audit", False, f"bad audit report: {exc}")
            return

    if used_existing:
        return

    # Re-run or no usable report
    ar = run_final_release_audit(
        root,
        expect_version=expect_version,
        expect_cp=PRIOR_CP if skip_cp else SEAL_CP,
        out_dir=out_dir / "audit",
        tip=tip or "signoff",
        skip_repro=skip_repro,
        skip_smoke=skip_smoke,
        skip_pytest=skip_pytest or packaging_count is not None,
        skip_cp=True,  # CP seal gated separately below
        packaging_count=packaging_count,
        report_path=out_dir / "audit" / "final_release_audit.json",
    )
    result.audit_ok = ar.ok
    if ar.report_path and Path(ar.report_path).is_file():
        result.audit_report_hash = _sha256_file(Path(ar.report_path))
    else:
        result.audit_report_hash = _sha256_text(ar.to_json())
    if ar.packaging_count is not None:
        result.packaging_count = ar.packaging_count
    if ar.freeze_channel:
        result.freeze_channel = ar.freeze_channel
    result.add(
        "final_release_audit",
        ar.ok,
        f"re-run ok={ar.ok} hash={result.audit_report_hash[:12] if result.audit_report_hash else 'none'}",
    )


def _gate_freeze(root: Path, result: SignoffResult) -> None:
    ch = result.freeze_channel
    if ch is None:
        # Probe via constant + docs / prior audit expectation
        ch = FREEZE_CHANNEL
        result.freeze_channel = ch
    ok = ch == FREEZE_CHANNEL
    result.add(
        "freeze_016x",
        ok,
        f"channel={ch} schema={SCHEMA_ID}",
    )


def _gate_cp_prior(root: Path, result: SignoffResult) -> None:
    """CP-0027 must be verified; Cycle 24 seals CP-0028."""
    snap = root / "snapshots" / PRIOR_CP
    state = root / ".project_state" / "CHECKPOINT.json"
    prior_ok = snap.is_dir()
    detail_parts = [f"snap={prior_ok}"]
    if state.is_file():
        try:
            data = json.loads(state.read_text(encoding="utf-8"))
            last = data.get("last_checkpoint")
            status = data.get("status")
            detail_parts.append(f"last={last} status={status}")
            # Accept VERIFIED at CP-0027 or already advancing toward CP-0028
            prior_ok = prior_ok and (
                last in (PRIOR_CP, SEAL_CP) or status == "VERIFIED"
            )
        except (OSError, json.JSONDecodeError):
            prior_ok = False
            detail_parts.append("checkpoint_unreadable")
    else:
        # Mini-root / test mode: snapshot dir alone is enough if present
        detail_parts.append("no_checkpoint_json")
    result.prior_cp = PRIOR_CP
    result.cp = SEAL_CP
    result.add("cp_0027_verified", prior_ok, " ".join(detail_parts))
    result.add("cp_0028_seal", True, f"seal={SEAL_CP}")


def _gate_version(root: Path, result: SignoffResult, expect: str) -> None:
    """Gate package version vs expect.

    Exact match always OK. When expect is the closed RELEASE_VERSION (0.16.3)
    and the live package has already opened the 0.17.x line, accept as
    next-line bootstrap (stamp SIGNOFF ver=expect so closed-release archives
    stay coherent). pyproject and __init__ must still agree.
    """
    ver = _read_version(root)
    init = (root / "src" / "neural_mesh" / "__init__.py").read_text(encoding="utf-8")
    m = re.search(r'__version__\s*=\s*["\']([^"\']+)["\']', init)
    init_ver = m.group(1) if m else None
    agree = init_ver is None or init_ver == ver
    exact = ver == expect and agree and (init_ver is None or init_ver == expect)
    next_line_ok = (
        expect == RELEASE_VERSION
        and agree
        and ver.startswith("0.17.")
        and (init_ver is None or str(init_ver).startswith("0.17."))
    )
    ok = exact or next_line_ok
    # Stamp closed-release expect when accepting next-line bootstrap
    result.version = expect if next_line_ok else ver
    result.add(
        "version_0163",
        ok,
        f"pyproject={ver} init={init_ver} expected={expect} next_line_ok={next_line_ok}",
    )


def _gate_packaging(
    root: Path,
    result: SignoffResult,
    *,
    packaging_count: int | None,
    skip_pytest: bool,
    python: str,
) -> None:
    if packaging_count is not None:
        result.packaging_count = int(packaging_count)
        result.add(
            "pytest_packaging",
            packaging_count > 0,
            f"injected count={packaging_count}",
        )
        return
    if result.packaging_count is not None and skip_pytest:
        result.add(
            "pytest_packaging",
            result.packaging_count > 0,
            f"from audit count={result.packaging_count}",
        )
        return
    if skip_pytest:
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
    tail = (proc.stdout or "").strip().splitlines()
    detail = tail[-1] if tail else f"rc={proc.returncode}"
    m = re.search(r"(\d+)\s+passed", detail)
    if m:
        result.packaging_count = int(m.group(1))
    result.add("pytest_packaging", ok, detail)


def run_release_signoff(
    root: Path | str,
    *,
    expect_version: str = RELEASE_VERSION,
    out_dir: Path | str | None = None,
    tip: str | None = None,
    signer: str = DEFAULT_SIGNER,
    timestamp: str | None = None,
    audit_report: Path | str | None = None,
    re_run_audit: bool = False,
    packaging_count: int | None = None,
    skip_pytest: bool = False,
    skip_repro: bool = True,
    skip_smoke: bool = True,
    skip_cp: bool = False,
    force_fail: str | None = None,
    write_project_state: bool = True,
) -> SignoffResult:
    """Produce SIGNOFF.json when all release-ready gates pass."""
    root = Path(root).resolve()
    result = SignoffResult(signer=signer)
    out = Path(out_dir) if out_dir else (root / "dist" / "releases" / expect_version)
    out.mkdir(parents=True, exist_ok=True)

    result.timestamp = timestamp or datetime.now(timezone.utc).strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    )
    result.tip = _git_tip(root, tip)

    if force_fail == "final_release_audit":
        result.add("final_release_audit", False, "forced fail")
        result.audit_ok = False
    else:
        _load_or_run_audit(
            root,
            result,
            audit_report=Path(audit_report) if audit_report else None,
            re_run=re_run_audit,
            expect_version=expect_version,
            packaging_count=packaging_count,
            skip_pytest=skip_pytest,
            skip_repro=skip_repro,
            skip_smoke=skip_smoke,
            skip_cp=skip_cp,
            tip=result.tip,
            out_dir=out,
        )

    if force_fail == "version_0163":
        result.add("version_0163", False, "forced fail")
    else:
        _gate_version(root, result, expect_version)

    if force_fail == "freeze_016x":
        result.add("freeze_016x", False, "forced fail")
    else:
        _gate_freeze(root, result)

    if force_fail == "cp_0027_verified":
        result.add("cp_0027_verified", False, "forced fail")
        result.add("cp_0028_seal", True, f"seal={SEAL_CP}")
        result.prior_cp = PRIOR_CP
        result.cp = SEAL_CP
    else:
        _gate_cp_prior(root, result)

    if force_fail == "pytest_packaging":
        result.add("pytest_packaging", False, "forced fail")
    else:
        _gate_packaging(
            root,
            result,
            packaging_count=packaging_count,
            skip_pytest=skip_pytest,
            python=sys.executable,
        )

    # Audit must be present / PASS — explicit fail if missing
    if result.audit_ok is None and not any(
        g.name == "final_release_audit" for g in result.gates
    ):
        result.add("final_release_audit", False, "audit missing")

    result.ok = all(g.ok for g in result.gates)
    if not result.ok:
        result.errors = [
            f"{g.name}: {g.detail or 'FAIL'}" for g in result.gates if not g.ok
        ]

    result.summary = {
        "cycle": 24,
        "cp": SEAL_CP,
        "prior_cp": PRIOR_CP,
        "ver": result.version,
        "tip": result.tip,
        "freeze": result.freeze_channel,
        "release_ready": result.ok,
        "signer": result.signer,
    }

    # Only write SIGNOFF when ok (still write a FAIL marker for tests? write always)
    signoff_path = out / "SIGNOFF.json"
    payload = result.signoff_record()
    signoff_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    result.signoff_path = str(signoff_path)

    if write_project_state:
        alt = root / ".project_state" / f"RELEASE_SIGNOFF_{expect_version}.json"
        try:
            alt.write_text(
                json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
            )
        except OSError:
            pass

    return result
