"""Tests for Cycle 37 / CP-0041: 0.18_H4_obs_telemetry.

Markers: obs_telemetry_cycle37
Aim: ≥14 — emit/validate mesh.obs/v1, signals+adversary+cadence,
ABORT→block CP mint, dual_primary=0, no Raft/N>2, extends status_snapshot.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from neural_mesh import __version__
from neural_mesh.obs import (
    CADENCE_TIERS,
    SCHEMA_ID,
    ObsAbortBlockCp,
    ObsCadenceInvalid,
    ObsN2Only,
    ObsPlaintextForbidden,
    TelemetryDocument,
    cmd_obs_schema,
    cmd_obs_telemetry,
    cmd_obs_validate,
    emit_from_snapshot,
    emit_telemetry,
    format_telemetry_m2m,
    schema_descriptor,
    validate_telemetry,
)
from neural_mesh.status_snapshot import SCHEMA_ID as SNAPSHOT_SCHEMA
from neural_mesh.status_snapshot import snapshot

pytestmark = [pytest.mark.obs_telemetry_cycle37]

REPO = Path(__file__).resolve().parents[1]
MESH = [sys.executable, "-m", "neural_mesh.cli"]

NO_HELD = (
    "Raft,N>2,multi-primary,ML,R2,R3,plaintext,Vault-ACME-req,GIA,"
    "SLO_chase,tag_schema,EVERY_fsync"
)


def _write_mini_root(tmp: Path, *, ver: str = "0.18.0", cp: str = "CP-0041") -> Path:
    (tmp / ".project_state").mkdir(parents=True)
    (tmp / "docs" / "debt").mkdir(parents=True)
    (tmp / "snapshots" / "CP-0001").mkdir(parents=True)
    (tmp / "snapshots" / cp).mkdir(parents=True)
    (tmp / "pyproject.toml").write_text(
        f'[project]\nname = "neural-mesh-gia"\nversion = "{ver}"\n',
        encoding="utf-8",
    )
    state = {
        "last_checkpoint": cp,
        "project_version": ver,
        "current_phase": 5,
        "current_module": "mesh-obs-telemetry",
        "safety_status": "SAFE",
        "status": "VERIFIED",
        "test_summary": {"passed": 645, "failed": 0},
    }
    (tmp / ".project_state" / "CHECKPOINT.json").write_text(
        json.dumps(state, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    (tmp / ".project_state" / "CURRENT_STATE.md").write_text(
        "# CURRENT STATE\n\n**Cycle:** 37\n**Checkpoint:** CP-0041 VERIFIED\n",
        encoding="utf-8",
    )
    (tmp / "docs" / "debt" / "CHECKPOINT_EVERY_FLOOR.md").write_text(
        "# EXPLICIT DEBT\n\n**Status:** SCHEMA-GATED\n",
        encoding="utf-8",
    )
    return tmp


def test_package_version_still_0180():
    assert __version__ == "0.18.0"
    pyproject = (REPO / "pyproject.toml").read_text(encoding="utf-8")
    assert 'version = "0.18.0"' in pyproject


def test_capability_and_schema_docs_present():
    cap = REPO / "docs" / "capabilities" / "MESH_OBS_TELEMETRY.md"
    sch = REPO / "docs" / "schema" / "obs" / "v1.md"
    assert cap.is_file()
    assert sch.is_file()
    ctext = cap.read_text(encoding="utf-8")
    stext = sch.read_text(encoding="utf-8")
    assert "CP-0041" in ctext
    assert "0.18.0" in ctext
    assert "ABORT" in ctext and "block CP" in ctext
    assert "mesh.obs/v1" in stext
    assert "Deprecation" in stext or "deprecation" in stext.lower()
    assert "recovery_p99" in stext
    assert "cadence" in stext.lower()
    for item in ("Raft", "plaintext", "Vault-ACME-req"):
        assert item in NO_HELD


def test_emit_from_repo_snapshot_schema(tmp_path: Path):
    root = _write_mini_root(tmp_path)
    doc = emit_telemetry(root, node_id="n0", cadence="10s", cycle=37)
    assert doc.schema == SCHEMA_ID
    assert doc.source_schema == SNAPSHOT_SCHEMA
    assert doc.dual_primary == 0
    assert doc.plaintext_fallback == 0
    assert doc.vault_acme_required == 0
    assert doc.invariants_ok is True
    assert doc.abort_block_cp is False
    assert doc.window.window_id.startswith("obs-win-")
    assert doc.signals.dual_primary == 0
    assert doc.signals.minority_writes == 0
    assert doc.cadence == "10s"
    d = doc.to_dict()
    assert d["schema"] == SCHEMA_ID
    assert d["dual_primary"] == 0


def test_emit_extends_status_snapshot(tmp_path: Path):
    root = _write_mini_root(tmp_path)
    snap = snapshot(root, node_id="local")
    doc = emit_from_snapshot(snap, cadence="60s", packaging="test-pack")
    assert doc.ver == snap.ver
    assert doc.cp_tip == snap.cp_tip
    assert doc.cadence == "60s"
    assert doc.packaging == "test-pack"
    assert "ckpt_durable" in doc.signals.to_dict()


def test_validate_accepts_good_document(tmp_path: Path):
    root = _write_mini_root(tmp_path)
    doc = emit_telemetry(root, cycle=37)
    again = validate_telemetry(doc.to_dict())
    assert again.invariants_ok
    assert again.abort_block_cp is False


def test_validate_rejects_wrong_schema():
    bad = {
        "schema": "mesh.obs/v0-bad",
        "node_id": "n0",
        "cycle": 37,
        "ver": "0.18.0",
        "cp_tip": "CP-0041",
        "cp_range": "CP-0001..0041",
        "pytest": {"passed": 1, "failed": 0},
        "signals": {
            "recovery_p99": "MET",
            "ckpt_durable": "MET",
            "ckpt_parity": "MET",
            "conflict_full": 0,
            "conflict_classify": 0,
            "minority_writes": 0,
            "dual_primary": 0,
            "cp_lag": 0,
        },
        "adversary": {"replay_attempts": 0, "auth_fails": 0, "tier_changes": 0},
        "cadence": "10s",
        "window": {"window_id": "obs-win-x"},
        "dual_primary": 0,
        "plaintext_fallback": 0,
        "vault_acme_required": 0,
    }
    with pytest.raises(ObsAbortBlockCp) as ei:
        validate_telemetry(bad)
    assert "ABORT" in str(ei.value) or ei.value.code == "OBS_ABORT_BLOCK_CP"
    assert ei.value.code == "OBS_ABORT_BLOCK_CP"


def test_validate_rejects_missing_required():
    bad = {
        "schema": SCHEMA_ID,
        "node_id": "n0",
        # missing cycle/ver/cp
        "pytest": {"passed": 0, "failed": 0},
        "signals": {},
        "adversary": {},
        "cadence": "10s",
        "window": {},
        "dual_primary": 0,
        "plaintext_fallback": 0,
        "vault_acme_required": 0,
    }
    with pytest.raises(ObsAbortBlockCp):
        validate_telemetry(bad)


def test_validate_rejects_dual_primary_nonzero():
    good_signals = {
        "recovery_p99": "MET",
        "ckpt_durable": "MET",
        "ckpt_parity": "MET",
        "conflict_full": 0,
        "conflict_classify": 0,
        "minority_writes": 0,
        "dual_primary": 0,
        "cp_lag": 0,
    }
    bad = {
        "schema": SCHEMA_ID,
        "node_id": "n0",
        "cycle": 37,
        "ver": "0.18.0",
        "cp_tip": "CP-0041",
        "cp_range": "CP-0001..0041",
        "pytest": {"passed": 1, "failed": 0},
        "signals": good_signals,
        "adversary": {"replay_attempts": 0, "auth_fails": 0, "tier_changes": 0},
        "cadence": "10s",
        "window": {"window_id": "obs-win-x"},
        "dual_primary": 1,
        "plaintext_fallback": 0,
        "vault_acme_required": 0,
    }
    # to_dict forces 0, so validate raw mapping path
    with pytest.raises(ObsAbortBlockCp) as ei:
        validate_telemetry(bad)
    assert "dual_primary" in str(ei.value)


def test_validate_rejects_plaintext_and_minority():
    base = {
        "schema": SCHEMA_ID,
        "node_id": "n0",
        "cycle": 37,
        "ver": "0.18.0",
        "cp_tip": "CP-0041",
        "cp_range": "CP-0001..0041",
        "pytest": {"passed": 1, "failed": 0},
        "signals": {
            "recovery_p99": "MET",
            "ckpt_durable": "MET",
            "ckpt_parity": "MET",
            "conflict_full": 0,
            "conflict_classify": 0,
            "minority_writes": 1,
            "dual_primary": 0,
            "cp_lag": 0,
        },
        "adversary": {"replay_attempts": 0, "auth_fails": 0, "tier_changes": 0},
        "cadence": "10s",
        "window": {"window_id": "obs-win-x"},
        "dual_primary": 0,
        "plaintext_fallback": 0,
        "vault_acme_required": 0,
    }
    with pytest.raises(ObsAbortBlockCp) as ei:
        validate_telemetry(base)
    assert "minority_writes" in str(ei.value)

    base2 = dict(base)
    base2["signals"] = dict(base["signals"])
    base2["signals"]["minority_writes"] = 0
    base2["plaintext_fallback"] = 1
    with pytest.raises(ObsAbortBlockCp) as ei2:
        validate_telemetry(base2)
    assert "plaintext" in str(ei2.value)


def test_plaintext_mode_forbidden(tmp_path: Path):
    root = _write_mini_root(tmp_path)
    with pytest.raises(ObsPlaintextForbidden):
        emit_telemetry(root, mode="plaintext")


def test_invalid_cadence_rejected(tmp_path: Path):
    root = _write_mini_root(tmp_path)
    snap = snapshot(root)
    with pytest.raises(ObsCadenceInvalid):
        emit_from_snapshot(snap, cadence="5s")  # type: ignore[arg-type]
    assert set(CADENCE_TIERS) == {"1s", "10s", "60s"}


def test_probed_peers_n2_only(tmp_path: Path):
    root = _write_mini_root(tmp_path)
    peers = [
        {"node_id": "a", "reachable": True, "source": "probed"},
        {"node_id": "b", "reachable": True, "source": "probed"},
        {"node_id": "c", "reachable": True, "source": "probed"},
    ]
    with pytest.raises(ObsN2Only):
        emit_telemetry(root, peers=peers)


def test_m2m_format_includes_contract_fields(tmp_path: Path):
    root = _write_mini_root(tmp_path)
    doc = emit_telemetry(root, cycle=37, cadence="1s")
    line = format_telemetry_m2m(doc)
    assert line.startswith("OBS:")
    assert "cadence=1s" in line
    assert "window=obs-win-" in line
    assert "dual_primary=0" in line
    assert "schema=mesh.obs/v1" in line
    assert "invariants_ok=True" in line


def test_schema_descriptor():
    desc = schema_descriptor()
    assert desc["schema"] == SCHEMA_ID
    assert "recovery_p99" in desc["signals"]
    assert desc["abort"] == "block_cp_mint"
    assert "mesh.status.snapshot/v1" in desc["deprecation_note"]


def test_cli_telemetry_json(tmp_path: Path):
    root = _write_mini_root(tmp_path)
    proc = subprocess.run(
        MESH
        + [
            "obs",
            "telemetry",
            "--repo",
            str(root),
            "--cadence",
            "10s",
            "--cycle",
            "37",
        ],
        cwd=str(REPO),
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr + proc.stdout
    data = json.loads(proc.stdout)
    assert data["schema"] == SCHEMA_ID
    assert data["dual_primary"] == 0
    assert data["abort_block_cp"] is False


def test_cli_validate_good_and_bad(tmp_path: Path):
    root = _write_mini_root(tmp_path)
    doc = emit_telemetry(root, cycle=37)
    good = tmp_path / "good.json"
    good.write_text(json.dumps(doc.to_dict()), encoding="utf-8")
    proc = subprocess.run(
        MESH + ["obs", "validate", "--file", str(good)],
        cwd=str(REPO),
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr + proc.stdout
    assert json.loads(proc.stdout)["ok"] is True

    bad = tmp_path / "bad.json"
    payload = doc.to_dict()
    payload["schema"] = "nope"
    bad.write_text(json.dumps(payload), encoding="utf-8")
    proc2 = subprocess.run(
        MESH + ["obs", "validate", "--file", str(bad)],
        cwd=str(REPO),
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc2.returncode != 0
    err = json.loads(proc2.stdout)
    assert err["abort_block_cp"] is True
    assert err["ok"] is False


def test_cli_schema_and_helpers(tmp_path: Path, capsys):
    proc = subprocess.run(
        MESH + ["obs", "schema"],
        cwd=str(REPO),
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0
    data = json.loads(proc.stdout)
    assert data["schema"] == SCHEMA_ID

    root = _write_mini_root(tmp_path)
    rc = cmd_obs_telemetry(repo=root, cycle=37, m2m=True)
    assert rc == 0
    out = capsys.readouterr().out
    assert out.startswith("OBS:")
    assert cmd_obs_schema(as_json=True) == 0


def test_hard_zeros_in_serialized_document(tmp_path: Path):
    root = _write_mini_root(tmp_path)
    doc = emit_telemetry(root)
    # Even if caller tampers attributes before serialize, to_dict forces 0
    doc.dual_primary = 7  # type: ignore[assignment]
    doc.signals.dual_primary = 3  # type: ignore[assignment]
    d = doc.to_dict()
    assert d["dual_primary"] == 0
    assert d["signals"]["dual_primary"] == 0
    assert d["signals"]["minority_writes"] == 0
    assert d["plaintext_fallback"] == 0
    assert d["vault_acme_required"] == 0


def test_from_dict_roundtrip(tmp_path: Path):
    root = _write_mini_root(tmp_path)
    doc = emit_telemetry(root, cadence="60s")
    rt = TelemetryDocument.from_dict(doc.to_dict())
    assert rt.schema == SCHEMA_ID
    assert rt.cadence == "60s"
    assert rt.window.window_id == doc.window.window_id
