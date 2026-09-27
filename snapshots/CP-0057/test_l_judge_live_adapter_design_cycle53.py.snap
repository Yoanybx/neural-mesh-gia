"""Tests for Cycle 53 / CP-0057: L_judge live-adapter design (design-only).

Markers: l_judge_live_adapter_design_cycle53
No live API keys; no network; no src/ judge codec.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

import pytest

from neural_mesh import __version__

pytestmark = [pytest.mark.l_judge_live_adapter_design_cycle53]

REPO = Path(__file__).resolve().parents[1]
DESIGN = REPO / "docs" / "design" / "L_JUDGE_LIVE_ADAPTER_DESIGN.md"
CAP = REPO / "docs" / "capabilities" / "MESH_L_JUDGE_LIVE_ADAPTER_DESIGN.md"


def test_version_held():
    assert __version__ == "0.18.0"


def test_design_doc_present():
    assert DESIGN.is_file()
    text = DESIGN.read_text(encoding="utf-8")
    assert "DESIGN ONLY" in text
    assert "CP-0057" in text
    assert "EngineTransport" in text
    assert "PromptBundle" in text
    assert "RawEngineResult" in text
    assert "secret_handle" in text
    assert "RefuseTransport" in text
    assert "enabled\": false" in text or "enabled=false" in text


def test_extends_prior_l_judge_artifacts():
    text = DESIGN.read_text(encoding="utf-8")
    assert "L_JUDGE_MIX_INTEGRATION" in text
    assert "L_JUDGE_MIX_DESIGN" in text
    assert "dry_run" in text
    assert "live_advisory" in text
    assert (REPO / "docs" / "design" / "L_JUDGE_MIX_INTEGRATION.md").is_file()
    assert (REPO / "docs" / "schema" / "judge" / "v0.md").is_file()
    assert (REPO / "docs" / "schema" / "judge" / "injection_v0.md").is_file()


def test_no_live_api_or_keys_in_design():
    text = DESIGN.read_text(encoding="utf-8")
    assert "no live API" in text.lower() or "No live API" in text
    # Forbid embedding live-looking secrets (mentions as forbidden OK)
    assert not re.search(r"sk-[A-Za-z0-9]{10,}", text)
    assert "Authorization: Bearer sk-" not in text
    assert "secret_handle" in text
    assert "forbid embedding" in text.lower() or "never a raw key" in text.lower()


def test_failure_taxonomy_and_abort():
    text = DESIGN.read_text(encoding="utf-8")
    for code in (
        "ENGINE_DISABLED",
        "ENGINE_AUTH",
        "ENGINE_TIMEOUT",
        "ENGINE_HTTP",
        "PLAINTEXT_FORBIDDEN",
        "SCHEMA_INVALID",
        "NO_AUDIT",
        "FENCE",
    ):
        assert code in text
    assert "never invent ACCEPT" in text.lower() or "Never invent ACCEPT" in text
    assert "forbid_plaintext" in text


def test_default_live_disabled():
    text = DESIGN.read_text(encoding="utf-8")
    assert "enabled=false" in text or '"enabled": false' in text
    assert "RefuseTransport" in text
    assert "safe default" in text.lower() or "Default for this design" in text


def test_capability_and_agreement():
    assert CAP.is_file()
    ctext = CAP.read_text(encoding="utf-8")
    assert "CP-0057" in ctext
    assert "DESIGN ONLY" in ctext
    assert "NO_HELD" in ctext
    atext = (REPO / "council" / "COUNCIL_AGREEMENT_CYCLE53.md").read_text(encoding="utf-8")
    assert "CP-0057" in atext
    assert "live-adapter" in atext.lower() or "live_adapter" in atext.lower()


def test_no_src_judge_codec():
    src = REPO / "src" / "neural_mesh"
    banned = list(src.glob("judge*.py")) + list(src.glob("**/live_adapter*.py"))
    assert banned == [], f"unexpected runtime codec files: {banned}"
    text = DESIGN.read_text(encoding="utf-8").lower()
    assert "no `src/`" in text or "no src/" in text or "codec" in text


def test_no_gia_raft_train_claims():
    text = DESIGN.read_text(encoding="utf-8")
    low = text.lower()
    assert "NO_HELD" in text
    assert "DO_NOT_TRAIN_70B_NOW" in text
    assert "we unlocked gia" not in low
    assert "raft runtime" not in low or "no raft" in low
    assert "n>2" in low  # mentioned as forbidden


def test_l1_still_closed_context():
    # Continuity: L1 closeout remains CLOSED while advancing design
    bp = (REPO / "council" / "blueprint" / "FINAL_BLUEPRINT_ROOT.md").read_text(
        encoding="utf-8"
    )
    assert "L1 REMAINING_0.17 [CLOSED]" in bp
    assert (REPO / "docs" / "planning" / "L1_RESIDUE_CLOSEOUT.md").is_file()


def test_tags_untouched():
    for tag in ("v0.18.0", "v0.17.0", "v0.16.3"):
        assert (
            subprocess.run(
                ["git", "rev-parse", "--verify", tag],
                cwd=str(REPO),
                capture_output=True,
            ).returncode
            == 0
        )


def test_pyproject_marker_registered():
    text = (REPO / "pyproject.toml").read_text(encoding="utf-8")
    assert "l_judge_live_adapter_design_cycle53" in text
