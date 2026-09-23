#!/usr/bin/env python3
"""Rollback smoke (CP-0026 / P13).

Install bundle B then rollback to A in the same prefix (filesystem-level).

Usage:
  .venv/bin/python scripts/rollback_smoke.py --bundle-a A.tar.gz --bundle-b B.tar.gz --prefix /tmp/mesh-prefix
  .venv/bin/python scripts/rollback_smoke.py --build --ver-a 0.16.1 --ver-b 0.16.2
"""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
from pathlib import Path

_REPO = Path(__file__).resolve().parents[1]
_SRC = _REPO / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from neural_mesh.packaging import build_bundle, rollback_smoke  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Rollback smoke for mesh single-node bundles")
    p.add_argument("--bundle-a", type=Path, default=None)
    p.add_argument("--bundle-b", type=Path, default=None)
    p.add_argument("--manifest-a", type=Path, default=None)
    p.add_argument("--manifest-b", type=Path, default=None)
    p.add_argument("--build", action="store_true", help="Build A and B from --root with --ver-a/--ver-b")
    p.add_argument("--root", type=Path, default=_REPO)
    p.add_argument("--out", type=Path, default=_REPO / "dist" / "rollback")
    p.add_argument("--ver-a", default="0.16.1")
    p.add_argument("--ver-b", default="0.16.2")
    p.add_argument("--tip-a", default="rollbaa")
    p.add_argument("--tip-b", default="rollbab")
    p.add_argument("--prefix", type=Path, default=None)
    p.add_argument("--forbidden-repo", type=Path, default=_REPO)
    p.add_argument("--json", action="store_true")
    args = p.parse_args(argv)

    bundle_a = args.bundle_a
    bundle_b = args.bundle_b
    if args.build or bundle_a is None or bundle_b is None:
        args.out.mkdir(parents=True, exist_ok=True)
        ma = build_bundle(
            args.root, args.out, ver=args.ver_a, tip=args.tip_a, cp_range="CP-0001..0026"
        )
        mb = build_bundle(
            args.root, args.out, ver=args.ver_b, tip=args.tip_b, cp_range="CP-0001..0026"
        )
        bundle_a = args.out / f"{ma.name}-{ma.ver}.tar.gz"
        bundle_b = args.out / f"{mb.name}-{mb.ver}.tar.gz"
        print(f"BUILT_A: {bundle_a}")
        print(f"BUILT_B: {bundle_b}")

    prefix = args.prefix
    tmp = None
    if prefix is None:
        tmp = tempfile.mkdtemp(prefix="mesh-rollback-")
        prefix = Path(tmp)

    result = rollback_smoke(
        bundle_a,
        bundle_b,
        prefix,
        manifest_a=args.manifest_a,
        manifest_b=args.manifest_b,
        forbidden_repo=args.forbidden_repo,
        expect_ver_a=args.ver_a if args.build else None,
    )
    if args.json:
        print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
    else:
        status = "PASS" if result.ok else "FAIL"
        print(f"ROLLBACK_SMOKE: {status}")
        print(f"VER_BEFORE: {result.ver_before}")
        print(f"VER_AFTER: {result.ver_after}")
        print(f"TIP_AFTER: {result.tip_after}")
        for w in result.warnings:
            print(f"WARN: {w}")
        for e in result.errors:
            print(f"ERROR: {e}")
    return 0 if result.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
