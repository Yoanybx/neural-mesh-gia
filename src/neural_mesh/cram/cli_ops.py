"""C-RAM CLI operations.

Exit codes (frozen Cycle 5 — ChatGPT ∩ DeepSeek):
  0 = PASS
  1 = generic CLI error (do NOT reuse 2/3)
  2 = integrity failure (corrupt)
  3 = missing / unavailable

fsck --json includes versioned schema field ``fsck_schema: 1``.
fsck exit = worst case found (corrupt beats missing).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import TextIO

from .errors import CRAMCorrupt, NodeUnavailable, ObjectMissing
from .store import CRAMStore

EXIT_OK = 0
EXIT_GENERIC = 1
EXIT_CORRUPT = 2
EXIT_MISSING = 3


def _store(root: Path | None) -> CRAMStore:
    return CRAMStore(root or Path.cwd())


def cmd_put(
    content: bytes,
    *,
    root: Path | None = None,
    metadata: dict | None = None,
    out: TextIO = sys.stdout,
    err: TextIO = sys.stderr,
) -> int:
    try:
        store = _store(root)
        key = store.put(content, metadata=metadata)
        out.write(key + "\n")
        return EXIT_OK
    except Exception as exc:  # noqa: BLE001 — CLI boundary
        err.write(f"ERROR: {exc}\n")
        return EXIT_GENERIC


def cmd_get(
    key: str,
    *,
    root: Path | None = None,
    out: TextIO = sys.stdout,
    err: TextIO = sys.stderr,
) -> int:
    try:
        store = _store(root)
        data = store.get(key)
    except ObjectMissing as exc:
        err.write(f"MISSING: {exc}\n")
        return EXIT_MISSING
    except NodeUnavailable as exc:
        err.write(f"UNAVAILABLE: {exc}\n")
        return EXIT_MISSING
    except Exception as exc:  # noqa: BLE001
        err.write(f"ERROR: {exc}\n")
        return EXIT_GENERIC
    try:
        out.buffer.write(data)
    except Exception:
        out.write(data.decode("utf-8", errors="replace"))
    return EXIT_OK


def cmd_verify(
    key: str,
    *,
    root: Path | None = None,
    out: TextIO = sys.stdout,
    err: TextIO = sys.stderr,
) -> int:
    try:
        store = _store(root)
        store.verify_or_raise(key)
    except ObjectMissing as exc:
        err.write(f"MISSING: {exc}\n")
        return EXIT_MISSING
    except CRAMCorrupt as exc:
        err.write(f"CORRUPT: {exc}\n")
        return EXIT_CORRUPT
    except Exception as exc:  # noqa: BLE001
        err.write(f"ERROR: {exc}\n")
        return EXIT_GENERIC
    out.write(f"OK {key}\n")
    return EXIT_OK


def cmd_fsck(
    *,
    root: Path | None = None,
    as_json: bool = False,
    out: TextIO = sys.stdout,
    err: TextIO = sys.stderr,
) -> int:
    try:
        store = _store(root)
        report = store.fsck()
    except Exception as exc:  # noqa: BLE001
        err.write(f"ERROR: {exc}\n")
        return EXIT_GENERIC
    if as_json:
        out.write(json.dumps(report, indent=2, sort_keys=True) + "\n")
    else:
        out.write(
            f"status={report['status']} checked={report['checked']} "
            f"ok={len(report['ok'])} corrupt={len(report['corrupt'])} "
            f"missing={len(report['missing'])} orphans={len(report['orphans'])}\n"
        )
        for k in report["corrupt"]:
            err.write(f"CORRUPT {k}\n")
        for k in report["missing"]:
            err.write(f"MISSING {k}\n")
        for o in report["orphans"]:
            out.write(f"ORPHAN {o}\n")
    # Worst case: integrity failure (2) beats missing (3)
    if report["corrupt"]:
        return EXIT_CORRUPT
    if report["missing"]:
        return EXIT_MISSING
    return EXIT_OK
