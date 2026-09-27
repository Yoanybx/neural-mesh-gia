"""Tests for Cycle 63 / CP-0067: perf_hotspot_and_improvement_design.

Markers: mesh_perf_hotspot_cycle63
Hotspot analysis + ranked improvement designs; optional experimental A/B
behind flag (default OFF). No world-fastest claims; M1=NO_CONSENSUS_YET;
no Raft/N>2/GIA unlock.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
from pathlib import Path

import pytest

from neural_mesh import __version__
from neural_mesh.packaging.mesh_perf_hotspot import (
    CYCLE,
    EXPERIMENTAL_FLAG_ENV,
    IMPROVEMENT_DESIGNS,
    LIVE_API_ENABLED,
    M1_STATUS,
    N_CAP,
    PACKAGE_HELD,
    PREFERRED_NEXT_DEFAULT,
    PRIOR_CP,
    SCHEMA_HOTSPOT,
    SEAL_CP,
    analyze_hotspots,
    assert_honest_claims,
    bench_fence_reuse_root,
    bench_obs_tip_inject,
    bench_receipt_hash_memo,
    experimental_enabled,
    ranked_improvement_designs,
    run_experimental_ab,
)
from neural_mesh.packaging.mesh_perf_research import BENCH_NAMES, run_all_microbenches

pytestmark = [pytest.mark.mesh_perf_hotspot_cycle63]

REPO = Path(__file__).resolve().parents[1]
DESIGN = REPO / "docs" / "design" / "MESH_PERF_HOTSPOT_AND_IMPROVEMENT_DESIGN.md"
CAP = REPO / "docs" / "capabilities" / "MESH_PERF_HOTSPOT_AND_IMPROVEMENT.md"
AGREEMENT = REPO / "council" / "COUNCIL_AGREEMENT_CYCLE63.md"
PASTE = REPO / "council" / "PASTE_CYCLE63_M2M.md"
PKG = REPO / "src" / "neural_mesh" / "packaging" / "mesh_perf_hotspot.py"


def test_version_and_constants():
    assert __version__ == "0.18.0"
    assert PACKAGE_HELD == "0.18.0"
    assert SEAL_CP == "CP-0067"
    assert PRIOR_CP == "CP-0066"
    assert CYCLE == 63
    assert PREFERRED_NEXT_DEFAULT == "await_deepseek"
    assert SCHEMA_HOTSPOT == "mesh.perf.hotspot_report/v0"
    assert N_CAP == 2
    assert LIVE_API_ENABLED is False
    assert M1_STATUS == "NO_CONSENSUS_YET"
    assert EXPERIMENTAL_FLAG_ENV == "MESH_PERF_EXPERIMENTAL"


def test_design_and_capability():
    assert DESIGN.is_file() and CAP.is_file()
    d = DESIGN.read_text(encoding="utf-8")
    assert "CP-0067" in d
    assert "I1" in d and "I2" in d and "I3" in d
    assert "hotspot" in d.lower()
    assert "NO_CONSENSUS_YET" in d
    assert "NO_HELD" in d
    assert "ranking_claim" in d.lower() or "ranking_claim=null" in d
    assert "continuity" in d.lower()  # queued, not dropped
    c = CAP.read_text(encoding="utf-8")
    assert "CP-0067" in c
    assert "perf_hotspot_and_improvement_design" in c
    assert "await_deepseek" in c


def test_analyze_hotspots_ranks_all_benches():
    report = run_all_microbenches(
        fence_iters=2, obs_iters=2, member_iters=3, chain_iters=2, pkg_iters=2
    )
    hot = analyze_hotspots(report)
    assert hot.honest is True
    assert hot.ranking_claim is None
    names = [r.name for r in hot.rows]
    assert set(names) == set(BENCH_NAMES)
    # local rank: descending median
    medians = [r.median_ms for r in hot.rows]
    assert medians == sorted(medians, reverse=True)
    d = hot.to_dict()
    assert d["ranking_claim"] is None
    assert d["box_local"] is True
    assert_honest_claims(d)


def test_ranked_improvement_designs():
    designs = ranked_improvement_designs()
    assert len(designs) == len(IMPROVEMENT_DESIGNS) == 7
    ids = [x.to_dict()["id"] for x in designs]
    assert ids[0].startswith("I1_")
    assert ids[2].startswith("I3_")
    for d in designs:
        payload = d.to_dict()
        assert payload["ranking_claim"] is None
        assert payload["achieved_speedup_claimed"] is False
        assert payload["m1_status"] == M1_STATUS
        assert payload["production_default"] in ("OFF", "N/A_HARNESS", "N/A")


def test_experimental_flag_default_off(monkeypatch):
    monkeypatch.delenv(EXPERIMENTAL_FLAG_ENV, raising=False)
    assert experimental_enabled() is False
    skipped = run_experimental_ab()
    assert skipped["enabled"] is False
    assert skipped["pairs"] == []
    assert skipped["ranking_claim"] is None
    assert skipped["achieved_speedup_claimed"] is False


def test_experimental_ab_force_runs_pairs():
    # force=True exercises A/B without requiring env; tiny iters
    ab = run_experimental_ab(
        force=True, obs_iters=2, fence_iters=2, memo_iters=2
    )
    assert ab["enabled"] is True
    assert ab["ranking_claim"] is None
    assert ab["achieved_speedup_claimed"] is False
    ids = {p["id"] for p in ab["pairs"]}
    assert "I1_obs_tip_inject_or_cache" in ids
    assert "I2_fence_harness_vs_logic_split" in ids
    assert "I3_receipt_content_hash_memo" in ids
    assert_honest_claims(ab)


def test_experimental_individual_benches_smoke():
    o = bench_obs_tip_inject(iterations=2)
    assert o.name == "obs_tip_inject" and o.median_ms >= 0
    f = bench_fence_reuse_root(iterations=2)
    assert f.name == "fence_reuse_root" and f.dual_primary == 0
    r = bench_receipt_hash_memo(iterations=2, chain_len=4)
    assert r.name == "receipt_hash_memo"
    for s in (o, f, r):
        assert s.live_api is False
        assert s.to_dict()["ranking_claim"] is None


def test_docs_and_pkg_honest():
    blob = "\n".join(p.read_text(encoding="utf-8") for p in (DESIGN, CAP, PKG))
    assert_honest_claims(blob)
    with pytest.raises(AssertionError):
        assert_honest_claims("Mesh is the fastest in the world at OBS")


def test_no_live_secrets():
    for path in (DESIGN, CAP, PKG):
        text = path.read_text(encoding="utf-8")
        assert not re.search(r"sk-[A-Za-z0-9]{10,}", text), path.name
        assert "BEGIN PRIVATE KEY" not in text


def test_council_paste_last_sealed():
    assert AGREEMENT.is_file() and PASTE.is_file()
    ptext = PASTE.read_text(encoding="utf-8")
    assert "CP-0067" in ptext
    assert "LAST_SEALED" in ptext
    assert "CP-0066" in ptext
    assert "0778d32" in ptext or "tip=0778d32" in ptext
    assert "PREFERRED_NEXT" in ptext
    assert "await_deepseek" in ptext
    assert "NO_CONSENSUS_YET" in ptext or "m1=NO_CONSENSUS_YET" in ptext.lower()
    # no affirmative world-fastest
    assert_honest_claims(ptext)
    atext = AGREEMENT.read_text(encoding="utf-8")
    assert "CP-0067" in atext and "NO_HELD" in atext


def test_tags_untouched():
    assert (
        subprocess.run(
            ["git", "rev-parse", "--verify", "v0.18.0"],
            cwd=str(REPO),
            capture_output=True,
        ).returncode
        == 0
    )


def test_hotspot_json_roundtrip():
    hot = analyze_hotspots(
        run_all_microbenches(
            fence_iters=1, obs_iters=1, member_iters=1, chain_iters=1, pkg_iters=1
        )
    )
    data = json.loads(json.dumps(hot.to_dict()))
    assert data["honest"] is True
    assert len(data["hotspots"]) == 5
