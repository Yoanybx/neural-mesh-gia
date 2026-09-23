"""Single writable primary witness for fabric fault tests (CP-0011 parity)."""

from __future__ import annotations

import json
import os
from pathlib import Path


class PrimaryWitness:
    """Lexicographic + file-lock style witness: ≤1 writable primary."""

    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def _read(self) -> dict:
        if not self.path.exists():
            return {"writable_primary": None, "epoch": 0}
        return json.loads(self.path.read_text(encoding="utf-8"))

    def _write(self, data: dict) -> None:
        tmp = self.path.with_suffix(".tmp")
        tmp.write_text(
            json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        os.replace(tmp, self.path)

    def claim(self, node_id: str, *, epoch: int | None = None) -> bool:
        data = self._read()
        cur = data.get("writable_primary")
        cur_epoch = int(data.get("epoch") or 0)
        new_epoch = cur_epoch + 1 if epoch is None else int(epoch)
        if cur is None or str(cur) == str(node_id) or str(node_id) < str(cur):
            data = {"writable_primary": str(node_id), "epoch": new_epoch}
            self._write(data)
            return True
        return False

    def release(self, node_id: str) -> None:
        data = self._read()
        if data.get("writable_primary") == str(node_id):
            data["writable_primary"] = None
            self._write(data)

    def writable_primary(self) -> str | None:
        return self._read().get("writable_primary")

    def count_writable(self) -> int:
        return 1 if self.writable_primary() else 0


__all__ = ["PrimaryWitness"]
