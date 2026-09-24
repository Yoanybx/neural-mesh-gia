"""Tests for Cycle 31 / CP-0035: external_quickstart (0.17 theme 4).

Markers: quickstart_cycle31
Aim: ≥10 tests — doc presence, script dry checks, stub honesty (no GIA/Raft/N>2
claims), link paths resolve, helper fail-closed / no rebuild / no plaintext.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

import pytest

pytestmark = [pytest.mark.quickstart_cycle31]

REPO = Path(__file__).resolve().parents[1]
QS_016 = REPO / "docs" / "quickstart" / "QUICKSTART_0.16.3.md"
QS_017 = REPO / "docs" / "quickstart" / "QUICKSTART_0.17_STUB.md"
CAP = REPO / "docs" / "capabilities" / "MESH_EXTERNAL_QUICKSTART.md"
SCRIPT = REPO / "scripts" / "quickstart_0.16.3.sh"
RELEASE = REPO / "dist" / "releases" / "0.16.3"
FORBIDDEN_CLAIM_RE = re.compile(
    r"(?i)\b(raft\s+consensus|n\s*>\s*2\s+topology|gia\s+runtime|agi\s+runtime|"
    r"multi-primary\s+available|plaintext\s+fallback\s+enabled|"
    r"vault/?acme\s+required)\b"
)
# Phrases that would falsely claim unfinished features as shipped/done
STUB_BAD_DONE = re.compile(
    r"(?i)(0\.17\.0\s+is\s+released|raft\s+is\s+shipped|n\s*>\s*2\s+is\s+supported|"
    r"gia\s+is\s+available|plaintext\s+fallback\s+is\s+supported|"
    r"multi-primary\s+is\s+enabled)"
)


def _read(p: Path) -> str:
    return p.read_text(encoding="utf-8")


def test_quickstart_0163_doc_present():
    assert QS_016.is_file()
    text = _read(QS_016)
    assert "0.16.3" in text
    assert "neural-mesh-gia-single-node-0.16.3.tar.gz" in text
    assert "CLOSED" in text or "FROZEN" in text


def test_quickstart_017_stub_present():
    assert QS_017.is_file()
    text = _read(QS_017)
    assert "STUB" in text
    assert "0.17" in text
    assert "EXPERIMENTAL" in text or "experimental" in text.lower() or "not a signed-off" in text.lower()


def test_capability_doc_present():
    assert CAP.is_file()
    text = _read(CAP)
    assert "MESH_EXTERNAL_QUICKSTART" in text
    assert "CP-0035" in text
    assert "quickstart_0.16.3.sh" in text


def test_helper_script_present_executable():
    assert SCRIPT.is_file()
    mode = SCRIPT.stat().st_mode
    assert mode & 0o111, "quickstart_0.16.3.sh should be executable"
    text = _read(SCRIPT)
    assert "dry-run" in text
    assert "--execute" in text
    assert "set -euo pipefail" in text


def test_release_artifacts_referenced_exist():
    """Paths asserted by the 0.16.3 quickstart must exist on disk."""
    for name in (
        "neural-mesh-gia-single-node-0.16.3.tar.gz",
        "neural-mesh-gia-single-node-0.16.3.manifest.json",
        "SHA256SUMS",
        "SIGNOFF.json",
    ):
        p = RELEASE / name
        assert p.is_file(), f"missing release artifact: {p}"


def test_stub_links_to_real_capability_docs():
    text = _read(QS_017)
    linked = [
        "docs/capabilities/MESH_PACKAGING_N2_MULTI_NODE.md",
        "docs/capabilities/MESH_FABRIC_OPS_UX.md",
        "docs/capabilities/MESH_OBS_PEERS.md",
        "docs/capabilities/MESH_EXTERNAL_QUICKSTART.md",
        "docs/quickstart/QUICKSTART_0.16.3.md",
        "docs/planning/0.17_SCOPE_FROZEN.md",
    ]
    for rel in linked:
        assert rel in text, f"stub should reference {rel}"
        assert (REPO / rel).is_file(), f"broken link target: {rel}"


def test_0163_links_to_real_scripts_and_docs():
    text = _read(QS_016)
    for rel in (
        "scripts/verify_bundle.py",
        "scripts/rc_install_verify.py",
        "scripts/clean_node_smoke.py",
        "scripts/quickstart_0.16.3.sh",
        "docs/capabilities/MESH_PACKAGING_SINGLE_NODE_BUNDLE.md",
        "docs/quickstart/QUICKSTART_0.17_STUB.md",
    ):
        assert rel in text, f"0.16.3 quickstart should reference {rel}"
        assert (REPO / rel).is_file(), f"broken link target: {rel}"


def test_stub_does_not_claim_raft_gia_n_gt_2_as_done():
    text = _read(QS_017)
    assert STUB_BAD_DONE.search(text) is None, "stub must not claim unfinished features as done"
    # Must explicitly list NO_HELD / non-claims
    assert "Raft" in text or "raft" in text.lower()
    assert "N>2" in text or "N>2" in text.replace(" ", "")
    assert "GIA" in text
    assert "NO_HELD" in text
    # Positive honesty: shipped themes table mentions themes 1-4 without Raft
    assert "MESH_FABRIC_OPS_UX" in text
    assert "MESH_OBS_PEERS" in text
    assert "MESH_PACKAGING_N2_MULTI_NODE" in text


def test_0163_and_capability_forbid_plaintext_and_rebuild():
    for path in (QS_016, CAP, SCRIPT):
        text = _read(path)
        assert "plaintext" in text.lower()
        # helper / docs must not invoke build_bundle
        assert "build_bundle" not in text or "never calls `build_bundle`" in text or "Does NOT rebuild" in text or "do not" in text.lower()


def test_helper_dry_run_pass():
    proc = subprocess.run(
        ["bash", str(SCRIPT), "--dry-run"],
        cwd=str(REPO),
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr or proc.stdout
    out = proc.stdout
    assert "DRY_RUN: PASS" in out
    assert "mode=dry-run" in out
    assert "neural-mesh-gia-single-node-0.16.3.tar.gz" in out or "OK present" in out


def test_helper_fail_closed_missing_release_dir(tmp_path: Path):
    missing = tmp_path / "empty_release"
    missing.mkdir()
    proc = subprocess.run(
        ["bash", str(SCRIPT), "--dry-run", "--release-dir", str(missing)],
        cwd=str(REPO),
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode != 0
    assert "ERROR" in (proc.stderr + proc.stdout)


def test_helper_help_and_default_is_dry_run():
    help_proc = subprocess.run(
        ["bash", str(SCRIPT), "--help"],
        cwd=str(REPO),
        capture_output=True,
        text=True,
        check=False,
    )
    assert help_proc.returncode == 0
    assert "--dry-run" in help_proc.stdout
    assert "--execute" in help_proc.stdout

    # bare invocation == dry-run
    bare = subprocess.run(
        ["bash", str(SCRIPT)],
        cwd=str(REPO),
        capture_output=True,
        text=True,
        check=False,
    )
    assert bare.returncode == 0
    assert "DRY_RUN: PASS" in bare.stdout


def test_stub_and_0163_point_at_each_other():
    assert "QUICKSTART_0.17_STUB.md" in _read(QS_016)
    assert "QUICKSTART_0.16.3.md" in _read(QS_017)


def test_no_held_unchanged_in_capability():
    text = _read(CAP)
    for token in (
        "Raft",
        "N>2",
        "multi-primary",
        "plaintext",
        "Vault",
        "GIA",
        "SLO",
        "tag_schema",
        "EVERY_fsync",
    ):
        assert token in text or token.lower() in text.lower(), f"NO_HELD token missing: {token}"


def test_pyproject_marker_registered():
    toml = (REPO / "pyproject.toml").read_text(encoding="utf-8")
    assert "quickstart_cycle31" in toml
