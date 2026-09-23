"""Cycle 16 — CP-0020 optimize checkpoint_every_floor / 0.14.2."""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from neural_mesh.cram.durability import (
    FSYNC_POLICY,
    DirFsyncCoalescer,
    DurabilityChecker,
    GroupFsyncSeal,
    SyncMode,
    atomic_write_bytes,
    compact_checkpoint_bytes,
    reset_dir_coalescer,
    reset_seal_group,
    resolve_dir_fsync_mode,
    resolve_sync_mode,
    simulate_crash_mid_write,
)
from neural_mesh.cram.recovery_protocol import run_recovery_test
from neural_mesh.cram.replication.manager import ReplicaManager
from neural_mesh.twin.schema import Topology, TopologyLink, TopologyNode

ROOT = Path(__file__).resolve().parents[1]


def _topo(seed: int = 42) -> Topology:
    return Topology(
        network_id="c16",
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


def test_version_is_0142():
    from neural_mesh import __version__

    assert __version__ == "0.14.2"


def test_pyproject_version_0142():
    text = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert 'version = "0.14.2"' in text


def test_doc_every_opt_c16():
    doc = (ROOT / "docs" / "phase5c_durability.md").read_text(encoding="utf-8")
    assert "CP-0020" in doc
    assert "0.14.2" in doc
    assert "DirFsyncCoalescer" in doc
    assert "DURABLE_DIR_FSYNC" in doc
    assert "compact_checkpoint_bytes" in doc
    assert "every_opt_c16" in doc or "Cycle 16" in doc or "EVERY floor" in doc
    assert "NOT Raft" in doc or "not Raft" in doc.lower()


def test_debt_doc_present():
    p = ROOT / "docs" / "debt" / "CHECKPOINT_EVERY_FLOOR.md"
    assert p.is_file()
    text = p.read_text(encoding="utf-8")
    assert "EXPLICIT DEBT" in text
    assert "CP-0020" in text
    assert "0.1" in text


def test_fsync_policy_has_every_opt_c16():
    assert "every_opt_c16" in FSYNC_POLICY
    assert "sync_modes" in FSYNC_POLICY
    assert "every" in FSYNC_POLICY["sync_modes"]
    assert "batch" in FSYNC_POLICY["sync_modes"]


def test_resolve_dir_fsync_mode_env(monkeypatch):
    monkeypatch.setenv("DURABLE_DIR_FSYNC", "coalesce")
    assert resolve_dir_fsync_mode() == "coalesce"
    monkeypatch.setenv("DURABLE_DIR_FSYNC", "every")
    assert resolve_dir_fsync_mode() == "every"
    assert resolve_dir_fsync_mode("coalesce") == "coalesce"


def test_compact_checkpoint_bytes_small():
    b = compact_checkpoint_bytes(7, "abcd")
    assert b.startswith(b"{")
    assert b"7" in b
    assert len(b) < 80


def test_every_os_write_path(tmp_path: Path):
    path = tmp_path / "e.json"
    mode = atomic_write_bytes(path, compact_checkpoint_bytes(1), sync_mode=SyncMode.EVERY)
    assert mode == SyncMode.EVERY
    assert path.exists()


def test_every_dir_coalesce(tmp_path: Path):
    coal = reset_dir_coalescer()
    for i in range(5):
        atomic_write_bytes(
            tmp_path / f"c{i}.json",
            compact_checkpoint_bytes(i),
            sync_mode=SyncMode.EVERY,
            dir_fsync="coalesce",
            dir_coalescer=coal,
        )
    assert len(coal.dirty) >= 1
    info = coal.flush()
    assert info["dirs"] >= 1
    assert not coal.dirty


def test_every_mid_write_crash_invariant(tmp_path: Path):
    target = tmp_path / "final.json"
    tmp = simulate_crash_mid_write(target, b"partial")
    assert tmp.exists()
    assert not target.exists()


def test_batch_still_met_path(tmp_path: Path):
    seal = GroupFsyncSeal()
    path = tmp_path / "b.json"
    atomic_write_bytes(path, b'{"ok":true}', sync_mode=SyncMode.BATCH, seal_group=seal)
    assert path.exists()
    info = seal.seal()
    assert info["sealed_files"] >= 1


def test_recovery_still_recovers(tmp_path: Path):
    mgr = ReplicaManager(tmp_path, _topo(), seed=42)
    key = mgr.put_replicated(b"c16-rec", sync=True)
    prior = mgr._registry[key].primary_node
    mgr.mark_node_lost(prior)
    result = run_recovery_test(
        mgr, key, reason="primary_unavailable", log_dir=tmp_path / "logs"
    )
    assert result.status == "RECOVERED"
    assert result.dual_primary == 0


def test_council_agreement_cycle16_present():
    p = ROOT / "council" / "COUNCIL_AGREEMENT_CYCLE16.md"
    assert p.is_file()
    text = p.read_text(encoding="utf-8")
    assert "CP-0020" in text
    assert "0.14.2" in text or "0.15.0" in text


def test_deepseek_reply_cycle15_present():
    p = ROOT / "council" / "DEEPSEEK_REPLY_CYCLE15.md"
    assert p.is_file()
    text = p.read_text(encoding="utf-8")
    assert "PASS_WITH_HONEST_GAP" in text or "CP-0020" in text or "EVERY" in text


def test_exports_c16_symbols():
    from neural_mesh import cram

    assert hasattr(cram, "DirFsyncCoalescer")
    assert hasattr(cram, "compact_checkpoint_bytes")
    assert hasattr(cram, "reset_dir_coalescer")
    assert hasattr(cram, "resolve_dir_fsync_mode")


def test_no_raft_introduced():
    for rel in (
        "src/neural_mesh/cram/durability.py",
        "docs/phase5c_durability.md",
        "docs/debt/CHECKPOINT_EVERY_FLOOR.md",
    ):
        text = (ROOT / rel).read_text(encoding="utf-8")
        if "Raft" in text or "raft" in text:
            assert "NOT Raft" in text or "not Raft" in text.lower() or "No Raft" in text
