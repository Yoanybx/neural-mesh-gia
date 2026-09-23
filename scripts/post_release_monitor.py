#!/usr/bin/env python3
"""Post-release monitor (CP-0028 / P20).

--once checks after release: signoff, tag/archive marker, freeze, debt,
OBS fields, no forbidden drift. Writes MONITOR.json.

Usage:
  .venv/bin/python scripts/post_release_monitor.py --once
  .venv/bin/python scripts/post_release_monitor.py --once --json
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[1]
_SRC = _REPO / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from neural_mesh.packaging import run_post_release_monitor  # noqa: E402
from neural_mesh.packaging.release_signoff import RELEASE_VERSION  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Post-release monitor")
    p.add_argument("--root", type=Path, default=_REPO)
    p.add_argument("--once", action="store_true", default=True)
    p.add_argument("--ver", default=RELEASE_VERSION)
    p.add_argument("--out", type=Path, default=None)
    p.add_argument("--report", type=Path, default=None)
    p.add_argument("--tip", default=None)
    p.add_argument("--manifest", type=Path, default=None)
    p.add_argument("--force-fail", default=None)
    p.add_argument("--json", action="store_true")
    args = p.parse_args(argv)

    result = run_post_release_monitor(
        args.root,
        once=args.once,
        version=args.ver,
        out_dir=args.out,
        report_path=args.report,
        tip=args.tip,
        prebuilt_manifest=args.manifest,
        force_fail=args.force_fail,
    )
    if args.json:
        print(result.to_json(), end="")
    else:
        status = "PASS" if result.ok else "FAIL"
        print(f"POST_RELEASE_MONITOR: {status}")
        print(f"MODE: {result.mode}")
        print(f"VERSION: {result.version}")
        for c in result.checks:
            mark = "OK" if c.ok else "FAIL"
            print(f"  [{mark}] {c.name}: {c.detail}")
        for n in result.notes:
            print(f"NOTE: {n}")
        if result.report_path:
            print(f"REPORT: {result.report_path}")
        for e in result.errors:
            print(f"ERROR: {e}")
    return 0 if result.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
