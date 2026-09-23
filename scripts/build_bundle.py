#!/usr/bin/env python3
"""Build a reproducible single-node Neural Mesh bundle (CP-0024).

Usage:
  python scripts/build_bundle.py [--root PATH] [--out DIR] [--ver VER] [--tip TIP]

Prefer repo .venv:
  .venv/bin/python scripts/build_bundle.py --out dist/
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Allow running from repo without install.
_REPO = Path(__file__).resolve().parents[1]
_SRC = _REPO / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from neural_mesh.packaging import (  # noqa: E402
    DEFAULT_BUNDLE_NAME,
    build_bundle,
    manifest_to_dict,
)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Build single-node mesh bundle")
    p.add_argument(
        "--root",
        type=Path,
        default=_REPO,
        help="Repository root (default: parent of scripts/)",
    )
    p.add_argument(
        "--out",
        type=Path,
        default=_REPO / "dist",
        help="Output directory for tarball + manifest",
    )
    p.add_argument("--name", default=DEFAULT_BUNDLE_NAME)
    p.add_argument("--ver", default=None, help="Override version (default: pyproject)")
    p.add_argument("--tip", default=None, help="Override git tip (7-char)")
    p.add_argument("--cp-range", default=None, dest="cp_range")
    p.add_argument("--entrypoint", default="mesh")
    p.add_argument(
        "--pytest-passed",
        type=int,
        default=None,
        help="Override pytest passed count in manifest",
    )
    p.add_argument(
        "--pytest-failed",
        type=int,
        default=None,
        help="Override pytest failed count in manifest",
    )
    p.add_argument("--json", action="store_true", help="Print manifest JSON to stdout")
    args = p.parse_args(argv)

    pytest = None
    if args.pytest_passed is not None or args.pytest_failed is not None:
        pytest = {
            "passed": int(args.pytest_passed or 0),
            "failed": int(args.pytest_failed or 0),
        }

    manifest = build_bundle(
        args.root,
        args.out,
        name=args.name,
        ver=args.ver,
        tip=args.tip,
        cp_range=args.cp_range,
        pytest=pytest,
        entrypoint=args.entrypoint,
    )
    tar_name = f"{manifest.name}-{manifest.ver}.tar.gz"
    man_name = f"{manifest.name}-{manifest.ver}.manifest.json"
    print(f"BUNDLE: {args.out / tar_name}")
    print(f"MANIFEST: {args.out / man_name}")
    print(f"SHA256: {manifest.bundle_sha256}")
    print(f"VER: {manifest.ver} TIP: {manifest.tip} CP: {manifest.cp_range}")
    if args.json:
        print(json.dumps(manifest_to_dict(manifest), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
