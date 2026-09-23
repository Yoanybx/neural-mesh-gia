#!/usr/bin/env python3
"""Release tag + archive (CP-0028 / P19).

Build dist/releases/<ver>/ archive. Optional --tag creates a local annotated
git tag with one-shot author (never edits git config; never pushes).

Usage:
  .venv/bin/python scripts/release_tag_archive.py
  .venv/bin/python scripts/release_tag_archive.py --tag
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[1]
_SRC = _REPO / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from neural_mesh.packaging import run_release_tag_archive  # noqa: E402
from neural_mesh.packaging.release_signoff import RELEASE_VERSION  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="RC release tag + archive")
    p.add_argument("--root", type=Path, default=_REPO)
    p.add_argument("--out", type=Path, default=None)
    p.add_argument("--ver", default=RELEASE_VERSION)
    p.add_argument("--tip", default=None)
    p.add_argument(
        "--tag",
        action="store_true",
        help="Create local annotated tag when working tree is clean",
    )
    p.add_argument("--tag-name", default=None)
    p.add_argument(
        "--allow-dirty",
        action="store_true",
        help="Allow tag creation on dirty tree (not recommended)",
    )
    p.add_argument("--skip-bundle", action="store_true")
    p.add_argument("--no-require-signoff", action="store_true")
    p.add_argument("--force-fail", default=None)
    p.add_argument("--json", action="store_true")
    args = p.parse_args(argv)

    result = run_release_tag_archive(
        args.root,
        version=args.ver,
        out_dir=args.out,
        tip=args.tip,
        create_tag=args.tag,
        require_clean=not args.allow_dirty,
        require_signoff=not args.no_require_signoff,
        tag_name=args.tag_name,
        skip_bundle=args.skip_bundle,
        force_fail=args.force_fail,
    )
    if args.json:
        print(result.to_json(), end="")
    else:
        status = "PASS" if result.ok else "FAIL"
        print(f"RELEASE_TAG_ARCHIVE: {status}")
        print(f"VERSION: {result.version}")
        print(f"TIP: {result.tip}")
        print(f"TAG: {result.tag_name} created={result.tag_created}")
        print(f"ARCHIVE: {result.archive_dir}")
        if result.release_archive:
            print(f"RELEASE_TAR: {result.release_archive}")
        for g in result.gates:
            mark = "OK" if g.ok else "FAIL"
            print(f"  [{mark}] {g.name}: {g.detail}")
        for e in result.errors:
            print(f"ERROR: {e}")
    return 0 if result.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
