#!/usr/bin/env python3
"""N=2 dual-prefix install + one-node rollback smoke (CP-0031 / P29).

Filesystem-level / loopback only. Full replica serve is out-of-band.

Usage:
  .venv/bin/python scripts/n2_install_rollback_smoke.py --build
  .venv/bin/python scripts/n2_install_rollback_smoke.py \\
      --bundle-prior A.tar.gz --bundle-new B.tar.gz --prefix /tmp/n2-smoke
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

from neural_mesh.packaging.bundle_n2 import build_n2_bundle  # noqa: E402
from neural_mesh.packaging.n2_install import (  # noqa: E402
    n2_install_dual,
    n2_install_rollback_smoke,
)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="N=2 install + rollback smoke")
    p.add_argument("--bundle-prior", type=Path, default=None)
    p.add_argument("--bundle-new", type=Path, default=None)
    p.add_argument("--manifest-prior", type=Path, default=None)
    p.add_argument("--manifest-new", type=Path, default=None)
    p.add_argument("--build", action="store_true")
    p.add_argument("--install-only", action="store_true", help="Only dual install (no rollback)")
    p.add_argument("--root", type=Path, default=_REPO)
    p.add_argument("--out", type=Path, default=_REPO / "dist" / "n2" / "rollback")
    p.add_argument("--ver-prior", default="0.17.0")
    p.add_argument("--ver-new", default="0.17.0")
    p.add_argument("--tip-prior", default="n2prior")
    p.add_argument("--tip-new", default="n2new00")
    p.add_argument("--roll-node", default="node-a", choices=["node-a", "node-b"])
    p.add_argument("--prefix", type=Path, default=None)
    p.add_argument("--json", action="store_true")
    args = p.parse_args(argv)

    bundle_prior = args.bundle_prior
    bundle_new = args.bundle_new

    if args.build or bundle_prior is None or bundle_new is None:
        args.out.mkdir(parents=True, exist_ok=True)
        # Distinct tips so markers differ even if ver stays 0.17.0
        mp = build_n2_bundle(
            args.root,
            args.out,
            ver=args.ver_prior,
            tip=args.tip_prior,
            cp_range="CP-0001..0031",
            single_node_for_parity=False,
        )
        mn = build_n2_bundle(
            args.root,
            args.out,
            ver=args.ver_new if args.ver_new != args.ver_prior else "0.17.0-rc-n2",
            tip=args.tip_new,
            cp_range="CP-0001..0031",
            single_node_for_parity=False,
        )
        # If user kept same ver, force distinct via tip-only; for rollback expect prior ver
        if args.ver_new == args.ver_prior:
            # rebuild new with slightly different ver string for marker clarity
            mn = build_n2_bundle(
                args.root,
                args.out,
                ver=f"{args.ver_new}+n2b",
                tip=args.tip_new,
                cp_range="CP-0001..0031",
                single_node_for_parity=False,
            )
        bundle_prior = args.out / f"{mp.name}-{mp.ver}.tar.gz"
        bundle_new = args.out / f"{mn.name}-{mn.ver}.tar.gz"
        print(f"BUILT_PRIOR: {bundle_prior}")
        print(f"BUILT_NEW: {bundle_new}")

    prefix = args.prefix
    if prefix is None:
        prefix = Path(tempfile.mkdtemp(prefix="mesh-n2-smoke-"))

    if args.install_only:
        result = n2_install_dual(bundle_new, prefix)
        payload = result.to_dict()
        ok = result.ok
        label = "N2_INSTALL"
    else:
        result = n2_install_rollback_smoke(
            bundle_prior,
            bundle_new,
            prefix,
            manifest_prior=args.manifest_prior,
            manifest_new=args.manifest_new,
            roll_node=args.roll_node,
            expect_ver_prior=args.ver_prior if args.build else None,
        )
        payload = result.to_dict()
        ok = result.ok
        label = "N2_INSTALL_ROLLBACK"

    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(f"{label}: {'PASS' if ok else 'FAIL'}")
        for k in ("ver_before", "ver_after", "rolled_node", "prefix_a", "prefix_b", "version"):
            if k in payload and payload[k] is not None:
                print(f"{k.upper()}: {payload[k]}")
        for w in payload.get("warnings") or []:
            print(f"WARN: {w}")
        for e in payload.get("errors") or []:
            print(f"ERROR: {e}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
