"""Tests for Cycle 33 / CP-0037: 0.18 bootstrap + GOV.7 entry waiver.

Markers: bootstrap_cycle33
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from neural_mesh import __version__
from neural_mesh.packaging import RELEASE_VERSION, version_matches_expect

pytestmark = [pytest.mark.bootstrap_cycle33]

REPO = Path(__file__).resolve().parents[1]

NO_HELD = (
    "Raft,N>2,multi-primary,ML,R2,R3,plaintext,Vault-ACME-req,GIA,"
    "SLO_chase,tag_schema,EVERY_fsync"
)


def test_package_version_is_0180():
    init = (REPO / "src" / "neural_mesh" / "__init__.py").read_text(encoding="utf-8")
    pyproject = (REPO / "pyproject.toml").read_text(encoding="utf-8")
    assert 'version = "0.18.0"' in pyproject
    assert '__version__ = "0.18.0"' in init
    assert __version__ == "0.18.0"
    assert RELEASE_VERSION == "0.16.3"


def test_bootstrap_doc_present():
    path = REPO / "docs" / "planning" / "0.18_BOOTSTRAP.md"
    assert path.is_file()
    text = path.read_text(encoding="utf-8")
    assert "0.18.0" in text
    assert "GOV.7" in text or "SCHEMA_GATE_0.18_ENTRY" in text
    assert "H1" in text
    assert "deferred" in text.lower() or "not** implemented" in text.lower() or "not implemented" in text.lower()
    assert "0.17.0" in text


def test_scope_frozen_ordered_h1_h8():
    path = REPO / "docs" / "planning" / "0.18_SCOPE_FROZEN.md"
    assert path.is_file()
    text = path.read_text(encoding="utf-8")
    assert "FROZEN" in text
    for token in (
        "H1 identity",
        "H2 recovery",
        "H3 dual-primary",
        "H4 OBS",
        "H5 packaging",
        "H6 minority_write",
        "H7 clock_skew",
        "H8 manifest parity",
    ):
        assert token in text, token
    assert "NO_HELD" in text


def test_scope_and_non_goals_files_exist():
    assert (REPO / "docs" / "planning" / "0.18_SCOPE.md").is_file()
    ng = REPO / "docs" / "planning" / "0.18_NON_GOALS.md"
    assert ng.is_file()
    text = ng.read_text(encoding="utf-8")
    assert "NO_HELD" in text
    for item in NO_HELD.split(","):
        assert item in text, item
    assert "GOV.7" in text
    assert "GIA" in text


def test_council_scope_018_frozen():
    path = REPO / "council" / "SCOPE_0.18_FROZEN.md"
    assert path.is_file()
    text = path.read_text(encoding="utf-8")
    assert "STATUS: FROZEN" in text
    assert "VER_PACKAGE: 0.18.0" in text
    assert "H1_identity" in text
    assert "H8_manifest_parity" in text
    assert "WAIVE_VIA_ACCEPT_AND_CARRY" in text or "ACCEPT_AND_CARRY" in text
    for token in ("Raft", "N>2", "GIA", "SLO_chase", "EVERY_fsync"):
        assert token in text


def test_gov7_entry_waiver_doc():
    path = REPO / "docs" / "debt" / "SCHEMA_GATE_0.18_ENTRY.md"
    assert path.is_file()
    text = path.read_text(encoding="utf-8")
    assert "WAIVE_VIA_ACCEPT_AND_CARRY" in text
    assert "GOV.7" in text
    assert "ACCEPT_AND_CARRY" in text
    assert "SCHEMA-GATED" in text
    assert "CHECKPOINT_EVERY_FLOOR" in text
    assert "SCHEMA_GATE_RESOLUTION_0.17" in text
    assert "SLO_chase" in text or "NOT** SLO" in text
    # no invented unlock language claiming floor MET
    assert "floor is MET" not in text.lower()


def test_prior_017_resolution_still_present():
    path = REPO / "docs" / "debt" / "SCHEMA_GATE_RESOLUTION_0.17.md"
    assert path.is_file()
    text = path.read_text(encoding="utf-8")
    assert "ACCEPT_AND_CARRY" in text
    assert "SCHEMA_GATE_0.18_ENTRY" in text or "0.18" in text


def test_capability_018_bootstrap_doc():
    path = REPO / "docs" / "capabilities" / "MESH_0.18_BOOTSTRAP.md"
    assert path.is_file()
    text = path.read_text(encoding="utf-8")
    assert "0.18.0" in text
    assert "CP-0037" in text
    assert "NO_HELD" in text
    assert "GIA" in text
    assert "H1" in text
    low = text.lower()
    assert "gia-cos" not in low or "no gia" in low or "not claim" in low
    assert "do not implement h1" in low or "not implement" in low


def test_017_release_archive_and_tag_untouched():
    rel = REPO / "dist" / "releases" / "0.17.0"
    assert rel.is_dir()
    assert (rel / "SIGNOFF.json").is_file()
    r = subprocess.run(
        ["git", "rev-parse", "--verify", "v0.17.0"],
        cwd=str(REPO),
        capture_output=True,
        text=True,
        check=False,
    )
    assert r.returncode == 0, r.stderr
    show = subprocess.run(
        ["git", "show", "v0.17.0:src/neural_mesh/__init__.py"],
        cwd=str(REPO),
        capture_output=True,
        text=True,
        check=False,
    )
    assert show.returncode == 0
    assert '__version__ = "0.17.0"' in show.stdout
    # 0.16.3 still present
    assert (REPO / "dist" / "releases" / "0.16.3").is_dir()
    r2 = subprocess.run(
        ["git", "rev-parse", "--verify", "v0.16.3"],
        cwd=str(REPO),
        capture_output=True,
        text=True,
        check=False,
    )
    assert r2.returncode == 0


def test_no_gia_claims_in_018_planning():
    for rel in (
        "docs/planning/0.18_BOOTSTRAP.md",
        "docs/planning/0.18_SCOPE_FROZEN.md",
        "docs/planning/0.18_NON_GOALS.md",
        "docs/capabilities/MESH_0.18_BOOTSTRAP.md",
    ):
        text = (REPO / rel).read_text(encoding="utf-8").lower()
        assert "we are gia" not in text
        assert "agi achieved" not in text
        assert "consciousness proven" not in text
        # GIA may appear only as held / non-goal
        if "gia" in text:
            assert (
                "no gia" in text
                or "gia," in text
                or "gia/" in text
                or "held" in text
                or "non-goal" in text
                or "no_held" in text
            )


def test_version_matches_expect_allows_018_next_line():
    assert version_matches_expect("0.18.0", "0.18.0") is True
    assert version_matches_expect("0.18.0", "0.17.0") is True
    assert version_matches_expect("0.18.0", "0.16.3") is True
    assert version_matches_expect("0.17.0", "0.16.3") is True
    assert version_matches_expect("0.19.0", "0.16.3") is False


def test_deepseek_c32_prefers_bootstrap_then_h1():
    path = REPO / "council" / "DEEPSEEK_REPLY_CYCLE32.md"
    assert path.is_file()
    text = path.read_text(encoding="utf-8")
    assert "VERDICT: PASS" in text
    assert "0.18_bootstrap" in text
    assert "0.18_H1_identity" in text
    assert "GOV.7" in text
