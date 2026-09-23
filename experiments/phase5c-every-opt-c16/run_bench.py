#!/usr/bin/env python3
"""Cycle 16 Phase 5C EVERY-floor opt bench (CP-0020).

Push checkpoint_every_floor toward ≤0.1ms (C16 opts). Keep BATCH MET; recovery ≤2.
Report EVERY (full + coalesce + compact) + BATCH + parity + tmpfs note. Never fabricate p99.
"""

from __future__ import annotations

import json
import shutil
import statistics
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from neural_mesh.cram.compaction import SnapshotCompactor  # noqa: E402
from neural_mesh.cram.consistency import ConsistencyLayer  # noqa: E402
from neural_mesh.cram.durability import (  # noqa: E402
    DurabilityChecker,
    DurabilityWAL,
    GroupFsyncSeal,
    SyncMode,
    WALRecordType,
    atomic_write_bytes,
    compact_checkpoint_bytes,
    reset_dir_coalescer,
    reset_seal_group,
    simulate_crash_mid_append,
    simulate_crash_mid_checkpoint,
    simulate_crash_mid_write,
)
from neural_mesh.cram.partition_suite import run_partition_suite  # noqa: E402
from neural_mesh.cram.recovery_protocol import run_recovery_test  # noqa: E402
from neural_mesh.cram.replication.manager import ReplicaManager  # noqa: E402
from neural_mesh.cram.store import CRAMStore  # noqa: E402
from neural_mesh.router.metrics import percentile  # noqa: E402
from neural_mesh.twin.schema import Topology, TopologyLink, TopologyNode  # noqa: E402

OUT = Path(__file__).resolve().parent

N_SMALL = 10_000
N_MEDIUM = 1_000
N_LARGE = 100

BOUNDS = {
    "recovery_p99_ms": 2.0,
    "checkpoint_p99_ms": 0.1,
    "conflict_detect_p99_ms": 0.1,
}


def _topo(seed: int = 42) -> Topology:
    return Topology(
        network_id="phase5c-bench",
        seed=seed,
        nodes=[
            TopologyNode(id="node-01", cpu=4),
            TopologyNode(id="node-02", cpu=4),
            TopologyNode(id="node-03", cpu=4),
        ],
        links=[
            TopologyLink(source="node-01", target="node-02"),
            TopologyLink(source="node-02", target="node-03"),
        ],
    )


def _stats(lat: list[float]) -> dict:
    if not lat:
        return {"n": 0}
    return {
        "n": len(lat),
        "mean_ms": statistics.mean(lat),
        "p50_ms": percentile(lat, 50),
        "p95_ms": percentile(lat, 95),
        "p99_ms": percentile(lat, 99),
        "max_ms": max(lat),
    }


def main() -> None:
    work = OUT / "work"
    if work.exists():
        shutil.rmtree(work)
    work.mkdir(parents=True, exist_ok=True)

    layer = ConsistencyLayer(work / "cons", node_id="node-01")
    mgr = ReplicaManager(work / "repl", _topo(), seed=42)
    store = CRAMStore(work / "cas")

    conflict_lat: list[float] = []
    apply_small: list[float] = []
    apply_medium: list[float] = []
    apply_large: list[float] = []
    dup_lat: list[float] = []
    checkpoint_lat: list[float] = []
    recovery_lat: list[float] = []
    crash_recover_lat: list[float] = []
    partition_lat: list[float] = []
    reconnect_lat: list[float] = []

    # ---- 10k small + conflict ----
    for i in range(N_SMALL):
        oid = f"small-{i % 100}"
        payload = f"small-{i}".encode()
        t0 = time.perf_counter()
        r = layer.apply_write(oid, payload, operation_id=f"s-{i}", epoch=0)
        dt = (time.perf_counter() - t0) * 1000.0
        apply_small.append(dt)
        if r.status == "CONFLICT" or (
            r.status == "DUPLICATE" and r.detail.get("same_hash")
        ):
            conflict_lat.append(dt)
        elif r.status in ("APPLIED", "REJECTED_STALE_EPOCH", "CONFLICT"):
            # measure classify path cost for non-first writes on reused ids
            if i >= 100:
                conflict_lat.append(dt)

    # Explicit conflict detect samples (full apply path incl. WAL fsync — honest C14)
    for i in range(400):
        layer.apply_write(f"c-{i}", b"base", operation_id=f"cb-{i}", epoch=0)
        t0 = time.perf_counter()
        layer.apply_write(f"c-{i}", b"other", operation_id=f"cc-{i}", epoch=0)
        conflict_lat.append((time.perf_counter() - t0) * 1000.0)

    # Parity with C13: classify_write only (no WAL) — for bound comparison fairness
    from neural_mesh.cram.conflict import classify_write
    from neural_mesh.cram.version import CRAMVersion
    from neural_mesh.cram.models import utc_now
    from neural_mesh.cram.hashing import content_hash as _ch2

    conflict_classify_lat: list[float] = []
    for i in range(2000):
        existing = CRAMVersion(
            object_id=f"cf-{i}",
            epoch=0,
            sequence=1,
            hash=_ch2(b"a"),
            timestamp=utc_now(),
            origin_node="node-01",
        )
        incoming = CRAMVersion(
            object_id=f"cf-{i}",
            epoch=0,
            sequence=2,
            hash=_ch2(b"b"),
            timestamp=utc_now(),
            origin_node="node-01",
        )
        t0 = time.perf_counter()
        classify_write(existing, incoming)
        conflict_classify_lat.append((time.perf_counter() - t0) * 1000.0)

    # ---- 1k medium ----
    med = b"m" * 4096
    for i in range(N_MEDIUM):
        t0 = time.perf_counter()
        layer.apply_write(f"med-{i}", med, operation_id=f"m-{i}", epoch=0)
        apply_medium.append((time.perf_counter() - t0) * 1000.0)

    # ---- 100 large ----
    large = b"L" * 65536
    for i in range(N_LARGE):
        t0 = time.perf_counter()
        layer.apply_write(f"large-{i}", large, operation_id=f"l-{i}", epoch=0)
        apply_large.append((time.perf_counter() - t0) * 1000.0)

    # ---- duplicate suppress ----
    layer.apply_write("dup", b"once", operation_id="dup-op")
    dup_ok = 0
    for i in range(1000):
        t0 = time.perf_counter()
        r = layer.apply_write("dup", b"once", operation_id="dup-op")
        dup_lat.append((time.perf_counter() - t0) * 1000.0)
        if r.status == "DUPLICATE":
            dup_ok += 1

    # ---- checkpoint cost (C16: EVERY full/coalesce/compact + BATCH + parity) ----
    from neural_mesh.cram.hashing import content_hash as _ch

    (work / "ckpts_every").mkdir(parents=True, exist_ok=True)
    (work / "ckpts_every_coal").mkdir(parents=True, exist_ok=True)
    (work / "ckpts_every_compact").mkdir(parents=True, exist_ok=True)
    (work / "ckpts_batch").mkdir(parents=True, exist_ok=True)
    (work / "ckpts_parity").mkdir(parents=True, exist_ok=True)

    # EVERY full = sync-every-write + per-op dir fsync (C15 method; C16 hot path)
    checkpoint_every_lat: list[float] = []
    for i in range(200):
        payload = json.dumps(
            {"i": i, "hash": _ch(f"ckpt-every-{i}".encode())}, sort_keys=True
        ).encode()
        t0 = time.perf_counter()
        h = _ch(payload)
        path = work / "ckpts_every" / f"{h}.json"
        atomic_write_bytes(path, payload, sync_mode=SyncMode.EVERY, dir_fsync="every")
        checkpoint_every_lat.append((time.perf_counter() - t0) * 1000.0)

    # EVERY + dir coalesce (POSIX-safe defer of dir fsync; content still fdatasync'd)
    checkpoint_every_coal_lat: list[float] = []
    coal = reset_dir_coalescer()
    for i in range(200):
        payload = json.dumps(
            {"i": i, "hash": _ch(f"ckpt-coal-{i}".encode())}, sort_keys=True
        ).encode()
        t0 = time.perf_counter()
        h = _ch(payload)
        path = work / "ckpts_every_coal" / f"{h}.json"
        atomic_write_bytes(
            path, payload, sync_mode=SyncMode.EVERY, dir_fsync="coalesce", dir_coalescer=coal
        )
        checkpoint_every_coal_lat.append((time.perf_counter() - t0) * 1000.0)
    coal_flush_t0 = time.perf_counter()
    coal_info = coal.flush()
    coal_flush_ms = (time.perf_counter() - coal_flush_t0) * 1000.0

    # EVERY + compact payload (smaller seal) + full dir fsync
    checkpoint_every_compact_lat: list[float] = []
    for i in range(200):
        digest = _ch(f"ckpt-compact-{i}".encode())
        payload = compact_checkpoint_bytes(i, digest)
        t0 = time.perf_counter()
        h = _ch(payload)
        path = work / "ckpts_every_compact" / f"{h}.json"
        atomic_write_bytes(path, payload, sync_mode=SyncMode.EVERY, dir_fsync="every")
        checkpoint_every_compact_lat.append((time.perf_counter() - t0) * 1000.0)

    # BATCH hot-path (P7 primary claim) + group seal after
    seal = reset_seal_group()
    for i in range(200):
        payload = json.dumps(
            {"i": i, "hash": _ch(f"ckpt-batch-{i}".encode())}, sort_keys=True
        ).encode()
        t0 = time.perf_counter()
        h = _ch(payload)
        path = work / "ckpts_batch" / f"{h}.json"
        atomic_write_bytes(path, payload, sync_mode=SyncMode.BATCH, seal_group=seal)
        checkpoint_lat.append((time.perf_counter() - t0) * 1000.0)
    seal_t0 = time.perf_counter()
    seal_info = seal.seal()
    seal_ms = (time.perf_counter() - seal_t0) * 1000.0

    # C13-parity checkpoint (plain write_text, no fsync)
    checkpoint_parity_lat: list[float] = []
    for i in range(200):
        payload = json.dumps(
            {"i": i, "hash": _ch(f"ckpt-parity-{i}".encode())}, sort_keys=True
        ).encode()
        t0 = time.perf_counter()
        h = _ch(payload)
        path = work / "ckpts_parity" / f"{h}.json"
        path.write_text(payload.decode(), encoding="utf-8")
        checkpoint_parity_lat.append((time.perf_counter() - t0) * 1000.0)

    # tmpfs isolation note (NOT primary MET/GAP claim)
    checkpoint_every_tmpfs_lat: list[float] = []
    tmpfs_root = Path("/dev/shm/nm_c16_every")
    try:
        if tmpfs_root.exists():
            shutil.rmtree(tmpfs_root)
        tmpfs_root.mkdir(parents=True, exist_ok=True)
        for i in range(200):
            payload = compact_checkpoint_bytes(i, _ch(f"tmpfs-{i}".encode()))
            t0 = time.perf_counter()
            h = _ch(payload)
            path = tmpfs_root / f"{h}.json"
            atomic_write_bytes(path, payload, sync_mode=SyncMode.EVERY, dir_fsync="every")
            checkpoint_every_tmpfs_lat.append((time.perf_counter() - t0) * 1000.0)
        tmpfs_ok = True
    except OSError as exc:
        tmpfs_ok = False
        tmpfs_error = str(exc)
    else:
        tmpfs_error = None
    finally:
        if tmpfs_root.exists():
            shutil.rmtree(tmpfs_root, ignore_errors=True)

    # Compaction latency (informational; not the SLO checkpoint bound)
    compact_lat: list[float] = []
    cas_keys = [store.put(f"cp-{i}".encode()) for i in range(20)]
    for i in range(20):
        t0 = time.perf_counter()
        SnapshotCompactor(work / "cas").compact(
            retain_keys=cas_keys, delete_orphans=False
        )
        compact_lat.append((time.perf_counter() - t0) * 1000.0)

    # ---- recovery FSM (restore all lost nodes each iter — C13 pattern) ----
    for i in range(80):
        for nid in list(getattr(mgr, "_lost", set()) or []):
            mgr.restore_node(nid)
        key = mgr.put_replicated(f"rec-{i}".encode(), sync=True)
        rec = mgr._registry[key]
        prior_primary = rec.primary_node
        for nid in list(getattr(mgr, "_lost", set()) or []):
            mgr.restore_node(nid)
        mgr.mark_node_lost(prior_primary)
        result = run_recovery_test(
            mgr,
            key,
            reason="primary_unavailable",
            log_dir=work / "repl" / "recovery_logs",
        )
        # FSM-reported latency (audit log flush is evidence I/O, post-snapshot)
        recovery_lat.append(float(result.recovery_time_ms))
        assert result.status == "RECOVERED", result.error
        assert result.dual_primary == 0
        mgr.restore_node(prior_primary)

    # ---- crash simulation + durability check (reconnect path) ----
    crash_root = work / "crash"
    for i in range(30):
        cl = ConsistencyLayer(crash_root / f"n{i}", node_id="node-01")
        cl.apply_write("o", f"v{i}".encode(), operation_id=f"cr-{i}")
        simulate_crash_mid_append(
            crash_root / f"n{i}" / "consistency" / "durability" / "wal.jsonl"
        )
        simulate_crash_mid_write(
            crash_root / f"n{i}" / ".cram" / "aa" / f"tmp{i}", b"partial"
        )
        simulate_crash_mid_checkpoint(
            crash_root / f"n{i}" / "consistency" / "CHECKPOINT.json"
        )
        t0 = time.perf_counter()
        # "reconnect": new layer + durability check
        cl2 = ConsistencyLayer(crash_root / f"n{i}", node_id="node-01")
        rep = DurabilityChecker(crash_root / f"n{i}").check()
        _ = cl2.apply_write("o", f"v{i}".encode(), operation_id=f"cr-{i}")  # idempotent
        crash_recover_lat.append((time.perf_counter() - t0) * 1000.0)
        assert rep.ok

    # ---- partition suite + reconnect ----
    for i in range(20):
        t0 = time.perf_counter()
        pr = run_partition_suite(work / "part" / f"run{i}")
        partition_lat.append((time.perf_counter() - t0) * 1000.0)
        assert pr.ok and pr.minority_writes_accepted == 0 and pr.dual_primary == 0
        t1 = time.perf_counter()
        # reconnect: re-open layers under healed root
        from neural_mesh.cram.partition_suite import PartitionPair

        pair = PartitionPair(work / "part" / f"run{i}" / "pair")
        pair.heal()
        reconnect_lat.append((time.perf_counter() - t1) * 1000.0)

    stale_rejected = 0
    stale_total = 100
    layer.apply_write("stale", b"0", operation_id="st0", epoch=0)
    from neural_mesh.cram.version import CRAMVersion
    from neural_mesh.cram.models import utc_now

    h = layer.versions.head("stale")
    layer.versions.set_head(
        CRAMVersion(
            object_id="stale",
            epoch=9,
            sequence=1,
            hash=h.hash,
            timestamp=utc_now(),
            origin_node="node-01",
        )
    )
    for i in range(stale_total):
        r = layer.apply_write("stale", f"x{i}".encode(), operation_id=f"st-{i}", epoch=1)
        if r.status == "REJECTED_STALE_EPOCH":
            stale_rejected += 1

    rec_stats = _stats(recovery_lat)
    cp_stats = _stats(checkpoint_lat)  # BATCH hot-path = checkpoint_durable
    cp_every = _stats(checkpoint_every_lat)
    cp_every_coal = _stats(checkpoint_every_coal_lat)
    cp_every_compact = _stats(checkpoint_every_compact_lat)
    cp_every_tmpfs = _stats(checkpoint_every_tmpfs_lat)
    conf_stats = _stats(conflict_lat)

    cp_parity = _stats(checkpoint_parity_lat)
    conf_parity = _stats(conflict_classify_lat)
    bounds_eval = {
        "recovery_p99_ms": {
            "bound": BOUNDS["recovery_p99_ms"],
            "measured": rec_stats.get("p99_ms"),
            "met": rec_stats.get("p99_ms", 999) <= BOUNDS["recovery_p99_ms"],
            "note": "C15 VERIFY tune + FSM recovery_time_ms (audit log flush excluded)",
        },
        "checkpoint_durable_p99_ms": {
            "bound": BOUNDS["checkpoint_p99_ms"],
            "measured_batch_hotpath": cp_stats.get("p99_ms"),
            "measured_every_floor": cp_every.get("p99_ms"),
            "measured_every_coalesce": cp_every_coal.get("p99_ms"),
            "measured_every_compact_payload": cp_every_compact.get("p99_ms"),
            "measured_every_tmpfs_isolation": cp_every_tmpfs.get("p99_ms"),
            "measured_parity_c13_plain_write": cp_parity.get("p99_ms"),
            "met_batch": cp_stats.get("p99_ms", 999) <= BOUNDS["checkpoint_p99_ms"],
            "met_every": cp_every.get("p99_ms", 999) <= BOUNDS["checkpoint_p99_ms"],
            "met_every_coalesce": cp_every_coal.get("p99_ms", 999)
            <= BOUNDS["checkpoint_p99_ms"],
            "met_every_compact": cp_every_compact.get("p99_ms", 999)
            <= BOUNDS["checkpoint_p99_ms"],
            "met_parity_c13_method": cp_parity.get("p99_ms", 999)
            <= BOUNDS["checkpoint_p99_ms"],
            "group_seal_ms": seal_ms,
            "group_seal": seal_info,
            "dir_coalesce_flush_ms": coal_flush_ms,
            "dir_coalesce": coal_info,
            "tmpfs_ok": tmpfs_ok,
            "tmpfs_error": tmpfs_error,
            "note": (
                "C16: EVERY primary = full dir fsync on same FS as C15; coalesce/compact/"
                "tmpfs are attempts + isolation notes. Never substitute tmpfs for primary. "
                "BATCH remains P7 MET mode."
            ),
        },
        "conflict_detect_p99_ms": {
            "bound": BOUNDS["conflict_detect_p99_ms"],
            "measured_full_apply_wal": conf_stats.get("p99_ms"),
            "measured_classify_only_parity": conf_parity.get("p99_ms"),
            "met_full_apply": conf_stats.get("p99_ms", 999)
            <= BOUNDS["conflict_detect_p99_ms"],
            "met_classify_parity": conf_parity.get("p99_ms", 999)
            <= BOUNDS["conflict_detect_p99_ms"],
            "note": "Full path includes WAL/idempotency fsync; classify-only matches C13 spirit",
        },
    }

    baseline = {
        "cycle": 16,
        "checkpoint": "CP-0020",
        "version": "0.14.2",
        "counts": {
            "small": N_SMALL,
            "medium": N_MEDIUM,
            "large": N_LARGE,
            "duplicates_total": 1000,
            "duplicates_suppressed": dup_ok,
            "duplicate_suppression_pct": 100.0 * dup_ok / 1000,
            "stale_total": stale_total,
            "stale_rejected": stale_rejected,
            "stale_reject_pct": 100.0 * stale_rejected / stale_total,
        },
        "invariants": {
            "dual_primary": 0,
            "minority_writes_accepted": 0,
            "duplicate_idempotent_pct": 100.0 * dup_ok / 1000,
            "stale_reject_pct": 100.0 * stale_rejected / stale_total,
        },
        "latency_ms": {
            "apply_small": _stats(apply_small),
            "apply_medium": _stats(apply_medium),
            "apply_large": _stats(apply_large),
            "conflict_detect": conf_stats,
            "duplicate_suppress": _stats(dup_lat),
            "checkpoint_durable_batch": cp_stats,
            "checkpoint_every_floor": cp_every,
            "checkpoint_every_coalesce": cp_every_coal,
            "checkpoint_every_compact": cp_every_compact,
            "checkpoint_every_tmpfs_isolation": cp_every_tmpfs,
            "checkpoint_parity_c13": cp_parity,
            "conflict_classify_parity": conf_parity,
            "compaction": _stats(compact_lat),
            "recovery": rec_stats,
            "crash_recover": _stats(crash_recover_lat),
            "partition_suite": _stats(partition_lat),
            "reconnect_heal": _stats(reconnect_lat),
        },
        "bounds": BOUNDS,
        "bounds_evaluation": bounds_eval,
        "clarification": (
            "N=2 'majority' = fenced primary / heal path only — NOT Raft quorum"
        ),
        "notes": [
            "Honest measurement on this box; fsync best-effort as FS honors it.",
            "checkpoint_durable = BATCH hot-path (tmp→replace, no per-op fsync) + GroupFsyncSeal.",
            "checkpoint_every_floor = C16 EVERY full (os.write+fdatasync+dir fsync); primary claim.",
            "coalesce/compact/tmpfs are optimization attempts + isolation notes — not substitutes.",
            "If EVERY primary still >0.1ms → EXPLICIT DEBT docs/debt/CHECKPOINT_EVERY_FLOOR.md.",
            "Never fabricate p99.",
        ],
        "sync_mode_primary": "batch",
    }

    out_path = OUT / "baseline.json"
    out_path.write_text(json.dumps(baseline, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(bounds_eval, indent=2))
    print(f"wrote {out_path}")


if __name__ == "__main__":
    main()
