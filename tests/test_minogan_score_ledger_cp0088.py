"""CP-0088 P0.6 — score ledger: per-tenant hash chain, byte-identical replay, whole-chain verify, tamper, kill -9."""

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

from neural_mesh.cram.models import ObjectType
from neural_mesh.minogan import parse_scorer_input
from neural_mesh.minogan.canonical import canonical_json
from neural_mesh.minogan.ledger import (
    LedgerNotFound,
    ScoreLedger,
    entry_hash,
    record_scoring,
)
from neural_mesh.minogan.memory import DAY_MS, GENESIS, AgentMemory, record_hash
from neural_mesh.minogan.scorer import MeshScorer, score

pytestmark = pytest.mark.minogan_cp0088

REPO = Path(__file__).resolve().parents[1]
FX = json.loads((REPO / "tests/fixtures/minogan/scorer_v1_fixtures.json").read_text(encoding="utf-8"))["fixtures"]


def _hot() -> dict:
    f = next(x for x in FX if x["expected"]["score"] >= 85 and any(
        s["type"] == "data exfil pattern" and s["severity"] == "high" for s in x["input"]["signals"]))
    d = copy.deepcopy(f["input"])
    d["features"].update(baselineSpans=200, recentSpans=50, hasBaseline=True)  # confidence 1.0
    return d


def _shift(d: dict, days: int, tag: str) -> dict:
    """Same input ``days`` earlier with distinct signal ids (a genuinely earlier scoring)."""
    x = copy.deepcopy(d)
    dt = days * DAY_MS
    x["now"] -= dt
    x["window"] = {"from": x["window"]["from"] - dt, "to": x["window"]["to"] - dt}
    for s in x["signals"]:
        s["ts"] -= dt
        s["id"] = f"{s['id']}-{tag}"
    for e in x.get("events") or []:
        e["ts"] -= dt
    return x


def _run(root: Path, inputs: list[dict]) -> tuple[AgentMemory, ScoreLedger, list[tuple[dict, dict]]]:
    m, led = AgentMemory(root), ScoreLedger(root)
    res = []
    for d in inputs:
        out, _, e = record_scoring(parse_scorer_input(d), m, led)
        res.append((out, e))
    return m, led, res


def _hot_history() -> list[dict]:
    h = _hot()
    return [_shift(h, 20, "d20"), _shift(h, 12, "d12"), h]


@pytest.fixture
def hot(tmp_path):
    m, led, res = _run(tmp_path, _hot_history())
    assert res[-1][0]["components"]["uw"]["outcome"] == "decline"
    assert res[-1][0]["components"]["drift_long"]["n"] == 2
    return tmp_path, m, led, res


def _fresh(root: Path) -> tuple[AgentMemory, ScoreLedger]:
    return AgentMemory(root), ScoreLedger(root)


def _verify(root: Path, **kw) -> dict:
    m, led = _fresh(root)
    return led.verify(m, **kw)


# ----------------------------------------------------------------------------- replay


def test_replay_all_fixtures_byte_identical(tmp_path):
    inputs = [f["input"] for f in sorted(FX, key=lambda f: f["input"]["now"])]  # stable: per-agent ts order
    _, _, res = _run(tmp_path, inputs)
    assert len(res) == len(FX)
    m2, led2 = _fresh(tmp_path)
    for out, e in res:
        r = led2.replay(e["id"], m2)
        assert r["ok"] and r["identical"] and r["memory_used_ok"], r
        assert r["replay_digest"] == e["output_digest"] == "sha256:" + __import__("hashlib").sha256(
            canonical_json(out)).hexdigest()
    v = led2.verify(m2, replay=True)
    assert v["ok"] and v["errors"] == [], v["errors"]
    assert sum(t["replayed"] for t in v["tenants"]) == len(FX)
    assert {t["tenant_id"] for t in v["tenants"]} == {f["input"]["org_id"] for f in FX}


def test_replay_memory_backed_decline_and_drift_long(hot):
    root, _, _, res = hot
    m, led = _fresh(root)
    for out, e in res:
        r = led.replay(e["id"], m)
        assert r["ok"], r
    last = res[-1][1]
    assert last["uw_outcome"] == "decline" and last["memory"]["before"]["seq"] == 2
    assert last["memory"]["used"]["n"] == 2 and last["memory"]["appended"]["seq"] == 3
    # the replay of the first entry sees an empty memory even though memory now holds 3 records
    assert led.replay(res[0][1]["id"], m)["memory_seq"] == 0


def test_replay_uses_memory_as_of_the_scoring(hot):
    root, m, led, res = hot
    # later scorings of the same agent change "current" memory, never the replay of earlier entries
    h = _hot()
    for i in range(1, 4):
        record_scoring(parse_scorer_input({**_shift(h, 0, f"n{i}"), "now": h["now"] + i * 3_600_000}), m, led)
    m2, led2 = _fresh(root)
    assert all(led2.replay(e["id"], m2)["ok"] for _, e in res)
    assert led2.verify(m2, replay=True)["ok"]


def test_entry_fields_metadata_only(hot):
    root, _, led, res = hot
    e = res[-1][1]
    for k in ("id", "tenant_id", "agent_id", "input_digest", "input_key", "memory", "model_version",
              "output_digest", "output_key", "prev_hash", "hash", "seq", "ts"):
        assert k in e
    assert e["hash"] == entry_hash(e) and e["prev_hash"] == res[-2][1]["hash"]
    assert res[0][1]["prev_hash"] == GENESIS and res[0][1]["memory"]["before"] == {"seq": 0, "hash": GENESIS, "ts": None}
    stored = json.loads(led.cram.get(e["input_key"]))
    assert parse_scorer_input(stored).canonical_dict() == stored
    blob = b"".join(p.read_bytes() for p in root.rglob("*") if p.is_file())
    for needle in (b'"prompt"', b'"completion"', b'"tool_args"', b'"messages"'):
        assert needle not in blob


def test_get_and_unknown_ids(hot):
    _, _, led, res = hot
    assert led.get(res[1][1]["id"]) == res[1][1]
    for bad in ("nope", "msl_0000000000000000_1", res[0][1]["id"][:-1] + "9"):
        with pytest.raises(LedgerNotFound):
            led.get(bad)


def test_model_version_mismatch_refuses_replay(hot, monkeypatch):
    import neural_mesh.minogan.ledger as L

    _, m, led, res = hot
    monkeypatch.setattr(L, "MODEL_VERSION", "mesh.minogan.score/v999")
    r = led.replay(res[0][1]["id"], m)
    assert not r["ok"] and r["error"] == "model_version_mismatch"


def test_in_process_scorer_records_and_no_memory_path(tmp_path):
    led = ScoreLedger(tmp_path)
    f = FX[0]["input"]
    out = MeshScorer(ledger=led).score(f)
    assert out == score(f)  # no memory: parity path, still ledgered
    e = led.get(f"msl_{led._tdir(f['org_id']).name[:16]}_1")
    assert e["memory"] is None and led.replay(e, AgentMemory(tmp_path))["ok"]
    m = AgentMemory(tmp_path / "m")
    led2 = ScoreLedger(tmp_path / "m")
    assert MeshScorer(memory=m, ledger=led2).score(f) == score(f, memory=AgentMemory(tmp_path / "x"))
    assert led2.verify(m, replay=True)["ok"]


def test_pre_ledger_memory_is_recorded_as_unledgered(tmp_path):
    h = _hot()
    m = AgentMemory(tmp_path)
    t, a = h["org_id"], h["agent"]["id"]
    for d in (40, 35):
        m.append(t, a, {"kind": "score", "ts": h["now"] - d * DAY_MS, "score": 20, "signals": []})
    led = ScoreLedger(tmp_path)
    e = record_scoring(parse_scorer_input(h), m, led)[2]
    assert e["seq"] == 2 and e["memory"]["before"]["seq"] == 2
    u = led.get(f"msl_{led._tdir(t).name[:16]}_1")
    assert u["kind"] == "memory_unledgered" and u["memory"]["from_seq"] == 1 and u["memory"]["to_seq"] == 2
    v = _verify(tmp_path, replay=True)
    assert v["ok"] and any("recorded without scoring entries" in w for w in v["warnings"])
    assert not led.replay(u["id"], m)["ok"]  # not replayable, by design


# ----------------------------------------------------------------------------- tamper → verify fails


def _line_path(led: ScoreLedger, tenant: str, seq: int) -> Path:
    return led._chunk(led._tdir(tenant), seq)


def test_verify_ok_baseline(hot):
    root, *_ = hot
    v = _verify(root, replay=True)
    assert v["ok"] and v["tenants"][0]["n"] == 3 and v["tenants"][0]["replayed"] == 3


@pytest.mark.parametrize("which", ["entry", "input", "output"])
def test_tamper_cas_bytes(hot, which):
    root, _, led, res = hot
    e = res[1][1]
    if which == "entry":
        key = json.loads(_line_path(led, e["tenant_id"], 2).read_text().splitlines()[1])["key"]
    else:
        key = e[f"{which}_key"]
    p = led.cram._object_path(key)
    p.write_bytes(p.read_bytes()[:-1] + b" ")  # one byte flipped
    v = _verify(root)
    assert not v["ok"] and v["errors"]
    m, led2 = _fresh(root)
    r = led2.replay(e["id"], m)
    assert not r["ok"] and r["error"] == "ledger_corrupt"


@pytest.mark.parametrize("field,value", [("score", 1), ("uw_outcome", "bind"), ("output_digest", "sha256:" + "0" * 64),
                                         ("memory", None), ("agent_id", "someone-else")])
def test_tamper_rehashed_entry_breaks_chain(hot, field, value):
    root, _, led, res = hot
    e = dict(res[1][1])
    e[field] = value
    e["hash"] = entry_hash(e)  # internally consistent forgery
    key = led.cram.put_object(canonical_json(e), ObjectType.EVIDENCE).content_hash
    p = _line_path(led, e["tenant_id"], 2)
    lines = [json.loads(x) for x in p.read_text().splitlines()]
    lines[1].update(key=key, hash=e["hash"], agent_id=e["agent_id"])
    p.write_bytes(b"".join(canonical_json(x) + b"\n" for x in lines))
    assert not _verify(root)["ok"]


def test_tamper_index_line_and_head(hot):
    root, _, led, res = hot
    t = res[0][1]["tenant_id"]
    p = _line_path(led, t, 1)
    orig = p.read_bytes()
    lines = [json.loads(x) for x in orig.decode().splitlines()]
    lines[0]["mem_to"] = 7
    p.write_bytes(b"".join(canonical_json(x) + b"\n" for x in lines))
    assert not _verify(root)["ok"]
    p.write_bytes(orig)
    assert _verify(root)["ok"]
    hp = led._tdir(t) / "head.json"
    head = json.loads(hp.read_text())
    hp.write_text(json.dumps({**head, "hash": "f" * 64}))
    assert not _verify(root)["ok"]


def test_deleted_ledger_tail_detected_via_memory(hot):
    root, _, led, res = hot
    t = res[0][1]["tenant_id"]
    p = _line_path(led, t, 1)
    p.write_bytes(b"".join(x + b"\n" for x in p.read_bytes().split(b"\n")[:2]))  # drop entry 3
    hp = led._tdir(t) / "head.json"
    hp.write_text(json.dumps({"tenant_id": t, "seq": 2, "hash": res[1][1]["hash"], "pending": None}))
    v = _verify(root)
    assert not v["ok"] and "has no ledger entry" in v["errors"][0]


def test_tamper_referenced_memory_bytes(hot):
    root, m, _, res = hot
    t, a = res[0][1]["tenant_id"], res[0][1]["agent_id"]
    line = json.loads((m._agent_dir(t, a) / "days").glob("*.jsonl").__next__().read_text().splitlines()[0])
    p = m.cram._object_path(line["key"])
    p.write_bytes(p.read_bytes().replace(b'"score":', b'"score":1', 1))
    assert not _verify(root)["ok"]
    m2, led2 = _fresh(root)
    assert not led2.replay(res[-1][1]["id"], m2)["ok"]


def test_consistently_rewritten_memory_detected_by_ledger(hot):
    """Attacker rewrites the whole memory chain consistently (memory verify passes); the ledger refs catch it."""
    root, m, _, res = hot
    t, a = res[0][1]["tenant_id"], res[0][1]["agent_id"]
    recs = m.history(t, a, 0, 10**13)
    adir = m._agent_dir(t, a)
    prev, buckets = GENESIS, {}
    from neural_mesh.minogan.memory import _day

    for r in recs:
        r = {**r, "prev_hash": prev}
        if r["seq"] == 1:
            r["score"] = 0  # "nicer" history
        r["hash"] = record_hash(r)
        key = m.cram.put_object(canonical_json(r), ObjectType.MEMORY).content_hash
        buckets.setdefault(_day(r["ts"]), []).append(m._index_line(r, key))
        prev = r["hash"]
    for day, lines in buckets.items():
        (adir / "days" / f"{day}.jsonl").write_bytes(b"".join(canonical_json(x) + b"\n" for x in lines))
    head = json.loads((adir / "head.json").read_text())
    (adir / "head.json").write_bytes(canonical_json({**head, "hash": prev}))
    m2, led2 = _fresh(root)
    assert m2.verify_chain(t, a)["ok"]  # memory alone looks fine
    v = led2.verify(m2)
    assert not v["ok"] and "memory" in v["errors"][0]
    assert not led2.replay(res[-1][1]["id"], m2)["ok"]


# ----------------------------------------------------------------------------- crash safety


_CHILD = textwrap.dedent(
    """
    import json, sys, copy
    sys.path.insert(0, {src!r})
    from neural_mesh.minogan import parse_scorer_input
    from neural_mesh.minogan.ledger import ScoreLedger, record_scoring
    from neural_mesh.minogan.memory import AgentMemory
    root, base, n = {root!r}, json.loads(open({inp!r}).read()), {n}
    m, led = AgentMemory(root), ScoreLedger(root)
    for i in range(n):
        d = copy.deepcopy(base); d["now"] = base["now"] + i * 1000
        for s in d["signals"]:
            s["id"] = s["id"] + "-" + str(i)
        record_scoring(parse_scorer_input(d), m, led)
        print(i, flush=True)
    """
)


def _child(tmp: Path, n: int, env_extra: dict | None = None) -> subprocess.Popen:
    inp = tmp / "inp.json"
    inp.write_text(json.dumps(_hot()))
    code = _CHILD.format(src=str(REPO / "src"), root=str(tmp / "r"), inp=str(inp), n=n)
    env = {**os.environ, **(env_extra or {})}
    return subprocess.Popen([sys.executable, "-c", code], env=env, stdout=subprocess.PIPE, text=True)


def _next_scoring(tmp: Path) -> dict:
    h = _hot()
    d = {**copy.deepcopy(h), "now": h["now"] + 10**8}
    for s in d["signals"]:
        s["id"] += "-after"
    m, led = _fresh(tmp / "r")
    return record_scoring(parse_scorer_input(d), m, led)[2]


@pytest.mark.parametrize(
    "env,ledger_n,verify_ok_before",
    [
        ({"MESH_MINOGAN_MEMORY_CRASH_AT": "after_cas"}, 0, True),  # nothing durable
        ({"MESH_MINOGAN_MEMORY_CRASH_AT": "after_pending"}, 0, False),  # memory rolled forward, no entry
        ({"MESH_MINOGAN_LEDGER_CRASH_AT": "after_cas"}, 0, False),  # memory committed, entry orphan CAS
        ({"MESH_MINOGAN_LEDGER_CRASH_AT": "after_pending"}, 1, True),  # entry rolled forward
        ({"MESH_MINOGAN_LEDGER_CRASH_AT": "after_index"}, 1, True),
    ],
)
def test_kill9_at_each_step(tmp_path, env, ledger_n, verify_ok_before):
    p = _child(tmp_path, 1, env)
    p.wait(timeout=60)
    assert p.returncode == -signal.SIGKILL
    root = tmp_path / "r"
    led = ScoreLedger(root)
    t = _hot()["org_id"]
    tenants = led.tenants()
    n = led._read_head(led._tdir(t))["seq"] if tenants else 0
    assert n == ledger_n
    v = _verify(root)
    assert v["ok"] is verify_ok_before, v
    e = _next_scoring(tmp_path)  # next scoring heals the gap with a memory_unledgered entry
    v = _verify(root, replay=True)
    assert v["ok"], v["errors"]
    assert e["kind"] == "score"


def test_kill9_mid_stream_then_heal(tmp_path):
    p = _child(tmp_path, 400)
    for _ in range(15):
        p.stdout.readline()
    time.sleep(0.05)
    p.send_signal(signal.SIGKILL)
    p.wait(timeout=30)
    _next_scoring(tmp_path)
    v = _verify(tmp_path / "r", replay=True)
    assert v["ok"], v["errors"]
    assert v["tenants"][0]["replayed"] >= 15


# ----------------------------------------------------------------------------- CLI


def test_cli_replay_and_verify(hot):
    root, _, led, res = hot
    env = {**os.environ, "PYTHONPATH": str(REPO / "src")}

    def cli(*args):
        return subprocess.run([sys.executable, "-m", "neural_mesh.cli", "minogan", *args], check=False,
                              capture_output=True, text=True, env=env, timeout=60, cwd=root)

    r = cli("replay", res[-1][1]["id"], "--root", str(root))
    assert r.returncode == 0 and json.loads(r.stdout)["identical"] is True
    r = cli("verify", "--root", str(root), "--replay")
    assert r.returncode == 0 and json.loads(r.stdout)["ok"] is True
    assert cli("replay", "msl_0000000000000000_1", "--root", str(root)).returncode == 1
    p = led.cram._object_path(res[0][1]["output_key"])
    p.write_bytes(p.read_bytes() + b" ")
    r = cli("verify", "--root", str(root))
    assert r.returncode == 1 and json.loads(r.stdout)["ok"] is False


# ----------------------------------------------------------------------------- service wiring


def _svc():
    import importlib.util

    spec = importlib.util.spec_from_file_location("_mino_svc_tests", REPO / "tests/test_minogan_service_cp0088.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.BIG, mod.Srv


def test_service_records_every_scoring_and_replays(tmp_path):
    BIG, Srv = _svc()

    s = Srv(tmp_path)
    try:
        ids = []
        for i in range(3):
            d = copy.deepcopy(BIG)
            d["now"] += i * 1000
            st, h, body = s.req("POST", "/v1/score", d)
            assert st == 200
            ids.append(h["X-Mesh-Ledger-Id"])
        assert s.req("POST", "/v1/score", BIG, token="bad")[0] == 401  # refused requests are not ledgered
    finally:
        s.close()
    m, led = _fresh(s.root)
    assert [led.replay(i, m)["ok"] for i in ids] == [True] * 3
    assert json.loads(led.cram.get(led.get(ids[-1])["output_key"])) == json.loads(body)
    v = led.verify(m, replay=True)
    assert v["ok"] and v["tenants"][0]["n"] == 3


def test_service_deadline_writes_neither_memory_nor_ledger(tmp_path):
    BIG, Srv = _svc()

    def slow(inp, memory=None):
        time.sleep(1.8)
        return score(inp, memory=memory)

    s = Srv(tmp_path, score_fn=slow)
    try:
        assert s.req("POST", "/v1/score", BIG)[0] == 504
        time.sleep(0.6)
    finally:
        s.close()
    assert not any(s.root.rglob("days/*.jsonl")) and not any(s.root.rglob("minogan_ledger/*/head.json"))
