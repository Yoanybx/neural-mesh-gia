#!/usr/bin/env python3
"""Clean-node bundle smoke (CP-0025 / P9).

Extracts a single-node bundle into an empty temp root and runs:
  - verify_bundle (checksums + import)
  - isolated import of neural_mesh (no reach-back to original repo)
  - mesh status --snapshot (cwd = extract)

Usage:
  .venv/bin/python scripts/clean_node_smoke.py dist/neural-mesh-gia-single-node-0.16.1.tar.gz
  .venv/bin/python scripts/clean_node_smoke.py --build --out dist/
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

from neural_mesh.packaging import build_bundle, clean_node_smoke  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Clean-node smoke for mesh single-node bundle")
    p.add_argument(
        "bundle",
        type=Path,
        nargs="?",
        default=None,
        help="Path to .tar.gz (optional if --build)",
    )
    p.add_argument("--manifest", type=Path, default=None)
    p.add_argument("--build", action="store_true", help="Build bundle from --root first")
    p.add_argument("--root", type=Path, default=_REPO)
    p.add_argument("--out", type=Path, default=_REPO / "dist")
    p.add_argument("--ver", default=None)
    p.add_argument("--tip", default=None)
    p.add_argument("--forbidden-repo", type=Path, default=_REPO,
                   help="Original repo path that must NOT appear in module __file__")
    p.add_argument("--json", action="store_true")
    p.add_argument("--keep-extract", type=Path, default=None)
    args = p.parse_args(argv)

    bundle = args.bundle
    if args.build or bundle is None:
        m = build_bundle(args.root, args.out, ver=args.ver, tip=args.tip)
        bundle = args.out / f"{m.name}-{m.ver}.tar.gz"
        print(f"BUILT: {bundle}")
        print(f"SHA256: {m.bundle_sha256}")

    result = clean_node_smoke(
        bundle,
        manifest_path=args.manifest,
        forbidden_repo=args.forbidden_repo,
        keep_extract=args.keep_extract,
    )
    if args.json:
        print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
    else:
        status = "PASS" if result.ok else "FAIL"
        print(f"CLEAN_NODE_SMOKE: {status}")
        if result.extract_root:
            print(f"EXTRACT: {result.extract_root}")
        if result.version:
            print(f"VERSION: {result.version}")
        if result.neural_mesh_file:
            print(f"MODULE: {result.neural_mesh_file}")
        if result.status_snapshot:
            print(
                f"SNAPSHOT: schema={result.status_snapshot.get('schema')} "
                f"ver={result.status_snapshot.get('ver')} "
                f"cp={result.status_snapshot.get('cp_tip')}"
            )
        for w in result.warnings:
            print(f"WARN: {w}")
        for e in result.errors:
            print(f"ERROR: {e}")
    return 0 if result.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
