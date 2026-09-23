#!/usr/bin/env python3
"""Final release audit (CP-0027 / P16).

Aggregate gate before calling RC release-ready. Exit nonzero on any fail.

Usage:
  .venv/bin/python scripts/final_release_audit.py
  .venv/bin/python scripts/final_release_audit.py --json --skip-pytest --packaging-count 48
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[1]
_SRC = _REPO / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from neural_mesh.packaging import run_final_release_audit  # noqa: E402
from neural_mesh.packaging.final_release_audit import EXPECTED_CP, EXPECTED_VERSION  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Final RC release audit")
    p.add_argument("--root", type=Path, default=_REPO)
    p.add_argument("--out", type=Path, default=_REPO / "dist" / "final_audit")
    p.add_argument("--report", type=Path, default=None)
    p.add_argument("--expect-version", default=EXPECTED_VERSION)
    p.add_argument("--expect-cp", default=EXPECTED_CP)
    p.add_argument("--tip", default=None)
    p.add_argument("--skip-repro", action="store_true")
    p.add_argument("--skip-smoke", action="store_true", default=True)
    p.add_argument("--run-smoke", action="store_true")
    p.add_argument("--skip-pytest", action="store_true")
    p.add_argument("--skip-cp", action="store_true")
    p.add_argument("--skip-checklist", action="store_true")
    p.add_argument("--packaging-count", type=int, default=None)
    p.add_argument("--pytest-timeout", type=int, default=600)
    p.add_argument("--json", action="store_true")
    args = p.parse_args(argv)

    result = run_final_release_audit(
        args.root,
        expect_version=args.expect_version,
        expect_cp=args.expect_cp,
        out_dir=args.out,
        tip=args.tip,
        skip_repro=args.skip_repro,
        skip_smoke=not args.run_smoke if args.run_smoke else args.skip_smoke,
        skip_pytest=args.skip_pytest,
        skip_cp=args.skip_cp,
        skip_checklist=args.skip_checklist,
        packaging_count=args.packaging_count,
        pytest_timeout=args.pytest_timeout,
        report_path=args.report,
    )
    if args.json:
        print(result.to_json(), end="")
    else:
        status = "PASS" if result.ok else "FAIL"
        print(f"FINAL_RELEASE_AUDIT: {status}")
        print(f"VERSION: {result.version}")
        print(f"CP_TIP: {result.cp_tip}")
        print(f"FREEZE: {result.freeze_channel}")
        print(f"PACKAGING: {result.packaging_count}")
        print(f"DUAL_PRIMARY: {result.dual_primary}")
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
