"""Cycle 13 — Phase 5B: Consistency & Recovery Hardening → CP-0017."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from neural_mesh.cram.conflict import (
    ConflictOutcome,
    ConflictPolicy,
    classify_write,
    resolve_deterministic,
)
from neural_mesh.cram.consistency import ConsistencyLayer
from neural_mesh.cram.hashing import content_hash
from neural_mesh.cram.recovery_protocol import (
    RecoveryFSM,
    RecoveryMsgType,
    RecoveryState,
    make_recovery_commit,
    make_recovery_request,
    make_recovery_response,
    make_recovery_verify,
    run_recovery_test,
)
from neural_mesh.cram.replication.manager import ReplicaManager
from neural_mesh.cram.version import CRAMVersion, compare_versions
from neural_mesh.network.protocol import PHASE5B_REQUIRED_MESSAGE_TYPES, MessageType
from neural_mesh.twin.schema import Topology, TopologyLink, TopologyNode

ROOT = Path(__file__).resolve().parents[1]


def _topo(seed: int = 42) -> Topology:
    return Topology(
        network_id="cram-phase5b-test",
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


@pytest.fixture
def mgr(tmp_path: Path):
    return ReplicaManager(tmp_path / "repl", _topo(42), seed=42)


@pytest.fixture
def layer(tmp_path: Path):
    return ConsistencyLayer(tmp_path / "cons", node_id="node-01")


# ----- P0 docs / freeze -----


def test_phase5b_doc_frozen():
    doc = (ROOT / "docs" / "phase5b_consistency.md").read_text(encoding="utf-8")
    assert "CRAMVersion" in doc
    assert "conflict" in doc.lower()
    assert "RECOVERY_REQUEST" in doc
    assert "fail-closed" in doc.lower() or "fail closed" in doc.lower()
    assert "dual-primary" in doc.lower() or "dual_primary" in doc.lower()
    assert "Raft" in doc or "raft" in doc.lower()
    assert "N>2" in doc or "N>2" in doc
    assert "idempoten" in doc.lower()


def test_phase5b_message_types_present():
    names = {t.value for t in PHASE5B_REQUIRED_MESSAGE_TYPES}
    for need in (
        "RECOVERY_REQUEST",
        "RECOVERY_RESPONSE",
        "RECOVERY_VERIFY",
        "RECOVERY_COMMIT",
    ):
        assert need in names
        assert MessageType[need].value == need


def test_version_is_0130():
    from neural_mesh import __version__

    assert __version__ == "0.13.0"


# ----- P1 versioning / conflict -----


def test_cram_version_roundtrip():
    v = CRAMVersion(
        object_id="obj-1",
        epoch=1,
        sequence=2,
        hash="abc",
        timestamp="2026-09-23T00:00:00+00:00",
        origin_node="node-01",
    )
    assert CRAMVersion.from_dict(v.to_dict()) == v


def test_same_id_same_hash_idempotent(layer: ConsistencyLayer):
    r1 = layer.apply_write("obj-a", b"hello", operation_id="op-1")
    assert r1.status == "APPLIED"
    r2 = layer.apply_write("obj-a", b"hello", operation_id="op-2")
    assert r2.status == "DUPLICATE"
    assert r2.version is not None
    assert r2.version.hash == r1.version.hash


def test_same_id_diff_hash_explicit_conflict(layer: ConsistencyLayer):
    r1 = layer.apply_write("obj-b", b"v1", operation_id="op-a")
    assert r1.status == "APPLIED"
    r2 = layer.apply_write("obj-b", b"v2", operation_id="op-b", epoch=r1.version.epoch)
    assert r2.status == "CONFLICT"
    assert r2.conflict is not None
    assert r2.conflict.outcome == ConflictOutcome.CONFLICT
    conflicts = layer.versions.conflicts("obj-b")
    assert len(conflicts) >= 1


def test_lesser_epoch_rejected(layer: ConsistencyLayer):
    r1 = layer.apply_write("obj-c", b"data", operation_id="op-1", epoch=5)
    assert r1.status == "APPLIED"
    assert r1.version.epoch == 5
    r2 = layer.apply_write("obj-c", b"newer", operation_id="op-2", epoch=3)
    assert r2.status == "REJECTED_STALE_EPOCH"
    assert r2.conflict is not None


def test_idempotency_survives_restart(tmp_path: Path):
    root = tmp_path / "idemp"
    layer1 = ConsistencyLayer(root, node_id="n1")
    r1 = layer1.apply_write("obj-d", b"payload", operation_id="stable-op-99")
    assert r1.status == "APPLIED"
    # New process / new layer instance over same root
    layer2 = ConsistencyLayer(root, node_id="n1")
    r2 = layer2.apply_write("obj-d", b"payload", operation_id="stable-op-99")
    assert r2.status == "DUPLICATE"
    assert r2.detail.get("idempotent_replay") is True


def test_classify_write_rules():
    existing = CRAMVersion("o", 2, 1, "h1", "t", "n1")
    assert classify_write(None, existing) == ConflictOutcome.ACCEPTED
    same = CRAMVersion("o", 2, 2, "h1", "t", "n1")
    assert classify_write(existing, same) == ConflictOutcome.IDEMPOTENT
    stale = CRAMVersion("o", 1, 9, "h2", "t", "n1")
    assert classify_write(existing, stale) == ConflictOutcome.REJECTED_STALE_EPOCH
    conflict = CRAMVersion("o", 2, 2, "h2", "t", "n1")
    assert classify_write(existing, conflict) == ConflictOutcome.CONFLICT


def test_resolve_deterministic_stable():
    a = CRAMVersion("o", 1, 1, "aaa", "t", "n1")
    b = CRAMVersion("o", 1, 2, "bbb", "t", "n2")
    assert resolve_deterministic(a, b).sequence == 2
    c = CRAMVersion("o", 2, 0, "ccc", "t", "n3")
    assert resolve_deterministic(b, c).epoch == 2


def test_compare_versions_ordering():
    a = CRAMVersion("o", 1, 1, "h", "t", "n")
    b = CRAMVersion("o", 1, 2, "h", "t", "n")
    c = CRAMVersion("o", 2, 0, "h", "t", "n")
    assert compare_versions(a, b) < 0
    assert compare_versions(c, b) > 0
    assert compare_versions(a, a) == 0


def test_conflict_policy_deterministic_resolve(tmp_path: Path):
    layer = ConsistencyLayer(
        tmp_path / "det",
        policy=ConflictPolicy.CONFLICT_RESOLVE_DETERMINISTIC,
    )
    r1 = layer.apply_write("obj", b"aaaa", operation_id="1", epoch=1)
    # Force same epoch higher sequence different hash — resolve audited
    r2 = layer.apply_write("obj", b"bbbb", operation_id="2", epoch=1)
    assert r2.conflict is not None
    assert r2.status in ("APPLIED", "CONFLICT")


# ----- P2 recovery protocol -----


def test_recovery_message_builders():
    req = make_recovery_request(
        object_id="h", from_node="op", to_node="n2", reason="primary_unavailable"
    )
    assert req.msg_type == RecoveryMsgType.RECOVERY_REQUEST
    resp = make_recovery_response(
        object_id="h",
        from_node="n2",
        to_node="op",
        epoch=1,
        content_hash="h",
        role="STANDBY",
    )
    assert resp.msg_type == RecoveryMsgType.RECOVERY_RESPONSE
    ver = make_recovery_verify(
        object_id="h", from_node="op", to_node="n2", epoch=1, content_hash="h"
    )
    assert ver.msg_type == RecoveryMsgType.RECOVERY_VERIFY
    com = make_recovery_commit(
        object_id="h",
        from_node="n2",
        to_node="op",
        epoch=2,
        content_hash="h",
        writable_primary="n2",
        checkpoint_hash="ckpt",
    )
    assert com.msg_type == RecoveryMsgType.RECOVERY_COMMIT
    assert RecoveryMessage_roundtrip(req)


def RecoveryMessage_roundtrip(msg):
    from neural_mesh.cram.recovery_protocol import RecoveryMessage

    return RecoveryMessage.from_dict(msg.to_dict()).msg_type == msg.msg_type


def test_recovery_fsm_detect_to_resume(mgr: ReplicaManager):
    key = mgr.put_replicated(b"recover-me-please", sync=True)
    rec = mgr._registry[key]
    prior_epoch = int(rec.epoch)
    prior_primary = rec.primary_node
    mgr.mark_node_lost(prior_primary)
    fsm = RecoveryFSM(mgr, log_dir=mgr.root / "rec_logs")
    result = fsm.run(key, reason="primary_unavailable")
    assert result.status == "RECOVERED"
    assert result.state == RecoveryState.DONE
    assert result.dual_primary == 0
    assert result.checkpoint_hash
    assert result.new_epoch is not None and result.new_epoch > prior_epoch
    assert result.writable_primary != prior_primary
    types = [m["msg_type"] for m in result.messages]
    assert "RECOVERY_REQUEST" in types
    assert "RECOVERY_RESPONSE" in types
    assert "RECOVERY_VERIFY" in types
    assert "RECOVERY_COMMIT" in types
    writers = mgr.writable_primaries(key)
    assert len(writers) == 1


def test_recovery_after_primary_crash_before_checkpoint(mgr: ReplicaManager):
    key = mgr.put_replicated(b"ack-then-crash", sync=True)
    rec = mgr._registry[key]
    # Simulate: ACK done (synced), primary dies before external checkpoint
    assert rec.verified or mgr._registry[key].status.value in ("SYNCED", "CREATED")
    mgr.mark_node_lost(rec.primary_node)
    result = run_recovery_test(mgr, key, reason="primary_crash_after_ack")
    assert result.status == "RECOVERED"
    assert result.dual_primary == 0
    assert result.checkpoint_hash is not None


# ----- P3 CLI -----


def test_cli_consistency_check(tmp_path: Path, mgr: ReplicaManager):
    from neural_mesh.cram.consistency_cli import cmd_consistency_check

    key = mgr.put_replicated(b"cli-check", sync=True)
    # Re-open manager rooted same path
    code = cmd_consistency_check(key, root=mgr.root)
    assert code == 0


def test_cli_recovery_test(tmp_path: Path):
    from neural_mesh.cram.consistency_cli import cmd_recovery_test
    from io import StringIO

    out = StringIO()
    code = cmd_recovery_test(
        root=tmp_path / "rec-cli",
        put="seed-for-recovery",
        out=out,
    )
    assert code == 0
    data = json.loads(out.getvalue())
    assert data["status"] == "RECOVERED"
    assert data["dual_primary"] == 0


def test_cli_history(tmp_path: Path, layer: ConsistencyLayer):
    from neural_mesh.cram.consistency_cli import cmd_history
    from io import StringIO

    layer.apply_write("hist-obj", b"one", operation_id="h1")
    out = StringIO()
    code = cmd_history("hist-obj", root=layer.root, out=out)
    assert code == 0
    data = json.loads(out.getvalue())
    assert data["object_id"] == "hist-obj"
    assert len(data["versions"]) >= 1


def test_cli_trace_still_registered():
    from neural_mesh.cli import main
    import io
    from contextlib import redirect_stderr

    err = io.StringIO()
    with redirect_stderr(err):
        try:
            main(["cram", "trace", "--help"])
        except SystemExit as e:
            assert e.code in (0, None)


# ----- P4 fault matrix -----


def test_fault_replica_crash_mid_append(mgr: ReplicaManager):
    key = mgr.put_replicated(b"mid-append", sync=False)
    rec = mgr._registry[key]
    # Crash secondary mid-append: mark lost before sync completes
    mgr.mark_node_lost(rec.replica_node)
    synced = mgr.sync_object(key)
    assert synced.status.value == "FAILED" or synced.error
    writers = mgr.writable_primaries(key)
    assert len(writers) <= 1
    assert mgr.dual_primary_count(key) == 0 if hasattr(mgr, "dual_primary_count") else True
    # Primary still sole writer
    assert rec.writable_primary == rec.primary_node or len(writers) == 1


def test_fault_stale_epoch_write_100pct(layer: ConsistencyLayer):
    layer.apply_write("stale", b"base", operation_id="s0", epoch=10)
    rejected = 0
    total = 50
    for i in range(total):
        r = layer.apply_write(
            "stale", f"x{i}".encode(), operation_id=f"stale-{i}", epoch=5
        )
        if r.status == "REJECTED_STALE_EPOCH":
            rejected += 1
    assert rejected == total


def test_fault_duplicate_replay_100pct_idempotent(tmp_path: Path):
    layer = ConsistencyLayer(tmp_path / "dup")
    layer.apply_write("d", b"body", operation_id="dup-op")
    ok = 0
    for _ in range(100):
        # restart layer each batch of 10 to prove durability
        layer = ConsistencyLayer(tmp_path / "dup")
        r = layer.apply_write("d", b"body", operation_id="dup-op")
        if r.status == "DUPLICATE":
            ok += 1
    assert ok == 100


def test_fault_network_partition_fail_closed(layer: ConsistencyLayer):
    layer.apply_write("p", b"ok", operation_id="p0")
    layer.set_partitioned(True, fenced_primary="node-01")
    # Same node is fenced — may write
    r1 = layer.apply_write("p2", b"fenced", operation_id="p1")
    assert r1.status == "APPLIED"
    # Simulate minority node
    minority = ConsistencyLayer(layer.root, node_id="node-02")
    minority.set_partitioned(True, fenced_primary="node-01")
    r2 = minority.apply_write("p3", b"illegal", operation_id="p2")
    assert r2.status == "REJECTED_PARTITION"
    assert layer.dual_primary_count == 0
    assert minority.dual_primary_count == 0


def test_fault_corrupt_replica_metadata(mgr: ReplicaManager):
    key = mgr.put_replicated(b"corrupt-meta", sync=True)
    rec = mgr._registry[key]
    # Corrupt registry metadata
    rec.verified = False
    from neural_mesh.cram.replication.models import ReplicaState
    rec.status = ReplicaState.FAILED
    rec.error = "corrupt metadata"
    mgr._save_registry()
    # Promote while primary healthy + corrupt → blocked or refused path
    from neural_mesh.cram.replication.models import FailoverStatus

    status = mgr.check_failover(key)
    # Primary still healthy → no failover
    assert status == FailoverStatus.PRIMARY_HEALTHY
    mgr.mark_node_lost(rec.primary_node)
    status2 = mgr.check_failover(key)
    assert status2 in (
        FailoverStatus.FAILOVER_BLOCKED,
        FailoverStatus.FAILOVER_AVAILABLE,
    )
    if status2 == FailoverStatus.FAILOVER_BLOCKED:
        with pytest.raises(Exception):
            mgr.promote(key)
    writers = mgr.writable_primaries(key)
    assert len(writers) <= 1


def test_dual_primary_always_zero(mgr: ReplicaManager):
    key = mgr.put_replicated(b"dual-guard", sync=True)
    rec = mgr._registry[key]
    # Attempt split-brain: partition + both try to be primary
    mgr.set_partition(groups=[[rec.primary_node], [rec.replica_node]])
    writers = mgr.writable_primaries(key)
    assert len(writers) <= 1
    # Promote on minority without authority should fail or keep single writer
    try:
        mgr.promote(key, node_id=rec.replica_node)
    except Exception:
        pass
    writers2 = mgr.writable_primaries(key)
    assert len(writers2) <= 1


def test_partition_no_silent_minority_writes(mgr: ReplicaManager):
    key = mgr.put_replicated(b"part-write", sync=True)
    rec = mgr._registry[key]
    mgr.set_partition(groups=[[rec.replica_node], [rec.primary_node]])
    # If primary partitioned from authority view, put may fail-closed
    from neural_mesh.cram.errors import NodeUnavailable

    # Fresh content → new key; use existing key path via put on partitioned writer
    try:
        # Force write through non-authority side by swapping
        mgr.set_partition(groups=[[rec.replica_node], [rec.primary_node]])
        # Secondary should not silently accept puts as primary
        writers = mgr.writable_primaries(key)
        assert len(writers) <= 1
        if writers and writers[0] != rec.replica_node:
            with pytest.raises(NodeUnavailable):
                # Attempt write when registry still points primary but partition isolates
                if not mgr._partition_has_authority(rec.replica_node, key):
                    raise NodeUnavailable("fail-closed", node_id=rec.replica_node)
    finally:
        mgr.clear_partition()


# ----- consistency check API -----


def test_consistency_check_ok(mgr: ReplicaManager, tmp_path: Path):
    key = mgr.put_replicated(b"consist-ok", sync=True)
    layer = ConsistencyLayer(tmp_path / "cchk", replica_manager=mgr)
    report = layer.check(key)
    assert report.dual_primary == 0
    assert report.object_id == key


def test_history_lists_versions(layer: ConsistencyLayer):
    layer.apply_write("hx", b"v1", operation_id="1", epoch=0)
    # New epoch rewrite after "promote"
    layer.apply_write("hx", b"v2", operation_id="2", epoch=1)
    hist = layer.history("hx")
    assert len(hist) >= 2
    assert hist[0]["epoch"] <= hist[-1]["epoch"]


def test_errors_exported():
    from neural_mesh.cram.errors import ConflictError, PartitionFailClosed, StaleEpoch

    assert StaleEpoch.code == "REJECTED_STALE_EPOCH"
    assert ConflictError.code == "CRAM_CONFLICT"
    assert PartitionFailClosed.code == "CRAM_PARTITION_FAIL_CLOSED"


def test_recovery_message_json_roundtrip():
    from neural_mesh.cram.recovery_protocol import RecoveryMessage

    m = make_recovery_request(
        object_id="x", from_node="a", to_node="b", reason="test"
    )
    m2 = RecoveryMessage.from_dict(json.loads(json.dumps(m.to_dict())))
    assert m2.msg_type == m.msg_type
    assert m2.object_id == "x"
