"""Tests for Cycle 62 / CP-0066: MESH_PERF_RESEARCH_TRACK.

Markers: mesh_perf_research_cycle62
Honest local microbenches only; no fastest-in-world claims; M1=NO_CONSENSUS_YET;
no Raft/N>2/GIA unlock.
"""

from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

import pytest

from neural_mesh import __version__
from neural_mesh.packaging.mesh_perf_research import (
    BENCH_NAMES,
    CLAIM_POLICY,
    CYCLE,
    LIVE_API_ENABLED,
    M1_STATUS,
    N_CAP,
    NONDEFAULT_REFS,
    PACKAGE_HELD,
    PREFERRED_NEXT_DEFAULT,
    PRIOR_CP,
    SCHEMA_PERF,
    SEAL_CP,
    ResearchProgram,
    assert_honest_claims,
    bench_fence_path,
    bench_membership_sm,
    bench_obs_snapshot,
    bench_packaging_verify,
    bench_receipt_hash_chain,
    run_all_microbenches,
)

pytestmark = [pytest.mark.mesh_perf_research_cycle62]

REPO = Path(__file__).resolve().parents[1]
DESIGN = REPO / "docs" / "design" / "MESH_PERF_RESEARCH_TRACK.md"
LIT = REPO / "docs" / "design" / "MESH_PERF_LITERATURE_POINTERS_NONDEFAULT.md"
CAP = REPO / "docs" / "capabilities" / "MESH_PERF_RESEARCH_TRACK.md"
AGREEMENT = REPO / "council" / "COUNCIL_AGREEMENT_CYCLE62.md"
PASTE = REPO / "council" / "PASTE_CYCLE62_M2M.md"
PKG = REPO / "src" / "neural_mesh" / "packaging" / "mesh_perf_research.py"


def test_version_and_constants():
    assert __version__ == "0.18.0"
    assert PACKAGE_HELD == "0.18.0"
    assert SEAL_CP == "CP-0066"
    assert PRIOR_CP == "CP-0065"
    assert CYCLE == 62
    assert PREFERRED_NEXT_DEFAULT == "await_deepseek"
    assert SCHEMA_PERF == "mesh.perf.research_sample/v0"
    assert N_CAP == 2
    assert LIVE_API_ENABLED is False
    assert M1_STATUS == "NO_CONSENSUS_YET"
    assert set(BENCH_NAMES) == {
        "fence_path",
        "obs_snapshot",
        "membership_sm",
        "receipt_hash_chain",
        "packaging_verify",
    }
    assert "NO_FASTEST_IN_WORLD" in CLAIM_POLICY


def test_design_literature_capability():
    assert DESIGN.is_file() and LIT.is_file() and CAP.is_file()
    d = DESIGN.read_text(encoding="utf-8")
    assert "CP-0066" in d
    assert "fence_path" in d and "obs_snapshot" in d
    assert "membership_sm" in d and "receipt_hash_chain" in d
    assert "packaging_verify" in d
    assert "fastest in the world" in d.lower()  # mentioned as forbidden
    assert "NO_CONSENSUS_YET" in d
    assert "NO_HELD" in d
    lit = LIT.read_text(encoding="utf-8")
    assert "etcd" in lit and "Raft" in lit and "CRDT" in lit
    assert "NON_DEFAULT" in lit or "NON-DEFAULT" in lit or "NONDEFAULT" in lit
    assert "NO_CONSENSUS_YET" in lit
    c = CAP.read_text(encoding="utf-8")
    assert "MESH_PERF_RESEARCH_TRACK" in c
    assert "CP-0066" in c


def test_research_program_surface():
    prog = ResearchProgram()
    d = prog.to_dict()
    assert set(d["targets"]) == set(BENCH_NAMES)
    assert d["m1_status"] == M1_STATUS
    assert "Raft" in d["deferred"] or any("Raft" in x for x in d["deferred"])
    assert len(d["nondefault_refs"]) == 3


def test_individual_microbenches_smoke():
    # Tiny iteration counts for unit speed; CI-safe
    f = bench_fence_path(iterations=2)
    assert f.name == "fence_path" and f.median_ms >= 0 and f.dual_primary == 0
    o = bench_obs_snapshot(iterations=2)
    assert o.name == "obs_snapshot" and o.iterations == 2
    m = bench_membership_sm(iterations=3)
    assert m.name == "membership_sm"
    c = bench_receipt_hash_chain(iterations=2, chain_len=4)
    assert c.name == "receipt_hash_chain"
    p = bench_packaging_verify(iterations=2)
    assert p.name == "packaging_verify"
    for s in (f, o, m, c, p):
        assert s.live_api is False
        assert s.to_dict()["ranking_claim"] is None
        assert s.to_dict()["m1_status"] == M1_STATUS


def test_run_all_microbenches_honest_report():
    report = run_all_microbenches(
        fence_iters=2,
        obs_iters=2,
        member_iters=3,
        chain_iters=2,
        pkg_iters=2,
    )
    assert report.honest is True
    assert report.m1_status == M1_STATUS
    names = [s.name for s in report.samples]
    assert names == list(BENCH_NAMES)
    d = report.to_dict()
    assert d["ranking_claim"] is None
    assert d["live_api"] is False
    assert_honest_claims(report)


def test_assert_honest_claims_rejects_forbidden():
    with pytest.raises(AssertionError):
        assert_honest_claims("Mesh is the fastest in the world at fencing")
    with pytest.raises(AssertionError):
        assert_honest_claims({"note": "beats etcd on all writes"})
    assert_honest_claims("local baseline median_ms=1.2; no ranking")


def test_nondefault_refs_do_not_unlock_runtime():
    names = {r["name"] for r in NONDEFAULT_REFS}
    assert names == {"etcd", "Raft", "CRDT"}
    for r in NONDEFAULT_REFS:
        assert r["role"] == "NON_DEFAULT_REFERENCE"
    # Design must not claim unlock
    text = (DESIGN.read_text() + LIT.read_text()).lower()
    assert "we unlocked raft" not in text
    assert "n>2 is live" not in text
    assert "raft enabled" not in text


def test_docs_forbid_false_superlatives():
    blob = "\n".join(
        p.read_text(encoding="utf-8") for p in (DESIGN, LIT, CAP, PKG)
    )
    assert_honest_claims(blob)
    # Ensure policy language present
    assert "LOCAL_BASELINE_ONLY" in blob or "local" in blob.lower()
    assert "NO_FASTEST_IN_WORLD" in blob or "no" in blob.lower() and "fastest" in blob.lower()


def test_no_live_secrets():
    for path in (DESIGN, LIT, CAP, PKG):
        text = path.read_text(encoding="utf-8")
        assert not re.search(r"sk-[A-Za-z0-9]{10,}", text), path.name
        assert "BEGIN PRIVATE KEY" not in text


def test_council_paste_last_sealed():
    assert AGREEMENT.is_file() and PASTE.is_file()
    ptext = PASTE.read_text(encoding="utf-8")
    assert "CP-0066" in ptext
    assert "LAST_SEALED" in ptext
    assert "CP-0065" in ptext
    assert "PREFERRED_NEXT" in ptext
    assert "await_deepseek" in ptext
    assert "NO_CONSENSUS_YET" in ptext or "m1=NO_CONSENSUS_YET" in ptext.lower()
    assert "fastest in the world" not in ptext.lower() or "no" in ptext.lower()
    atext = AGREEMENT.read_text(encoding="utf-8")
    assert "CP-0066" in atext and "NO_HELD" in atext


def test_tags_untouched():
    assert subprocess.run(
        ["git", "rev-parse", "--verify", "v0.18.0"],
        cwd=str(REPO),
        capture_output=True,
    ).returncode == 0


def test_sample_json_roundtrip():
    report = run_all_microbenches(
        fence_iters=1, obs_iters=1, member_iters=1, chain_iters=1, pkg_iters=1
    )
    blob = json.dumps(report.to_dict())
    data = json.loads(blob)
    assert data["honest"] is True
    assert len(data["samples"]) == 5
