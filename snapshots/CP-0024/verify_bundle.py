#!/usr/bin/env python3
"""Verify a single-node Neural Mesh bundle (CP-0024).

Checks: manifest schema/fields, bundle sha256, per-file checksums, optional smoke import.

Usage:
  python scripts/verify_bundle.py path/to/bundle.tar.gz [--manifest PATH] [--no-smoke]
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

from neural_mesh.packaging import verify_bundle  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Verify single-node mesh bundle")
    p.add_argument("bundle", type=Path, help="Path to .tar.gz bundle")
    p.add_argument("--manifest", type=Path, default=None)
    p.add_argument("--no-smoke", action="store_true", help="Skip import smoke test")
    p.add_argument("--expected-ver", default=None)
    p.add_argument("--json", action="store_true", help="Print VerifyResult JSON")
    args = p.parse_args(argv)

    result = verify_bundle(
        args.bundle,
        args.manifest,
        smoke=not args.no_smoke,
        expected_ver=args.expected_ver,
    )
    if args.json:
        print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
    else:
        status = "PASS" if result.ok else "FAIL"
        print(f"VERIFY: {status}")
        if result.manifest:
            m = result.manifest
            print(f"NAME: {m.name} VER: {m.ver} TIP: {m.tip} CP: {m.cp_range}")
            print(f"ENTRYPOINT: {m.entrypoint}")
            print(f"BUNDLE_SHA256: {m.bundle_sha256}")
        if result.smoke_ok is not None:
            print(f"SMOKE: {'PASS' if result.smoke_ok else 'FAIL'}")
        for w in result.warnings:
            print(f"WARN: {w}")
        for e in result.errors:
            print(f"ERROR: {e}")
    return 0 if result.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
