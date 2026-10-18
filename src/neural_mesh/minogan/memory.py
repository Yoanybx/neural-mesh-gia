"""AgentMemory — per-(tenant_id, agent_id) behaviour memory on C-RAM (CP-0088 P0.4).

Substrate persistence, not cognition. Metadata only: score outputs, features and signal summaries
(id/type/rule/severity/ts/pattern/trace ids). Prompts / completions / tool content are refused.

Layout under ``root`` (design: docs/schema/minogan/agent_memory_v0.md)::

    <root>/.cram/…                                   C-RAM CAS: one MEMORY object per record (immutable)
    <root>/minogan_memory/<T>/<A>/head.json          head: seq, hash, ts, first_day, last_day, pending?
    <root>/minogan_memory/<T>/<A>/days/YYYY-MM-DD.jsonl   day bucket: one index line per record (append+fsync)
    <root>/minogan_memory/<T>/<A>/.lock              flock for append / recovery

``T = sha256("minogan.memory/v0\\0" + tenant_id)[:32]``, ``A = sha256(tenant_id + "\\0" + agent_id)[:32]``.

Append protocol (crash-safe; kill -9 at any point leaves a valid chain):
1. CAS put of the record (fsync)            — crash after: orphan CAS object, invisible
2. head.pending = {seq, day, key, hash} (atomic replace + fsync) — record is now durable
3. bucket append of the index line (fsync)
4. head commit (seq/hash/ts advanced, pending cleared)
Recovery on open (under lock): torn bucket tail truncated; a pending record is verified (CAS bytes,
record hash, prev_hash == head.hash) and rolled forward; otherwise refused with MemoryCorrupt.

Reads touch only the day buckets in the requested range (``stats`` counts bucket and record reads) —
never ``CRAMStore.list_keys``. Every record read is re-hashed and its tenant/agent checked.
"""

from __future__ import annotations

import fcntl
import hashlib
import json
import os
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from neural_mesh.cram.durability import SyncMode, atomic_write_bytes
from neural_mesh.cram.errors import CRAMCorrupt, ObjectMissing
from neural_mesh.cram.models import ObjectType
from neural_mesh.cram.store import CRAMStore
from neural_mesh.minogan.canonical import canonical_json, sha256_hex
from neural_mesh.minogan.contract import CONTENT_KEYS, ScorerInput

SCHEMA = "mesh.minogan.memory/v0"
DAY_MS = 86_400_000
GENESIS = "0" * 64
_CRASH_ENV = "MESH_MINOGAN_MEMORY_CRASH_AT"  # test hook: after_cas | after_pending | after_bucket


class MemoryError_(Exception):
    code = "memory"


class MemoryCorrupt(MemoryError_):
    code = "memory_corrupt"


class MemoryTenantError(MemoryError_):
    """A record read under (tenant, agent) belongs to someone else — isolation violation refused."""

    code = "memory_tenant"


class MemoryOrderError(MemoryError_):
    code = "memory_order"


class MemoryContentError(MemoryError_):
    code = "memory_content"


def _day(ts: int) -> str:
    return datetime.fromtimestamp(ts / 1000, tz=timezone.utc).strftime("%Y-%m-%d")


def _days(since: int, until: int) -> Iterator[str]:
    d = datetime.fromtimestamp(since / 1000, tz=timezone.utc).date()
    end = datetime.fromtimestamp(until / 1000, tz=timezone.utc).date()
    while d <= end:
        yield d.isoformat()
        d += timedelta(days=1)


def _check_id(name: str, v: Any) -> str:
    if not isinstance(v, str) or not v or len(v) > 128:
        raise ValueError(f"{name} must be a non-empty str ≤128 chars")
    return v


def _has_content_key(v: Any) -> bool:
    if isinstance(v, dict):
        return any((isinstance(k, str) and k.lower() in CONTENT_KEYS) or _has_content_key(x) for k, x in v.items())
    if isinstance(v, list):
        return any(_has_content_key(x) for x in v)
    return False


def record_hash(rec: dict[str, Any]) -> str:
    return sha256_hex(canonical_json({k: v for k, v in rec.items() if k != "hash"}))


def record_from_score(inp: ScorerInput, out: dict[str, Any]) -> dict[str, Any]:
    """Metadata-only memory payload for one scoring (no titles, no content)."""
    c = out.get("components", {})
    return {
        "kind": "score",
        "ts": inp.now,
        "input_digest": c.get("input_digest"),
        "model_version": c.get("model_version"),
        "score": out["score"],
        "exposure": out["exposure"],
        "behavior": out["behavior"],
        "driftPct": out["driftPct"],
        "driftStatus": out["driftStatus"],
        "window": {"from": inp.window.from_, "to": inp.window.to},
        "features": inp.features.model_dump(),
        "signals": [
            {"id": s.id, "type": s.type, "rule": s.rule, "severity": s.severity, "ts": s.ts, "pattern": s.pattern,
             "trace_ids": list(s.trace_ids[:10])}
            for s in inp.signals
        ],
    }


def recurrence_from_records(records: list[dict[str, Any]], rule: str, days: int, now: int, *,
                            severity: str | None = None,
                            extra_signals: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    """Pure recurrence over already-read records (+ optional current-input signals), dedup by signal id."""
    since = now - days * DAY_MS
    seen: dict[str, int] = {}
    for s in [x for r in records for x in r.get("signals", [])] + list(extra_signals or []):
        if s["rule"] == rule and (severity is None or s["severity"] == severity) and since < s["ts"] <= now:
            seen.setdefault(s["id"], s["ts"])
    ts = sorted(seen.values())
    return {"rule": rule, "days": days, "severity": severity, "occurrences": len(ts),
            "distinct_days": len({_day(t) for t in ts}), "first_ts": ts[0] if ts else None,
            "last_ts": ts[-1] if ts else None}


class AgentMemory:
    def __init__(self, root: str | Path):
        self.root = Path(root)
        self.cram = CRAMStore(self.root)
        self.base = self.root / "minogan_memory"
        self.base.mkdir(parents=True, exist_ok=True)
        self.stats = {"bucket_reads": 0, "record_reads": 0, "lines_read": 0}
        self._recovered: set[Path] = set()

    # ------------------------------------------------------------------ layout

    def _agent_dir(self, tenant_id: str, agent_id: str) -> Path:
        _check_id("tenant_id", tenant_id)
        _check_id("agent_id", agent_id)
        t = hashlib.sha256(f"minogan.memory/v0\0{tenant_id}".encode()).hexdigest()[:32]
        a = hashlib.sha256(f"{tenant_id}\0{agent_id}".encode()).hexdigest()[:32]
        return self.base / t / a

    @contextmanager
    def _lock(self, adir: Path) -> Iterator[None]:
        adir.mkdir(parents=True, exist_ok=True)
        with open(adir / ".lock", "a+") as lf:
            fcntl.flock(lf.fileno(), fcntl.LOCK_EX)
            try:
                yield
            finally:
                fcntl.flock(lf.fileno(), fcntl.LOCK_UN)

    @staticmethod
    def _read_head(adir: Path) -> dict[str, Any]:
        p = adir / "head.json"
        if not p.exists():
            return {"seq": 0, "hash": GENESIS, "ts": None, "first_day": None, "last_day": None, "pending": None}
        return json.loads(p.read_text(encoding="utf-8"))

    @staticmethod
    def _write_head(adir: Path, head: dict[str, Any]) -> None:
        atomic_write_bytes(adir / "head.json", canonical_json(head), sync_mode=SyncMode.EVERY, dir_fsync="every")

    @staticmethod
    def _append_line(path: Path, line: dict[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        created = not path.exists()
        with path.open("ab") as f:
            f.write(canonical_json(line) + b"\n")
            f.flush()
            os.fsync(f.fileno())
        if created:  # make the new bucket's directory entry durable
            dfd = os.open(str(path.parent), os.O_RDONLY)
            try:
                os.fsync(dfd)
            finally:
                os.close(dfd)

    @staticmethod
    def _crash(point: str) -> None:
        if os.environ.get(_CRASH_ENV) == point:  # test hook: simulate kill -9 at a protocol step
            os.kill(os.getpid(), 9)

    # ------------------------------------------------------------------ recovery

    def _bucket_lines(self, path: Path) -> list[dict[str, Any]]:
        self.stats["bucket_reads"] += 1
        if not path.exists():
            return []
        data = path.read_bytes()
        out = []
        for raw in data.split(b"\n")[:-1]:  # a trailing partial line (no \n) is ignored
            out.append(json.loads(raw))
        self.stats["lines_read"] += len(out)
        return out

    @staticmethod
    def _truncate_torn_tail(path: Path) -> None:
        if not path.exists():
            return
        data = path.read_bytes()
        if data and not data.endswith(b"\n"):
            keep = data[: data.rfind(b"\n") + 1]
            with path.open("r+b") as f:
                f.truncate(len(keep))
                f.flush()
                os.fsync(f.fileno())

    def _recover(self, adir: Path, tenant_id: str, agent_id: str) -> dict[str, Any]:
        head = self._read_head(adir)
        pend = head.get("pending")
        if pend:
            bpath = adir / "days" / f"{pend['day']}.jsonl"
            self._truncate_torn_tail(bpath)
            lines = self._bucket_lines(bpath)
            rec = self._load(pend["key"], tenant_id, agent_id)
            if rec["hash"] != pend["hash"] or rec["prev_hash"] != head["hash"] or rec["seq"] != head["seq"] + 1:
                raise MemoryCorrupt(f"pending record does not extend the chain at seq {head['seq']}")
            if not (lines and lines[-1]["seq"] == pend["seq"]):
                self._append_line(bpath, self._index_line(rec, pend["key"]))
            head = self._committed(head, rec)
            self._write_head(adir, head)
        elif head["last_day"]:
            self._truncate_torn_tail(adir / "days" / f"{head['last_day']}.jsonl")
        return head

    def _ensure(self, adir: Path, tenant_id: str, agent_id: str) -> None:
        if adir in self._recovered:
            return
        if (adir / "head.json").exists():
            with self._lock(adir):
                self._recover(adir, tenant_id, agent_id)
        self._recovered.add(adir)

    # ------------------------------------------------------------------ records

    @staticmethod
    def _index_line(rec: dict[str, Any], key: str) -> dict[str, Any]:
        return {"seq": rec["seq"], "ts": rec["ts"], "key": key, "hash": rec["hash"], "prev_hash": rec["prev_hash"]}

    @staticmethod
    def _committed(head: dict[str, Any], rec: dict[str, Any]) -> dict[str, Any]:
        day = _day(rec["ts"])
        return {"seq": rec["seq"], "hash": rec["hash"], "ts": rec["ts"], "first_day": head["first_day"] or day,
                "last_day": day, "pending": None}

    def _load(self, key: str, tenant_id: str, agent_id: str) -> dict[str, Any]:
        self.stats["record_reads"] += 1
        try:
            self.cram.verify_or_raise(key)
            rec = json.loads(self.cram.get(key))
        except (ObjectMissing, CRAMCorrupt) as e:
            raise MemoryCorrupt(f"record {key[:12]}: {type(e).__name__}") from None
        if rec.get("tenant_id") != tenant_id or rec.get("agent_id") != agent_id:
            raise MemoryTenantError("record does not belong to the requested (tenant_id, agent_id)")
        if rec.get("schema") != SCHEMA or record_hash(rec) != rec.get("hash"):
            raise MemoryCorrupt(f"record {key[:12]}: hash mismatch")
        return rec

    def append(self, tenant_id: str, agent_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        """Append one metadata record (payload must carry int ``ts`` ms). Returns the stored record."""
        if _has_content_key(payload):
            raise MemoryContentError("content keys are never stored (metadata only)")
        ts = payload.get("ts")
        if not isinstance(ts, int) or isinstance(ts, bool) or ts < 0:
            raise ValueError("payload.ts must be a non-negative int (epoch ms)")
        adir = self._agent_dir(tenant_id, agent_id)
        self._ensure(adir, tenant_id, agent_id)
        with self._lock(adir):
            head = self._recover(adir, tenant_id, agent_id)
            if head["ts"] is not None and ts < head["ts"]:
                raise MemoryOrderError(f"ts {ts} < last ts {head['ts']} for this agent")
            rec = {**payload, "schema": SCHEMA, "tenant_id": tenant_id, "agent_id": agent_id,
                   "seq": head["seq"] + 1, "prev_hash": head["hash"]}
            rec["hash"] = record_hash(rec)
            key = self.cram.put_object(canonical_json(rec), ObjectType.MEMORY,
                                       metadata={"schema": SCHEMA, "agent_dir": adir.name}).content_hash
            self._crash("after_cas")
            day = _day(ts)
            self._write_head(adir, {**head, "pending": {"seq": rec["seq"], "day": day, "key": key, "hash": rec["hash"]}})
            self._crash("after_pending")
            self._append_line(adir / "days" / f"{day}.jsonl", self._index_line(rec, key))
            self._crash("after_bucket")
            self._write_head(adir, self._committed(head, rec))
        return rec

    def append_score(self, inp: ScorerInput, out: dict[str, Any]) -> dict[str, Any]:
        return self.append(inp.org_id, inp.agent.id, record_from_score(inp, out))

    # ------------------------------------------------------------------ queries

    def head(self, tenant_id: str, agent_id: str) -> dict[str, Any]:
        adir = self._agent_dir(tenant_id, agent_id)
        self._ensure(adir, tenant_id, agent_id)
        return self._read_head(adir)

    def history(self, tenant_id: str, agent_id: str, since: int, until: int) -> list[dict[str, Any]]:
        """Records with since ≤ ts ≤ until (inclusive), in chain order. Reads only the day buckets in range."""
        if until < since:
            return []
        adir = self._agent_dir(tenant_id, agent_id)
        self._ensure(adir, tenant_id, agent_id)
        head = self._read_head(adir)
        if not head["last_day"]:
            return []
        out = []
        for day in _days(since, until):
            if day < head["first_day"] or day > head["last_day"]:
                continue  # outside this agent's lifetime: no read
            for line in self._bucket_lines(adir / "days" / f"{day}.jsonl"):
                if since <= line["ts"] <= until and line["seq"] <= head["seq"]:
                    rec = self._load(line["key"], tenant_id, agent_id)
                    if rec["hash"] != line["hash"] or rec["seq"] != line["seq"]:
                        raise MemoryCorrupt(f"index line seq {line['seq']} does not match its record")
                    out.append(rec)
        return out

    def baseline(self, tenant_id: str, agent_id: str, since: int, until: int) -> dict[str, Any]:
        recs = [r for r in self.history(tenant_id, agent_id, since, until) if r.get("kind") == "score"]
        if not recs:
            return {"n": 0, "mean_score": None, "min_score": None, "max_score": None, "from": None, "to": None}
        s = [r["score"] for r in recs]
        return {"n": len(s), "mean_score": sum(s) / len(s), "min_score": min(s), "max_score": max(s),
                "from": recs[0]["ts"], "to": recs[-1]["ts"]}

    def recurrence(self, tenant_id: str, agent_id: str, rule: str, days: int, now: int,
                   severity: str | None = None, extra_signals: list[dict[str, Any]] | None = None) -> dict[str, Any]:
        """Distinct UTC days (by signal ts) on which ``rule`` fired within (now − days, now]. Dedup by signal id."""
        recs = self.history(tenant_id, agent_id, now - days * DAY_MS, now)
        return recurrence_from_records(recs, rule, days, now, severity=severity, extra_signals=extra_signals)

    # ------------------------------------------------------------------ audit

    def verify_chain(self, tenant_id: str, agent_id: str) -> dict[str, Any]:
        """Full audit of one agent's chain (reads all of its buckets — audit path, not the query path)."""
        adir = self._agent_dir(tenant_id, agent_id)
        try:
            self._ensure(adir, tenant_id, agent_id)
            head = self._read_head(adir)
            if not head["last_day"]:
                return {"ok": True, "n": 0, "head_seq": 0}
            prev, expect = GENESIS, 1
            first = datetime.fromisoformat(head["first_day"]).replace(tzinfo=timezone.utc)
            last = datetime.fromisoformat(head["last_day"]).replace(tzinfo=timezone.utc)
            for day in _days(int(first.timestamp() * 1000), int(last.timestamp() * 1000)):
                for line in self._bucket_lines(adir / "days" / f"{day}.jsonl"):
                    rec = self._load(line["key"], tenant_id, agent_id)
                    if rec["seq"] != expect or line["seq"] != expect:
                        raise MemoryCorrupt(f"sequence gap at {expect}")
                    if rec["prev_hash"] != prev or line["prev_hash"] != prev or line["hash"] != rec["hash"]:
                        raise MemoryCorrupt(f"chain break at seq {expect}")
                    if _day(rec["ts"]) != day:
                        raise MemoryCorrupt(f"record seq {expect} in wrong day bucket")
                    prev, expect = rec["hash"], expect + 1
            if expect - 1 != head["seq"] or prev != head["hash"]:
                raise MemoryCorrupt("head does not match chain tail")
            return {"ok": True, "n": expect - 1, "head_seq": head["seq"], "head_hash": head["hash"]}
        except (MemoryError_, json.JSONDecodeError, KeyError) as e:
            return {"ok": False, "error": f"{type(e).__name__}: {e}"}
