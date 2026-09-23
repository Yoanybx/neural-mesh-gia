#!/usr/bin/env python3
"""Build the same bundle twice and compare checksums (CP-0025 / P10).

Usage:
  .venv/bin/python scripts/repro_check.py [--root PATH] [--out DIR] [--ver VER] [--tip TIP]
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

from neural_mesh.packaging import repro_check  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Manifest/archive reproducibility check")
    p.add_argument("--root", type=Path, default=_REPO)
    p.add_argument("--out", type=Path, default=_REPO / "dist" / "repro")
    p.add_argument("--ver", default=None)
    p.add_argument("--tip", default=None)
    p.add_argument("--cp-range", default=None, dest="cp_range")
    p.add_argument("--pytest-passed", type=int, default=None)
    p.add_argument("--pytest-failed", type=int, default=None)
    p.add_argument("--json", action="store_true")
    args = p.parse_args(argv)

    pytest = None
    if args.pytest_passed is not None or args.pytest_failed is not None:
        pytest = {
            "passed": int(args.pytest_passed or 0),
            "failed": int(args.pytest_failed or 0),
        }

    result = repro_check(
        args.root,
        args.out,
        ver=args.ver,
        tip=args.tip,
        cp_range=args.cp_range,
        pytest=pytest,
    )
    if args.json:
        print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
    else:
        status = "PASS" if result.ok else "FAIL"
        print(f"REPRO: {status}")
        print(f"SHA_A: {result.sha_a}")
        print(f"SHA_B: {result.sha_b}")
        for e in result.errors:
            print(f"ERROR: {e}")
    return 0 if result.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
