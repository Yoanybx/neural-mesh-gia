"""Cycle 10 — Cognitive Router R1 Capability-aware."""

from __future__ import annotations

import time
from pathlib import Path

import pytest

from neural_mesh.router import (
    CAPABILITY_SCHEMA_VERSION,
    CapabilityAwareStrategy,
    CapabilityNoMatch,
    CapabilityRegistry,
    CognitiveRouterR0,
    DecisionStatus,
    DecisionStore,
    NodeCapability,
    RoundRobinStrategy,
    RouteCandidate,
    TaskSpec,
    UnknownCapabilitySchema,
    cap_state_fingerprint,
    explain_decision,
    policy_hash,
    replay_from_store,
    score_node,
    validate_capability,
)
from neural_mesh.router.capabilities import DEFAULT_CAP_TTL_MS, T_CONV_CAPABILITY_S
from neural_mesh.router.metrics import percentile, summarize_decisions
from neural_mesh.router.scoring import pick_best


def _now() -> int:
    return int(time.time() * 1000)


def _cap(
    node_id: str,
    *,
    cpu: int = 4,
    memory: int = 8192,
    tasks: tuple[str, ...] = ("compute",),
    accel: tuple[str, ...] = (),
    health: float = 1.0,
    ttl_ms: int = DEFAULT_CAP_TTL_MS,
    advertised_at_ms: int | None = None,
) -> NodeCapability:
    return NodeCapability(
        node_id=node_id,
        cpu=cpu,
        memory=memory,
        accelerators=accel,
        supported_tasks=tasks,
        health=health,
        advertised_at_ms=_now() if advertised_at_ms is None else advertised_at_ms,
        ttl_ms=ttl_ms,
    )


def _cands(*specs: tuple) -> list[RouteCandidate]:
    out = []
    for s in specs:
        if len(s) == 2:
            nid, caps = s
            out.append(RouteCandidate(node_id=nid, capabilities=tuple(caps), cpu=4, memory=4096))
        else:
            nid, caps, cpu, mem = s
            out.append(
                RouteCandidate(
                    node_id=nid, capabilities=tuple(caps), cpu=cpu, memory=mem
                )
            )
    return out


def test_capability_model_validation():
    cap = validate_capability(
        {
            "node_id": "n1",
            "cpu": 8,
            "memory": 16384,
            "accelerators": ["gpu"],
            "supported_tasks": ["compute", "gpu"],
            "health": 0.9,
            "advertised_at_ms": 1,
            "ttl_ms": 1000,
            "schema_version": CAPABILITY_SCHEMA_VERSION,
        }
    )
    assert cap.node_id == "n1"
    assert cap.accelerators == ("gpu",)
    with pytest.raises(UnknownCapabilitySchema):
        validate_capability({"node_id": "x", "schema_version": 99})


def test_capability_registry_persisted_cram(tmp_path: Path):
    reg = CapabilityRegistry(tmp_path / "caps")
    cap = _cap("node-01", tasks=("compute", "gpu"), accel=("gpu",))
    ack = reg.upsert(cap, op_id="op-cap-1", epoch=10, trace_id="tr-cap-1")
    assert ack
    assert reg.has_op_id("op-cap-1")
    # Idempotent
    ack2 = reg.upsert(cap, op_id="op-cap-1", epoch=10, trace_id="tr-cap-1")
    assert ack2 == ack
    # Reload
    reg2 = CapabilityRegistry(tmp_path / "caps")
    got = reg2.get("node-01")
    assert got is not None
    assert got.to_dict() == cap.to_dict()
    assert reg2.fingerprint() == cap_state_fingerprint([cap])


def test_capability_selects_best_fit():
    reg = CapabilityRegistry()
    reg.upsert(_cap("a", cpu=2, memory=2048, tasks=("compute",)), op_id="a")
    reg.upsert(
        _cap("b", cpu=16, memory=65536, tasks=("compute", "gpu"), accel=("gpu",)),
        op_id="b",
    )
    cands = _cands(("a", ("compute",), 2, 2048), ("b", ("compute", "gpu"), 16, 65536))
    strat = CapabilityAwareStrategy(reg)
    task = TaskSpec(
        task_id="gpu-job",
        required_capabilities=("gpu",),
        resource_requirements={"cpu": 8, "memory": 16384},
    )
    chosen, idx = strat.select(task, cands)
    assert chosen is not None
    assert chosen.node_id == "b"
    assert strat.last_score is not None and strat.last_score > 0
    assert "capability_match" in strat.last_factors or "gpu_match" in strat.last_factors


def test_capability_deterministic():
    reg = CapabilityRegistry()
    for nid, cpu in (("a", 4), ("b", 8), ("c", 2)):
        reg.upsert(_cap(nid, cpu=cpu, tasks=("compute",)), op_id=f"op-{nid}")
    cands = _cands(("a", ("compute",)), ("b", ("compute",)), ("c", ("compute",)))
    task = TaskSpec(task_id="det", required_capabilities=("compute",))
    results = []
    for _ in range(20):
        strat = CapabilityAwareStrategy(reg)
        chosen, idx = strat.select(task, cands)
        results.append((chosen.node_id if chosen else None, idx, strat.last_score))
    assert len(set(results)) == 1


def test_missing_capability_rejected():
    reg = CapabilityRegistry()
    reg.upsert(_cap("a", tasks=("compute",)), op_id="a")
    cands = _cands(("a", ("compute",)))
    router = CognitiveRouterR0(
        cands,
        seed=0,
        strategy=CapabilityAwareStrategy(reg),
        capability_registry=reg,
    )
    d = router.route(
        TaskSpec(task_id="q", required_capabilities=("quantum",), op_id="op-q")
    )
    assert d.status == DecisionStatus.REJECTED
    # Either R0 filter NO_CAPABLE_NODE (candidate lacks quantum) or R1 no-match
    assert d.reason in ("NO_CAPABLE_NODE", "CAPABILITY_NO_MATCH")
    assert d.selected_node_id is None


def test_capability_no_match_never_silent_rr():
    """Registry empty / no fit ⇒ CAPABILITY_NO_MATCH, not Round-Robin."""
    reg = CapabilityRegistry()
    # Candidate advertises compute at RouteCandidate level, but registry empty
    # and we still pass R0 filter — strategy must not silently RR.
    cands = _cands(("a", ("compute",)), ("b", ("compute",)))
    # Seed registry with unrelated task types so R0 eligible but R1 no-match
    # Actually R0 filters by RouteCandidate.capabilities. Seed registry with
    # caps that don't include required 'ml'.
    reg.upsert(_cap("a", tasks=("compute",)), op_id="a")
    reg.upsert(_cap("b", tasks=("compute",)), op_id="b")
    # Make candidates also claim "ml" so R0 filter passes, then R1 scores fail.
    cands_ml = [
        RouteCandidate(node_id="a", capabilities=("compute", "ml"), cpu=4, memory=4096),
        RouteCandidate(node_id="b", capabilities=("compute", "ml"), cpu=4, memory=4096),
    ]
    router = CognitiveRouterR0(
        cands_ml,
        seed=0,
        strategy=CapabilityAwareStrategy(reg),
        capability_registry=reg,
    )
    d = router.route(
        TaskSpec(task_id="ml", required_capabilities=("ml",), op_id="op-ml")
    )
    assert d.status == DecisionStatus.REJECTED
    assert d.reason == "CAPABILITY_NO_MATCH"
    assert d.selected_node_id is None
    assert d.metrics.get("strategy") == "CAPABILITY_AWARE"


def test_rr_compatibility():
    cands = _cands(("a", ("compute",)), ("b", ("compute",)))
    r_rr = CognitiveRouterR0(cands, seed=0, strategy=RoundRobinStrategy(index=0))
    d1 = r_rr.route(TaskSpec(task_id="r1", op_id="op-r1"))
    d2 = r_rr.route(TaskSpec(task_id="r2", op_id="op-r2"))
    assert d1.status == DecisionStatus.ACCEPTED
    assert d2.status == DecisionStatus.ACCEPTED
    assert d1.reason == "ROUND_ROBIN"
    assert d1.selected_node_id != d2.selected_node_id  # RR advances


def test_explain_contains_factors():
    reg = CapabilityRegistry()
    reg.upsert(
        _cap("gpu-node", cpu=16, memory=32768, tasks=("compute", "gpu"), accel=("gpu",)),
        op_id="g",
    )
    reg.upsert(_cap("cpu-node", cpu=2, memory=2048, tasks=("compute",)), op_id="c")
    cands = _cands(
        ("cpu-node", ("compute",), 2, 2048),
        ("gpu-node", ("compute", "gpu"), 16, 32768),
    )
    router = CognitiveRouterR0(
        cands,
        seed=0,
        strategy=CapabilityAwareStrategy(reg),
        capability_registry=reg,
    )
    d = router.route(
        TaskSpec(
            task_id="ex",
            required_capabilities=("gpu",),
            resource_requirements={"cpu": 8, "memory": 8192},
            op_id="op-ex",
        )
    )
    exp = explain_decision(d)
    assert exp["strategy"] == "CAPABILITY_AWARE"
    assert exp["strategy_alias"] == "capability"
    assert exp["selected"] == "gpu-node"
    assert exp["score"] is not None and exp["score"] > 0
    assert isinstance(exp["factors"], list) and len(exp["factors"]) >= 1
    assert exp["cap_state_fp"]


def test_policy_hash_changes_on_strategy_change():
    policy = {
        "policy_schema_version": 1,
        "allow_network_actions": False,
        "allow_physical_actions": False,
        "require_human_approval": True,
    }
    cands = _cands(("a", ("compute",)))
    reg = CapabilityRegistry()
    reg.upsert(_cap("a"), op_id="a")
    rr = CognitiveRouterR0(cands, seed=0, policy=policy, strategy=RoundRobinStrategy(index=0))
    cap = CognitiveRouterR0(
        cands,
        seed=0,
        policy=policy,
        strategy=CapabilityAwareStrategy(reg),
        capability_registry=reg,
    )
    assert rr.policy_hash == policy_hash(policy)
    assert cap.policy_hash != rr.policy_hash
    assert cap.policy_hash == policy_hash({**policy, "routing_strategy": "capability"})


def test_stale_capabilities_rejected():
    fixed_now = [1_000_000]

    def now_fn():
        return fixed_now[0]

    reg = CapabilityRegistry(now_fn=now_fn)
    # Advertised long ago relative to TTL
    stale = _cap(
        "stale-node",
        tasks=("compute", "gpu"),
        accel=("gpu",),
        ttl_ms=100,
        advertised_at_ms=fixed_now[0] - 10_000,
    )
    fresh = _cap(
        "fresh-node",
        tasks=("compute",),
        ttl_ms=5000,
        advertised_at_ms=fixed_now[0],
    )
    reg.upsert(stale, op_id="s")
    reg.upsert(fresh, op_id="f")
    assert reg.list_stale(fixed_now[0])[0].node_id == "stale-node"
    cands = _cands(
        ("stale-node", ("compute", "gpu")),
        ("fresh-node", ("compute",)),
    )
    strat = CapabilityAwareStrategy(reg, now_fn=now_fn)
    # GPU task: only stale had gpu → no-match (0 routes to expired)
    chosen, _ = strat.select(
        TaskSpec(task_id="g", required_capabilities=("gpu",)), cands
    )
    assert chosen is None
    router = CognitiveRouterR0(
        cands,
        seed=0,
        strategy=CapabilityAwareStrategy(reg, now_fn=now_fn),
        capability_registry=reg,
    )
    d = router.route(
        TaskSpec(task_id="g2", required_capabilities=("gpu",), op_id="op-stale")
    )
    assert d.status == DecisionStatus.REJECTED
    assert d.selected_node_id is None


def test_zero_routes_to_expired_caps_batch():
    fixed_now = [5_000_000]

    def now_fn():
        return fixed_now[0]

    reg = CapabilityRegistry(now_fn=now_fn)
    for i in range(5):
        reg.upsert(
            _cap(
                f"n{i}",
                tasks=("compute", "gpu"),
                accel=("gpu",),
                ttl_ms=50,
                advertised_at_ms=fixed_now[0] - 10_000,
            ),
            op_id=f"op-{i}",
        )
    cands = _cands(*[(f"n{i}", ("compute", "gpu")) for i in range(5)])
    router = CognitiveRouterR0(
        cands,
        seed=0,
        strategy=CapabilityAwareStrategy(reg, now_fn=now_fn),
        capability_registry=reg,
    )
    routed_to_expired = 0
    for i in range(50):
        d = router.route(
            TaskSpec(
                task_id=f"t{i}",
                required_capabilities=("gpu",),
                op_id=f"op-t{i}",
            )
        )
        if d.selected_node_id is not None:
            routed_to_expired += 1
    assert routed_to_expired == 0


def test_cap_state_fp_in_decision_and_determinism_1000():
    reg = CapabilityRegistry()
    reg.upsert(_cap("a", cpu=4), op_id="a")
    reg.upsert(_cap("b", cpu=8), op_id="b")
    cands = _cands(("a", ("compute",)), ("b", ("compute",)))
    fp = reg.fingerprint()
    bytes_set = set()
    for i in range(1000):
        # Fresh router each time with same inputs (no store; no RR cursor drift
        # for capability — capability strategy has no advancing cursor).
        r = CognitiveRouterR0(
            cands,
            seed=7,
            strategy=CapabilityAwareStrategy(reg),
            capability_registry=reg,
        )
        d = r.route(TaskSpec(task_id="same", op_id=f"unique-{i}"))  # unique to avoid idempotency
        # Actually for determinism of selection we compare selected + score factors
        # Canonical form includes op_id so use fixed op_id without store:
        break
    # Proper 1000× with fixed op_id, no store
    ref = None
    for _ in range(1000):
        r = CognitiveRouterR0(
            cands,
            seed=7,
            strategy=CapabilityAwareStrategy(reg),
            capability_registry=reg,
        )
        d = r.route(TaskSpec(task_id="same", op_id="op-fixed"))
        assert d.cap_state_fp == fp
        cb = d.canonical_bytes()
        if ref is None:
            ref = cb
        else:
            assert cb == ref
        bytes_set.add(cb)
    assert len(bytes_set) == 1


def test_r0_fail_closed_persist_ack_preserved(tmp_path: Path):
    from neural_mesh.router import CramPersistError

    store = DecisionStore(tmp_path / "dec")
    store.mark_unavailable()
    reg = CapabilityRegistry(tmp_path / "caps")
    reg.upsert(_cap("a"), op_id="seed-a")
    router = CognitiveRouterR0(
        _cands(("a", ("compute",))),
        seed=0,
        decision_store=store,
        strategy=CapabilityAwareStrategy(reg),
        capability_registry=reg,
    )
    with pytest.raises(CramPersistError):
        router.route(TaskSpec(task_id="x", op_id="op-x"))


def test_capability_replay_byte_identical(tmp_path: Path):
    store = DecisionStore(tmp_path / "dec")
    reg = CapabilityRegistry(tmp_path / "caps")
    reg.upsert(_cap("a", cpu=4), op_id="seed-a")
    reg.upsert(_cap("b", cpu=16, tasks=("compute", "gpu"), accel=("gpu",)), op_id="seed-b")
    cands = _cands(("a", ("compute",)), ("b", ("compute", "gpu")))
    router = CognitiveRouterR0(
        cands,
        seed=0,
        decision_store=store,
        strategy=CapabilityAwareStrategy(reg),
        capability_registry=reg,
        epoch=10,
    )
    d = router.route(
        TaskSpec(
            task_id="rep",
            required_capabilities=("gpu",),
            op_id="op-rep",
            trace_id="tr-rep",
        )
    )
    assert d.status == DecisionStatus.ACCEPTED
    stored, recomputed = replay_from_store(store, "tr-rep")
    assert stored.canonical_bytes() == recomputed.canonical_bytes()


def test_capability_update_propagation_under_t_conv(tmp_path: Path):
    reg = CapabilityRegistry(tmp_path / "caps")
    t0 = time.perf_counter()
    for i in range(100):
        reg.upsert(
            _cap(f"n{i % 10}", cpu=i + 1, advertised_at_ms=_now()),
            op_id=f"upd-{i}",
            epoch=1,
            trace_id=f"tr-upd-{i}",
        )
    elapsed = time.perf_counter() - t0
    assert elapsed < T_CONV_CAPABILITY_S


def test_routing_p99_under_8ms():
    reg = CapabilityRegistry()
    for nid in ("a", "b", "c", "d"):
        reg.upsert(_cap(nid, cpu=8, tasks=("compute", "gpu"), accel=("gpu",)), op_id=nid)
    cands = _cands(
        ("a", ("compute", "gpu")),
        ("b", ("compute", "gpu")),
        ("c", ("compute",)),
        ("d", ("compute", "gpu")),
    )
    router = CognitiveRouterR0(
        cands,
        seed=0,
        strategy=CapabilityAwareStrategy(reg),
        capability_registry=reg,
    )
    lat = []
    for i in range(300):
        t0 = time.perf_counter()
        router.route(
            TaskSpec(
                task_id=f"p-{i}",
                required_capabilities=("gpu",),
                op_id=f"op-p-{i}",
            )
        )
        lat.append((time.perf_counter() - t0) * 1000.0)
    assert percentile(lat, 99) < 8.0


def test_typed_capability_no_match_error_class():
    err = CapabilityNoMatch(task_id="t1")
    assert err.code == "ROUTER_CAPABILITY_NO_MATCH"


def test_score_components_deterministic():
    cap = _cap("n", cpu=8, memory=16384, tasks=("compute", "gpu"), accel=("gpu",))
    cand = RouteCandidate(node_id="n", capabilities=("compute", "gpu"), cpu=8, memory=16384)
    task = TaskSpec(
        task_id="s",
        required_capabilities=("gpu",),
        resource_requirements={"cpu": 4, "memory": 8192},
    )
    s1, f1, b1 = score_node(task, cand, cap)
    s2, f2, b2 = score_node(task, cand, cap)
    assert s1 == s2 and f1 == f2 and b1 == b2
    assert b1["total"] == s1


def test_capability_schema_version_constant():
    assert CAPABILITY_SCHEMA_VERSION == 1
    assert T_CONV_CAPABILITY_S == 5.0
    assert DEFAULT_CAP_TTL_MS == 5000


def test_pick_best_tie_break_lexicographic():
    cands = [
        RouteCandidate(node_id="b", capabilities=("compute",)),
        RouteCandidate(node_id="a", capabilities=("compute",)),
    ]
    scored = [
        (cands[0], 50.0, ["x"], {"total": 50.0}),
        (cands[1], 50.0, ["x"], {"total": 50.0}),
    ]
    chosen, idx, score, _ = pick_best(scored)
    assert chosen is not None and chosen.node_id == "a"
    assert score == 50.0


def test_cli_strategy_rr_default_unchanged(tmp_path: Path):
    import json
    import subprocess
    import sys

    from neural_mesh.safety import ensure_default_policy

    ensure_default_policy(tmp_path)
    mesh = [sys.executable, "-m", "neural_mesh.cli"]
    r = subprocess.run(
        mesh + ["router", "route", "rr-def", "--seed", "0", "--strategy", "rr", "--json"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
    )
    assert r.returncode == 0, r.stderr
    data = json.loads(r.stdout)
    assert data["strategy"] == "ROUND_ROBIN"
    assert data["strategy_alias"] == "rr"


def test_registry_fail_closed_when_unavailable(tmp_path: Path):
    from neural_mesh.router import CramPersistError

    reg = CapabilityRegistry(tmp_path / "caps")
    reg.mark_unavailable()
    with pytest.raises(CramPersistError):
        reg.upsert(_cap("x"), op_id="op-x", epoch=1, trace_id="tr-x")


def test_health_zero_reduces_score():
    healthy = _cap("h", health=1.0)
    sick = _cap("s", health=0.0)
    cand_h = RouteCandidate(node_id="h", capabilities=("compute",), cpu=4, memory=4096)
    cand_s = RouteCandidate(node_id="s", capabilities=("compute",), cpu=4, memory=4096)
    task = TaskSpec(task_id="t", required_capabilities=("compute",))
    sh, _, _ = score_node(task, cand_h, healthy)
    ss, _, _ = score_node(task, cand_s, sick)
    assert sh > ss


def test_no_silent_rr_when_capability_strategy_configured():
    """Even if RR would have a pick, capability no-match must not fall back."""
    reg = CapabilityRegistry()
    # Only advertise 'storage' — not 'gpu'
    reg.upsert(_cap("a", tasks=("storage",)), op_id="a")
    cands = [
        RouteCandidate(node_id="a", capabilities=("storage", "gpu"), cpu=4, memory=4096)
    ]
    r_cap = CognitiveRouterR0(
        cands,
        seed=0,
        strategy=CapabilityAwareStrategy(reg),
        capability_registry=reg,
    )
    d = r_cap.route(
        TaskSpec(task_id="g", required_capabilities=("gpu",), op_id="op-g")
    )
    assert d.reason == "CAPABILITY_NO_MATCH"
    # RR alone with same candidates would accept (RouteCandidate claims gpu).
    r_rr = CognitiveRouterR0(cands, seed=0, strategy=RoundRobinStrategy(index=0))
    d_rr = r_rr.route(
        TaskSpec(task_id="g2", required_capabilities=("gpu",), op_id="op-g2")
    )
    assert d_rr.status == DecisionStatus.ACCEPTED
