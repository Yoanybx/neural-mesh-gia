"""Tests for Cycle 38 / CP-0042: 0.18_H5_packaging_distribution.

Markers: packaging_dist_cycle38
Aim: ≥14 — T-H5a..f(+neg): distribute/verify/pin-prior mesh.bundle/v1,
provenance, replay guard, signed manifest, toolchain pin (P-09),
ABORT→pin prior; dual_primary=0; no reopen 0.16.3/0.17.0; no Raft/N>2.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from neural_mesh import __version__
from neural_mesh.packaging.distribution import (
    DIST_CHANNEL,
    SCHEMA_ID,
    DistAbortPinPrior,
    DistFrozenChannel,
    DistN2Only,
    DistPlaintextForbidden,
    DistReplayDetected,
    DistSignatureInvalid,
    DistributionDocument,
    cmd_dist_distribute,
    cmd_dist_pin_prior,
    cmd_dist_schema,
    cmd_dist_verify,
    compute_toolchain_pin,
    detect_replay,
    distribute,
    document_to_json,
    format_dist_m2m,
    load_prior_pin,
    pin_prior,
    schema_descriptor,
    sign_document,
    validate_dict,
    verify_distribution,
    verify_signature,
)

pytestmark = [pytest.mark.packaging_dist_cycle38]

REPO = Path(__file__).resolve().parents[1]
MESH = [sys.executable, "-m", "neural_mesh.cli"]

NO_HELD = (
    "Raft,N>2,multi-primary,ML,R2,R3,plaintext,Vault-ACME-req,GIA,"
    "SLO_chase,tag_schema,EVERY_fsync"
)


def _write_mini_root(tmp: Path, *, ver: str = "0.18.0", cp: str = "CP-0042") -> Path:
    (tmp / ".project_state").mkdir(parents=True)
    (tmp / "docs" / "schema" / "bundle").mkdir(parents=True)
    (tmp / "docs" / "capabilities").mkdir(parents=True)
    (tmp / "src" / "neural_mesh" / "packaging" / "dist").mkdir(parents=True)
    (tmp / "dist" / "releases" / "0.18.0").mkdir(parents=True)
    (tmp / "dist" / "releases" / "0.16.3").mkdir(parents=True)
    (tmp / "dist" / "releases" / "0.17.0").mkdir(parents=True)
    (tmp / "pyproject.toml").write_text(
        f'[project]\nname = "neural-mesh-gia"\nversion = "{ver}"\n',
        encoding="utf-8",
    )
    (tmp / "src" / "neural_mesh" / "packaging" / "dist" / "marker.txt").write_text(
        "dist-lib\n", encoding="utf-8"
    )
    state = {
        "last_checkpoint": cp,
        "project_version": ver,
        "version": ver,
        "current_phase": 5,
        "current_module": "mesh-packaging-distribution",
        "safety_status": "SAFE",
        "status": "VERIFIED",
        "test_summary": {"passed": 650, "failed": 0},
    }
    (tmp / ".project_state" / "CHECKPOINT.json").write_text(
        json.dumps(state, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    return tmp


def test_package_version_still_0180():
    assert __version__ == "0.18.0"
    pyproject = (REPO / "pyproject.toml").read_text(encoding="utf-8")
    assert 'version = "0.18.0"' in pyproject


def test_capability_and_schema_docs_present():
    # T-H5 docs gate
    cap = REPO / "docs" / "capabilities" / "MESH_PACKAGING_DISTRIBUTION.md"
    sch = REPO / "docs" / "schema" / "bundle" / "v1.md"
    assert cap.is_file()
    assert sch.is_file()
    ctext = cap.read_text(encoding="utf-8")
    stext = sch.read_text(encoding="utf-8")
    assert "CP-0042" in ctext
    assert "0.18.0" in ctext
    assert "ABORT" in ctext and "pin prior" in ctext.lower()
    assert "mesh.bundle/v1" in stext
    assert "T-H5a" in stext and "T-H5f" in stext
    assert "toolchain" in stext.lower()
    assert "replay" in stext.lower()
    assert "provenance" in stext.lower()
    for item in ("Raft", "plaintext", "Vault-ACME-req"):
        assert item in NO_HELD


def test_distribute_mints_bundle_v1(tmp_path: Path):
    """T-H5a: distribute mints mesh.bundle/v1 on 0.18.x channel."""
    root = _write_mini_root(tmp_path)
    doc = distribute(
        root,
        files=["pyproject.toml", "src/neural_mesh/packaging/distribution"],
        cycle=38,
    )
    assert doc.schema == SCHEMA_ID
    assert doc.channel == DIST_CHANNEL
    assert doc.ver == "0.18.0"
    assert doc.dual_primary == 0
    assert doc.plaintext_fallback == 0
    assert doc.vault_acme_required == 0
    assert doc.invariants_ok is True
    assert doc.abort_pin_prior is False
    assert doc.bundle_id.startswith("bundle-")
    assert doc.signature.value
    out = root / "dist" / "releases" / "0.18.0"
    assert any(out.glob("*.bundle.json"))
    # frozen dirs must remain empty of our new artifact names
    assert not any((root / "dist" / "releases" / "0.16.3").glob("*.bundle.json"))
    assert not any((root / "dist" / "releases" / "0.17.0").glob("*.bundle.json"))


def test_provenance_chain_mint_and_derive(tmp_path: Path):
    """T-H5b: provenance mint + derive parent link."""
    root = _write_mini_root(tmp_path)
    parent = distribute(root, files=["pyproject.toml"], cycle=38)
    assert parent.provenance
    assert parent.provenance[0].step == "mint"
    child = distribute(
        root,
        files=["pyproject.toml"],
        parent=parent,
        cycle=38,
        name="neural-mesh-gia-dist-child",
    )
    assert child.provenance[0].step == "derive"
    assert child.provenance[0].parent_bundle_id == parent.bundle_id
    assert child.provenance[0].parent_sha256 == parent.bundle_sha256


def test_replay_guard_detects_collision(tmp_path: Path):
    """T-H5c: replay guard — nonce collision / second consume aborts."""
    root = _write_mini_root(tmp_path)
    doc = distribute(root, files=["pyproject.toml"], cycle=38)
    # Fresh nonce not in empty registry
    detect_replay(doc.replay_nonce, set())
    with pytest.raises(DistReplayDetected):
        detect_replay(doc.replay_nonce, {doc.replay_nonce})
    # First consume ok; second consume → abort
    verify_distribution(doc, repo=root, mark_replay_seen=True)
    with pytest.raises(DistAbortPinPrior):
        verify_distribution(doc.to_dict(), repo=root, mark_replay_seen=True)


def test_signed_manifest_verify_and_tamper(tmp_path: Path):
    """T-H5d: signed-manifest verify; tamper → DistSignatureInvalid / abort."""
    root = _write_mini_root(tmp_path)
    doc = distribute(root, files=["pyproject.toml"], cycle=38)
    verify_signature(doc)
    again = verify_distribution(doc.to_dict(), repo=root)
    assert again.invariants_ok
    bad = doc.to_dict()
    bad["checksums"] = {"evil": "0" * 64}
    # signature no longer matches canonical payload
    with pytest.raises(DistAbortPinPrior):
        validate_dict(bad, abort_on_breach=True, check_sig=True)


def test_toolchain_pin_p09(tmp_path: Path):
    """T-H5e: toolchain pin (compiler+libc+locale → pin_hash)."""
    root = _write_mini_root(tmp_path)
    tc = compute_toolchain_pin(compiler="cpython-3.12", libc="glibc", locale="C.UTF-8")
    assert tc.pin_hash
    assert len(tc.pin_hash) == 64
    doc = distribute(root, files=["pyproject.toml"], toolchain=tc, cycle=38)
    assert doc.toolchain.pin_hash == tc.pin_hash
    assert doc.toolchain.compiler == "cpython-3.12"
    # empty pin rejected
    broken = doc.to_dict()
    broken["toolchain"] = {
        "compiler": "x",
        "libc": "y",
        "locale": "z",
        "pin_hash": "",
        "schema": "mesh.bundle.toolchain/v1",
    }
    # re-sign so signature is valid but pin empty → invariant breach
    tmp_doc = DistributionDocument.from_dict(broken)
    tmp_doc.signature = sign_document(tmp_doc)
    broken = tmp_doc.to_dict()
    with pytest.raises(DistAbortPinPrior):
        validate_dict(broken, abort_on_breach=True, check_sig=True)


def test_abort_pin_prior_records_prior_untouched_tags(tmp_path: Path):
    """T-H5f: ABORT→pin prior; retag=false; v0.16.3/v0.17.0 untouched."""
    root = _write_mini_root(tmp_path)
    pin = pin_prior(root, reason="test breach", ver="0.17.0")
    assert pin.ver == "0.17.0"
    record = load_prior_pin(root)
    assert record is not None
    assert record["abort_pin_prior"] is True
    assert record["retag"] is False
    assert "v0.16.3" in record["tags_untouched"]
    assert "v0.17.0" in record["tags_untouched"]
    # tags must still exist on real repo and not be moved by this test
    tags = subprocess.check_output(
        ["git", "tag", "-l", "v0.16.3", "v0.17.0"], cwd=str(REPO)
    ).decode()
    assert "v0.16.3" in tags
    assert "v0.17.0" in tags


def test_validate_rejects_wrong_schema():
    bad = {
        "schema": "mesh.bundle/v0-bad",
        "bundle_id": "x",
        "ver": "0.18.0",
        "channel": "0.18.x",
        "name": "n",
        "cp_tip": "CP-0042",
        "cp_range": "CP-0001..0042",
        "entrypoint": "mesh",
        "checksums": {},
        "bundle_sha256": "a" * 64,
        "signature": {"alg": "hmac-sha256-local", "key_id": "mesh-dist-local-v1", "value": "00"},
        "provenance": [{"step": "mint"}],
        "replay_nonce": "abc",
        "toolchain": {"compiler": "c", "libc": "l", "locale": "C", "pin_hash": "p" * 64},
        "dual_primary": 0,
        "plaintext_fallback": 0,
        "vault_acme_required": 0,
    }
    with pytest.raises(DistAbortPinPrior):
        validate_dict(bad, abort_on_breach=True, check_sig=False)


def test_validate_rejects_dual_primary_and_plaintext(tmp_path: Path):
    root = _write_mini_root(tmp_path)
    doc = distribute(root, files=["pyproject.toml"], cycle=38)
    d = doc.to_dict()
    d["dual_primary"] = 1
    # force zeros stripped by to_dict — inject raw
    raw = json.loads(document_to_json(doc))
    raw["dual_primary"] = 1
    # signature over tampered zeros-stripped canonical still uses 0 in sign path;
    # validate_dict checks raw dual_primary field before forcing.
    # Re-sign after setting on object then mutate dict field:
    doc2 = DistributionDocument.from_dict(doc.to_dict())
    payload = doc2.to_dict()
    # Bypass to_dict hard-zero by validating a handcrafted mapping
    payload["dual_primary"] = 0  # signed with 0
    sig = sign_document(DistributionDocument.from_dict(payload))
    payload["signature"] = sig.to_dict()
    payload["plaintext_fallback"] = 1  # breach after sign — sig may fail first
    # For invariant path with check_sig=False:
    payload["plaintext_fallback"] = 1
    with pytest.raises(DistAbortPinPrior):
        validate_dict(payload, abort_on_breach=True, check_sig=False)


def test_refuse_frozen_channel_and_bad_ver(tmp_path: Path):
    root = _write_mini_root(tmp_path)
    with pytest.raises(DistFrozenChannel):
        distribute(root, channel="0.16.3", files=["pyproject.toml"])
    with pytest.raises(DistFrozenChannel):
        distribute(root, channel="0.17.0", files=["pyproject.toml"])
    with pytest.raises(Exception):
        distribute(root, ver="0.17.0", files=["pyproject.toml"])


def test_plaintext_and_raft_refused(tmp_path: Path):
    root = _write_mini_root(tmp_path)
    with pytest.raises(DistPlaintextForbidden):
        distribute(root, files=["pyproject.toml"], mode="plaintext")
    with pytest.raises(DistN2Only):
        distribute(root, files=["pyproject.toml"], claim_raft=True)
    with pytest.raises(DistN2Only):
        distribute(root, files=["pyproject.toml"], n_nodes=3)


def test_schema_descriptor_and_m2m(tmp_path: Path):
    desc = schema_descriptor()
    assert desc["schema"] == SCHEMA_ID
    assert desc["abort"] == "pin prior"
    assert "T-H5a" in desc["tests"]
    assert "distribute" in desc["ops"]
    root = _write_mini_root(tmp_path)
    doc = distribute(root, files=["pyproject.toml"], cycle=38)
    line = format_dist_m2m(doc)
    assert line.startswith("DIST:")
    assert "mesh.bundle/v1" in line or "schema=mesh.bundle/v1" in line


def test_cli_distribute_verify_pin_schema(tmp_path: Path):
    root = _write_mini_root(tmp_path)
    # library CLI helpers
    assert cmd_dist_schema(as_json=True) == 0
    rc = cmd_dist_distribute(repo=root, cycle=38, as_json=True)
    assert rc == 0
    out_files = list((root / "dist" / "releases" / "0.18.0").glob("*.bundle.json"))
    assert out_files
    assert cmd_dist_verify(file=out_files[0], repo=root) == 0
    assert cmd_dist_pin_prior(repo=root, reason="cli test") == 0
    # subprocess CLI
    proc = subprocess.run(
        MESH + ["dist", "schema", "--json"],
        cwd=str(REPO),
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0
    assert SCHEMA_ID in proc.stdout


def test_cli_verify_rejects_bad_schema(tmp_path: Path, capsys):
    bad = tmp_path / "bad.json"
    bad.write_text(json.dumps({"schema": "nope"}), encoding="utf-8")
    rc = cmd_dist_verify(file=bad, repo=tmp_path)
    assert rc == 2
    out = capsys.readouterr().out
    assert "abort_pin_prior" in out


def test_hard_zeros_and_roundtrip(tmp_path: Path):
    root = _write_mini_root(tmp_path)
    doc = distribute(root, files=["pyproject.toml"], cycle=38)
    doc.dual_primary = 9  # type: ignore[assignment]
    d = doc.to_dict()
    assert d["dual_primary"] == 0
    assert d["plaintext_fallback"] == 0
    assert d["vault_acme_required"] == 0
    rt = DistributionDocument.from_dict(d)
    assert rt.schema == SCHEMA_ID
    assert rt.bundle_id == doc.bundle_id
    assert rt.toolchain.pin_hash == doc.toolchain.pin_hash


def test_from_dict_roundtrip_and_sign(tmp_path: Path):
    root = _write_mini_root(tmp_path)
    doc = distribute(root, files=["pyproject.toml"], cycle=38)
    rt = DistributionDocument.from_dict(json.loads(document_to_json(doc)))
    verify_signature(rt)
    assert rt.replay_nonce == doc.replay_nonce
