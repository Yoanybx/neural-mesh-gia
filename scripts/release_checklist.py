#!/usr/bin/env python3
"""Release checklist for single-node RC (CP-0026 / P14).

Exits 0 only if all gates pass. Emits JSON summary for M2M with --json.

Usage:
  .venv/bin/python scripts/release_checklist.py
  .venv/bin/python scripts/release_checklist.py --json --skip-pytest
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[1]
_SRC = _REPO / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from neural_mesh.packaging import run_release_checklist  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Single-node RC release checklist")
    p.add_argument("--root", type=Path, default=_REPO)
    p.add_argument("--out", type=Path, default=_REPO / "dist" / "checklist")
    p.add_argument("--expect-version", default="0.16.3")
    p.add_argument("--expect-cp", default="CP-0027")
    p.add_argument("--tip", default=None)
    p.add_argument("--skip-repro", action="store_true")
    p.add_argument("--skip-smoke", action="store_true")
    p.add_argument("--skip-pytest", action="store_true")
    p.add_argument("--skip-cp", action="store_true")
    p.add_argument("--no-require-freeze", action="store_true")
    p.add_argument("--prebuilt-tar", type=Path, default=None)
    p.add_argument("--smoke-marker", type=Path, default=None)
    p.add_argument("--json", action="store_true")
    args = p.parse_args(argv)

    result = run_release_checklist(
        args.root,
        expect_version=args.expect_version,
        expect_cp=args.expect_cp,
        out_dir=args.out,
        tip=args.tip,
        skip_repro=args.skip_repro,
        skip_smoke=args.skip_smoke,
        skip_pytest=args.skip_pytest,
        skip_cp=args.skip_cp,
        require_freeze=not args.no_require_freeze,
        smoke_marker=args.smoke_marker,
        prebuilt_tar=args.prebuilt_tar,
    )
    if args.json:
        print(result.to_json(), end="")
    else:
        status = "PASS" if result.ok else "FAIL"
        print(f"RELEASE_CHECKLIST: {status}")
        print(f"VERSION: {result.version}")
        print(f"CP_TIP: {result.cp_tip}")
        print(f"FREEZE: {result.freeze_channel}")
        for g in result.gates:
            mark = "OK" if g.ok else "FAIL"
            print(f"  [{mark}] {g.name}: {g.detail}")
        for e in result.errors:
            print(f"ERROR: {e}")
    return 0 if result.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
