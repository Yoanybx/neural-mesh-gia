#!/usr/bin/env python3
"""Cycle 14 Phase 5C bench: crash + partition + reconnect (+ 10k/1k/100).

Compare recovery / checkpoint / conflict p99 vs DeepSeek bounds:
  recovery ≤ 2 ms, checkpoint ≤ 0.1 ms, conflict ≤ 0.1 ms.
Report MET or gap honestly.
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
    WALRecordType,
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

    # ---- checkpoint cost (same method as C13 for fair bound compare) ----
    from neural_mesh.cram.hashing import content_hash as _ch
    from neural_mesh.cram.durability import atomic_write_bytes

    for i in range(100):
        payload = json.dumps(
            {"i": i, "hash": _ch(f"ckpt-{i}".encode())}, sort_keys=True
        ).encode()
        t0 = time.perf_counter()
        h = _ch(payload)
        path = work / "ckpts" / f"{h}.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        # C14: durable fsync write (honest durability); also record plain for parity
        atomic_write_bytes(path, payload)
        checkpoint_lat.append((time.perf_counter() - t0) * 1000.0)

    # C13-parity checkpoint (plain write_text, no fsync) for bound comparison
    checkpoint_parity_lat: list[float] = []
    for i in range(100):
        payload = json.dumps(
            {"i": i, "hash": _ch(f"ckpt-parity-{i}".encode())}, sort_keys=True
        ).encode()
        t0 = time.perf_counter()
        h = _ch(payload)
        path = work / "ckpts_parity" / f"{h}.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(payload.decode(), encoding="utf-8")
        checkpoint_parity_lat.append((time.perf_counter() - t0) * 1000.0)

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
    for i in range(50):
        for nid in list(getattr(mgr, "_lost", set()) or []):
            mgr.restore_node(nid)
        key = mgr.put_replicated(f"rec-{i}".encode(), sync=True)
        rec = mgr._registry[key]
        prior_primary = rec.primary_node
        for nid in list(getattr(mgr, "_lost", set()) or []):
            mgr.restore_node(nid)
        mgr.mark_node_lost(prior_primary)
        t0 = time.perf_counter()
        result = run_recovery_test(
            mgr,
            key,
            reason="primary_unavailable",
            log_dir=work / "repl" / "recovery_logs",
        )
        recovery_lat.append((time.perf_counter() - t0) * 1000.0)
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
    cp_stats = _stats(checkpoint_lat)
    conf_stats = _stats(conflict_lat)

    cp_parity = _stats(checkpoint_parity_lat)
    conf_parity = _stats(conflict_classify_lat)
    bounds_eval = {
        "recovery_p99_ms": {
            "bound": BOUNDS["recovery_p99_ms"],
            "measured": rec_stats.get("p99_ms"),
            "met": rec_stats.get("p99_ms", 999) <= BOUNDS["recovery_p99_ms"],
            "note": "stretch vs prior path; WAL fsync in apply may add cost",
        },
        "checkpoint_p99_ms": {
            "bound": BOUNDS["checkpoint_p99_ms"],
            "measured_durable_fsync": cp_stats.get("p99_ms"),
            "measured_parity_c13_plain_write": cp_parity.get("p99_ms"),
            "met_durable": cp_stats.get("p99_ms", 999) <= BOUNDS["checkpoint_p99_ms"],
            "met_parity_c13_method": cp_parity.get("p99_ms", 999)
            <= BOUNDS["checkpoint_p99_ms"],
            "note": "Primary claim uses durable fsync; parity uses C13 plain write_text",
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
        "cycle": 14,
        "checkpoint": "CP-0018",
        "version": "0.14.0",
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
            "checkpoint": cp_stats,
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
            "Checkpoint metric = atomic_write_bytes fsync JSON (C14 durable); compaction separate.",
        ],
    }

    out_path = OUT / "baseline.json"
    out_path.write_text(json.dumps(baseline, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(bounds_eval, indent=2))
    print(f"wrote {out_path}")


if __name__ == "__main__":
    main()
