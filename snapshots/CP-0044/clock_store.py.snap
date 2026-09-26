"""Filesystem clock-skew store: pair, samples, abort/refuse-join flags.

Layout under ``<data_root>/clock/``:

  clock_state.json
  samples.jsonl
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from .models import (
    DEFAULT_SKEW_THRESHOLD_MS,
    SCHEMA_STORE,
    ClockN2Only,
    ClockPlaintextForbidden,
    ClockSample,
    HLC,
)


def require_no_plaintext(mode: str | None) -> None:
    """Refuse plaintext / cleartext as a clock-skew transport claim."""
    if mode is None:
        return
    m = str(mode).strip().lower()
    if m in ("plaintext", "plain", "tcp", "cleartext"):
        raise ClockPlaintextForbidden(
            f"plaintext mode forbidden for clock ops: {mode!r}"
        )


class ClockStore:
    """Persist N=2 pair + skew fence state under a data root."""

    MAX_NODES = 2

    def __init__(self, data_root: str | Path):
        self.data_root = Path(data_root)
        self.root = self.data_root / "clock"
        self.state_path = self.root / "clock_state.json"
        self.samples_path = self.root / "samples.jsonl"
        self.root.mkdir(parents=True, exist_ok=True)

    def _atomic_json(self, path: Path, data: dict[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(path.suffix + ".tmp")
        tmp.write_text(
            json.dumps(data, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        os.replace(tmp, path)

    def _default_state(self) -> dict[str, Any]:
        return {
            "schema": SCHEMA_STORE,
            "pair": [],
            "skew_threshold_ms": DEFAULT_SKEW_THRESHOLD_MS,
            "skew_ms": 0,
            "skew_pending": False,
            "pending_nodes": [],
            "join_refused": False,
            "abort_refuse_join": False,
            "abort_reason": "",
            "wall_clock_as_authority": 0,
            "dual_primary": 0,
            "minority_writes": 0,
            "vault_acme_required": 0,
            "plaintext_fallback": 0,
            "refused_join_count": 0,
            "accepted_join_count": 0,
            "local_hlc": HLC().to_dict(),
            "local_mono": 0,
            "last_walls": {},
        }

    def _read_state(self) -> dict[str, Any]:
        if not self.state_path.is_file():
            return self._default_state()
        data = json.loads(self.state_path.read_text(encoding="utf-8"))
        data["wall_clock_as_authority"] = 0
        data["dual_primary"] = 0
        data["minority_writes"] = 0
        data["vault_acme_required"] = 0
        data["plaintext_fallback"] = 0
        data["schema"] = SCHEMA_STORE
        if "pair" not in data or data["pair"] is None:
            data["pair"] = []
        if "pending_nodes" not in data or data["pending_nodes"] is None:
            data["pending_nodes"] = []
        if "last_walls" not in data or data["last_walls"] is None:
            data["last_walls"] = {}
        if "local_hlc" not in data or data["local_hlc"] is None:
            data["local_hlc"] = HLC().to_dict()
        return data

    def _write_state(self, data: dict[str, Any]) -> None:
        data = dict(data)
        data["schema"] = SCHEMA_STORE
        data["wall_clock_as_authority"] = 0
        data["dual_primary"] = 0
        data["minority_writes"] = 0
        data["vault_acme_required"] = 0
        data["plaintext_fallback"] = 0
        pair = list(data.get("pair") or [])
        if len(pair) > self.MAX_NODES:
            raise ClockN2Only(
                f"N>2 refused: pair has {len(pair)} nodes (max {self.MAX_NODES})"
            )
        data["pair"] = pair
        self._atomic_json(self.state_path, data)

    def state(self) -> dict[str, Any]:
        return self._read_state()

    @property
    def pair(self) -> list[str]:
        return list(self._read_state().get("pair") or [])

    @property
    def skew_threshold_ms(self) -> int:
        return int(
            self._read_state().get("skew_threshold_ms") or DEFAULT_SKEW_THRESHOLD_MS
        )

    @property
    def join_refused(self) -> bool:
        return bool(self._read_state().get("join_refused"))

    @property
    def abort_refuse_join(self) -> bool:
        return bool(self._read_state().get("abort_refuse_join"))

    def set_pair(self, node_ids: list[str]) -> list[str]:
        ids = [str(n) for n in node_ids]
        if len(ids) > self.MAX_NODES:
            raise ClockN2Only(
                f"N>2 refused: cannot register {len(ids)} nodes (max {self.MAX_NODES})"
            )
        if len(ids) != len(set(ids)):
            raise ClockN2Only("duplicate node_id in pair refused")
        st = self._read_state()
        st["pair"] = ids
        self._write_state(st)
        return ids

    def set_threshold(self, threshold_ms: int) -> None:
        st = self._read_state()
        st["skew_threshold_ms"] = int(threshold_ms)
        self._write_state(st)

    def set_local_clock(self, *, hlc: dict[str, Any], mono: int) -> None:
        st = self._read_state()
        st["local_hlc"] = dict(hlc)
        st["local_hlc"]["wall_clock_as_authority"] = 0
        st["local_mono"] = int(mono)
        self._write_state(st)

    def record_wall(self, node_id: str, wall_ms: int) -> dict[str, Any]:
        st = self._read_state()
        walls = dict(st.get("last_walls") or {})
        walls[str(node_id)] = int(wall_ms)
        st["last_walls"] = walls
        # recompute diagnostic skew if both present
        pair = list(st.get("pair") or [])
        if len(pair) == 2 and all(n in walls for n in pair):
            st["skew_ms"] = abs(int(walls[pair[0]]) - int(walls[pair[1]]))
        self._write_state(st)
        return st

    def enter_abort(self, reason: str, *, nodes: list[str] | None = None) -> dict[str, Any]:
        st = self._read_state()
        st["abort_refuse_join"] = True
        st["join_refused"] = True
        st["abort_reason"] = str(reason or "")
        st["skew_pending"] = True
        if nodes is not None:
            st["pending_nodes"] = list(nodes)
        self._write_state(st)
        return st

    def refuse_join(self, reason: str) -> dict[str, Any]:
        st = self._read_state()
        st["join_refused"] = True
        st["abort_refuse_join"] = True
        st["abort_reason"] = str(reason or "ABORT→refuse join")
        self._write_state(st)
        return st

    def clear_pending_detection(self) -> dict[str, Any]:
        """Clear pending detection after refuse engaged (refuse stays)."""
        st = self._read_state()
        st["skew_pending"] = False
        st["pending_nodes"] = []
        self._write_state(st)
        return st

    def mark_pending(self, nodes: list[str], *, skew_ms: int) -> dict[str, Any]:
        st = self._read_state()
        st["skew_pending"] = True
        st["pending_nodes"] = list(nodes)
        st["skew_ms"] = int(skew_ms)
        self._write_state(st)
        return st

    def append_sample(self, sample: ClockSample) -> None:
        line = json.dumps(sample.to_dict(), sort_keys=True)
        with self.samples_path.open("a", encoding="utf-8") as fh:
            fh.write(line + "\n")

    def list_samples(self) -> list[ClockSample]:
        if not self.samples_path.is_file():
            return []
        out: list[ClockSample] = []
        for line in self.samples_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            out.append(ClockSample.from_dict(json.loads(line)))
        return out

    def bump_refused(self) -> int:
        st = self._read_state()
        n = int(st.get("refused_join_count") or 0) + 1
        st["refused_join_count"] = n
        st["wall_clock_as_authority"] = 0
        self._write_state(st)
        return n

    def bump_accepted(self) -> int:
        st = self._read_state()
        n = int(st.get("accepted_join_count") or 0) + 1
        st["accepted_join_count"] = n
        st["wall_clock_as_authority"] = 0
        self._write_state(st)
        return n


__all__ = [
    "ClockStore",
    "require_no_plaintext",
]
