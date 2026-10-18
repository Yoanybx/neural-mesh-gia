"""CP-0088 P0.4 — AgentMemory on C-RAM: (tenant_id, agent_id) chains, day-bucket index, kill -9, isolation, tamper.

Also: scorer wiring (long-horizon drift, recurrence, decline only with memory). Parity path (no memory) is covered by
tests/test_minogan_scorer_parity_cp0088.py and must stay byte-identical.
"""

from __future__ import annotations

import copy
import json
import os
import signal
import subprocess
import sys
import textwrap
import time
from pathlib import Path

import pytest

from neural_mesh.cram.store import CRAMStore
from neural_mesh.minogan import parse_scorer_input
from neural_mesh.minogan.memory import (
    DAY_MS,
    AgentMemory,
    MemoryContentError,
    MemoryCorrupt,
    MemoryOrderError,
    MemoryTenantError,
)
from neural_mesh.minogan.scorer import score, score_bytes

pytestmark = pytest.mark.minogan_cp0088

REPO = Path(__file__).resolve().parents[1]
FX = json.loads((REPO / "tests/fixtures/minogan/scorer_v1_fixtures.json").read_text(encoding="utf-8"))["fixtures"]
T0 = 1_790_856_000_000  # 2026-10-01T12:00:00Z
T, A = "org_a", "agent-1"


def _rec(ts: int, score_: int = 30, signals: list | None = None) -> dict:
    return {"kind": "score", "ts": ts, "score": score_, "signals": signals or []}


def _sig(sid: str, ts: int, rule="pii_outbound", typ="data exfil pattern", sev="high") -> dict:
    return {"id": sid, "type": typ, "rule": rule, "severity": sev, "ts": ts, "pattern": "tool=send_reply", "trace_ids": ["t" + sid]}


def _bucket(mem: AgentMemory, tenant: str, agent: str, ts: int) -> Path:
    from neural_mesh.minogan.memory import _day

    return mem._agent_dir(tenant, agent) / "days" / f"{_day(ts)}.jsonl"


# ------------------------------------------------------------------ basics


def test_append_history_head_and_chain(tmp_path):
    m = AgentMemory(tmp_path)
    recs = [m.append(T, A, _rec(T0 + i * 3_600_000, 10 + i)) for i in range(30)]  # spans 2 days
    assert [r["seq"] for r in recs] == list(range(1, 31))
    assert recs[0]["prev_hash"] == "0" * 64 and all(recs[i]["prev_hash"] == recs[i - 1]["hash"] for i in range(1, 30))
    h = m.history(T, A, T0, T0 + 5 * 3_600_000)
    assert [r["seq"] for r in h] == [1, 2, 3, 4, 5, 6]
    assert m.head(T, A)["seq"] == 30
    assert m.verify_chain(T, A) == {"ok": True, "n": 30, "head_seq": 30, "head_hash": recs[-1]["hash"]}
    b = m.baseline(T, A, T0, T0 + 9 * 3_600_000)
    assert b["n"] == 10 and b["mean_score"] == 14.5 and b["min_score"] == 10 and b["max_score"] == 19


def test_records_use_cram_memory_objects(tmp_path):
    m = AgentMemory(tmp_path)
    m.append(T, A, _rec(T0))
    line = json.loads(_bucket(m, T, A, T0).read_text().splitlines()[0])
    obj = json.loads(Path(str(m.cram._object_path(line["key"])) + ".object.json").read_text())
    assert obj["object_type"] == "MEMORY" and m.cram.verify(line["key"])


def test_content_keys_refused_and_order_enforced(tmp_path):
    m = AgentMemory(tmp_path)
    with pytest.raises(MemoryContentError):
        m.append(T, A, {**_rec(T0), "prompt": "never"})
    with pytest.raises(MemoryContentError):
        m.append(T, A, _rec(T0, signals=[{"id": "x", "completion": "never"}]))
    m.append(T, A, _rec(T0 + 10))
    with pytest.raises(MemoryOrderError):
        m.append(T, A, _rec(T0))


def test_recurrence_distinct_days_dedup_by_signal_id(tmp_path):
    m = AgentMemory(tmp_path)
    s1, s2 = _sig("s1", T0 - 20 * DAY_MS), _sig("s2", T0 - 10 * DAY_MS)
    m.append(T, A, _rec(T0 - 20 * DAY_MS, signals=[s1]))
    m.append(T, A, _rec(T0 - 19 * DAY_MS, signals=[s1]))  # same signal re-seen next day: counted once
    m.append(T, A, _rec(T0 - 10 * DAY_MS, signals=[s2]))
    r = m.recurrence(T, A, "pii_outbound", 30, T0)
    assert (r["occurrences"], r["distinct_days"]) == (2, 2)
    assert m.recurrence(T, A, "pii_outbound", 15, T0)["distinct_days"] == 1
    assert m.recurrence(T, A, "tool_loop", 30, T0)["occurrences"] == 0


# ------------------------------------------------------------------ bounded reads (no full scan)


def test_90_day_history_reads_only_its_buckets(tmp_path, monkeypatch):
    m = AgentMemory(tmp_path)
    start = T0 - 300 * DAY_MS
    for d in range(301):  # 301 days of history, one record per day
        m.append(T, A, _rec(start + d * DAY_MS, d % 100))
    m.append(T, "other-agent", _rec(T0))
    m2 = AgentMemory(tmp_path)  # fresh process view

    def _no_scan(*_a, **_k):
        raise AssertionError("full scan attempted")

    monkeypatch.setattr(CRAMStore, "list_keys", _no_scan)
    monkeypatch.setattr(CRAMStore, "fsck", _no_scan)
    h = m2.history(T, A, T0 - 90 * DAY_MS, T0)
    assert len(h) == 91
    assert m2.stats["bucket_reads"] <= 91 and m2.stats["record_reads"] == 91 and m2.stats["lines_read"] == 91
    # a window entirely before the agent's first day costs zero bucket reads
    before = m2.stats["bucket_reads"]
    assert m2.history(T, A, start - 400 * DAY_MS, start - DAY_MS) == []
    assert m2.stats["bucket_reads"] == before


# ------------------------------------------------------------------ kill -9

_CHILD = textwrap.dedent(
    """
    import os, sys
    from neural_mesh.minogan.memory import AgentMemory
    root, mode = sys.argv[1], sys.argv[2]
    m = AgentMemory(root)
    T0 = 1_790_856_000_000
    if mode == "loop":
        i = m.head("org_a", "agent-1")["seq"]
        while True:
            i += 1
            m.append("org_a", "agent-1", {"kind": "score", "ts": T0 + i * 600_000, "score": i % 100, "signals": []})
            print(i, flush=True)
    else:  # crash at a protocol step on the 4th append
        for i in range(1, 4):
            m.append("org_a", "agent-1", {"kind": "score", "ts": T0 + i, "score": i, "signals": []})
        os.environ["MESH_MINOGAN_MEMORY_CRASH_AT"] = mode
        m.append("org_a", "agent-1", {"kind": "score", "ts": T0 + 4, "score": 4, "signals": []})
        print("NOT KILLED", flush=True)
    """
)


def _child(root: Path, mode: str, **kw) -> subprocess.Popen:
    env = {k: v for k, v in os.environ.items() if k != "MESH_MINOGAN_MEMORY_CRASH_AT"}
    return subprocess.Popen([sys.executable, "-c", _CHILD, str(root), mode], stdout=subprocess.PIPE, text=True, env=env, **kw)


def test_survives_real_sigkill_mid_stream(tmp_path):
    p = _child(tmp_path, "loop")
    acked = 0
    deadline = time.monotonic() + 60
    while acked < 40 and time.monotonic() < deadline:
        line = p.stdout.readline()
        if line.strip().isdigit():
            acked = int(line)
    os.kill(p.pid, signal.SIGKILL)
    p.wait(timeout=30)
    assert p.returncode == -signal.SIGKILL and acked >= 40
    m = AgentMemory(tmp_path)  # reopen → recovery
    v = m.verify_chain(T, A)
    assert v["ok"], v
    assert v["n"] >= acked  # every acknowledged append is durable (one in-flight may also have landed)
    m.append(T, A, _rec(T0 + (v["n"] + 1) * 600_000))
    assert m.verify_chain(T, A)["n"] == v["n"] + 1


@pytest.mark.parametrize("point,expected_n", [("after_cas", 3), ("after_pending", 4), ("after_bucket", 4)])
def test_sigkill_at_each_protocol_step(tmp_path, point, expected_n):
    p = _child(tmp_path, point)
    out, _ = p.communicate(timeout=60)
    assert p.returncode == -signal.SIGKILL and "NOT KILLED" not in out
    m = AgentMemory(tmp_path)
    v = m.verify_chain(T, A)
    assert v["ok"] and v["n"] == expected_n, v
    assert m.head(T, A)["pending"] is None
    m.append(T, A, _rec(T0 + 10))
    assert m.verify_chain(T, A)["n"] == expected_n + 1


def test_torn_bucket_tail_is_truncated_on_open(tmp_path):
    m = AgentMemory(tmp_path)
    m.append(T, A, _rec(T0))
    m.append(T, A, _rec(T0 + 1))
    with _bucket(m, T, A, T0).open("ab") as f:
        f.write(b'{"seq":3,"ts":')  # torn write without pending (cannot be a committed record)
    m2 = AgentMemory(tmp_path)
    assert len(m2.history(T, A, T0, T0 + 10)) == 2
    m2.append(T, A, _rec(T0 + 2))
    assert m2.verify_chain(T, A)["n"] == 3


# ------------------------------------------------------------------ tenant isolation


def test_no_cross_tenant_leak(tmp_path):
    m = AgentMemory(tmp_path)
    for i in range(5):
        m.append("org_a", A, _rec(T0 + i, 90, [_sig(f"a{i}", T0 + i)]))
    assert m.history("org_b", A, 0, T0 + DAY_MS) == []
    assert m.recurrence("org_b", A, "pii_outbound", 30, T0 + DAY_MS)["occurrences"] == 0
    assert m.head("org_b", A)["seq"] == 0
    # hostile ids stay inside the memory dir and stay isolated
    m.append("../../org_a", A, _rec(T0))
    assert m._agent_dir("../../org_a", A).resolve().is_relative_to((tmp_path / "minogan_memory").resolve())
    assert len(m.history("org_a", A, 0, T0 + DAY_MS)) == 5


def test_forged_index_pointing_at_other_tenant_is_refused(tmp_path):
    m = AgentMemory(tmp_path)
    m.append("org_a", A, _rec(T0, 99))
    m.append("org_b", A, _rec(T0, 1))
    a_line = _bucket(m, "org_a", A, T0).read_text()
    _bucket(m, "org_b", A, T0).write_text(a_line)  # attacker swaps org_b's index to org_a's record
    with pytest.raises(MemoryTenantError):
        AgentMemory(tmp_path).history("org_b", A, 0, T0 + 1)
    assert AgentMemory(tmp_path).verify_chain("org_b", A)["ok"] is False


def test_scorer_memory_is_tenant_scoped(tmp_path):
    f = next(x for x in FX if x["input"]["signals"])
    inp = copy.deepcopy(f["input"])
    m = AgentMemory(tmp_path)
    m.append("org_other", inp["agent"]["id"], _rec(inp["now"] - 40 * DAY_MS, 5, [_sig("zz", inp["now"] - 20 * DAY_MS, rule=inp["signals"][0]["rule"])]))
    out = score(inp, memory=m)
    assert out["components"]["drift_long"]["n"] == 0
    assert all(r["occurrences"] == sum(1 for s in inp["signals"] if s["rule"] == r["rule"]) for r in out["components"]["recurrence"])


# ------------------------------------------------------------------ tamper detection


def test_tamper_cas_bytes_detected(tmp_path):
    m = AgentMemory(tmp_path)
    for i in range(3):
        m.append(T, A, _rec(T0 + i))
    key = json.loads(_bucket(m, T, A, T0).read_text().splitlines()[1])["key"]
    p = m.cram._object_path(key)
    p.write_bytes(p.read_bytes().replace(b'"score":30', b'"score":31'))
    assert AgentMemory(tmp_path).verify_chain(T, A)["ok"] is False
    with pytest.raises(MemoryCorrupt):
        AgentMemory(tmp_path).history(T, A, T0, T0 + 5)


def test_tamper_rehashed_record_breaks_chain(tmp_path):
    from neural_mesh.cram.models import ObjectType
    from neural_mesh.minogan.canonical import canonical_json
    from neural_mesh.minogan.memory import record_hash

    m = AgentMemory(tmp_path)
    for i in range(3):
        m.append(T, A, _rec(T0 + i))
    b = _bucket(m, T, A, T0)
    lines = [json.loads(x) for x in b.read_text().splitlines()]
    rec = json.loads(m.cram.get(lines[1]["key"]))
    rec["score"] = 0  # forge a "nicer" history and re-hash it consistently
    rec["hash"] = record_hash(rec)
    lines[1]["key"] = m.cram.put_object(canonical_json(rec), ObjectType.MEMORY).content_hash
    lines[1]["hash"] = rec["hash"]
    b.write_text("".join(json.dumps(x) + "\n" for x in lines))
    v = AgentMemory(tmp_path).verify_chain(T, A)
    assert v["ok"] is False and "chain break" in v["error"]


def test_tamper_deleted_line_and_head_detected(tmp_path):
    m = AgentMemory(tmp_path)
    for i in range(3):
        m.append(T, A, _rec(T0 + i))
    b = _bucket(m, T, A, T0)
    lines = b.read_text().splitlines(keepends=True)
    b.write_text(lines[0] + lines[2])
    assert AgentMemory(tmp_path).verify_chain(T, A)["ok"] is False
    b.write_text("".join(lines))
    hp = m._agent_dir(T, A) / "head.json"
    head = json.loads(hp.read_text())
    hp.write_text(json.dumps({**head, "hash": "f" * 64}))
    assert AgentMemory(tmp_path).verify_chain(T, A)["ok"] is False


# ------------------------------------------------------------------ scorer wiring


def test_no_memory_output_unchanged():
    for f in FX[::7]:
        assert score_bytes(f["input"]) == score_bytes(f["input"], None)
        assert "drift_long" not in score(f["input"])["components"]


def test_memory_never_changes_the_number_and_replays_identically(tmp_path):
    m = AgentMemory(tmp_path)
    world = [f for f in FX if f["world"] == 101 and "variant" not in f["step"]]
    for f in world:
        base = score(f["input"])
        with_mem = score(f["input"], memory=m)
        for k in ("score", "exposure", "behavior", "driftPct", "driftStatus", "axes", "cited_trace_ids"):
            assert with_mem[k] == base[k]
        before = score_bytes(f["input"], m)
        m.append_score(parse_scorer_input(f["input"]), with_mem)
        assert score_bytes(f["input"], m) == before  # appending its own record does not change the replay
    assert m.verify_chain(world[0]["input"]["org_id"], world[0]["input"]["agent"]["id"])["n"] == len(world)


def _hot_input() -> dict:
    f = next(x for x in FX if x["expected"]["score"] >= 85 and any(s["type"] == "data exfil pattern" and s["severity"] == "high" for s in x["input"]["signals"]))
    inp = copy.deepcopy(f["input"])
    inp["features"].update(baselineSpans=200, recentSpans=50, hasBaseline=True)  # confidence 1.0; not a score input
    return inp


def test_long_horizon_drift(tmp_path):
    inp = _hot_input()
    m = AgentMemory(tmp_path)
    for d in (60, 45, 30):
        m.append(inp["org_id"], inp["agent"]["id"], _rec(inp["now"] - d * DAY_MS, 20))
    c = score(inp, memory=m)["components"]
    assert c["drift_long"]["n"] == 3 and c["drift_long"]["baseline_mean"] == 20 and c["drift_long"]["status"] == "critical"
    assert score(inp, memory=m)["driftPct"] == score(inp)["driftPct"]


def test_decline_only_with_memory_recurrence(tmp_path):
    inp = _hot_input()
    rule = next(s["rule"] for s in inp["signals"] if s["type"] == "data exfil pattern" and s["severity"] == "high")
    assert score(inp)["components"]["uw"]["outcome"] == "refer"
    m = AgentMemory(tmp_path)
    t, a, now = inp["org_id"], inp["agent"]["id"], inp["now"]
    assert score(inp, memory=m)["components"]["uw"]["outcome"] == "refer"  # empty memory: no recurrence
    m.append(t, a, _rec(now - 20 * DAY_MS, 60, [_sig("old1", now - 20 * DAY_MS, rule=rule)]))
    m.append(t, a, _rec(now - 12 * DAY_MS, 60, [_sig("old2", now - 12 * DAY_MS, rule=rule)]))
    out = score(inp, memory=m)
    assert out["components"]["uw"]["outcome"] == "decline"
    assert out["components"]["decline_basis"]["recurrence"][0]["high_distinct_days"] >= 2
    assert out["score"] == score(inp)["score"]
    low = copy.deepcopy(inp)
    low["features"].update(baselineSpans=0, recentSpans=0, hasBaseline=False)  # confidence 0 → no decline
    assert score(low, memory=m)["components"]["uw"]["outcome"] == "refer"
    m2 = AgentMemory(tmp_path / "older")
    m2.append(t, a, _rec(now - 60 * DAY_MS, 60, [_sig("o1", now - 60 * DAY_MS, rule=rule)]))
    m2.append(t, a, _rec(now - 50 * DAY_MS, 60, [_sig("o2", now - 50 * DAY_MS, rule=rule)]))
    assert score(inp, memory=m2)["components"]["uw"]["outcome"] == "refer"  # outside the 30-day recurrence window
