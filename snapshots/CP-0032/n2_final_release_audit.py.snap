#!/usr/bin/env python3
"""N2 final release audit (CP-0032 / P31).

Usage:
  .venv/bin/python scripts/n2_final_release_audit.py
  .venv/bin/python scripts/n2_final_release_audit.py --json --skip-pytest --packaging-n2-count 26
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[1]
_SRC = _REPO / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from neural_mesh.packaging import run_n2_final_release_audit  # noqa: E402
from neural_mesh.packaging.n2_final_release_audit import (  # noqa: E402
    EXPECTED_CP_N2,
    EXPECTED_VERSION_N2,
)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="N2 final RC release audit")
    p.add_argument("--root", type=Path, default=_REPO)
    p.add_argument("--out", type=Path, default=_REPO / "dist" / "n2_final_audit")
    p.add_argument("--report", type=Path, default=None)
    p.add_argument("--expect-version", default=EXPECTED_VERSION_N2)
    p.add_argument("--expect-cp", default=EXPECTED_CP_N2)
    p.add_argument("--tip", default=None)
    p.add_argument("--skip-verify", action="store_true")
    p.add_argument("--skip-soak", action="store_true", default=True)
    p.add_argument("--require-soak", action="store_true")
    p.add_argument("--soak-ok", type=lambda s: s.lower() in ("1", "true", "yes", "pass"), default=None)
    p.add_argument("--skip-pytest", action="store_true")
    p.add_argument("--skip-cp", action="store_true")
    p.add_argument("--packaging-n2-count", type=int, default=None)
    p.add_argument("--pytest-timeout", type=int, default=600)
    p.add_argument("--json", action="store_true")
    args = p.parse_args(argv)

    skip_soak = False if args.require_soak else args.skip_soak

    result = run_n2_final_release_audit(
        args.root,
        expect_version=args.expect_version,
        expect_cp=args.expect_cp,
        out_dir=args.out,
        tip=args.tip,
        skip_verify=args.skip_verify,
        skip_soak=skip_soak,
        soak_ok=args.soak_ok,
        skip_pytest=args.skip_pytest,
        skip_cp=args.skip_cp,
        packaging_n2_count=args.packaging_n2_count,
        pytest_timeout=args.pytest_timeout,
        report_path=args.report,
    )
    if args.json:
        print(result.to_json(), end="")
    else:
        status = "PASS" if result.ok else "FAIL"
        print(f"N2_FINAL_RELEASE_AUDIT: {status}")
        print(f"VERSION: {result.version}")
        print(f"CP_TIP: {result.cp_tip}")
        print(f"FREEZE: {result.freeze_channel}")
        print(f"SCHEMA: {result.schema}")
        print(f"PACKAGING_N2: {result.packaging_n2_count}")
        print(f"DUAL_PRIMARY: {result.dual_primary}")
        print(f"SOAK: {result.soak_ok}")
        for g in result.gates:
            mark = "OK" if g.ok else "FAIL"
            print(f"  [{mark}] {g.name}: {g.detail}")
        for e in result.errors:
            print(f"ERROR: {e}")
        if result.report_path:
            print(f"REPORT: {result.report_path}")
    return 0 if result.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
