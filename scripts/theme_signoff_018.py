#!/usr/bin/env python3
"""0.18.0 H1..H8 theme-set signoff / archive / post-signoff monitor (CP-0046 / Cycle 42).

Usage:
  .venv/bin/python scripts/theme_signoff_018.py signoff
  .venv/bin/python scripts/theme_signoff_018.py archive [--tag]
  .venv/bin/python scripts/theme_signoff_018.py monitor --once
  .venv/bin/python scripts/theme_signoff_018.py all [--tag]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[1]
_SRC = _REPO / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from neural_mesh.packaging.theme_signoff_018 import (  # noqa: E402
    THEME_VERSION,
    run_018_theme_signoff,
    run_018_theme_archive,
    run_018_post_signoff_monitor,
)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="0.18.0 H1..H8 theme-set signoff closeout")
    p.add_argument(
        "command",
        choices=("signoff", "archive", "monitor", "all"),
        help="signoff | archive | monitor | all",
    )
    p.add_argument("--root", type=Path, default=_REPO)
    p.add_argument("--out", type=Path, default=None)
    p.add_argument("--ver", default=THEME_VERSION)
    p.add_argument("--tip", default=None)
    p.add_argument("--tag", action="store_true", help="Create local annotated tag")
    p.add_argument("--allow-dirty", action="store_true")
    p.add_argument("--skip-bundle", action="store_true")
    p.add_argument("--skip-pytest", action="store_true")
    p.add_argument("--pytest-count", type=int, default=None)
    p.add_argument("--once", action="store_true", default=True)
    p.add_argument("--json", action="store_true")
    p.add_argument("--force-fail", default=None)
    args = p.parse_args(argv)

    def _print_signoff(r) -> None:
        status = "PASS" if r.ok else "FAIL"
        if args.json:
            print(r.to_json(), end="")
            return
        print(f"THEME_SIGNOFF_018: {status}")
        print(f"VERSION: {r.version}")
        print(f"TIP: {r.tip}")
        print(f"CP: {r.cp}")
        print(f"FREEZE: {r.freeze_channel}")
        for g in r.gates:
            mark = "OK" if g.ok else "FAIL"
            print(f"  [{mark}] {g.name}: {g.detail}")
        if r.signoff_path:
            print(f"SIGNOFF: {r.signoff_path}")

    def _print_archive(r) -> None:
        status = "PASS" if r.ok else "FAIL"
        if args.json:
            print(r.to_json(), end="")
            return
        print(f"THEME_ARCHIVE_018: {status}")
        print(f"VERSION: {r.version}")
        print(f"TAG: {r.tag_name} created={r.tag_created}")
        print(f"ARCHIVE: {r.archive_dir}")
        for g in r.gates:
            mark = "OK" if g.ok else "FAIL"
            print(f"  [{mark}] {g.name}: {g.detail}")

    def _print_monitor(r) -> None:
        status = "PASS" if r.ok else "FAIL"
        if args.json:
            print(r.to_json(), end="")
            return
        print(f"POST_SIGNOFF_MONITOR_018: {status}")
        print(f"VERSION: {getattr(r, 'version', None)}")
        for c in getattr(r, "checks", []):
            mark = "OK" if c.ok else "FAIL"
            print(f"  [{mark}] {c.name}: {c.detail}")
        if getattr(r, "report_path", None):
            print(f"REPORT: {r.report_path}")

    rc = 0
    if args.command in ("signoff", "all"):
        r = run_018_theme_signoff(
            args.root,
            expect_version=args.ver,
            out_dir=args.out,
            tip=args.tip,
            pytest_count=args.pytest_count,
            skip_pytest=args.skip_pytest,
            force_fail=args.force_fail,
            write_project_state=args.out is None,
        )
        _print_signoff(r)
        if not r.ok:
            rc = 1
            if args.command != "all":
                return rc

    if args.command in ("archive", "all") and rc == 0:
        r = run_018_theme_archive(
            args.root,
            version=args.ver,
            out_dir=args.out,
            tip=args.tip,
            create_tag=args.tag,
            require_clean=not args.allow_dirty,
            skip_bundle=args.skip_bundle,
            force_fail=args.force_fail,
        )
        _print_archive(r)
        if not r.ok:
            rc = 1
            if args.command != "all":
                return rc

    if args.command in ("monitor", "all") and rc == 0:
        r = run_018_post_signoff_monitor(
            args.root,
            version=args.ver,
            out_dir=args.out,
            tip=args.tip,
            force_fail=args.force_fail,
        )
        _print_monitor(r)
        if not r.ok:
            rc = 1

    return rc


if __name__ == "__main__":
    raise SystemExit(main())
