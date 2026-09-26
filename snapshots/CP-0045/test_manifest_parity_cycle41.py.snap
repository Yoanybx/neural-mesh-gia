"""Tests for Cycle 41 / CP-0045: 0.18_H8_manifest_parity.

Markers: manifest_parity_cycle41
Aim: ≥14 — byte-equality under concurrent build @N2, toolchain pin (P-09),
ABORT→reject build, extend manifest_n2 core_parity, no Raft/N>2,
no Vault/ACME, no plaintext, dual_primary=0, no reopen 0.16.3/0.17.0.
T-H8a(+neg): concurrent match; mismatch→reject build.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from neural_mesh import __version__
from neural_mesh.packaging.parity import (
    SCHEMA_ID,
    ParityAbortRejectBuild,
    ParityFrozenChannel,
    ParityN2Only,
    ParityPlaintextForbidden,
    ParityService,
    ParityToolchainMismatch,
    canonical_manifest_bytes,
    cmd_parity_build_check,
    cmd_parity_check,
    cmd_parity_status,
    compare_checksum_maps,
    compute_toolchain_pin,
)

pytestmark = [pytest.mark.manifest_parity_cycle41]

REPO = Path(__file__).resolve().parents[1]

NO_HELD = (
    "Raft,N>2,multi-primary,ML,R2,R3,plaintext,Vault-ACME-req,GIA,"
    "SLO_chase,tag_schema,EVERY_fsync"
)


def _manifest(ver: str = "0.18.0", tip: str = "abc1234", **extra) -> dict:
    base = {
        "schema": "mesh.bundle.manifest/v1-n2",
        "name": "neural-mesh-gia-n2",
        "ver": ver,
        "tip": tip,
        "cp_range": "CP-0001..0045",
        "topology": "n2",
        "roles": ["primary", "secondary"],
        "dual_primary": 0,
        "majority": "fenced_primary_heal",
        "checksums": {
            "pyproject.toml": "aa" * 32,
            "src/neural_mesh/__init__.py": "bb" * 32,
        },
        "bundle_sha256": "cc" * 32,
    }
    base.update(extra)
    return base


@pytest.fixture
def data_root(tmp_path: Path) -> Path:
    root = tmp_path / "data"
    root.mkdir()
    return root


@pytest.fixture
def pair(data_root: Path) -> ParityService:
    svc = ParityService(data_root)
    svc.bootstrap_pair("build-a", "build-b")
    return svc


def test_package_version_still_0180():
    assert __version__ == "0.18.0"
    pyproject = (REPO / "pyproject.toml").read_text(encoding="utf-8")
    assert 'version = "0.18.0"' in pyproject


def test_capability_and_schema_docs_present():
    cap = REPO / "docs" / "capabilities" / "MESH_MANIFEST_PARITY.md"
    sch = REPO / "docs" / "schema" / "manifest_parity" / "v1.md"
    assert cap.is_file()
    assert sch.is_file()
    ctext = cap.read_text(encoding="utf-8")
    stext = sch.read_text(encoding="utf-8")
    assert "CP-0045" in ctext
    assert "0.18.0" in ctext
    assert "ABORT" in ctext and "reject" in ctext.lower()
    assert "byte-equality" in ctext.lower() or "byte equality" in ctext.lower()
    assert "0.18_signoff" in ctext
    assert "mesh.manifest.parity/v1" in stext
    assert "PARITY_MISMATCH" in stext
    assert "PARITY_ABORT_REJECT_BUILD" in stext
    for item in ("Raft", "plaintext", "Vault-ACME-req"):
        assert item in NO_HELD


def test_bootstrap_pair_pins_toolchain(pair: ParityService):
    st = pair.status()
    assert set(st.pair) == {"build-a", "build-b"}
    assert st.build_rejected is False
    assert st.dual_primary == 0
    assert st.minority_writes == 0
    assert st.toolchain.get("pin_hash")
    assert st.toolchain.get("schema") == "mesh.manifest.parity.toolchain/v1"


def test_t_h8a_matched_byte_equality(pair: ParityService):
    """T-H8a happy: identical manifests → matched; dual_primary=0."""
    m = _manifest()
    pair.record_build("build-a", m)
    pair.record_build("build-b", m)
    r = pair.check()
    assert r.ok
    assert r.outcome == "matched"
    assert r.parity_ok is True
    assert r.digest_a == r.digest_b
    assert r.dual_primary == 0
    assert r.build_rejected is False
    st = pair.status()
    assert st.ok
    assert st.parity_ok is True


def test_t_h8a_mismatch_abort_reject_build(pair: ParityService):
    """T-H8a: digest mismatch → ABORT→reject build."""
    pair.record_build("build-a", _manifest(tip="aaaaaaa"))
    pair.record_build("build-b", _manifest(tip="bbbbbbb"))
    r = pair.check()
    assert r.ok is False
    assert r.outcome == "mismatch"
    assert r.abort_reject_build is True
    assert r.build_rejected is True
    assert r.error_code == "PARITY_MISMATCH"
    assert "canonical_manifest" in r.mismatch_paths
    st = pair.status()
    assert st.build_rejected is True
    assert st.ok is False


def test_t_h8a_neg_rejected_blocks_further_builds(pair: ParityService):
    """T-H8a neg: after reject, further record_build / check fail-closed."""
    pair.record_build("build-a", _manifest(tip="aaaaaaa"))
    pair.record_build("build-b", _manifest(tip="bbbbbbb"))
    pair.check()
    with pytest.raises(ParityAbortRejectBuild):
        pair.record_build("build-a", _manifest())
    r2 = pair.check()
    assert r2.outcome == "rejected_abort"
    assert r2.abort_reject_build is True
    assert r2.error_code == "PARITY_ABORT_REJECT_BUILD"


def test_concurrent_build_byte_equal(pair: ParityService):
    """Concurrent builders produce byte-equal digests @N2."""
    pin = compute_toolchain_pin()

    def builder():
        return _manifest(tip="same001", toolchain=pin.to_dict())

    cbr = pair.concurrent_build_check(builder)
    assert cbr.ok
    assert cbr.byte_equal is True
    assert cbr.parity_ok is True
    assert cbr.digest_a == cbr.digest_b
    assert cbr.dual_primary == 0


def test_concurrent_build_mismatch_rejects(pair: ParityService):
    """Non-deterministic concurrent builder → mismatch → reject."""
    state = {"n": 0}

    def builder():
        state["n"] += 1
        return _manifest(tip=f"diff{state['n']:04d}")

    cbr = pair.concurrent_build_check(builder)
    assert cbr.ok is False
    assert cbr.byte_equal is False
    assert cbr.abort_reject_build is True
    assert cbr.error_code == "PARITY_MISMATCH"


def test_concurrent_workers_must_be_n2(pair: ParityService):
    with pytest.raises(ParityN2Only):
        pair.concurrent_build_check(lambda: _manifest(), workers=3)


def test_core_parity_vs_single_match_and_mismatch(pair: ParityService):
    good = {
        "pyproject.toml": "aa" * 32,
        "src/neural_mesh/__init__.py": "bb" * 32,
    }
    r = pair.core_parity_vs_single(good, good)
    assert r.ok and r.parity_ok

    pair2 = ParityService(pair.data_root.parent / "data2")
    pair2.bootstrap_pair("n-a", "n-b")
    bad = dict(good)
    bad["pyproject.toml"] = "ff" * 32
    r2 = pair2.core_parity_vs_single(good, bad)
    assert r2.ok is False
    assert r2.abort_reject_build is True
    assert r2.error_code == "PARITY_MISMATCH"


def test_canonical_bytes_strip_created_utc_and_force_dual_primary():
    m1 = _manifest(created_utc="2026-01-01T00:00:00Z")
    m2 = _manifest(created_utc="2099-12-31T23:59:59Z")
    m2["dual_primary"] = 1  # forced to 0 in canonical
    assert canonical_manifest_bytes(m1) == canonical_manifest_bytes(m2)
    # Tip change breaks equality
    m3 = _manifest(tip="other01")
    assert canonical_manifest_bytes(m1) != canonical_manifest_bytes(m3)


def test_compare_checksum_maps_and_toolchain_pin():
    ok, errs = compare_checksum_maps({"a": "1"}, {"a": "1"})
    assert ok and not errs
    ok2, errs2 = compare_checksum_maps({"a": "1"}, {"a": "2"})
    assert not ok2 and "a" in errs2
    pin = compute_toolchain_pin(compiler="cpython-3.13", libc="glibc", locale="C.UTF-8")
    assert len(pin.pin_hash) == 64
    pin2 = compute_toolchain_pin(compiler="cpython-3.13", libc="glibc", locale="C.UTF-8")
    assert pin.pin_hash == pin2.pin_hash


def test_plaintext_forbidden_and_frozen_channel(data_root: Path):
    svc = ParityService(data_root)
    with pytest.raises(ParityFrozenChannel):
        svc.bootstrap_pair("a", "b", channel="0.17.0")
    svc.bootstrap_pair("a", "b")
    with pytest.raises(ParityPlaintextForbidden):
        svc.record_build("a", _manifest(), mode="plaintext")
    with pytest.raises(ParityPlaintextForbidden):
        svc.check(mode="plaintext")


def test_n2_only_refuses_duplicate_and_toolchain_expect(data_root: Path):
    svc = ParityService(data_root)
    with pytest.raises(ParityN2Only):
        svc.bootstrap_pair("same", "same")
    svc.bootstrap_pair("a", "b")
    m = _manifest()
    svc.record_build("a", m)
    svc.record_build("b", m)
    with pytest.raises(ParityToolchainMismatch):
        svc.check(expect_toolchain_pin="0" * 64)


def test_check_no_auto_reject_enters_abort(pair: ParityService):
    pair.record_build("build-a", _manifest(tip="aaaaaaa"))
    pair.record_build("build-b", _manifest(tip="bbbbbbb"))
    r = pair.check(auto_reject=False)
    assert r.ok is False
    assert r.abort_reject_build is True
    assert r.mismatch_detected is True
    assert r.action == "abort_reject_build"


def test_cli_status_check_build_check(data_root: Path, capsys):
    svc = ParityService(data_root)
    svc.bootstrap_pair("build-a", "build-b")
    m = _manifest()
    svc.record_build("build-a", m)
    svc.record_build("build-b", m)
    rc = cmd_parity_status(data_root=data_root, as_json=True)
    assert rc == 0
    out = capsys.readouterr().out
    assert SCHEMA_ID in out or "parity_ok" in out
    rc2 = cmd_parity_check(data_root=data_root, as_json=True)
    assert rc2 == 0
    # fresh root for build-check concurrent smoke
    root2 = data_root.parent / "bc"
    root2.mkdir()
    rc3 = cmd_parity_build_check(data_root=root2, as_json=True)
    assert rc3 == 0


def test_mesh_cli_parity_subcommand(data_root: Path):
    # bootstrap via library then invoke CLI
    svc = ParityService(data_root)
    svc.bootstrap_pair("build-a", "build-b")
    m = _manifest()
    svc.record_build("build-a", m)
    svc.record_build("build-b", m)
    env = {**dict(**{k: v for k, v in __import__("os").environ.items()})}
    env["PYTHONPATH"] = str(REPO / "src")
    r = subprocess.run(
        [
            sys.executable,
            "-m",
            "neural_mesh.cli",
            "parity",
            "status",
            "--data-root",
            str(data_root),
            "--json",
        ],
        cwd=str(REPO),
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert r.returncode == 0, r.stderr + r.stdout
    payload = json.loads(r.stdout)
    assert payload.get("schema") == SCHEMA_ID
    assert payload.get("dual_primary") == 0


def test_dual_primary_hard_zero_on_all_reports(pair: ParityService):
    m = _manifest()
    pair.record_build("build-a", m)
    pair.record_build("build-b", m)
    r = pair.check()
    assert r.to_dict()["dual_primary"] == 0
    assert r.to_dict()["minority_writes"] == 0
    assert r.to_dict()["vault_acme_required"] == 0
    assert r.to_dict()["plaintext_fallback"] == 0
    st = pair.status().to_dict()
    assert st["dual_primary"] == 0
    assert st["schema"] == SCHEMA_ID


def test_no_held_bounds_and_no_retag_docs():
    cap = (REPO / "docs" / "capabilities" / "MESH_MANIFEST_PARITY.md").read_text(
        encoding="utf-8"
    )
    assert "NO_HELD" in cap or "No Raft" in cap
    assert "0.16.3" in cap and "0.17.0" in cap
    assert "retag" in cap.lower() or "untouched" in cap.lower()
    assert "GIA" in cap
    assert "0.18_signoff" in cap
    for item in NO_HELD.split(","):
        assert item  # sanity
    # frozen tags still present locally; do not retag
    tags = subprocess.run(
        ["git", "tag", "-l", "v0.16.3", "v0.17.0"],
        cwd=str(REPO),
        capture_output=True,
        text=True,
        check=False,
    ).stdout
    assert "v0.16.3" in tags
    assert "v0.17.0" in tags


def test_schema_id_and_defaults():
    assert SCHEMA_ID == "mesh.manifest.parity/v1"
    pin = compute_toolchain_pin()
    assert pin.locale == "C.UTF-8"
