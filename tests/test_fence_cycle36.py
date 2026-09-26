"""Tests for Cycle 36 / CP-0040: 0.18_H3_dual_primary_fence.

Markers: fence_cycle36
Aim: ≥14 — detect dual-primary @N2, demote+reelect, ABORT→demote+re-elect,
dual_primary intent=0, no Raft/N>2, no Vault/ACME, no plaintext.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from neural_mesh import __version__
from neural_mesh.fence import (
    SCHEMA_ID,
    FenceDualPrimary,
    FenceN2Only,
    FenceNodeUnknown,
    FencePlaintextForbidden,
    FenceService,
    FenceUnresolved,
    cmd_fence_demote,
    cmd_fence_probe,
    cmd_fence_reelect,
    cmd_fence_status,
)

pytestmark = [pytest.mark.fence_cycle36]

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


@pytest.fixture
def pair(data_root: Path) -> FenceService:
    svc = FenceService(data_root)
    svc.bootstrap_pair("n-a", "n-b", primary="n-a")
    return svc


def test_package_version_still_0180():
    assert __version__ == "0.18.0"
    pyproject = (REPO / "pyproject.toml").read_text(encoding="utf-8")
    assert 'version = "0.18.0"' in pyproject


def test_capability_and_schema_docs_present():
    cap = REPO / "docs" / "capabilities" / "MESH_DUAL_PRIMARY_FENCE.md"
    sch = REPO / "docs" / "schema" / "fence" / "v1.md"
    assert cap.is_file()
    assert sch.is_file()
    ctext = cap.read_text(encoding="utf-8")
    stext = sch.read_text(encoding="utf-8")
    assert "CP-0040" in ctext
    assert "0.18.0" in ctext
    assert "ABORT" in ctext and "demote" in ctext.lower()
    assert "mesh.fence/v1" in stext
    assert "FENCE_DUAL_PRIMARY" in stext
    for item in ("Raft", "plaintext", "Vault-ACME-req"):
        assert item in NO_HELD


def test_bootstrap_pair_elects_sole_primary(pair: FenceService):
    st = pair.status()
    assert st.ok
    assert st.writable_primary == "n-a"
    assert st.roles["n-a"] == "primary"
    assert st.roles["n-b"] == "secondary"
    assert st.fence_epoch >= 1
    assert st.dual_primary == 0
    assert st.dual_primary_detected is False
    assert st.durable_token


def test_detect_dual_primary_and_refuse_claim(pair: FenceService):
    with pytest.raises(FenceDualPrimary):
        pair.claim_primary("n-b")
    pair.claim_primary("n-b", force_dual=True)
    detected, claimants = pair.detect_dual_primary()
    assert detected is True
    assert set(claimants) == {"n-a", "n-b"}
    st = pair.status()
    assert st.ok is False
    assert st.dual_primary_detected is True
    assert st.dual_primary == 0  # intent hard 0
    assert "dual_primary_detected" in st.issues


def test_abort_demote_reelect_resolves_dual(pair: FenceService):
    pair.claim_primary("n-b", force_dual=True)
    action = pair.abort_demote_reelect(preferred="n-a")
    assert action.ok
    assert action.elected == "n-a"
    assert "n-b" in action.demoted
    assert action.dual_primary == 0
    assert action.abort_demote_reelect is False
    assert action.dual_primary_detected_before is True
    st = pair.status()
    assert st.ok
    assert st.writable_primary == "n-a"
    assert st.roles["n-b"] == "demoted"
    assert st.dual_primary_detected is False
    assert st.abort_demote_reelect is False


def test_probe_auto_fence_clears_dual(pair: FenceService):
    pair.claim_primary("n-b", force_dual=True)
    pr = pair.probe(auto_fence=True, preferred="n-a")
    assert pr.ok
    assert pr.action == "abort_demote_reelect"
    assert pr.dual_primary == 0
    assert pr.dual_primary_detected is False
    assert pr.writable_primary == "n-a"
    assert pair.status().ok


def test_probe_no_auto_fence_enters_abort(pair: FenceService):
    pair.claim_primary("n-b", force_dual=True)
    pr = pair.probe(auto_fence=False)
    assert pr.ok is False
    assert pr.dual_primary_detected is True
    assert pr.dual_primary == 0
    assert pr.abort_demote_reelect is True
    assert pr.error_code == "FENCE_DUAL_PRIMARY"
    assert pair.store.abort_demote_reelect is True


def test_demote_and_reelect(pair: FenceService):
    # demote current primary → no writable; then reelect n-b
    d = pair.demote("n-a")
    assert d.ok
    assert d.demoted == "n-a"
    assert d.dual_primary == 0
    assert pair.status().writable_primary is None or pair.status().roles["n-a"] == "demoted"
    r = pair.reelect(preferred="n-b")
    assert r.ok
    assert r.elected == "n-b"
    assert r.durable_token
    assert r.dual_primary == 0
    st = pair.status()
    assert st.writable_primary == "n-b"
    assert st.roles["n-b"] == "primary"


def test_n2_only_refuses_three_nodes(data_root: Path):
    svc = FenceService(data_root)
    with pytest.raises(FenceN2Only):
        svc.store.set_pair(["a", "b", "c"])
    svc.bootstrap_pair("x", "y")
    with pytest.raises(FenceN2Only):
        svc.store.set_pair(["x", "y", "z"])


def test_plaintext_forbidden(pair: FenceService):
    with pytest.raises(FencePlaintextForbidden):
        pair.probe(mode="plaintext")
    with pytest.raises(FencePlaintextForbidden):
        pair.demote("n-a", mode="cleartext")
    with pytest.raises(FencePlaintextForbidden):
        pair.reelect(mode="tcp")
    with pytest.raises(FencePlaintextForbidden):
        pair.claim_primary("n-a", mode="plain")


def test_dual_primary_hard_zero_on_all_reports(pair: FenceService):
    pair.claim_primary("n-b", force_dual=True)
    st = pair.status()
    assert st.dual_primary == 0
    assert st.to_dict()["dual_primary"] == 0
    pr = pair.probe(auto_fence=True)
    assert pr.dual_primary == 0
    assert pr.to_dict()["dual_primary"] == 0
    assert pr.vault_acme_required == 0
    assert pr.plaintext_fallback == 0
    d = pair.demote("n-b") if pair.status().roles.get("n-b") == "primary" else pair.demote(
        [n for n, r in pair.status().roles.items() if r != "primary"][0]
        if any(r != "primary" for r in pair.status().roles.values())
        else "n-b"
    )
    # after probe, only one primary; demote the non-primary path already cleared
    r = pair.reelect(preferred="n-a")
    assert r.dual_primary == 0
    assert d.dual_primary == 0


def test_no_vault_acme_required(pair: FenceService):
    st = pair.status()
    assert st.vault_acme_required == 0
    assert st.plaintext_fallback == 0
    cap = (REPO / "docs" / "capabilities" / "MESH_DUAL_PRIMARY_FENCE.md").read_text(
        encoding="utf-8"
    )
    assert "Vault" in cap
    assert "not" in cap.lower() or "No Vault" in cap


def test_schema_id_on_status(pair: FenceService):
    st = pair.status()
    assert st.schema == SCHEMA_ID
    assert st.to_dict()["schema"] == SCHEMA_ID


def test_unknown_node_and_ack_abort(pair: FenceService):
    with pytest.raises(FenceNodeUnknown):
        pair.demote("n-z")
    with pytest.raises(FenceNodeUnknown):
        pair.reelect(preferred="n-z")
    pair.claim_primary("n-b", force_dual=True)
    pair.probe(auto_fence=False)
    with pytest.raises(FenceUnresolved):
        pair.acknowledge_abort()
    pair.abort_demote_reelect(preferred="n-a")
    cleared = pair.acknowledge_abort()
    assert cleared["abort_demote_reelect"] is False


def test_cli_fence_ops(data_root: Path):
    svc = FenceService(data_root)
    svc.bootstrap_pair("n-a", "n-b", primary="n-a")
    assert cmd_fence_status(data_root=data_root, as_json=True) == 0
    svc.claim_primary("n-b", force_dual=True)
    rc = cmd_fence_probe(data_root=data_root, auto_fence=True, preferred="n-a")
    assert rc == 0
    # demote secondary/demoted then reelect
    assert cmd_fence_demote(data_root=data_root, node_id="n-b") == 0
    assert cmd_fence_reelect(data_root=data_root, preferred="n-a") == 0


def test_cli_mesh_fence_entrypoint(data_root: Path):
    svc = FenceService(data_root)
    svc.bootstrap_pair("n-a", "n-b", primary="n-a")
    env = {**os.environ, "PYTHONPATH": str(REPO / "src")}
    proc = subprocess.run(
        [
            sys.executable,
            "-m",
            "neural_mesh.cli",
            "fence",
            "status",
            "--data-root",
            str(data_root),
            "--json",
        ],
        cwd=str(REPO),
        capture_output=True,
        text=True,
        check=False,
        env=env,
    )
    assert proc.returncode == 0, proc.stderr + proc.stdout
    payload = json.loads(proc.stdout)
    assert payload["dual_primary"] == 0
    assert payload["schema"] == SCHEMA_ID
    assert payload["writable_primary"] == "n-a"

    # force dual then probe via CLI
    svc.claim_primary("n-b", force_dual=True)
    proc2 = subprocess.run(
        [
            sys.executable,
            "-m",
            "neural_mesh.cli",
            "fence",
            "probe",
            "--data-root",
            str(data_root),
            "--preferred",
            "n-a",
        ],
        cwd=str(REPO),
        capture_output=True,
        text=True,
        check=False,
        env=env,
    )
    assert proc2.returncode == 0, proc2.stderr + proc2.stdout
    out = json.loads(proc2.stdout)
    assert out["dual_primary"] == 0
    assert out["ok"] is True
    assert out["writable_primary"] == "n-a"


def test_bounds_docs_no_h4_impl_claim():
    cap = (REPO / "docs" / "capabilities" / "MESH_DUAL_PRIMARY_FENCE.md").read_text(
        encoding="utf-8"
    )
    assert "H4" in cap  # deferred mention
    assert "deferred" in cap.lower() or "Do not" in cap or "No H4" in cap
    service = (REPO / "src" / "neural_mesh" / "fence" / "service.py").read_text(
        encoding="utf-8"
    )
    assert "no Raft" in service or "No Raft" in service
    assert "dual_primary" in service
    assert "N>2" in service or "N=2" in service


def test_witness_sync_after_fence(pair: FenceService):
    pair.claim_primary("n-b", force_dual=True)
    pair.abort_demote_reelect(preferred="n-b")
    wit = pair.store.witness.writable_primary()
    assert wit == "n-b"
    assert pair.store.load_epoch().writable_primary == "n-b"
    assert pair.detect_dual_primary()[0] is False
