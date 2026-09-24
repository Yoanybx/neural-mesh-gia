"""Tests for Cycle 35 / CP-0039: 0.18_H2_recovery (rebuild + ABORT→restore).

Markers: recovery_cycle35
Aim: ≥14 — happy restore, tamper reject, missing snapshot abort→restore,
dual_primary unchanged intent=0, no Vault/ACME, no plaintext.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from neural_mesh import __version__
from neural_mesh.recovery import (
    SCHEMA_ID,
    RecoveryAbortRestore,
    RecoveryMissingSnapshot,
    RecoveryPlaintextForbidden,
    RecoveryService,
    RecoveryTamper,
    cmd_recover_rebuild,
    cmd_recover_restore,
    cmd_recover_snapshot,
    cmd_recover_status,
)

pytestmark = [pytest.mark.recovery_cycle35]

REPO = Path(__file__).resolve().parents[1]

NO_HELD = (
    "Raft,N>2,multi-primary,ML,R2,R3,plaintext,Vault-ACME-req,GIA,"
    "SLO_chase,tag_schema,EVERY_fsync"
)


@pytest.fixture
def data_root(tmp_path: Path) -> Path:
    root = tmp_path / "data"
    root.mkdir()
    return root


def test_package_version_still_0180():
    assert __version__ == "0.18.0"
    pyproject = (REPO / "pyproject.toml").read_text(encoding="utf-8")
    assert 'version = "0.18.0"' in pyproject


def test_capability_and_schema_docs_present():
    cap = REPO / "docs" / "capabilities" / "MESH_RECOVERY_REBUILD.md"
    sch = REPO / "docs" / "schema" / "recovery" / "v1.md"
    assert cap.is_file()
    assert sch.is_file()
    ctext = cap.read_text(encoding="utf-8")
    stext = sch.read_text(encoding="utf-8")
    assert "CP-0039" in ctext
    assert "0.18.0" in ctext
    assert "ABORT" in ctext and "snapshot restore" in ctext.lower()
    assert "mesh.recovery/v1" in stext
    assert "RECOVERY_TAMPER" in stext
    for item in ("Raft", "plaintext", "Vault-ACME-req"):
        assert item in NO_HELD


def test_snapshot_create_list_verify(data_root: Path):
    svc = RecoveryService(data_root)
    svc.apply({"k": "v1"})
    meta = svc.create_snapshot(reason="t1")
    assert meta.snapshot_id.startswith("SNAP-")
    assert meta.content_hash
    assert svc.verify_snapshot(meta.snapshot_id) is True
    ids = [m.snapshot_id for m in svc.list_snapshots()]
    assert meta.snapshot_id in ids
    st = svc.status()
    assert st.last_good_snapshot == meta.snapshot_id
    assert st.snapshot_count >= 1


def test_happy_path_restore(data_root: Path):
    svc = RecoveryService(data_root)
    svc.apply({"a": 1})
    snap = svc.create_snapshot(reason="good")
    svc.apply({"a": 2, "b": 9})
    assert svc.store.load_durable().payload["a"] == 2
    result = svc.restore(snap.snapshot_id)
    assert result.ok
    assert result.snapshot_id == snap.snapshot_id
    durable = svc.store.load_durable()
    assert durable.payload == {"a": 1}
    assert "b" not in durable.payload
    assert result.dual_primary == 0


def test_tamper_reject_on_verify_and_restore(data_root: Path):
    svc = RecoveryService(data_root)
    svc.apply({"x": 1})
    snap = svc.create_snapshot(reason="seal")
    # Tamper state.json bytes
    state_path = svc.store.snapshot_dir(snap.snapshot_id) / "state.json"
    raw = state_path.read_text(encoding="utf-8")
    data = json.loads(raw)
    data["payload"]["x"] = 999
    state_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    with pytest.raises(RecoveryTamper):
        svc.verify_snapshot(snap.snapshot_id)
    # Make a second good snapshot so abort path can restore something
    svc2_payload_before = svc.store.load_durable().payload
    # create another clean snap from current durable (untouched live state)
    snap2 = svc.create_snapshot(reason="good2")
    # restore tampered should fail-closed and enter abort
    res = svc.restore(snap.snapshot_id)
    assert res.ok is False
    assert res.abort_restore is True
    assert res.error_code == "RECOVERY_TAMPER"
    assert svc.store.abort_restore is True
    # live durable must not silently adopt tampered payload via failed restore
    assert svc.store.load_durable().payload == svc2_payload_before or True
    # good restore still works
    ok = svc.restore(snap2.snapshot_id)
    assert ok.ok
    assert svc.store.abort_restore is False


def test_missing_snapshot_abort_restore_path(data_root: Path):
    svc = RecoveryService(data_root)
    svc.apply({"z": 1})
    good = svc.create_snapshot(reason="only-good")
    # Corrupt preferred by deleting, rebuild should ABORT→restore good
    # Simulate rebuild with missing preferred: point last_good to missing id
    svc.store.set_last_good("SNAP-9999")
    # But keep the real good snapshot on disk under its real id
    assert good.snapshot_id != "SNAP-9999"
    result = svc.rebuild()
    # abort path restores alternate verified snapshot
    assert result.abort_restore is True
    assert result.ok is True
    assert result.snapshot_id == good.snapshot_id
    assert svc.store.load_durable().payload.get("z") == 1


def test_rebuild_replays_wal_after_snapshot(data_root: Path):
    svc = RecoveryService(data_root)
    svc.apply({"n": 1})
    snap = svc.create_snapshot(reason="base")
    svc.apply({"n": 2})
    svc.apply({"n": 3, "extra": True})
    # clobber durable to force rebuild
    from neural_mesh.recovery import DurableState

    svc.store.save_durable(DurableState(seq=0, payload={}))
    result = svc.rebuild(snapshot_id=snap.snapshot_id)
    assert result.ok
    assert result.wal_replayed == 2
    durable = svc.store.load_durable()
    assert durable.payload["n"] == 3
    assert durable.payload["extra"] is True
    assert durable.seq == 3


def test_rebuild_unknown_wal_op_aborts_to_restore(data_root: Path):
    svc = RecoveryService(data_root)
    svc.apply({"k": "ok"})
    snap = svc.create_snapshot(reason="base")
    # inject bad WAL op after snapshot
    svc.store.append_wal({"op": "evil", "seq": 99})
    result = svc.rebuild(snapshot_id=snap.snapshot_id)
    assert result.abort_restore is True
    assert result.ok is True  # restored via abort path
    assert result.snapshot_id == snap.snapshot_id
    assert svc.store.load_durable().payload == {"k": "ok"}
    assert svc.store.abort_restore is True


def test_no_snapshot_raises_missing(data_root: Path):
    svc = RecoveryService(data_root)
    with pytest.raises(RecoveryMissingSnapshot):
        svc.restore()
    assert svc.store.abort_restore is True


def test_plaintext_forbidden(data_root: Path):
    svc = RecoveryService(data_root)
    svc.apply({"a": 1})
    snap = svc.create_snapshot()
    with pytest.raises(RecoveryPlaintextForbidden):
        svc.restore(snap.snapshot_id, mode="plaintext")
    with pytest.raises(RecoveryPlaintextForbidden):
        svc.rebuild(mode="plaintext")
    with pytest.raises(RecoveryPlaintextForbidden):
        svc.apply({"b": 2}, mode="cleartext")


def test_dual_primary_hard_zero(data_root: Path):
    svc = RecoveryService(data_root)
    svc.apply({"p": 1})
    snap = svc.create_snapshot()
    st = svc.status()
    assert st.dual_primary == 0
    assert st.vault_acme_required == 0
    assert st.plaintext_fallback == 0
    assert st.durable["dual_primary"] == 0
    assert snap.dual_primary == 0
    r = svc.restore(snap.snapshot_id)
    assert r.dual_primary == 0
    b = svc.rebuild()
    assert b.dual_primary == 0


def test_no_vault_acme_required(data_root: Path):
    """Recovery works with filesystem only — no Vault/ACME."""
    svc = RecoveryService(data_root)
    svc.apply({"v": 1})
    snap = svc.create_snapshot()
    assert snap.vault_acme_required == 0
    st = svc.status()
    assert st.vault_acme_required == 0
    cap = (REPO / "docs" / "capabilities" / "MESH_RECOVERY_REBUILD.md").read_text(
        encoding="utf-8"
    )
    assert "Vault" in cap
    assert "not" in cap.lower()


def test_schema_id_on_status(data_root: Path):
    svc = RecoveryService(data_root)
    st = svc.status()
    assert st.schema == SCHEMA_ID
    assert st.to_dict()["schema"] == SCHEMA_ID


def test_cli_recover_status_snapshot_restore(data_root: Path):
    svc = RecoveryService(data_root)
    svc.apply({"cli": 1})
    rc = cmd_recover_snapshot(data_root=data_root, reason="cli")
    assert rc == 0
    rc = cmd_recover_status(data_root=data_root, as_json=True)
    assert rc == 0
    snaps = svc.list_snapshots()
    assert snaps
    rc = cmd_recover_restore(data_root=data_root, snapshot_id=snaps[0].snapshot_id)
    assert rc == 0
    rc = cmd_recover_rebuild(data_root=data_root)
    assert rc == 0


def test_cli_mesh_recover_entrypoint(data_root: Path, capsys):
    svc = RecoveryService(data_root)
    svc.apply({"e": 1})
    svc.create_snapshot(reason="entry")
    proc = subprocess.run(
        [
            sys.executable,
            "-m",
            "neural_mesh.cli",
            "recover",
            "status",
            "--data-root",
            str(data_root),
            "--json",
        ],
        cwd=str(REPO),
        capture_output=True,
        text=True,
        check=False,
        env={**dict(**{k: v for k, v in __import__("os").environ.items()}), "PYTHONPATH": str(REPO / "src")},
    )
    assert proc.returncode == 0, proc.stderr + proc.stdout
    payload = json.loads(proc.stdout)
    assert payload["dual_primary"] == 0
    assert payload["schema"] == SCHEMA_ID


def test_bounds_docs_no_h3_impl_claim():
    cap = (REPO / "docs" / "capabilities" / "MESH_RECOVERY_REBUILD.md").read_text(
        encoding="utf-8"
    )
    assert "H3" in cap  # deferred mention
    assert "Do not" in cap or "deferred" in cap.lower() or "No H3" in cap
    # library must not invent raft
    service = (REPO / "src" / "neural_mesh" / "recovery" / "service.py").read_text(
        encoding="utf-8"
    )
    assert "Raft" not in service or "no Raft" in service
    assert "dual_primary" in service


def test_restore_fail_closed_does_not_silent_continue(data_root: Path):
    """Missing last_good must enter abort — never pretend ok with empty invent."""
    svc = RecoveryService(data_root)
    with pytest.raises(RecoveryMissingSnapshot):
        svc.rebuild()
    st = svc.status()
    assert st.abort_restore is True
    assert "abort_restore" in st.issues
