#!/usr/bin/env python3
"""Verify an N=2 multi-node mesh bundle (CP-0031 / Cycle 27).

Usage:
  .venv/bin/python scripts/verify_n2_bundle.py dist/n2/neural-mesh-gia-n2-0.17.0.tar.gz
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

from neural_mesh.packaging.bundle_n2 import verify_n2_bundle  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Verify N=2 multi-node mesh bundle")
    p.add_argument("bundle", type=Path)
    p.add_argument("--manifest", type=Path, default=None)
    p.add_argument("--single-manifest", type=Path, default=None)
    p.add_argument("--expected-ver", default=None)
    p.add_argument("--no-smoke", action="store_true")
    p.add_argument("--json", action="store_true")
    args = p.parse_args(argv)

    result = verify_n2_bundle(
        args.bundle,
        args.manifest,
        smoke=not args.no_smoke,
        expected_ver=args.expected_ver,
        single_manifest_path=args.single_manifest,
    )
    if args.json:
        print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
    else:
        status = "PASS" if result.ok else "FAIL"
        print(f"VERIFY_N2: {status}")
        if result.manifest:
            print(f"SCHEMA: {result.manifest.schema_name}")
            print(f"VER: {result.manifest.ver} DUAL_PRIMARY: {result.manifest.dual_primary}")
        print(f"SMOKE: {result.smoke_ok}")
        print(f"PARITY: {result.parity_ok}")
        for w in result.warnings:
            print(f"WARN: {w}")
        for e in result.errors:
            print(f"ERROR: {e}")
    return 0 if result.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
