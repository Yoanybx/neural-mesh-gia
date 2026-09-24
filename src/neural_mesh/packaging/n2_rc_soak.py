"""N2 RC soak stability (CP-0032 / P30).

Deterministic N-iteration soak of N=2 install smoke on node-a / node-b.
Records step latencies (p50/p99); fails on any iteration failure or high variance.
"""

from __future__ import annotations

import json
import statistics
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

from .bundle_n2 import build_n2_bundle, verify_n2_bundle
from .manifest_n2 import FREEZE_CHANNEL_N2
from .n2_install import NODE_A, NODE_B, n2_install_dual
from .rc_soak import percentile

__all__ = [
    "N2SoakIteration",
    "N2SoakResult",
    "DEFAULT_ITERATIONS",
    "DEFAULT_VARIANCE_RATIO",
    "run_n2_rc_soak",
]

DEFAULT_ITERATIONS = 5
DEFAULT_VARIANCE_RATIO = 100.0


@dataclass
class N2SoakIteration:
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
class N2SoakResult:
    ok: bool = True
    errors: list[str] = field(default_factory=list)
    iterations: list[N2SoakIteration] = field(default_factory=list)
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
    schema: str | None = None
    dual_primary: int = 0
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
            "schema": self.schema,
            "dual_primary": self.dual_primary,
            "report_path": self.report_path,
        }

    def to_json(self, *, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, sort_keys=True) + "\n"


def _time_step(name: str, steps: dict[str, float], fn: Callable[[], Any]) -> Any:
    t0 = time.perf_counter()
    try:
        return fn()
    finally:
        steps[name] = (time.perf_counter() - t0) * 1000.0


def run_n2_rc_soak(
    root: Path | str | None = None,
    *,
    bundle: Path | str | None = None,
    prefix: Path | str | None = None,
    n: int = DEFAULT_ITERATIONS,
    out_dir: Path | str | None = None,
    report_path: Path | str | None = None,
    variance_bound: float = DEFAULT_VARIANCE_RATIO,
    reuse_prefix: bool = True,
    tip: str | None = None,
    ver: str | None = None,
    expect_freeze_channel: str | None = FREEZE_CHANNEL_N2,
    force_fail_step: str | None = None,
    step_hooks: dict[str, Callable[[], None]] | None = None,
) -> N2SoakResult:
    """Run N iterations of N2 verify + dual-node install smoke; emit JSON report."""
    result = N2SoakResult(n=max(1, int(n)), variance_bound=float(variance_bound))
    root_p = Path(root).resolve() if root else None
    out = Path(out_dir) if out_dir else (
        (root_p / "dist" / "n2_soak") if root_p else Path("dist/n2_soak")
    )
    out.mkdir(parents=True, exist_ok=True)

    bundle_path: Path | None = Path(bundle).resolve() if bundle else None
    man_path: Path | None = None
    if bundle_path is None:
        if root_p is None:
            result.fail("root or bundle required")
            return result
        m = build_n2_bundle(
            root_p,
            out,
            tip=tip or "n2soak",
            ver=ver,
            freeze=True,
            single_node_for_parity=False,
        )
        bundle_path = out / f"{m.name}-{m.ver}.tar.gz"
        man_path = out / f"{m.name}-{m.ver}.manifest.json"
        result.version = m.ver
        result.schema = m.schema_name
        result.dual_primary = m.dual_primary
        if m.freeze:
            result.freeze_channel = m.freeze.channel

    if not bundle_path.is_file():
        result.fail(f"bundle missing: {bundle_path}")
        return result

    if man_path is None:
        stem = bundle_path.name
        base = stem[: -len(".tar.gz")] if stem.endswith(".tar.gz") else bundle_path.stem
        man_path = bundle_path.with_name(f"{base}.manifest.json")

    vr0 = verify_n2_bundle(
        bundle_path,
        man_path,
        smoke=False,
        expected_ver=ver,
        expect_freeze_channel=expect_freeze_channel,
    )
    if not vr0.ok:
        result.fail("initial verify_n2_bundle failed: " + "; ".join(vr0.errors))
        return result
    if vr0.manifest is not None:
        result.version = result.version or vr0.manifest.ver
        result.schema = result.schema or vr0.manifest.schema_name
        result.dual_primary = vr0.manifest.dual_primary
        if vr0.manifest.freeze:
            result.freeze_channel = vr0.manifest.freeze.channel

    pfx = Path(prefix) if prefix else (out / "prefix")
    pfx.mkdir(parents=True, exist_ok=True)
    result.prefix = str(pfx)

    hooks = step_hooks or {}

    for i in range(result.n):
        it = N2SoakIteration(index=i, ok=True)
        steps: dict[str, float] = {}
        t_iter = time.perf_counter()
        try:
            def _verify() -> None:
                if force_fail_step == "verify":
                    raise RuntimeError("forced fail: verify")
                if "verify" in hooks:
                    hooks["verify"]()
                    return
                vr = verify_n2_bundle(
                    bundle_path,
                    man_path,
                    smoke=False,
                    expect_freeze_channel=expect_freeze_channel,
                )
                if not vr.ok:
                    raise RuntimeError("verify_n2_bundle: " + "; ".join(vr.errors))

            _time_step("verify", steps, _verify)

            def _install() -> None:
                if force_fail_step == "install":
                    raise RuntimeError("forced fail: install")
                if "install" in hooks:
                    hooks["install"]()
                    return
                marker_a = pfx / NODE_A / "INSTALL_N2.json"
                marker_b = pfx / NODE_B / "INSTALL_N2.json"
                clear = not (reuse_prefix and i > 0 and marker_a.is_file() and marker_b.is_file())
                ir = n2_install_dual(
                    bundle_path,
                    pfx,
                    manifest_path=man_path,
                    run_replica_mock=True,
                    clear_prefixes=clear or i == 0,
                )
                if not ir.ok:
                    raise RuntimeError("n2_install_dual: " + "; ".join(ir.errors))
                if ir.dual_primary != 0:
                    raise RuntimeError(f"dual_primary must be 0, got {ir.dual_primary}")
                result.version = ir.version or result.version
                result.schema = ir.schema or result.schema
                result.dual_primary = (
                    ir.dual_primary if ir.dual_primary is not None else 0
                )

            _time_step("install", steps, _install)

            def _markers() -> None:
                if force_fail_step == "markers":
                    raise RuntimeError("forced fail: markers")
                if "markers" in hooks:
                    hooks["markers"]()
                    return
                for node in (NODE_A, NODE_B):
                    marker = pfx / node / "INSTALL_N2.json"
                    if not marker.is_file():
                        raise RuntimeError(f"missing INSTALL_N2.json under {node}")

            _time_step("markers", steps, _markers)

        except Exception as exc:  # noqa: BLE001
            it.ok = False
            it.errors.append(str(exc))
            result.fail(f"iteration[{i}]: {exc}")

        it.steps_ms = steps
        it.total_ms = (time.perf_counter() - t_iter) * 1000.0
        result.iterations.append(it)
        if it.ok:
            result.pass_count += 1
        else:
            result.fail_count += 1

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

    rp = Path(report_path) if report_path else (out / "n2_rc_soak_report.json")
    rp.parent.mkdir(parents=True, exist_ok=True)
    rp.write_text(result.to_json(), encoding="utf-8")
    result.report_path = str(rp)
    return result
