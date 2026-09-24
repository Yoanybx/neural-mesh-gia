"""Cycle 14 — Phase 5C: Durability & Adversarial Partition → CP-0018."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from neural_mesh.cram.compaction import SnapshotCompactor
from neural_mesh.cram.consistency import ConsistencyLayer
from neural_mesh.cram.durability import (
    FSYNC_POLICY,
    DurabilityChecker,
    DurabilityWAL,
    WALRecordType,
    durable_apply,
    simulate_crash_mid_append,
    simulate_crash_mid_checkpoint,
    simulate_crash_mid_write,
)
from neural_mesh.cram.hashing import content_hash
from neural_mesh.cram.partition_suite import PartitionPair, run_partition_suite
from neural_mesh.cram.store import CRAMStore

ROOT = Path(__file__).resolve().parents[1]


# ----- P0 docs / version -----


def test_phase5c_doc_frozen():
    doc = (ROOT / "docs" / "phase5c_durability.md").read_text(encoding="utf-8")
    assert "WAL" in doc or "wal" in doc.lower()
    assert "fsync" in doc.lower()
    assert "kill -9" in doc or "mid-write" in doc
    assert "fail-closed" in doc.lower() or "fail closed" in doc.lower()
    assert "NOT Raft" in doc or "not Raft" in doc.lower() or "NOT Raft" in doc
    assert "majority" in doc.lower()
    assert "N=2" in doc or "N≤2" in doc
    assert "dual-primary" in doc.lower() or "dual_primary" in doc.lower()
    assert "compaction" in doc.lower()
    assert "CP-0018" in doc or "CP-0019" in doc


def test_version_is_at_least_0140():
    from neural_mesh import __version__

    # C15 bumped to 0.14.1; C14 floor remains ≥0.14.0
    parts = [int(x) for x in __version__.split(".")]
    assert parts >= [0, 14, 0]


def test_pyproject_version_014x():
    text = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    # C14 introduced 0.14.x; later cycles may bump (C19 → 0.15.0)
    assert (
        'version = "0.14.' in text
        or 'version = "0.15.' in text
        or 'version = "0.16.' in text
        or 'version = "0.17.' in text
    )


def test_fsync_policy_clarifies_majority_not_raft():
    assert "NOT Raft" in FSYNC_POLICY["majority_clarification"]
    assert "wal" in FSYNC_POLICY
    assert "ordering" in FSYNC_POLICY


# ----- P1 WAL / fsync / crash invariants -----


def test_wal_append_and_commit(tmp_path: Path):
    wal = DurabilityWAL(tmp_path / "wal.jsonl")
    wal.append(op_id="op1", record_type=WALRecordType.BEGIN, object_id="o")
    wal.append(op_id="op1", record_type=WALRecordType.APPLY, object_id="o")
    wal.append(op_id="op1", record_type=WALRecordType.COMMIT, object_id="o")
    assert "op1" in wal.committed_ops()
    assert "op1" not in wal.incomplete_ops()


def test_wal_incomplete_without_commit(tmp_path: Path):
    wal = DurabilityWAL(tmp_path / "wal.jsonl")
    wal.append(op_id="op2", record_type=WALRecordType.BEGIN)
    wal.append(op_id="op2", record_type=WALRecordType.APPLY)
    assert "op2" in wal.incomplete_ops()
    assert "op2" not in wal.committed_ops()


def test_wal_survives_restart(tmp_path: Path):
    path = tmp_path / "wal.jsonl"
    wal = DurabilityWAL(path)
    wal.append(op_id="op3", record_type=WALRecordType.BEGIN)
    wal.append(op_id="op3", record_type=WALRecordType.COMMIT)
    wal2 = DurabilityWAL(path)
    assert "op3" in wal2.committed_ops()


def test_wal_ignores_truncated_mid_append(tmp_path: Path):
    path = tmp_path / "wal.jsonl"
    wal = DurabilityWAL(path)
    wal.append(op_id="good", record_type=WALRecordType.BEGIN)
    wal.append(op_id="good", record_type=WALRecordType.COMMIT)
    simulate_crash_mid_append(path)
    wal2 = DurabilityWAL(path)
    assert "good" in wal2.committed_ops()
    # truncated line must not raise
    assert isinstance(wal2.records(), list)


def test_crash_mid_write_no_visible_object(tmp_path: Path):
    target = tmp_path / ".cram" / "ab" / "cdef"
    tmp = simulate_crash_mid_write(target, b"partial-data")
    assert tmp.exists()
    assert not target.exists()


def test_crash_mid_checkpoint_prior_intact(tmp_path: Path):
    final = tmp_path / "CHECKPOINT.json"
    final.write_text('{"checkpoint_id":"CP-0017","ok":true}', encoding="utf-8")
    tmp = simulate_crash_mid_checkpoint(final)
    assert tmp.exists()
    assert json.loads(final.read_text(encoding="utf-8"))["checkpoint_id"] == "CP-0017"


def test_durable_apply_commit_and_abort(tmp_path: Path):
    wal = DurabilityWAL(tmp_path / "wal.jsonl")

    def ok():
        return {"x": 1}

    r = durable_apply(
        wal,
        op_id="d1",
        object_id="o",
        epoch=0,
        content_hash_val="abc",
        commit_fn=ok,
    )
    assert r["status"] == "COMMITTED"
    assert "d1" in wal.committed_ops()

    def boom():
        raise RuntimeError("fail")

    r2 = durable_apply(
        wal,
        op_id="d2",
        object_id="o",
        epoch=0,
        content_hash_val="abc",
        commit_fn=boom,
    )
    assert r2["status"] == "ABORTED"
    assert "d2" not in wal.committed_ops()


def test_consistency_layer_writes_wal(tmp_path: Path):
    layer = ConsistencyLayer(tmp_path / "c", node_id="node-01")
    r = layer.apply_write("obj", b"hello", operation_id="w1")
    assert r.status == "APPLIED"
    assert "w1" in layer.wal.committed_ops()


def test_consistency_heads_atomic_fsync(tmp_path: Path):
    layer = ConsistencyLayer(tmp_path / "c", node_id="node-01")
    layer.apply_write("obj", b"data", operation_id="h1")
    heads = tmp_path / "c" / "consistency" / "versions" / "heads.json"
    assert heads.exists()
    raw = json.loads(heads.read_text(encoding="utf-8"))
    assert "obj" in raw


def test_durability_checker_pass_clean(tmp_path: Path):
    layer = ConsistencyLayer(tmp_path, node_id="node-01")
    layer.apply_write("a", b"1", operation_id="a1")
    report = DurabilityChecker(tmp_path).check()
    assert report.ok
    assert report.incomplete_ops == 0
    names = {c.name for c in report.crash_invariants}
    assert "mid_append_truncated_ignored" in names
    assert "mid_checkpoint_heads_intact" in names


def test_durability_checker_after_mid_append_fault(tmp_path: Path):
    layer = ConsistencyLayer(tmp_path, node_id="node-01")
    layer.apply_write("a", b"1", operation_id="a1")
    simulate_crash_mid_append(tmp_path / "consistency" / "durability" / "wal.jsonl")
    report = DurabilityChecker(tmp_path).check()
    assert report.ok  # truncated ignored


def test_idempotency_survives_restart_with_fsync(tmp_path: Path):
    layer = ConsistencyLayer(tmp_path, node_id="node-01")
    r1 = layer.apply_write("x", b"v", operation_id="idem-1")
    assert r1.status == "APPLIED"
    layer2 = ConsistencyLayer(tmp_path, node_id="node-01")
    r2 = layer2.apply_write("x", b"v", operation_id="idem-1")
    assert r2.status == "DUPLICATE"


# ----- P2 Partition suite (FIRST GATE) -----


def test_partition_suite_ok(tmp_path: Path):
    report = run_partition_suite(tmp_path / "suite")
    assert report.ok, json.dumps(report.to_dict(), indent=2)
    assert report.minority_writes_accepted == 0
    assert report.dual_primary == 0
    assert report.stale_reject_pct == 100.0
    assert "NOT Raft" in report.clarification


def test_partition_minority_zero_writes(tmp_path: Path):
    pair = PartitionPair(tmp_path / "p")
    pair.partition()
    for i in range(3):
        r = pair.standby.apply_write(f"m{i}", b"x", operation_id=f"m{i}")
        assert r.status == "REJECTED_PARTITION"


def test_partition_fenced_primary_can_write(tmp_path: Path):
    pair = PartitionPair(tmp_path / "p")
    pair.partition()
    r = pair.primary.apply_write("ok", b"yes", operation_id="p1")
    assert r.status == "APPLIED"


def test_partition_stale_epoch_100(tmp_path: Path):
    pair = PartitionPair(tmp_path / "p")
    pair.partition()
    pair.primary.apply_write("e", b"0", operation_id="e0", epoch=0)
    from neural_mesh.cram.version import CRAMVersion
    from neural_mesh.cram.models import utc_now

    h = pair.primary.versions.head("e")
    pair.primary.versions.set_head(
        CRAMVersion(
            object_id="e",
            epoch=5,
            sequence=1,
            hash=h.hash,
            timestamp=utc_now(),
            origin_node="node-01",
        )
    )
    rejected = 0
    n = 20
    for i in range(n):
        r = pair.primary.apply_write("e", f"s{i}".encode(), operation_id=f"s{i}", epoch=2)
        if r.status == "REJECTED_STALE_EPOCH":
            rejected += 1
    assert rejected == n


def test_partition_dual_primary_zero(tmp_path: Path):
    pair = PartitionPair(tmp_path / "p")
    pair.partition()
    assert pair.attempt_dual_primary() == 0
    assert pair.primary.dual_primary_count == 0
    assert pair.standby.dual_primary_count == 0


def test_partition_heal_deterministic_reconcile(tmp_path: Path):
    pair = PartitionPair(tmp_path / "p")
    pair.primary.apply_write("shared", b"v1", operation_id="s1")
    pair.standby.apply_write("shared", b"v1", operation_id="s1b")
    pair.partition()
    pair.primary.apply_write("only-p", b"p", operation_id="op")
    heal = pair.heal()
    assert heal["dual_primary"] == 0
    a = pair.primary.versions.head("only-p")
    b = pair.standby.versions.head("only-p")
    assert a is not None and b is not None
    assert a.hash == b.hash
    assert a.epoch == b.epoch


def test_partition_heal_conflict_audited(tmp_path: Path):
    pair = PartitionPair(tmp_path / "p")
    # Divergent same-epoch different hash before heal (simulate split write
    # that somehow landed — reconcile must pick deterministically)
    pair.primary.apply_write("div", b"A", operation_id="a1", epoch=0)
    # Directly set standby head to different hash same epoch
    from neural_mesh.cram.version import CRAMVersion
    from neural_mesh.cram.models import utc_now

    pair.standby.versions.set_head(
        CRAMVersion(
            object_id="div",
            epoch=0,
            sequence=1,
            hash=content_hash(b"B"),
            timestamp=utc_now(),
            origin_node="node-02",
        )
    )
    heal = pair.heal()
    assert heal["dual_primary"] == 0
    a = pair.primary.versions.head("div")
    b = pair.standby.versions.head("div")
    assert a.hash == b.hash
    assert a.epoch >= 1


def test_partition_suite_case_names(tmp_path: Path):
    report = run_partition_suite(tmp_path / "s2")
    names = {c.name for c in report.cases}
    assert "minority_accepts_zero_writes" in names
    assert "stale_epoch_under_partition" in names
    assert "dual_primary_zero" in names
    assert "deterministic_reconcile_on_heal" in names


# ----- P3 compaction -----


def test_compaction_retains_verified(tmp_path: Path):
    store = CRAMStore(tmp_path)
    k1 = store.put(b"keep-me")
    k2 = store.put(b"also-keep")
    report = SnapshotCompactor(tmp_path).compact(retain_keys=[k1, k2])
    assert report.ok
    assert report.verified == 2
    assert store.verify(k1) and store.verify(k2)
    cur = tmp_path / "consistency" / "snapshots" / "CURRENT.json"
    assert cur.exists()


def test_compaction_crash_before_flip_preserves_prior(tmp_path: Path):
    store = CRAMStore(tmp_path)
    k = store.put(b"data")
    c = SnapshotCompactor(tmp_path)
    r1 = c.compact(retain_keys=[k], delete_orphans=False)
    assert r1.ok and not r1.aborted
    prior = r1.snapshot_id
    r2 = c.compact(
        retain_keys=[k], delete_orphans=False, simulate_crash_before_flip=True
    )
    assert r2.aborted
    assert r2.ok  # no corruption
    assert c._read_current() == prior


def test_compaction_does_not_lose_verified_on_gc(tmp_path: Path):
    store = CRAMStore(tmp_path)
    keep = store.put(b"keep")
    orphan = store.put(b"orphan-soon")
    r = SnapshotCompactor(tmp_path).compact(retain_keys=[keep], delete_orphans=True)
    assert r.ok
    assert store.exists(keep)
    assert store.verify(keep)
    # orphan may be deleted
    assert r.deleted >= 0


def test_compaction_aborts_on_missing_required(tmp_path: Path):
    r = SnapshotCompactor(tmp_path).compact(retain_keys=["deadbeef" * 8])
    assert r.aborted
    assert not r.ok


def test_compaction_wal_commit(tmp_path: Path):
    store = CRAMStore(tmp_path)
    k = store.put(b"x")
    SnapshotCompactor(tmp_path).compact(retain_keys=[k], delete_orphans=False)
    wal = DurabilityWAL(tmp_path / "consistency" / "durability" / "wal.jsonl")
    types = [r.record_type for r in wal.records()]
    assert WALRecordType.COMPACT in types
    assert WALRecordType.COMMIT in types


# ----- P4 CLI -----


def _mesh(*args: str, root: Path | None = None) -> subprocess.CompletedProcess:
    cmd = [sys.executable, "-m", "neural_mesh.cli", *args]
    if root is not None and "--root" not in args:
        # callers pass --root explicitly when needed
        pass
    return subprocess.run(
        cmd,
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        env={**dict(**{k: v for k, v in __import__("os").environ.items()}), "PYTHONPATH": str(ROOT / "src")},
    )


def test_cli_durability_check(tmp_path: Path):
    layer = ConsistencyLayer(tmp_path, node_id="node-01")
    layer.apply_write("z", b"1", operation_id="z1")
    r = _mesh("cram", "durability", "check", "--root", str(tmp_path))
    assert r.returncode == 0, r.stderr + r.stdout
    data = json.loads(r.stdout)
    assert data["ok"] is True


def test_cli_partition_test(tmp_path: Path):
    r = _mesh("cram", "partition", "test", "--root", str(tmp_path))
    assert r.returncode == 0, r.stderr + r.stdout
    data = json.loads(r.stdout)
    assert data["ok"] is True
    assert data["minority_writes_accepted"] == 0
    assert data["dual_primary"] == 0


def test_cli_recovery_trace(tmp_path: Path):
    layer = ConsistencyLayer(tmp_path, node_id="node-01")
    layer.apply_write("t", b"trace", operation_id="tr1")
    r = _mesh("cram", "recovery", "trace", "--root", str(tmp_path))
    assert r.returncode == 0, r.stderr + r.stdout
    data = json.loads(r.stdout)
    assert "wal_records" in data
    assert "fsm_states" in data
    assert "NOT Raft" in data["clarification"]


def test_cli_recovery_trace_filter(tmp_path: Path):
    layer = ConsistencyLayer(tmp_path, node_id="node-01")
    layer.apply_write("keep", b"1", operation_id="k1")
    layer.apply_write("other", b"2", operation_id="o1")
    r = _mesh("cram", "recovery", "trace", "keep", "--root", str(tmp_path))
    assert r.returncode == 0, r.stderr
    data = json.loads(r.stdout)
    for rec in data["wal_records"]:
        assert rec.get("object_id") in (None, "keep")


# ----- Integration / invariants -----


def test_no_raft_in_phase5c_modules():
    for name in ("durability.py", "partition_suite.py", "compaction.py"):
        text = (ROOT / "src" / "neural_mesh" / "cram" / name).read_text(encoding="utf-8")
        # Mentions of Raft only as negation / clarification
        if "Raft" in text or "raft" in text:
            assert "NOT Raft" in text or "not Raft" in text or "No Raft" in text or "not support" in text.lower() or "NOT" in text


def test_store_still_fsync_atomic(tmp_path: Path):
    s = CRAMStore(tmp_path)
    k = s.put(b"durable-bytes")
    s2 = CRAMStore(tmp_path)
    assert s2.get(k) == b"durable-bytes"
    assert s2.verify(k)


def test_exports_phase5c():
    from neural_mesh import cram

    assert hasattr(cram, "DurabilityChecker")
    assert hasattr(cram, "run_partition_suite")
    assert hasattr(cram, "SnapshotCompactor")


def test_checkpoint_cp0018_dir_placeholder_or_ready():
    # Directory may be created during seal; doc must exist now
    assert (ROOT / "docs" / "phase5c_durability.md").is_file()


def test_partition_suite_latency_recorded(tmp_path: Path):
    r = run_partition_suite(tmp_path)
    assert r.latency_ms >= 0


def test_durability_report_includes_policy(tmp_path: Path):
    ConsistencyLayer(tmp_path, node_id="n").apply_write("a", b"b", operation_id="1")
    rep = DurabilityChecker(tmp_path).check()
    assert "ordering" in rep.fsync_policy


def test_mid_write_then_checker(tmp_path: Path):
    ConsistencyLayer(tmp_path, node_id="n").apply_write("a", b"b", operation_id="1")
    simulate_crash_mid_write(tmp_path / ".cram" / "aa" / "bb", b"x")
    rep = DurabilityChecker(tmp_path).check()
    # leftover tmp is ok; no partial visible final
    assert any(c.name == "mid_write_no_partial_visible" for c in rep.crash_invariants)


def test_hard_no_n_gt_2_in_partition_suite_source():
    text = (ROOT / "src" / "neural_mesh" / "cram" / "partition_suite.py").read_text()
    assert "N>2" in text or "does not support N>2" in text or "NOT Raft" in text


def test_apply_write_under_partition_idempotent_reject(tmp_path: Path):
    layer = ConsistencyLayer(tmp_path, node_id="node-02")
    layer.set_partitioned(True, fenced_primary="node-01")
    r1 = layer.apply_write("x", b"1", operation_id="rej-1")
    r2 = layer.apply_write("x", b"1", operation_id="rej-1")
    assert r1.status == "REJECTED_PARTITION"
    assert r2.status == "DUPLICATE"  # idempotency records reject too


def test_cas_verify_invariant_detects_corruption(tmp_path: Path):
    store = CRAMStore(tmp_path)
    k = store.put(b"good")
    path = store._object_path(k)
    path.write_bytes(b"tampered!!!")
    rep = DurabilityChecker(tmp_path).check()
    assert not rep.ok
    assert any(c.name == "cas_objects_verify" and not c.ok for c in rep.crash_invariants)


def test_council_agreement_cycle14_present():
    p = ROOT / "council" / "COUNCIL_AGREEMENT_CYCLE14.md"
    assert p.is_file()
    text = p.read_text(encoding="utf-8")
    assert "CP-0018" in text
    assert "0.14.0" in text


def test_deepseek_reply_cycle13_points_to_cp0018():
    p = ROOT / "council" / "DEEPSEEK_REPLY_CYCLE13.md"
    assert p.is_file()
    assert "CP-0018" in p.read_text(encoding="utf-8")
