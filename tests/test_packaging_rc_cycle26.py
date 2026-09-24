"""Tests for Cycle 26 / CP-0030: 0.17 scope freeze, schema gate resolution, bootstrap.

Markers: packaging_rc_cycle26, packaging_single_node_bundle
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from neural_mesh import __version__
from neural_mesh.packaging import (
    FREEZE_CHANNEL,
    RELEASE_VERSION,
    RESOLUTION_ACCEPT_AND_CARRY,
    debt_gate_status,
    run_debt_gate_review,
    version_matches_expect,
)
from neural_mesh.packaging.manifest import SCHEMA_ID

pytestmark = [
    pytest.mark.packaging_rc_cycle26,
    pytest.mark.packaging_single_node_bundle,
]

REPO = Path(__file__).resolve().parents[1]
SCRIPTS = REPO / "scripts"


# --- P24: 0.17 scope freeze --------------------------------------------------


def test_frozen_scope_doc_present_and_status():
    path = REPO / "docs" / "planning" / "0.17_SCOPE_FROZEN.md"
    assert path.is_file()
    text = path.read_text(encoding="utf-8")
    assert "Status:** FROZEN" in text or "**Status:** FROZEN" in text
    assert "FROZEN" in text
    # Ordered themes
    assert "N=2" in text or "multi-node" in text.lower()
    assert "Fabric ops" in text or "fabric_ops" in text.lower() or "Fabric ops UX" in text
    assert "OBS" in text or "peers" in text.lower()
    assert "quickstart" in text.lower()
    assert "NO_HELD" in text
    assert "NON-GOALS" in text or "NON_GOALS" in text


def test_council_scope_frozen_and_plan_marked():
    scope = REPO / "council" / "SCOPE_0.17_FROZEN.md"
    plan = REPO / "council" / "PLAN_0.17_DRAFT.md"
    assert scope.is_file()
    assert plan.is_file()
    st = scope.read_text(encoding="utf-8")
    pt = plan.read_text(encoding="utf-8")
    assert "STATUS: FROZEN" in st
    assert "STATUS: FROZEN" in pt
    assert "multi_node_packaging" in st
    assert "ACCEPT_AND_CARRY" in st or "SCHEMA-GATED" in st
    for token in ("Raft", "N>2", "SLO_chase", "EVERY_fsync", "tag_schema"):
        assert token in st


def test_frozen_scope_does_not_invent_new_themes():
    frozen = (REPO / "docs" / "planning" / "0.17_SCOPE_FROZEN.md").read_text(
        encoding="utf-8"
    )
    # Must not invent held features as goals
    assert "implement Raft" not in frozen.lower()
    assert "N>3" not in frozen
    assert "multi-primary" in frozen.lower() or "multi-primary" in (
        REPO / "docs" / "planning" / "0.17_NON_GOALS.md"
    ).read_text(encoding="utf-8")


# --- P25: schema gate resolution ---------------------------------------------


def test_schema_gate_resolution_doc_accept_and_carry():
    path = REPO / "docs" / "debt" / "SCHEMA_GATE_RESOLUTION_0.17.md"
    assert path.is_file()
    text = path.read_text(encoding="utf-8")
    assert "ACCEPT_AND_CARRY" in text
    assert "SCHEMA-GATED" in text
    assert "resolution" in text.lower()
    assert "EVERY" in text or "EVERY_fsync" in text
    assert "tag_schema" in text or "tag schema" in text.lower()


def test_debt_gate_status_helper_accept_and_carry():
    status = debt_gate_status(REPO)
    assert status["resolution"] == RESOLUTION_ACCEPT_AND_CARRY
    assert status["status"] == "SCHEMA-GATED"
    assert status["schema_gate_present"] is True
    assert status["rebenchmarked"] is False
    assert status["blocking"] is False
    assert status["resolution_doc_present"] is True


def test_debt_gate_review_emits_resolution(tmp_path: Path):
    report = tmp_path / "DEBT_GATE_REVIEW.json"
    result = run_debt_gate_review(REPO, report_path=report)
    assert result.ok, result.errors
    assert result.resolution == "ACCEPT_AND_CARRY"
    assert result.schema_gate_present is True
    assert result.rebenchmarked is False
    data = json.loads(report.read_text(encoding="utf-8"))
    assert data["resolution"] == "ACCEPT_AND_CARRY"
    assert data["ok"] is True
    ids = {g["id"] for g in data["gates"]}
    assert "CHECKPOINT_EVERY_FLOOR" in ids
    assert "SCHEMA_GATE_RESOLUTION_0.17" in ids
    floor = next(g for g in data["gates"] if g["id"] == "CHECKPOINT_EVERY_FLOOR")
    assert floor["status"] == "SCHEMA-GATED"
    res_gate = next(
        g for g in data["gates"] if g["id"] == "SCHEMA_GATE_RESOLUTION_0.17"
    )
    assert res_gate["status"] == "ACCEPT_AND_CARRY"
    assert res_gate["ok"] is True


def test_debt_gate_review_script_prints_resolution(tmp_path: Path):
    py = REPO / ".venv" / "bin" / "python"
    if not py.is_file():
        py = Path(sys.executable)
    report = tmp_path / "DEBT_GATE_REVIEW.json"
    r = subprocess.run(
        [
            str(py),
            str(SCRIPTS / "debt_gate_review.py"),
            "--root",
            str(REPO),
            "--report",
            str(report),
            "--json",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert r.returncode == 0, r.stderr + r.stdout
    data = json.loads(r.stdout)
    assert data["resolution"] == "ACCEPT_AND_CARRY"
    assert "SCHEMA-GATED" in json.dumps(data)


# --- P26: 0.17 bootstrap -----------------------------------------------------


def test_package_version_is_0170():
    init = (REPO / "src" / "neural_mesh" / "__init__.py").read_text(encoding="utf-8")
    pyproject = (REPO / "pyproject.toml").read_text(encoding="utf-8")
    assert 'version = "0.17.0"' in pyproject
    assert '__version__ = "0.17.0"' in init
    assert __version__ == "0.17.0"
    # Closed release id unchanged
    assert RELEASE_VERSION == "0.16.3"


def test_bootstrap_doc_present():
    path = REPO / "docs" / "planning" / "0.17_BOOTSTRAP.md"
    assert path.is_file()
    text = path.read_text(encoding="utf-8")
    assert "0.17.0" in text
    assert "FROZEN" in text or "frozen" in text.lower()
    assert "deferred" in text.lower() or "bootstrap" in text.lower()
    assert "0.16.3" in text


def test_v0163_tag_still_exists():
    r = subprocess.run(
        ["git", "rev-parse", "--verify", "v0.16.3"],
        cwd=str(REPO),
        capture_output=True,
        text=True,
        check=False,
    )
    assert r.returncode == 0, r.stderr
    tip = r.stdout.strip()
    assert len(tip) == 40
    # Tag blob still shows 0.16.3 package at tag time
    show = subprocess.run(
        ["git", "show", "v0.16.3:src/neural_mesh/__init__.py"],
        cwd=str(REPO),
        capture_output=True,
        text=True,
        check=False,
    )
    assert show.returncode == 0
    assert '__version__ = "0.16.3"' in show.stdout


def test_freeze_channel_docs_still_closed_016x():
    assert FREEZE_CHANNEL == "0.16.x"
    assert SCHEMA_ID == "mesh.bundle.manifest/v1"
    doc = (
        REPO / "docs" / "capabilities" / "MESH_PACKAGING_SINGLE_NODE_BUNDLE.md"
    ).read_text(encoding="utf-8")
    assert "0.16.x" in doc
    assert "FROZEN" in doc
    # RC channel remains closed language
    assert "freeze" in doc.lower()


def test_version_matches_expect_next_line_helper():
    assert version_matches_expect("0.16.3", "0.16.3") is True
    assert version_matches_expect("0.17.0", "0.16.3") is True
    assert version_matches_expect("0.17.0", "0.17.0") is True
    assert version_matches_expect("0.18.0", "0.16.3") is False
    assert version_matches_expect("0.15.0", "0.16.3") is False


def test_next_action_points_at_first_frozen_theme():
    na = (REPO / ".project_state" / "NEXT_ACTION.md").read_text(encoding="utf-8")
    # After seal this will point at N=2 multi-node; allow bootstrap phrasing too
    low = na.lower()
    assert (
        "n=2" in low
        or "multi-node" in low
        or "multi_node" in low
        or "0.17" in low
        or "cp-0030" in low
    )
