"""Tests for Cycle 25 / CP-0029: monitor continue, 0.17 planning, debt gate review.

Markers: packaging_rc_cycle25, packaging_single_node_bundle
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from neural_mesh.packaging import (
    DEFAULT_SIGNER,
    HISTORY_BASENAME,
    MONITOR_CHECKLIST,
    RELEASE_VERSION,
    SEAL_CP,
    append_monitor_history,
    run_debt_gate_review,
    run_post_release_monitor,
    run_release_signoff,
    run_release_tag_archive,
)
from tests.test_packaging_rc_cycle24 import _mini_root

pytestmark = [
    pytest.mark.packaging_rc_cycle25,
    pytest.mark.packaging_single_node_bundle,
]

REPO = Path(__file__).resolve().parents[1]
SCRIPTS = REPO / "scripts"


def _seed_release(root: Path) -> Path:
    rel = root / "dist" / "releases" / "0.16.3"
    sg = run_release_signoff(
        root,
        out_dir=rel,
        tip="c25seed",
        timestamp="2026-09-24T00:00:00Z",
        packaging_count=12,
        skip_pytest=True,
        re_run_audit=False,
        write_project_state=True,
    )
    assert sg.ok, sg.errors
    ar = run_release_tag_archive(
        root,
        version="0.16.3",
        out_dir=rel,
        tip="c25seed",
        create_tag=False,
        require_signoff=True,
        skip_bundle=False,
    )
    assert ar.ok, ar.errors
    return rel


# --- P21: post_release_monitor --continue ------------------------------------


def test_monitor_continue_appends_history(tmp_path: Path):
    root = _mini_root(tmp_path)
    # Extend mini root with cycle25 NO_HELD docs so drift check passes
    (root / "docs" / "planning").mkdir(parents=True, exist_ok=True)
    (root / "docs" / "planning" / "0.17_NON_GOALS.md").write_text(
        "NO_HELD: Raft,N>2,SLO_chase,tag_schema,EVERY_fsync\n", encoding="utf-8"
    )
    (root / "council" / "COUNCIL_AGREEMENT_CYCLE25.md").write_text(
        "NO_HELD: Raft,N>2,SLO_chase,tag_schema,EVERY_fsync\n", encoding="utf-8"
    )
    # Ensure tags schema gate helpers exist for debt check
    tags = root / "src" / "neural_mesh" / "tags.py"
    if "schema_gate_checkpoint_every_floor" not in tags.read_text(encoding="utf-8"):
        tags.write_text(
            "SCHEMA_GATE_STATUS = 'SCHEMA-GATED'\n"
            "def schema_gate_checkpoint_every_floor(*a, **k):\n"
            "    return 'SCHEMA-GATED'\n"
            "CHECKPOINT_FLOOR = 'CHECKPOINT@floor'\n",
            encoding="utf-8",
        )
    # Keep cycle24 mini debt doc ("Status: SCHEMA-GATED" + "No SLO chase")
    rel = _seed_release(root)
    r1 = run_post_release_monitor(
        root,
        continue_mode=True,
        version="0.16.3",
        out_dir=rel,
        tip="c25c1",
    )
    assert r1.ok, r1.errors
    assert r1.mode == "continue"
    assert r1.history_appended is True
    hp = Path(r1.history_path)
    assert hp.is_file()
    assert hp.name == HISTORY_BASENAME
    lines1 = hp.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines1) == 1
    rec1 = json.loads(lines1[0])
    assert rec1["ok"] is True
    assert rec1["mode"] == "continue"

    r2 = run_post_release_monitor(
        root,
        continue_mode=True,
        version="0.16.3",
        out_dir=rel,
        tip="c25c2",
    )
    assert r2.ok, r2.errors
    lines2 = hp.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines2) == 2
    assert set(MONITOR_CHECKLIST) <= {c.name for c in r2.checks}


def test_monitor_continue_fail_missing_signoff(tmp_path: Path):
    root = _mini_root(tmp_path)
    (root / "docs" / "planning").mkdir(parents=True, exist_ok=True)
    (root / "docs" / "planning" / "0.17_NON_GOALS.md").write_text(
        "NO_HELD: Raft\n", encoding="utf-8"
    )
    rel = root / "dist" / "releases" / "0.16.3"
    rel.mkdir(parents=True)
    (rel / "TAG_MARKER.json").write_text(
        json.dumps({"ok": True, "ver": "0.16.3"}), encoding="utf-8"
    )
    result = run_post_release_monitor(
        root,
        continue_mode=True,
        version="0.16.3",
        out_dir=rel,
        tip="c25nosg",
        history_path=rel / HISTORY_BASENAME,
        force_fail="signoff_present",
    )
    assert not result.ok
    assert any(c.name == "signoff_present" and not c.ok for c in result.checks)
    assert result.history_appended is True
    assert Path(result.history_path).is_file()
    rec = json.loads(
        Path(result.history_path).read_text(encoding="utf-8").splitlines()[0]
    )
    assert rec["ok"] is False


def test_monitor_continue_fail_missing_archive(tmp_path: Path):
    root = _mini_root(tmp_path)
    (root / "docs" / "planning").mkdir(parents=True, exist_ok=True)
    (root / "docs" / "planning" / "0.17_NON_GOALS.md").write_text(
        "NO_HELD: Raft\n", encoding="utf-8"
    )
    rel = root / "dist" / "releases" / "0.16.3"
    rel.mkdir(parents=True)
    (rel / "SIGNOFF.json").write_text(
        json.dumps({"ok": True, "ver": "0.16.3", "tip": "x"}), encoding="utf-8"
    )
    result = run_post_release_monitor(
        root,
        continue_mode=True,
        version="0.16.3",
        out_dir=rel,
        tip="c25noar",
        force_fail="tag_or_archive_marker",
    )
    assert not result.ok
    assert any(c.name == "tag_or_archive_marker" and not c.ok for c in result.checks)


def test_append_monitor_history_roll(tmp_path: Path):
    hp = tmp_path / HISTORY_BASENAME
    for i in range(5):
        append_monitor_history(hp, {"i": i, "ok": True}, roll_max=3)
    lines = hp.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 3
    assert json.loads(lines[0])["i"] == 2
    assert json.loads(lines[-1])["i"] == 4


def test_monitor_continue_script_cli(tmp_path: Path):
    rel = REPO / "dist" / "releases" / "0.16.3"
    assert (rel / "SIGNOFF.json").is_file() or (
        REPO / ".project_state" / "RELEASE_SIGNOFF_0.16.3.json"
    ).is_file()
    hist = tmp_path / HISTORY_BASENAME
    py = REPO / ".venv" / "bin" / "python"
    if not py.is_file():
        py = Path(sys.executable)
    r = subprocess.run(
        [
            str(py),
            str(SCRIPTS / "post_release_monitor.py"),
            "--continue",
            "--root",
            str(REPO),
            "--ver",
            "0.16.3",
            "--history",
            str(hist),
            "--report",
            str(tmp_path / "MONITOR.json"),
            "--json",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert r.returncode == 0, r.stderr + r.stdout
    data = json.loads(r.stdout)
    assert data["ok"] is True
    assert data["mode"] == "continue"
    assert data["history_appended"] is True
    assert hist.is_file()


# --- P22: 0.17 scope planning ------------------------------------------------


def test_planning_docs_exist_with_required_headings():
    scope = REPO / "docs" / "planning" / "0.17_SCOPE.md"
    non_goals = REPO / "docs" / "planning" / "0.17_NON_GOALS.md"
    plan = REPO / "council" / "PLAN_0.17_DRAFT.md"
    assert scope.is_file()
    assert non_goals.is_file()
    assert plan.is_file()
    scope_text = scope.read_text(encoding="utf-8")
    assert "Proposed themes" in scope_text
    assert "0.17" in scope_text
    assert "PLANNING ONLY" in scope_text or "planning" in scope_text.lower()
    ng = non_goals.read_text(encoding="utf-8")
    assert "NO_HELD" in ng
    assert "NON-GOALS" in ng or "NON_GOALS" in ng
    assert "SCHEMA-GATED" in ng
    assert "Raft" in ng and "SLO_chase" in ng and "EVERY_fsync" in ng
    draft = plan.read_text(encoding="utf-8")
    assert "0.17" in draft
    assert "NO_HELD" in draft
    assert "PLANNING_ONLY" in draft or "PLANNING ONLY" in draft or "THEMES" in draft


def test_planning_docs_exclude_held_features_as_goals():
    scope = (REPO / "docs" / "planning" / "0.17_SCOPE.md").read_text(encoding="utf-8")
    ng = (REPO / "docs" / "planning" / "0.17_NON_GOALS.md").read_text(encoding="utf-8")
    for token in ("Raft", "N>2", "GIA", "SLO_chase", "tag_schema", "EVERY_fsync"):
        assert token in ng
    assert "implement Raft" not in scope.lower()


def test_version_still_0163_no_0170_shipped():
    init = (REPO / "src" / "neural_mesh" / "__init__.py").read_text(encoding="utf-8")
    pyproject = (REPO / "pyproject.toml").read_text(encoding="utf-8")
    assert 'version = "0.16.3"' in pyproject
    assert '__version__ = "0.16.3"' in init
    assert RELEASE_VERSION == "0.16.3"
    assert 'version = "0.17.0"' not in pyproject
    assert '__version__ = "0.17.0"' not in init
    assert SEAL_CP == "CP-0028"
    assert DEFAULT_SIGNER


# --- P23: debt_gate_review ---------------------------------------------------


def test_debt_gate_review_pass_real_repo(tmp_path: Path):
    report = tmp_path / "DEBT_GATE_REVIEW.json"
    result = run_debt_gate_review(REPO, report_path=report)
    assert result.ok, result.errors
    assert result.schema_gate_present is True
    assert result.rebenchmarked is False
    assert report.is_file()
    data = json.loads(report.read_text(encoding="utf-8"))
    assert data["ok"] is True
    assert data["cp"] == "CP-0029"
    ids = {g["id"] for g in data["gates"]}
    assert "CHECKPOINT_EVERY_FLOOR" in ids
    floor = next(g for g in data["gates"] if g["id"] == "CHECKPOINT_EVERY_FLOOR")
    assert floor["status"] == "SCHEMA-GATED"
    assert floor["ok"] is True


def test_debt_gate_review_fail_missing_debt_file(tmp_path: Path):
    root = _mini_root(tmp_path)
    debt = root / "docs" / "debt" / "CHECKPOINT_EVERY_FLOOR.md"
    if debt.is_file():
        debt.unlink()
    result = run_debt_gate_review(root, report_path=tmp_path / "debt_fail.json")
    assert not result.ok
    assert any(g.id == "CHECKPOINT_EVERY_FLOOR" and not g.ok for g in result.gates)


def test_debt_gate_review_fail_missing_schema_gate(tmp_path: Path):
    root = _mini_root(tmp_path)
    (root / "docs" / "debt" / "CHECKPOINT_EVERY_FLOOR.md").write_text(
        "# debt\n**Status:** SCHEMA-GATED\nNo SLO chase\n", encoding="utf-8"
    )
    (root / "src" / "neural_mesh" / "tags.py").write_text(
        "# no schema gate\n", encoding="utf-8"
    )
    result = run_debt_gate_review(root, report_path=tmp_path / "debt_sg.json")
    assert not result.ok
    assert result.schema_gate_present is False


def test_debt_gate_review_script_cli(tmp_path: Path):
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
    assert data["ok"] is True
    assert data["rebenchmarked"] is False
    assert report.is_file()
