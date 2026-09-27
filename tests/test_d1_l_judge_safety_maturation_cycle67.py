"""Tests for Cycle 67 / CP-0071: D1 L_judge safety-case maturation.

Markers: d1_l_judge_safety_maturation_cycle67
Design-only absorption of ChatGPT D4-A..K. live=DISABLED; M1=NO_CONSENSUS_YET;
pkg0190 NOT_OPENED; MESH_PERF_EXPERIMENTAL=OFF; no GIA/Raft/N>2/train/SaaS.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from neural_mesh import __version__
from neural_mesh.packaging.d1_l_judge_safety_maturation import (
    AUTHORITY_MATRIX,
    CAPABILITY_DOC,
    COMPOSED_CPS,
    CYCLE,
    D4_DEBT_IDS,
    MUST_STAY_FALSE,
    PACKAGE_HELD,
    PLANNING_DOC,
    PREFERRED_NEXT_DEFAULT,
    PRIOR_CP,
    ROLLBACK_VERIFICATION_IDS,
    SCHEMA_DOC,
    SCHEMA_ID,
    SEAL_CP,
    authority_matrix_as_rows,
    default_maturation_gate,
    run_d1_safety_maturation_gates,
)

pytestmark = [pytest.mark.d1_l_judge_safety_maturation_cycle67]

REPO = Path(__file__).resolve().parents[1]


def test_constants():
    assert __version__ == "0.18.0"
    assert PACKAGE_HELD == "0.18.0"
    assert SEAL_CP == "CP-0071"
    assert PRIOR_CP == "CP-0070"
    assert CYCLE == 67
    assert PREFERRED_NEXT_DEFAULT == "await_deepseek"
    assert SCHEMA_ID == "mesh.judge.d1_safety_maturation/v0"
    assert D4_DEBT_IDS == tuple(f"D4-{c}" for c in "ABCDEFGHIJK")
    assert COMPOSED_CPS == ("CP-0058", "CP-0068", "CP-0069")
    assert ROLLBACK_VERIFICATION_IDS == tuple(f"RV-{i}" for i in range(1, 8))
    assert "live_adapter.enabled" in MUST_STAY_FALSE
    assert "d1_exit_ready_for_live" in MUST_STAY_FALSE
    assert "m1_consensus_default_selected" in MUST_STAY_FALSE


def test_authority_matrix_semantics():
    assert AUTHORITY_MATRIX["L_judge"] == (True, False, False, False)
    assert AUTHORITY_MATRIX["Oversight_I5"] == (True, True, True, False)
    assert AUTHORITY_MATRIX["Continuity"] == (False, False, True, False)
    assert AUTHORITY_MATRIX["Operator"][2] is True  # veto
    assert AUTHORITY_MATRIX["RefuseTransport"][3] is False
    rows = authority_matrix_as_rows()
    assert len(rows) == len(AUTHORITY_MATRIX)
    assert {r["component"] for r in rows} == set(AUTHORITY_MATRIX)


def test_default_gate_live_disabled():
    gate = default_maturation_gate()
    assert gate["live_enabled"] is False
    assert gate["d1_exit_ready_for_live"] is False
    assert gate["m1_status"] == "NO_CONSENSUS_YET"
    assert gate["mesh_perf_experimental"] == "OFF"
    assert gate["d4_debt_ids"] == list(D4_DEBT_IDS)
    assert gate["rollback_verification_ids"] == list(ROLLBACK_VERIFICATION_IDS)
    assert all(v is False for v in gate["must_stay_false"].values())


def test_planning_doc_cites_d4_a_to_k():
    text = (REPO / PLANNING_DOC).read_text(encoding="utf-8")
    assert "DESIGN ONLY" in text or "design-only" in text.lower()
    assert "CP-0071" in text
    assert "CP-0058" in text and "CP-0068" in text and "CP-0069" in text
    assert "live=DISABLED" in text or "**live=DISABLED**" in text
    assert "NO_CONSENSUS_YET" in text
    for debt_id in D4_DEBT_IDS:
        assert debt_id in text, debt_id
    for rv in ROLLBACK_VERIFICATION_IDS:
        assert rv in text, rv
    assert "Authority Matrix" in text
    assert "Claim hygiene" in text
    assert "adversarial" in text.lower()
    assert "independence" in text.lower() or "Independence" in text
    assert "provenance" in text.lower()
    assert "MESH_PERF_EXPERIMENTAL" in text


def test_capability_and_schema_docs():
    cap = (REPO / CAPABILITY_DOC).read_text(encoding="utf-8")
    sch = (REPO / SCHEMA_DOC).read_text(encoding="utf-8")
    assert "CP-0071" in cap
    assert "D4-A" in cap and "D4-K" in cap
    assert "live=DISABLED" in cap or "DISABLED" in cap
    assert "await_deepseek" in cap
    assert SCHEMA_ID in sch
    assert "RV-1" in sch
    assert "must be false" in sch.lower() or "**must be false**" in sch


def test_composed_cps_verified():
    for cp in COMPOSED_CPS:
        data = json.loads(
            (REPO / "snapshots" / cp / "CHECKPOINT.json").read_text(encoding="utf-8")
        )
        assert str(data.get("status", "")).upper() == "VERIFIED", cp


def test_gates_pass(tmp_path: Path):
    out = tmp_path / "releases" / "d1-safety-maturation"
    result = run_d1_safety_maturation_gates(
        REPO,
        out_dir=out,
        tip="d10071",
        timestamp="2026-09-27T03:05:00Z",
        pytest_count=1090,
        write_project_state=False,
    )
    assert result.ok, result.errors
    assert result.cp == SEAL_CP
    assert result.prior_cp == PRIOR_CP
    assert result.version == "0.18.0"
    path = Path(result.summary_path)
    assert path.is_file()
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["ok"] is True
    assert data["live"] == "DISABLED"
    assert data["m1_status"] == "NO_CONSENSUS_YET"
    assert data["mesh_perf_experimental"] == "OFF"
    assert data["d1_exit_ready_for_live"] is False
    assert data["package_open_0190"] is False
    assert data["d4_debt_ids"] == list(D4_DEBT_IDS)
    assert data["composed_cps"] == list(COMPOSED_CPS)


@pytest.mark.parametrize(
    "force_fail",
    [
        "planning_doc_present",
        "d4_ids_cited",
        "authority_matrix",
        "consensus_draft_no_default",
        "continuity_limits",
        "oversight_bounds",
        "rollback_verification",
        "evidence_provenance",
        "d1_exit_criteria",
        "claim_hygiene",
        "live_disabled",
        "composed_cps",
        "mesh_perf_experimental_off",
        "pkg0190_not_opened",
        "no_gia_claim",
        "authority_semantics",
        "version_held",
    ],
)
def test_gates_force_fail(tmp_path: Path, force_fail: str):
    result = run_d1_safety_maturation_gates(
        REPO,
        out_dir=tmp_path / force_fail,
        tip="bad",
        pytest_count=10,
        force_fail=force_fail,
        write_project_state=False,
    )
    assert not result.ok
    assert any(g.name == force_fail and not g.ok for g in result.gates)


def test_agreement_cycle67():
    text = (REPO / "council" / "COUNCIL_AGREEMENT_CYCLE67.md").read_text(encoding="utf-8")
    assert "CP-0071" in text
    assert "D4-A" in text
    assert "live=DISABLED" in text
    assert "NO_CONSENSUS_YET" in text


def test_paste_has_last_sealed():
    text = (REPO / "council" / "PASTE_CYCLE67_M2M.md").read_text(encoding="utf-8")
    assert "LAST_SEALED:" in text
    assert "CP-0070" in text
    assert "PREFERRED_NEXT: await_deepseek" in text
    assert "CP-0071" in text
    assert "65e4985" in text
    assert "D4-A" in text or "D4-A..K" in text


def test_tags_untouched_no_v019():
    assert (
        subprocess.run(
            ["git", "rev-parse", "--verify", "v0.18.0"],
            cwd=str(REPO),
            capture_output=True,
        ).returncode
        == 0
    )
    assert (
        subprocess.run(
            ["git", "rev-parse", "--verify", "v0.19.0"],
            cwd=str(REPO),
            capture_output=True,
        ).returncode
        != 0
    )


def test_no_gia_claims_in_d1_docs():
    for rel in (PLANNING_DOC, CAPABILITY_DOC):
        t = (REPO / rel).read_text(encoding="utf-8").lower()
        assert "we are gia" not in t
        assert "agi achieved" not in t
        assert "gia unlocked" not in t


def test_upstream_safety_continuity_oversight_present():
    assert (REPO / "docs/design/L_JUDGE_LIVE_ADAPTER_SAFETY_CASE.md").is_file()
    assert (REPO / "docs/design/ORCHESTRATOR_CONTINUITY_DESIGN.md").is_file()
    assert (REPO / "docs/design/ORCHESTRATOR_OVERSIGHT_HOOKS_DESIGN.md").is_file()
    assert (REPO / "council/COUNCIL_AGREEMENT_D4.md").is_file()
    assert (REPO / "council/D4_CHATGPT_FINDINGS.md").is_file()
