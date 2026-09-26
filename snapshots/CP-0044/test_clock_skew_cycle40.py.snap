"""Tests for Cycle 40 / CP-0044: 0.18_H7_clock_skew.

Markers: clock_skew_cycle40
Aim: ≥14 — detect clock skew @N2, ABORT→refuse join, wall_clock_as_authority=0,
HLC + monotonic helpers, no Raft/N>2, no Vault/ACME, no plaintext, dual_primary=0.
T-H7a(+neg): skew refuse join; wall non-authoritative.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from neural_mesh import __version__
from neural_mesh.clock import (
    DEFAULT_SKEW_THRESHOLD_MS,
    SCHEMA_ID,
    ClockN2Only,
    ClockNodeUnknown,
    ClockPlaintextForbidden,
    ClockService,
    HLC,
    compare_hlc,
    cmd_clock_join_check,
    cmd_clock_probe,
    cmd_clock_status,
    skew_ms_diagnostic,
)

pytestmark = [pytest.mark.clock_skew_cycle40]

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
def pair(data_root: Path) -> ClockService:
    svc = ClockService(data_root)
    svc.bootstrap_pair("n-a", "n-b", skew_threshold_ms=5000)
    return svc


def test_package_version_still_0180():
    assert __version__ == "0.18.0"
    pyproject = (REPO / "pyproject.toml").read_text(encoding="utf-8")
    assert 'version = "0.18.0"' in pyproject


def test_capability_and_schema_docs_present():
    cap = REPO / "docs" / "capabilities" / "MESH_CLOCK_SKEW_FENCE.md"
    sch = REPO / "docs" / "schema" / "clock_skew" / "v1.md"
    assert cap.is_file()
    assert sch.is_file()
    ctext = cap.read_text(encoding="utf-8")
    stext = sch.read_text(encoding="utf-8")
    assert "CP-0044" in ctext
    assert "0.18.0" in ctext
    assert "ABORT" in ctext and "refuse" in ctext.lower()
    assert "wall_clock_as_authority" in ctext
    assert "HLC" in ctext or "hlc" in ctext.lower()
    assert "P-02" in ctext or "P-02" in stext
    assert "mesh.clock/v1" in stext
    assert "CLOCK_SKEW_DETECTED" in stext
    for item in ("Raft", "plaintext", "Vault-ACME-req"):
        assert item in NO_HELD


def test_bootstrap_pair_sets_threshold(pair: ClockService):
    st = pair.status()
    assert st.ok
    assert set(st.pair) == {"n-a", "n-b"}
    assert st.skew_threshold_ms == 5000
    assert st.wall_clock_as_authority == 0
    assert st.dual_primary == 0
    assert st.minority_writes == 0
    assert st.join_refused is False
    assert st.skew_detected is False


def test_t_h7a_join_within_threshold_accepted(pair: ClockService):
    """T-H7a happy: join with small wall delta accepted; wall not authority."""
    base = 1_700_000_000_000
    jr = pair.join_check(
        "n-b",
        local_wall_ms=base,
        peer_wall_ms=base + 100,
    )
    assert jr.ok
    assert jr.outcome == "accepted"
    assert jr.skew_ms == 100
    assert jr.wall_clock_as_authority == 0
    assert jr.join_refused is False
    st = pair.status()
    assert st.ok
    assert st.wall_clock_as_authority == 0


def test_t_h7a_skew_refused_and_abort(pair: ClockService):
    """T-H7a: excess skew → refused_skew; ABORT→refuse join; wall_authority=0."""
    base = 1_700_000_000_000
    jr = pair.join_check(
        "n-b",
        local_wall_ms=base,
        peer_wall_ms=base + 10_000,  # > 5000 threshold
    )
    assert jr.ok is False
    assert jr.outcome == "refused_skew"
    assert jr.skew_ms == 10_000
    assert jr.join_refused is True
    assert jr.abort_refuse_join is True
    assert jr.wall_clock_as_authority == 0
    assert jr.error_code == "CLOCK_SKEW_DETECTED"
    st = pair.status()
    assert st.ok is False
    assert st.join_refused is True
    assert st.wall_clock_as_authority == 0
    assert st.to_dict()["wall_clock_as_authority"] == 0


def test_t_h7a_neg_refused_blocks_further_joins(pair: ClockService):
    """T-H7a(+neg): after refuse, further joins refused_abort."""
    base = 1_700_000_000_000
    pair.join_check("n-b", local_wall_ms=base, peer_wall_ms=base + 20_000)
    jr = pair.join_check("n-b", local_wall_ms=base, peer_wall_ms=base + 50)
    assert jr.ok is False
    assert jr.outcome == "refused_abort"
    assert jr.join_refused is True
    assert jr.wall_clock_as_authority == 0
    assert jr.error_code == "CLOCK_JOIN_REFUSED"


def test_hlc_tick_and_merge_wall_non_authoritative(pair: ClockService):
    """HLC ordering ignores wall for compare; merge advances logical/counter."""
    h0 = pair.tick(wall_ms=1000)
    h1 = pair.tick(wall_ms=900)  # wall went backwards — must not rewind HLC
    assert h1.logical >= h0.logical
    assert (h1.logical, h1.counter) > (h0.logical, h0.counter) or h1.counter > h0.counter
    remote = HLC(logical=h1.logical + 5, counter=0, wall_ms=50)
    h2 = pair.receive_hlc(remote, wall_ms=50)
    assert h2.logical >= remote.logical
    assert compare_hlc(h2, remote) >= 0
    # wall alone must not dominate compare when logical equal path differs
    a = HLC(logical=10, counter=1, wall_ms=99999)
    b = HLC(logical=10, counter=2, wall_ms=1)
    assert compare_hlc(a, b) == -1  # counter decides, not wall


def test_monotonic_counter_strictly_increases(pair: ClockService):
    a = pair.mono_next()
    b = pair.mono_next()
    c = pair.mono_next()
    assert a < b < c
    assert pair.local_mono == c


def test_probe_auto_refuse_on_pending(pair: ClockService):
    base = 1_700_000_000_000
    pair.record_sample("n-a", wall_ms=base)
    pair.record_sample("n-b", wall_ms=base + 12_000)
    detected, skew, nodes = pair.detect_skew()
    assert detected is True
    assert skew == 12_000
    pr = pair.probe(auto_refuse=True)
    assert pr.join_refused is True
    assert pr.wall_clock_as_authority == 0
    assert pr.action == "abort_refuse_join"
    assert pr.dual_primary == 0
    assert pr.minority_writes == 0
    detected2, _, _ = pair.detect_skew()
    assert detected2 is False  # pending cleared into refuse


def test_probe_no_auto_refuse_enters_abort(pair: ClockService):
    base = 1_700_000_000_000
    pair.record_sample("n-a", wall_ms=base)
    pair.record_sample("n-b", wall_ms=base + 15_000)
    pr = pair.probe(auto_refuse=False)
    assert pr.wall_clock_as_authority == 0
    assert pr.dual_primary == 0
    assert pr.abort_refuse_join is True or pr.join_refused is True
    assert pr.skew_detected is True or pr.action == "abort_refuse_join"


def test_n2_only_refuses_three_nodes(data_root: Path):
    svc = ClockService(data_root)
    with pytest.raises(ClockN2Only):
        svc.store.set_pair(["a", "b", "c"])
    svc.bootstrap_pair("x", "y")
    with pytest.raises(ClockN2Only):
        svc.store.set_pair(["x", "y", "z"])


def test_plaintext_forbidden(pair: ClockService):
    with pytest.raises(ClockPlaintextForbidden):
        pair.probe(mode="plaintext")
    with pytest.raises(ClockPlaintextForbidden):
        pair.join_check("n-b", mode="cleartext")
    with pytest.raises(ClockPlaintextForbidden):
        pair.record_sample("n-a", mode="tcp")
    with pytest.raises(ClockPlaintextForbidden):
        pair.bootstrap_pair("a", "b", mode="plain")


def test_unknown_node_refused(pair: ClockService):
    with pytest.raises(ClockNodeUnknown):
        pair.join_check("n-z", local_wall_ms=1, peer_wall_ms=1)


def test_wall_clock_as_authority_hard_zero_on_all_reports(pair: ClockService):
    base = 1_700_000_000_000
    pair.join_check("n-b", local_wall_ms=base, peer_wall_ms=base + 20_000)
    st = pair.status()
    assert st.wall_clock_as_authority == 0
    assert st.to_dict()["wall_clock_as_authority"] == 0
    assert st.dual_primary == 0
    assert st.minority_writes == 0
    assert st.vault_acme_required == 0
    assert st.plaintext_fallback == 0
    pr = pair.probe(auto_refuse=True)
    assert pr.wall_clock_as_authority == 0
    assert pr.to_dict()["wall_clock_as_authority"] == 0


def test_cli_status_probe_join_check(data_root: Path, capsys):
    svc = ClockService(data_root)
    svc.bootstrap_pair("n-a", "n-b", skew_threshold_ms=5000)
    rc = cmd_clock_status(data_root=data_root, as_json=True)
    assert rc == 0
    out = capsys.readouterr().out
    payload = json.loads(out)
    assert payload["wall_clock_as_authority"] == 0
    assert payload["schema"] == SCHEMA_ID

    base = 1_700_000_000_000
    svc.record_sample("n-a", wall_ms=base)
    svc.record_sample("n-b", wall_ms=base + 9000)
    rc2 = cmd_clock_probe(data_root=data_root, auto_refuse=True)
    assert rc2 in (0, 1, 2)
    out2 = capsys.readouterr().out
    assert "wall_clock_as_authority" in out2

    # fresh root for join-check accept path
    root2 = data_root.parent / "data2"
    root2.mkdir()
    ClockService(root2).bootstrap_pair("n-a", "n-b")
    rc3 = cmd_clock_join_check(
        data_root=root2,
        node_id="n-b",
        peer_wall_ms=base + 10,
        local_wall_ms=base,
    )
    assert rc3 == 0
    out3 = json.loads(capsys.readouterr().out)
    assert out3["outcome"] == "accepted"
    assert out3["wall_clock_as_authority"] == 0


def test_mesh_cli_clock_subcommand(data_root: Path):
    ClockService(data_root).bootstrap_pair("n-a", "n-b", skew_threshold_ms=5000)
    env = {**dict(**{k: v for k, v in __import__("os").environ.items()})}
    r = subprocess.run(
        [
            sys.executable,
            "-m",
            "neural_mesh.cli",
            "clock",
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
    assert payload["wall_clock_as_authority"] == 0
    assert set(payload["pair"]) == {"n-a", "n-b"}


def test_schema_id_and_defaults():
    assert SCHEMA_ID == "mesh.clock/v1"
    assert DEFAULT_SKEW_THRESHOLD_MS == 5000
    assert skew_ms_diagnostic(10, 25) == 15


def test_no_held_bounds_documented():
    cap = (REPO / "docs" / "capabilities" / "MESH_CLOCK_SKEW_FENCE.md").read_text(
        encoding="utf-8"
    )
    for held in ("Raft", "N>2", "multi-primary", "plaintext", "Vault/ACME", "GIA"):
        assert held in cap or held.replace("/", "") in cap or held.lower() in cap.lower()
    assert "H8" in cap
    assert "wall_clock_as_authority" in cap
