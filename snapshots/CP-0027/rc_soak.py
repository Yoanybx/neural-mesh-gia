"""RC soak stability (CP-0027 / P15).

Deterministic, fast soak of an installed single-node RC:
N iterations of install-or-reuse prefix → status snapshot → verify_bundle
→ optional clean_node smoke. Records step latencies; fails if any iteration
fails or variance exceeds a simple bound.
"""

from __future__ import annotations

import json
import statistics
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

from .bundle import build_bundle, verify_bundle
from .clean_smoke import clean_node_smoke
from .manifest import FREEZE_CHANNEL
from .rc_install import rc_install_verify

__all__ = [
    "SoakIteration",
    "SoakResult",
    "DEFAULT_ITERATIONS",
    "DEFAULT_VARIANCE_RATIO",
    "percentile",
    "run_rc_soak",
]

DEFAULT_ITERATIONS = 5
DEFAULT_VARIANCE_RATIO = 100.0  # max_ms / max(p50, 1) must be <= this


@dataclass
class SoakIteration:
    index: int
    ok: bool
    steps_ms: dict[str, float] = field(default_factory=dict)
    total_ms: float = 0.0
    errors: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "index": self.index,
            "ok": self.ok,
            "steps_ms": dict(self.steps_ms),
            "total_ms": self.total_ms,
            "errors": list(self.errors),
        }


@dataclass
class SoakResult:
    ok: bool = True
    errors: list[str] = field(default_factory=list)
    iterations: list[SoakIteration] = field(default_factory=list)
    n: int = 0
    pass_count: int = 0
    fail_count: int = 0
    step_stats: dict[str, dict[str, float]] = field(default_factory=dict)
    total_p50_ms: float | None = None
    total_p99_ms: float | None = None
    variance_ratio: float | None = None
    variance_bound: float = DEFAULT_VARIANCE_RATIO
    prefix: str | None = None
    version: str | None = None
    freeze_channel: str | None = None
    report_path: str | None = None

    def fail(self, msg: str) -> None:
        self.ok = False
        self.errors.append(msg)

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "errors": list(self.errors),
            "n": self.n,
            "pass": self.pass_count,
            "fail": self.fail_count,
            "iterations": [it.to_dict() for it in self.iterations],
            "step_stats": self.step_stats,
            "total_p50_ms": self.total_p50_ms,
            "total_p99_ms": self.total_p99_ms,
            "variance_ratio": self.variance_ratio,
            "variance_bound": self.variance_bound,
            "prefix": self.prefix,
            "version": self.version,
            "freeze_channel": self.freeze_channel,
            "report_path": self.report_path,
        }

    def to_json(self, *, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, sort_keys=True) + "\n"


def percentile(values: list[float], pct: float) -> float:
    """Nearest-rank percentile; ``pct`` in [0, 100]."""
    if not values:
        return 0.0
    if len(values) == 1:
        return float(values[0])
    ordered = sorted(values)
    if pct <= 0:
        return float(ordered[0])
    if pct >= 100:
        return float(ordered[-1])
    # nearest-rank
    k = max(1, int(round(pct / 100.0 * len(ordered))))
    return float(ordered[min(k, len(ordered)) - 1])


def _time_step(name: str, steps: dict[str, float], fn: Callable[[], Any]) -> Any:
    t0 = time.perf_counter()
    try:
        return fn()
    finally:
        steps[name] = (time.perf_counter() - t0) * 1000.0


def run_rc_soak(
    root: Path | str | None = None,
    *,
    bundle: Path | str | None = None,
    prefix: Path | str | None = None,
    n: int = DEFAULT_ITERATIONS,
    out_dir: Path | str | None = None,
    report_path: Path | str | None = None,
    variance_bound: float = DEFAULT_VARIANCE_RATIO,
    run_clean_smoke: bool = True,
    reuse_prefix: bool = True,
    tip: str | None = None,
    ver: str | None = None,
    # Test hooks
    force_fail_step: str | None = None,
    step_hooks: dict[str, Callable[[], None]] | None = None,
) -> SoakResult:
    """Run N soak iterations; return SoakResult with latency stats."""
    result = SoakResult(n=max(1, int(n)), variance_bound=float(variance_bound))
    root_p = Path(root).resolve() if root else None
    out = Path(out_dir) if out_dir else (
        (root_p / "dist" / "soak") if root_p else Path("dist/soak")
    )
    out.mkdir(parents=True, exist_ok=True)

    # Resolve / build bundle
    bundle_path: Path | None = Path(bundle).resolve() if bundle else None
    if bundle_path is None:
        if root_p is None:
            result.fail("root or bundle required")
            return result
        m = build_bundle(
            root_p,
            out,
            tip=tip or "soakrun",
            ver=ver,
            freeze=True,
        )
        bundle_path = out / f"{m.name}-{m.ver}.tar.gz"
        result.version = m.ver
        if m.freeze:
            result.freeze_channel = m.freeze.channel

    if not bundle_path.is_file():
        result.fail(f"bundle missing: {bundle_path}")
        return result

    # Pre-verify once
    vr0 = verify_bundle(bundle_path, smoke=False)
    if not vr0.ok:
        result.fail("initial verify_bundle failed: " + "; ".join(vr0.errors))
        return result
    if vr0.manifest is not None:
        result.version = result.version or vr0.manifest.ver
        if vr0.manifest.freeze:
            result.freeze_channel = vr0.manifest.freeze.channel

    pfx = Path(prefix) if prefix else (out / "prefix")
    pfx.mkdir(parents=True, exist_ok=True)
    result.prefix = str(pfx)

    hooks = step_hooks or {}

    for i in range(result.n):
        it = SoakIteration(index=i, ok=True)
        steps: dict[str, float] = {}
        t_iter = time.perf_counter()
        try:
            # --- install-or-reuse ---
            def _install() -> None:
                if force_fail_step == "install":
                    raise RuntimeError("forced fail: install")
                if "install" in hooks:
                    hooks["install"]()
                    return
                # First iteration always install; later reuse if requested
                clear = not (reuse_prefix and i > 0 and (pfx / "bin" / "mesh").is_file())
                if clear or i == 0:
                    ir = rc_install_verify(
                        bundle_path,
                        prefix=pfx,
                        forbidden_repo=root_p,
                        keep_prefix=True,
                        expect_freeze_channel=FREEZE_CHANNEL,
                    )
                    if not ir.ok:
                        raise RuntimeError("rc_install_verify: " + "; ".join(ir.errors))
                    result.version = ir.version or result.version
                    result.freeze_channel = ir.freeze_channel or result.freeze_channel
                else:
                    # Reuse: still confirm launcher present
                    if not (pfx / "bin" / "mesh").is_file():
                        raise RuntimeError("reuse prefix missing bin/mesh")

            _time_step("install", steps, _install)

            # --- status snapshot ---
            def _status() -> None:
                if force_fail_step == "status":
                    raise RuntimeError("forced fail: status")
                if "status" in hooks:
                    hooks["status"]()
                    return
                import os
                import subprocess
                import sys

                launcher = pfx / "bin" / "mesh"
                py = sys.executable
                env = os.environ.copy()
                env.pop("PYTHONPATH", None)
                env["PYTHONNOUSERSITE"] = "1"
                root_ext = pfx / "root"
                st = subprocess.run(
                    [py, str(launcher), "status", "--snapshot"],
                    cwd=str(root_ext if root_ext.is_dir() else pfx),
                    env=env,
                    capture_output=True,
                    text=True,
                    timeout=60,
                    check=False,
                )
                if st.returncode != 0:
                    raise RuntimeError(
                        f"status --snapshot failed: {st.stderr.strip() or st.stdout.strip()}"
                    )

            _time_step("status", steps, _status)

            # --- verify_bundle checksums ---
            def _verify() -> None:
                if force_fail_step == "verify":
                    raise RuntimeError("forced fail: verify")
                if "verify" in hooks:
                    hooks["verify"]()
                    return
                vr = verify_bundle(bundle_path, smoke=False)
                if not vr.ok:
                    raise RuntimeError("verify_bundle: " + "; ".join(vr.errors))

            _time_step("verify", steps, _verify)

            # --- optional clean_node smoke ---
            if run_clean_smoke:

                def _smoke() -> None:
                    if force_fail_step == "smoke":
                        raise RuntimeError("forced fail: smoke")
                    if "smoke" in hooks:
                        hooks["smoke"]()
                        return
                    cs = clean_node_smoke(
                        bundle_path,
                        forbidden_repo=root_p,
                        run_verify=True,
                        run_status_snapshot=False,
                    )
                    if not cs.ok:
                        raise RuntimeError("clean_node_smoke: " + "; ".join(cs.errors))

                _time_step("smoke", steps, _smoke)

        except Exception as exc:  # noqa: BLE001
            it.ok = False
            it.errors.append(str(exc))
            result.fail(f"iteration[{i}]: {exc}")

        it.steps_ms = steps
        it.total_ms = (time.perf_counter() - t_iter) * 1000.0
        # If steps timed but exception after, keep ok=False
        result.iterations.append(it)
        if it.ok:
            result.pass_count += 1
        else:
            result.fail_count += 1

    # Aggregate stats
    step_names: set[str] = set()
    for it in result.iterations:
        step_names.update(it.steps_ms.keys())
    stats: dict[str, dict[str, float]] = {}
    for name in sorted(step_names):
        vals = [it.steps_ms[name] for it in result.iterations if name in it.steps_ms]
        if not vals:
            continue
        stats[name] = {
            "p50_ms": percentile(vals, 50),
            "p99_ms": percentile(vals, 99),
            "max_ms": float(max(vals)),
            "min_ms": float(min(vals)),
            "mean_ms": float(statistics.fmean(vals)),
        }
    result.step_stats = stats

    totals = [it.total_ms for it in result.iterations]
    if totals:
        result.total_p50_ms = percentile(totals, 50)
        result.total_p99_ms = percentile(totals, 99)
        p50 = max(result.total_p50_ms or 1.0, 1.0)
        result.variance_ratio = float(max(totals)) / p50
        if result.variance_ratio > result.variance_bound:
            result.fail(
                f"variance_ratio {result.variance_ratio:.2f} > bound {result.variance_bound}"
            )

    # Write report
    rp = Path(report_path) if report_path else (out / "rc_soak_report.json")
    rp.parent.mkdir(parents=True, exist_ok=True)
    rp.write_text(result.to_json(), encoding="utf-8")
    result.report_path = str(rp)
    return result
