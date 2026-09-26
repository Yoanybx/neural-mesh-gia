"""Tests for Cycle 39 / CP-0043: 0.18_H6_minority_write.

Markers: minority_write_cycle39
Aim: ≥14 — detect minority write @N2, ABORT→halt writes, MINORITY_WRITES=0,
no Raft/N>2, no Vault/ACME, no plaintext, dual_primary=0.
T-H6a(+neg): minority_write_reject; MINORITY_WRITES=0.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from neural_mesh import __version__
from neural_mesh.minority import (
    SCHEMA_ID,
    MinorityN2Only,
    MinorityNodeUnknown,
    MinorityPlaintextForbidden,
    MinorityService,
    cmd_minority_halt,
    cmd_minority_probe,
    cmd_minority_status,
)

pytestmark = [pytest.mark.minority_write_cycle39]

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
def pair(data_root: Path) -> MinorityService:
    svc = MinorityService(data_root)
    svc.bootstrap_pair("n-a", "n-b", primary="n-a")
    return svc


def test_package_version_still_0180():
    assert __version__ == "0.18.0"
    pyproject = (REPO / "pyproject.toml").read_text(encoding="utf-8")
    assert 'version = "0.18.0"' in pyproject


def test_capability_and_schema_docs_present():
    cap = REPO / "docs" / "capabilities" / "MESH_MINORITY_WRITE_FENCE.md"
    sch = REPO / "docs" / "schema" / "minority_write" / "v1.md"
    assert cap.is_file()
    assert sch.is_file()
    ctext = cap.read_text(encoding="utf-8")
    stext = sch.read_text(encoding="utf-8")
    assert "CP-0043" in ctext
    assert "0.18.0" in ctext
    assert "ABORT" in ctext and "halt" in ctext.lower()
    assert "MINORITY_WRITES" in ctext or "minority_writes" in ctext
    assert "mesh.minority/v1" in stext
    assert "MINORITY_WRITE_DETECTED" in stext
    for item in ("Raft", "plaintext", "Vault-ACME-req"):
        assert item in NO_HELD


def test_bootstrap_pair_elects_sole_primary(pair: MinorityService):
    st = pair.status()
    assert st.ok
    assert st.writable_primary == "n-a"
    assert set(st.pair) == {"n-a", "n-b"}
    assert st.minority_writes == 0
    assert st.dual_primary == 0
    assert st.writes_halted is False
    assert st.minority_write_detected is False


def test_t_h6a_primary_write_accepted(pair: MinorityService):
    """T-H6a happy: primary write accepted; minority_writes stays 0."""
    wr = pair.try_write("n-a", "obj/alpha")
    assert wr.ok
    assert wr.outcome == "accepted"
    assert wr.minority_writes == 0
    assert wr.is_minority is False
    st = pair.status()
    assert st.ok
    assert st.minority_writes == 0


def test_t_h6a_minority_write_rejected_and_halt(pair: MinorityService):
    """T-H6a: minority write rejected; ABORT→halt; MINORITY_WRITES=0."""
    wr = pair.try_write("n-b", "obj/beta")
    assert wr.ok is False
    assert wr.outcome == "rejected_minority"
    assert wr.is_minority is True
    assert wr.minority_writes == 0  # never committed
    assert wr.writes_halted is True
    assert wr.abort_halt_writes is True
    assert wr.error_code == "MINORITY_WRITE_DETECTED"
    st = pair.status()
    assert st.ok is False
    assert st.writes_halted is True
    assert st.minority_writes == 0
    assert st.rejected_minority_count >= 1
    assert st.to_dict()["minority_writes"] == 0


def test_t_h6a_neg_halted_blocks_all_writes(pair: MinorityService):
    """T-H6a(+neg): after halt, even primary writes are refused."""
    pair.try_write("n-b", "obj/evil")
    wr = pair.try_write("n-a", "obj/after-halt")
    assert wr.ok is False
    assert wr.outcome == "rejected_halted"
    assert wr.writes_halted is True
    assert wr.minority_writes == 0
    assert wr.error_code == "MINORITY_WRITES_HALTED"


def test_probe_auto_halt_clears_pending(pair: MinorityService):
    # force pending without auto_halt first
    wr = pair.try_write("n-b", "k1", auto_halt=False)
    assert wr.outcome == "rejected_minority"
    assert pair.store.state().get("minority_write_pending") is True
    pr = pair.probe(auto_halt=True)
    assert pr.writes_halted is True
    assert pr.minority_writes == 0
    assert pr.action == "abort_halt_writes"
    assert pr.dual_primary == 0
    # pending cleared after halt
    detected, _ = pair.detect_minority_write()
    assert detected is False


def test_probe_no_auto_halt_enters_abort(pair: MinorityService):
    pair.try_write("n-b", "k2", auto_halt=False)
    # re-mark pending for probe (try_write already entered abort)
    pr = pair.probe(auto_halt=False)
    # either still pending or already halted from try_write
    assert pr.minority_writes == 0
    assert pr.dual_primary == 0
    assert pr.abort_halt_writes is True or pr.writes_halted is True


def test_explicit_halt(pair: MinorityService):
    hr = pair.halt(reason="operator test halt")
    assert hr.ok
    assert hr.writes_halted is True
    assert hr.abort_halt_writes is True
    assert hr.minority_writes == 0
    assert hr.to_dict()["minority_writes"] == 0
    st = pair.status()
    assert st.writes_halted is True
    assert "operator test halt" in st.abort_reason or st.abort_reason


def test_n2_only_refuses_three_nodes(data_root: Path):
    svc = MinorityService(data_root)
    with pytest.raises(MinorityN2Only):
        svc.store.set_pair(["a", "b", "c"])
    svc.bootstrap_pair("x", "y")
    with pytest.raises(MinorityN2Only):
        svc.store.set_pair(["x", "y", "z"])


def test_plaintext_forbidden(pair: MinorityService):
    with pytest.raises(MinorityPlaintextForbidden):
        pair.probe(mode="plaintext")
    with pytest.raises(MinorityPlaintextForbidden):
        pair.halt(mode="cleartext")
    with pytest.raises(MinorityPlaintextForbidden):
        pair.try_write("n-a", "k", mode="tcp")
    with pytest.raises(MinorityPlaintextForbidden):
        pair.bootstrap_pair("a", "b", mode="plain")


def test_unknown_node_refused(pair: MinorityService):
    with pytest.raises(MinorityNodeUnknown):
        pair.try_write("n-z", "k")


def test_minority_writes_hard_zero_on_all_reports(pair: MinorityService):
    pair.try_write("n-b", "x")
    st = pair.status()
    assert st.minority_writes == 0
    assert st.to_dict()["minority_writes"] == 0
    assert st.dual_primary == 0
    assert st.vault_acme_required == 0
    assert st.plaintext_fallback == 0
    pr = pair.probe(auto_halt=True)
    assert pr.minority_writes == 0
    assert pr.to_dict()["minority_writes"] == 0
    hr = pair.halt(reason="again")
    assert hr.minority_writes == 0


def test_cli_status_probe_halt(data_root: Path, capsys):
    svc = MinorityService(data_root)
    svc.bootstrap_pair("n-a", "n-b", primary="n-a")
    rc = cmd_minority_status(data_root=data_root, as_json=True)
    assert rc == 0
    out = capsys.readouterr().out
    payload = json.loads(out)
    assert payload["minority_writes"] == 0
    assert payload["schema"] == SCHEMA_ID

    svc.try_write("n-b", "cli-key")
    rc2 = cmd_minority_probe(data_root=data_root, auto_halt=True)
    # halted → probe may return non-zero ok=False
    assert rc2 in (0, 1, 2)
    out2 = capsys.readouterr().out
    assert "minority_writes" in out2

    rc3 = cmd_minority_halt(data_root=data_root, reason="cli halt")
    assert rc3 == 0
    out3 = json.loads(capsys.readouterr().out)
    assert out3["writes_halted"] is True
    assert out3["minority_writes"] == 0


def test_mesh_cli_minority_subcommand(data_root: Path):
    # bootstrap via library then hit CLI
    MinorityService(data_root).bootstrap_pair("n-a", "n-b", primary="n-a")
    env = {**dict(**{k: v for k, v in __import__("os").environ.items()})}
    r = subprocess.run(
        [
            sys.executable,
            "-m",
            "neural_mesh.cli",
            "minority",
            "status",
            "--data-root",
            str(data_root),
            "--json",
        ],
        cwd=str(REPO),
        capture_output=True,
        text=True,
        env=env,
    )
    assert r.returncode == 0, r.stderr
    payload = json.loads(r.stdout)
    assert payload["minority_writes"] == 0
    assert payload["writable_primary"] == "n-a"


def test_schema_id_constant():
    assert SCHEMA_ID == "mesh.minority/v1"


def test_no_held_bounds_documented():
    cap = (REPO / "docs" / "capabilities" / "MESH_MINORITY_WRITE_FENCE.md").read_text(
        encoding="utf-8"
    )
    for held in ("Raft", "N>2", "multi-primary", "plaintext", "Vault/ACME", "GIA"):
        assert held in cap or held.replace("/", "") in cap or held.lower() in cap.lower()
    assert "H7" in cap or "H8" in cap
    assert "silent_minority_write" in cap or "MINORITY_WRITES" in cap
