#!/usr/bin/env python3
"""RC install verify (CP-0026 / P12).

Extract a single-node RC bundle into a clean prefix (PYTHONPATH install) and
verify mesh --help / status --snapshot / import / freeze channel.

Usage:
  .venv/bin/python scripts/rc_install_verify.py dist/neural-mesh-gia-single-node-0.16.2.tar.gz
  .venv/bin/python scripts/rc_install_verify.py --build --out dist/
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

from neural_mesh.packaging import build_bundle, rc_install_verify  # noqa: E402
from neural_mesh.packaging.manifest import FREEZE_CHANNEL  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="RC install verify for mesh single-node bundle")
    p.add_argument("bundle", type=Path, nargs="?", default=None)
    p.add_argument("--manifest", type=Path, default=None)
    p.add_argument("--build", action="store_true")
    p.add_argument("--root", type=Path, default=_REPO)
    p.add_argument("--out", type=Path, default=_REPO / "dist")
    p.add_argument("--ver", default=None)
    p.add_argument("--tip", default=None)
    p.add_argument("--prefix", type=Path, default=None)
    p.add_argument("--forbidden-repo", type=Path, default=_REPO)
    p.add_argument("--expect-freeze", default=FREEZE_CHANNEL)
    p.add_argument("--keep-prefix", action="store_true")
    p.add_argument("--json", action="store_true")
    args = p.parse_args(argv)

    bundle = args.bundle
    if args.build or bundle is None:
        m = build_bundle(args.root, args.out, ver=args.ver, tip=args.tip)
        bundle = args.out / f"{m.name}-{m.ver}.tar.gz"
        print(f"BUILT: {bundle}")
        print(f"SHA256: {m.bundle_sha256}")

    result = rc_install_verify(
        bundle,
        prefix=args.prefix,
        manifest_path=args.manifest,
        forbidden_repo=args.forbidden_repo,
        expect_freeze_channel=args.expect_freeze,
        keep_prefix=args.keep_prefix or args.prefix is not None,
    )
    if args.json:
        print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
    else:
        status = "PASS" if result.ok else "FAIL"
        print(f"RC_INSTALL_VERIFY: {status}")
        if result.prefix:
            print(f"PREFIX: {result.prefix}")
        if result.version:
            print(f"VERSION: {result.version}")
        if result.freeze_channel:
            print(f"FREEZE: {result.freeze_channel} / {result.freeze_schema}")
        print(f"HELP: {result.help_ok} STATUS: {result.status_ok} IMPORT: {result.import_ok}")
        for w in result.warnings:
            print(f"WARN: {w}")
        for e in result.errors:
            print(f"ERROR: {e}")
    return 0 if result.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
