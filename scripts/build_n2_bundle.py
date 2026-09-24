#!/usr/bin/env python3
"""Build a reproducible N=2 Neural Mesh multi-node bundle (CP-0031 / Cycle 27).

Usage:
  .venv/bin/python scripts/build_n2_bundle.py --out dist/n2
  .venv/bin/python scripts/build_n2_bundle.py --ver 0.17.0 --tip deadbee
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

from neural_mesh.packaging.bundle_n2 import build_n2_bundle  # noqa: E402
from neural_mesh.packaging.manifest_n2 import (  # noqa: E402
    DEFAULT_BUNDLE_NAME_N2,
    n2_manifest_to_dict,
)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Build N=2 multi-node mesh bundle")
    p.add_argument("--root", type=Path, default=_REPO)
    p.add_argument("--out", type=Path, default=_REPO / "dist" / "n2")
    p.add_argument("--name", default=DEFAULT_BUNDLE_NAME_N2)
    p.add_argument("--ver", default=None)
    p.add_argument("--tip", default=None)
    p.add_argument("--cp-range", default=None, dest="cp_range")
    p.add_argument("--entrypoint-primary", default="mesh")
    p.add_argument("--entrypoint-secondary", default="mesh")
    p.add_argument("--pytest-passed", type=int, default=None)
    p.add_argument("--pytest-failed", type=int, default=None)
    p.add_argument("--no-freeze", action="store_true")
    p.add_argument("--no-parity-build", action="store_true")
    p.add_argument("--json", action="store_true")
    args = p.parse_args(argv)

    pytest = None
    if args.pytest_passed is not None or args.pytest_failed is not None:
        pytest = {
            "passed": int(args.pytest_passed or 0),
            "failed": int(args.pytest_failed or 0),
        }

    manifest = build_n2_bundle(
        args.root,
        args.out,
        name=args.name,
        ver=args.ver,
        tip=args.tip,
        cp_range=args.cp_range,
        pytest=pytest,
        entrypoint_primary=args.entrypoint_primary,
        entrypoint_secondary=args.entrypoint_secondary,
        freeze=not args.no_freeze,
        single_node_for_parity=not args.no_parity_build,
    )
    tar_name = f"{manifest.name}-{manifest.ver}.tar.gz"
    man_name = f"{manifest.name}-{manifest.ver}.manifest.json"
    print(f"BUNDLE_N2: {args.out / tar_name}")
    print(f"MANIFEST_N2: {args.out / man_name}")
    print(f"SHA256: {manifest.bundle_sha256}")
    print(f"VER: {manifest.ver} TIP: {manifest.tip} CP: {manifest.cp_range}")
    print(f"SCHEMA: {manifest.schema_name}")
    print(f"TOPOLOGY: {manifest.topology} ROLES: {manifest.roles}")
    print(f"DUAL_PRIMARY: {manifest.dual_primary} MAJORITY: {manifest.majority}")
    print(f"N2_EXTRAS: {len(manifest.n2_extras)}")
    if args.json:
        print(json.dumps(n2_manifest_to_dict(manifest), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
