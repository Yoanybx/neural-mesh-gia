"""Tests for Cycle 24 / CP-0028: release signoff, tag archive, post-release monitor.

Markers: packaging_rc_cycle24, packaging_single_node_bundle
Aim: ≥10 new tests covering P18–P20.
"""

from __future__ import annotations

import json
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest

from neural_mesh.packaging import (
    DEFAULT_SIGNER,
    FREEZE_CHANNEL,
    MONITOR_CHECKLIST,
    RELEASE_VERSION,
    SEAL_CP,
    preferred_tag_name,
    run_post_release_monitor,
    run_release_signoff,
    run_release_tag_archive,
)

pytestmark = [
    pytest.mark.packaging_rc_cycle24,
    pytest.mark.packaging_single_node_bundle,
]

REPO = Path(__file__).resolve().parents[1]
SCRIPTS = REPO / "scripts"


def _mini_root(tmp_path: Path, *, ver: str = "0.16.3", tip_cp: str = "CP-0027") -> Path:
    root = tmp_path / f"repo-{ver}"
    (root / "src" / "neural_mesh").mkdir(parents=True)
    (root / "src" / "neural_mesh" / "__init__.py").write_text(
        f'__version__ = "{ver}"\n', encoding="utf-8"
    )
    (root / "src" / "neural_mesh" / "cli.py").write_text(
        textwrap.dedent(
            f"""
            def main(argv=None):
                import json, sys
                argv = list(sys.argv[1:] if argv is None else argv)
                if argv and argv[0] == "--help":
                    print("usage: mesh")
                    return 0
                if argv[:2] == ["status", "--snapshot"]:
                    print(json.dumps({{
                        "schema": "mesh.status.snapshot/v1",
                        "node_id": "local",
                        "cycle": 24,
                        "ver": "{ver}",
                        "tip": None,
                        "cp_range": "CP-0001..0028",
                        "cp_tip": "CP-0028",
                        "pytest": {{"passed": 1, "failed": 0}},
                        "slo_state": {{}},
                        "debt_gates": [],
                        "peers": [],
                        "local": {{}},
                    }}))
                    return 0
                print("mesh", argv)
                return 0
            """
        ).strip()
        + "\n",
        encoding="utf-8",
    )
    (root / "pyproject.toml").write_text(
        textwrap.dedent(
            f"""
            [build-system]
            requires = ["setuptools>=69"]
            build-backend = "setuptools.build_meta"
            [project]
            name = "neural-mesh-gia"
            version = "{ver}"
            requires-python = ">=3.10"
            [project.scripts]
            mesh = "neural_mesh.cli:main"
            [tool.setuptools.packages.find]
            where = ["src"]
            """
        ).strip()
        + "\n",
        encoding="utf-8",
    )
    (root / "scripts").mkdir()
    for name in (
        "build_bundle.py",
        "verify_bundle.py",
        "clean_node_smoke.py",
        "repro_check.py",
        "rc_install_verify.py",
        "rollback_smoke.py",
        "release_checklist.py",
        "rc_soak.py",
        "final_release_audit.py",
        "post_rc_watch.py",
        "release_signoff.py",
        "release_tag_archive.py",
        "post_release_monitor.py",
    ):
        (root / "scripts" / name).write_text(f"# stub {name}\n", encoding="utf-8")
    (root / "scripts" / "audit.sh").write_text("#!/bin/sh\necho ok\n", encoding="utf-8")
    (root / "scripts" / "bootstrap.sh").write_text(
        "#!/bin/sh\necho boot\n", encoding="utf-8"
    )
    debt = root / "docs" / "debt"
    debt.mkdir(parents=True)
    (debt / "CHECKPOINT_EVERY_FLOOR.md").write_text(
        "# debt\nStatus: SCHEMA-GATED\nNo SLO chase\n", encoding="utf-8"
    )
    cap = root / "docs" / "capabilities"
    cap.mkdir(parents=True)
    (cap / "MESH_PACKAGING_SINGLE_NODE_BUNDLE.md").write_text(
        "# packaging\nNO: Raft\nNO_HELD: Raft,N>2,SLO_chase,tag_schema,EVERY_fsync\n",
        encoding="utf-8",
    )
    (cap / "MESH_PACKAGING_RELEASE_CHECKLIST.md").write_text(
        "# checklist\nNO_HELD: Raft,N>2,SLO_chase,tag_schema,EVERY_fsync\n"
        "dual_primary=0\n",
        encoding="utf-8",
    )
    (cap / "MESH_PACKAGING_FINAL_RELEASE_AUDIT.md").write_text(
        "# audit\nNO_HELD: Raft,N>2,SLO_chase,tag_schema,EVERY_fsync\n"
        "dual_primary=0\n",
        encoding="utf-8",
    )
    (cap / "MESH_PACKAGING_RELEASE_SIGNOFF.md").write_text(
        "# signoff\nNO_HELD: Raft,N>2,SLO_chase,tag_schema,EVERY_fsync\n"
        "dual_primary=0\n",
        encoding="utf-8",
    )
    (cap / "MESH_PACKAGING_POST_RELEASE_MONITOR.md").write_text(
        "# monitor\nNO_HELD: Raft,N>2,SLO_chase,tag_schema,EVERY_fsync\n",
        encoding="utf-8",
    )
    (cap / "MESH_PACKAGING_POST_RC_WATCH.md").write_text(
        "# watch\nNO_HELD: Raft,N>2\n", encoding="utf-8"
    )
    (root / "src" / "neural_mesh" / "tags.py").write_text(
        "SCHEMA_GATE_STATUS = 'SCHEMA-GATED'\n"
        "def schema_gate_checkpoint_every_floor(*a, **k):\n"
        "    return 'SCHEMA-GATED'\n"
        "CHECKPOINT_FLOOR = 'CHECKPOINT@floor'\n",
        encoding="utf-8",
    )
    (root / "src" / "neural_mesh" / "status_snapshot.py").write_text(
        textwrap.dedent(
            """
            from pydantic import BaseModel, ConfigDict, Field
            SCHEMA_ID = "mesh.status.snapshot/v1"
            class PytestSummary(BaseModel):
                model_config = ConfigDict(extra="forbid")
                passed: int = 0
                failed: int = 0
            class DebtGate(BaseModel):
                model_config = ConfigDict(extra="forbid")
                id: str
                state: str
                path: str
            class PeerSummary(BaseModel):
                model_config = ConfigDict(extra="forbid")
                node_id: str
                reachable: bool = False
                summary: dict = Field(default_factory=dict)
            class StatusSnapshot(BaseModel):
                model_config = ConfigDict(extra="forbid", populate_by_name=True)
                schema_name: str = Field(default=SCHEMA_ID, alias="schema")
                node_id: str
                cycle: int
                ver: str
                tip: str | None = None
                cp_range: str
                cp_tip: str
                pytest: PytestSummary = Field(default_factory=PytestSummary)
                slo_state: dict[str, str] = Field(default_factory=dict)
                debt_gates: list[DebtGate] = Field(default_factory=list)
                peers: list[PeerSummary] = Field(default_factory=list)
                local: dict = Field(default_factory=dict)
            """
        ).strip()
        + "\n",
        encoding="utf-8",
    )
    state = root / ".project_state"
    state.mkdir()
    (state / "CHECKPOINT.json").write_text(
        json.dumps(
            {
                "last_checkpoint": tip_cp,
                "project_version": ver,
                "test_summary": {"passed": 439, "failed": 0},
                "status": "VERIFIED",
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    (root / "snapshots" / "CP-0027").mkdir(parents=True)
    (root / "snapshots" / "CP-0028").mkdir(parents=True)
    (root / "council").mkdir(parents=True)
    (root / "council" / "COUNCIL_AGREEMENT_CYCLE24.md").write_text(
        "NO_HELD: Raft,N>2,multi-primary,ML,R2,R3,plaintext,Vault-ACME-req,GIA,"
        "SLO_chase,tag_schema,EVERY_fsync\n",
        encoding="utf-8",
    )
    (root / "council" / "STATUS_CYCLE24.md").write_text(
        "dual_primary=0\nDUAL_PRIMARY: 0\n", encoding="utf-8"
    )
    # Seed a PASS audit report for signoff reuse
    audit_dir = root / "dist" / "final_audit"
    audit_dir.mkdir(parents=True)
    (audit_dir / "final_release_audit.json").write_text(
        json.dumps(
            {
                "ok": True,
                "version": ver,
                "freeze_channel": FREEZE_CHANNEL,
                "packaging_count": 53,
                "dual_primary": 0,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    return root


# --- P18: release_signoff ----------------------------------------------------


def test_release_signoff_pass_real_repo(tmp_path: Path):
    """Signoff against live package version (0.17.0); RELEASE_VERSION stays 0.16.3."""
    result = run_release_signoff(
        REPO,
        expect_version="0.17.0",
        out_dir=tmp_path / "releases" / "0.17.0",
        tip="sgnoff1",
        timestamp="2026-09-23T22:00:00Z",
        packaging_count=53,
        skip_pytest=True,
        re_run_audit=True,
        write_project_state=False,
    )
    assert result.ok, result.errors
    assert result.version == "0.17.0"
    assert result.cp == SEAL_CP
    assert result.prior_cp == "CP-0027"
    assert result.signer == DEFAULT_SIGNER
    assert result.timestamp == "2026-09-23T22:00:00Z"
    assert result.freeze_channel == FREEZE_CHANNEL
    assert RELEASE_VERSION == "0.16.3"
    assert result.signoff_path and Path(result.signoff_path).is_file()
    data = json.loads(Path(result.signoff_path).read_text(encoding="utf-8"))
    assert data["ok"] is True
    assert data["ver"] == "0.17.0"
    assert data["signer"] == DEFAULT_SIGNER
    assert data["schema"] == "mesh.release.signoff/v1"
    assert data["cp"] == "CP-0028"


def test_release_signoff_fail_missing_audit(tmp_path: Path):
    root = _mini_root(tmp_path)
    # Remove audit
    (root / "dist" / "final_audit" / "final_release_audit.json").unlink()
    result = run_release_signoff(
        root,
        out_dir=tmp_path / "out" / "0.16.3",
        tip="sgbad",
        timestamp="2026-09-23T22:00:00Z",
        packaging_count=10,
        skip_pytest=True,
        re_run_audit=False,
        write_project_state=False,
        force_fail="final_release_audit",
    )
    assert not result.ok
    assert any(g.name == "final_release_audit" and not g.ok for g in result.gates)


def test_release_signoff_fail_wrong_freeze(tmp_path: Path):
    result = run_release_signoff(
        REPO,
        out_dir=tmp_path / "rel" / "0.16.3",
        tip="sgfrz",
        timestamp="2026-09-23T22:00:00Z",
        packaging_count=10,
        skip_pytest=True,
        re_run_audit=True,
        write_project_state=False,
        force_fail="freeze_016x",
    )
    assert not result.ok
    assert any(g.name == "freeze_016x" and not g.ok for g in result.gates)


def test_release_signoff_reuse_audit_mini(tmp_path: Path):
    root = _mini_root(tmp_path)
    result = run_release_signoff(
        root,
        out_dir=tmp_path / "so" / "0.16.3",
        tip="sgmini",
        timestamp="2026-09-23T22:00:00Z",
        packaging_count=12,
        skip_pytest=True,
        re_run_audit=False,
        write_project_state=True,
    )
    assert result.ok, result.errors
    assert result.audit_ok is True
    assert result.audit_report_hash
    alt = root / ".project_state" / "RELEASE_SIGNOFF_0.16.3.json"
    assert alt.is_file()


def test_release_signoff_script_cli(tmp_path: Path):
    py = REPO / ".venv" / "bin" / "python"
    if not py.is_file():
        py = Path(sys.executable)
    r = subprocess.run(
        [
            str(py),
            str(SCRIPTS / "release_signoff.py"),
            "--root",
            str(REPO),
            "--out",
            str(tmp_path / "0.16.3"),
            "--tip",
            "sgcli",
            "--timestamp",
            "2026-09-23T22:00:00Z",
            "--packaging-count",
            "40",
            "--skip-pytest",
            "--re-run-audit",
            "--json",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert r.returncode == 0, r.stderr + r.stdout
    data = json.loads(r.stdout)
    assert data["ok"] is True
    assert data["version"] == "0.16.3"
    assert data["signer"] == DEFAULT_SIGNER


# --- P19: release_tag_archive ------------------------------------------------


def test_release_tag_archive_builds(tmp_path: Path):
    # Signoff first into archive dir
    out = tmp_path / "releases" / "0.16.3"
    sg = run_release_signoff(
        REPO,
        out_dir=out,
        tip="arch01",
        timestamp="2026-09-23T22:00:00Z",
        packaging_count=40,
        skip_pytest=True,
        re_run_audit=True,
        write_project_state=False,
    )
    assert sg.ok, sg.errors
    result = run_release_tag_archive(
        REPO,
        version="0.16.3",
        out_dir=out,
        tip="arch01",
        create_tag=False,
        require_signoff=True,
    )
    assert result.ok, result.errors
    assert result.archive_dir
    assert Path(result.archive_dir).is_dir()
    assert result.tarball and Path(result.tarball).is_file()
    assert result.manifest_path and Path(result.manifest_path).is_file()
    assert result.sha256sums_path and Path(result.sha256sums_path).is_file()
    assert result.release_archive and Path(result.release_archive).is_file()
    assert (out / "TAG_MARKER.json").is_file()
    assert (out / "ARCHIVE_MANIFEST.json").is_file()
    assert (out / "SIGNOFF.json").is_file()


def test_release_tag_archive_fail_missing_signoff(tmp_path: Path):
    out = tmp_path / "releases" / "0.16.3"
    out.mkdir(parents=True)
    result = run_release_tag_archive(
        REPO,
        version="0.16.3",
        out_dir=out,
        tip="archbad",
        create_tag=False,
        require_signoff=True,
        skip_bundle=True,
        force_fail="signoff_present",
    )
    assert not result.ok
    assert any(g.name == "signoff_present" and not g.ok for g in result.gates)


def test_release_tag_archive_mock_tag(tmp_path: Path):
    out = tmp_path / "releases" / "0.16.3"
    sg = run_release_signoff(
        REPO,
        out_dir=out,
        tip="archtg",
        timestamp="2026-09-23T22:00:00Z",
        packaging_count=40,
        skip_pytest=True,
        re_run_audit=True,
        write_project_state=False,
    )
    assert sg.ok

    def mock_tag(root, name, **kwargs):
        return True, f"mock-created {name}"

    result = run_release_tag_archive(
        REPO,
        version="0.16.3",
        out_dir=out,
        tip="archtg",
        create_tag=True,
        require_clean=False,
        tag_fn=mock_tag,
        skip_bundle=True,
    )
    assert result.ok, result.errors
    assert result.tag_created is True
    assert result.tag_name in ("v0.16.3", "release-0.16.3")
    marker = json.loads((out / "TAG_MARKER.json").read_text(encoding="utf-8"))
    assert marker["created"] is True


def test_preferred_tag_name_and_script(tmp_path: Path):
    name = preferred_tag_name(REPO, "0.16.3")
    assert name in ("v0.16.3", "release-0.16.3")
    # Script without --tag
    out = tmp_path / "0.16.3"
    # need signoff first
    run_release_signoff(
        REPO,
        out_dir=out,
        tip="archcli",
        timestamp="2026-09-23T22:00:00Z",
        packaging_count=40,
        skip_pytest=True,
        re_run_audit=True,
        write_project_state=False,
    )
    py = REPO / ".venv" / "bin" / "python"
    if not py.is_file():
        py = Path(sys.executable)
    r = subprocess.run(
        [
            str(py),
            str(SCRIPTS / "release_tag_archive.py"),
            "--root",
            str(REPO),
            "--out",
            str(out),
            "--ver",
            "0.16.3",
            "--tip",
            "archcli",
            "--skip-bundle",
            "--json",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert r.returncode == 0, r.stderr + r.stdout
    data = json.loads(r.stdout)
    assert data["ok"] is True
    assert data["version"] == "0.16.3"


# --- P20: post_release_monitor -----------------------------------------------


def test_post_release_monitor_once_pass(tmp_path: Path):
    # Prepare release dir with signoff + marker via archive (no tag)
    out = tmp_path / "releases" / "0.16.3"
    # Use REPO's dist path by writing into real releases via out_dir under tmp,
    # but monitor looks at root/dist/releases/ver — so point root at mini or
    # write into REPO dist (ok for tests) OR use mini_root.
    root = _mini_root(tmp_path)
    # Place release artifacts where monitor expects
    rel = root / "dist" / "releases" / "0.16.3"
    sg = run_release_signoff(
        root,
        out_dir=rel,
        tip="monok",
        timestamp="2026-09-23T22:00:00Z",
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
        tip="monok",
        create_tag=False,
        require_signoff=True,
        skip_bundle=False,
    )
    assert ar.ok, ar.errors
    result = run_post_release_monitor(
        root,
        once=True,
        version="0.16.3",
        out_dir=rel,
        tip="monok",
    )
    assert result.ok, result.errors
    assert result.mode == "once"
    names = {c.name for c in result.checks}
    assert set(MONITOR_CHECKLIST) <= names
    assert result.report_path and Path(result.report_path).is_file()
    data = json.loads(Path(result.report_path).read_text(encoding="utf-8"))
    assert data["scheduled_routine"]["create_grok_bot_routine"] is False
    assert data["ok"] is True


def test_post_release_monitor_once_fail(tmp_path: Path):
    root = _mini_root(tmp_path)
    rel = root / "dist" / "releases" / "0.16.3"
    rel.mkdir(parents=True)
    result = run_post_release_monitor(
        root,
        once=True,
        version="0.16.3",
        out_dir=rel,
        tip="monbad",
        force_fail="signoff_present",
    )
    assert not result.ok
    assert any(c.name == "signoff_present" and not c.ok for c in result.checks)


def test_post_release_monitor_script_once(tmp_path: Path):
    # Use real repo after ensuring release artifacts under dist/releases/0.16.3
    rel = REPO / "dist" / "releases" / "0.16.3"
    sg = run_release_signoff(
        REPO,
        out_dir=rel,
        tip="moncli",
        timestamp="2026-09-23T22:00:00Z",
        packaging_count=40,
        skip_pytest=True,
        re_run_audit=True,
        write_project_state=True,
    )
    assert sg.ok, sg.errors
    ar = run_release_tag_archive(
        REPO,
        version="0.16.3",
        out_dir=rel,
        tip="moncli",
        create_tag=False,
        skip_bundle=True,
    )
    assert ar.ok, ar.errors
    py = REPO / ".venv" / "bin" / "python"
    if not py.is_file():
        py = Path(sys.executable)
    r = subprocess.run(
        [
            str(py),
            str(SCRIPTS / "post_release_monitor.py"),
            "--once",
            "--root",
            str(REPO),
            "--ver",
            "0.16.3",
            "--tip",
            "moncli",
            "--json",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert r.returncode == 0, r.stderr + r.stdout
    data = json.loads(r.stdout)
    assert data["ok"] is True
    assert data["mode"] == "once"


def test_version_gate_0163_unchanged():
    """Package opened at 0.17.0; closed release id RELEASE_VERSION stays 0.16.3."""
    init = (REPO / "src" / "neural_mesh" / "__init__.py").read_text(encoding="utf-8")
    pyproject = (REPO / "pyproject.toml").read_text(encoding="utf-8")
    assert 'version = "0.17.0"' in pyproject
    assert '__version__ = "0.17.0"' in init
    assert RELEASE_VERSION == "0.16.3"
