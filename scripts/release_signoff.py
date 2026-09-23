#!/usr/bin/env python3
"""Release signoff (CP-0028 / P18).

Machine-checkable SIGNOFF that RC 0.16.3 is release-ready.

Usage:
  .venv/bin/python scripts/release_signoff.py
  .venv/bin/python scripts/release_signoff.py --json --packaging-count 53 --skip-pytest
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[1]
_SRC = _REPO / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from neural_mesh.packaging import run_release_signoff  # noqa: E402
from neural_mesh.packaging.release_signoff import (  # noqa: E402
    DEFAULT_SIGNER,
    RELEASE_VERSION,
)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="RC release signoff")
    p.add_argument("--root", type=Path, default=_REPO)
    p.add_argument(
        "--out",
        type=Path,
        default=None,
        help="Default: dist/releases/<ver>/",
    )
    p.add_argument("--expect-version", default=RELEASE_VERSION)
    p.add_argument("--tip", default=None)
    p.add_argument("--signer", default=DEFAULT_SIGNER)
    p.add_argument("--timestamp", default=None, help="Override timestamp (tests)")
    p.add_argument("--audit-report", type=Path, default=None)
    p.add_argument("--re-run-audit", action="store_true")
    p.add_argument("--packaging-count", type=int, default=None)
    p.add_argument("--skip-pytest", action="store_true")
    p.add_argument("--skip-repro", action="store_true", default=True)
    p.add_argument("--run-repro", action="store_true")
    p.add_argument("--force-fail", default=None)
    p.add_argument("--json", action="store_true")
    args = p.parse_args(argv)

    result = run_release_signoff(
        args.root,
        expect_version=args.expect_version,
        out_dir=args.out,
        tip=args.tip,
        signer=args.signer,
        timestamp=args.timestamp,
        audit_report=args.audit_report,
        re_run_audit=args.re_run_audit,
        packaging_count=args.packaging_count,
        skip_pytest=args.skip_pytest,
        skip_repro=not args.run_repro if args.run_repro else args.skip_repro,
        force_fail=args.force_fail,
    )
    if args.json:
        print(result.to_json(), end="")
    else:
        status = "PASS" if result.ok else "FAIL"
        print(f"RELEASE_SIGNOFF: {status}")
        print(f"VERSION: {result.version}")
        print(f"TIP: {result.tip}")
        print(f"CP: {result.cp}")
        print(f"PRIOR_CP: {result.prior_cp}")
        print(f"FREEZE: {result.freeze_channel}")
        print(f"SIGNER: {result.signer}")
        print(f"TIMESTAMP: {result.timestamp}")
        for g in result.gates:
            mark = "OK" if g.ok else "FAIL"
            print(f"  [{mark}] {g.name}: {g.detail}")
        for e in result.errors:
            print(f"ERROR: {e}")
        if result.signoff_path:
            print(f"SIGNOFF: {result.signoff_path}")
    return 0 if result.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
