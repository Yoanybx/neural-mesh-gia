"""Append-only decision log for Cognitive Router R0."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable

from .models import RouteDecision


class DecisionLog:
    """JSONL decision log — every RouteDecision is persisted (P2)."""

    def __init__(self, path: str | Path | None = None):
        self.path = Path(path) if path else None
        self._memory: list[dict[str, Any]] = []
        if self.path is not None:
            self.path.parent.mkdir(parents=True, exist_ok=True)

    def append(self, decision: RouteDecision) -> None:
        payload = decision.to_dict()
        self._memory.append(payload)
        if self.path is not None:
            with self.path.open("a", encoding="utf-8") as f:
                f.write(json.dumps(payload, sort_keys=True) + "\n")
                f.flush()

    def entries(self) -> list[dict[str, Any]]:
        if self.path is not None and self.path.exists():
            out: list[dict[str, Any]] = []
            for line in self.path.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if line:
                    out.append(json.loads(line))
            return out
        return list(self._memory)

    def clear_memory(self) -> None:
        self._memory.clear()

    def __len__(self) -> int:
        return len(self.entries())

    def __iter__(self) -> Iterable[dict[str, Any]]:
        return iter(self.entries())


__all__ = ["DecisionLog"]
