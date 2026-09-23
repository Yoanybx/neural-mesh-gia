"""Light Phase 5A observability — trace_id / operation_id / node_path (Cycle 12)."""

from __future__ import annotations

import json
import os
import time
import uuid
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


STAGE_ORDER = ("Task", "Router", "Network", "C-RAM", "Checkpoint")


@dataclass
class TraceSpan:
    stage: str
    detail: str = ""
    latency_ms: float = 0.0
    result: str = "OK"
    node_id: str | None = None
    ts_ms: int = 0


@dataclass
class OperationTrace:
    operation_id: str
    trace_id: str
    op: str
    node_path: list[str] = field(default_factory=list)
    spans: list[TraceSpan] = field(default_factory=list)
    latency_ms: float = 0.0
    result: str = "OK"
    extras: dict[str, Any] = field(default_factory=dict)
    created_at_ms: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "operation_id": self.operation_id,
            "trace_id": self.trace_id,
            "op": self.op,
            "node_path": list(self.node_path),
            "spans": [asdict(s) for s in self.spans],
            "latency_ms": self.latency_ms,
            "result": self.result,
            "extras": dict(self.extras),
            "created_at_ms": self.created_at_ms,
            "reconstruction": " → ".join(
                s.stage for s in sorted(self.spans, key=lambda x: STAGE_ORDER.index(x.stage) if x.stage in STAGE_ORDER else 99)
            )
            or "Task → Router → Network → C-RAM → Checkpoint",
        }


class TraceStore:
    """Append-only JSONL traces under ``<root>/.cram/traces.jsonl``."""

    def __init__(self, root: str | Path):
        self.root = Path(root)
        self.path = self.root / ".cram" / "traces.jsonl"
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._cache: dict[str, OperationTrace] = {}
        self._load()

    def _load(self) -> None:
        if not self.path.exists():
            return
        for line in self.path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                data = json.loads(line)
            except json.JSONDecodeError:
                continue
            spans = [
                TraceSpan(**s) if isinstance(s, dict) else s
                for s in data.get("spans", [])
            ]
            tr = OperationTrace(
                operation_id=str(data["operation_id"]),
                trace_id=str(data.get("trace_id") or data["operation_id"]),
                op=str(data.get("op") or ""),
                node_path=list(data.get("node_path") or []),
                spans=spans,
                latency_ms=float(data.get("latency_ms") or 0.0),
                result=str(data.get("result") or "OK"),
                extras=dict(data.get("extras") or {}),
                created_at_ms=int(data.get("created_at_ms") or 0),
            )
            self._cache[tr.operation_id] = tr

    def begin(
        self,
        op: str,
        *,
        operation_id: str | None = None,
        trace_id: str | None = None,
        node_path: list[str] | None = None,
    ) -> OperationTrace:
        oid = operation_id or uuid.uuid4().hex
        tid = trace_id or oid
        tr = OperationTrace(
            operation_id=oid,
            trace_id=tid,
            op=op,
            node_path=list(node_path or []),
            created_at_ms=int(time.time() * 1000),
        )
        return tr

    def add_span(
        self,
        tr: OperationTrace,
        stage: str,
        *,
        detail: str = "",
        latency_ms: float = 0.0,
        result: str = "OK",
        node_id: str | None = None,
    ) -> None:
        tr.spans.append(
            TraceSpan(
                stage=stage,
                detail=detail,
                latency_ms=float(latency_ms),
                result=result,
                node_id=node_id,
                ts_ms=int(time.time() * 1000),
            )
        )
        if node_id and node_id not in tr.node_path:
            tr.node_path.append(node_id)

    def commit(self, tr: OperationTrace, *, result: str | None = None) -> OperationTrace:
        if result is not None:
            tr.result = result
        tr.latency_ms = sum(s.latency_ms for s in tr.spans)
        self._cache[tr.operation_id] = tr
        with open(self.path, "a", encoding="utf-8") as f:
            f.write(json.dumps(tr.to_dict(), sort_keys=True) + "\n")
            f.flush()
            os.fsync(f.fileno())
        return tr

    def get(self, operation_id: str) -> OperationTrace | None:
        return self._cache.get(operation_id)

    def reconstruct(self, operation_id: str) -> dict[str, Any] | None:
        tr = self.get(operation_id)
        if tr is None:
            # refresh from disk
            self._load()
            tr = self.get(operation_id)
        if tr is None:
            return None
        d = tr.to_dict()
        # Ensure minimal reconstruction path always present
        if not d.get("reconstruction"):
            d["reconstruction"] = "Task → Router → Network → C-RAM → Checkpoint"
        # Fill missing stages as placeholders for CLI readability
        have = {s.stage for s in tr.spans}
        filled = []
        for stage in STAGE_ORDER:
            if stage in have:
                span = next(s for s in tr.spans if s.stage == stage)
                filled.append(asdict(span))
            else:
                filled.append(
                    {
                        "stage": stage,
                        "detail": "(not recorded)",
                        "latency_ms": 0.0,
                        "result": "N/A",
                        "node_id": None,
                        "ts_ms": 0,
                    }
                )
        d["pipeline"] = filled
        d["reconstruction"] = " → ".join(STAGE_ORDER)
        return d


def cmd_trace(operation_id: str, *, root: str | Path) -> int:
    store = TraceStore(root)
    data = store.reconstruct(operation_id)
    if data is None:
        print(json.dumps({"error": "operation_id not found", "operation_id": operation_id}))
        return 3
    print(json.dumps(data, indent=2, sort_keys=True))
    return 0


__all__ = [
    "STAGE_ORDER",
    "OperationTrace",
    "TraceSpan",
    "TraceStore",
    "cmd_trace",
]
