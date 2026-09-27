"""Mesh performance research track helpers (CP-0066 / Cycle 62).

Competitive *systems research plan* + local microbench harness for Mesh
packaging/ops paths. Honest baselines only — **no** "fastest in the world"
claims. Literature pointers (etcd / Raft / CRDT) are NON-default references;
M1 remains NO_CONSENSUS_YET. No GIA / Raft / N>2 runtime unlock.

Microbenches use time.perf_counter / timeit (pytest-benchmark optional later).
"""

from __future__ import annotations

import hashlib
import json
import statistics
import tempfile
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

from neural_mesh.fence import FenceService
from neural_mesh.packaging.m2_membership_rejoin import (
    MembershipSM,
    TrustTierName,
)
from neural_mesh.packaging.orchestrator_judge_routing import (
    OrchestratorRouter,
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
    "SCHEMA_PERF",
    "N_CAP",
    "M1_STATUS",
    "BENCH_NAMES",
    "CLAIM_POLICY",
    "NONDEFAULT_REFS",
    "BenchSample",
    "BenchReport",
    "ResearchProgram",
    "run_microbench",
    "bench_fence_path",
    "bench_obs_snapshot",
    "bench_membership_sm",
    "bench_receipt_hash_chain",
    "bench_packaging_verify",
    "run_all_microbenches",
    "assert_honest_claims",
]

PACKAGE_HELD = "0.18.0"
CYCLE = 62
SEAL_CP = "CP-0066"
PRIOR_CP = "CP-0065"
PREFERRED_NEXT_DEFAULT = "await_deepseek"
LIVE_API_ENABLED = False
SCHEMA_PERF = "mesh.perf.research_sample/v0"
N_CAP = 2
M1_STATUS = "NO_CONSENSUS_YET"

BENCH_NAMES: tuple[str, ...] = (
    "fence_path",
    "obs_snapshot",
    "membership_sm",
    "receipt_hash_chain",
    "packaging_verify",
)

# Honest claim policy — enforced in docs + tests
CLAIM_POLICY: tuple[str, ...] = (
    "LOCAL_BASELINE_ONLY",
    "NO_FASTEST_IN_WORLD",
    "NO_CROSS_SYSTEM_RANKING_WITHOUT_SHARED_HARNESS",
    "NONDEFAULT_LITERATURE_REFS",
)

# Literature pointers — NON-default (not Mesh consensus choice)
NONDEFAULT_REFS: tuple[dict[str, str], ...] = (
    {
        "name": "etcd",
        "role": "NON_DEFAULT_REFERENCE",
        "note": "Distributed KV / Raft-backed store; useful latency literature, not Mesh SoT.",
    },
    {
        "name": "Raft",
        "role": "NON_DEFAULT_REFERENCE",
        "note": "Consensus algorithm family; Mesh M1=NO_CONSENSUS_YET; Raft remains NO_HELD.",
    },
    {
        "name": "CRDT",
        "role": "NON_DEFAULT_REFERENCE",
        "note": "Conflict-free replicated data types; orthogonal research pointer, not default Mesh path.",
    },
)


@dataclass
class BenchSample:
    name: str
    iterations: int
    times_ms: list[float]
    notes: str = ""
    dual_primary: int = 0
    live_api: bool = False

    @property
    def median_ms(self) -> float:
        return float(statistics.median(self.times_ms)) if self.times_ms else 0.0

    @property
    def p95_ms(self) -> float:
        if not self.times_ms:
            return 0.0
        ordered = sorted(self.times_ms)
        idx = min(len(ordered) - 1, max(0, int(round(0.95 * (len(ordered) - 1)))))
        return float(ordered[idx])

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": SCHEMA_PERF,
            "name": self.name,
            "iterations": self.iterations,
            "median_ms": self.median_ms,
            "p95_ms": self.p95_ms,
            "min_ms": min(self.times_ms) if self.times_ms else 0.0,
            "max_ms": max(self.times_ms) if self.times_ms else 0.0,
            "notes": self.notes,
            "dual_primary": 0,
            "live_api": False,
            "claim_policy": list(CLAIM_POLICY),
            "m1_status": M1_STATUS,
            "ranking_claim": None,  # always null — no competitive ranking emitted
        }


@dataclass
class BenchReport:
    samples: list[BenchSample] = field(default_factory=list)
    honest: bool = True
    m1_status: str = M1_STATUS

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": "mesh.perf.research_report/v0",
            "samples": [s.to_dict() for s in self.samples],
            "honest": self.honest,
            "m1_status": self.m1_status,
            "claim_policy": list(CLAIM_POLICY),
            "nondefault_refs": list(NONDEFAULT_REFS),
            "n_cap": N_CAP,
            "live_api": False,
            "ranking_claim": None,
        }


@dataclass
class ResearchProgram:
    """What to measure (design surface for the research track)."""

    targets: tuple[str, ...] = BENCH_NAMES
    claim_policy: tuple[str, ...] = CLAIM_POLICY
    nondefault_refs: tuple[dict[str, str], ...] = NONDEFAULT_REFS
    m1_status: str = M1_STATUS

    def to_dict(self) -> dict[str, Any]:
        return {
            "targets": list(self.targets),
            "claim_policy": list(self.claim_policy),
            "nondefault_refs": list(self.nondefault_refs),
            "m1_status": self.m1_status,
            "purpose": (
                "Local microbench baselines for Mesh packaging/ops paths; "
                "honest comparison scaffolding — never 'fastest in world'."
            ),
            "deferred": [
                "shared cross-system harness vs etcd/Raft/CRDT",
                "live WAN benches",
                "N>2 / Raft unlock",
                "GIA",
            ],
        }


def run_microbench(
    fn: Callable[[], None],
    *,
    name: str,
    iterations: int = 21,
    warmup: int = 2,
    notes: str = "",
) -> BenchSample:
    """Time `fn` with perf_counter. Small iteration counts keep CI safe."""
    for _ in range(warmup):
        fn()
    times: list[float] = []
    for _ in range(iterations):
        t0 = time.perf_counter()
        fn()
        times.append((time.perf_counter() - t0) * 1000.0)
    return BenchSample(name=name, iterations=iterations, times_ms=times, notes=notes)


def bench_fence_path(*, iterations: int = 11) -> BenchSample:
    """H3 fence: bootstrap pair, inject dual-primary, ABORT→demote+re-elect via probe."""

    def once() -> None:
        with tempfile.TemporaryDirectory(prefix="mesh-perf-fence-") as td:
            root = Path(td) / "data"
            root.mkdir()
            svc = FenceService(root)
            svc.bootstrap_pair("n-a", "n-b", primary="n-a")
            svc.claim_primary("n-b", force_dual=True)
            pr = svc.probe(auto_fence=True, preferred="n-a")
            st = svc.status()
            assert st.dual_primary == 0
            assert pr.dual_primary == 0
            assert st.dual_primary_detected is False

    return run_microbench(
        once,
        name="fence_path",
        iterations=iterations,
        notes="local tmp FenceService probe(auto_fence); not cross-system",
    )


def bench_obs_snapshot(*, iterations: int = 21) -> BenchSample:
    def once() -> None:
        snap = snapshot()
        assert snap is not None

    return run_microbench(
        once,
        name="obs_snapshot",
        iterations=iterations,
        notes="status_snapshot.snapshot() local; IO-bound on project_state",
    )


def bench_membership_sm(*, iterations: int = 51) -> BenchSample:
    def once() -> None:
        sm = MembershipSM()
        sm.join_intent("n1", fingerprint="fp-n1")
        sm.begin_attest("n1")
        sm.attest_ok("n1", tier=TrustTierName.T2)
        sm.drain("n1")
        sm.drain_complete("n1")
        sm.rejoin_intent("n1")
        sm.enter_joining_from_rejoin("n1")

    return run_microbench(
        once,
        name="membership_sm",
        iterations=iterations,
        notes="in-memory M2 SM full churn path; N_CAP=2 held",
    )


def bench_receipt_hash_chain(*, iterations: int = 21, chain_len: int = 32) -> BenchSample:
    def once() -> None:
        r = OrchestratorRouter()
        for i in range(chain_len):
            r.route(
                sample_envelope(
                    request_id=f"req:{i:04d}",
                    workload_class=WorkloadClass.JUDGE_ADVISORY,
                    prompt_body=f"perf-{i}",
                )
            )
        assert verify_receipt_chain(r.receipts)
        assert len(r.receipts) == chain_len

    return run_microbench(
        once,
        name="receipt_hash_chain",
        iterations=iterations,
        notes=f"orchestrator routing receipts chain_len={chain_len}",
    )


def bench_packaging_verify(*, iterations: int = 21) -> BenchSample:
    """Lightweight packaging verify: deterministic sha256 over a synthetic manifest."""

    def once() -> None:
        with tempfile.TemporaryDirectory(prefix="mesh-perf-pkg-") as td:
            root = Path(td)
            files = {
                "manifest.json": json.dumps(
                    {
                        "schema": "mesh.perf.synthetic_manifest/v0",
                        "version": PACKAGE_HELD,
                        "dual_primary": 0,
                        "n_cap": N_CAP,
                        "files": ["a.txt", "b.txt"],
                    },
                    sort_keys=True,
                ),
                "a.txt": "alpha\n",
                "b.txt": "bravo\n",
            }
            digests: dict[str, str] = {}
            for name, body in files.items():
                path = root / name
                path.write_text(body, encoding="utf-8")
                digests[name] = hashlib.sha256(path.read_bytes()).hexdigest()
            # verify: re-hash and compare
            for name, expected in digests.items():
                got = hashlib.sha256((root / name).read_bytes()).hexdigest()
                assert got == expected
            # envelope digest
            blob = json.dumps(digests, sort_keys=True).encode()
            assert len(hashlib.sha256(blob).hexdigest()) == 64

    return run_microbench(
        once,
        name="packaging_verify",
        iterations=iterations,
        notes="synthetic manifest sha256 verify; local only",
    )


def run_all_microbenches(
    *,
    fence_iters: int = 7,
    obs_iters: int = 11,
    member_iters: int = 31,
    chain_iters: int = 11,
    pkg_iters: int = 11,
) -> BenchReport:
    """Run all named microbenches with CI-safe iteration counts."""
    samples = [
        bench_fence_path(iterations=fence_iters),
        bench_obs_snapshot(iterations=obs_iters),
        bench_membership_sm(iterations=member_iters),
        bench_receipt_hash_chain(iterations=chain_iters),
        bench_packaging_verify(iterations=pkg_iters),
    ]
    report = BenchReport(samples=samples, honest=True, m1_status=M1_STATUS)
    assert_honest_claims(report)
    return report


def assert_honest_claims(report: BenchReport | dict[str, Any] | str) -> None:
    """Fail closed on *affirmative* ranking language.

    Design docs may *mention* forbidden phrases while prohibiting them
    (e.g. "no fastest in the world"). Those negated mentions are allowed.
    """
    import re

    if isinstance(report, BenchReport):
        text = json.dumps(report.to_dict())
        if report.to_dict().get("ranking_claim") is not None:
            raise AssertionError("ranking_claim must be null")
    else:
        text = report if isinstance(report, str) else json.dumps(report)
    low = text.lower()
    # Affirmative patterns only (negation window ~48 chars before match)
    patterns = (
        r"(?<![\w-])(?:is|are|becomes|claims?|delivers?)\s+the\s+fastest\s+in\s+(?:the\s+)?world",
        r"(?<![\w-])world'?s\s+fastest",
        r"(?<![\w-])beats\s+etcd",
        r"(?<![\w-])beats\s+raft",
        r"(?<![\w-])faster\s+than\s+all",
        r"(?<![\w-])number\s+one\s+latency",
    )
    for pat in patterns:
        for m in re.finditer(pat, low):
            window = low[max(0, m.start() - 96) : m.start()]
            if re.search(r"\b(?:no|not|never|forbid(?:den)?|prohibit(?:ed)?|without|unlike)\b", window):
                continue
            raise AssertionError(f"forbidden performance claim near: {m.group(0)!r}")
