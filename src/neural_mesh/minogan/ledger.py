"""Score ledger — per-tenant hash chain of every scoring, replayable byte-for-byte (CP-0088 P0.6).

Design: docs/schema/minogan/score_ledger_v0.md. Metadata only: the stored input is the validated contract input
(``minogan.scorer/v1`` refuses prompts / completions / tool content), the stored output is the ScorerOutput.

Layout under ``root`` (same root as AgentMemory; shares its C-RAM CAS)::

    <root>/.cram/…                                     EVIDENCE objects: entry, canonical input, canonical output
    <root>/minogan_ledger/<T>/head.json                tenant_id, seq, hash, pending?
    <root>/minogan_ledger/<T>/seq/NNNNNNNN.jsonl       index, 1000 entries per chunk (seq-addressed lookup)
    <root>/minogan_ledger/<T>/.lock                    flock for append / recovery

``T = sha256("minogan.ledger/v0\\0" + tenant_id)[:32]``; entry id ``msl_<T[:16]>_<seq>``.

Append protocol = AgentMemory's (CAS put → head.pending → index append → head commit; recovery rolls a
verified pending entry forward, truncates a torn index tail). Scoring order: memory append, then ledger append;
a crash between the two leaves memory records without an entry — verify fails (indistinguishable from a deleted
ledger tail) until it is recorded as a
``memory_unledgered`` entry before the agent's next scoring, so the chain of custody has no silent holes.
"""

from __future__ import annotations

import fcntl
import hashlib
import json
import os
import re
import threading
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any

from neural_mesh.cram.errors import CRAMCorrupt, ObjectMissing
from neural_mesh.cram.models import ObjectType
from neural_mesh.cram.store import CRAMStore
from neural_mesh.minogan.canonical import canonical_json, input_digest, sha256_hex
from neural_mesh.minogan.contract import ContractError, ScorerInput, parse_scorer_input
from neural_mesh.minogan.memory import GENESIS, AgentMemory, MemoryError_, _check_id
from neural_mesh.minogan.scorer import MODEL_VERSION, score

SCHEMA = "mesh.minogan.ledger/v0"
CHUNK = 1000
_CRASH_ENV = "MESH_MINOGAN_LEDGER_CRASH_AT"  # test hook: after_cas | after_pending | after_index
_ID_RE = re.compile(r"^msl_([0-9a-f]{16})_([1-9][0-9]{0,15})$")


class LedgerError(Exception):
    code = "ledger"


class LedgerCorrupt(LedgerError):
    code = "ledger_corrupt"


class LedgerNotFound(LedgerError):
    code = "ledger_not_found"


class DeadlineExceeded(Exception):
    code = "deadline"


def entry_hash(e: dict[str, Any]) -> str:
    return sha256_hex(canonical_json({k: v for k, v in e.items() if k != "hash"}))


def output_digest(out: dict[str, Any]) -> str:
    return "sha256:" + sha256_hex(canonical_json(out))


class ScoreLedger:
    def __init__(self, root: str | Path):
        self.root = Path(root)
        self.cram = CRAMStore(self.root)
        self.base = self.root / "minogan_ledger"
        self.base.mkdir(parents=True, exist_ok=True)
        self._recovered: set[Path] = set()
        self._covered: dict[str, dict[str, int]] = {}  # tenant -> agent -> memory seq covered by entries
        self._guard = threading.Lock()
        self._mem_agents: list[tuple[str, str]] = []

    # ------------------------------------------------------------------ layout / io

    def _tdir(self, tenant_id: str) -> Path:
        _check_id("tenant_id", tenant_id)
        return self.base / hashlib.sha256(f"minogan.ledger/v0\0{tenant_id}".encode()).hexdigest()[:32]

    @staticmethod
    def _chunk(tdir: Path, seq: int) -> Path:
        return tdir / "seq" / f"{(seq - 1) // CHUNK:08d}.jsonl"

    @contextmanager
    def _lock(self, tdir: Path) -> Iterator[None]:
        tdir.mkdir(parents=True, exist_ok=True)
        with open(tdir / ".lock", "a+") as lf:
            fcntl.flock(lf.fileno(), fcntl.LOCK_EX)
            try:
                yield
            finally:
                fcntl.flock(lf.fileno(), fcntl.LOCK_UN)

    @staticmethod
    def _read_head(tdir: Path) -> dict[str, Any]:
        p = tdir / "head.json"
        if not p.exists():
            return {"tenant_id": None, "seq": 0, "hash": GENESIS, "pending": None}
        return json.loads(p.read_text(encoding="utf-8"))

    @staticmethod
    def _lines(path: Path) -> list[dict[str, Any]]:
        if not path.exists():
            return []
        return [json.loads(raw) for raw in path.read_bytes().split(b"\n")[:-1]]

    @staticmethod
    def _crash(point: str) -> None:
        if os.environ.get(_CRASH_ENV) == point:
            os.kill(os.getpid(), 9)

    @staticmethod
    def _line(e: dict[str, Any], key: str) -> dict[str, Any]:
        m = e.get("memory") or {}
        mem_to = (m.get("appended") or {}).get("seq") if e["kind"] == "score" else m.get("to_seq")
        return {"seq": e["seq"], "id": e["id"], "key": key, "hash": e["hash"], "prev_hash": e["prev_hash"],
                "agent_id": e["agent_id"], "mem_to": mem_to}

    def _put(self, data: bytes, part: str) -> str:
        return self.cram.put_object(data, ObjectType.EVIDENCE, metadata={"schema": f"{SCHEMA}#{part}"}).content_hash

    def _get(self, key: str) -> bytes:
        try:
            self.cram.verify_or_raise(key)
            return self.cram.get(key)
        except (ObjectMissing, CRAMCorrupt) as e:
            raise LedgerCorrupt(f"object {key[:12]}: {type(e).__name__}") from None

    def _load(self, key: str) -> dict[str, Any]:
        e = json.loads(self._get(key))
        if e.get("schema") != SCHEMA or entry_hash(e) != e.get("hash"):
            raise LedgerCorrupt(f"entry {key[:12]}: hash mismatch")
        return e

    # ------------------------------------------------------------------ recovery

    def _recover(self, tdir: Path) -> dict[str, Any]:
        head = self._read_head(tdir)
        pend = head.get("pending")
        if pend:
            cpath = self._chunk(tdir, pend["seq"])
            AgentMemory._truncate_torn_tail(cpath)
            lines = self._lines(cpath)
            e = self._load(pend["key"])
            if e["hash"] != pend["hash"] or e["prev_hash"] != head["hash"] or e["seq"] != head["seq"] + 1:
                raise LedgerCorrupt(f"pending entry does not extend the chain at seq {head['seq']}")
            if not (lines and lines[-1]["seq"] == pend["seq"]):
                AgentMemory._append_line(cpath, self._line(e, pend["key"]))
            head = {"tenant_id": head["tenant_id"], "seq": e["seq"], "hash": e["hash"], "pending": None}
            AgentMemory._write_head(tdir, head)
        elif head["seq"]:
            AgentMemory._truncate_torn_tail(self._chunk(tdir, head["seq"]))
        return head

    def _ensure(self, tdir: Path) -> None:
        if tdir in self._recovered:
            return
        if (tdir / "head.json").exists():
            with self._lock(tdir):
                self._recover(tdir)
        self._recovered.add(tdir)

    # ------------------------------------------------------------------ append

    def append(self, body: dict[str, Any]) -> dict[str, Any]:
        tenant = body["tenant_id"]
        tdir = self._tdir(tenant)
        self._ensure(tdir)
        with self._lock(tdir):
            head = self._recover(tdir)
            if head["tenant_id"] not in (None, tenant):
                raise LedgerCorrupt("ledger directory belongs to another tenant")
            seq = head["seq"] + 1
            e = {**body, "schema": SCHEMA, "id": f"msl_{tdir.name[:16]}_{seq}", "seq": seq,
                 "prev_hash": head["hash"]}
            e["hash"] = entry_hash(e)
            key = self._put(canonical_json(e), "entry")
            self._crash("after_cas")
            AgentMemory._write_head(tdir, {"tenant_id": tenant, "seq": head["seq"], "hash": head["hash"],
                                           "pending": {"seq": seq, "key": key, "hash": e["hash"]}})
            self._crash("after_pending")
            AgentMemory._append_line(self._chunk(tdir, seq), self._line(e, key))
            self._crash("after_index")
            AgentMemory._write_head(tdir, {"tenant_id": tenant, "seq": seq, "hash": e["hash"], "pending": None})
            mem_to = self._line(e, key)["mem_to"]
            with self._guard:
                if tenant in self._covered and mem_to is not None:
                    self._covered[tenant][e["agent_id"]] = mem_to
        return e

    def append_scoring(self, inp: ScorerInput, out: dict[str, Any], mem: dict[str, Any] | None) -> dict[str, Any]:
        out_bytes = canonical_json(out)
        body = {
            "kind": "score", "tenant_id": inp.org_id, "agent_id": inp.agent.id, "ts": inp.now,
            "contract": inp.contract, "input_key": self._put(canonical_json(inp.canonical_dict()), "input"),
            "input_digest": out["components"]["input_digest"], "memory": mem,
            "model_version": out["components"]["model_version"], "methodology": out["methodology"],
            "output_key": self._put(out_bytes, "output"), "output_digest": "sha256:" + sha256_hex(out_bytes),
            "score": out["score"], "uw_outcome": out["components"]["uw"]["outcome"],
        }
        return self.append(body)

    def covered_mem_seq(self, tenant_id: str, agent_id: str) -> int:
        with self._guard:
            if tenant_id not in self._covered:
                tdir = self._tdir(tenant_id)
                self._ensure(tdir)
                cov: dict[str, int] = {}
                for line in self._iter_lines(tdir, self._read_head(tdir)["seq"]):
                    if line["mem_to"] is not None:
                        cov[line["agent_id"]] = line["mem_to"]
                self._covered[tenant_id] = cov
            return self._covered[tenant_id].get(agent_id, 0)

    def reconcile(self, memory: AgentMemory, tenant_id: str, agent_id: str, head: dict[str, Any]) -> dict | None:
        """Record memory records that have no ledger entry (crash window / pre-ledger history). Idempotent."""
        covered = self.covered_mem_seq(tenant_id, agent_id)
        if head["seq"] < covered:
            raise LedgerCorrupt("agent memory is behind the ledger (memory rolled back?)")
        if head["seq"] == covered:
            return None
        return self.append({
            "kind": "memory_unledgered", "tenant_id": tenant_id, "agent_id": agent_id, "ts": head["ts"],
            "memory": {"from_seq": covered + 1, "to_seq": head["seq"], "to_hash": head["hash"], "to_ts": head["ts"]},
            "reason": "memory records without a ledger entry (crash between memory and ledger commit, or pre-ledger)",
        })

    # ------------------------------------------------------------------ read

    def _iter_lines(self, tdir: Path, upto: int) -> Iterator[dict[str, Any]]:
        for c in range((upto + CHUNK - 1) // CHUNK):
            for line in self._lines(tdir / "seq" / f"{c:08d}.jsonl"):
                if line["seq"] <= upto:
                    yield line

    def get(self, entry_id: str) -> dict[str, Any]:
        m = _ID_RE.match(entry_id or "")
        if not m:
            raise LedgerNotFound("malformed ledger id")
        dirs = [d for d in self.base.glob(f"{m.group(1)}*") if (d / "head.json").exists()]
        if len(dirs) != 1:
            raise LedgerNotFound("unknown ledger id")
        tdir, seq = dirs[0], int(m.group(2))
        self._ensure(tdir)
        if seq > self._read_head(tdir)["seq"]:
            raise LedgerNotFound("unknown ledger id")
        for line in self._lines(self._chunk(tdir, seq)):
            if line["seq"] == seq:
                e = self._load(line["key"])
                if e["hash"] != line["hash"] or e["id"] != entry_id or e["seq"] != seq:
                    raise LedgerCorrupt(f"index line {seq} does not match its entry")
                return e
        raise LedgerCorrupt(f"entry {seq} missing from index")

    def tenants(self) -> list[str]:
        out = []
        for d in sorted(self.base.iterdir()):
            if (d / "head.json").exists():
                self._ensure(d)
                out.append(self._read_head(d)["tenant_id"])
        return out

    # ------------------------------------------------------------------ memory refs / replay

    def check_memory_refs(self, e: dict[str, Any], memory: AgentMemory) -> None:
        t, a, m = e["tenant_id"], e["agent_id"], e.get("memory")
        try:
            if e["kind"] == "memory_unledgered":
                if memory.record_at(t, a, m["to_seq"], m["to_ts"])["hash"] != m["to_hash"]:
                    raise LedgerCorrupt(f"{e['id']}: memory seq {m['to_seq']} hash differs from the ledger")
                return
            if m is None:
                return
            b, ap = m["before"], m["appended"]
            if b["seq"] == 0:
                if b["hash"] != GENESIS:
                    raise LedgerCorrupt(f"{e['id']}: empty memory snapshot must reference genesis")
            elif memory.record_at(t, a, b["seq"], b["ts"])["hash"] != b["hash"]:
                raise LedgerCorrupt(f"{e['id']}: memory snapshot seq {b['seq']} hash differs from the ledger")
            rec = memory.record_at(t, a, ap["seq"], ap["ts"])
            if ap["seq"] != b["seq"] + 1 or rec["hash"] != ap["hash"] or rec.get("input_digest") != e["input_digest"]:
                raise LedgerCorrupt(f"{e['id']}: appended memory record does not match the ledger")
        except MemoryError_ as x:
            raise LedgerCorrupt(f"{e['id']}: memory reference: {type(x).__name__}: {x}") from None

    def replay(self, entry: dict[str, Any] | str, memory: AgentMemory) -> dict[str, Any]:
        """Re-score from the stored input with the memory view as of the scoring; compare output bytes."""
        if isinstance(entry, str):
            try:
                e = self.get(entry)
            except LedgerError as x:
                return {"id": entry, "ok": False, "error": x.code, "detail": str(x)[:300]}
        else:
            e = entry
        res: dict[str, Any] = {"id": e["id"], "kind": e["kind"], "ok": False}
        if e["kind"] != "score":
            return {**res, "error": "not_replayable", "detail": "memory_unledgered entries carry no input"}
        if e["model_version"] != MODEL_VERSION:
            return {**res, "error": "model_version_mismatch", "entry_model": e["model_version"],
                    "running_model": MODEL_VERSION}
        try:
            inp = parse_scorer_input(self._get(e["input_key"]))
            if input_digest(inp.canonical_dict()) != e["input_digest"]:
                raise LedgerCorrupt(f"{e['id']}: stored input does not match input_digest")
            if inp.org_id != e["tenant_id"] or inp.agent.id != e["agent_id"] or inp.now != e["ts"]:
                raise LedgerCorrupt(f"{e['id']}: stored input does not match entry tenant/agent/ts")
            self.check_memory_refs(e, memory)
            m = e["memory"]
            view = memory.view(e["tenant_id"], e["agent_id"], m["before"]["seq"]) if m else None
            out = score(inp, memory=view)
            got = canonical_json(out)
            stored = self._get(e["output_key"])
        except (LedgerError, ContractError, MemoryError_) as x:
            return {**res, "error": getattr(x, "code", "error"), "detail": str(x)[:300]}
        used_ok = view is None or view.used_ref() == m["used"]
        identical = got == stored and "sha256:" + sha256_hex(got) == e["output_digest"]
        return {**res, "ok": identical and used_ok, "identical": identical, "memory_used_ok": used_ok,
                "output_digest": e["output_digest"], "replay_digest": "sha256:" + sha256_hex(got),
                "model_version": MODEL_VERSION, "memory_seq": m["before"]["seq"] if m else None}

    # ------------------------------------------------------------------ verify

    def verify(self, memory: AgentMemory, tenant_id: str | None = None, *, replay: bool = False) -> dict[str, Any]:
        """Whole-chain audit: ledger links + entry/input/output CAS bytes + digests + memory refs and coverage."""
        report: dict[str, Any] = {"ok": True, "tenants": [], "errors": [], "warnings": []}
        try:  # tenants known to memory but absent from the ledger are audited too (unledgered records)
            mem_agents = memory.agents(tenant_id)
        except MemoryError_ as x:
            return {"ok": False, "tenants": [], "errors": [f"memory: {type(x).__name__}: {x}"], "warnings": []}
        self._mem_agents = mem_agents
        names = [tenant_id] if tenant_id else sorted(set(self.tenants()) | {t for t, _ in mem_agents})
        for t in names:
            r = self._verify_tenant(t, memory, replay)
            report["tenants"].append(r)
            report["errors"] += r.pop("errors")
            report["warnings"] += r.pop("warnings")
        report["ok"] = not report["errors"]
        return report

    def _verify_tenant(self, t: str, memory: AgentMemory, replay: bool) -> dict[str, Any]:
        r: dict[str, Any] = {"tenant_id": t, "n": 0, "replayed": 0, "errors": [], "warnings": []}
        tdir = self._tdir(t)
        covered: dict[str, int] = {}
        try:
            self._ensure(tdir)
            head = self._read_head(tdir)
            if head["seq"] and head["tenant_id"] != t:
                raise LedgerCorrupt("head tenant_id mismatch")
            prev, expect = GENESIS, 1
            for line in self._iter_lines(tdir, head["seq"]):
                if line["seq"] != expect or line["prev_hash"] != prev:
                    raise LedgerCorrupt(f"index gap or chain break at seq {expect}")
                e = self._load(line["key"])
                if (e["hash"] != line["hash"] or e["seq"] != expect or e["prev_hash"] != prev
                        or e["tenant_id"] != t or e["id"] != f"msl_{tdir.name[:16]}_{expect}"
                        or e["agent_id"] != line["agent_id"] or self._line(e, line["key"]) != line):
                    raise LedgerCorrupt(f"entry {expect} does not match its index line / chain")
                a, m = e["agent_id"], e.get("memory")
                if e["kind"] == "score":
                    inp_raw = self._get(e["input_key"])
                    if input_digest(json.loads(inp_raw)) != e["input_digest"]:
                        raise LedgerCorrupt(f"{e['id']}: input digest mismatch")
                    out_raw = self._get(e["output_key"])
                    if "sha256:" + sha256_hex(out_raw) != e["output_digest"]:
                        raise LedgerCorrupt(f"{e['id']}: output digest mismatch")
                    if json.loads(out_raw)["components"]["input_digest"] != e["input_digest"]:
                        raise LedgerCorrupt(f"{e['id']}: output cites another input")
                    if m is not None:
                        if m["before"]["seq"] != covered.get(a, 0):
                            raise LedgerCorrupt(f"{e['id']}: memory snapshot skips unledgered records")
                        covered[a] = m["appended"]["seq"]
                elif e["kind"] == "memory_unledgered":
                    if m["from_seq"] != covered.get(a, 0) + 1 or m["to_seq"] < m["from_seq"]:
                        raise LedgerCorrupt(f"{e['id']}: unledgered range does not continue coverage")
                    covered[a] = m["to_seq"]
                    r["warnings"].append(f"{e['id']}: memory seq {m['from_seq']}..{m['to_seq']} of agent "
                                         f"{a!r} recorded without scoring entries")
                else:
                    raise LedgerCorrupt(f"{e['id']}: unknown kind")
                self.check_memory_refs(e, memory)
                if replay and e["kind"] == "score":
                    rr = self.replay(e, memory)
                    if not rr["ok"]:
                        raise LedgerCorrupt(f"{e['id']}: replay failed: {rr.get('error') or 'output differs'}")
                    r["replayed"] += 1
                prev, expect = e["hash"], expect + 1
            if expect - 1 != head["seq"] or prev != head["hash"]:
                raise LedgerCorrupt("head does not match chain tail")
            for ta, aa in self._mem_agents:
                if ta == t:
                    covered.setdefault(aa, 0)  # memory agent never ledgered ⇒ coverage 0
            r.update(n=head["seq"], head_hash=head["hash"], agents=len(covered))
            for a, cov in sorted(covered.items()):
                vc = memory.verify_chain(t, a)
                if not vc["ok"]:
                    raise LedgerCorrupt(f"agent {a!r} memory chain: {vc['error']}")
                if vc["head_seq"] > cov:  # crash window OR a deleted ledger tail: indistinguishable → error
                    raise LedgerCorrupt(f"agent {a!r}: memory seq {cov + 1}..{vc['head_seq']} has no ledger entry "
                                        "(deleted ledger tail, or a crash between memory and ledger commit; the "
                                        "agent's next scoring records it as memory_unledgered)")
                if vc["head_seq"] < cov:
                    raise LedgerCorrupt(f"agent {a!r}: memory head {vc['head_seq']} behind ledger {cov}")
        except (LedgerError, MemoryError_, json.JSONDecodeError, KeyError, TypeError) as x:
            r["errors"].append(f"tenant {t!r}: {type(x).__name__}: {x}")
        return r


# ---------------------------------------------------------------------- scoring with memory + ledger


def record_scoring(inp: ScorerInput, memory: AgentMemory | None, ledger: ScoreLedger, *,
                   score_fn: Callable[..., dict] = score,
                   check: Callable[[], bool] | None = None) -> tuple[dict[str, Any], dict | None, dict[str, Any]]:
    """Score ``inp`` (memory view as of the current head), append memory, then append the ledger entry.

    Callers serialise per (tenant, agent). ``check()`` False after scoring ⇒ DeadlineExceeded, nothing persisted.
    """
    tenant, agent = inp.org_id, inp.agent.id
    if memory is None:
        out = score_fn(inp)
        if check is not None and not check():
            raise DeadlineExceeded("deadline passed before persisting")
        return out, None, ledger.append_scoring(inp, out, None)
    head = memory.head(tenant, agent)
    ledger.reconcile(memory, tenant, agent, head)
    view = memory.view(tenant, agent, head["seq"])
    out = score_fn(inp, memory=view)
    if check is not None and not check():
        raise DeadlineExceeded("deadline passed before persisting")
    rec = memory.append_score(inp, out)
    if rec["seq"] != head["seq"] + 1:
        raise LedgerError("concurrent memory writer for this agent (one writer per memory root)")
    mem = {"before": {"seq": head["seq"], "hash": head["hash"], "ts": head["ts"]}, "used": view.used_ref(),
           "appended": {"seq": rec["seq"], "hash": rec["hash"], "ts": rec["ts"]}}
    return out, rec, ledger.append_scoring(inp, out, mem)
