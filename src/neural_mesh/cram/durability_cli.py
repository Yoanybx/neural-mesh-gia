"""CLI: durability check | partition test | recovery trace (Cycle 14 Phase 5C)."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import TextIO

from neural_mesh.cram.cli_ops import EXIT_GENERIC, EXIT_OK
from neural_mesh.cram.compaction import SnapshotCompactor
from neural_mesh.cram.durability import DurabilityChecker
from neural_mesh.cram.partition_suite import run_partition_suite
from neural_mesh.cram.recovery_protocol import RecoveryState


def cmd_durability_check(
    *,
    root: Path,
    out: TextIO = sys.stdout,
    err: TextIO = sys.stderr,
) -> int:
    try:
        report = DurabilityChecker(root).check()
        out.write(json.dumps(report.to_dict(), indent=2, sort_keys=True) + "\n")
        return EXIT_OK if report.ok else EXIT_GENERIC
    except Exception as exc:  # noqa: BLE001
        err.write(f"ERROR: {exc}\n")
        return EXIT_GENERIC


def cmd_partition_test(
    *,
    root: Path,
    out: TextIO = sys.stdout,
    err: TextIO = sys.stderr,
) -> int:
    try:
        report = run_partition_suite(root / "partition_suite")
        out.write(json.dumps(report.to_dict(), indent=2, sort_keys=True) + "\n")
        return EXIT_OK if report.ok else EXIT_GENERIC
    except Exception as exc:  # noqa: BLE001
        err.write(f"ERROR: {exc}\n")
        return EXIT_GENERIC


def cmd_recovery_trace(
    *,
    root: Path,
    object_id: str | None = None,
    out: TextIO = sys.stdout,
    err: TextIO = sys.stderr,
) -> int:
    """Trace WAL + recovery FSM evidence for an object (or whole root)."""
    try:
        checker = DurabilityChecker(root)
        wal_recs = [r.to_dict() for r in checker.wal.records()]
        if object_id:
            wal_recs = [r for r in wal_recs if r.get("object_id") == object_id]

        recovery_logs: list[dict] = []
        log_dir = root / "replication" / "recovery_logs"
        if log_dir.exists():
            for p in sorted(log_dir.glob("*.json*")):
                try:
                    data = json.loads(p.read_text(encoding="utf-8"))
                    if object_id:
                        oid = data.get("object_id") or data.get("detail", {}).get(
                            "object_id"
                        )
                        if oid and oid != object_id:
                            continue
                    recovery_logs.append({"file": p.name, "data": data})
                except (json.JSONDecodeError, OSError):
                    recovery_logs.append({"file": p.name, "error": "unreadable"})

        # Compact CURRENT pointer if any
        current = None
        cur_path = root / "consistency" / "snapshots" / "CURRENT.json"
        if cur_path.exists():
            try:
                current = json.loads(cur_path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                current = {"error": "corrupt"}

        payload = {
            "object_id": object_id,
            "fsm_states": [s.value for s in RecoveryState],
            "wal_records": wal_recs,
            "incomplete_ops": sorted(checker.wal.incomplete_ops()),
            "committed_ops": sorted(checker.wal.committed_ops()),
            "recovery_logs": recovery_logs,
            "snapshot_current": current,
            "clarification": (
                "N=2 'majority' = fenced primary / heal path only — NOT Raft"
            ),
        }
        out.write(json.dumps(payload, indent=2, sort_keys=True) + "\n")
        return EXIT_OK
    except Exception as exc:  # noqa: BLE001
        err.write(f"ERROR: {exc}\n")
        return EXIT_GENERIC


def cmd_compact(
    *,
    root: Path,
    out: TextIO = sys.stdout,
    err: TextIO = sys.stderr,
) -> int:
    try:
        report = SnapshotCompactor(root).compact()
        out.write(json.dumps(report.to_dict(), indent=2, sort_keys=True) + "\n")
        return EXIT_OK if report.ok else EXIT_GENERIC
    except Exception as exc:  # noqa: BLE001
        err.write(f"ERROR: {exc}\n")
        return EXIT_GENERIC


__all__ = [
    "cmd_compact",
    "cmd_durability_check",
    "cmd_partition_test",
    "cmd_recovery_trace",
]
