#!/usr/bin/env python3
"""Debt gate review (CP-0029 / P23; CP-0030 / P25 resolution).

Reviews CHECKPOINT_EVERY_FLOOR SCHEMA-GATED status and known SLO markers
without re-benchmarking. Emits resolution=ACCEPT_AND_CARRY for 0.17.
Writes JSON report for M2M.

Usage:
  .venv/bin/python scripts/debt_gate_review.py
  .venv/bin/python scripts/debt_gate_review.py --json
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[1]
_SRC = _REPO / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from neural_mesh.packaging.debt_gate_review import run_debt_gate_review  # noqa: E402
from neural_mesh.packaging.release_signoff import RELEASE_VERSION  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Debt gate review (no rebenchmark)")
    p.add_argument("--root", type=Path, default=_REPO)
    p.add_argument("--ver", default=RELEASE_VERSION)
    p.add_argument("--report", type=Path, default=None)
    p.add_argument("--force-fail", default=None)
    p.add_argument("--json", action="store_true")
    args = p.parse_args(argv)

    result = run_debt_gate_review(
        args.root,
        version=args.ver,
        report_path=args.report,
        force_fail=args.force_fail,
    )
    if args.json:
        print(result.to_json(), end="")
    else:
        status = "PASS" if result.ok else "FAIL"
        print(f"DEBT_GATE_REVIEW: {status}")
        print(f"VERSION: {result.version}")
        print(f"CP: {result.cp}")
        print(f"SCHEMA_GATE_PRESENT: {result.schema_gate_present}")
        print(f"REBENCHMARKED: {result.rebenchmarked}")
        print(f"RESOLUTION: {result.resolution}")
        for g in result.gates:
            mark = "OK" if g.ok else "FAIL"
            print(f"  [{mark}] {g.id}: {g.status} — {g.detail}")
        for n in result.notes:
            print(f"NOTE: {n}")
        if result.report_path:
            print(f"REPORT: {result.report_path}")
        for e in result.errors:
            print(f"ERROR: {e}")
    return 0 if result.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
