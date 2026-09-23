"""CLI handlers for consistency / recovery / history (Cycle 13 Phase 5B)."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import TextIO

from neural_mesh.cram.cli_ops import EXIT_GENERIC, EXIT_MISSING, EXIT_OK
from neural_mesh.cram.consistency import ConsistencyLayer
from neural_mesh.cram.hashing import content_hash
from neural_mesh.cram.recovery_protocol import run_recovery_test
from neural_mesh.cram.replica_cli import _mgr, load_topology


def cmd_consistency_check(
    object_id: str,
    *,
    root: Path,
    topology_path: str | Path | None = None,
    seed: int = 42,
    out: TextIO = sys.stdout,
    err: TextIO = sys.stderr,
) -> int:
    try:
        topo = load_topology(topology_path, seed=seed)
        mgr = _mgr(root, topology=topo, seed=seed)
        layer = ConsistencyLayer(root, replica_manager=mgr)
        # Prefer registry key; if object_id looks like raw content, hash it
        key = object_id
        if key not in mgr._registry and Path(object_id).exists():
            key = content_hash(Path(object_id).read_bytes())
        report = layer.check(key)
        # Enrich from replica_status when available
        if hasattr(mgr, "replica_status"):
            st = mgr.replica_status(key)
            report.detail["replica_status"] = st
            if st.get("status") == "MISSING" and not report.primary_hash:
                out.write(json.dumps(report.to_dict(), indent=2, sort_keys=True) + "\n")
                err.write(f"MISSING: {key}\n")
                return EXIT_MISSING
            writers = mgr.writable_primaries(key) if key in mgr._registry else []
            report.dual_primary = 0 if len(writers) <= 1 else len(writers)
            report.writable_primary = (
                writers[0] if writers else report.writable_primary
            )
            if report.dual_primary > 0:
                report.ok = False
                if "dual_primary_detected" not in report.issues:
                    report.issues.append("dual_primary_detected")
        out.write(json.dumps(report.to_dict(), indent=2, sort_keys=True) + "\n")
        return EXIT_OK if report.ok else EXIT_GENERIC
    except Exception as exc:  # noqa: BLE001
        err.write(f"ERROR: {exc}\n")
        return EXIT_GENERIC


def cmd_recovery_test(
    *,
    root: Path,
    object_id: str | None = None,
    topology_path: str | Path | None = None,
    seed: int = 42,
    put: str | None = None,
    reason: str = "primary_unavailable",
    out: TextIO = sys.stdout,
    err: TextIO = sys.stderr,
) -> int:
    """Run formal recovery FSM (optionally seed with --put then kill primary)."""
    try:
        topo = load_topology(topology_path, seed=seed)
        mgr = _mgr(root, topology=topo, seed=seed)
        key = object_id
        if put is not None:
            key = mgr.put_replicated(put.encode("utf-8"), sync=True)
        if not key:
            err.write("ERROR: provide object hash or --put payload\n")
            return EXIT_GENERIC
        if key not in mgr._registry:
            err.write(f"MISSING: {key}\n")
            return EXIT_MISSING
        rec = mgr._registry[key]
        # Simulate primary loss for the test path
        mgr.mark_node_lost(rec.primary_node)
        result = run_recovery_test(
            mgr,
            key,
            reason=reason,
            log_dir=root / "replication" / "recovery_logs",
        )
        out.write(json.dumps(result.to_dict(), indent=2, sort_keys=True) + "\n")
        if result.status == "RECOVERED" and result.dual_primary == 0:
            return EXIT_OK
        return EXIT_GENERIC
    except Exception as exc:  # noqa: BLE001
        err.write(f"ERROR: {exc}\n")
        return EXIT_GENERIC


def cmd_history(
    object_id: str,
    *,
    root: Path,
    topology_path: str | Path | None = None,
    seed: int = 42,
    out: TextIO = sys.stdout,
    err: TextIO = sys.stderr,
) -> int:
    try:
        layer = ConsistencyLayer(root)
        hist = layer.history(object_id)
        # Also surface replica log ops if present
        log_ops: list[dict] = []
        log_path = root / "replication" / "log.jsonl"
        if log_path.exists():
            for line in log_path.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if not line:
                    continue
                rec = json.loads(line)
                if rec.get("content_hash") == object_id:
                    log_ops.append(rec)
        conflicts = [c.to_dict() for c in layer.versions.conflicts(object_id)]
        payload = {
            "object_id": object_id,
            "versions": hist,
            "replication_ops": log_ops,
            "conflicts": conflicts,
        }
        out.write(json.dumps(payload, indent=2, sort_keys=True) + "\n")
        if not hist and not log_ops:
            # Not necessarily missing — empty history is OK for never-versioned keys
            return EXIT_OK
        return EXIT_OK
    except Exception as exc:  # noqa: BLE001
        err.write(f"ERROR: {exc}\n")
        return EXIT_GENERIC


__all__ = [
    "cmd_consistency_check",
    "cmd_history",
    "cmd_recovery_test",
]
