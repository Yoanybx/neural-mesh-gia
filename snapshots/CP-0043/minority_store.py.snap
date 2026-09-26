"""Filesystem minority-write store: pair, primary, halt flag, attempt log.

Layout under ``<data_root>/minority/``:

  minority_state.json
  attempts.jsonl
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from .models import (
    SCHEMA_STORE,
    MinorityN2Only,
    MinorityPlaintextForbidden,
    WriteAttempt,
)


def require_no_plaintext(mode: str | None) -> None:
    """Refuse plaintext / cleartext as a minority-write transport claim."""
    if mode is None:
        return
    m = str(mode).strip().lower()
    if m in ("plaintext", "plain", "tcp", "cleartext"):
        raise MinorityPlaintextForbidden(
            f"plaintext mode forbidden for minority ops: {mode!r}"
        )


class MinorityStore:
    """Persist N=2 pair + writable primary + halt state under a data root."""

    MAX_NODES = 2

    def __init__(self, data_root: str | Path):
        self.data_root = Path(data_root)
        self.root = self.data_root / "minority"
        self.state_path = self.root / "minority_state.json"
        self.attempts_path = self.root / "attempts.jsonl"
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
            "writable_primary": None,
            "writes_halted": False,
            "abort_halt_writes": False,
            "abort_reason": "",
            "minority_write_pending": False,
            "pending_claimants": [],
            "minority_writes": 0,
            "dual_primary": 0,
            "vault_acme_required": 0,
            "plaintext_fallback": 0,
            "rejected_minority_count": 0,
            "accepted_count": 0,
        }

    def _read_state(self) -> dict[str, Any]:
        if not self.state_path.is_file():
            return self._default_state()
        data = json.loads(self.state_path.read_text(encoding="utf-8"))
        data["minority_writes"] = 0
        data["dual_primary"] = 0
        data["vault_acme_required"] = 0
        data["plaintext_fallback"] = 0
        data["schema"] = SCHEMA_STORE
        if "pair" not in data or data["pair"] is None:
            data["pair"] = []
        if "pending_claimants" not in data or data["pending_claimants"] is None:
            data["pending_claimants"] = []
        return data

    def _write_state(self, data: dict[str, Any]) -> None:
        data = dict(data)
        data["schema"] = SCHEMA_STORE
        data["minority_writes"] = 0
        data["dual_primary"] = 0
        data["vault_acme_required"] = 0
        data["plaintext_fallback"] = 0
        pair = list(data.get("pair") or [])
        if len(pair) > self.MAX_NODES:
            raise MinorityN2Only(
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
    def writable_primary(self) -> str | None:
        v = self._read_state().get("writable_primary")
        return str(v) if v else None

    @property
    def writes_halted(self) -> bool:
        return bool(self._read_state().get("writes_halted"))

    @property
    def abort_halt_writes(self) -> bool:
        return bool(self._read_state().get("abort_halt_writes"))

    def set_pair(self, node_ids: list[str]) -> list[str]:
        ids = [str(n) for n in node_ids]
        if len(ids) > self.MAX_NODES:
            raise MinorityN2Only(
                f"N>2 refused: cannot register {len(ids)} nodes (max {self.MAX_NODES})"
            )
        if len(ids) != len(set(ids)):
            raise MinorityN2Only("duplicate node_id in pair refused")
        st = self._read_state()
        st["pair"] = ids
        self._write_state(st)
        return ids

    def set_writable_primary(self, node_id: str | None) -> None:
        st = self._read_state()
        if node_id is not None:
            pair = list(st.get("pair") or [])
            if node_id not in pair:
                raise MinorityN2Only(
                    f"primary {node_id!r} not in pair {pair}"
                )
        st["writable_primary"] = node_id
        self._write_state(st)

    def enter_abort(self, reason: str, *, claimants: list[str] | None = None) -> dict[str, Any]:
        st = self._read_state()
        st["abort_halt_writes"] = True
        st["writes_halted"] = True
        st["abort_reason"] = str(reason or "")
        st["minority_write_pending"] = True
        if claimants is not None:
            st["pending_claimants"] = list(claimants)
        self._write_state(st)
        return st

    def halt_writes(self, reason: str) -> dict[str, Any]:
        st = self._read_state()
        st["writes_halted"] = True
        st["abort_halt_writes"] = True
        st["abort_reason"] = str(reason or "ABORT→halt writes")
        self._write_state(st)
        return st

    def clear_pending_detection(self) -> dict[str, Any]:
        """Clear pending detection flag after halt engaged (halt stays)."""
        st = self._read_state()
        st["minority_write_pending"] = False
        st["pending_claimants"] = []
        self._write_state(st)
        return st

    def mark_pending(self, claimants: list[str]) -> dict[str, Any]:
        st = self._read_state()
        st["minority_write_pending"] = True
        st["pending_claimants"] = list(claimants)
        self._write_state(st)
        return st

    def append_attempt(self, attempt: WriteAttempt) -> None:
        line = json.dumps(attempt.to_dict(), sort_keys=True)
        with self.attempts_path.open("a", encoding="utf-8") as fh:
            fh.write(line + "\n")
        st = self._read_state()
        if attempt.outcome == "accepted":
            st["accepted_count"] = int(st.get("accepted_count") or 0) + 1
        elif attempt.outcome == "rejected_minority":
            st["rejected_minority_count"] = int(st.get("rejected_minority_count") or 0) + 1
        self._write_state(st)

    def list_attempts(self) -> list[WriteAttempt]:
        if not self.attempts_path.is_file():
            return []
        out: list[WriteAttempt] = []
        for line in self.attempts_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            out.append(WriteAttempt.from_dict(json.loads(line)))
        return out

    def bump_rejected_minority(self) -> int:
        st = self._read_state()
        n = int(st.get("rejected_minority_count") or 0) + 1
        st["rejected_minority_count"] = n
        # Never bump minority_writes (committed) — hard 0
        st["minority_writes"] = 0
        self._write_state(st)
        return n


__all__ = [
    "MinorityStore",
    "require_no_plaintext",
]
