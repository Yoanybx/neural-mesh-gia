#!/usr/bin/env python3
"""RC soak stability (CP-0027 / P15).

Deterministic N-iteration soak of installed RC. Emits JSON soak report.

Usage:
  .venv/bin/python scripts/rc_soak.py --n 5
  .venv/bin/python scripts/rc_soak.py --bundle dist/foo.tar.gz --n 3 --json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[1]
_SRC = _REPO / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from neural_mesh.packaging import run_rc_soak  # noqa: E402
from neural_mesh.packaging.rc_soak import DEFAULT_ITERATIONS, DEFAULT_VARIANCE_RATIO  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Deterministic RC soak stability")
    p.add_argument("--root", type=Path, default=_REPO)
    p.add_argument("--bundle", type=Path, default=None)
    p.add_argument("--prefix", type=Path, default=None)
    p.add_argument("--out", type=Path, default=_REPO / "dist" / "soak")
    p.add_argument("--report", type=Path, default=None)
    p.add_argument("--n", type=int, default=DEFAULT_ITERATIONS)
    p.add_argument("--variance-bound", type=float, default=DEFAULT_VARIANCE_RATIO)
    p.add_argument("--no-smoke", action="store_true")
    p.add_argument("--no-reuse", action="store_true")
    p.add_argument("--ver", default=None)
    p.add_argument("--tip", default=None)
    p.add_argument("--force-fail-step", default=None, help="Test hook: fail named step")
    p.add_argument("--json", action="store_true")
    args = p.parse_args(argv)

    result = run_rc_soak(
        args.root,
        bundle=args.bundle,
        prefix=args.prefix,
        n=args.n,
        out_dir=args.out,
        report_path=args.report,
        variance_bound=args.variance_bound,
        run_clean_smoke=not args.no_smoke,
        reuse_prefix=not args.no_reuse,
        tip=args.tip,
        ver=args.ver,
        force_fail_step=args.force_fail_step,
    )
    if args.json:
        print(result.to_json(), end="")
    else:
        status = "PASS" if result.ok else "FAIL"
        print(f"RC_SOAK: {status}")
        print(f"N: {result.n} PASS: {result.pass_count} FAIL: {result.fail_count}")
        print(f"P50_MS: {result.total_p50_ms} P99_MS: {result.total_p99_ms}")
        print(f"VARIANCE: {result.variance_ratio} bound={result.variance_bound}")
        if result.report_path:
            print(f"REPORT: {result.report_path}")
        for e in result.errors:
            print(f"ERROR: {e}")
    return 0 if result.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
