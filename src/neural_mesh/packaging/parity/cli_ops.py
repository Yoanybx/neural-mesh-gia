"""CLI helpers for ``mesh parity status|check|build-check``."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .models import (
    ParityAbortRejectBuild,
    ParityError,
    ParityFrozenChannel,
    ParityN2Only,
    ParityPlaintextForbidden,
    ParityToolchainMismatch,
)
from .service import ParityService, canonical_manifest_bytes, compute_toolchain_pin


def _svc(data_root: str | Path) -> ParityService:
    return ParityService(data_root)


def cmd_parity_status(*, data_root: str | Path, as_json: bool = False) -> int:
    svc = _svc(data_root)
    st = svc.status()
    payload = st.to_dict()
    if as_json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(
            f"ok={st.ok} parity_ok={st.parity_ok} mismatch={st.mismatch_detected} "
            f"rejected={st.build_rejected}"
        )
        print(f"data_root={st.data_root}")
        print(f"pair={','.join(st.pair) or '<none>'}")
        print(
            f"abort_reject_build={st.abort_reject_build} "
            f"dual_primary={st.dual_primary} "
            f"digest_a={st.last_digest_a[:12] or '-'} "
            f"digest_b={st.last_digest_b[:12] or '-'}"
        )
        if st.mismatch_paths:
            print("mismatch_paths=" + ",".join(st.mismatch_paths))
        if st.issues:
            print("issues=" + ",".join(st.issues))
        if st.abort_reason:
            print(f"abort_reason={st.abort_reason}")
    return 0 if st.ok else 1


def cmd_parity_check(
    *,
    data_root: str | Path,
    auto_reject: bool = True,
    mode: str = "local",
    as_json: bool = False,
) -> int:
    svc = _svc(data_root)
    try:
        result = svc.check(auto_reject=auto_reject, mode=mode)
    except ParityPlaintextForbidden as exc:
        print(
            json.dumps(
                {
                    "ok": False,
                    "error": str(exc),
                    "error_code": exc.code,
                    "dual_primary": 0,
                    "minority_writes": 0,
                    "plaintext_fallback": 0,
                },
                indent=2,
                sort_keys=True,
            )
        )
        return 1
    except (
        ParityAbortRejectBuild,
        ParityN2Only,
        ParityFrozenChannel,
        ParityToolchainMismatch,
        ParityError,
    ) as exc:
        print(
            json.dumps(
                {
                    "ok": False,
                    "error": str(exc),
                    "error_code": getattr(exc, "code", "PARITY_ERROR"),
                    "dual_primary": 0,
                    "minority_writes": 0,
                },
                indent=2,
                sort_keys=True,
            )
        )
        return 2
    print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
    if not result.ok:
        return 2 if result.abort_reject_build else 1
    return 0


def cmd_parity_build_check(
    *,
    data_root: str | Path,
    manifest_a: str | Path | None = None,
    manifest_b: str | Path | None = None,
    auto_reject: bool = True,
    mode: str = "local",
    as_json: bool = False,
) -> int:
    """Load two manifest JSON files (or run concurrent synthetic) and check.

    If both ``manifest_a`` and ``manifest_b`` are provided, record+check them.
    Otherwise run a concurrent self-build of the pinned toolchain descriptor
    (deterministic) as a smoke byte-equality probe.
    """
    svc = _svc(data_root)
    try:
        if not svc.store.pair:
            svc.bootstrap_pair("build-a", "build-b", mode=mode)
        if manifest_a and manifest_b:
            pa = Path(manifest_a)
            pb = Path(manifest_b)
            raw_a = pa.read_bytes()
            raw_b = pb.read_bytes()
            side_a, side_b = (
                (svc.store.pair[0], svc.store.pair[1])
                if svc.store.pair
                else ("a", "b")
            )
            svc.record_build(side_a, raw_a, mode=mode)
            svc.record_build(side_b, raw_b, mode=mode)
            result = svc.check(auto_reject=auto_reject, mode=mode)
            payload: dict[str, Any] = result.to_dict()
        else:
            # Concurrent deterministic builder (toolchain pin doc)
            pin = compute_toolchain_pin()

            def _builder() -> dict[str, Any]:
                return {
                    "schema": "mesh.bundle.manifest/v1-n2",
                    "name": "neural-mesh-gia-n2",
                    "ver": "0.18.0",
                    "topology": "n2",
                    "roles": ["primary", "secondary"],
                    "dual_primary": 0,
                    "majority": "fenced_primary_heal",
                    "checksums": {
                        "pyproject.toml": "deadbeef",
                        "src/neural_mesh/__init__.py": "cafebabe",
                    },
                    "toolchain": pin.to_dict(),
                }

            cbr = svc.concurrent_build_check(
                _builder, auto_reject=auto_reject, mode=mode
            )
            payload = cbr.to_dict()
            result_ok = cbr.ok
            print(json.dumps(payload, indent=2, sort_keys=True))
            return 0 if result_ok else (2 if cbr.abort_reject_build else 1)
    except ParityPlaintextForbidden as exc:
        print(
            json.dumps(
                {
                    "ok": False,
                    "error": str(exc),
                    "error_code": exc.code,
                    "dual_primary": 0,
                    "plaintext_fallback": 0,
                },
                indent=2,
                sort_keys=True,
            )
        )
        return 1
    except (
        ParityAbortRejectBuild,
        ParityN2Only,
        ParityFrozenChannel,
        ParityError,
    ) as exc:
        print(
            json.dumps(
                {
                    "ok": False,
                    "error": str(exc),
                    "error_code": getattr(exc, "code", "PARITY_ERROR"),
                    "dual_primary": 0,
                },
                indent=2,
                sort_keys=True,
            )
        )
        return 2
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if result.ok else (2 if result.abort_reject_build else 1)


__all__ = [
    "cmd_parity_status",
    "cmd_parity_check",
    "cmd_parity_build_check",
    "canonical_manifest_bytes",
]
