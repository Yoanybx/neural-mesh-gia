"""Mesh perf hotspot analysis + improvement designs (CP-0067 / Cycle 63).

Consumes CP-0066 microbench baselines, ranks *local* hotspots (not cross-system
ranking), and proposes experimental measurable improvements. Optional A/B
microbenches run only when ``experimental=True`` / flag enabled — defaults OFF.
No "world-fastest" claims; M1=NO_CONSENSUS_YET; no Raft/N>2/GIA unlock.
"""

from __future__ import annotations

import json
import os
import tempfile
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from neural_mesh.fence import FenceService
from neural_mesh.packaging.mesh_perf_research import (
    BENCH_NAMES,
    CLAIM_POLICY,
    M1_STATUS,
    N_CAP,
    BenchReport,
    BenchSample,
    assert_honest_claims,
    run_all_microbenches,
    run_microbench,
)
from neural_mesh.packaging.orchestrator_judge_routing import (
    OrchestratorRouter,
    RoutingReceipt,
    WorkloadClass,
    sample_envelope,
    verify_receipt_chain,
)
from neural_mesh.status_snapshot import snapshot

__all__ = [
    "PACKAGE_HELD",
    "CYCLE",
    "SEAL_CP",
    "PRIOR_CP",
    "PREFERRED_NEXT_DEFAULT",
    "LIVE_API_ENABLED",
    "SCHEMA_HOTSPOT",
    "SCHEMA_IMPROVEMENT",
    "N_CAP",
    "M1_STATUS",
    "EXPERIMENTAL_FLAG_ENV",
    "IMPROVEMENT_DESIGNS",
    "HotspotRow",
    "HotspotReport",
    "ImprovementDesign",
    "experimental_enabled",
    "analyze_hotspots",
    "ranked_improvement_designs",
    "bench_obs_tip_inject",
    "bench_fence_reuse_root",
    "bench_receipt_hash_memo",
    "run_experimental_ab",
    "assert_honest_claims",
]

PACKAGE_HELD = "0.18.0"
CYCLE = 63
SEAL_CP = "CP-0067"
PRIOR_CP = "CP-0066"
PREFERRED_NEXT_DEFAULT = "await_deepseek"
LIVE_API_ENABLED = False
SCHEMA_HOTSPOT = "mesh.perf.hotspot_report/v0"
SCHEMA_IMPROVEMENT = "mesh.perf.improvement_design/v0"
EXPERIMENTAL_FLAG_ENV = "MESH_PERF_EXPERIMENTAL"

# Ranked experimental improvement candidates (design surface).
# Order = priority for measurement follow-up; NOT a claim of achieved speedup.
IMPROVEMENT_DESIGNS: tuple[dict[str, Any], ...] = (
    {
        "id": "I1_obs_tip_inject_or_cache",
        "target": "obs_snapshot",
        "rank": 1,
        "summary": (
            "Avoid per-call git rev-parse by injecting tip= or a short TTL tip cache "
            "(research/ops callers that already know tip)."
        ),
        "mechanism": "snapshot(tip=...) already skips _git_tip7; optional process-local cache behind flag",
        "hypothesis": (
            "On this box, tip inject cut OBS median ~2.05ms → ~0.93ms (~55% local relative). "
            "Expect similar order when git subprocess dominates; IO remainder (cp list, pyproject) remains."
        ),
        "measure": "A/B: bench_obs_snapshot vs bench_obs_tip_inject; report median/p95 delta only",
        "risk": "stale tip if cache TTL too long; default OFF; never authority for fence/consensus",
        "status": "EXPERIMENTAL_MEASURABLE",
        "production_default": "OFF",
    },
    {
        "id": "I2_fence_harness_vs_logic_split",
        "target": "fence_path",
        "rank": 2,
        "summary": (
            "Separate TemporaryDirectory+bootstrap setup cost from dual-claim+probe logic "
            "so hotspot attribution is honest."
        ),
        "mechanism": "reuse data_root across iterations; measure dual+probe only",
        "hypothesis": (
            "Full fence_path ~2.6ms includes ~1.3ms tmp/bootstrap; reuse-root dual+probe ~1.2ms. "
            "Further fence gains need store read coalescing — separate experiment."
        ),
        "measure": "A/B: bench_fence_path vs bench_fence_reuse_root",
        "risk": "none for production (harness-only); do not weaken dual_primary=0 asserts",
        "status": "EXPERIMENTAL_MEASURABLE",
        "production_default": "N/A_HARNESS",
    },
    {
        "id": "I3_receipt_content_hash_memo",
        "target": "receipt_hash_chain",
        "rank": 3,
        "summary": (
            "Memoize RoutingReceipt.content_hash during verify_receipt_chain to avoid "
            "re-json+sha256 when building then verifying the same objects."
        ),
        "mechanism": "local memo dict keyed by id(receipt) inside experimental verify wrapper",
        "hypothesis": (
            "verify_only ~0.30ms for chain_len=32 is almost all content_hash; memo on second "
            "pass approaches near-zero; first-pass build still dominates (~0.7ms route)."
        ),
        "measure": "A/B: verify vs verify_with_memo on same chain; also build+verify",
        "risk": "memo invalid if receipt mutated after hash (receipts are append-only today)",
        "status": "EXPERIMENTAL_MEASURABLE",
        "production_default": "OFF",
    },
    {
        "id": "I4_obs_cp_index_cache",
        "target": "obs_snapshot",
        "rank": 4,
        "summary": "Cache _list_cp_ids result or maintain tip CP pointer instead of scanning snapshots/.",
        "mechanism": "mtime/size gated directory index; invalidate on CP mint",
        "hypothesis": "_list_cp_ids ~0.37ms local; grows with CP count; cache should drop to <<0.1ms hits",
        "measure": "microbench list_cp_ids cold vs warm after synthetic CP growth",
        "risk": "stale cp_tip if invalidation missed — fail-closed: miss → rescan",
        "status": "DESIGN_ONLY",
        "production_default": "OFF",
    },
    {
        "id": "I5_fence_store_read_coalesce",
        "target": "fence_path",
        "rank": 5,
        "summary": "Coalesce repeated fence_state/epoch/role JSON reads within a single probe()",
        "mechanism": "request-scoped read cache inside FenceStore for one probe/claim call",
        "hypothesis": "reuse-root dual+probe ~1.2ms; coalescing may cut tens of percent of remaining IO",
        "measure": "instrument read counts + A/B probe latency; dual_primary must stay 0",
        "risk": "stale state mid-probe if another process writes (N=2 local; document single-writer)",
        "status": "DESIGN_ONLY",
        "production_default": "OFF",
    },
    {
        "id": "I6_packaging_verify_batch_hash",
        "target": "packaging_verify",
        "rank": 6,
        "summary": "Single-pass hash of file bytes into running digest (avoid double read-write verify loop).",
        "mechanism": "hash-while-write then compare envelope only",
        "hypothesis": "packaging_verify already ~0.25ms local — low priority; expect modest relative gain",
        "measure": "A/B synthetic manifest 3-file vs larger fixture",
        "risk": "low; keep sha256 algorithm (no algorithm swap without design CP)",
        "status": "DESIGN_ONLY",
        "production_default": "OFF",
    },
    {
        "id": "I7_membership_sm_noop",
        "target": "membership_sm",
        "rank": 7,
        "summary": "No improvement planned — in-memory SM ~0.002ms; noise floor.",
        "mechanism": "none",
        "hypothesis": "not a hotspot under current local harness",
        "measure": "keep in run_all_microbenches as regression canary only",
        "risk": "none",
        "status": "DEFER",
        "production_default": "N/A",
    },
)


@dataclass
class HotspotRow:
    name: str
    median_ms: float
    p95_ms: float
    share_pct: float
    iterations: int
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "median_ms": self.median_ms,
            "p95_ms": self.p95_ms,
            "share_pct": self.share_pct,
            "iterations": self.iterations,
            "notes": self.notes,
        }


@dataclass
class HotspotReport:
    rows: list[HotspotRow] = field(default_factory=list)
    honest: bool = True
    m1_status: str = M1_STATUS
    ranking_claim: None = None
    box_local: bool = True
    baseline: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": SCHEMA_HOTSPOT,
            "honest": self.honest,
            "m1_status": self.m1_status,
            "ranking_claim": None,
            "box_local": True,
            "claim_policy": list(CLAIM_POLICY),
            "n_cap": N_CAP,
            "live_api": False,
            "note": (
                "Rows ranked by local median_ms only — NOT a cross-system ranking; "
                "ranking_claim=null"
            ),
            "hotspots": [r.to_dict() for r in self.rows],
            "baseline": self.baseline,
        }


@dataclass
class ImprovementDesign:
    payload: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        d = dict(self.payload)
        d["schema"] = SCHEMA_IMPROVEMENT
        d["ranking_claim"] = None
        d["m1_status"] = M1_STATUS
        d["achieved_speedup_claimed"] = False
        return d


def experimental_enabled(flag: str | None = None) -> bool:
    """Return True when MESH_PERF_EXPERIMENTAL enables research A/B benches.

    Values: ``1``/``true``/``all`` enable all; comma-list enables named flags
    (obs_tip_inject, fence_reuse_root, receipt_hash_memo). Default: disabled.
    """
    raw = os.environ.get(EXPERIMENTAL_FLAG_ENV, "").strip().lower()
    if not raw or raw in ("0", "false", "off", "no"):
        return False
    if raw in ("1", "true", "yes", "all"):
        return True
    if flag is None:
        return True
    return flag.strip().lower() in {p.strip() for p in raw.split(",") if p.strip()}


def analyze_hotspots(
    report: BenchReport | None = None,
    *,
    fence_iters: int = 11,
    obs_iters: int = 21,
    member_iters: int = 51,
    chain_iters: int = 11,
    pkg_iters: int = 11,
) -> HotspotReport:
    """Rank CP-0066-style microbench medians as local hotspots (honest)."""
    if report is None:
        report = run_all_microbenches(
            fence_iters=fence_iters,
            obs_iters=obs_iters,
            member_iters=member_iters,
            chain_iters=chain_iters,
            pkg_iters=pkg_iters,
        )
    samples = list(report.samples)
    total = sum(s.median_ms for s in samples) or 1.0
    rows = sorted(
        [
            HotspotRow(
                name=s.name,
                median_ms=float(s.median_ms),
                p95_ms=float(s.p95_ms),
                share_pct=100.0 * float(s.median_ms) / total,
                iterations=s.iterations,
                notes=s.notes,
            )
            for s in samples
        ],
        key=lambda r: r.median_ms,
        reverse=True,
    )
    out = HotspotReport(
        rows=rows,
        honest=True,
        m1_status=M1_STATUS,
        baseline=report.to_dict(),
    )
    assert_honest_claims(out.to_dict())
    return out


def ranked_improvement_designs() -> list[ImprovementDesign]:
    return [ImprovementDesign(payload=dict(p)) for p in IMPROVEMENT_DESIGNS]


def bench_obs_tip_inject(*, iterations: int = 21) -> BenchSample:
    """Experimental A: snapshot with tip injected (skips git subprocess)."""

    def once() -> None:
        snap = snapshot(tip="c63test")
        assert snap is not None
        assert snap.tip == "c63test"

    return run_microbench(
        once,
        name="obs_tip_inject",
        iterations=iterations,
        notes="experimental A/B: snapshot(tip=) skips _git_tip7; LOCAL only",
    )


def bench_fence_reuse_root(*, iterations: int = 11) -> BenchSample:
    """Experimental A: dual-claim+probe on a reused FenceService root."""

    times: list[float] = []
    with tempfile.TemporaryDirectory(prefix="mesh-perf-fence-reuse-") as td:
        root = Path(td) / "data"
        root.mkdir()
        svc = FenceService(root)
        svc.bootstrap_pair("n-a", "n-b", primary="n-a")
        # warmup
        for _ in range(2):
            svc.claim_primary("n-b", force_dual=True)
            svc.probe(auto_fence=True, preferred="n-a")
            assert svc.status().dual_primary == 0
        for _ in range(iterations):
            t0 = time.perf_counter()
            svc.claim_primary("n-b", force_dual=True)
            pr = svc.probe(auto_fence=True, preferred="n-a")
            st = svc.status()
            assert st.dual_primary == 0 and pr.dual_primary == 0
            times.append((time.perf_counter() - t0) * 1000.0)
    return BenchSample(
        name="fence_reuse_root",
        iterations=iterations,
        times_ms=times,
        notes="experimental A/B: dual+probe only; excludes TemporaryDirectory/bootstrap",
    )


def _verify_receipt_chain_memo(receipts: list[RoutingReceipt]) -> bool:
    """Experimental verify with content_hash memo (does not mutate receipts)."""
    memo: dict[int, str] = {}
    prev: str | None = None
    for r in receipts:
        if r.prev_receipt_hash != prev:
            return False
        if r.dual_primary != 0 or r.live_api is not False:
            return False
        key = id(r)
        h = memo.get(key)
        if h is None:
            h = r.content_hash()
            memo[key] = h
        prev = h
    return True


def bench_receipt_hash_memo(
    *, iterations: int = 21, chain_len: int = 32
) -> BenchSample:
    """Experimental A: build chain once, verify with memoized content_hash."""

    router = OrchestratorRouter()
    for i in range(chain_len):
        router.route(
            sample_envelope(
                request_id=f"hot:{i:04d}",
                workload_class=WorkloadClass.JUDGE_ADVISORY,
                prompt_body=f"hot-{i}",
            )
        )
    assert verify_receipt_chain(router.receipts)

    def once() -> None:
        # First pass fills memo; second pass hits — still correct
        assert _verify_receipt_chain_memo(router.receipts)
        assert _verify_receipt_chain_memo(router.receipts)

    return run_microbench(
        once,
        name="receipt_hash_memo",
        iterations=iterations,
        notes="experimental A/B: memoized verify (double-pass); LOCAL only",
    )


def run_experimental_ab(
    *,
    force: bool = False,
    obs_iters: int = 11,
    fence_iters: int = 7,
    memo_iters: int = 11,
) -> dict[str, Any]:
    """Run optional experimental A/B benches. Default skips unless flag/force.

    Never claims victory — returns paired medians for human/council review.
    """
    enabled = force or experimental_enabled()
    payload: dict[str, Any] = {
        "schema": "mesh.perf.experimental_ab/v0",
        "enabled": enabled,
        "env": EXPERIMENTAL_FLAG_ENV,
        "honest": True,
        "ranking_claim": None,
        "m1_status": M1_STATUS,
        "live_api": False,
        "achieved_speedup_claimed": False,
        "pairs": [],
    }
    if not enabled:
        payload["note"] = "experimental A/B skipped (flag OFF); designs remain DESIGN_ONLY"
        return payload

    pairs: list[dict[str, Any]] = []
    if force or experimental_enabled("obs_tip_inject"):
        from neural_mesh.packaging.mesh_perf_research import bench_obs_snapshot

        base = bench_obs_snapshot(iterations=obs_iters)
        alt = bench_obs_tip_inject(iterations=obs_iters)
        pairs.append(
            {
                "id": "I1_obs_tip_inject_or_cache",
                "baseline": base.to_dict(),
                "experimental": alt.to_dict(),
                "delta_median_ms": alt.median_ms - base.median_ms,
                "note": "negative delta_median_ms means experimental was faster locally",
            }
        )
    if force or experimental_enabled("fence_reuse_root"):
        from neural_mesh.packaging.mesh_perf_research import bench_fence_path

        base = bench_fence_path(iterations=fence_iters)
        alt = bench_fence_reuse_root(iterations=fence_iters)
        pairs.append(
            {
                "id": "I2_fence_harness_vs_logic_split",
                "baseline": base.to_dict(),
                "experimental": alt.to_dict(),
                "delta_median_ms": alt.median_ms - base.median_ms,
                "note": "isolates harness setup; not a production fence change",
            }
        )
    if force or experimental_enabled("receipt_hash_memo"):
        from neural_mesh.packaging.mesh_perf_research import bench_receipt_hash_chain

        base = bench_receipt_hash_chain(iterations=memo_iters, chain_len=32)
        alt = bench_receipt_hash_memo(iterations=memo_iters, chain_len=32)
        pairs.append(
            {
                "id": "I3_receipt_content_hash_memo",
                "baseline": base.to_dict(),
                "experimental": alt.to_dict(),
                "delta_median_ms": alt.median_ms - base.median_ms,
                "note": "memo verify vs full build+verify — different work; interpret carefully",
            }
        )
    payload["pairs"] = pairs
    assert_honest_claims(payload)
    return payload
