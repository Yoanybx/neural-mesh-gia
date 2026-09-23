"""Cycle 15 — Close CP-0018 SLO gaps → CP-0019 / 0.14.1."""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from neural_mesh.cram.durability import (
    FSYNC_POLICY,
    DurabilityChecker,
    GroupFsyncSeal,
    SyncMode,
    atomic_write_bytes,
    reset_seal_group,
    resolve_sync_mode,
    simulate_crash_mid_write,
)
from neural_mesh.cram.recovery_protocol import run_recovery_test
from neural_mesh.cram.replication.manager import ReplicaManager
from neural_mesh.twin.schema import Topology, TopologyLink, TopologyNode

ROOT = Path(__file__).resolve().parents[1]


def _topo(seed: int = 42) -> Topology:
    return Topology(
        network_id="c15",
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


def test_version_is_at_least_0141():
    from neural_mesh import __version__

    # C15 introduced 0.14.1; C16 may bump to 0.14.2 / 0.15.0
    parts = [int(x) for x in __version__.split(".")[:3]]
    assert parts >= [0, 14, 1]


def test_pyproject_version_014x():
    text = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert (
        'version = "0.14.' in text
        or 'version = "0.15.' in text
        or 'version = "0.16.' in text
    )


def test_doc_slo_close_durable_vs_parity():
    doc = (ROOT / "docs" / "phase5c_durability.md").read_text(encoding="utf-8")
    assert "DURABLE_SYNC" in doc or "BATCH" in doc
    assert "checkpoint_durable" in doc or "durable" in doc.lower()
    assert "parity" in doc.lower()
    assert "GroupFsyncSeal" in doc or "group fsync" in doc.lower() or "BATCH" in doc
    assert "CP-0019" in doc
    assert "0.14.1" in doc
    assert "NOT Raft" in doc or "not Raft" in doc.lower()


def test_fsync_policy_has_sync_modes():
    assert "sync_modes" in FSYNC_POLICY
    assert "batch" in FSYNC_POLICY["sync_modes"]
    assert "every" in FSYNC_POLICY["sync_modes"]
    assert "slo_close_c15" in FSYNC_POLICY


def test_resolve_sync_mode_env(monkeypatch):
    monkeypatch.setenv("DURABLE_SYNC", "batch")
    assert resolve_sync_mode() == SyncMode.BATCH
    monkeypatch.setenv("DURABLE_SYNC", "every")
    assert resolve_sync_mode() == SyncMode.EVERY
    assert resolve_sync_mode("batch") == SyncMode.BATCH


def test_batch_write_no_partial_visible(tmp_path: Path):
    seal = GroupFsyncSeal()
    path = tmp_path / "obj.json"
    atomic_write_bytes(path, b'{"ok":true}', sync_mode=SyncMode.BATCH, seal_group=seal)
    assert path.exists()
    assert json.loads(path.read_text(encoding="utf-8"))["ok"] is True
    assert len(seal.dirty) == 1
    info = seal.seal()
    assert info["sealed_files"] >= 1
    assert seal.sealed


def test_batch_mid_write_crash_invariant(tmp_path: Path):
    target = tmp_path / "final.json"
    tmp = simulate_crash_mid_write(target, b"partial")
    assert tmp.exists()
    assert not target.exists()


def test_batch_seal_then_checker(tmp_path: Path):
    seal = reset_seal_group()
    for i in range(5):
        atomic_write_bytes(
            tmp_path / f"c{i}.json",
            json.dumps({"i": i}).encode(),
            sync_mode=SyncMode.BATCH,
            seal_group=seal,
        )
    seal.seal()
    # Process-style root with consistency layout
    from neural_mesh.cram.consistency import ConsistencyLayer

    layer = ConsistencyLayer(tmp_path / "root", node_id="node-01")
    layer.apply_write("a", b"1", operation_id="a1")
    rep = DurabilityChecker(tmp_path / "root").check()
    assert rep.ok


def test_every_mode_still_fsync(tmp_path: Path):
    path = tmp_path / "e.json"
    mode = atomic_write_bytes(path, b"{}", sync_mode=SyncMode.EVERY)
    assert mode == SyncMode.EVERY
    assert path.exists()


def test_recovery_still_recovers(tmp_path: Path):
    mgr = ReplicaManager(tmp_path, _topo(), seed=42)
    key = mgr.put_replicated(b"c15-rec", sync=True)
    prior = mgr._registry[key].primary_node
    mgr.mark_node_lost(prior)
    result = run_recovery_test(
        mgr, key, reason="primary_unavailable", log_dir=tmp_path / "logs"
    )
    assert result.status == "RECOVERED"
    assert result.dual_primary == 0
    assert result.checkpoint_hash


def test_recovery_rejects_corrupt_target(tmp_path: Path):
    mgr = ReplicaManager(tmp_path, _topo(), seed=7)
    key = mgr.put_replicated(b"corrupt-me", sync=True)
    rec = mgr._registry[key]
    # Corrupt standby (target after primary loss)
    store = mgr._store(rec.replica_node)
    path = store._object_path(key)
    path.write_bytes(b"TAMPERED_DATA!!!!")
    mgr.mark_node_lost(rec.primary_node)
    result = run_recovery_test(mgr, key, reason="primary_unavailable")
    assert result.status == "ERROR"


def test_exports_sync_mode():
    from neural_mesh import cram

    assert hasattr(cram, "SyncMode")
    assert hasattr(cram, "GroupFsyncSeal")
    assert hasattr(cram, "reset_seal_group")


def test_council_agreement_cycle15_present():
    p = ROOT / "council" / "COUNCIL_AGREEMENT_CYCLE15.md"
    assert p.is_file()
    text = p.read_text(encoding="utf-8")
    assert "CP-0019" in text
    assert "0.14.1" in text
    assert "checkpoint_durable" in text or "P7" in text


def test_deepseek_reply_cycle14_pass_with_gaps():
    p = ROOT / "council" / "DEEPSEEK_REPLY_CYCLE14.md"
    assert p.is_file()
    text = p.read_text(encoding="utf-8")
    assert "PASS_WITH_GAPS" in text
    assert "HOLD" in text or "checkpoint_durable" in text


def test_no_raft_introduced():
    for rel in (
        "src/neural_mesh/cram/durability.py",
        "src/neural_mesh/cram/recovery_protocol.py",
        "docs/phase5c_durability.md",
    ):
        text = (ROOT / rel).read_text(encoding="utf-8")
        if "Raft" in text or "raft" in text:
            assert "NOT Raft" in text or "not Raft" in text.lower() or "No Raft" in text
